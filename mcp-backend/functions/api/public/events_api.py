from firebase_functions import https_fn
from flask import jsonify, request
from config.firebase_config import cors
from services.events.events_service import EventsService
from errors.service_errors import NotFoundError, ServiceError, ValidationError
from utils.events_utils import sanitize_event
from config.firebase_config import region

events_service = EventsService()

def _handle_service_error(err: Exception):
    if isinstance(err, ValidationError):
        return jsonify({"error": str(err)}), 400
    if isinstance(err, NotFoundError):
        return jsonify({"error": str(err)}), 404
    if isinstance(err, ServiceError):
        return jsonify({"error": str(err)}), 500
    return jsonify({"error": "Internal server error"}), 500


@https_fn.on_request(cors=cors, region=region)
def get_all_events(req):
    """API to get all events"""
    if req.method != 'GET':
        return 'Invalid request method', 405

    view = req.args.get("view")
    try:
        events = events_service.list_public_events(view=view)
        if view:
            return jsonify(events), 200
        sanitized_events = [sanitize_event(event) for event in events]
        return jsonify(sanitized_events), 200
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
def get_next_event(req):
    """API to get the next upcoming event"""
    if req.method != 'GET':
        return 'Invalid request method', 405

    try:
        events = events_service.get_next_public_event()
        sanitized = [sanitize_event(event) for event in events]
        return jsonify(sanitized), 200
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
def get_event_by_id(req):
    """API to get event details by ID"""
    if req.method != 'GET':
        return 'Invalid request method', 405

    event_id = req.args.get('id')
    slug = req.args.get('slug')
    if not event_id and not slug:
        return {'error': 'Missing event ID or slug'}, 400
    print(f"Fetching event with ID: {event_id} slug: {slug}")
    try:
        event = events_service.get_public_event_by_id(event_id, slug=slug)
        return jsonify(sanitize_event(event)), 200
    except Exception as err:
        return _handle_service_error(err)
