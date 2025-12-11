from functools import wraps

from flask import jsonify

from config.firebase_config import db
from utils.events_utils import ensure_event_is_active


def require_active_event(handler):
    """
    Validates that the incoming request is targeting an active/future event.
    Expects the request payload to contain a cart with a single item that
    includes the `eventId`. Injects the payload and event data onto the
    request object so downstream handlers can reuse them without refetching.
    """

    @wraps(handler)
    def wrapper(req, *args, **kwargs):
        if req.method != "POST":
            return handler(req, *args, **kwargs)

        payload = getattr(req, "json_data", None) or req.get_json(silent=True)
        if not payload:
            return jsonify({"error": "Missing request body"}), 400

        cart = payload.get("cart", [])
        if not isinstance(cart, list) or len(cart) != 1:
            return jsonify({"error": "Only one cart item is allowed"}), 400

        cart_item = cart[0] or {}
        event_id = cart_item.get("eventId")
        if not event_id:
            return jsonify({"error": "Missing eventId"}), 400

        event_snapshot = db.collection("events").document(event_id).get()
        if not event_snapshot.exists:
            return jsonify({"error": "Evento non trovato"}), 404

        event_data = event_snapshot.to_dict() or {}
        try:
            ensure_event_is_active(event_data)
        except ValueError as exc:
            return jsonify({"error": "validation_error", "message": str(exc)}), 400

        setattr(req, "event_payload", payload)
        setattr(req, "event_data", event_data)
        setattr(req, "event_id", event_id)
        setattr(req, "json_data", payload)

        return handler(req, *args, **kwargs)

    return wrapper
