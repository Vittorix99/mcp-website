from __future__ import annotations

from dataclasses import replace

from dto.participant_api import ParticipantCreateRequestDTO, ParticipantResponseDTO, ParticipantUpdateRequestDTO
from models import EventParticipant, PaymentMethod


def create_participant_dto_to_model(
    dto: ParticipantCreateRequestDTO,
    *,
    email: str,
    phone: str,
    membership_id: str | None,
    membership_included: bool,
    payment_method: PaymentMethod,
    price: float | None,
    created_at,
) -> EventParticipant:
    return EventParticipant(
        event_id=dto.event_id,
        name=dto.name or "",
        surname=dto.surname or "",
        email=email,
        phone=phone,
        birthdate=dto.birthdate,
        membership_included=membership_included,
        membership_id=membership_id,
        payment_method=payment_method,
        ticket_sent=bool(dto.ticket_sent) if dto.ticket_sent is not None else False,
        location_sent=bool(dto.location_sent) if dto.location_sent is not None else False,
        newsletter_consent=bool(dto.newsletter_consent) if dto.newsletter_consent is not None else False,
        send_ticket_on_create=bool(dto.send_ticket_on_create) if dto.send_ticket_on_create is not None else False,
        price=price,
        purchase_id=dto.purchase_id,
        discount_code_id=dto.discount_code_id,
        discount_code=dto.discount_code,
        price_original=dto.price_original,
        riduzione=bool(dto.riduzione) if dto.riduzione is not None else False,
        gender=dto.gender,
        gender_probability=dto.gender_probability,
        created_at=created_at,
    )


def apply_participant_update_dto_to_model(
    participant: EventParticipant,
    dto: ParticipantUpdateRequestDTO,
) -> EventParticipant:
    for field_name, value in dto.changes().items():
        if field_name == "payment_method":
            participant.payment_method = PaymentMethod(value) if value is not None else participant.payment_method
            continue
        setattr(participant, field_name, value)
    return participant


def participant_to_response(participant: EventParticipant) -> ParticipantResponseDTO:
    return ParticipantResponseDTO(
        id=participant.id,
        event_id=participant.event_id,
        name=participant.name,
        surname=participant.surname,
        email=participant.email,
        phone=participant.phone,
        birthdate=participant.birthdate,
        membership_id=participant.membership_id,
        membership_included=participant.membership_included,
        entered=participant.entered,
        entered_at=participant.entered_at,
        ticket_pdf_url=participant.ticket_pdf_url,
        ticket_sent=participant.ticket_sent,
        send_ticket_on_create=participant.send_ticket_on_create,
        location_sent=participant.location_sent,
        location_sent_at=participant.location_sent_at,
        location_job_id=participant.location_job_id,
        omaggio_email_sent=participant.omaggio_email_sent,
        omaggio_email_sent_at=participant.omaggio_email_sent_at,
        gender=participant.gender,
        gender_probability=participant.gender_probability,
        newsletter_consent=participant.newsletter_consent,
        price=participant.price,
        payment_method=participant.payment_method.value if participant.payment_method else None,
        purchase_id=participant.purchase_id,
        discount_code_id=participant.discount_code_id,
        discount_code=participant.discount_code,
        price_original=participant.price_original,
        riduzione=participant.riduzione,
        created_at=participant.created_at,
    )


def mark_participant_location_sent(
    participant: EventParticipant,
    *,
    sent_at,
    job_id: str | None = None,
) -> EventParticipant:
    return replace(
        participant,
        location_sent=True,
        location_sent_at=sent_at,
        location_job_id=job_id,
    )
