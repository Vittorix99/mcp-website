from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from domain.event_rules import EVENT_TIMEZONE, get_event_start_datetime, is_event_finished
from dto.event_api import (
    AdminEventEnvelopeResponseDTO,
    AdminEventResponseDTO,
    CreateEventRequestDTO,
    EventActionResponseDTO,
    PublicEventResponseDTO,
    UpdateEventRequestDTO,
)
from errors.service_errors import NotFoundError
from interfaces.repositories import EventRepositoryProtocol, ParticipantRepositoryProtocol
from models import EventStatus
from repositories.event_repository import EventRepository
from repositories.participant_repository import ParticipantRepository
from mappers.event_mappers import (
    apply_event_update_dto_to_model,
    create_event_dto_to_model,
    event_to_admin_response,
    event_to_public_response,
)


class EventsService:
    """
    Single service layer for the events domain.
    Authorization concerns stay in the API layer; this service only handles
    business logic, domain models and orchestration with repositories.
    """

    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
    ):
        self.event_repository = event_repository or EventRepository()
        self.participant_repository = participant_repository or ParticipantRepository()

    def create_event(self, dto: CreateEventRequestDTO, admin_uid: str) -> EventActionResponseDTO:
        event = create_event_dto_to_model(dto, admin_uid)
        slug_seed = f"{event.title} {event.date}".strip()
        event_id = self.event_repository.create_from_model(event, slug_seed)
        return EventActionResponseDTO(message="Event created", event_id=event_id)

    def update_event(self, dto: UpdateEventRequestDTO, admin_uid: str) -> EventActionResponseDTO:
        event = self.event_repository.get_model(dto.id)
        if not event:
            raise NotFoundError("Event not found")

        updated_event = apply_event_update_dto_to_model(event, dto, admin_uid)
        self.event_repository.update_from_model(dto.id, updated_event)
        return EventActionResponseDTO(message="Event updated", event_id=dto.id)

    def delete_event(self, event_id: str, admin_uid: str) -> EventActionResponseDTO:
        del admin_uid
        event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError("Event not found")

        self.event_repository.delete(event_id)
        return EventActionResponseDTO(message="Event deleted", event_id=event_id)

    def get_all_events(self) -> List[AdminEventResponseDTO]:
        events_list: List[AdminEventResponseDTO] = []
        for event in self.event_repository.stream_models():
            event.participants_count = self.participant_repository.count(event.id)
            events_list.append(event_to_admin_response(event))
        return events_list

    def get_event_by_id(
        self,
        event_id: Optional[str] = None,
        slug: Optional[str] = None,
    ) -> AdminEventEnvelopeResponseDTO:
        event = None
        if slug:
            event = self.event_repository.get_model_by_slug(slug)
        if event is None and event_id:
            event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError("Event not found")

        if event.id:
            event.participants_count = self.participant_repository.count(event.id)
        return AdminEventEnvelopeResponseDTO(event=event_to_admin_response(event))

    def list_public_events(self) -> List[PublicEventResponseDTO]:
        return [event_to_public_response(model) for model in self.event_repository.stream_models()]

    def list_upcoming_events(self, limit: int = 5) -> List[PublicEventResponseDTO]:
        now = datetime.now(EVENT_TIMEZONE)
        upcoming = []
        for model in self.event_repository.stream_models():
            if model.status == EventStatus.ENDED:
                continue
            start_dt = get_event_start_datetime(model, tzinfo=now.tzinfo)
            if not start_dt or is_event_finished(model, now=now):
                continue
            upcoming.append((start_dt, model))

        upcoming.sort(key=lambda item: item[0])
        if limit:
            upcoming = upcoming[:limit]
        return [event_to_public_response(model) for _, model in upcoming]

    def get_next_public_event(self) -> List[PublicEventResponseDTO]:
        return self.list_upcoming_events(limit=0)

    def get_public_event_by_id(
        self,
        event_id: Optional[str] = None,
        slug: Optional[str] = None,
    ) -> PublicEventResponseDTO:
        event = None
        if slug:
            event = self.event_repository.get_model_by_slug(slug)
        if event is None and event_id:
            event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError("Event not found")
        return event_to_public_response(event)
