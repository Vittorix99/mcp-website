import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.sender_api import (
    CreateGroupRequestDTO,
    GroupDeleteRequestDTO,
    GroupSubscribersQueryDTO,
    UpdateGroupRequestDTO,
)
from utils.http_responses import handle_pydantic_error, handle_service_error
from .helpers import get_sender_service

logger = logging.getLogger("AdminSenderGroupsAPI")


@admin_endpoint(methods=("GET", "POST", "PUT", "DELETE"))
def admin_sender_groups(req):
    sender_service = get_sender_service()

    if req.method == "GET":
        try:
            return jsonify(sender_service.list_groups() or {}), 200
        except Exception as err:
            return handle_service_error(err)

    if req.method == "POST":
        try:
            dto = CreateGroupRequestDTO.model_validate(req.get_json(silent=True) or {})
            return jsonify(sender_service.create_group(dto.title) or {}), 200
        except PydanticValidationError as err:
            return handle_pydantic_error(err)
        except Exception as err:
            return handle_service_error(err)

    if req.method == "PUT":
        try:
            dto = UpdateGroupRequestDTO.model_validate(req.get_json(silent=True) or {})
            return jsonify(sender_service.rename_group(dto.id, dto.title) or {}), 200
        except PydanticValidationError as err:
            return handle_pydantic_error(err)
        except Exception as err:
            return handle_service_error(err)

    try:
        data = {**(req.get_json(silent=True) or {}), **dict(req.args or {})}
        dto = GroupDeleteRequestDTO.model_validate(data)
        sender_service.delete_group(dto.id)
        return jsonify({"deleted": True}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_sender_group_subscribers(req):
    sender_service = get_sender_service()
    try:
        dto = GroupSubscribersQueryDTO.model_validate(dict(req.args or {}))
        params = {k: v for k, v in req.args.items() if k not in ("id", "group_id", "groupId")}
        return jsonify(sender_service.list_group_subscribers(dto.id, params=params) or {}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
