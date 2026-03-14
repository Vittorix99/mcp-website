from datetime import datetime, timedelta

from dto import ContactMessageDTO, EventParticipantDTO, MembershipDTO
from models import Event, Purchase
from services.core.stats_service import StatsService


class _DummyMembershipRepo:
    def __init__(self, stream_items=None, last=None):
        self._stream = stream_items or []
        self._last = last

    def stream(self):
        return iter(self._stream)

    def get_last_by_start_date(self):
        return self._last


class _DummyPurchaseRepo:
    def __init__(self, models=None, last=None):
        self._models = models or []
        self._last = last

    def stream_models(self):
        return iter(self._models)

    def get_last_by_timestamp(self):
        return self._last


class _DummyParticipantRepo:
    def __init__(self, participants=None, last=None):
        self._participants = participants or []
        self._last = last

    def list(self, event_id):
        return self._participants

    def get_last_across_events(self):
        return self._last


class _DummyEventRepo:
    def __init__(self, models=None):
        self._models = models or []

    def stream_models(self):
        return iter(self._models)


class _DummyMessageRepo:
    def __init__(self, count=0, last=None):
        self._count = count
        self._last = last

    def count_unanswered_since(self, time_limit):
        return self._count

    def get_last_dto(self):
        return self._last


def _make_service():
    service = StatsService()
    return service


def test_get_general_stats_happy_path():
    """Computes totals and last entities."""
    service = _make_service()
    today = datetime.now().date()
    event1 = Event(title="Event 1", date=(today + timedelta(days=1)).strftime("%d-%m-%Y"))
    event1.id = "evt-1"
    event2 = Event(title="Event 2", date=(today + timedelta(days=2)).strftime("%d-%m-%Y"))
    event2.id = "evt-2"
    service.event_repository = _DummyEventRepo(models=[event2, event1])

    member1 = MembershipDTO(name="A", subscription_valid=True)
    member2 = MembershipDTO(name="B", subscription_valid=False)
    service.membership_repository = _DummyMembershipRepo(
        stream_items=[member1, member2],
        last=MembershipDTO(name="Last"),
    )

    purchase1 = Purchase(amount_total="30.0", net_amount="20.0")
    purchase1.id = "pur-1"
    purchase2 = Purchase(amount_total="abc", net_amount=None)
    purchase2.id = "pur-2"
    service.purchase_repository = _DummyPurchaseRepo(
        models=[purchase1, purchase2],
        last=purchase1,
    )

    participant1 = EventParticipantDTO(event_id="evt-1", price=10)
    participant2 = EventParticipantDTO(event_id="evt-1", price="5.5")
    service.participant_repository = _DummyParticipantRepo(
        participants=[participant1, participant2],
        last=EventParticipantDTO(event_id="evt-x", name="Last"),
    )

    service.message_repository = _DummyMessageRepo(
        count=3,
        last=ContactMessageDTO(name="Hello", email="a@b.com", message="hi"),
    )

    payload = service.get_general_stats()

    assert payload["total_active_members"] == 1
    assert payload["total_purchases"] == 2
    assert payload["total_events"] == 2
    assert payload["upcoming_event_participants"] == 2
    assert payload["upcoming_event_total_paid"] == "15.50"
    assert payload["total_gross_amount"] == "30.00"
    assert payload["total_net_amount"] == "20.00"
    assert payload["last_24h_unanswered_messages"] == 3
    assert payload["last_message"]["name"] == "Hello"
    assert payload["last_membership"]["name"] == "Last"
    assert payload["last_purchase"]["id"] == "pur-1"


def test_get_general_stats_no_upcoming_event():
    """Handles no upcoming events."""
    service = _make_service()
    past_event = Event(title="Past", date="01-01-2000")
    service.event_repository = _DummyEventRepo(models=[past_event])
    service.membership_repository = _DummyMembershipRepo()
    service.purchase_repository = _DummyPurchaseRepo()
    service.participant_repository = _DummyParticipantRepo()
    service.message_repository = _DummyMessageRepo()

    payload = service.get_general_stats()
    assert payload["upcoming_event_participants"] == 0
    assert payload["upcoming_event_total_paid"] == "0.00"
