from firebase_functions import https_fn
from config.firebase_config import cors, region
from services.core.auth_service import require_admin
from services.core.error_logs_service import ErrorLogsService

error_logs_service = ErrorLogsService()


def _parse_bool(value):
    if value is None:
        return None
    value_str = str(value).strip().lower()
    if value_str in {"true", "1", "yes"}:
        return True
    if value_str in {"false", "0", "no"}:
        return False
    return None


@https_fn.on_request(cors=cors, region=region)
@require_admin
def admin_error_logs(req):
    if req.method == "GET":
        error_log_id = req.args.get("id")
        if error_log_id:
            entry = error_logs_service.get_log(error_log_id)
            if not entry:
                return {"error": "Error log not found"}, 404
            return entry, 200

        limit = req.args.get("limit", "100")
        try:
            limit_value = int(limit)
        except Exception:
            return {"error": "Invalid limit"}, 400

        service = req.args.get("service")
        resolved = _parse_bool(req.args.get("resolved"))
        return {"error_logs": error_logs_service.list_logs(limit=limit_value, service=service, resolved=resolved)}, 200

    if req.method == "POST":
        try:
            payload = req.get_json() or {}
        except Exception:
            return {"error": "Invalid JSON"}, 400
        try:
            created = error_logs_service.create_log(payload)
        except ValueError as err:
            return {"error": str(err)}, 400
        return created, 201

    if req.method == "PUT":
        try:
            payload = req.get_json() or {}
        except Exception:
            return {"error": "Invalid JSON"}, 400
        error_log_id = payload.get("id")
        if not error_log_id:
            return {"error": "Missing id"}, 400
        updated = error_logs_service.update_log(error_log_id, payload)
        if not updated:
            return {"error": "Error log not found"}, 404
        return updated, 200

    if req.method == "DELETE":
        error_log_id = req.args.get("id")
        if not error_log_id:
            try:
                payload = req.get_json() or {}
            except Exception:
                payload = {}
            error_log_id = payload.get("id")
        if not error_log_id:
            return {"error": "Missing id"}, 400
        deleted = error_logs_service.delete_log(error_log_id)
        if not deleted:
            return {"error": "Error log not found"}, 404
        return {"deleted": True}, 200

    return {"error": "Invalid request method"}, 405
