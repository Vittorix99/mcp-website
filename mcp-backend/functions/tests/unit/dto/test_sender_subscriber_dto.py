from dto.sender_subscriber import SenderSubscriberDTO, SubscriberSource
from models.event_participant import EventParticipant
from models.membership import Membership


class TestFromMembership:
    """Unit tests for SenderSubscriberDTO.from_membership."""

    def test_email_lowercased(self):
        membership = Membership(email="MARIO@TEST.COM")
        dto = SenderSubscriberDTO.from_membership("m1", membership)
        assert dto.email == "mario@test.com"

    def test_source_is_member(self):
        membership = Membership(email="x@test.com")
        dto = SenderSubscriberDTO.from_membership("m1", membership)
        assert dto.source == SubscriberSource.MEMBER

    def test_fields_mapped(self):
        membership = Membership(email="x@test.com", name="Mario", surname="Rossi", phone="123")
        dto = SenderSubscriberDTO.from_membership("m1", membership)
        assert dto.membership_id == "m1"
        assert dto.firstname == "Mario"
        assert dto.lastname == "Rossi"
        assert dto.phone == "123"

    def test_missing_phone_is_none(self):
        membership = Membership(email="x@test.com", name="Mario", surname="Rossi", phone=None)
        dto = SenderSubscriberDTO.from_membership("m1", membership)
        assert dto.phone is None


class TestFromParticipant:
    """Unit tests for SenderSubscriberDTO.from_participant."""

    def test_source_is_ticket_buyer(self):
        participant = EventParticipant(email="x@test.com")
        dto = SenderSubscriberDTO.from_participant("p1", participant, "event-1")
        assert dto.source == SubscriberSource.TICKET_BUYER

    def test_event_id_set(self):
        participant = EventParticipant(email="x@test.com")
        dto = SenderSubscriberDTO.from_participant("p1", participant, "event-1")
        assert dto.event_id == "event-1"

    def test_membership_id_set_if_present(self):
        participant = EventParticipant(email="x@test.com", membership_id="m1")
        dto = SenderSubscriberDTO.from_participant("p1", participant, "event-1")
        assert dto.membership_id == "m1"

    def test_newsletter_consent_ignored(self):
        participant = EventParticipant(email="x@test.com", newsletter_consent=False)
        dto = SenderSubscriberDTO.from_participant("p1", participant, "event-1")
        assert dto.email == "x@test.com"


class TestFromNewsletterSignup:
    """Unit tests for SenderSubscriberDTO.from_newsletter_signup."""

    def test_source_is_newsletter(self):
        dto = SenderSubscriberDTO.from_newsletter_signup("x@test.com", "Mario Rossi")
        assert dto.source == SubscriberSource.NEWSLETTER

    def test_name_split(self):
        dto = SenderSubscriberDTO.from_newsletter_signup("x@test.com", "Alice Bianchi")
        assert dto.firstname == "Alice"
        assert dto.lastname is None

    def test_name_none_ok(self):
        dto = SenderSubscriberDTO.from_newsletter_signup("x@test.com", None)
        assert dto.firstname is None

    def test_email_lowercased(self):
        dto = SenderSubscriberDTO.from_newsletter_signup("MARIO@TEST.COM", "Mario")
        assert dto.email == "mario@test.com"


class TestToSenderFields:
    """Unit tests for DTO -> Sender custom fields mapping."""

    def test_returns_source_even_without_other_custom_fields(self):
        dto = SenderSubscriberDTO(
            email="x@test.com",
            source=SubscriberSource.NEWSLETTER,
            membership_id=None,
            event_id=None,
        )
        assert dto.to_sender_fields() == {"source": "newsletter"}

    def test_returns_dict_with_membership_id(self):
        dto = SenderSubscriberDTO(
            email="x@test.com",
            source=SubscriberSource.MEMBER,
            membership_id="X",
        )
        assert dto.to_sender_fields()["membership_id"] == "X"

    def test_returns_dict_with_event_id(self):
        dto = SenderSubscriberDTO(
            email="x@test.com",
            source=SubscriberSource.TICKET_BUYER,
            event_id="Y",
        )
        assert dto.to_sender_fields()["event_id"] == "Y"

    def test_includes_source(self):
        dto = SenderSubscriberDTO(
            email="x@test.com",
            source=SubscriberSource.TICKET_BUYER,
            event_id="Y",
        )
        assert dto.to_sender_fields()["source"] == "ticket_buyer"


class TestToUpsertKwargs:
    """Unit tests for kwargs generation used by SenderService.upsert_subscriber."""

    def test_contains_email(self):
        dto = SenderSubscriberDTO(email="x@test.com", source=SubscriberSource.NEWSLETTER)
        kwargs = dto.to_upsert_kwargs(groups=["g1"])
        assert kwargs["email"] == "x@test.com"

    def test_groups_passed_through(self):
        dto = SenderSubscriberDTO(email="x@test.com", source=SubscriberSource.NEWSLETTER)
        kwargs = dto.to_upsert_kwargs(groups=["g1"])
        assert kwargs["groups"] == ["g1"]

    def test_fields_from_to_sender_fields(self):
        dto = SenderSubscriberDTO(email="x@test.com", source=SubscriberSource.MEMBER, membership_id="X")
        kwargs = dto.to_upsert_kwargs(groups=None)
        assert kwargs["fields"]["membership_id"] == "X"

    def test_no_fields_key_if_none(self):
        dto = SenderSubscriberDTO(email="x@test.com", source=SubscriberSource.NEWSLETTER)
        kwargs = dto.to_upsert_kwargs(groups=None)
        assert "fields" in kwargs
        assert kwargs["fields"] == {"source": "newsletter"}
