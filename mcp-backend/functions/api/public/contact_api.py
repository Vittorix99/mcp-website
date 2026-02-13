from firebase_functions import https_fn
from config.firebase_config import cors, region
from dto import ContactMessageDTO
from services.messages_service import MessagesService
from services.service_errors import ExternalServiceError, NotFoundError, ServiceError, ValidationError


messages_service = MessagesService()


@https_fn.on_request(cors=cors, region=region)
def contact_us(req):
    """API to handle contact form submissions"""
    if req.method != 'POST':
        return 'Invalid request method', 405

    req_json = req.get_json()
    if not req_json:
        return 'Invalid request', 400

    send_copy = bool(req_json.get("send_copy"))
    message_dto = ContactMessageDTO.from_payload(req_json)
    try:
        payload = messages_service.submit_contact_message(message_dto, send_copy=send_copy)
        return payload, 200
    except Exception as err:
        return _handle_service_error(err)


def _handle_service_error(err: Exception):
    if isinstance(err, ValidationError):
        return {"error": str(err)}, 400
    if isinstance(err, NotFoundError):
        return {"error": str(err)}, 404
    if isinstance(err, ExternalServiceError):
        return {"error": str(err)}, 502
    if isinstance(err, ServiceError):
        return {"error": str(err)}, 500
    return {"error": "Internal server error"}, 500
