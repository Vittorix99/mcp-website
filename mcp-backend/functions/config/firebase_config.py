import json
import os

import firebase_admin
from firebase_admin import credentials, firestore, storage
from firebase_functions import options

region = "us-central1"

_cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")


def _load_credentials():
    """Return a firebase_admin credential, supporting both service accounts and ADC files."""
    # Prefer explicit service-account JSON path/file
    if _cred_path and os.path.exists(_cred_path):
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
    firebase_admin.initialize_app(cred, {"storageBucket": os.environ.get("STORAGE_BUCKET")})
else:
    cred = None

db = firestore.client()
bucket = storage.bucket()

if os.environ.get("FIRESTORE_EMULATOR_HOST"):
    print(f"Using Firestore emulator at {os.environ['FIRESTORE_EMULATOR_HOST']}")
else:
    print("Using Firestore production project.")

cors = options.CorsOptions(
    cors_origins="*",
    cors_methods=["get", "post", "put", "delete", "options"],
)

__all__ = ["db", "bucket", "cors", "region"]
