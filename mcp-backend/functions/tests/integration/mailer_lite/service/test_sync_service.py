import time

import pytest

from services.mailer_lite import GroupsClient, SubscribersClient
from tests.integration.mailer_lite.conftest import _extract_id, _get_registry_entry
from utils.events_utils import normalize_email


GROUP_MEMBERSHIPS = "memberships"
GROUP_NEWSLETTER = "newsletter"


def _ensure_group(groups_client: GroupsClient, name: str) -> str:
    response = groups_client.list(params={"limit": 1, "page": 1, "filter": {"name": name}})
    data = response.get("data") if isinstance(response, dict) else None
    if data:
        group_id = _extract_id(data[0])
        if group_id:
            return str(group_id)
    created = groups_client.create(name)
    group_id = _extract_id(created)
    if not group_id:
        raise AssertionError(f"Unable to resolve group id for {name}")
    return str(group_id)


def _group_has_subscriber(groups_client: GroupsClient, group_id: str, email: str) -> bool:
    response = groups_client.subscribers(group_id, params={"limit": 50})
    data = response.get("data") if isinstance(response, dict) else None
    if not isinstance(data, list):
        return False
    normalized = normalize_email(email)
    for item in data:
        if not isinstance(item, dict):
            continue
        if normalize_email(item.get("email")) == normalized:
            return True
        if str(item.get("id")) == str(item.get("subscriber_id")):
            return True
    return False


def _wait_for_group(groups_client: GroupsClient, group_id: str, email: str, retries: int = 4):
    for _ in range(max(retries, 1)):
        if _group_has_subscriber(groups_client, group_id, email):
            return True
        time.sleep(0.4)
    return False


@pytest.mark.integration
def test_sync_newsletter_happy_path(unique_email):
    """Sync newsletter consent creates subscriber, registry, and group assignment."""
    subscribers_client = SubscribersClient()
    groups_client = GroupsClient()

    group_id = _ensure_group(groups_client, GROUP_NEWSLETTER)
    subscriber_id = None
    try:
        subscriber_id = subscribers_client.sync_newsletter_consent(
            unique_email,
            {
                "birthdate": "01-01-1999",
                "phone": "+390000000000",
                "participant_id": "P-1",
            },
            opted_in_at="2026-02-12 10:00:00",
        )
        assert subscriber_id is not None

        registry_entry = _get_registry_entry(unique_email)
        assert registry_entry is not None
        assert registry_entry.get("mailerlite_id") == str(subscriber_id)

        fetched = subscribers_client.get(unique_email)
        assert normalize_email(fetched["data"]["email"]) == normalize_email(unique_email)

        assert _wait_for_group(groups_client, group_id, unique_email)
    finally:
        if subscriber_id is not None:
            subscribers_client.delete_subscriber(subscriber_id)


@pytest.mark.integration
def test_sync_membership_happy_path(unique_email):
    """Sync membership creates subscriber, registry, and group assignment."""
    subscribers_client = SubscribersClient()
    groups_client = GroupsClient()

    group_id = _ensure_group(groups_client, GROUP_MEMBERSHIPS)
    subscriber_id = None
    try:
        subscriber_id = subscribers_client.sync_membership(
            unique_email,
            {
                "birthdate": "01-01-2000",
                "phone": "+390000000000",
                "membership_id": "M-1",
            },
        )
        assert subscriber_id is not None

        registry_entry = _get_registry_entry(unique_email)
        assert registry_entry is not None
        assert registry_entry.get("mailerlite_id") == str(subscriber_id)

        fetched = subscribers_client.get(unique_email)
        assert normalize_email(fetched["data"]["email"]) == normalize_email(unique_email)

        assert _wait_for_group(groups_client, group_id, unique_email)
    finally:
        if subscriber_id is not None:
            subscribers_client.delete_subscriber(subscriber_id)
