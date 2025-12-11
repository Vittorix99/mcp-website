from firebase_functions import https_fn
from flask import jsonify
from config.firebase_config import cors
from services.participants_service import ParticipantsService
from config.firebase_config import region

participants_service = ParticipantsService()

@https_fn.on_request(cors=cors, region=region)
def check_participants(req):
    """API to verify participants are not duplicated or already registered"""
    if req.method != "POST":
        return "Invalid request method", 405

    data = req.get_json()
    if not data or "participants" not in data or "eventId" not in data:
        return jsonify({"error": "Missing participants or event ID"}), 400

    return participants_service.check_participants(data.get("eventId"), data.get("participants"))

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
