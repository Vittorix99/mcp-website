from firebase_functions import https_fn
from config.firebase_config import cors
from services.auth_service import require_admin
from config.firebase_config import region
from services.settings_service import SettingsService
from flask import jsonify
from services.service_errors import ExternalServiceError, NotFoundError, ServiceError, ValidationError


settings_service = SettingsService()




@https_fn.on_request(cors=cors, region=region)
def get_settings(req):
    try:
        key = req.args.get("key")
        if key:
            setting = settings_service.get_setting(key)
            return jsonify(setting.to_payload()), 200

        all_settings = [entry.to_payload() for entry in settings_service.get_all_settings()]
        return jsonify({"settings": all_settings}), 200
    except Exception as err:
        return _handle_service_error(err)


@https_fn.on_request(cors=cors, region=region)
@require_admin
def set_settings(req):
    try:
        data = req.get_json()
        key = data.get("key") if data else None
        value = data.get("value") if data else None

        setting = settings_service.set_setting(key, value)
        return jsonify({"message": f"Setting '{key}' updated", "setting": setting.to_payload()}), 200
    except Exception as err:
        return _handle_service_error(err)


def _handle_service_error(err: Exception):
    if isinstance(err, ValidationError):
        return jsonify({"error": str(err)}), 400
    if isinstance(err, NotFoundError):
        return jsonify({"error": str(err)}), 404
    if isinstance(err, ExternalServiceError):
        return jsonify({"error": str(err)}), 502
    if isinstance(err, ServiceError):
        return jsonify({"error": str(err)}), 500
    return jsonify({"error": "Internal server error"}), 500
