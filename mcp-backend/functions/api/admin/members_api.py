# memberships_api.py

from firebase_functions import https_fn
from config.firebase_config import region
from flask import request, jsonify
from config.firebase_config import cors
from services.auth_service import require_admin
from services.memberships_service import MembershipsService
from services.membership_reports_service import MembershipReportsService
from services.service_errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from dto import MembershipDTO

memberships_service = MembershipsService()
membership_reports_service = MembershipReportsService()


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
def get_memberships(req):
    if req.method != "GET":
        return "Invalid method", 405
    try:
        payload = memberships_service.get_all()
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_membership(req):
    if req.method != "GET":
        return "Invalid method", 405
    membership_id = req.args.get("id")
    slug = req.args.get("slug")
    if not membership_id and not slug:
        return {"error": "Missing membership ID or slug"}, 400
    try:
        payload = memberships_service.get_by_id(membership_id, slug=slug)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def create_membership(req):
    if req.method != "POST":
        return "Invalid method", 405
    data = request.get_json()
    if not data:
        return {"error": "Missing JSON body"}, 400
    dto = MembershipDTO.from_payload(data)
    try:
        payload = memberships_service.create(dto)
        return jsonify(payload), 201
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def update_membership(req):
    if req.method != "PUT":
        return "Invalid method", 405
    data = request.get_json()
    if not data or "membership_id" not in data:
        return {"error": "Missing membership_id or body"}, 400
    membership_id = data.pop("membership_id")
    dto = MembershipDTO.from_payload(data)
    try:
        payload = memberships_service.update(membership_id, dto)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def delete_membership(req):
    if req.method != "DELETE":
        return "Invalid method", 405
    data = request.get_json()
    membership_id = data.get("membership_id")
    if not membership_id:
        return {"error": "Missing membership_id"}, 400
    try:
        payload = memberships_service.delete(membership_id)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def send_membership_card(req):
    if req.method != "POST":
        return "Invalid method", 405
    data = request.get_json()
    membership_id = data.get("membership_id")
    if not membership_id:
        return {"error": "Missing membership_id"}, 400
    try:
        payload = memberships_service.send_card(membership_id)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_membership_purchases(req):
    if req.method != "GET":
        return "Invalid method", 405

    membership_id = req.args.get("id")
    slug = req.args.get("slug")
    if not membership_id and not slug:
        return {"error": "Missing membership_id or slug"}, 400
    if not membership_id and slug:
        try:
            resolved_payload = memberships_service.get_by_id(None, slug=slug)
            membership_id = resolved_payload.get("id")
        except Exception as err:
            return _handle_service_error(err)
    try:
        payload = memberships_service.get_purchases(membership_id)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_membership_events(req):
    if req.method != "GET":
        return "Invalid method", 405

    membership_id = req.args.get("id")
    slug = req.args.get("slug")
    if not membership_id and not slug:
        return {"error": "Missing membership_id or slug"}, 400
    if not membership_id and slug:
        try:
            resolved_payload = memberships_service.get_by_id(None, slug=slug)
            membership_id = resolved_payload.get("id")
        except Exception as err:
            return _handle_service_error(err)
    try:
        payload = memberships_service.get_events(membership_id)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def set_membership_price(req):
    if req.method != "POST":
        return "Invalid method", 405

    data = request.get_json()
    print("Data price is:", data)
    membership_fee = data.get("membership_fee")
    year = data.get("year")
    if membership_fee is None:
        return {"error": "Missing membership_fee"}, 400

    try:
        payload = memberships_service.set_membership_price(membership_fee, year=year)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_membership_price(req):
    if req.method != "GET":
        return "Invalid method", 405

    year = req.args.get("year")
    try:
        payload = memberships_service.get_membership_price(year=year)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_memberships_report(req):
    if req.method != "GET":
        return "Invalid method", 405

    event_id = req.args.get("event_id")
    if not event_id:
        return {"error": "Missing event_id"}, 400
    try:
        payload = membership_reports_service.get_memberships_report(event_id=event_id)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)
