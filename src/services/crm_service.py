import os, io, json, mimetypes, requests
from urllib.parse import urlparse, unquote
from typing import Any, Dict, List, Optional, Tuple

from services.config_loader_services import config_loader

DEFAULT_SSICRM_URL = "https://ssiapi.com/api"
SSICRM_MAIN_URL = config_loader.get("ssicrm", "base_url", env="SSICRM_MAIN_URL", default=DEFAULT_SSICRM_URL)

class SSICRMService:
    """
    Encapsulates all interactions with SSICRM.
    """
    def __init__(self):
        self.r = requests.Session()
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    # ------------------ Auth ------------------
    def login(self, user_name: str, password: str) -> bool:
        url = f"{SSICRM_MAIN_URL}/User/auth"
        data = {"userName": user_name, "password": password, "returnUrl": ""}
        res = self.r.post(url, json=data, timeout=30)
        if res.status_code == 200:
            body = res.json()
            self.token = body["data"]["token"]
            self.refresh_token = body["data"]["refreshToken"]
            print("Login to SSICRM successful")
            return True
        raise RuntimeError(f"Can't log in to SSICRM (status {res.status_code}): {res.text[:200]}")

    # ------------------ Unmapped search ------------------
    def search_unmapped_documents(self) -> List[Dict[str, Any]]:
        self._require_auth()
        headers = {"Content-Type": "application/json", "authorization": f"Bearer {self.token}"}
        url = f"{SSICRM_MAIN_URL}/UnMappedDocument/search"
        data = {
            "start": 0,
            "length": 300,
            "columns": [
                {"columnName": "status", "search": {"value": 0, "operator": 0}},
                # {"columnName": "originDocumentReferenceType", "search": {"value": "1", "operator": 0}}
            ]
        }
        res = self.r.post(url, json=data, headers=headers, timeout=60)
        res.raise_for_status()
        payload = res.json()
        return (payload.get("data") or {}).get("data") or []

    # ------------------ Preview URL ------------------
    def preview_document(self, document_id: str) -> Optional[str]:
        self._require_auth()
        headers = {"Content-Type": "application/json", "authorization": f"Bearer {self.token}"}
        url = f"{SSICRM_MAIN_URL}/UnMappedDocument/{document_id}/preview"
        res = self.r.post(url, json={"URL": True}, headers=headers, timeout=60)
        if res.status_code != 200:
            print(f"Failed to preview document {document_id}. Status code: {res.status_code}")
            return None
        body = res.json()
        return (body.get("data") or {}).get("url")

    # ------------------ Save changes ------------------
    def save_changes(
        self,
        document_id: str,
        profile_id: Optional[str],
        liability_id: Optional[str],
        title: str,
        category: str,
        status: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Updates unmapped document fields in SSICRM.
        'category' should be the UUID returned by CDS (category_uuid) if SSICRM expects UUID.
        """
        self._require_auth()
        headers = {"Content-Type": "application/json", "authorization": f"Bearer {self.token}"}
        url = f"{SSICRM_MAIN_URL}/UnMappedDocument/{document_id}" 
        data = {
            "documentId": document_id,
            "profileId": profile_id,
            "liabilityId": liability_id,
            "title": title,
            "category": category,
            "description": "",
            "status": status,
        }
        res = self.r.put(url, json=data, headers=headers, timeout=60)
        if res.status_code != 200:
            print(f"Failed to save changes for document {document_id}. Status code: {res.status_code}")
            return None
        return res.json()

    def set_pending(
        self,
        document_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Updates unmapped document fields in SSICRM.
        'category' should be the UUID returned by CDS (category_uuid) if SSICRM expects UUID.
        """
        self._require_auth()
        headers = {"Content-Type": "application/json", "authorization": f"Bearer {self.token}"}
        url = f"{SSICRM_MAIN_URL}/UnMappedDocument/{document_id}"  # ensure /save
        data = {
            "documentId": document_id,
            "profileId": None,
            "liabilityId": None,
            "title": "Pending File",
            "category": None,
            "description": None,
            "status": 1,
        }
        res = self.r.put(url, json=data, headers=headers, timeout=60)
        if res.status_code != 200:
            print(f"Failed to save changes for document {document_id}. Status code: {res.status_code}")
            return None
        return res.json()
    
    def clear_pending(self, document_id: str) -> Optional[Dict[str, Any]]:
        self._require_auth()
        headers = {"Content-Type": "application/json", "authorization": f"Bearer {self.token}"}
        url = f"{SSICRM_MAIN_URL}/UnMappedDocument/{document_id}"

        data = {
            "documentId": document_id,
            "profileId": None,
            "liabilityId": None,
            "title": "Pending File",
            "category": None,
            "description": "",
            "status": 0,
        }

        res = self.r.put(url, json=data, headers=headers, timeout=60)
        if res.status_code != 200:
            print(f"Failed to clear pending for document {document_id}. Status code: {res.status_code}; Body: {res.text[:400]}")
            return None
        return res.json()

    # ------------------ Download helper ------------------
    def download_file(self, file_url: str) -> Tuple[io.BytesIO, str, str]:
        with self.r.get(file_url, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            cd = resp.headers.get("Content-Disposition", "")
            filename = None
            if "filename=" in cd:
                filename = cd.split("filename=")[-1].strip('"; ')
                filename = unquote(filename)
            if not filename:
                filename = os.path.basename(urlparse(file_url).path) or "document"

            # MIME type
            mime_type = resp.headers.get("Content-Type")
            if not mime_type or "/" not in mime_type:
                mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

            buf = io.BytesIO()
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    buf.write(chunk)
            buf.seek(0)

            return buf, filename, mime_type

    # ------------------ Helper ------------------
    def _require_auth(self):
        if not self.token:
            raise RuntimeError("Not authenticated to SSICRM. Call login() first.")

