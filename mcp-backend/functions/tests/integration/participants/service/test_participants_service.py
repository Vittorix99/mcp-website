import pytest

from dto.participant_api import CheckoutParticipantRequestDTO, ParticipantCreateRequestDTO
from errors.service_errors import ConflictError, ForbiddenError, ValidationError


def _create_dto(payload):
    return ParticipantCreateRequestDTO.model_validate(payload)


def _checkout_dto(payload):
    allowed = {
        "name",
        "surname",
        "email",
        "phone",
        "birthdate",
        "newsletterConsent",
        "newsletter_consent",
        "gender",
        "genderProbability",
        "gender_probability",
    }
    return CheckoutParticipantRequestDTO.model_validate({key: value for key, value in payload.items() if key in allowed})


@pytest.mark.integration
def test_participant_create_and_count(
    create_event,
    participants_service,
    participant_repository,
    participant_payload,
):
    """Creates a participant and confirms repository count increments."""
    event_id = create_event()
    payload = dict(participant_payload, event_id=event_id)
    participant_id = None
    try:
        result = participants_service.create(_create_dto(payload))
        participant_id = result.id
        assert participant_id

        count = participant_repository.count(event_id)
        assert count == 1
    finally:
        if participant_id:
            participants_service.delete(event_id, participant_id)


@pytest.mark.integration
def test_participant_create_rejects_minor(
    create_event,
    participants_service,
    minor_participant_payload,
):
    """Rejects minors during participant creation."""
    event_id = create_event()
    payload = dict(minor_participant_payload, event_id=event_id)
    with pytest.raises(ForbiddenError):
        participants_service.create(_create_dto(payload))


@pytest.mark.integration
def test_participant_membership_included_conflict(
    create_event,
    participants_service,
    participant_payload,
    member_record,
):
    """Rejects membership_included when member is already active."""
    event_id = create_event()
    payload = dict(participant_payload, event_id=event_id, membership_included=True)
    with pytest.raises(ConflictError):
        participants_service.create(_create_dto(payload))


@pytest.mark.integration
def test_participant_create_with_explicit_membership_id(
    create_event,
    participants_service,
    participant_repository,
    participant_payload,
    member_record,
):
    """Links an existing membership explicitly without triggering renewal conflict."""
    event_id = create_event()
    participant_id = None
    payload = dict(
        participant_payload,
        event_id=event_id,
        membership_id=member_record,
        membership_included=False,
    )
    try:
        result = participants_service.create(_create_dto(payload))
        participant_id = result.id
        assert participant_id

        saved = participant_repository.get(event_id, participant_id)
        assert saved is not None
        assert saved.membership_id == member_record
    finally:
        if participant_id:
            participants_service.delete(event_id, participant_id)


@pytest.mark.integration
def test_participant_only_members_event_requires_membership(
    only_members_event,
    participants_service,
    participant_payload,
):
    """Admin/manual create remains allowed; membership restrictions are checked in checkout validation."""
    payload = dict(participant_payload, event_id=only_members_event)
    participant_id = None
    try:
        result = participants_service.create(_create_dto(payload))
        participant_id = result.id
        assert participant_id
    finally:
        if participant_id:
            participants_service.delete(only_members_event, participant_id)


@pytest.mark.integration
def test_participant_check_detects_duplicate_in_db(
    create_event,
    participants_service,
    participant_payload,
):
    """Detects duplicate participant already stored for the event."""
    event_id = create_event()
    payload = dict(participant_payload, event_id=event_id)
    participant_id = None
    try:
        result = participants_service.create(_create_dto(payload))
        participant_id = result.id
        assert participant_id

        with pytest.raises(ValidationError) as exc:
            participants_service.check_participants(event_id, [_checkout_dto(participant_payload)])
        details = getattr(exc.value, "details", None) or []
        assert any("già acquistato" in msg or "duplicati" in msg for msg in details)
    finally:
        if participant_id:
            participants_service.delete(event_id, participant_id)


@pytest.mark.integration
def test_participant_check_detects_duplicate_in_payload(
    create_event,
    participants_service,
    participant_payload,
):
    """Detects duplicate participants within the same request payload."""
    event_id = create_event()
    dup = dict(participant_payload)
    dup["email"] = participant_payload["email"]
    dup["phone"] = participant_payload["phone"]

    with pytest.raises(ValidationError) as exc:
        participants_service.check_participants(event_id, [_checkout_dto(participant_payload), _checkout_dto(dup)])
    details = getattr(exc.value, "details", None) or []
    assert any("duplicati" in msg for msg in details)
