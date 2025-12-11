from firebase_functions import https_fn
from config.firebase_config import cors, region
from services.auth_service import require_admin
from services.newsletter_service import NewsletterService

newsletter_service = NewsletterService()
@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_get_newsletter_signups(req):
    """Admin: Get all or specific newsletter signups"""
    if req.method != "GET":
        return {"error": "Invalid request method"}, 405

    signup_id = req.args.get("id")
    if signup_id:
        return newsletter_service.get_by_id(signup_id)
    else:
        return newsletter_service.get_all()


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_update_newsletter_signup(req):
    """Admin: Update a newsletter signup"""
    if req.method != "PUT":
        return {"error": "Invalid request method"}, 405

    try:
        data = req.get_json()
    except Exception:
        return {"error": "Invalid JSON"}, 400

    if not data or "id" not in data:
        return {"error": "Missing signup ID"}, 400

    signup_id = data.pop("id")
    return newsletter_service.update(signup_id, data)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_delete_newsletter_signup(req):
    """Admin: Delete a newsletter signup"""
    if req.method != "DELETE":
        return {"error": "Invalid request method"}, 405

    signup_id = req.args.get("id")
    if not signup_id:
        return {"error": "Missing signup ID"}, 400

    return newsletter_service.delete(signup_id)
