from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import public_endpoint, require_active_event
from dto.preorder import OrderCaptureDTO, PreOrderDTO
from models import Event
from services.payments.event_payment_service import EventPaymentService
from utils.http_responses import handle_pydantic_error, handle_service_error


event_payment_service = EventPaymentService()


@public_endpoint(methods=("POST",))
@require_active_event
def create_order_event(req):
    try:
        req_json = getattr(req, "event_payload", None) or req.get_json(silent=True) or {}
        event_data = getattr(req, "event_data", None) or {}
        event_id = getattr(req, "event_id", None)

        order_dto = PreOrderDTO.model_validate(req_json)
        event_model = Event.from_firestore(event_data, event_id) if event_data and event_id else None

        payload = event_payment_service.create_order_event(order_dto, event_model)
        return jsonify(payload.to_payload()), 201
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@public_endpoint(methods=("POST",))
def capture_order_event(req):
    try:
        req_json = req.get_json(silent=True) or {}
        capture_dto = OrderCaptureDTO.model_validate(req_json)
        payload = event_payment_service.capture_order_event(capture_dto)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
