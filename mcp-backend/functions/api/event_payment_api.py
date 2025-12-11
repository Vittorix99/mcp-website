from firebase_functions import https_fn
from flask import jsonify

from api.decorators import require_active_event
from config.firebase_config import cors, region
from services.event_payment_service import create_order_event_service, capture_order_event_service


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
    return create_order_event_service(req_json, event_data)


@https_fn.on_request(cors=cors, region=region)
def capture_order_event(req):
    if req.method != "POST":
        return "Invalid request method", 405

    req_json = req.get_json()
    if not req_json:
        return jsonify({"error": "Missing request body"}), 400

    return capture_order_event_service(req_json)
