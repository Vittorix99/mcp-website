from firebase_functions import https_fn
from flask import jsonify, request
from config.firebase_config import cors
from services.events_service import (
    get_all_events_service,
    get_next_event_service,
    get_event_by_id_service
)
from utils.events_utils import sanitize_event
from config.firebase_config import region


@https_fn.on_request(cors=cors, region=region)
def get_all_events(req):
    """API to get all events"""
    if req.method != 'GET':
        return 'Invalid request method', 405

    response, status = get_all_events_service()

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

    response, status = get_next_event_service()

    if status == 200:
        event = response.get_json()
        return jsonify(sanitize_event(event)), 200
    return response, status

@https_fn.on_request(cors=cors, region=region)
def get_event_by_id(req):
    """API to get event details by ID"""
    if req.method != 'GET':
        return 'Invalid request method', 405

    event_id = req.args.get('id')
    if not event_id:
        return {'error': 'Missing event ID'}, 400

    response, status = get_event_by_id_service(event_id)

    if status == 200:
        event = response.get_json()
        return jsonify(sanitize_event(event)), 200
    return response, status