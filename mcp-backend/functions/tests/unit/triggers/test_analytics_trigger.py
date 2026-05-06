import types

from triggers import analytics_trigger


class _Snap:
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return dict(self._data)


def test_on_purchase_written_enqueues_event_rebuild(monkeypatch):
    called = {}

    monkeypatch.setattr(
        analytics_trigger.analytics_snapshot_service,
        "enqueue_event_rebuild",
        lambda event_id, reason="": called.setdefault("payload", (event_id, reason)),
    )

    event = types.SimpleNamespace(
        data=types.SimpleNamespace(before=_Snap({"ref_id": "evt-old"}), after=_Snap({"ref_id": "evt-new"})),
        params={"purchaseId": "purchase-1"},
    )

    analytics_trigger.on_purchase_written.__wrapped__(event)

    assert called.get("payload")[0] == "evt-new"


def test_on_participant_written_enqueues_event_rebuild(monkeypatch):
    called = {}

    monkeypatch.setattr(
        analytics_trigger.analytics_snapshot_service,
        "enqueue_event_rebuild",
        lambda event_id, reason="": called.setdefault("event_id", event_id),
    )

    event = types.SimpleNamespace(data={}, params={"eventId": "evt-1", "participantId": "p-1"})
    analytics_trigger.on_participant_written.__wrapped__(event)

    assert called.get("event_id") == "evt-1"


def test_on_membership_written_enqueues_global_rebuild(monkeypatch):
    called = {}

    monkeypatch.setattr(
        analytics_trigger.analytics_snapshot_service,
        "enqueue_global_rebuild",
        lambda reason="": called.setdefault("called", True),
    )

    event = types.SimpleNamespace(data={}, params={"membershipId": "m-1"})
    analytics_trigger.on_membership_written.__wrapped__(event)

    assert called.get("called") is True
