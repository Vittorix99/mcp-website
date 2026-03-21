from uuid import uuid4

import pytest

from dto import MembershipDTO
from errors.service_errors import ConflictError, ForbiddenError, ValidationError


@pytest.mark.integration
def test_memberships_service_crud(
    memberships_service,
    membership_repository,
    membership_payload,
    create_membership,
):
    """Creates, fetches, updates, and deletes a membership."""
    membership_id = None
    try:
        membership_id = create_membership(membership_payload)
        fetched = memberships_service.get_by_id(membership_id)
        assert fetched.get("id") == membership_id

        update_phone = f"+39{uuid4().int % 10**10:010d}"
        update_dto = MembershipDTO.from_payload({"phone": update_phone})
        memberships_service.update(membership_id, update_dto)

        updated = membership_repository.get_model(membership_id)
        assert updated is not None
        assert updated.phone == update_phone
    finally:
        if membership_id:
            memberships_service.delete(membership_id)


@pytest.mark.integration
def test_memberships_service_create_duplicate_email(
    memberships_service,
    membership_payload,
    create_membership,
):
    """Rejects duplicate membership emails."""
    membership_id = None
    try:
        membership_id = create_membership(membership_payload)
        with pytest.raises(ConflictError):
            memberships_service.create(MembershipDTO.from_payload(membership_payload))
    finally:
        if membership_id:
            memberships_service.delete(membership_id)


@pytest.mark.integration
def test_memberships_service_rejects_minor(
    memberships_service,
    minor_membership_payload,
):
    """Rejects minors during membership creation."""
    with pytest.raises(ValidationError):
        memberships_service.create(MembershipDTO.from_payload(minor_membership_payload))


@pytest.mark.integration
def test_memberships_service_rejects_protected_update(
    memberships_service,
    membership_payload,
    create_membership,
):
    """Rejects updates on protected fields."""
    membership_id = create_membership(membership_payload)
    try:
        with pytest.raises(ForbiddenError):
            memberships_service.update(membership_id, MembershipDTO(card_url="forbidden"))
    finally:
        memberships_service.delete(membership_id)


@pytest.mark.integration
@pytest.mark.email
@pytest.mark.usefixtures("mailersend_api_key")
def test_memberships_service_send_card_sends_email(
    memberships_service,
    membership_repository,
    membership_payload,
    create_membership,
):
    """Sends membership email via MailerSend and updates membership flags."""
    membership_id = create_membership(membership_payload)
    try:
        result = memberships_service.send_card(membership_id)
        assert result.get("message") == "Card sent successfully"

        refreshed = membership_repository.get_model(membership_id)
        assert refreshed is not None
        assert refreshed.membership_sent is True
    finally:
        memberships_service.delete(membership_id)


@pytest.mark.integration
def test_memberships_service_get_purchases_and_events(
    memberships_service,
    membership_repository,
    membership_payload,
    create_membership,
    create_purchase,
    create_event,
):
    """Returns purchases and attended events linked to a membership."""
    membership_id = create_membership(membership_payload)
    try:
        purchase_id = create_purchase()
        event_id = create_event()

        membership_repository.update_from_model(
            membership_id,
            MembershipDTO(
                purchases=[purchase_id],
                attended_events=[event_id],
            ),
        )

        purchases = memberships_service.get_purchases(membership_id)
        assert any(item.get("id") == purchase_id for item in purchases)

        events = memberships_service.get_events(membership_id)
        assert any(item.get("id") == event_id for item in events)
    finally:
        memberships_service.delete(membership_id)
