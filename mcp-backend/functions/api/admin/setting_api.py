from firebase_functions import https_fn
from config.firebase_config import cors
from services.auth_service import require_admin
from config.firebase_config import region
from services.settings_service import SettingsService
from flask import jsonify


settings_service = SettingsService()




@https_fn.on_request(cors=cors, region=region)
def get_settings(req):
    try:
        key = req.args.get("key")

        if key:
            setting = settings_service.get_setting(key)
            if not setting:
                return jsonify({"error": "Setting not found"}), 404
            return jsonify(setting.to_kv()), 200

        all_settings = [entry.to_kv() for entry in settings_service.get_all_settings()]
        return jsonify({"settings": all_settings}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@https_fn.on_request(cors=cors, region=region)
@require_admin
def set_settings(req):
    try:
        data = req.get_json()
        key = data.get("key")
        value = data.get("value")

        if not key or value is None:
            return jsonify({"error": "Missing 'key' or 'value' in body"}), 400

        setting = settings_service.set_setting(key, value)
        return jsonify({"message": f"Setting '{key}' updated", "setting": setting.to_kv()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
