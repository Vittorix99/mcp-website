# api/admin/purchases_api.py

from firebase_functions import https_fn
from flask import request, jsonify
from config.firebase_config import cors
from services.core.auth_service import require_admin
from services.payments.purchases_service import PurchasesService
from errors.service_errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from config.firebase_config import region
from dto import PurchaseDTO
# Service instance
purchases_service = PurchasesService()

def _handle_service_error(err: Exception):
    if isinstance(err, ValidationError):
        return jsonify({"error": str(err)}), 400
    if isinstance(err, ForbiddenError):
        return jsonify({"error": str(err)}), 403
    if isinstance(err, NotFoundError):
        return jsonify({"error": str(err)}), 404
    if isinstance(err, ConflictError):
        return jsonify({"error": str(err)}), 409
    if isinstance(err, ServiceError):
        return jsonify({"error": str(err)}), 500
    return jsonify({"error": "Internal server error"}), 500

@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_all_purchases(req):
    if req.method != "GET":
        return "Invalid method", 405
    try:
        payload = purchases_service.get_all()
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_purchase(req):
    if req.method != "GET":
        return "Invalid method", 405
    purchase_id = req.args.get("id")
    slug = req.args.get("slug")
    if not purchase_id and not slug:
        return {"error": "Missing purchase_id or slug"}, 400
    try:
        payload = purchases_service.get_by_id(purchase_id, slug=slug)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def create_purchase(req):
    if req.method != "POST":
        return "Invalid method", 405
    data = request.get_json()
    if not data:
        return {"error": "Missing JSON body"}, 400
    dto = PurchaseDTO.from_payload(data)
    try:
        payload = purchases_service.create(dto)
        return jsonify(payload), 201
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def delete_purchase(req):
    if req.method != "DELETE":
        return "Invalid method", 405
    data = request.get_json()
    purchase_id = data.get("purchase_id")
    if not purchase_id:
        return {"error": "Missing purchase_id"}, 400
    try:
        payload = purchases_service.delete(purchase_id)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)
