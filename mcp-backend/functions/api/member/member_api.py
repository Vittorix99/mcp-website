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
    email = (token.get("email") or "").strip().lower()
    uid = token.get("uid", "")
    return email, uid


@member_endpoint(methods=("GET",))
def member_get_me(req):
    try:
        email, uid = _token_claims(req)
        payload = member_service.get_me(email, uid)
        return jsonify(payload.to_payload()), 200
    except (NotFoundError, ValidationError) as err:
        status = 404 if isinstance(err, NotFoundError) else 401
        return jsonify({"error": str(err)}), status
    except Exception as err:
        return handle_service_error(err)


@member_endpoint(methods=("GET",))
def member_get_events(req):
    try:
        email, uid = _token_claims(req)
        events = member_service.get_attended_events(email, uid)
        return jsonify([e.to_payload() for e in events]), 200
    except (NotFoundError, ValidationError) as err:
        status = 404 if isinstance(err, NotFoundError) else 401
        return jsonify({"error": str(err)}), status
    except Exception as err:
        return handle_service_error(err)


@member_endpoint(methods=("GET",))
def member_get_purchases(req):
    try:
        email, uid = _token_claims(req)
        purchases = member_service.get_purchases(email, uid)
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
        email, uid = _token_claims(req)
        payload = member_service.get_ticket(email, uid, dto.event_id)
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
        email, uid = _token_claims(req)
        result = member_service.patch_preferences(email, uid, dto.newsletter_consent)
        return jsonify(result), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except (NotFoundError, ValidationError) as err:
        status = 404 if isinstance(err, NotFoundError) else 401
        return jsonify({"error": str(err)}), status
    except Exception as err:
        return handle_service_error(err)
