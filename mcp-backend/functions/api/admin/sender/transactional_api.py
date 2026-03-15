from firebase_functions import https_fn
from config.firebase_config import cors, region
from services.core.auth_service import require_admin
from .helpers import get_payload, pick, get_sender_service


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_transactional(req):
    svc = get_sender_service()

    if req.method == "GET":
        return svc.list_transactional_campaigns() or {}, 200

    if req.method == "POST":
        payload = get_payload(req)
        title = pick(payload, "title")
        subject = pick(payload, "subject")
        from_name = pick(payload, "from_name", "fromName")
        from_email = pick(payload, "from_email", "fromEmail")
        content_html = pick(payload, "content_html", "html")
        if not all([title, subject, from_name, from_email, content_html]):
            return {"error": "Missing required fields: title, subject, from_name, from_email, content_html"}, 400
        return svc.create_transactional_campaign(
            title=title,
            subject=subject,
            from_name=from_name,
            from_email=from_email,
            content_html=content_html,
        ) or {}, 200

    if req.method == "DELETE":
        payload = get_payload(req)
        campaign_id = pick(payload, "id", "campaign_id") or req.args.get("id")
        if not campaign_id:
            return {"error": "Missing campaign_id"}, 400
        # Sender API does not expose a DELETE for transactional campaigns;
        # return a not-implemented response so the frontend knows.
        return {"error": "Delete not supported by Sender transactional API"}, 501

    return {"error": "Invalid request method"}, 405


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_transactional_send(req):
    if req.method != "POST":
        return {"error": "Invalid request method"}, 405
    payload = get_payload(req)
    campaign_id = pick(payload, "id", "campaign_id", "campaignId")
    to_email = pick(payload, "to_email", "toEmail")
    to_name = pick(payload, "to_name", "toName") or ""
    variables = payload.get("variables")
    if not campaign_id or not to_email:
        return {"error": "Missing campaign_id or to_email"}, 400
    svc = get_sender_service()
    result = svc.send_transactional_campaign(
        campaign_id=campaign_id,
        to_email=to_email,
        to_name=to_name,
        variables=variables,
    )
    return result or {"sent": True}, 200
