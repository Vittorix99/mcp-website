import logging
from flask import jsonify
from firebase_functions import https_fn
from config.firebase_config import cors
from services.payments_service import create_order_service, capture_order_service
from config.firebase_config import region
@https_fn.on_request(cors=cors, region=region)
def create_order(req):
    """API to create a PayPal order"""
    if req.method != "POST":
        return "Invalid request method", 405

    req_json = req.get_json()
    if not req_json:
        return jsonify({"error": "Missing request body"}), 400

    return create_order_service(req_json)

@https_fn.on_request(cors=cors, region=region)
def capture_order(req):
    """API to capture a PayPal order"""
    if req.method != "POST":
        return "Invalid request method", 405

    req_json = req.get_json()
    if not req_json:
        return jsonify({"error": "Missing request body"}), 400

    return capture_order_service(req_json)