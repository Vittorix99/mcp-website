import hmac
import logging

from flask import jsonify

from api.decorators import public_endpoint
from config.external_services import SENDER_WEBHOOK_SECRET
from repositories.newsletter_repository import NewsletterRepository
from utils.safe_logging import mask_email, redact_sensitive

logger = logging.getLogger("SenderWebhook")

_UNSUBSCRIBE_EVENTS = {
    "subscriber.unsubscribed",
    "subscriber.bounced",
    "subscriber.spam_reported",
}


@public_endpoint(methods=("POST",))
def sender_webhook(req):
    """
    Receives webhook events from Sender (sender.net).
    Always returns 200 so Sender does not retry indefinitely.
    """
    if SENDER_WEBHOOK_SECRET:
        token = req.headers.get("X-Sender-Token") or req.headers.get("X-Webhook-Token", "")
        if not hmac.compare_digest(token, SENDER_WEBHOOK_SECRET):
            logger.warning("[SenderWebhook] Invalid or missing webhook secret")
            return jsonify({"error": "Unauthorized"}), 403

    payload = req.get_json(silent=True) or {}
    event = payload.get("event", "")
    data = payload.get("data") or {}
    email = (data.get("email") or "").strip().lower()

    logger.info("[SenderWebhook] event=%s email=%s", event, mask_email(email))

    if event in _UNSUBSCRIBE_EVENTS and email:
        try:
            NewsletterRepository().unsubscribe_by_email(email)
            logger.info("[SenderWebhook] unsubscribed %s (event=%s)", mask_email(email), event)
        except Exception as exc:
            logger.error("[SenderWebhook] unsubscribe_by_email failed for %s: %s", mask_email(email), redact_sensitive(str(exc)))

    return jsonify({"received": True}), 200
