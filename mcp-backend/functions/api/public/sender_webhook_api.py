import hmac
import logging

from firebase_functions import https_fn

from config.firebase_config import cors, region
from config.external_services import SENDER_WEBHOOK_SECRET
from repositories.newsletter_repository import NewsletterRepository

logger = logging.getLogger("SenderWebhook")

# Event types that mean the subscriber no longer wants emails
_UNSUBSCRIBE_EVENTS = {
    "subscriber.unsubscribed",
    "subscriber.bounced",
    "subscriber.spam_reported",
}


@https_fn.on_request(cors=cors, region=region)
def sender_webhook(req):
    """
    Receives webhook events from Sender (sender.net).
    Handles unsubscribe / bounce / spam events by marking the subscriber
    as inactive in Firestore (newsletter_signups + newsletter_consents).

    Always returns 200 so Sender does not retry indefinitely.
    """
    if req.method != "POST":
        return {"error": "Method not allowed"}, 405

    # Verify webhook secret if configured
    if SENDER_WEBHOOK_SECRET:
        token = req.headers.get("X-Sender-Token") or req.headers.get("X-Webhook-Token", "")
        if not hmac.compare_digest(token, SENDER_WEBHOOK_SECRET):
            logger.warning("[SenderWebhook] Invalid or missing webhook secret")
            return {"error": "Unauthorized"}, 403

    try:
        payload = req.get_json(silent=True) or {}
    except Exception:
        payload = {}

    event = payload.get("event", "")
    data = payload.get("data") or {}
    email = (data.get("email") or "").strip().lower()

    logger.info("[SenderWebhook] event=%s email=%s", event, email)

    if event in _UNSUBSCRIBE_EVENTS and email:
        try:
            NewsletterRepository().unsubscribe_by_email(email)
            logger.info("[SenderWebhook] unsubscribed %s from Firestore (event=%s)", email, event)
        except Exception as exc:
            logger.error("[SenderWebhook] unsubscribe_by_email failed for %s: %s", email, exc)

    return {"received": True}, 200
