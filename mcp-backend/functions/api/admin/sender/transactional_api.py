import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.sender_api import (
    CampaignIdRequestDTO,
    CreateTransactionalCampaignRequestDTO,
    SendTransactionalCampaignRequestDTO,
)
from errors.service_errors import ExternalServiceError
from utils.http_responses import handle_pydantic_error, handle_service_error
from .helpers import get_sender_service

logger = logging.getLogger("AdminSenderTransactionalAPI")


@admin_endpoint(methods=("GET", "POST", "DELETE"))
def admin_sender_transactional(req):
    sender_service = get_sender_service()

    if req.method == "GET":
        try:
            result = sender_service.list_transactional_campaigns()
            if result is None:
                raise ExternalServiceError("Sender non ha restituito le campagne transazionali")
            return jsonify(result), 200
        except Exception as err:
            return handle_service_error(err)

    if req.method == "DELETE":
        try:
            data = {**(req.get_json(silent=True) or {}), **dict(req.args or {})}
            dto = CampaignIdRequestDTO.model_validate(data)
            if not sender_service.delete_transactional_campaign(dto.id):
                raise ExternalServiceError("Sender non ha eliminato la campagna transazionale")
            return jsonify({"deleted": True}), 200
        except PydanticValidationError as err:
            return handle_pydantic_error(err)
        except Exception as err:
            return handle_service_error(err)

    try:
        dto = CreateTransactionalCampaignRequestDTO.model_validate(req.get_json(silent=True) or {})
        result = sender_service.create_transactional_campaign(
            title=dto.title,
            subject=dto.subject,
            from_name=dto.from_name,
            from_email=str(dto.from_email),
            content_html=dto.content_html,
        )
        if result is None:
            raise ExternalServiceError("Sender non ha creato la campagna transazionale")
        return jsonify(result), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def admin_sender_transactional_send(req):
    sender_service = get_sender_service()
    try:
        dto = SendTransactionalCampaignRequestDTO.model_validate(req.get_json(silent=True) or {})
        result = sender_service.send_transactional_campaign(
            campaign_id=dto.id,
            to_email=str(dto.to_email),
            to_name=dto.to_name,
            variables=dto.variables,
        )
        if result is None:
            raise ExternalServiceError("Sender non ha inviato la campagna transazionale")
        return jsonify(result), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
