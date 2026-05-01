from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import public_endpoint
from dto.participant_api import CheckParticipantsRequestDTO
from services.events.participants_service import ParticipantsService
from utils.http_responses import handle_pydantic_error, handle_service_error

participants_service = ParticipantsService()

@public_endpoint(methods=("POST",))
def check_participants(req):
    """API to verify participants are not duplicated or already registered"""
    try:
        dto = CheckParticipantsRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = participants_service.check_participants(dto.event_id, dto.participants)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
