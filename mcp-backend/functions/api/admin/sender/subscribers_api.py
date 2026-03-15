from firebase_functions import https_fn
from config.firebase_config import cors, region
from services.core.auth_service import require_admin
from .helpers import get_payload, get_query_params, pick, get_sender_service


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_subscribers(req):
    svc = get_sender_service()

    if req.method == "GET":
        params = get_query_params(req)
        email = pick(params, "email")
        if email:
            return svc.get_subscriber(email) or {}, 200
        return svc.list_subscribers(params=params) or {}, 200

    if req.method == "POST":
        payload = get_payload(req)
        email = pick(payload, "email")
        if not email:
            return {"error": "Missing email"}, 400
        result = svc.upsert_subscriber(
            email=email,
            firstname=payload.get("firstname"),
            lastname=payload.get("lastname"),
            phone=payload.get("phone"),
            groups=payload.get("groups"),
            fields=payload.get("fields"),
        )
        return result or {}, 200

    if req.method == "PUT":
        payload = get_payload(req)
        email = pick(payload, "email")
        if not email:
            return {"error": "Missing email"}, 400
        payload.pop("email", None)
        return svc.update_subscriber(email, payload) or {}, 200

    if req.method == "DELETE":
        payload = get_payload(req)
        email = pick(payload, "email") or req.args.get("email")
        if not email:
            return {"error": "Missing email"}, 400
        svc.delete_subscriber(email)
        return {"deleted": True}, 200

    return {"error": "Invalid request method"}, 405


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_subscriber_groups(req):
    """Add or remove a subscriber from a group."""
    svc = get_sender_service()
    payload = get_payload(req)
    params = get_query_params(req)
    email = pick(payload, "email") or pick(params, "email")
    group_id = pick(payload, "group_id", "groupId") or pick(params, "group_id", "groupId")

    if not email or not group_id:
        return {"error": "Missing email or group_id"}, 400

    if req.method == "POST":
        result = svc.add_to_group(email, group_id)
        return {"added": result}, 200

    if req.method == "DELETE":
        result = svc.remove_from_group(email, group_id)
        return {"removed": result}, 200

    return {"error": "Invalid request method"}, 405


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_subscriber_events(req):
    if req.method != "GET":
        return {"error": "Invalid request method"}, 405
    identifier = req.args.get("email") or req.args.get("id")
    if not identifier:
        return {"error": "Missing email or id"}, 400
    actions = req.args.get("actions")
    svc = get_sender_service()
    return svc.get_subscriber_events(identifier, actions=actions) or {}, 200
