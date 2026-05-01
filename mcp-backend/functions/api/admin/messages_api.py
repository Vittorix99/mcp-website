from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.message_api import MessageIdRequestDTO, ReplyMessageRequestDTO
from services.communications.messages_service import MessagesService
from utils.http_responses import handle_pydantic_error, handle_service_error

messages_service = MessagesService()

@admin_endpoint(methods=("GET",))
def get_messages(req):
    try:
        payload = messages_service.get_all()
        return jsonify([item.to_payload() for item in payload]), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)

@admin_endpoint(methods=("DELETE",))
def delete_message(req):
    try:
        dto = MessageIdRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = messages_service.delete_by_id(dto.message_id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)

@admin_endpoint(methods=("POST",))
def reply_to_message(req):
    try:
        dto = ReplyMessageRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = messages_service.reply(dto)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
