from firebase_functions import https_fn
from flask import jsonify

from api.decorators import require_active_event
from config.firebase_config import cors, region
from dto import PreOrderDTO, OrderCaptureDTO, EventDTO
from services.event_payment_service import create_order_event_service, capture_order_event_service
from services.service_errors import (
    ExternalServiceError,
    NotFoundError,
    ServiceError,
    ValidationError,
)


@https_fn.on_request(cors=cors, region=region)
@require_active_event
def create_order_event(req):
    if req.method != "POST":
        return "Invalid request method", 405

    req_json = getattr(req, "event_payload", None)
    if not req_json:
        req_json = req.get_json()
    if not req_json:
        return jsonify({"error": "Missing request body"}), 400

    event_data = getattr(req, "event_data", None)
    event_id = getattr(req, "event_id", None)
    event_dto = EventDTO.from_payload({**event_data, "id": event_id}) if event_data else None
    order_dto = PreOrderDTO.from_payload(req_json)
    try:
        payload = create_order_event_service(order_dto, event_dto)
        return jsonify(payload), 201
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
def capture_order_event(req):
    if req.method != "POST":
        return "Invalid request method", 405

    req_json = req.get_json()
    if not req_json:
        return jsonify({"error": "Missing request body"}), 400

    capture_dto = OrderCaptureDTO.from_payload(req_json)
    try:
        payload = capture_order_event_service(capture_dto)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)


def _handle_service_error(err: Exception):
    if isinstance(err, ValidationError):
        details = getattr(err, "details", None)
        if details:
            return jsonify({"error": "validation_error", "messages": details}), 400
        return jsonify({"error": str(err)}), 400
    if isinstance(err, NotFoundError):
        return jsonify({"error": str(err)}), 404
    if isinstance(err, ExternalServiceError):
        return jsonify({"error": str(err)}), 502
    if isinstance(err, ServiceError):
        return jsonify({"error": str(err)}), 500
    return jsonify({"error": "Internal server error"}), 500
