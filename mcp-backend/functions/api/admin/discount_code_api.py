import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.discount_code_dto import (
    AdminCreateDiscountCodeRequestDTO,
    AdminUpdateDiscountCodeRequestDTO,
    DiscountCodeEventRequestDTO,
    DiscountCodeIdRequestDTO,
)
from services.payments.discount_code_admin_service import DiscountCodeAdminService
from utils.http_responses import handle_pydantic_error, handle_service_error


logger = logging.getLogger("AdminDiscountCodeAPI")
discount_code_admin_service = DiscountCodeAdminService()


@admin_endpoint(methods=("POST",))
def admin_create_discount_code(req):
    try:
        dto = AdminCreateDiscountCodeRequestDTO.model_validate(req.get_json(silent=True) or {})
        admin_uid = req.admin_token["uid"]
        payload = discount_code_admin_service.create_discount_code(dto.event_id, dto, admin_uid)
        return jsonify(payload.to_payload()), 201
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.exception("[admin_create_discount_code]")
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_list_discount_codes(req):
    try:
        dto = DiscountCodeEventRequestDTO.model_validate(dict(req.args or {}))
        payload = discount_code_admin_service.list_discount_codes(dto.event_id)
        return jsonify([item.to_payload() for item in payload]), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.exception("[admin_list_discount_codes]")
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_discount_code(req):
    try:
        dto = DiscountCodeIdRequestDTO.model_validate(dict(req.args or {}))
        payload = discount_code_admin_service.get_discount_code(dto.discount_code_id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.exception("[admin_get_discount_code]")
        return handle_service_error(err)


@admin_endpoint(methods=("PATCH",))
def admin_update_discount_code(req):
    try:
        dto = AdminUpdateDiscountCodeRequestDTO.model_validate(req.get_json(silent=True) or {})
        admin_uid = req.admin_token["uid"]
        payload = discount_code_admin_service.update_discount_code(dto.discount_code_id, dto, admin_uid)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.exception("[admin_update_discount_code]")
        return handle_service_error(err)


@admin_endpoint(methods=("DELETE",))
def admin_disable_discount_code(req):
    try:
        dto = DiscountCodeIdRequestDTO.model_validate(req.get_json(silent=True) or {})
        admin_uid = req.admin_token["uid"]
        payload = discount_code_admin_service.disable_discount_code(dto.discount_code_id, admin_uid)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.exception("[admin_disable_discount_code]")
        return handle_service_error(err)
