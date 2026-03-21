import pytest

from services.mailer_lite.subscribers_client import SubscribersClient
from services.mailer_lite.client import MailerLiteError


class _DummySubscribersSDK:
    def create(self, email, **kwargs):
        return {"data": {"id": 1, "email": email}}

    def update(self, email, **kwargs):
        return {"data": {"id": 1, "email": email}}

    def get(self, email):
        return {"data": {"id": 1, "email": email, "status": "active"}}


class _DummySDK:
    def __init__(self):
        self.subscribers = _DummySubscribersSDK()


class _DummyClient:
    def __init__(self):
        self.sdk = _DummySDK()

    def call(self, fn, *args, **kwargs):
        return fn(*args, **kwargs)


class _DummyRegistry:
    def upsert(self, email, mailerlite_id):
        return None


class _DummyGroups:
    def assign_subscriber(self, subscriber_id, group_id):
        return {"status": True}


def _make_client():
    client = SubscribersClient(client=_DummyClient())
    client.registry = _DummyRegistry()
    client.groups_client = _DummyGroups()
    client._resolve_group_id = lambda name: 1
    return client


def test_create_rejects_invalid_fields():
    """Rejects invalid fields during create."""
    client = _make_client()
    with pytest.raises(MailerLiteError) as exc:
        client.create("a@b.com", {"fields": {"unknown_field": "x"}})
    assert exc.value.status == 400


def test_update_rejects_invalid_fields():
    """Rejects invalid fields during update."""
    client = _make_client()
    with pytest.raises(MailerLiteError) as exc:
        client.update("a@b.com", {"fields": {"unknown_field": "x"}})
    assert exc.value.status == 400


def test_sync_newsletter_rejects_invalid_fields():
    """Rejects invalid fields during newsletter sync."""
    client = _make_client()
    client._get_or_create_subscriber = lambda *args, **kwargs: pytest.fail("should not create")
    assert client.sync_newsletter_consent("a@b.com", {"unknown_field": "x"}) is None


def test_sync_membership_rejects_invalid_fields():
    """Rejects invalid fields during membership sync."""
    client = _make_client()
    client._get_or_create_subscriber = lambda *args, **kwargs: pytest.fail("should not create")
    assert client.sync_membership("a@b.com", {"unknown_field": "x"}) is None


def test_sync_newsletter_happy_path():
    """Creates/updates subscriber, stores registry, and assigns newsletter group."""
    client = _make_client()
    calls = {"updates": [], "assigned": [], "stored": []}

    client._resolve_group_id = lambda name: 123
    client._get_or_create_subscriber = lambda email, fields: {
        "id": "55",
        "email": email,
        "status": "active",
    }
    client._store_registry = lambda email, subscriber_id: calls["stored"].append(
        (email, subscriber_id)
    )

    def fake_update(email, payload):
        calls["updates"].append((email, payload))
        return {"ok": True}

    client.update = fake_update
    client.groups_client.assign_subscriber = lambda subscriber_id, group_id: calls["assigned"].append(
        (subscriber_id, group_id)
    )

    result = client.sync_newsletter_consent(
        "a@b.com",
        {"birthdate": "01-01-1999", "phone": "+390000000000"},
        opted_in_at="2026-02-12 10:00:00",
    )

    assert result == "55"
    assert ("a@b.com", "55") in calls["stored"]
    assert ("55", 123) in calls["assigned"]
    assert any(payload.get("fields") for _, payload in calls["updates"])
    assert any(payload.get("opted_in_at") for _, payload in calls["updates"])


def test_sync_membership_happy_path():
    """Creates/updates subscriber, stores registry, and assigns memberships group."""
    client = _make_client()
    calls = {"updates": [], "assigned": [], "stored": []}

    client._resolve_group_id = lambda name: 456
    client._get_or_create_subscriber = lambda email, fields: {
        "id": "77",
        "email": email,
        "status": "active",
    }
    client._store_registry = lambda email, subscriber_id: calls["stored"].append(
        (email, subscriber_id)
    )

    def fake_update(email, payload):
        calls["updates"].append((email, payload))
        return {"ok": True}

    client.update = fake_update
    client.groups_client.assign_subscriber = lambda subscriber_id, group_id: calls["assigned"].append(
        (subscriber_id, group_id)
    )

    result = client.sync_membership(
        "a@b.com",
        {"birthdate": "01-01-1999", "membership_id": "MEM-1"},
    )

    assert result == "77"
    assert ("a@b.com", "77") in calls["stored"]
    assert ("77", 456) in calls["assigned"]
    assert any(payload.get("fields") for _, payload in calls["updates"])
