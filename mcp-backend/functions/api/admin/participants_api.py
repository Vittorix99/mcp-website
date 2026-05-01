from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.participant_api import (
    ParticipantCreateRequestDTO,
    ParticipantEventRequestDTO,
    ParticipantLookupRequestDTO,
    ParticipantUpdateRequestDTO,
    SendLocationRequestDTO,
    SendLocationToAllRequestDTO,
    SendOmaggioEmailsRequestDTO,
    SendTicketRequestDTO,
)
from services.events.participants_service import ParticipantsService
from services.events.location_service import LocationService
from utils.http_responses import handle_pydantic_error, handle_service_error

location_service = LocationService()

participants_service = ParticipantsService()

@admin_endpoint(methods=("POST",))
def get_participants_by_event(req):
    """Admin: get participants for an event"""
    try:
        dto = ParticipantEventRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = participants_service.get_all(dto.event_id)
        return jsonify([item.to_payload() for item in payload]), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def get_participant(req):
    """Admin: get a single participant by ID"""
    try:
        dto = ParticipantLookupRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = participants_service.get_by_id(dto.event_id, dto.participant_id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def create_participant(req):
    """Admin: create a new participant"""
    try:
        dto = ParticipantCreateRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = participants_service.create(dto)
        return jsonify(payload.to_payload()), 201
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("PUT",))
def update_participant(req):
    """Admin: update an existing participant"""
    try:
        dto = ParticipantUpdateRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = participants_service.update(dto.event_id, dto.participant_id, dto)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("DELETE",))
def delete_participant(req):
    """Admin: delete a participant"""
    try:
        dto = ParticipantLookupRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = participants_service.delete(dto.event_id, dto.participant_id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)





@admin_endpoint(methods=("POST",))
def send_ticket(req):
    """Reinvia il ticket via email"""
    try:
        dto = SendTicketRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = participants_service.send_ticket(dto.event_id, dto.participant_id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)




@admin_endpoint(methods=("POST",))
def send_location(req):
    try:
        dto = SendLocationRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = location_service.send_location(dto)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)

@admin_endpoint(methods=("POST",))
def send_location_to_all(req):
    try:
        dto = SendLocationToAllRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = location_service.start_send_location_job(dto)
        return jsonify(payload.to_payload()), 202
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def send_omaggio_emails(req):
    """Invia email personalizzate agli omaggi dell'evento."""
    try:
        dto = SendOmaggioEmailsRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = participants_service.send_omaggio_emails(dto)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
