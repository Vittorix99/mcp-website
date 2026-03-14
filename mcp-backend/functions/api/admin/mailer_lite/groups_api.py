from firebase_functions import https_fn

from config.firebase_config import cors, region
from services.core.auth_service import require_admin
from services.mailer_lite import GroupsClient, MailerLiteError

from .helpers import get_payload, get_query_params, pick, handle_mailerlite_error


groups_client = None


def _get_groups_client():
    global groups_client
    if groups_client is None:
        groups_client = GroupsClient()
    return groups_client


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_groups(req):
    if req.method == "GET":
        params = get_query_params(req)
        client = groups_client or _get_groups_client()
        try:
            return client.list(params=params), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "POST":
        payload = get_payload(req)
        name = pick(payload, "name", "group_name", "groupName")
        if not name:
            return {"error": "Missing group name"}, 400
        client = groups_client or _get_groups_client()
        try:
            return client.create(name), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "PUT":
        payload = get_payload(req)
        group_id = pick(payload, "id", "group_id", "groupId")
        name = pick(payload, "name", "group_name", "groupName")
        if not group_id:
            return {"error": "Missing group id"}, 400
        if not name:
            return {"error": "Missing group name"}, 400
        client = groups_client or _get_groups_client()
        try:
            return client.update(group_id, name), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "DELETE":
        data = get_payload(req)
        group_id = pick(data, "id", "group_id", "groupId") or req.args.get("id")
        if not group_id:
            return {"error": "Missing group id"}, 400
        client = groups_client or _get_groups_client()
        try:
            return client.delete(group_id), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    return {"error": "Invalid request method"}, 405


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_group_subscribers(req):
    if req.method != "GET":
        return {"error": "Invalid request method"}, 405

    group_id = req.args.get("group_id") or req.args.get("groupId") or req.args.get("id")
    if not group_id:
        return {"error": "Missing group_id"}, 400

    params = get_query_params(req)
    params.pop("group_id", None)
    params.pop("groupId", None)
    params.pop("id", None)
    client = groups_client or _get_groups_client()
    try:
        return client.subscribers(group_id, params=params), 200
    except MailerLiteError as e:
        return handle_mailerlite_error(e)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_group_assign_subscriber(req):
    if req.method != "POST":
        return {"error": "Invalid request method"}, 405

    payload = get_payload(req)
    group_id = pick(payload, "group_id", "groupId", "id")
    subscriber_id = pick(payload, "subscriber_id", "subscriberId")
    if not group_id or not subscriber_id:
        return {"error": "Missing group_id or subscriber_id"}, 400

    client = groups_client or _get_groups_client()
    try:
        return client.assign_subscriber(subscriber_id, group_id), 200
    except MailerLiteError as e:
        return handle_mailerlite_error(e)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_group_unassign_subscriber(req):
    if req.method != "DELETE":
        return {"error": "Invalid request method"}, 405

    payload = get_payload(req)
    group_id = pick(payload, "group_id", "groupId", "id")
    subscriber_id = pick(payload, "subscriber_id", "subscriberId")
    if not group_id or not subscriber_id:
        return {"error": "Missing group_id or subscriber_id"}, 400

    client = groups_client or _get_groups_client()
    try:
        return client.unassign_subscriber(subscriber_id, group_id), 200
    except MailerLiteError as e:
        return handle_mailerlite_error(e)
