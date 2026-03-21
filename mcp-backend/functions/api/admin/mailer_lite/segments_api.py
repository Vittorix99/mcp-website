from firebase_functions import https_fn

from config.firebase_config import cors, region
from services.core.auth_service import require_admin
from services.mailer_lite import SegmentsClient, MailerLiteError

from .helpers import get_payload, get_query_params, pick, handle_mailerlite_error


segments_client = None


def _get_segments_client():
    global segments_client
    if segments_client is None:
        segments_client = SegmentsClient()
    return segments_client


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_segments(req):
    if req.method == "GET":
        params = get_query_params(req)
        segment_id = pick(params, "id", "segment_id", "segmentId")
        if segment_id:
            params.pop("id", None)
            params.pop("segment_id", None)
            params.pop("segmentId", None)
            client = segments_client or _get_segments_client()
            try:
                return client.get(segment_id, params=params), 200
            except MailerLiteError as e:
                return handle_mailerlite_error(e)
        client = segments_client or _get_segments_client()
        try:
            return client.list(params=params), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "PUT":
        payload = get_payload(req)
        segment_id = pick(payload, "id", "segment_id", "segmentId")
        name = pick(payload, "name")
        if not segment_id:
            return {"error": "Missing segment id"}, 400
        if not name:
            return {"error": "Missing segment name"}, 400
        client = segments_client or _get_segments_client()
        try:
            return client.update(segment_id, name), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "DELETE":
        payload = get_payload(req)
        segment_id = pick(payload, "id", "segment_id", "segmentId") or req.args.get("id")
        if not segment_id:
            return {"error": "Missing segment id"}, 400
        client = segments_client or _get_segments_client()
        try:
            return client.delete(segment_id), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    return {"error": "Invalid request method"}, 405


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_segment_subscribers(req):
    if req.method != "GET":
        return {"error": "Invalid request method"}, 405

    segment_id = req.args.get("segment_id") or req.args.get("segmentId") or req.args.get("id")
    if not segment_id:
        return {"error": "Missing segment_id"}, 400

    params = get_query_params(req)
    params.pop("segment_id", None)
    params.pop("segmentId", None)
    params.pop("id", None)
    client = segments_client or _get_segments_client()
    try:
        return client.subscribers(segment_id, params=params), 200
    except MailerLiteError as e:
        return handle_mailerlite_error(e)
