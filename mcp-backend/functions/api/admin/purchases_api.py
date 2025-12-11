# api/admin/purchases_api.py

from firebase_functions import https_fn
from flask import request, jsonify
from config.firebase_config import cors
from services.auth_service import require_admin
from services.purchases_service import PurchasesService
from config.firebase_config import region
# 🔧 Service instance
purchases_service = PurchasesService()

@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_all_purchases(req):
    if req.method != "GET":
        return "Invalid method", 405
    return purchases_service.get_all()

@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_purchase(req):
    if req.method != "GET":
        return "Invalid method", 405
    purchase_id = req.args.get("id")
    if not purchase_id:
        return {"error": "Missing purchase_id"}, 400
    return purchases_service.get_by_id(purchase_id)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def create_purchase(req):
    if req.method != "POST":
        return "Invalid method", 405
    data = request.get_json()
    if not data:
        return {"error": "Missing JSON body"}, 400
    return purchases_service.create(data)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def delete_purchase(req):
    if req.method != "DELETE":
        return "Invalid method", 405
    data = request.get_json()
    purchase_id = data.get("purchase_id")
    if not purchase_id:
        return {"error": "Missing purchase_id"}, 400
    return purchases_service.delete(purchase_id)
