import logging
from firebase_functions import https_fn
from config.firebase_config import cors
from services.admin.auth_services import require_admin
from services.admin.events_service import EventsService
from config.firebase_config import region

from flask import jsonify

logger = logging.getLogger('AdminEventsAPI')
events_service = EventsService()


@https_fn.on_request(cors=cors, region = region)
@require_admin
def admin_create_event(req):
    logger.debug("admin_create_event called")

    if req.method != 'POST':
        logger.debug("Invalid method for admin_create_event")
        return 'Invalid request method', 405

    req_json = req.get_json()
    logger.debug(f"Request JSON: {req_json}")
    if not req_json:
        return jsonify({'error': 'Missing request body'}), 400

    try:
        admin_uid = req.admin_token['uid']
        logger.debug(f"Admin UID: {admin_uid}")
        response, status = events_service.create_event(req_json, admin_uid)
        logger.info("Event created successfully")
        return response, status
    except Exception as e:
        logger.error(f"[admin_create_event] {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_update_event(req):
    logger.debug("admin_update_event called")

    if req.method != 'PUT':
        logger.debug("Invalid method for admin_update_event")
        return 'Invalid request method', 405

    req_json = req.get_json()
    logger.debug(f"Request JSON: {req_json}")
    if not req_json or 'id' not in req_json:
        return jsonify({'error': 'Missing event ID'}), 400

    try:
        print(req_json)
        event_id = req_json.pop('id')
        admin_uid = req.admin_token['uid']
        logger.debug(f"Updating event {event_id} by admin {admin_uid}")
        response, status = events_service.update_event(event_id, req_json, admin_uid)
        logger.info(f"Event {event_id} updated successfully")
        return response, status
    except Exception as e:
        logger.error(f"[admin_update_event] {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_delete_event(req):
    logger.debug("admin_delete_event called")

    if req.method != 'DELETE':
        logger.debug("Invalid method for admin_delete_event")
        return 'Invalid request method', 405

    try:
        req_json = req.get_json()
        logger.debug(f"Request body: {req_json}")

        if not req_json or 'id' not in req_json:
            return jsonify({'error': 'Missing event ID'}), 400

        event_id = req_json['id']
        admin_uid = req.admin_token['uid']
        logger.debug(f"Deleting event {event_id} by admin {admin_uid}")

        response, status = events_service.delete_event(event_id, admin_uid)
        logger.info(f"Event {event_id} deleted successfully")
        return response, status

    except Exception as e:
        logger.error(f"[admin_delete_event] {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_get_all_events(req):
    logger.debug("admin_get_all_events called")

    if req.method != 'GET':
        logger.debug("Invalid method for admin_get_all_events")
        return 'Invalid request method', 405

    try:
        response, status = events_service.get_all_events()
        logger.info("Fetched all events successfully")
        return response, status
    except Exception as e:
        logger.error(f"[admin_get_all_events] {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_get_event_by_id(req):
    logger.debug("admin_get_event_by_id called")

    if req.method != 'GET':
        logger.debug("Invalid method for admin_get_event_by_id")
        return 'Invalid request method', 405

    event_id = req.args.get('id')
    logger.debug(f"Query param eventId: {event_id}")
    if not event_id:
        return jsonify({'error': 'Missing event ID'}), 400

    try:
        response, status = events_service.get_event_by_id(event_id)
        logger.info(f"Event {event_id} fetched successfully")
        return response, status
    except Exception as e:
        logger.error(f"[admin_get_event_by_id] {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_upload_event_photo(req):
    logger.debug("admin_upload_event_photo called")

    if req.method != 'POST':
        logger.debug("Invalid method for admin_upload_event_photo")
        return 'Invalid request method', 405

    req_json = req.get_json()
    logger.debug(f"Request JSON: {req_json}")
    if not req_json or 'eventId' not in req_json or 'photo' not in req_json:
        return jsonify({'error': 'Missing eventId or photo'}), 400

    try:
        event_id = req_json['eventId']
        photo_data = req_json['image']
        admin_uid = req.admin_token['uid']
        logger.debug(f"Uploading photo for event {event_id} by admin {admin_uid}")
        response, status = events_service.upload_event_photo(event_id, photo_data, admin_uid)
        logger.info(f"Photo uploaded for event {event_id}")
        return response, status
    except Exception as e:
        logger.error(f"[admin_upload_event_photo] {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500