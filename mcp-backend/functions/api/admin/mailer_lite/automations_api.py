from firebase_functions import https_fn

from config.firebase_config import cors, region
from services.core.auth_service import require_admin
from services.mailer_lite import AutomationsClient, MailerLiteError

from .helpers import get_query_params, pick, handle_mailerlite_error


automations_client = None


def _get_automations_client():
    global automations_client
    if automations_client is None:
        automations_client = AutomationsClient()
    return automations_client


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_automations(req):
    if req.method == "GET":
        params = get_query_params(req)
        automation_id = pick(params, "id", "automation_id", "automationId")
        client = automations_client or _get_automations_client()
        if automation_id:
            try:
                return client.get(automation_id), 200
            except MailerLiteError as e:
                return handle_mailerlite_error(e)
        try:
            return client.list(params=params), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    return {"error": "Invalid request method"}, 405


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_automation_activity(req):
    if req.method != "GET":
        return {"error": "Invalid request method"}, 405

    automation_id = req.args.get("automation_id") or req.args.get("automationId") or req.args.get("id")
    if not automation_id:
        return {"error": "Missing automation_id"}, 400

    params = get_query_params(req)
    params.pop("automation_id", None)
    params.pop("automationId", None)
    params.pop("id", None)
    client = automations_client or _get_automations_client()
    try:
        return client.activity(automation_id, params=params), 200
    except MailerLiteError as e:
        return handle_mailerlite_error(e)
