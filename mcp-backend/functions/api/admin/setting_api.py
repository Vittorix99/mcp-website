from firebase_functions import https_fn
from config.firebase_config import cors
from services.admin.auth_services import require_admin
from services.admin.participants_service import ParticipantsService
from services.admin.location_service import LocationService
from config.firebase_config import region
from services.admin.settings_service import SettingsService
from flask import jsonify


settings_service = SettingsService()




@https_fn.on_request(cors=cors, region=region)
def get_settings(req):
    try:
        key = req.args.get("key")

        if key:
            # 🔍 Ritorna una singola setting
            value = settings_service.get_setting(key)
            return jsonify({"key": key, "value": value}), 200
        else:
            # 📋 Ritorna tutte le settings
            all_settings = settings_service.get_all_settings()
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

        settings_service.set_setting(key, value)
        return jsonify({"message": f"Setting '{key}' updated", "value": value}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

