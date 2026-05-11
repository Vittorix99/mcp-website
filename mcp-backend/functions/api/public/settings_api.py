import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import public_endpoint
from dto.setting_api import GetSettingQueryDTO
from errors.service_errors import NotFoundError
from services.core.settings_service import SettingsService
from services.memberships.memberships_service import MembershipsService
from utils.http_responses import handle_pydantic_error, handle_service_error

logger = logging.getLogger("PublicSettingAPI")
settings_service = SettingsService()
memberships_service = MembershipsService()


@public_endpoint(methods=("GET",))
def get_setting(req):
    try:
        dto = GetSettingQueryDTO.model_validate(dict(req.args or {}))
        if not dto.key:
            return jsonify({"error": "Missing key"}), 400
        try:
            setting = settings_service.get_setting(dto.key)
            return jsonify(setting.to_payload()), 200
        except NotFoundError:
            return jsonify({"key": dto.key, "value": None}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        logger.error("[get_setting] %s", str(err))
        return handle_service_error(err)


@public_endpoint(methods=("GET",))
def get_membership_price_public(req):
    try:
        year = (dict(req.args or {})).get("year") or None
        try:
            result = memberships_service.get_membership_price(year=year)
            return jsonify(result.to_payload()), 200
        except NotFoundError:
            return jsonify({"year": str(year or ""), "price": None}), 200
    except Exception as err:
        logger.error("[get_membership_price_public] %s", str(err))
        return handle_service_error(err)
