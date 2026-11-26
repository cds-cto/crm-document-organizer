import os, io, requests
from base64 import b64encode
from typing import Any, Dict, Tuple, Optional

from constant import APP_SETTING

class CDSZone2Service:
    """
    Encapsulates calls to CDS organizer/process (multipart 'file' + Basic Auth).
    """
    def __init__(self, username: str, password: str, base_url: Optional[str] = None):
        self.base_url = base_url or APP_SETTING.CDS_URL
        token = b64encode(f"{username}:{password}".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}", "Connection": "keep-alive"}

    def post_file(self, file_buf: io.BytesIO, filename: str, mime_type: str, document_id: str) -> Tuple[int, Dict[str, Any]]:
        files = {
            "file": (filename, file_buf, mime_type)
        }
        data = {
            "documentId": document_id
        }
        resp = requests.post(
            self.base_url,
            headers=self.headers,
            files=files,
            data=data,
            timeout=180
        )
        try:
            return resp.status_code, resp.json()
        except Exception:
            return resp.status_code, {"text": resp.text[:2000]}

    @staticmethod
    def normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes CDS responses into:
          status, title, category_uuid, ProfileId, LiabilityId
        """
        if not isinstance(payload, dict):
            return {
                "status": None,
                "title": None,
                "category_uuid": None,
                "ProfileId": None,
                "LiabilityId": None,
            }
        return {
            "status": payload.get("status"),
            "title": payload.get("title"),
            "category_uuid": payload.get("category_uuid"),
            "ProfileId": payload.get("ProfileId"),
            "LiabilityId": payload.get("LiabilityId"),
        }
