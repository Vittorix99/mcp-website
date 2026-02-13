import logging
from firebase_functions import https_fn
from config.firebase_config import cors
from services.auth_service import require_admin
from services.events_service import EventsService
from services.service_errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from config.firebase_config import region

from flask import jsonify
from api.validators import (
    CREATE_EVENT_SCHEMA,
    DELETE_EVENT_SCHEMA,
    EVENT_ID_QUERY_SCHEMA,
    UPDATE_EVENT_SCHEMA,
    inject_payload_dto,
    inject_payload_fields,
    inject_query_params,
    require_json_body,
    validate_body_fields,
    validate_query_params,
)
from dto import EventDTO

logger = logging.getLogger("AdminEventsAPI")
events_service = EventsService()


def _handle_service_error(err: Exception):
    if isinstance(err, ValidationError):
        return jsonify({"error": str(err)}), 400
    if isinstance(err, ForbiddenError):
        return jsonify({"error": str(err)}), 403
    if isinstance(err, NotFoundError):
        return jsonify({"error": str(err)}), 404
    if isinstance(err, ConflictError):
        return jsonify({"error": str(err)}), 409
    if isinstance(err, ServiceError):
        return jsonify({"error": str(err)}), 500
    return jsonify({"error": "Internal server error"}), 500


@https_fn.on_request(cors=cors, region=region)
@require_admin
@require_json_body
@validate_body_fields(CREATE_EVENT_SCHEMA, allow_extra=True)
@inject_payload_dto(EventDTO, arg_name="event_dto", exclude=("id",))
def admin_create_event(req, event_dto):
    logger.debug("admin_create_event called")

    if req.method != "POST":
        logger.debug("Invalid method for admin_create_event")
        return "Invalid request method", 405

    try:
        admin_uid = req.admin_token["uid"]
        logger.debug(f"Admin UID: {admin_uid}")
        print("[admin_create_event] raw request json:", req.get_json(silent=True))
        print("[admin_create_event] dto payload:", event_dto.to_payload())
        payload = events_service.create_event(event_dto, admin_uid)
        logger.info("Event created successfully")
        return jsonify(payload), 201
    except Exception as e:
        logger.error(f"[admin_create_event] {str(e)}")
        return _handle_service_error(e)


@https_fn.on_request(cors=cors, region=region)
@require_admin
@require_json_body
@validate_body_fields(UPDATE_EVENT_SCHEMA, allow_extra=True)
@inject_payload_dto(EventDTO, arg_name="event_dto", exclude=("id",))
@inject_payload_fields(["id"])
def admin_update_event(req, id, event_dto):
    logger.debug("admin_update_event called")

    if req.method != "PUT":
        logger.debug("Invalid method for admin_update_event")
        return "Invalid request method", 405

    try:
        event_id = id
        admin_uid = req.admin_token["uid"]
        logger.debug(f"Updating event {event_id} by admin {admin_uid}")
        raw_payload = req.get_json(silent=True) or {}
        print(f"[admin_update_event] raw request json (id={event_id}):", raw_payload)
        print(f"[admin_update_event] dto payload (id={event_id}):", event_dto.to_payload())
        payload = events_service.update_event(
            event_id,
            event_dto,
            admin_uid,
        )
        logger.info(f"Event {event_id} updated successfully")
        return jsonify(payload), 200
    except Exception as e:
        logger.error(f"[admin_update_event] {str(e)}")
        return _handle_service_error(e)


@https_fn.on_request(cors=cors, region=region)
@require_admin
@require_json_body
@validate_body_fields(DELETE_EVENT_SCHEMA, allow_extra=False)
@inject_payload_fields(["id"])
def admin_delete_event(req, id):
    logger.debug("admin_delete_event called")

    if req.method != "DELETE":
        logger.debug("Invalid method for admin_delete_event")
        return "Invalid request method", 405

    try:
        event_id = id
        admin_uid = req.admin_token["uid"]
        logger.debug(f"Deleting event {event_id} by admin {admin_uid}")

        payload = events_service.delete_event(event_id, admin_uid)
        logger.info(f"Event {event_id} deleted successfully")
        return jsonify(payload), 200

    except Exception as e:
        logger.error(f"[admin_delete_event] {str(e)}")
        return _handle_service_error(e)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_get_all_events(req):
    logger.debug("admin_get_all_events called")

    if req.method != 'GET':
        logger.debug("Invalid method for admin_get_all_events")
        return 'Invalid request method', 405

    try:
        payload = events_service.get_all_events()
        logger.info("Fetched all events successfully")
        return jsonify(payload), 200
    except Exception as e:
        logger.error(f"[admin_get_all_events] {str(e)}")
        return _handle_service_error(e)


@https_fn.on_request(cors=cors, region=region)
@require_admin
@validate_query_params(EVENT_ID_QUERY_SCHEMA, allow_extra=False)
@inject_query_params(["id", "slug"], allow_missing=True)
def admin_get_event_by_id(req, id=None, slug=None):
    logger.debug("admin_get_event_by_id called")

    if req.method != 'GET':
        logger.debug("Invalid method for admin_get_event_by_id")
        return 'Invalid request method', 405

    event_id = id
    logger.debug(f"Query param eventId: {event_id} slug: {slug}")
    if not event_id and not slug:
        return jsonify({"error": "Missing event ID or slug"}), 400

    try:
        payload = events_service.get_event_by_id(event_id, slug=slug)
        logger.info(f"Event {event_id} fetched successfully")
        return jsonify(payload), 200
    except Exception as e:
        logger.error(f"[admin_get_event_by_id] {str(e)}")
        return _handle_service_error(e)
