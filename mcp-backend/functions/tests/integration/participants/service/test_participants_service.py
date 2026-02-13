import pytest

from services.service_errors import ConflictError, ForbiddenError, ValidationError


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
        result = participants_service.create(payload)
        participant_id = result.get("id")
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
        participants_service.create(payload)


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
        participants_service.create(payload)


@pytest.mark.integration
def test_participant_only_members_event_requires_membership(
    only_members_event,
    participants_service,
    participant_payload,
):
    """Requires active membership for ONLY_MEMBERS events."""
    payload = dict(participant_payload, event_id=only_members_event)
    with pytest.raises(ForbiddenError):
        participants_service.create(payload)


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
        result = participants_service.create(payload)
        participant_id = result.get("id")
        assert participant_id

        with pytest.raises(ValidationError) as exc:
            participants_service.check_participants(event_id, [participant_payload])
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
        participants_service.check_participants(event_id, [participant_payload, dup])
    details = getattr(exc.value, "details", None) or []
    assert any("duplicati" in msg for msg in details)
