from __future__ import annotations

from dto.message_api import ContactFormRequestDTO, ContactMessageResponseDTO
from models import ContactMessage


def contact_form_dto_to_model(dto: ContactFormRequestDTO, *, timestamp) -> ContactMessage:
    return ContactMessage(
        name=dto.name,
        email=str(dto.email),
        message=dto.message,
        subject=dto.subject,
        answered=False,
        participant_id=dto.participant_id,
        event_id=dto.event_id,
        error_message=dto.error_message,
        timestamp=timestamp,
    )


def contact_message_to_response(message: ContactMessage) -> ContactMessageResponseDTO:
    return ContactMessageResponseDTO(
        id=message.id,
        name=message.name,
        email=message.email,
        message=message.message,
        subject=message.subject,
        answered=message.answered,
        participant_id=message.participant_id,
        event_id=message.event_id,
        error_message=message.error_message,
        timestamp=message.timestamp,
    )
