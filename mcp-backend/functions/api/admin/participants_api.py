from firebase_functions import https_fn
from config.firebase_config import cors
from services.auth_service import require_admin
from services.participants_service import ParticipantsService
from services.location_service import LocationService
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

    return participants_service.get_all(data['eventId'])


@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_participant(req):
    """Admin: get a single participant by ID"""
    if req.method != 'POST':
        return 'Invalid request method', 405

    data = req.get_json()
    if not data or 'participantId' not in data:
        return {'error': 'Missing participantId'}, 400

    return participants_service.get_by_id(data['participantId'])


@https_fn.on_request(cors=cors, region=region)
@require_admin
def create_participant(req):
    """Admin: create a new participant"""
    if req.method != 'POST':
        return 'Invalid request method', 405

    data = req.get_json()
    if not data or 'event_id' not in data:
        return {'error': 'Missing participant data or event_id'}, 400

    return participants_service.create(data)


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
    return participants_service.update(event_id, participant_id, data)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def delete_participant(req):
    """Admin: delete a participant"""
    if req.method != 'DELETE':
        return 'Invalid request method', 405

    data = req.get_json()
    if not data or 'participantId' not in data or 'event_id' not in data:
        return {'error': 'Missing participantId or event_id'}, 400

    return participants_service.delete(data['event_id'], data['participantId'])





@https_fn.on_request(cors=cors, region=region)
@require_admin
def send_ticket(req):
    """Reinvia il ticket via email"""
    req_json = req.get_json()
    event_id = req_json.get("eventId")
    participant_id = req_json.get("participantId")

    if not event_id or not participant_id:
        return {"error": "Missing eventId or participantId"}, 400

    return participants_service.send_ticket(event_id, participant_id)




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

    return location_service.send_location(event_id, participant_id, address, link, message)

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

    return location_service.start_send_location_job(event_id, address, link, message)
