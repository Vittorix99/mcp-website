"""Firebase clients created only after complete runtime-policy validation."""

import os

import firebase_admin
from firebase_admin import credentials, firestore, storage
from firebase_functions import options
from google.auth.credentials import AnonymousCredentials

from config.environment import load_environment
from config.runtime_settings import (
    CredentialMode, RuntimeConfigurationError, RuntimeSettings, get_runtime_settings,
)


region = "us-central1"


class _EmulatorCredential(credentials.Base):
    def get_credential(self):
        return AnonymousCredentials()


def initialize_firebase(settings: RuntimeSettings):
    firebase = settings.firebase
    emulator = firebase.credential_mode == CredentialMode.EMULATOR
    hosts = {
        "FIRESTORE_EMULATOR_HOST": firebase.firestore_emulator_host,
        "FIREBASE_AUTH_EMULATOR_HOST": firebase.auth_emulator_host,
        "STORAGE_EMULATOR_HOST": firebase.storage_emulator_host,
        "PUBSUB_EMULATOR_HOST": firebase.pubsub_emulator_host,
    }
    # SDKs consume these variables directly; propagate only validated settings.
    for key, host in hosts.items():
        if emulator:
            os.environ[key] = host
        elif os.environ.get(key):
            raise RuntimeConfigurationError(f"Cloud Firebase cannot use {key}")
    os.environ["GCLOUD_PROJECT"] = firebase.project_id
    os.environ["GOOGLE_CLOUD_PROJECT"] = firebase.project_id
    if firebase_admin._apps:
        app = firebase_admin.get_app()
        if app.project_id != firebase.project_id:
            raise RuntimeConfigurationError("Existing Firebase app project does not match runtime policy")
    else:
        credential = _EmulatorCredential() if emulator else credentials.ApplicationDefault()
        app = firebase_admin.initialize_app(credential, {
            "projectId": firebase.project_id,
            "storageBucket": firebase.storage_bucket,
        })
    return firestore.client(app=app), storage.bucket(firebase.storage_bucket, app=app)


load_environment()
db, bucket = initialize_firebase(get_runtime_settings())

cors = options.CorsOptions(
    cors_origins="*",
    cors_methods=["get", "post", "put", "delete", "options"],
)

__all__ = ["db", "bucket", "cors", "region", "initialize_firebase"]
