from firebase_functions import https_fn
from flask import jsonify, request
from config.firebase_config import cors
from services.events_service import EventsService
from utils.events_utils import sanitize_event
from config.firebase_config import region

events_service = EventsService()


@https_fn.on_request(cors=cors, region=region)
def get_all_events(req):
    """API to get all events"""
    if req.method != 'GET':
        return 'Invalid request method', 405

    response, status = events_service.list_public_events()

    if status == 200:
        events = response.get_json()
        sanitized_events = [sanitize_event(event) for event in events]
        return jsonify(sanitized_events), 200
    return response, status

@https_fn.on_request(cors=cors, region=region)
def get_next_event(req):
    """API to get the next upcoming event"""
    if req.method != 'GET':
        return 'Invalid request method', 405

    response, status = events_service.get_next_public_event()

    if status == 200:
        events = response.get_json() or []
        sanitized = [sanitize_event(event) for event in events]
        return jsonify(sanitized), 200
    return response, status

@https_fn.on_request(cors=cors, region=region)
def get_event_by_id(req):
    """API to get event details by ID"""
    if req.method != 'GET':
        return 'Invalid request method', 405

    event_id = req.args.get('id')
    if not event_id:
        return {'error': 'Missing event ID'}, 400

    response, status = events_service.get_public_event_by_id(event_id)

    if status == 200:
        event = response.get_json()
        return jsonify(sanitize_event(event)), 200
    return response, status
