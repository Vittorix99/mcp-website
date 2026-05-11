from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import member_endpoint
from dto.member_api import MemberEventQueryDTO
from errors.service_errors import NotFoundError
from services.events.location_service import LocationService
from utils.http_responses import handle_pydantic_error, handle_service_error

location_service = LocationService()


@member_endpoint(methods=("GET",))
def member_get_event_location(req):
    try:
        dto = MemberEventQueryDTO.model_validate(dict(req.args or {}))
        result = location_service.get_member_location(dto.event_id)
        return jsonify(result.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except NotFoundError as err:
        return jsonify({"error": str(err)}), 404
    except Exception as err:
        return handle_service_error(err)
