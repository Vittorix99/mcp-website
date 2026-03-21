from firebase_functions import https_fn
from config.firebase_config import cors, region
from services.communications.newsletter_service import NewsletterService
from services.sender.sender_sync import sync_newsletter_signup_to_sender

newsletter_service = NewsletterService()

@https_fn.on_request(cors=cors, region=region)
def newsletter_signup(req):
    """Public: Handle newsletter signup"""
    if req.method != "POST":
        return {"error": "Invalid request method"}, 405

    try:
        data = req.get_json()
    except Exception:
        return {"error": "Invalid JSON"}, 400

    if not data or "email" not in data:
        return {"error": "Missing email"}, 400

    result = newsletter_service.signup(data)

    # Sync to Sender (fire-and-forget, does not affect response)
    try:
        sync_newsletter_signup_to_sender(
            email=data.get("email", ""),
            name=data.get("name"),
        )
    except Exception as exc:
        print(f"[newsletter_signup] Sender sync failed: {exc}")

    return result



@https_fn.on_request(cors=cors, region=region)
def newsletter_participants(req):
    """Admin: Add newsletter participants in bulk"""
    if req.method != "POST":
        return {"error": "Invalid request method"}, 405

    try:
        data = req.get_json()
    except Exception:
        return {"error": "Invalid JSON"}, 400

    if not data or "participants" not in data:
        return {"error": "Missing participants"}, 400

    participants = data.get("participants", [])
    return newsletter_service.add_participants(participants)
