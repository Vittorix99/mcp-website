"""Prove real test-environment settings keep Sender calls offline."""

import pytest

from clients import sender_client
from config.runtime_settings import ProviderMode, load_runtime_settings
from models.event_participant import EventParticipant
from models.membership import Membership
from services.sender import sender_sync
from services.sender.sender_service import SenderService


@pytest.fixture
def disabled_sender_settings(monkeypatch):
    settings = load_runtime_settings({"MCP_ENV": "test"})
    assert settings.providers.sender is ProviderMode.DISABLED
    monkeypatch.setattr(sender_sync, "get_runtime_settings", lambda: settings)
    monkeypatch.setattr("services.sender.sender_service.get_runtime_settings", lambda: settings)
    return settings


@pytest.fixture
def sender_request_spy(monkeypatch):
    calls = []

    def fail_if_called(cls, method, endpoint, api_key, *args, **kwargs):
        calls.append((method, endpoint, api_key))
        raise AssertionError("disabled Sender policy reached the transport boundary")

    monkeypatch.setattr(sender_client.SenderRoutes, "_call", classmethod(fail_if_called))
    return calls


@pytest.mark.parametrize(
    ("operation", "expected"),
    [
        (
            "membership sync",
            lambda: sender_sync.sync_membership_to_sender(
                "membership-1", Membership(email="member@example.test", name="A", surname="B")
            ),
        ),
        (
            "participant sync with consent and event title",
            lambda: sender_sync.sync_participant_to_sender(
                "participant-1",
                EventParticipant(email="person@example.test", name="A", surname="B", newsletter_consent=True),
                "event-1",
                "Summer",
            ),
        ),
        (
            "participant sync without consent",
            lambda: sender_sync.sync_participant_to_sender(
                "participant-2",
                EventParticipant(email="person@example.test", name="A", surname="B", newsletter_consent=False),
                "event-1",
                "Summer",
            ),
        ),
        (
            "newsletter signup",
            lambda: sender_sync.sync_newsletter_signup_to_sender("news@example.test", "A B"),
        ),
        ("unsubscribe", lambda: sender_sync.unsubscribe_from_sender("person@example.test")),
        ("delete subscriber", lambda: sender_sync.delete_subscriber_from_sender("person@example.test")),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_sync_operations_skip_under_real_disabled_test_policy(
    operation, expected, disabled_sender_settings, sender_request_spy
):
    assert expected() is None
    assert sender_request_spy == []


@pytest.mark.parametrize(
    ("method", "args", "expected"),
    [
        ("upsert_subscriber", ("person@example.test",), None),
        ("get_subscriber", ("person@example.test",), None),
        ("update_subscriber", ("person@example.test", {"firstname": "Changed"}), None),
        ("delete_subscriber", ("person@example.test",), False),
        ("list_groups", (), None),
        ("create_group", ("Newsletter",), None),
        ("add_to_group", ("person@example.test", "group-1"), False),
        ("remove_from_group", ("person@example.test", "group-1"), False),
    ],
)
def test_direct_service_operations_cannot_bypass_disabled_policy(
    method, args, expected, disabled_sender_settings, sender_request_spy
):
    service = SenderService(api_key="fake-key", enabled=True)

    assert service.enabled is False
    assert getattr(service, method)(*args) == expected
    assert sender_request_spy == []
