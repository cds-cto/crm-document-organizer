from typing import Any, Dict, List, Optional
from services.cdszone_services import CDSZone2Service
from services.crm_service import SSICRMService

class DocumentProcessingFlow:
    """
    Implements: search → preview → download → post to CDS → save back to SSICRM
    """
    def __init__(self, crm: SSICRMService, cds: CDSZone2Service):
        self.crm = crm
        self.cds = cds

    def process_document(self, document_id: str, save_to_ssicrm: bool = True) -> Dict[str, Any]:
        """
        Processes a single document ID end-to-end.
        Returns a dict with details and the CDS payload.
        """
        result: Dict[str, Any] = {
            "documentId": document_id,
            "preview_url": None,
            "filename": None,
            "cds_http_status": None,
            "cds_payload": None,
            "saved": False,
            "save_response": None,
            "error": None,
        }

        try:
            # 1) preview
            preview_url = self.crm.preview_document(document_id)
            if not preview_url:
                result["error"] = "No preview URL"
                return result
            result["preview_url"] = preview_url

            # 2) download
            file_buf, filename, mime_type = self.crm.download_file(preview_url)
            result["filename"] = filename

            # 3) CDS post
            status, payload = self.cds.post_file(file_buf, filename, mime_type)
            result["cds_http_status"] = status
            result["cds_payload"] = payload

            # 4) Save back to SSICRM (optional)
            if save_to_ssicrm and status == 200 and isinstance(payload, dict):
                norm = self.cds.normalize_payload(payload)
                save_resp = self.crm.save_changes(
                    document_id=document_id,
                    profile_id=norm.get("ProfileId"),
                    liability_id=norm.get("LiabilityId"),
                    title=norm.get("title") or filename,
                    category=norm.get("category_uuid") or "",
                    status=norm.get("status") if norm.get("status") is not None else 0,
                )
                result["saved"] = save_resp is not None
                result["save_response"] = save_resp

        except Exception as e:
            result["error"] = f"{type(e).__name__}: {e}"

        return result

    def process_all_unmapped(self, save_to_ssicrm: bool = True, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Processes all (or the first `limit`) unmapped documents.
        """
        results: List[Dict[str, Any]] = []
        docs = self.crm.search_unmapped_documents()
        if limit is not None:
            docs = docs[:limit]

        for d in docs:
            doc_id = d.get("documentId")
            if not doc_id:
                continue
            r = self.process_document(doc_id, save_to_ssicrm=save_to_ssicrm)
            print(f"[{doc_id}] → {r.get('filename')} → CDS {r.get('cds_http_status')} {'(saved)' if r.get('saved') else ''}")
            results.append(r)

        return results
