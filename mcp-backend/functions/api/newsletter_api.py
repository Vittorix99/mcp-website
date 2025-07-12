from firebase_functions import https_fn
from config.firebase_config import cors, region
from services.admin.auth_services import require_admin
from services.newsletter_service import NewsletterService

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

    return newsletter_service.signup(data)



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

