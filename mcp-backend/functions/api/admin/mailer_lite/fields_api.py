from firebase_functions import https_fn

from config.firebase_config import cors, region
from services.auth_service import require_admin
from services.mailer_lite import FieldsClient, MailerLiteError

from .helpers import get_payload, get_query_params, pick, handle_mailerlite_error


fields_client = FieldsClient()


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_mailerlite_fields(req):
    if req.method == "GET":
        params = get_query_params(req)
        try:
            return fields_client.list(params=params), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "POST":
        payload = get_payload(req)
        name = pick(payload, "name")
        field_type = pick(payload, "type", "field_type", "fieldType")
        if not name or not field_type:
            return {"error": "Missing field name or type"}, 400
        try:
            return fields_client.create(name, field_type), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "PUT":
        payload = get_payload(req)
        field_id = pick(payload, "id", "field_id", "fieldId")
        name = pick(payload, "name")
        if not field_id:
            return {"error": "Missing field id"}, 400
        if not name:
            return {"error": "Missing field name"}, 400
        try:
            return fields_client.update(field_id, name), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    if req.method == "DELETE":
        payload = get_payload(req)
        field_id = pick(payload, "id", "field_id", "fieldId") or req.args.get("id")
        if not field_id:
            return {"error": "Missing field id"}, 400
        try:
            return fields_client.delete(field_id), 200
        except MailerLiteError as e:
            return handle_mailerlite_error(e)

    return {"error": "Invalid request method"}, 405
