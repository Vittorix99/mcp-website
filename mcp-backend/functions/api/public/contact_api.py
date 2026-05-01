from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import public_endpoint
from dto.message_api import ContactFormRequestDTO
from services.communications.messages_service import MessagesService
from utils.http_responses import handle_pydantic_error, handle_service_error


messages_service = MessagesService()


@public_endpoint(methods=("POST",))
def contact_us(req):
    """API to handle contact form submissions"""
    try:
        dto = ContactFormRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = messages_service.submit_contact_message(dto)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
