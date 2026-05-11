"""Integration tests for MemberService — hits the Firestore emulator directly."""
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from errors.service_errors import NotFoundError, ValidationError
from models import EventParticipant, Membership, PaymentMethod, Purchase, PurchaseTypes
from services.memberships.member_service import MemberService


@pytest.fixture
def service(membership_repository, participant_repository, purchase_repository, events_service):
    mock_sender = MagicMock()
    return MemberService(
        membership_repository=membership_repository,
        participant_repository=participant_repository,
        purchase_repository=purchase_repository,
        sender_service=mock_sender,
    )


# ---------------------------------------------------------------------------
# get_me
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_get_me_returns_correct_dto(service, create_membership, member_email):
    """get_me returns a DTO with the correct name, email and subscription_valid."""
    create_membership(name="Anna", surname="Bianchi", subscription_valid=True)

    result = service.get_me(member_email, uid="")

    assert result.name == "Anna"
    assert result.surname == "Bianchi"
    assert result.email == member_email
    assert result.subscription_valid is True
    assert result.id


@pytest.mark.integration
def test_get_me_raises_not_found_for_unknown_email(service):
    """get_me raises NotFoundError when email has no matching membership."""
    with pytest.raises(NotFoundError):
        service.get_me("nonexistent@example.com", uid="")


@pytest.mark.integration
def test_get_me_raises_validation_error_for_empty_email(service):
    """get_me raises ValidationError when email is empty."""
    with pytest.raises(ValidationError):
        service.get_me("", uid="")


@pytest.mark.integration
def test_get_me_self_heals_uid(service, create_membership, member_email, membership_repository):
    """get_me writes the uid into the membership document if it was missing."""
    membership_id = create_membership()

    service.get_me(member_email, uid="new-uid-123")

    updated = membership_repository.get(membership_id)
    assert updated.uid == "new-uid-123"


# ---------------------------------------------------------------------------
# get_attended_events
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_get_attended_events_returns_events(
    service, create_membership, create_event, membership_repository, member_email
):
    """Returns attended events list after linking event to membership."""
    membership_id = create_membership()
    event_id = create_event()
    membership_repository.add_attended_event(membership_id, event_id)

    result = service.get_attended_events(member_email, uid="")

    ids = [e.id for e in result]
    assert event_id in ids
    entry = next(e for e in result if e.id == event_id)
    assert entry.title
    assert entry.date


@pytest.mark.integration
def test_get_attended_events_returns_empty_list(service, create_membership, member_email):
    """Fresh membership with no attended events returns empty list."""
    create_membership(attended_events=[])

    result = service.get_attended_events(member_email, uid="")

    assert result == []


@pytest.mark.integration
def test_get_attended_events_skips_nonexistent_event(
    service, create_membership, membership_repository, member_email
):
    """Event IDs that no longer exist in Firestore are silently skipped."""
    membership_id = create_membership()
    membership_repository.add_attended_event(membership_id, "ghost-event-id")

    result = service.get_attended_events(member_email, uid="")

    assert result == []


# ---------------------------------------------------------------------------
# get_purchases
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_get_purchases_returns_correct_data(
    service, create_membership, membership_repository, purchase_repository, member_email
):
    """Returns purchase data with amount, currency and event_title when available."""
    membership_id = create_membership()
    suffix = uuid4().hex[:8]
    purchase = Purchase(
        payer_name="Mario",
        payer_surname="Rossi",
        payer_email=member_email,
        amount_total="12.50",
        currency="EUR",
        transaction_id=f"txn-{suffix}",
        order_id=f"order-{suffix}",
        status="COMPLETED",
        purchase_type=PurchaseTypes.EVENT,
        ref_id=f"event-{suffix}",
        payment_method="website",
        capture_status="COMPLETED",
    )
    purchase_id = purchase_repository.create_from_model(purchase)

    try:
        membership_repository.add_attended_event_and_purchase(membership_id, f"event-{suffix}", purchase_id)
        result = service.get_purchases(member_email, uid="")

        ids = [p.id for p in result]
        assert purchase_id in ids

        entry = next(p for p in result if p.id == purchase_id)
        assert entry.amount_total == "12.50"
        assert entry.currency == "EUR"
        assert entry.type == PurchaseTypes.EVENT.value
    finally:
        purchase_repository.delete(purchase_id)


@pytest.mark.integration
def test_get_purchases_returns_empty_list(service, create_membership, member_email):
    """Fresh membership with no purchases returns empty list."""
    create_membership(purchases=[])

    result = service.get_purchases(member_email, uid="")

    assert result == []


# ---------------------------------------------------------------------------
# get_ticket
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_get_ticket_is_participant(
    service, create_membership, create_event, create_participant, member_email
):
    """Returns is_participant=True when participant is linked via membership_id."""
    membership_id = create_membership()
    event_id = create_event()
    create_participant(event_id, membership_id)

    result = service.get_ticket(member_email, uid="", event_id=event_id)

    assert result.is_participant is True


@pytest.mark.integration
def test_get_ticket_not_participant(
    service, create_membership, create_event, member_email
):
    """Returns is_participant=False when no participant exists for this membership."""
    create_membership()
    event_id = create_event()

    result = service.get_ticket(member_email, uid="", event_id=event_id)

    assert result.is_participant is False
    assert result.ticket_pdf_url is None


# ---------------------------------------------------------------------------
# patch_preferences
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_patch_preferences_sets_false(
    service, create_membership, membership_repository, member_email
):
    """patch_preferences(False) updates newsletter_consent to False in Firestore."""
    membership_id = create_membership(newsletter_consent=True)

    result = service.patch_preferences(member_email, uid="", newsletter_consent=False)

    assert result.get("success") is True
    updated = membership_repository.get(membership_id)
    assert updated.newsletter_consent is False


@pytest.mark.integration
def test_patch_preferences_sets_true(
    service, create_membership, membership_repository, member_email
):
    """patch_preferences(True) updates newsletter_consent to True in Firestore."""
    membership_id = create_membership(newsletter_consent=False)

    service.patch_preferences(member_email, uid="", newsletter_consent=True)

    updated = membership_repository.get(membership_id)
    assert updated.newsletter_consent is True
