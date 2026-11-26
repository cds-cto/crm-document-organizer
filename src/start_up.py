# general import
import os
from typing import Tuple

# project import
from constant import GCP_SECRET
from services.gcloud_service import GoogleCloudServices


def load_secret(secret, project_id: str):
    secret.GCP_SECRET_VALUE = GoogleCloudServices.get_secret(secret.GCP_SECRET_NAME, project_id)
    print(f"{secret.GCP_SECRET_NAME} loaded from Secret Manager")


def split_user_pass(secret) -> Tuple[str, str]:
    """Split a 'user:password' secret. Only the first ':' splits, so the password may hold ':'."""
    user, _, password = (secret.GCP_SECRET_VALUE or "").partition(":")
    if not user or not password:
        raise ValueError(f"Secret {secret.GCP_SECRET_NAME} must use the format user:password")
    return user, password


def register_startup_event():
    project_id = os.getenv("GCP_PROJECT")
    if not project_id:
        raise ValueError("GCP_PROJECT environment variable not set")

    # SSICRM login, format: user:password
    load_secret(GCP_SECRET.SSICRM_LOGIN, project_id)

    # CDS Zone 2 Basic Auth, format: user:password
    load_secret(GCP_SECRET.CDS_LOGIN, project_id)
