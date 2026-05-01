from __future__ import annotations

from firebase_admin import firestore

from dto.event_api import (
    AdminEventResponseDTO,
    CreateEventRequestDTO,
    PublicEventResponseDTO,
    UpdateEventRequestDTO,
)
from models import Event


def create_event_dto_to_model(dto: CreateEventRequestDTO, admin_uid: str) -> Event:
    return Event(
        title=dto.title,
        date=dto.date,
        start_time=dto.start_time,
        end_time=dto.end_time,
        location=dto.location,
        location_hint=dto.location_hint,
        price=dto.price,
        fee=dto.fee,
        max_participants=dto.max_participants,
        status=dto.status,
        image=dto.image,
        lineup=dto.lineup,
        note=dto.note,
        photo_path=dto.photo_path,
        purchase_mode=dto.purchase_mode,
        allow_duplicates=dto.allow_duplicates,
        over21_only=dto.over21_only,
        only_females=dto.only_females,
        participants_count=0,
        external_link=dto.external_link,
        created_by=admin_uid,
        created_at=firestore.SERVER_TIMESTAMP,
    )


def apply_event_update_dto_to_model(event: Event, dto: UpdateEventRequestDTO, admin_uid: str) -> Event:
    for field_name, value in dto.changes().items():
        setattr(event, field_name, value)
    event.updated_at = firestore.SERVER_TIMESTAMP
    event.updated_by = admin_uid
    return event


def event_to_admin_response(event: Event) -> AdminEventResponseDTO:
    return AdminEventResponseDTO(
        id=event.id,
        title=event.title,
        slug=event.slug,
        date=event.date,
        start_time=event.start_time,
        end_time=event.end_time,
        location_hint=event.location_hint,
        location=event.location,
        price=event.price,
        fee=event.fee,
        max_participants=event.max_participants,
        status=event.status,
        image=event.image,
        lineup=event.lineup or [],
        note=event.note,
        photo_path=event.photo_path,
        purchase_mode=event.purchase_mode,
        allow_duplicates=event.allow_duplicates,
        over21_only=event.over21_only,
        only_females=event.only_females,
        participants_count=event.participants_count,
        external_link=event.external_link,
        created_at=event.created_at,
        created_by=event.created_by,
        updated_at=event.updated_at,
        updated_by=event.updated_by,
    )


def event_to_public_response(event: Event) -> PublicEventResponseDTO:
    return PublicEventResponseDTO(
        id=event.id,
        slug=event.slug,
        title=event.title,
        date=event.date,
        start_time=event.start_time,
        end_time=event.end_time,
        location_hint=event.location_hint,
        price=event.price,
        fee=event.fee,
        status=event.status,
        image=event.image,
        lineup=event.lineup or [],
        note=event.note,
        photo_path=event.photo_path,
        purchase_mode=event.purchase_mode,
        allow_duplicates=event.allow_duplicates,
        over21_only=event.over21_only,
        only_females=event.only_females,
        external_link=event.external_link,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )

