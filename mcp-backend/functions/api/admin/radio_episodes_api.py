import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.radio import (
    CreateRadioEpisodeRequestDTO,
    RadioEpisodeIdRequestDTO,
    UpdateRadioEpisodeRequestDTO,
)
from services.radio import RadioEpisodeService
from utils.http_responses import handle_pydantic_error, handle_service_error
from utils.safe_logging import redact_sensitive

logger = logging.getLogger("AdminRadioEpisodesAPI")
episode_service = RadioEpisodeService()


@admin_endpoint(methods=("GET",))
def admin_get_radio_episodes(req):
    try:
        payload = episode_service.get_all(published_only=False)
        return jsonify([e.to_payload() for e in payload]), 200
    except Exception as err:
        logger.error("[admin_get_radio_episodes] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def admin_create_radio_episode(req):
    try:
        dto = CreateRadioEpisodeRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = episode_service.create(dto)
        return jsonify(payload.to_payload()), 201
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_create_radio_episode] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_radio_episode(req):
    try:
        episode_id = (req.args or {}).get("id", "")
        if not episode_id:
            return jsonify({"error": "Missing required query param: id"}), 400
        payload = episode_service.get_by_id(episode_id)
        return jsonify(payload.to_payload()), 200
    except Exception as err:
        logger.error("[admin_get_radio_episode] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("PUT",))
def admin_update_radio_episode(req):
    try:
        dto = UpdateRadioEpisodeRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = episode_service.update(dto)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_update_radio_episode] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("DELETE",))
def admin_delete_radio_episode(req):
    try:
        body = req.get_json(silent=True) or {}
        episode_id = body.get("id", "")
        if not episode_id:
            return jsonify({"error": "Missing required field: id"}), 400
        episode_service.delete(episode_id)
        return jsonify({"message": "Radio episode deleted"}), 200
    except Exception as err:
        logger.error("[admin_delete_radio_episode] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("PATCH",))
def admin_publish_radio_episode(req):
    try:
        dto = RadioEpisodeIdRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = episode_service.publish(dto.id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_publish_radio_episode] %s", redact_sensitive(str(err)))
        return handle_service_error(err)


@admin_endpoint(methods=("PATCH",))
def admin_unpublish_radio_episode(req):
    try:
        dto = RadioEpisodeIdRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = episode_service.unpublish(dto.id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_unpublish_radio_episode] %s", redact_sensitive(str(err)))
        return handle_service_error(err)
