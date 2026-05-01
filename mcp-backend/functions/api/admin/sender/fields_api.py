import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.sender_api import CreateFieldRequestDTO, FieldDeleteRequestDTO
from utils.http_responses import handle_pydantic_error, handle_service_error
from .helpers import get_sender_service

logger = logging.getLogger("AdminSenderFieldsAPI")


@admin_endpoint(methods=("GET", "POST", "DELETE"))
def admin_sender_fields(req):
    sender_service = get_sender_service()

    if req.method == "GET":
        try:
            return jsonify(sender_service.list_fields() or {}), 200
        except Exception as err:
            return handle_service_error(err)

    if req.method == "POST":
        try:
            dto = CreateFieldRequestDTO.model_validate(req.get_json(silent=True) or {})
            return jsonify(sender_service.create_field(dto.title, dto.type) or {}), 200
        except PydanticValidationError as err:
            return handle_pydantic_error(err)
        except Exception as err:
            return handle_service_error(err)

    try:
        data = {**(req.get_json(silent=True) or {}), **dict(req.args or {})}
        dto = FieldDeleteRequestDTO.model_validate(data)
        sender_service.delete_field(dto.id)
        return jsonify({"deleted": True}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
