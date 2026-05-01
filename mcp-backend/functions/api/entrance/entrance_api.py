import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint, public_endpoint
from dto.entrance_api import (
    DeactivateScanTokenRequestDTO,
    GenerateScanTokenRequestDTO,
    ManualEntryRequestDTO,
    ValidateEntryRequestDTO,
    VerifyScanTokenQueryDTO,
)
from services.entrance_service import EntranceService
from utils.http_responses import handle_pydantic_error, handle_service_error

logger = logging.getLogger("EntranceAPI")
entrance_service = EntranceService()


@admin_endpoint(methods=("POST",))
def entrance_generate_scan_token(req):
    try:
        # API admin: valida la request e delega al service la creazione del token evento.
        dto = GenerateScanTokenRequestDTO.model_validate(req.get_json(silent=True) or {})
        admin_uid = req.admin_token.get("uid", "")
        payload = entrance_service.generate_scan_token(dto, admin_uid)
        return jsonify(payload.to_payload()), 201
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[entrance_generate_scan_token] %s", str(err))
        return handle_service_error(err)


@public_endpoint(methods=("GET",))
def entrance_verify_scan_token(req):
    try:
        # API pubblica usata dalla pagina scanner per capire se il token e' ancora utilizzabile.
        dto = VerifyScanTokenQueryDTO.model_validate(dict(req.args or {}))
        payload = entrance_service.verify_scan_token(dto)
        status = 200 if payload.valid else 401
        return jsonify(payload.to_payload()), status
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def entrance_deactivate_scan_token(req):
    try:
        dto = DeactivateScanTokenRequestDTO.model_validate(req.get_json(silent=True) or {})
        admin_uid = req.admin_token.get("uid", "")
        payload = entrance_service.deactivate_scan_token(dto, admin_uid)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[entrance_deactivate_scan_token] %s", str(err))
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def entrance_manual_entry(req):
    try:
        # L'override manuale resta admin-only: non passa dallo scanner pubblico.
        dto = ManualEntryRequestDTO.model_validate(req.get_json(silent=True) or {})
        admin_uid = req.admin_token.get("uid", "")
        payload = entrance_service.manual_entry(dto, admin_uid)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[entrance_manual_entry] %s", str(err))
        return handle_service_error(err)


@public_endpoint(methods=("POST",))
def entrance_validate(req):
    try:
        # Punto di ingresso dello scanner: JSON -> DTO -> service -> risposta tipizzata.
        dto = ValidateEntryRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = entrance_service.validate_entry(dto)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
