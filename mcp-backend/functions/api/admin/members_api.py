# memberships_api.py

from firebase_functions import https_fn
from config.firebase_config import region
from flask import request, jsonify
from config.firebase_config import cors
from services.auth_service import require_admin
from services.memberships_service import MembershipsService

memberships_service = MembershipsService()

@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_memberships(req):
    if req.method != "GET":
        return "Invalid method", 405
    return memberships_service.get_all()

@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_membership(req):
    if req.method != "GET":
        return "Invalid method", 405
    membership_id = req.args.get("id")
    if not membership_id:
        return {"error": "Missing membership ID"}, 400
    return memberships_service.get_by_id(membership_id)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def create_membership(req):
    if req.method != "POST":
        return "Invalid method", 405
    data = request.get_json()
    if not data:
        return {"error": "Missing JSON body"}, 400
    return memberships_service.create(data)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def update_membership(req):
    if req.method != "PUT":
        return "Invalid method", 405
    data = request.get_json()
    if not data or "membership_id" not in data:
        return {"error": "Missing membership_id or body"}, 400
    membership_id = data.pop("membership_id")
    return memberships_service.update(membership_id, data)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def delete_membership(req):
    if req.method != "DELETE":
        return "Invalid method", 405
    data = request.get_json()
    membership_id = data.get("membership_id")
    if not membership_id:
        return {"error": "Missing membership_id"}, 400
    return memberships_service.delete(membership_id)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def send_membership_card(req):
    if req.method != "POST":
        return "Invalid method", 405
    data = request.get_json()
    membership_id = data.get("membership_id")
    if not membership_id:
        return {"error": "Missing membership_id"}, 400
    return memberships_service.send_card(membership_id)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_membership_purchases(req):
    if req.method != "GET":
        return "Invalid method", 405

    membership_id = req.args.get("id")
    if not membership_id:
        return {"error": "Missing membership_id"}, 400

    return memberships_service.get_purchases(membership_id)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_membership_events(req):
    if req.method != "GET":
        return "Invalid method", 405

    membership_id = req.args.get("id")
    if not membership_id:
        return {"error": "Missing membership_id"}, 400

    return memberships_service.get_events(membership_id)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def set_membership_price(req):
    if req.method != "POST":
        return "Invalid method", 405

    data = request.get_json()
    print("Data price is:", data)
    membership_fee = data.get("membership_fee")
    if membership_fee is None:
        return {"error": "Missing membership_fee"}, 400

    return memberships_service.set_membership_price(membership_fee)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_membership_price(req):
    if req.method != "GET":
        return "Invalid method", 405

    return memberships_service.get_membership_price()
