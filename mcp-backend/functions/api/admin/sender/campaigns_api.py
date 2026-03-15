from firebase_functions import https_fn
from config.firebase_config import cors, region
from services.core.auth_service import require_admin
from .helpers import get_payload, get_query_params, pick, get_sender_service


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_campaigns(req):
    svc = get_sender_service()

    if req.method == "GET":
        params = get_query_params(req)
        campaign_id = pick(params, "id", "campaign_id", "campaignId")
        if campaign_id:
            return svc.get_campaign(campaign_id) or {}, 200
        return svc.list_campaigns(params=params) or {}, 200

    if req.method == "POST":
        payload = get_payload(req)
        title = pick(payload, "title")
        subject = pick(payload, "subject")
        from_name = pick(payload, "from_name", "fromName")
        from_email = pick(payload, "from_email", "fromEmail")
        reply_to = pick(payload, "reply_to", "replyTo") or from_email
        content_html = pick(payload, "content_html", "html")
        if not all([title, subject, from_name, from_email, content_html]):
            return {"error": "Missing required fields: title, subject, from_name, from_email, content_html"}, 400
        return svc.create_campaign(
            title=title,
            subject=subject,
            from_name=from_name,
            from_email=from_email,
            content_html=content_html,
            reply_to=reply_to,
            groups=payload.get("groups"),
        ) or {}, 200

    if req.method == "PUT":
        payload = get_payload(req)
        campaign_id = pick(payload, "id", "campaign_id", "campaignId")
        if not campaign_id:
            return {"error": "Missing campaign_id"}, 400
        groups = payload.get("groups")  # list of group IDs or None (None = don't change)
        return svc.update_campaign(
            campaign_id=campaign_id,
            title=pick(payload, "title"),
            subject=pick(payload, "subject"),
            from_name=pick(payload, "from_name", "fromName"),
            from_email=pick(payload, "from_email", "fromEmail"),
            content_html=pick(payload, "content_html", "html"),
            groups=groups,
        ) or {}, 200

    if req.method == "DELETE":
        payload = get_payload(req)
        campaign_id = pick(payload, "id", "campaign_id", "campaignId") or req.args.get("id")
        if not campaign_id:
            return {"error": "Missing campaign_id"}, 400
        ok = svc.delete_campaign(campaign_id)
        if not ok:
            return {"error": "Sender API non supporta l'eliminazione delle campagne via API. Eliminala dalla dashboard Sender."}, 501
        return {"deleted": True}, 200

    return {"error": "Invalid request method"}, 405


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_campaign_send(req):
    if req.method != "POST":
        return {"error": "Invalid request method"}, 405
    payload = get_payload(req)
    campaign_id = pick(payload, "id", "campaign_id", "campaignId")
    if not campaign_id:
        return {"error": "Missing campaign_id"}, 400
    svc = get_sender_service()
    ok, error = svc.send_campaign(campaign_id)
    if not ok:
        return {"sent": False, "error": error or "Sender ha rifiutato l'invio."}, 422
    return {"sent": True}, 200


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_campaign_schedule(req):
    if req.method == "POST":
        payload = get_payload(req)
        campaign_id = pick(payload, "id", "campaign_id", "campaignId")
        scheduled_at = pick(payload, "scheduled_at", "scheduledAt")
        if not campaign_id or not scheduled_at:
            return {"error": "Missing campaign_id or scheduled_at"}, 400
        svc = get_sender_service()
        ok, error = svc.schedule_campaign(campaign_id, scheduled_at)
        if not ok:
            return {"scheduled": False, "error": error or "Sender ha rifiutato la schedulazione."}, 422
        return {"scheduled": True}, 200

    if req.method == "DELETE":
        payload = get_payload(req)
        campaign_id = pick(payload, "id", "campaign_id", "campaignId") or req.args.get("id")
        if not campaign_id:
            return {"error": "Missing campaign_id"}, 400
        svc = get_sender_service()
        svc.cancel_scheduled_campaign(campaign_id)
        return {"cancelled": True}, 200

    return {"error": "Invalid request method"}, 405


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_campaign_copy(req):
    if req.method != "POST":
        return {"error": "Invalid request method"}, 405
    payload = get_payload(req)
    campaign_id = pick(payload, "id", "campaign_id", "campaignId")
    if not campaign_id:
        return {"error": "Missing campaign_id"}, 400
    svc = get_sender_service()
    return svc.copy_campaign(campaign_id) or {}, 200


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_sender_campaign_stats(req):
    if req.method != "GET":
        return {"error": "Invalid request method"}, 405
    campaign_id = req.args.get("id") or req.args.get("campaign_id")
    stat_type = req.args.get("type", "opens")
    if not campaign_id:
        return {"error": "Missing campaign_id"}, 400
    svc = get_sender_service()
    handlers = {
        "opens": svc.get_campaign_opens,
        "clicks": svc.get_campaign_clicks,
        "unsubscribes": svc.get_campaign_unsubscribes,
        "bounces_hard": svc.get_campaign_bounces_hard,
        "bounces_soft": svc.get_campaign_bounces_soft,
    }
    handler = handlers.get(stat_type)
    if not handler:
        return {"error": f"Unknown stat type: {stat_type}"}, 400
    return handler(campaign_id) or {}, 200
