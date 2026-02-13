import pytest

from tests.integration.mailer_lite.conftest import _extract_id, _get_registry_entry
from utils.events_utils import normalize_email


@pytest.mark.integration
def test_subscribers_crud_service(mailerlite_clients, unique_email, subscribed_at):
    """Verify subscribers CRUD operations and Firestore registry via the service client."""
    subscribers_client = mailerlite_clients["subscribers"]

    created = subscribers_client.create(
        unique_email,
        {
            "fields": {
                "birthdate": "01-01-1999",
                "phone": "+390000000000",
            },
            "subscribed_at": subscribed_at,
        },
    )
    subscriber_id = _extract_id(created)
    assert subscriber_id is not None

    registry_entry = _get_registry_entry(unique_email)
    assert registry_entry is not None
    assert registry_entry.get("mailerlite_id") == str(subscriber_id)

    fetched = subscribers_client.get(unique_email)
    assert fetched["data"]["email"] == normalize_email(unique_email)

    subscribers_client.update(
        unique_email,
        {
            "fields": {"birthdate": "01-01-2000"},
        },
    )

    subscribers_client.delete_subscriber(subscriber_id)

    registry_entry = _get_registry_entry(unique_email, retries=2, delay=0.1)
    assert registry_entry is None
