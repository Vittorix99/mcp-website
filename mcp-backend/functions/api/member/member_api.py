from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import member_endpoint
from dto.member_api import MemberEventQueryDTO, MemberPreferencesPatchDTO
from errors.service_errors import NotFoundError, ValidationError
from services.memberships.member_service import MemberService
from utils.http_responses import handle_pydantic_error, handle_service_error

member_service = MemberService()


def _token_claims(req):
    token = req.member_token
    email, uid = token.get("email"), token.get("uid")
    if not isinstance(email, str) or not email.strip() or not isinstance(uid, str) or not uid:
        raise ValidationError("Account identity is missing")
    return email.strip().lower(), uid, token.get("email_verified") is True


@member_endpoint(methods=("GET",))
def member_get_me(req):
    try:
        email, uid, email_verified = _token_claims(req)
        payload = member_service.get_me(email, uid, email_verified=email_verified)
        return jsonify(payload.to_payload()), 200
    except (NotFoundError, ValidationError) as err:
        status = 404 if isinstance(err, NotFoundError) else 401
        return jsonify({"error": str(err)}), status
    except Exception as err:
        return handle_service_error(err)


@member_endpoint(methods=("GET",))
def member_get_events(req):
    try:
        email, uid, email_verified = _token_claims(req)
        events = member_service.get_attended_events(email, uid, email_verified=email_verified)
        return jsonify([e.to_payload() for e in events]), 200
    except (NotFoundError, ValidationError) as err:
        status = 404 if isinstance(err, NotFoundError) else 401
        return jsonify({"error": str(err)}), status
    except Exception as err:
        return handle_service_error(err)


@member_endpoint(methods=("GET",))
def member_get_purchases(req):
    try:
        email, uid, email_verified = _token_claims(req)
        purchases = member_service.get_purchases(email, uid, email_verified=email_verified)
        return jsonify([p.to_payload() for p in purchases]), 200
    except (NotFoundError, ValidationError) as err:
        status = 404 if isinstance(err, NotFoundError) else 401
        return jsonify({"error": str(err)}), status
    except Exception as err:
        return handle_service_error(err)


@member_endpoint(methods=("GET",))
def member_get_ticket(req):
    try:
        dto = MemberEventQueryDTO.model_validate(dict(req.args or {}))
        email, uid, email_verified = _token_claims(req)
        payload = member_service.get_ticket(email, uid, dto.event_id, email_verified=email_verified)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except (NotFoundError, ValidationError) as err:
        status = 404 if isinstance(err, NotFoundError) else 401
        return jsonify({"error": str(err)}), status
    except Exception as err:
        return handle_service_error(err)


@member_endpoint(methods=("PATCH",))
def member_patch_preferences(req):
    try:
        dto = MemberPreferencesPatchDTO.model_validate(req.get_json(silent=True) or {})
        email, uid, email_verified = _token_claims(req)
        result = member_service.patch_preferences(email, uid, dto.newsletter_consent, email_verified=email_verified)
        return jsonify(result), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except (NotFoundError, ValidationError) as err:
        status = 404 if isinstance(err, NotFoundError) else 401
        return jsonify({"error": str(err)}), status
    except Exception as err:
        return handle_service_error(err)
