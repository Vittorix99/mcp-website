import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.newsletter_api import (
    NewsletterDeleteQueryDTO,
    NewsletterLookupQueryDTO,
    NewsletterUpdateRequestDTO,
)
from services.communications.newsletter_service import NewsletterService
from utils.http_responses import handle_pydantic_error, handle_service_error

logger = logging.getLogger("AdminNewsletterAPI")
newsletter_service = NewsletterService()


@admin_endpoint(methods=("GET",))
def admin_get_newsletter_signups(req):
    logger.debug("admin_get_newsletter_signups called")
    try:
        dto = NewsletterLookupQueryDTO.model_validate(dict(req.args or {}))
        if dto.id:
            payload = newsletter_service.get_signup_by_id(dto.id)
        else:
            payload = newsletter_service.get_all_signups()
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_get_newsletter_signups] %s", str(err))
        return handle_service_error(err)


@admin_endpoint(methods=("PUT",))
def admin_update_newsletter_signup(req):
    logger.debug("admin_update_newsletter_signup called")
    try:
        dto = NewsletterUpdateRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = newsletter_service.update_signup(dto)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_update_newsletter_signup] %s", str(err))
        return handle_service_error(err)


@admin_endpoint(methods=("DELETE",))
def admin_delete_newsletter_signup(req):
    logger.debug("admin_delete_newsletter_signup called")
    try:
        dto = NewsletterDeleteQueryDTO.model_validate(dict(req.args or {}))
        payload = newsletter_service.delete_signup(dto.id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[admin_delete_newsletter_signup] %s", str(err))
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_get_newsletter_consents(req):
    logger.debug("admin_get_newsletter_consents called")
    try:
        payload = newsletter_service.get_all_consents()
        return jsonify(payload.to_payload()), 200
    except Exception as err:
        logger.error("[admin_get_newsletter_consents] %s", str(err))
        return handle_service_error(err)
