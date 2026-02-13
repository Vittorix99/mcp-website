from firebase_functions import https_fn
from flask import request, jsonify
from config.firebase_config import cors, region
from services.auth_service import require_admin
from services.messages_service import MessagesService
from services.service_errors import ExternalServiceError, NotFoundError, ServiceError, ValidationError

messages_service = MessagesService()

@https_fn.on_request(cors=cors, region=region)
@require_admin
def get_messages(req):
    if req.method != "GET":
        return "Invalid method", 405
    try:
        payload = messages_service.get_all()
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def delete_message(req):
    if req.method != "DELETE":
        return "Invalid method", 405

    data = request.get_json()
    message_id = data.get("message_id")
    if not message_id:
        return {"error": "Missing message_id"}, 400

    try:
        payload = messages_service.delete_by_id(message_id)
        return jsonify(payload), 200
    except Exception as err:
        return _handle_service_error(err)

@https_fn.on_request(cors=cors, region=region)
@require_admin
def reply_to_message(req):
    if req.method != "POST":
        return "Invalid method", 405

    try:
        data = request.get_json()
        to = data.get("email")
        subject = data.get("subject", "Risposta al tuo messaggio")
        body = data.get("body")
        message_id = data.get("message_id")

        if not to or not body or not message_id:
            return {"error": "Missing email, message body or message ID"}, 400

        payload = messages_service.reply(to, subject, body, message_id)
        return jsonify(payload), 200

    except Exception as e:
        return _handle_service_error(e)


def _handle_service_error(err: Exception):
    if isinstance(err, ValidationError):
        return {"error": str(err)}, 400
    if isinstance(err, NotFoundError):
        return {"error": str(err)}, 404
    if isinstance(err, ExternalServiceError):
        return {"error": str(err)}, 502
    if isinstance(err, ServiceError):
        return {"error": str(err)}, 500
    return {"error": "Internal server error"}, 500
