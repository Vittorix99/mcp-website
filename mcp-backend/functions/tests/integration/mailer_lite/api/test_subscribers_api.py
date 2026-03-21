import pytest

from api.admin.mailer_lite import subscribers_api
from tests.integration.mailer_lite.conftest import _get_registry_entry
from tests.utils import DummyRequest, unwrap_response
from utils.events_utils import normalize_email


def _extract_id(payload):
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict) and "id" in data:
            return data["id"]
        if "id" in payload:
            return payload["id"]
    return None


@pytest.mark.integration
def test_subscribers_crud_api(unique_email, subscribed_at):
    """Verify subscribers CRUD endpoints and Firestore registry via the API."""
    subscriber_id = None
    try:
        create_req = DummyRequest(
            method="POST",
            json={
                "email": unique_email,
                "fields": {"birthdate": "01-01-1999", "phone": "+390000000000"},
                "subscribed_at": subscribed_at,
            },
        )
        resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscribers(create_req))
        assert status == 200
        subscriber_id = _extract_id(resp)
        assert subscriber_id is not None

        registry_entry = _get_registry_entry(unique_email)
        assert registry_entry is not None
        assert registry_entry.get("mailerlite_id") == str(subscriber_id)

        get_req = DummyRequest(method="GET", args={"email": unique_email})
        resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscribers(get_req))
        assert status == 200
        assert resp["data"]["email"] == normalize_email(unique_email)

        update_req = DummyRequest(
            method="PUT",
            json={"email": unique_email, "fields": {"birthdate": "01-01-2000"}},
        )
        resp, status = unwrap_response(subscribers_api.admin_mailerlite_subscribers(update_req))
        assert status == 200
    finally:
        if subscriber_id is not None:
            delete_req = DummyRequest(method="DELETE", json={"id": subscriber_id})
            unwrap_response(subscribers_api.admin_mailerlite_subscribers(delete_req))
            registry_entry = _get_registry_entry(unique_email, retries=2, delay=0.1)
            assert registry_entry is None
