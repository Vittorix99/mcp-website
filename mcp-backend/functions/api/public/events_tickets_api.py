from firebase_functions import https_fn
from flask import jsonify
from config.firebase_config import cors, region
from services.events.participants_service import ParticipantsService
from errors.service_errors import ExternalServiceError, NotFoundError, ServiceError, ValidationError, ForbiddenError

participants_service = ParticipantsService()

@https_fn.on_request(cors=cors, region=region)
def check_participants(req):
    """API to verify participants are not duplicated or already registered"""
    if req.method != "POST":
        return "Invalid request method", 405

    data = req.get_json()
    if not data or "participants" not in data or "eventId" not in data:
        return jsonify({"error": "Missing participants or event ID"}), 400

    try:
        payload = participants_service.check_participants(data.get("eventId"), data.get("participants"))
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)


def _handle_service_error(err: Exception):
    if isinstance(err, ValidationError):
        details = getattr(err, "details", None)
        if details:
            return jsonify({"error": "validation_error", "messages": details}), 400
        return jsonify({"error": str(err)}), 400
    if isinstance(err, ForbiddenError):
        return jsonify({"error": str(err)}), 403
    if isinstance(err, NotFoundError):
        return jsonify({"error": str(err)}), 404
    if isinstance(err, ExternalServiceError):
        return jsonify({"error": str(err)}), 502
    if isinstance(err, ServiceError):
        return jsonify({"error": str(err)}), 500
    return jsonify({"error": "Internal server error"}), 500

# Placeholder per `notify_location_service` (da implementare)
def notify_location_service(data: dict) -> dict:
    """
    Logic to notify users about event location.

    Args:
        data (dict): Expected to contain at least `eventId`.

    Returns:
        dict: Response object
    """
    # TODO: implement notification logic (e.g., via FCM, email, etc.)
    return {
        "status": "notified",
        "eventId": data.get("eventId"),
        "message": "Location notifications sent (simulation)"
    }
