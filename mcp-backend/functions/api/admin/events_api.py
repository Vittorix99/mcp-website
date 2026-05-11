import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.event_api import (
    CreateEventRequestDTO,
    EventDeleteRequestDTO,
    EventGuideQueryDTO,
    EventLookupQueryDTO,
    ToggleGuidePublishedRequestDTO,
    UpdateEventGuideRequestDTO,
    UpdateEventRequestDTO,
)
from errors.service_errors import NotFoundError
from services.events.events_service import EventsService
from services.events.guide_service import GuideService
from utils.http_responses import handle_pydantic_error, handle_service_error
from utils.safe_logging import redact_sensitive

logger = logging.getLogger("AdminEventsAPI")
events_service = EventsService()
guide_service = GuideService()


@admin_endpoint(methods=("POST",))
def admin_create_event(req):
    logger.debug("admin_create_event called")

    try:
        dto = CreateEventRequestDTO.model_validate(req.get_json(silent=True) or {})
        admin_uid = req.admin_token["uid"]
        payload = events_service.create_event(dto, admin_uid)
        logger.info("Event created successfully")
        return jsonify(payload.to_payload()), 201
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_create_event] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("PUT",))
def admin_update_event(req):
    logger.debug("admin_update_event called")

    try:
        dto = UpdateEventRequestDTO.model_validate(req.get_json(silent=True) or {})
        admin_uid = req.admin_token["uid"]
        payload = events_service.update_event(dto, admin_uid)
        logger.info("Event %s updated successfully", dto.id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_update_event] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("DELETE",))
def admin_delete_event(req):
    logger.debug("admin_delete_event called")

    try:
        dto = EventDeleteRequestDTO.model_validate(req.get_json(silent=True) or {})
        admin_uid = req.admin_token["uid"]
        payload = events_service.delete_event(dto.id, admin_uid)
        logger.info("Event %s deleted successfully", dto.id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_delete_event] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_all_events(req):
    logger.debug("admin_get_all_events called")

    try:
        payload = events_service.get_all_events()
        logger.info("Fetched all events successfully")
        return jsonify([item.to_payload() for item in payload]), 200
    except Exception as err:
        logger.error("[admin_get_all_events] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_event_by_id(req):
    logger.debug("admin_get_event_by_id called")

    try:
        dto = EventLookupQueryDTO.model_validate(dict(req.args or {}))
        payload = events_service.get_event_by_id(dto.id, slug=dto.slug)
        logger.info("Event lookup completed successfully")
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_get_event_by_id] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_event_guide(req):
    try:
        dto = EventGuideQueryDTO.model_validate(dict(req.args or {}))
        result = guide_service.get_admin_guide(dto.event_id)
        return jsonify(result), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Exception as err:
        logger.error("[admin_get_event_guide] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("PUT",))
def admin_update_event_guide(req):
    try:
        dto = UpdateEventGuideRequestDTO.model_validate(req.get_json(silent=True) or {})
        guide_service.upsert_guide(dto)
        return jsonify({"success": True}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Exception as err:
        logger.error("[admin_update_event_guide] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("PATCH",))
def admin_toggle_guide_published(req):
    try:
        dto = ToggleGuidePublishedRequestDTO.model_validate(req.get_json(silent=True) or {})
        guide_service.set_published(dto.event_id, dto.published)
        return jsonify({"success": True, "published": dto.published}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Exception as err:
        logger.error("[admin_toggle_guide_published] %s", redact_sensitive(str(err)))
        return handle_service_error(err)
