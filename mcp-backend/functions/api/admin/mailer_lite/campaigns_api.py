from firebase_functions import https_fn

from config.firebase_config import cors, region
from services.auth_service import require_admin
from services.mailer_lite import CampaignsClient, MailerLiteError

from .helpers import get_payload, get_query_params, pick, handle_mailerlite_error


campaigns_client = None


def _get_campaigns_client():
    global campaigns_client
    if campaigns_client is None:
        campaigns_client = CampaignsClient()
    return campaigns_client


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_campaigns(req):
    if req.method == "GET":
        params = get_query_params(req)
        campaign_id = pick(params, "id", "campaign_id", "campaignId")
        client = campaigns_client or _get_campaigns_client()
        if campaign_id:
            try:
                return client.get(campaign_id), 200
            except MailerLiteError as e:
                return handle_mailerlite_error(e)
        try:
            return client.list(params=params), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "POST":
        payload = get_payload(req)
        if not payload:
            return {"error": "Missing payload"}, 400
        client = campaigns_client or _get_campaigns_client()
        try:
            return client.create(payload), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "PUT":
        payload = get_payload(req)
        campaign_id = pick(payload, "id", "campaign_id", "campaignId")
        if not campaign_id:
            return {"error": "Missing campaign id"}, 400
        payload.pop("id", None)
        payload.pop("campaign_id", None)
        payload.pop("campaignId", None)
        client = campaigns_client or _get_campaigns_client()
        try:
            return client.update(campaign_id, payload), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "DELETE":
        payload = get_payload(req)
        campaign_id = pick(payload, "id", "campaign_id", "campaignId") or req.args.get("id")
        if not campaign_id:
            return {"error": "Missing campaign id"}, 400
        client = campaigns_client or _get_campaigns_client()
        try:
            return client.delete(campaign_id), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    return {"error": "Invalid request method"}, 405


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_campaign_schedule(req):
    if req.method != "POST":
        return {"error": "Invalid request method"}, 405

    payload = get_payload(req)
    campaign_id = pick(payload, "id", "campaign_id", "campaignId")
    if not campaign_id:
        return {"error": "Missing campaign id"}, 400

    payload.pop("id", None)
    payload.pop("campaign_id", None)
    payload.pop("campaignId", None)

    client = campaigns_client or _get_campaigns_client()
    try:
        return client.schedule(campaign_id, payload), 200
    except MailerLiteError as e:
        return handle_mailerlite_error(e)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_campaign_cancel_ready(req):
    if req.method != "POST":
        return {"error": "Invalid request method"}, 405

    payload = get_payload(req)
    campaign_id = pick(payload, "id", "campaign_id", "campaignId")
    if not campaign_id:
        return {"error": "Missing campaign id"}, 400

    client = campaigns_client or _get_campaigns_client()
    try:
        return client.cancel_ready(campaign_id), 200
    except MailerLiteError as e:
        return handle_mailerlite_error(e)
