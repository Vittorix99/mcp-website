import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from firebase_admin import firestore

from dto import EventDTO
from interfaces.repositories import EventRepositoryProtocol, ParticipantRepositoryProtocol
from models import Event
from repositories.event_repository import EventRepository
from repositories.participant_repository import ParticipantRepository
from errors.service_errors import NotFoundError, ValidationError
from utils.events_utils import map_purchase_mode

logger = logging.getLogger("EventsService")


class EventsService:
    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
    ):
        self.logger = logger
        self.event_repository = event_repository or EventRepository()
        self.participant_repository = participant_repository or ParticipantRepository()

    # ----------------------- Date helpers -----------------------
    def _normalize_date_string(self, date_str: str) -> str:
        """
        Accepts DD-MM-YYYY, DD/MM/YYYY, or YYYY-MM-DD and returns a normalized DD-MM-YYYY string.
        """
        if not date_str:
            raise ValidationError("Invalid date format. Use DD-MM-YYYY")

        value = str(date_str).strip()
        candidates = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"]
        for fmt in candidates:
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed.strftime("%d-%m-%Y")
            except ValueError:
                continue

        raise ValidationError("Invalid date format. Use DD-MM-YYYY")

    def _safe_parse_date(self, date_str: str):
        """
        Try to parse a stored date (accepting both '-' and '/' just in case of legacy data).
        Returns a date object or None.
        """
        if not date_str:
            return None
        value = str(date_str).strip()
        for fmt in ["%d-%m-%Y", "%d/%m/%Y"]:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    # ----------------------- Model helpers -----------------------
    def _event_to_dict(self, event: Event) -> Dict[str, Any]:
        dto = EventDTO.from_model(event)
        return dto.to_payload()

    def _shape_public_event(self, dto: EventDTO, view: Optional[str]):
        return dto.public_payload(view)

    def _apply_dto_to_event(
        self,
        event: Event,
        dto: EventDTO,
        fields_to_apply: Optional[Set[str]] = None,
    ) -> None:
        fields = fields_to_apply or dto.resolve_fields_to_apply(None, False)

        for attr in fields:
            value = getattr(dto, attr, None)
            if attr == "date" and value:
                value = self._normalize_date_string(value)
            if attr in {"price", "fee"} and value is not None:
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    raise ValidationError(f"Invalid value for {attr}")
            if attr == "max_participants" and value is not None:
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    raise ValidationError("Invalid maxParticipants format")
            if attr == "purchase_mode" and value is not None:
                value = map_purchase_mode(value)
            setattr(event, attr, value)

    # ----------------------- Admin helpers -----------------------
    def _validate_event_dto(self, dto: EventDTO, is_update: bool) -> Set[str]:
        fields_to_apply = dto.resolve_fields_to_apply(None, is_update)
        self.logger.debug(
            "_validate_event_dto called. is_update=%s, fields=%s", is_update, sorted(fields_to_apply)
        )
        error = dto.validate(
            fields_to_apply,
            is_update=is_update,
            normalize_date=self._normalize_date_string,
        )
        if error:
            raise ValidationError(error)

        return fields_to_apply

    # ----------------------- Admin actions -----------------------
    def create_event(self, event_dto: EventDTO, admin_uid: str) -> Dict[str, Any]:
        self.logger.debug(f"create_event by admin {admin_uid}")
        fields_to_apply = self._validate_event_dto(event_dto, is_update=False)

        event = Event(
            participants_count=0,
            created_at=firestore.SERVER_TIMESTAMP,
            created_by=admin_uid,
        )
        self._apply_dto_to_event(event, event_dto, fields_to_apply)

        slug_seed = f"{event.title} {event.date}".strip()
        event_id = self.event_repository.create_from_model(event, slug_seed)
        self.logger.info("Event created: %s", event_id)

        return {"message": "Event created", "eventId": event_id}

    def update_event(
        self,
        event_id: str,
        event_dto: EventDTO,
        admin_uid: str,
    ) -> Dict[str, Any]:
        self.logger.debug(f"update_event {event_id} by {admin_uid}")
        fields_to_apply = self._validate_event_dto(event_dto, is_update=True)

        event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError("Event not found")

        self._apply_dto_to_event(event, event_dto, fields_to_apply)
        event.updated_at = firestore.SERVER_TIMESTAMP
        event.updated_by = admin_uid

        self.event_repository.update_from_model(event_id, event)

        self.logger.info("Event %s updated", event_id)
        return {"message": "Event updated", "eventId": event_id}

    def delete_event(self, event_id: str, admin_uid: str) -> Dict[str, Any]:
        self.logger.debug(f"delete_event {event_id} by {admin_uid}")
        event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError("Event not found")

        self.event_repository.delete(event_id)
        self.logger.info("Event %s deleted", event_id)
        return {"message": "Event deleted", "eventId": event_id}

    def get_all_events(self) -> List[Dict[str, Any]]:
        self.logger.debug("get_all_events")
        events_list: List[Dict[str, Any]] = []

        for event in self.event_repository.stream_models():
            event.participants_count = self.get_event_participants_count(event.id)
            event_dict = self._event_to_dict(event)
            events_list.append(event_dict)

        self.logger.info("Fetched %s events", len(events_list))
        return events_list

    def get_event_by_id(self, event_id: Optional[str] = None, slug: Optional[str] = None) -> Dict[str, Any]:
        self.logger.debug(f"get_event_by_id {event_id}")
        model = None
        if slug:
            model = self.event_repository.get_model_by_slug(slug)
        if model is None and event_id:
            model = self.event_repository.get_model(event_id)
        if not model:
            raise NotFoundError("Event not found")
        event_payload = self._event_to_dict(model)
        return {"event": event_payload}

    def get_event_participants_count(self, event_id: str) -> int:
        return self.participant_repository.count(event_id)

    # ----------------------- Public endpoints -----------------------
    def list_public_events(self, view: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all events for the public site."""
        events_list = []
        for model in self.event_repository.stream_models():
            dto = EventDTO.from_model(model)
            events_list.append(self._shape_public_event(dto, view))
        return events_list

    def list_upcoming_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return upcoming events ordered by date (public data)."""
        events = []
        for model in self.event_repository.stream_models():
            if not model.date:
                continue
            event_date = self._safe_parse_date(model.date)
            if not event_date:
                continue
            if event_date >= datetime.now().date():
                events.append((event_date, model))

        events.sort(key=lambda item: item[0])
        limited = events[:limit] if limit else events
        payload = [self._event_to_dict(model) for _, model in limited]
        return payload

    def get_next_public_event(self) -> List[Dict[str, Any]]:
        today = datetime.now().date()
        events = [model for model in self.event_repository.stream_models()]

        def parse_date(event: Event):
            return self._safe_parse_date(event.date)

        future_events = [evt for evt in events if evt.date]
        sorted_events = sorted(future_events, key=parse_date)
        upcoming_events = [
            self._event_to_dict(model)
            for model in sorted_events
            if parse_date(model) and parse_date(model) >= today
        ]

        return upcoming_events

    def get_public_event_by_id(self, event_id: Optional[str] = None, slug: Optional[str] = None) -> Dict[str, Any]:
        model = None
        if slug:
            model = self.event_repository.get_model_by_slug(slug)
        if model is None and event_id:
            model = self.event_repository.get_model(event_id)

        if not model:
            raise NotFoundError("Event not found")

        payload = self._event_to_dict(model)
        return payload
