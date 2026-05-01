import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.sender_api import CreateTransactionalCampaignRequestDTO, SendTransactionalCampaignRequestDTO
from utils.http_responses import handle_pydantic_error, handle_service_error
from .helpers import get_sender_service

logger = logging.getLogger("AdminSenderTransactionalAPI")


@admin_endpoint(methods=("GET", "POST"))
def admin_sender_transactional(req):
    sender_service = get_sender_service()

    if req.method == "GET":
        try:
            return jsonify(sender_service.list_transactional_campaigns() or {}), 200
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
        return jsonify(result or {}), 200
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
        return jsonify(result or {"sent": True}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
