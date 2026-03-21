from firebase_functions import https_fn

from config.firebase_config import cors, region
from services.core.auth_service import require_admin
import logging

from services.mailer_lite import (
    SubscribersClient,
    MailerLiteError,
)

from .helpers import get_payload, get_query_params, pick, handle_mailerlite_error


logger = logging.getLogger("MailerLiteSubscribersAPI")
subscribers_client = None


def _get_subscribers_client():
    global subscribers_client
    if subscribers_client is None:
        subscribers_client = SubscribersClient()
    return subscribers_client


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_subscribers(req):
    if req.method == "GET":
        params = get_query_params(req)
        email = pick(params, "email")
        client = subscribers_client or _get_subscribers_client()
        if email:
            try:
                return client.get(email), 200
            except MailerLiteError as e:
                return handle_mailerlite_error(e)
        try:
            return client.list(params=params), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "POST":
        payload = get_payload(req)
        email = pick(payload, "email")
        if not email:
            return {"error": "Missing email"}, 400
        client = subscribers_client or _get_subscribers_client()
        try:
            payload.pop("email", None)
            response = client.create(email, payload)
            return response, 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "PUT":
        payload = get_payload(req)
        email = pick(payload, "email")
        if not email:
            return {"error": "Missing email"}, 400
        payload.pop("email", None)
        client = subscribers_client or _get_subscribers_client()
        try:
            return client.update(email, payload), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "DELETE":
        payload = get_payload(req)
        subscriber_id = pick(payload, "id", "subscriber_id", "subscriberId") or req.args.get("id")
        if not subscriber_id:
            return {"error": "Missing subscriber id"}, 400
        client = subscribers_client or _get_subscribers_client()
        try:
            return client.delete_subscriber(subscriber_id), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    return {"error": "Invalid request method"}, 405


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_subscriber_forget(req):
    if req.method != "POST":
        return {"error": "Invalid request method"}, 405

    payload = get_payload(req)
    subscriber_id = pick(payload, "id", "subscriber_id", "subscriberId")
    if not subscriber_id:
        return {"error": "Missing subscriber id"}, 400

    client = subscribers_client or _get_subscribers_client()
    try:
        return client.forget_subscriber(subscriber_id), 200
    except MailerLiteError as e:
        return handle_mailerlite_error(e)
