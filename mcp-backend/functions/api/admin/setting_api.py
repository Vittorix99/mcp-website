import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint, public_endpoint
from dto.setting_api import GetSettingQueryDTO, SetSettingRequestDTO
from services.core.settings_service import SettingsService
from utils.http_responses import handle_pydantic_error, handle_service_error

logger = logging.getLogger("SettingAPI")
settings_service = SettingsService()


@public_endpoint(methods=("GET",))
def get_settings(req):
    try:
        dto = GetSettingQueryDTO.model_validate(dict(req.args or {}))
        if dto.key:
            setting = settings_service.get_setting(dto.key)
            return jsonify(setting.to_payload()), 200
        result = settings_service.get_all_settings()
        return jsonify(result.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def set_settings(req):
    try:
        dto = SetSettingRequestDTO.model_validate(req.get_json(silent=True) or {})
        result = settings_service.set_setting(dto)
        return jsonify(result.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[set_settings] %s", str(err))
        return handle_service_error(err)
