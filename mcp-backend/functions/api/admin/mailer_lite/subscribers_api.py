from firebase_functions import https_fn

from config.firebase_config import cors, region
from services.auth_service import require_admin
import logging

from services.mailer_lite import (
    MailerLiteSubscribersRegistry,
    SubscribersClient,
    MailerLiteError,
)

from .helpers import get_payload, get_query_params, pick, handle_mailerlite_error


logger = logging.getLogger("MailerLiteSubscribersAPI")
subscribers_client = SubscribersClient()
subscribers_registry = MailerLiteSubscribersRegistry()


def _extract_subscriber_id(response):
    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, dict):
            for key in ("id", "subscriber_id", "subscriberId"):
                if key in data:
                    return str(data[key])
        for key in ("id", "subscriber_id", "subscriberId"):
            if key in response:
                return str(response[key])
    return None


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_subscribers(req):
    if req.method == "GET":
        params = get_query_params(req)
        email = pick(params, "email")
        if email:
            try:
                return subscribers_client.get(email), 200
            except MailerLiteError as e:
                return handle_mailerlite_error(e)
        try:
            return subscribers_client.list(params=params), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "POST":
        payload = get_payload(req)
        email = pick(payload, "email")
        if not email:
            return {"error": "Missing email"}, 400
        try:
            payload.pop("email", None)
            response = subscribers_client.create(email, payload)
            try:
                subscriber_id = _extract_subscriber_id(response)
                subscribers_registry.upsert(email, subscriber_id)
            except Exception as e:
                logger.warning("Unable to store MailerLite subscriber: %s", e)
            return response, 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "PUT":
        payload = get_payload(req)
        email = pick(payload, "email")
        if not email:
            return {"error": "Missing email"}, 400
        payload.pop("email", None)
        try:
            return subscribers_client.update(email, payload), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "DELETE":
        payload = get_payload(req)
        subscriber_id = pick(payload, "id", "subscriber_id", "subscriberId") or req.args.get("id")
        if not subscriber_id:
            return {"error": "Missing subscriber id"}, 400
        try:
            return subscribers_client.delete_subscriber(subscriber_id), 200
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

    try:
        return subscribers_client.forget_subscriber(subscriber_id), 200
    except MailerLiteError as e:
        return handle_mailerlite_error(e)
