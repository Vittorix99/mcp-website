import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.radio import (
    CreateRadioSeasonRequestDTO,
    UpdateRadioSeasonRequestDTO,
)
from services.radio import RadioSeasonService
from utils.http_responses import handle_pydantic_error, handle_service_error

logger = logging.getLogger("AdminRadioSeasonsAPI")
season_service = RadioSeasonService()


@admin_endpoint(methods=("GET",))
def admin_get_radio_seasons(req):
    try:
        payload = season_service.get_all()
        return jsonify([s.to_payload() for s in payload]), 200
    except Exception as err:
        logger.error("[admin_get_radio_seasons] %s", str(err))
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def admin_create_radio_season(req):
    try:
        dto = CreateRadioSeasonRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = season_service.create(dto)
        return jsonify(payload.to_payload()), 201
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_create_radio_season] %s", str(err))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_radio_season(req):
    try:
        season_id = (req.args or {}).get("id", "")
        if not season_id:
            return jsonify({"error": "Missing required query param: id"}), 400
        payload = season_service.get_by_id(season_id)
        return jsonify(payload.to_payload()), 200
    except Exception as err:
        logger.error("[admin_get_radio_season] %s", str(err))
        return handle_service_error(err)


@admin_endpoint(methods=("PUT",))
def admin_update_radio_season(req):
    try:
        dto = UpdateRadioSeasonRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = season_service.update(dto)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_update_radio_season] %s", str(err))
        return handle_service_error(err)


@admin_endpoint(methods=("DELETE",))
def admin_delete_radio_season(req):
    try:
        body = req.get_json(silent=True) or {}
        season_id = body.get("id", "")
        if not season_id:
            return jsonify({"error": "Missing required field: id"}), 400
        season_service.delete(season_id)
        return jsonify({"message": "Radio season deleted"}), 200
    except Exception as err:
        logger.error("[admin_delete_radio_season] %s", str(err))
        return handle_service_error(err)
