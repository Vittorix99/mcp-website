from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import public_endpoint
from dto.event_api import EventLookupQueryDTO, EventViewQueryDTO
from services.events.events_service import EventsService
from utils.http_responses import handle_pydantic_error, handle_service_error

events_service = EventsService()


@public_endpoint(methods=("GET",))
def get_all_events(req):
    """API to get all events"""
    try:
        dto = EventViewQueryDTO.model_validate(dict(req.args or {}))
        events = events_service.list_public_events()
        return jsonify([event.to_view_payload(dto.view) for event in events]), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@public_endpoint(methods=("GET",))
def get_next_event(req):
    """API to get the next upcoming event"""
    try:
        events = events_service.get_next_public_event()
        return jsonify([event.to_payload() for event in events]), 200
    except Exception as err:
        return handle_service_error(err)


@public_endpoint(methods=("GET",))
def get_event_by_id(req):
    """API to get event details by ID"""
    try:
        dto = EventLookupQueryDTO.model_validate(dict(req.args or {}))
        event = events_service.get_public_event_by_id(dto.id, slug=dto.slug)
        return jsonify(event.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
