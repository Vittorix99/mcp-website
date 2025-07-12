from firebase_functions import https_fn
from flask import jsonify, request
from config.firebase_config import cors
from services.event_tickets_service import (

    check_participants_service,
    
)
from config.firebase_config import region



@https_fn.on_request(cors=cors, region=region)
def check_participants(req):
    """API to verify participants are not duplicated or already registered"""
    if req.method != "POST":
        return "Invalid request method", 405

    data = req.get_json()
    if not data or "participants" not in data or "eventId" not in data:
        return jsonify({"error": "Missing participants or event ID"}), 400

    return check_participants_service(data)

# ✅ Placeholder per `notify_location_service` (da implementare)
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