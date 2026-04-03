from firebase_functions import https_fn
from config.firebase_config import cors
from services.core.auth_service import require_admin
from services.events.participants_service import ParticipantsService
from services.events.location_service import LocationService
from errors.service_errors import (
    ConflictError,
    ExternalServiceError,
    ForbiddenError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from config.firebase_config import region

location_service = LocationService()

participants_service = ParticipantsService()

@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_participants_by_event(req):
    """Admin: get participants for an event"""
    if req.method != 'POST':
        return 'Invalid request method', 405

    data = req.get_json()
    if not data or 'eventId' not in data:
        return {'error': 'Missing eventId'}, 400

    try:
        payload = participants_service.get_all(data['eventId'])
        return payload, 200
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_participant(req):
    """Admin: get a single participant by ID"""
    if req.method != 'POST':
        return 'Invalid request method', 405

    data = req.get_json()
    event_id = data.get("eventId") or data.get("event_id") if data else None
    participant_id = data.get("participantId") if data else None
    if not event_id or not participant_id:
        return {'error': 'Missing participantId or eventId'}, 400

    try:
        payload = participants_service.get_by_id(event_id, participant_id)
        return payload, 200
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def create_participant(req):
    """Admin: create a new participant"""
    if req.method != 'POST':
        return 'Invalid request method', 405

    data = req.get_json()
    if not data or 'event_id' not in data:
        return {'error': 'Missing participant data or event_id'}, 400

    try:
        payload = participants_service.create(data)
        return payload, 201
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def update_participant(req):
    """Admin: update an existing participant"""
    if req.method != 'PUT':
        return 'Invalid request method', 405

    data = req.get_json()
    print(data)
    if not data or 'participantId' not in data or 'event_id' not in data:
        return {'error': 'Missing participantId or event_id'}, 400

    participant_id = data.pop('participantId')
    event_id = data.pop('event_id')
    try:
        payload = participants_service.update(event_id, participant_id, data)
        return payload, 200
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def delete_participant(req):
    """Admin: delete a participant"""
    if req.method != 'DELETE':
        return 'Invalid request method', 405

    data = req.get_json()
    if not data or 'participantId' not in data or 'event_id' not in data:
        return {'error': 'Missing participantId or event_id'}, 400

    try:
        payload = participants_service.delete(data['event_id'], data['participantId'])
        return payload, 200
    except Exception as err:
        return _handle_service_error(err)





@https_fn.on_request(cors=cors, region=region)
@require_admin
def send_ticket(req):
    """Reinvia il ticket via email"""
    req_json = req.get_json()
    event_id = req_json.get("eventId")
    participant_id = req_json.get("participantId")

    if not event_id or not participant_id:
        return {"error": "Missing eventId or participantId"}, 400

    try:
        payload = participants_service.send_ticket(event_id, participant_id)
        return payload, 200
    except Exception as err:
        return _handle_service_error(err)




@https_fn.on_request(cors=cors, region=region)
@require_admin
def send_location(req):
    if req.method != 'POST':
        return {'error': 'Invalid request method'}, 405

    body = req.get_json()
    event_id = body.get("eventId")
    participant_id = body.get("participantId")
    address = body.get("address")
    link = body.get("link")
    message = body.get("message")

    try:
        payload = location_service.send_location(event_id, participant_id, address, link, message)
        return payload, 200
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors)
@require_admin
def send_location_to_all(req):
    if req.method != 'POST':
        return {'error': 'Invalid request method'}, 405

    body = req.get_json()
    event_id = body.get("eventId")
    address = body.get("address")
    link = body.get("link")
    message = body.get("message")

    try:
        payload = location_service.start_send_location_job(event_id, address, link, message)
        return payload, 202
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def send_omaggio_emails(req):
    """Invia email personalizzate agli omaggi dell'evento."""
    if req.method != 'POST':
        return {'error': 'Invalid request method'}, 405

    body = req.get_json()
    event_id = body.get("eventId") if body else None
    entry_time = body.get("entryTime") if body else None
    participant_id = body.get("participantId") if body else None
    skip_already_sent = body.get("skipAlreadySent", True) if body else True

    if not event_id:
        return {'error': 'Missing eventId'}, 400

    try:
        payload = participants_service.send_omaggio_emails(
            event_id,
            entry_time,
            participant_id=participant_id,
            skip_already_sent=bool(skip_already_sent),
        )
        return payload, 200
    except Exception as err:
        return _handle_service_error(err)


def _handle_service_error(err: Exception):
    if isinstance(err, ValidationError):
        return {"error": str(err)}, 400
    if isinstance(err, ConflictError):
        return {"error": str(err)}, 409
    if isinstance(err, ForbiddenError):
        return {"error": str(err)}, 403
    if isinstance(err, NotFoundError):
        return {"error": str(err)}, 404
    if isinstance(err, ExternalServiceError):
        return {"error": str(err)}, 502
    if isinstance(err, ServiceError):
        return {"error": str(err)}, 500
    return {"error": "Internal server error"}, 500
