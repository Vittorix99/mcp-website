import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.location_api import (
    GetEventLocationQueryDTO,
    ToggleLocationPublishedRequestDTO,
    UpdateEventLocationRequestDTO,
)
from errors.service_errors import NotFoundError
from services.events.location_service import LocationService
from utils.http_responses import handle_pydantic_error, handle_service_error
from utils.safe_logging import redact_sensitive

logger = logging.getLogger("AdminLocationAPI")
location_service = LocationService()


@admin_endpoint(methods=("GET",))
def admin_get_event_location(req):
    try:
        dto = GetEventLocationQueryDTO.model_validate(dict(req.args or {}))
        result = location_service.get_admin_location(dto)
        return jsonify(result.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Exception as err:
        logger.error("[admin_get_event_location] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("PUT",))
def admin_update_event_location(req):
    try:
        dto = UpdateEventLocationRequestDTO.model_validate(req.get_json(silent=True) or {})
        result = location_service.update_location(dto)
        return jsonify(result.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Exception as err:
        logger.error("[admin_update_event_location] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("PATCH",))
def admin_toggle_location_published(req):
    try:
        dto = ToggleLocationPublishedRequestDTO.model_validate(req.get_json(silent=True) or {})
        location_service.set_location_published(dto)
        return jsonify({"success": True, "published": dto.published}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Exception as err:
        logger.error("[admin_toggle_location_published] %s", redact_sensitive(str(err)))
        return handle_service_error(err)
