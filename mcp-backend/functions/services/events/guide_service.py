import logging
import uuid
from typing import Any, Dict, List, Optional

from dto.event_api import UpdateEventGuideRequestDTO
from errors.service_errors import NotFoundError
from interfaces.repositories import EventRepositoryProtocol
from models.event_guide import EventGuide
from repositories import EventRepository
from repositories.event_guide_repository import EventGuideRepository

logger = logging.getLogger("GuideService")


class GuideService:
    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        guide_repository: Optional[EventGuideRepository] = None,
    ) -> None:
        self.event_repository = event_repository or EventRepository()
        self.guide_repository = guide_repository or EventGuideRepository()

    def _require_event(self, event_id: str):
        if not self.event_repository.get_model(event_id):
            raise NotFoundError(f"Event {event_id} not found")

    def get_admin_guide(self, event_id: str) -> Dict[str, Any]:
        """Returns guide sections + published flag for admin editing."""
        self._require_event(event_id)
        guide = self.guide_repository.get(event_id)
        return {
            "published": bool(guide.published) if guide else False,
            "sections": list(guide.sections) if guide else [],
        }

    def upsert_guide(self, dto: UpdateEventGuideRequestDTO) -> None:
        """Save sections + published to event_guides."""
        self._require_event(dto.event_id)

        sections = []
        for s in dto.guide.sections:
            section = s.model_dump()
            if not section.get("id"):
                section["id"] = str(uuid.uuid4())
            sections.append(section)

        guide_model = EventGuide(published=dto.guide.published, sections=sections)
        self.guide_repository.replace(dto.event_id, guide_model)
        logger.info("upsert_guide: guide saved for event %s", dto.event_id)

    def set_published(self, event_id: str, published: bool) -> None:
        """Update only the published flag in event_guides."""
        self._require_event(event_id)
        self.guide_repository.set_published(event_id, published)
        logger.info("set_published: event %s published=%s", event_id, published)

    def get_public_guide(
        self,
        event_id: Optional[str] = None,
        slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Returns public-safe guide payload (sections only, no location). Raises NotFoundError if unpublished."""
        if event_id:
            event = self.event_repository.get_model(event_id)
        elif slug:
            event = self.event_repository.get_model_by_slug(slug)
        else:
            raise ValueError("event_id or slug required")

        if not event:
            raise NotFoundError("Event not found")

        resolved_id = event.id
        guide = self.guide_repository.get(resolved_id)
        if not guide or not guide.published:
            raise NotFoundError("Guide not available")

        sections = [
            {
                "id": s.get("id", ""),
                "type": s.get("type", "text"),
                "title": s.get("title", ""),
                "content": s.get("content", ""),
                "order": s.get("order", 0),
            }
            for s in (guide.sections or [])
            if s.get("visible", True)
        ]
        sections.sort(key=lambda s: s["order"])

        return {
            "event_id": resolved_id,
            "event_slug": event.slug or "",
            "event_title": event.title or "",
            "event_date": str(event.date or ""),
            "event_start_time": event.start_time or "",
            "location_hint": event.location_hint or "",
            "lineup": list(event.lineup or []),
            "guide": {
                "sections": sections,
            },
        }
