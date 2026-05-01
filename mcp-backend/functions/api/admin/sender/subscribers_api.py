import logging

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.sender_api import (
    DeleteSubscriberRequestDTO,
    SubscriberEventQueryDTO,
    SubscriberGroupRequestDTO,
    SubscriberQueryDTO,
    UpdateSubscriberRequestDTO,
    UpsertSubscriberRequestDTO,
)
from utils.http_responses import handle_pydantic_error, handle_service_error
from .helpers import get_sender_service

logger = logging.getLogger("AdminSenderSubscribersAPI")


@admin_endpoint(methods=("GET", "POST", "PUT", "DELETE"))
def admin_sender_subscribers(req):
    sender_service = get_sender_service()

    if req.method == "GET":
        try:
            dto = SubscriberQueryDTO.model_validate(dict(req.args or {}))
            if dto.email:
                return jsonify(sender_service.get_subscriber(str(dto.email)) or {}), 200
            return jsonify(sender_service.list_subscribers(params=dict(req.args or {})) or {}), 200
        except PydanticValidationError as err:
            return handle_pydantic_error(err)
        except Exception as err:
            return handle_service_error(err)

    if req.method == "POST":
        try:
            dto = UpsertSubscriberRequestDTO.model_validate(req.get_json(silent=True) or {})
            result = sender_service.upsert_subscriber(
                email=str(dto.email),
                firstname=dto.firstname,
                lastname=dto.lastname,
                phone=dto.phone,
                groups=dto.groups,
                fields=dto.fields,
            )
            return jsonify(result or {}), 200
        except PydanticValidationError as err:
            return handle_pydantic_error(err)
        except Exception as err:
            return handle_service_error(err)

    if req.method == "PUT":
        try:
            dto = UpdateSubscriberRequestDTO.model_validate(req.get_json(silent=True) or {})
            result = sender_service.update_subscriber(str(dto.email), dto.changes())
            return jsonify(result or {}), 200
        except PydanticValidationError as err:
            return handle_pydantic_error(err)
        except Exception as err:
            return handle_service_error(err)

    try:
        dto = DeleteSubscriberRequestDTO.model_validate(req.get_json(silent=True) or {})
        sender_service.delete_subscriber(str(dto.email))
        return jsonify({"deleted": True}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST", "DELETE"))
def admin_sender_subscriber_groups(req):
    sender_service = get_sender_service()
    try:
        data = {**(req.get_json(silent=True) or {}), **dict(req.args or {})}
        dto = SubscriberGroupRequestDTO.model_validate(data)

        if req.method == "POST":
            result = sender_service.add_to_group(str(dto.email), dto.group_id)
            return jsonify({"added": result}), 200

        result = sender_service.remove_from_group(str(dto.email), dto.group_id)
        return jsonify({"removed": result}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def admin_sender_subscriber_events(req):
    sender_service = get_sender_service()
    try:
        dto = SubscriberEventQueryDTO.model_validate(dict(req.args or {}))
        identifier = str(dto.email) if dto.email else dto.id
        result = sender_service.get_subscriber_events(identifier, actions=dto.actions)
        return jsonify(result or {}), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
