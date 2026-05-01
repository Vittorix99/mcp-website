from firebase_functions import https_fn
from pydantic import ValidationError as PydanticValidationError
from flask import jsonify

from config.firebase_config import cors, region
from dto.admin import AdminIdQueryDTO, CreateAdminRequestDTO, UpdateAdminRequestDTO
from services.core.admin_service import AdminService
from services.core.auth_service import require_admin, verify_admin_service
from utils.http_responses import handle_pydantic_error, handle_service_error


admin_service = AdminService()


@https_fn.on_request(cors=cors, region=region)
@require_admin
def create_admin(req):
    if req.method != "POST":
        return jsonify({"error": "Invalid method"}), 405

    try:
        dto = CreateAdminRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = admin_service.create(dto, created_by=req.admin_token.get("uid", ""))
        return jsonify(payload.model_dump(by_alias=True)), 201
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_all_admins(req):
    if req.method != "GET":
        return jsonify({"error": "Invalid method"}), 405

    try:
        payload = admin_service.get_all()
        return jsonify(payload.model_dump(by_alias=True)), 200
    except Exception as err:
        return handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_admin_by_id(req):
    if req.method != "GET":
        return jsonify({"error": "Invalid method"}), 405

    try:
        dto = AdminIdQueryDTO.model_validate(dict(req.args or {}))
        payload = admin_service.get_by_id(dto.id)
        return jsonify(payload.model_dump(by_alias=True)), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def update_admin(req):
    if req.method != "PUT":
        return jsonify({"error": "Invalid method"}), 405

    try:
        dto = UpdateAdminRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = admin_service.update(dto)
        return jsonify(payload.model_dump(by_alias=True)), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def delete_admin(req):
    if req.method != "DELETE":
        return jsonify({"error": "Invalid method"}), 405

    try:
        dto = AdminIdQueryDTO.model_validate(dict(req.args or {}))
        payload = admin_service.delete(dto.id)
        return jsonify(payload.model_dump(by_alias=True)), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@https_fn.on_call()
def verify_admin(req: https_fn.CallableRequest) -> dict:
    return verify_admin_service(req)
