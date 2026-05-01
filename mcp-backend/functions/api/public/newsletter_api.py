import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import public_endpoint
from dto.newsletter_api import NewsletterSignupRequestDTO
from services.communications.newsletter_service import NewsletterService
from services.sender.sender_sync import sync_newsletter_signup_to_sender
from utils.http_responses import handle_pydantic_error, handle_service_error

logger = logging.getLogger("PublicNewsletterAPI")
newsletter_service = NewsletterService()


@public_endpoint(methods=("POST",))
def newsletter_signup(req):
    try:
        dto = NewsletterSignupRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = newsletter_service.signup(dto)

        try:
            sync_newsletter_signup_to_sender(email=dto.email, name=dto.name)
        except Exception as exc:
            logger.warning("[newsletter_signup] Sender sync failed: %s", exc)

        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
