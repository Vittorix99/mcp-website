from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from api.decorators import admin_endpoint
from dto.membership_api import (
    CreateMembershipRequestDTO,
    MembershipIdRequestDTO,
    MembershipListQueryDTO,
    MembershipLookupQueryDTO,
    MembershipPriceQueryDTO,
    MembershipPriceSetRequestDTO,
    MembershipReportQueryDTO,
    MergeMembershipsRequestDTO,
    RenewMembershipRequestDTO,
    UpdateMembershipRequestDTO,
    WalletModelSetRequestDTO,
)
from services.memberships.memberships_service import MembershipsService
from services.memberships.membership_reports_service import MembershipReportsService
from services.memberships.merge_service import MergeService
from utils.http_responses import handle_pydantic_error, handle_service_error

memberships_service = MembershipsService()
membership_reports_service = MembershipReportsService()
merge_service = MergeService()


@admin_endpoint(methods=("GET",))
def get_memberships(req):
    try:
        dto = MembershipListQueryDTO.model_validate(dict(req.args or {}))
        payload = memberships_service.get_all(year=dto.year)
        return jsonify([item.to_payload() for item in payload]), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def get_membership(req):
    try:
        dto = MembershipLookupQueryDTO.model_validate(dict(req.args or {}))
        payload = memberships_service.get_by_id(dto.id, slug=dto.slug)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def create_membership(req):
    try:
        dto = CreateMembershipRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = memberships_service.create(dto)
        return jsonify(payload.to_payload()), 201
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("PUT",))
def update_membership(req):
    try:
        dto = UpdateMembershipRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = memberships_service.update(dto.membership_id, dto)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def merge_memberships(req):
    try:
        dto = MergeMembershipsRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = merge_service.merge(dto.source_id, dto.target_id)
        return jsonify(payload), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("DELETE",))
def delete_membership(req):
    try:
        dto = MembershipIdRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = memberships_service.delete(dto.membership_id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def renew_membership(req):
    try:
        dto = RenewMembershipRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = memberships_service.renew(dto.membership_id, dto)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def send_membership_card(req):
    try:
        dto = MembershipIdRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = memberships_service.send_card(dto.membership_id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def get_membership_purchases(req):
    try:
        dto = MembershipLookupQueryDTO.model_validate(dict(req.args or {}))
        membership_id = dto.id
        if not membership_id and dto.slug:
            membership_id = memberships_service.get_by_id(None, slug=dto.slug).id
        payload = memberships_service.get_purchases(membership_id)
        return jsonify(payload), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def get_membership_events(req):
    try:
        dto = MembershipLookupQueryDTO.model_validate(dict(req.args or {}))
        membership_id = dto.id
        if not membership_id and dto.slug:
            membership_id = memberships_service.get_by_id(None, slug=dto.slug).id
        payload = memberships_service.get_events(membership_id)
        return jsonify(payload), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def set_membership_price(req):
    try:
        dto = MembershipPriceSetRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = memberships_service.set_membership_price(dto.membership_fee, year=dto.year)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def get_membership_price(req):
    try:
        dto = MembershipPriceQueryDTO.model_validate(dict(req.args or {}))
        payload = memberships_service.get_membership_price(year=dto.year)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def create_wallet_pass(req):
    try:
        dto = MembershipIdRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = memberships_service.create_wallet_pass(dto.membership_id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def invalidate_wallet_pass(req):
    try:
        dto = MembershipIdRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = memberships_service.invalidate_wallet_pass(dto.membership_id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def get_wallet_model(req):
    try:
        payload = memberships_service.get_wallet_model()
        return jsonify(payload.to_payload()), 200
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("POST",))
def set_wallet_model(req):
    try:
        dto = WalletModelSetRequestDTO.model_validate(req.get_json(silent=True) or {})
        payload = memberships_service.set_wallet_model(dto.model_id)
        return jsonify(payload.to_payload()), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)


@admin_endpoint(methods=("GET",))
def get_memberships_report(req):
    try:
        dto = MembershipReportQueryDTO.model_validate(dict(req.args or {}))
        payload = membership_reports_service.get_memberships_report(event_id=dto.event_id)
        return jsonify(payload), 200
    except PydanticValidationError as err:
        return handle_pydantic_error(err)
    except Exception as err:
        return handle_service_error(err)
