import pytest
from types import SimpleNamespace

from services.mailer_lite.groups_client import GroupsClient


class _DummyClient:
    def __init__(self, sdk):
        self.sdk = sdk
        self.calls = []

    def call(self, fn, *args, **kwargs):
        self.calls.append((fn, args, kwargs))
        return True


def test_groups_list_filters_params():
    """Only allowed list params are forwarded to the SDK."""
    sdk = SimpleNamespace(groups=SimpleNamespace(list=lambda **kwargs: None))
    client = _DummyClient(sdk)
    groups = GroupsClient(client=client)

    groups.list(params={"limit": 10, "page": 2, "sort": "name", "filter": {"x": 1}, "extra": "no"})

    fn, args, kwargs = client.calls[0]
    assert fn is sdk.groups.list
    assert args == ()
    assert kwargs == {"limit": 10, "page": 2, "sort": "name", "filter": {"x": 1}}


def test_groups_delete_wraps_bool_response():
    """Delete wraps boolean SDK responses into a status payload."""
    sdk = SimpleNamespace(groups=SimpleNamespace(delete=lambda group_id: True))
    client = _DummyClient(sdk)
    groups = GroupsClient(client=client)

    response = groups.delete("123")

    assert response == {"status": True}
    fn, args, kwargs = client.calls[0]
    assert fn is sdk.groups.delete
    assert args == (123,)
    assert kwargs == {}


def test_groups_assign_wraps_bool_response():
    """Assign wraps boolean SDK responses into a status payload."""
    sdk = SimpleNamespace(
        subscribers=SimpleNamespace(assign_subscriber_to_group=lambda subscriber_id, group_id: True)
    )
    client = _DummyClient(sdk)
    groups = GroupsClient(client=client)

    response = groups.assign_subscriber("10", "20")

    assert response == {"status": True}
    fn, args, kwargs = client.calls[0]
    assert fn is sdk.subscribers.assign_subscriber_to_group
    assert args == (10, 20)
    assert kwargs == {}


def test_groups_unassign_wraps_bool_response():
    """Unassign wraps boolean SDK responses into a status payload."""
    sdk = SimpleNamespace(
        subscribers=SimpleNamespace(unassign_subscriber_from_group=lambda subscriber_id, group_id: True)
    )
    client = _DummyClient(sdk)
    groups = GroupsClient(client=client)

    response = groups.unassign_subscriber("10", "20")

    assert response == {"status": True}
    fn, args, kwargs = client.calls[0]
    assert fn is sdk.subscribers.unassign_subscriber_from_group
    assert args == (10, 20)
    assert kwargs == {}


def test_groups_update_rejects_invalid_id():
    """Update rejects non-int-compatible group ids."""
    sdk = SimpleNamespace(groups=SimpleNamespace(update=lambda group_id, name: None))
    client = _DummyClient(sdk)
    groups = GroupsClient(client=client)

    with pytest.raises(ValueError):
        groups.update("not-an-int", "name")
