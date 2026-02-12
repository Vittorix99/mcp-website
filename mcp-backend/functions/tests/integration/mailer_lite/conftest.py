import os
import time
from datetime import datetime
from uuid import uuid4

import pytest

from config.firebase_config import db
from services.mailer_lite import FieldsClient, GroupsClient, SubscribersClient
from utils.events_utils import normalize_email


REQUIRED_FIELDS = [
    {"name": "birthdate", "type": "text"},
    {"name": "phone", "type": "text"},
    {"name": "membership_id", "type": "text"},
    {"name": "participant_id", "type": "text"},
]


def _now_timestamp():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _extract_list_data(response):
    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, list):
            return data
    return []


def _extract_id(response):
    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, dict) and "id" in data:
            return data["id"]
        if "id" in response:
            return response["id"]
    return None


def _get_registry_entry(email: str, retries: int = 3, delay: float = 0.2):
    normalized = normalize_email(email)
    if not normalized:
        return None
    collection = db.collection("subscribers_mailerlite")
    for _ in range(max(retries, 1)):
        snap = collection.document(normalized).get()
        if snap.exists:
            return snap.to_dict() or {}
        time.sleep(delay)
    return None


@pytest.fixture(scope="session")
def mailerlite_env():
    api_key = os.environ.get("MAILERLITE_API_KEY")
    if not api_key:
        pytest.skip("MAILERLITE_API_KEY is not set")
    return api_key


@pytest.fixture(scope="session")
def mailerlite_prefix():
    return os.environ.get("MAILERLITE_TEST_PREFIX", "MCPWEB_TEST")


@pytest.fixture(scope="session")
def mailerlite_email_base():
    return os.environ.get("MAILERLITE_TEST_EMAIL_BASE", "mcpweb.testing@gmail.com")


@pytest.fixture(scope="session")
def mailerlite_clients(mailerlite_env):
    return {
        "fields": FieldsClient(),
        "groups": GroupsClient(),
        "subscribers": SubscribersClient(),
    }


@pytest.fixture(scope="session", autouse=True)
def ensure_custom_fields(mailerlite_clients):
    fields_client = mailerlite_clients["fields"]
    existing = {item.get("name") for item in _extract_list_data(fields_client.list())}
    for field in REQUIRED_FIELDS:
        name = field["name"]
        if name in existing:
            continue
        try:
            fields_client.create(name, field["type"])
        except Exception:
            pass


@pytest.fixture
def unique_group_name(mailerlite_prefix):
    return f"{mailerlite_prefix}_group_{uuid4().hex[:8]}"


@pytest.fixture
def unique_email(mailerlite_prefix, mailerlite_email_base):
    local, domain = mailerlite_email_base.split("@", 1)
    return f"{local}+{mailerlite_prefix}_{uuid4().hex[:8]}@{domain}"


@pytest.fixture
def subscribed_at():
    return _now_timestamp()


__all__ = [
    "_extract_list_data",
    "_extract_id",
    "_get_registry_entry",
]
