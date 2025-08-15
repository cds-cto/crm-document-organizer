import os, io, requests
from base64 import b64encode
from typing import Any, Dict, Tuple, Optional

from services.config_loader_services import config_loader

DEFAULT_CDS_URL = "https://api.cdszone2.com/api/organizer/process"
CDS_URL = config_loader.get("cdszone2", "base_url", env="CDS_URL", default=DEFAULT_CDS_URL)

class CDSZone2Service:
    """
    Encapsulates calls to CDS organizer/process (multipart 'file' + Basic Auth).
    """
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None, base_url: Optional[str] = None):
        user = username or config_loader.get("cdszone2", "username", env="CDS_USER", default="")
        pwd = password or config_loader.get("cdszone2", "password", env="CDS_PASS", default="")
        self.base_url = base_url or CDS_URL or DEFAULT_CDS_URL
        token = b64encode(f"{user}:{pwd}".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}", "Connection": "keep-alive"}

    def post_file(self, file_buf: io.BytesIO, filename: str, mime_type: str) -> Tuple[int, Dict[str, Any]]:
        files = {"file": (filename, file_buf, mime_type)}
        resp = requests.post(self.base_url, headers=self.headers, files=files, timeout=180)
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
