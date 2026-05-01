import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.sender_api import (
    CampaignIdRequestDTO,
    CampaignQueryDTO,
    CampaignStatsQueryDTO,
    CreateCampaignRequestDTO,
    ScheduleCampaignRequestDTO,
    UpdateCampaignRequestDTO,
)
from utils.http_responses import handle_pydantic_error, handle_service_error
from .helpers import get_sender_service

logger = logging.getLogger("AdminSenderCampaignsAPI")


@admin_endpoint(methods=("GET", "POST", "PUT", "DELETE"))
def admin_sender_campaigns(req):
    sender_service = get_sender_service()

    if req.method == "GET":
        try:
            dto = CampaignQueryDTO.model_validate(dict(req.args or {}))
            if dto.id:
                return jsonify(sender_service.get_campaign(dto.id) or {}), 200
            return jsonify(sender_service.list_campaigns(params=dict(req.args or {})) or {}), 200
        except PydanticValidationError as err:
            return handle_pydantic_error(err)
        except Exception as err:
            return handle_service_error(err)

    if req.method == "POST":
        try:
            dto = CreateCampaignRequestDTO.model_validate(req.get_json(silent=True) or {})
            result = sender_service.create_campaign(
                title=dto.title,
                subject=dto.subject,
                from_name=dto.from_name,
                from_email=str(dto.from_email),
                content_html=dto.content_html,
                reply_to=str(dto.reply_to) if dto.reply_to else str(dto.from_email),
                groups=dto.groups,
            )
            return jsonify(result or {}), 200
        except PydanticValidationError as err:
            return handle_pydantic_error(err)
        except Exception as err:
            return handle_service_error(err)

    if req.method == "PUT":
        try:
            dto = UpdateCampaignRequestDTO.model_validate(req.get_json(silent=True) or {})
            result = sender_service.update_campaign(
                campaign_id=dto.id,
                title=dto.title,
                subject=dto.subject,
                from_name=dto.from_name,
                from_email=str(dto.from_email) if dto.from_email else None,
                content_html=dto.content_html,
                groups=dto.groups,
            )
            return jsonify(result or {}), 200
        except PydanticValidationError as err:
            return handle_pydantic_error(err)
        except Exception as err:
            return handle_service_error(err)

    try:
        data = {**(req.get_json(silent=True) or {}), **dict(req.args or {})}
        dto = CampaignIdRequestDTO.model_validate(data)
        ok = sender_service.delete_campaign(dto.id)
        if not ok:
            return jsonify({"error": "Sender API non supporta l'eliminazione delle campagne via API. Eliminala dalla dashboard Sender."}), 501
        return jsonify({"deleted": True}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def admin_sender_campaign_send(req):
    sender_service = get_sender_service()
    try:
        dto = CampaignIdRequestDTO.model_validate(req.get_json(silent=True) or {})
        ok, error = sender_service.send_campaign(dto.id)
        if not ok:
            return jsonify({"sent": False, "error": error or "Sender ha rifiutato l'invio."}), 422
        return jsonify({"sent": True}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST", "DELETE"))
def admin_sender_campaign_schedule(req):
    sender_service = get_sender_service()

    if req.method == "POST":
        try:
            dto = ScheduleCampaignRequestDTO.model_validate(req.get_json(silent=True) or {})
            ok, error = sender_service.schedule_campaign(dto.id, dto.scheduled_at)
            if not ok:
                return jsonify({"scheduled": False, "error": error or "Sender ha rifiutato la schedulazione."}), 422
            return jsonify({"scheduled": True}), 200
        except PydanticValidationError as err:
            return handle_pydantic_error(err)
        except Exception as err:
            return handle_service_error(err)

    try:
        data = {**(req.get_json(silent=True) or {}), **dict(req.args or {})}
        dto = CampaignIdRequestDTO.model_validate(data)
        sender_service.cancel_scheduled_campaign(dto.id)
        return jsonify({"cancelled": True}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def admin_sender_campaign_copy(req):
    sender_service = get_sender_service()
    try:
        dto = CampaignIdRequestDTO.model_validate(req.get_json(silent=True) or {})
        return jsonify(sender_service.copy_campaign(dto.id) or {}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_sender_campaign_stats(req):
    sender_service = get_sender_service()
    try:
        dto = CampaignStatsQueryDTO.model_validate(dict(req.args or {}))
        handlers = {
            "opens": sender_service.get_campaign_opens,
            "clicks": sender_service.get_campaign_clicks,
            "unsubscribes": sender_service.get_campaign_unsubscribes,
            "bounces_hard": sender_service.get_campaign_bounces_hard,
            "bounces_soft": sender_service.get_campaign_bounces_soft,
        }
        return jsonify(handlers[dto.type](dto.id) or {}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
