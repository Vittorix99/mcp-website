from firebase_functions import https_fn
from flask import jsonify, request
from config.firebase_config import cors
from services.events_service import (
    create_event_service,
    get_all_events_service,
    update_event_service,
    delete_event_service,
    get_next_event_service,
    get_event_by_id_service
)



@https_fn.on_request(cors=cors)
def get_all_events(req):
    """API to get all events"""
    if req.method != 'GET':
        return 'Invalid request method', 405

    return get_all_events_service()

@https_fn.on_request(cors=cors)
def update_event(req):
    """API to update an event"""
    if req.method != 'PUT':
        return 'Invalid request method', 405

    req_json = req.get_json()
    if not req_json:
        return {'error': 'Missing required fields'}, 400

    return update_event_service(req_json)

@https_fn.on_request(cors=cors)
def delete_event(req):
    """API to delete an event"""
    if req.method != 'DELETE':
        return 'Invalid request method', 405

    event_id = req.args.get('id')
    if not event_id:
        return {'error': 'Missing event ID'}, 400

    return delete_event_service(event_id)

@https_fn.on_request(cors=cors)
def get_next_event2(req):
    """API to get the next upcoming event"""
    if req.method != 'GET':
        return 'Invalid request method', 405

    return get_next_event_service()

@https_fn.on_request(cors=cors)
def get_event_by_id(req):
    """API to get event details by ID"""
    event_id = req.args.get('id')
    if not event_id:
        return {'error': 'Missing event ID'}, 400

    return get_event_by_id_service(event_id)