import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.sender_api import SegmentDeleteRequestDTO, SegmentQueryDTO, SegmentSubscribersQueryDTO
from utils.http_responses import handle_pydantic_error, handle_service_error
from .helpers import get_sender_service

logger = logging.getLogger("AdminSenderSegmentsAPI")


@admin_endpoint(methods=("GET", "DELETE"))
def admin_sender_segments(req):
    sender_service = get_sender_service()

    if req.method == "GET":
        try:
            dto = SegmentQueryDTO.model_validate(dict(req.args or {}))
            if dto.id:
                return jsonify(sender_service.get_segment(dto.id) or {}), 200
            return jsonify(sender_service.list_segments() or {}), 200
        except PydanticValidationError as err:
            return handle_pydantic_error(err)
        except Exception as err:
            return handle_service_error(err)

    try:
        data = {**(req.get_json(silent=True) or {}), **dict(req.args or {})}
        dto = SegmentDeleteRequestDTO.model_validate(data)
        ok = sender_service.delete_segment(dto.id)
        if not ok:
            return jsonify({"error": "Impossibile eliminare il segmento."}), 500
        return jsonify({"deleted": True}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_sender_segment_subscribers(req):
    sender_service = get_sender_service()
    try:
        dto = SegmentSubscribersQueryDTO.model_validate(dict(req.args or {}))
        return jsonify(sender_service.list_segment_subscribers(dto.id) or {}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
