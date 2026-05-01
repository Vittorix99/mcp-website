from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.purchase import (
    CreatePurchaseRequestDTO,
    PurchaseIdRequestDTO,
    PurchaseLookupQueryDTO,
)
from services.payments.purchases_service import PurchasesService
from utils.http_responses import handle_pydantic_error, handle_service_error


purchases_service = PurchasesService()


@admin_endpoint(methods=("GET",))
def get_all_purchases(req):
    try:
        payload = purchases_service.get_all()
        return jsonify([purchase.to_payload() for purchase in payload]), 200
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def get_purchase(req):
    try:
        dto = PurchaseLookupQueryDTO.model_validate(req.args.to_dict())
        payload = purchases_service.get_by_id(dto.id, slug=dto.slug)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def create_purchase(req):
    try:
        dto = CreatePurchaseRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = purchases_service.create(dto)
        return jsonify(payload.to_payload()), 201
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("DELETE",))
def delete_purchase(req):
    try:
        dto = PurchaseIdRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = purchases_service.delete(dto.purchase_id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
