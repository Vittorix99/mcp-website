from firebase_functions import https_fn
from config.firebase_config import cors, region
from services.core.auth_service import require_admin
from .helpers import get_payload, get_query_params, pick, get_sender_service


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_fields(req):
    svc = get_sender_service()

    if req.method == "GET":
        return svc.list_fields() or {}, 200

    if req.method == "POST":
        payload = get_payload(req)
        title = pick(payload, "title")
        field_type = pick(payload, "type", "field_type") or "string"
        if not title:
            return {"error": "Missing required field: title"}, 400
        return svc.create_field(title, field_type) or {}, 200

    if req.method == "DELETE":
        payload = get_payload(req)
        field_id = pick(payload, "id", "field_id") or req.args.get("id")
        if not field_id:
            return {"error": "Missing field_id"}, 400
        svc.delete_field(field_id)
        return {"deleted": True}, 200

    return {"error": "Invalid request method"}, 405
