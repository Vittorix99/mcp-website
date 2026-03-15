from firebase_functions import https_fn
from config.firebase_config import cors, region
from services.core.auth_service import require_admin
from .helpers import get_payload, get_query_params, pick, get_sender_service


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_segments(req):
    svc = get_sender_service()

    if req.method == "GET":
        params = get_query_params(req)
        segment_id = pick(params, "id", "segment_id")
        if segment_id:
            return svc.get_segment(segment_id) or {}, 200
        return svc.list_segments() or {}, 200

    if req.method == "DELETE":
        segment_id = req.args.get("id") or req.args.get("segment_id")
        if not segment_id:
            payload = get_payload(req)
            segment_id = pick(payload, "id", "segment_id")
        if not segment_id:
            return {"error": "Missing segment_id"}, 400
        ok = svc.delete_segment(segment_id)
        if not ok:
            return {"error": "Impossibile eliminare il segmento."}, 500
        return {"deleted": True}, 200

    return {"error": "Invalid request method"}, 405


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_segment_subscribers(req):
    if req.method != "GET":
        return {"error": "Invalid request method"}, 405
    segment_id = req.args.get("segment_id") or req.args.get("id")
    if not segment_id:
        return {"error": "Missing segment_id"}, 400
    svc = get_sender_service()
    return svc.list_segment_subscribers(segment_id) or {}, 200
