from firebase_functions import https_fn
from flask import jsonify

from api.validators.entrance import (
    DEACTIVATE_SCAN_TOKEN_SCHEMA,
    DEACTIVATE_SCAN_TOKEN_SCHEMA,
    GENERATE_SCAN_TOKEN_SCHEMA,
    MANUAL_ENTRY_SCHEMA,
    VALIDATE_ENTRY_SCHEMA,
    VERIFY_SCAN_TOKEN_SCHEMA,
)
from api.validators.request import (
    require_json_body,
    validate_body_fields,
    validate_query_params,
    inject_payload_fields,
    inject_query_params,
)
from config.firebase_config import cors, region
from errors.service_errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from services.core.auth_service import require_admin
from services.entrance_service import EntranceService


entrance_service = EntranceService()


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
@require_json_body
@validate_body_fields(GENERATE_SCAN_TOKEN_SCHEMA)
@inject_payload_fields(["event_id"])
def entrance_generate_scan_token(req, event_id):
    """POST — genera un token di scansione per un evento (solo admin)."""
    if req.method != "POST":
        return jsonify({"error": "Invalid method"}), 405
    admin_uid = req.admin_token.get("uid", "")
    try:
        payload = entrance_service.generate_scan_token(event_id, admin_uid)
        return jsonify(payload), 201
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@validate_query_params(VERIFY_SCAN_TOKEN_SCHEMA)
@inject_query_params(["token"])
def entrance_verify_scan_token(req, token):
    """GET — verifica la validità di un token di scansione (pubblico)."""
    if req.method != "GET":
        return jsonify({"error": "Invalid method"}), 405
    result = entrance_service.verify_scan_token(token)
    if not result.get("valid"):
        return jsonify(result), 401
    return jsonify(result), 200


@https_fn.on_request(cors=cors, region=region)
@require_admin
@require_json_body
@validate_body_fields(DEACTIVATE_SCAN_TOKEN_SCHEMA)
@inject_payload_fields(["token"])
def entrance_deactivate_scan_token(req, token):
    """POST — disattiva un token di scansione esistente (solo admin)."""
    if req.method != "POST":
        return jsonify({"error": "Invalid method"}), 405
    admin_uid = req.admin_token.get("uid", "")
    try:
        payload = entrance_service.deactivate_scan_token(token, admin_uid)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
@require_json_body
@validate_body_fields(MANUAL_ENTRY_SCHEMA)
@inject_payload_fields(["event_id", "membership_id", "entered"])
def entrance_manual_entry(req, event_id, membership_id, entered):
    """POST — segna manualmente entrata/uscita di un membro (solo admin)."""
    if req.method != "POST":
        return jsonify({"error": "Invalid method"}), 405
    admin_uid = req.admin_token.get("uid", "")
    try:
        payload = entrance_service.manual_entry(event_id, membership_id, entered, admin_uid)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_json_body
@validate_body_fields(VALIDATE_ENTRY_SCHEMA)
@inject_payload_fields(["membership_id", "scan_token"])
def entrance_validate(req, membership_id, scan_token):
    """POST — valida l'ingresso di un membro tramite QR scan (protetto da scan_token)."""
    if req.method != "POST":
        return jsonify({"error": "Invalid method"}), 405
    try:
        payload = entrance_service.validate_entry(membership_id, scan_token)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)
