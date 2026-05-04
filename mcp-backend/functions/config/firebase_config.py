import json
import os

import firebase_admin
from firebase_admin import credentials, firestore, storage
from firebase_functions import options

from config.environment import load_environment

load_environment()

region = "us-central1"

_explicit_cred = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
_raw_cred = _explicit_cred or "service_account.json"
_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_functions_dir = os.path.abspath(os.path.join(_base_dir, ".."))
_repo_root = os.path.abspath(os.path.join(_base_dir, "..", ".."))


def _resolve_cred_path(path: str) -> str:
    if not path:
        return path
    if os.path.isabs(path):
        return path
    candidates = [
        os.path.abspath(path),
        os.path.abspath(os.path.join(_base_dir, path)),
        os.path.abspath(os.path.join(_functions_dir, path)),
        os.path.abspath(os.path.join(_repo_root, path)),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    # Fall back to a deterministic location to improve error messages
    return os.path.abspath(os.path.join(_base_dir, path))


_cred_path = _resolve_cred_path(_raw_cred)


def _load_credentials():
    """Return a firebase_admin credential, supporting both service accounts and ADC files."""
    service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        payload = json.loads(service_account_json)
        return credentials.Certificate(payload)

    # Prefer explicit service-account JSON path/file
    if _cred_path:
        if not os.path.exists(_cred_path):
            if _explicit_cred:
                raise FileNotFoundError(
                    f"Service account not found: {_cred_path} "
                    f"(from GOOGLE_APPLICATION_CREDENTIALS='{_explicit_cred}')"
                )
        else:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _cred_path
            try:
                with open(_cred_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if payload.get("type") == "service_account":
                    return credentials.Certificate(payload)
            except ValueError:
                pass  # Fall back to Application Default

    # Fallback: try Application Default Credentials (e.g. gcloud user credentials)
    return credentials.ApplicationDefault()


if not firebase_admin._apps:
    cred = _load_credentials()
    storage_bucket = os.environ.get("STORAGE_BUCKET")
    project_id = os.environ.get("GCLOUD_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raw_config = os.environ.get("FIREBASE_CONFIG")
        if raw_config:
            try:
                project_id = json.loads(raw_config).get("projectId")
            except (TypeError, ValueError):
                project_id = None
    init_opts = {}
    if storage_bucket:
        init_opts["storageBucket"] = storage_bucket
    if project_id:
        init_opts["projectId"] = project_id
    firebase_admin.initialize_app(cred, init_opts)
else:
    cred = None

db = firestore.client()
bucket = storage.bucket() if os.environ.get("STORAGE_BUCKET") else None

if os.environ.get("FIRESTORE_EMULATOR_HOST"):
    print(f"Using Firestore emulator at {os.environ['FIRESTORE_EMULATOR_HOST']}")
else:
    print(
        "Using Firestore cloud project "
        f"(cred={_cred_path}, project={db.project})"
    )
print(f"Firebase credentials file: {_cred_path}")

cors = options.CorsOptions(
    cors_origins="*",
    cors_methods=["get", "post", "put", "delete", "options"],
)

__all__ = ["db", "bucket", "cors", "region"]
