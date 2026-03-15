from firebase_functions import https_fn
from config.firebase_config import cors, region
from services.core.auth_service import require_admin
from .helpers import get_payload, get_query_params, pick, get_sender_service


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_groups(req):
    svc = get_sender_service()

    if req.method == "GET":
        return svc.list_groups() or {}, 200

    if req.method == "POST":
        payload = get_payload(req)
        title = pick(payload, "title", "name")
        if not title:
            return {"error": "Missing title"}, 400
        return svc.create_group(title) or {}, 200

    if req.method == "PUT":
        payload = get_payload(req)
        group_id = pick(payload, "id", "group_id", "groupId")
        title = pick(payload, "title", "name")
        if not group_id:
            return {"error": "Missing group_id"}, 400
        if not title:
            return {"error": "Missing title"}, 400
        return svc.rename_group(group_id, title) or {}, 200

    if req.method == "DELETE":
        payload = get_payload(req)
        group_id = pick(payload, "id", "group_id", "groupId") or req.args.get("id")
        if not group_id:
            return {"error": "Missing group_id"}, 400
        svc.delete_group(group_id)
        return {"deleted": True}, 200

    return {"error": "Invalid request method"}, 405


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_group_subscribers(req):
    if req.method != "GET":
        return {"error": "Invalid request method"}, 405
    group_id = req.args.get("group_id") or req.args.get("groupId") or req.args.get("id")
    if not group_id:
        return {"error": "Missing group_id"}, 400
    params = get_query_params(req)
    for k in ("group_id", "groupId", "id"):
        params.pop(k, None)
    svc = get_sender_service()
    return svc.list_group_subscribers(group_id, params=params) or {}, 200
