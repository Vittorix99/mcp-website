"""Request-contract characterization for the exported API handlers."""

import firebase_admin.auth
from flask import Flask, request
from unittest.mock import Mock

import pytest

from api.admin import events_api, members_api, order_recovery_api, participants_api, purchases_api
from api.entrance import entrance_api
from api.member import member_api
from api.public import discount_code_public_api, event_payment_api, events_api as public_events_api
from api.public import events_tickets_api
from tests.utils import unwrap_response


# module, handler, correct method, parses a body, service/repository boundaries
ENDPOINTS = (
    (events_api, "admin_create_event", "POST", True, ("events_service",)),
    (events_api, "admin_update_event", "PUT", True, ("events_service",)),
    (events_api, "admin_delete_event", "DELETE", True, ("events_service",)),
    (events_api, "admin_get_all_events", "GET", False, ("events_service",)),
    (events_api, "admin_get_event_by_id", "GET", False, ("events_service",)),
    (events_api, "admin_get_event_guide", "GET", False, ("guide_service",)),
    (events_api, "admin_update_event_guide", "PUT", True, ("guide_service",)),
    (events_api, "admin_toggle_guide_published", "PATCH", True, ("guide_service",)),
    (members_api, "get_memberships", "GET", False, ("memberships_service",)),
    (members_api, "get_membership", "GET", False, ("memberships_service",)),
    (members_api, "create_membership", "POST", True, ("membership_repository",)),
    (members_api, "update_membership", "PUT", True, ("memberships_service",)),
    (members_api, "merge_memberships", "POST", True, ("merge_service",)),
    (members_api, "delete_membership", "DELETE", True, ("memberships_service",)),
    (members_api, "renew_membership", "POST", True, ("memberships_service",)),
    (members_api, "send_membership_card", "POST", True, ("memberships_service",)),
    (members_api, "get_membership_purchases", "GET", False, ("memberships_service",)),
    (members_api, "get_membership_events", "GET", False, ("memberships_service",)),
    (members_api, "set_membership_price", "POST", True, ("memberships_service",)),
    (members_api, "get_membership_price", "GET", False, ("memberships_service",)),
    (members_api, "create_wallet_pass", "POST", True, ("memberships_service",)),
    (members_api, "invalidate_wallet_pass", "POST", True, ("memberships_service",)),
    (members_api, "get_wallet_model", "GET", False, ("memberships_service",)),
    (members_api, "set_wallet_model", "POST", True, ("memberships_service",)),
    (members_api, "get_memberships_report", "GET", False, ("membership_reports_service",)),
    (participants_api, "get_participants_by_event", "POST", True, ("participants_service",)),
    (participants_api, "get_participant", "POST", True, ("participants_service",)),
    (participants_api, "create_participant", "POST", True, ("participants_service",)),
    (participants_api, "update_participant", "PUT", True, ("participants_service",)),
    (participants_api, "delete_participant", "DELETE", True, ("participants_service",)),
    (participants_api, "send_ticket", "POST", True, ("participants_service",)),
    (participants_api, "send_location", "POST", True, ("location_service",)),
    (participants_api, "send_location_to_all", "POST", True, ("location_service",)),
    (participants_api, "send_omaggio_emails", "POST", True, ("participants_service",)),
    (purchases_api, "get_all_purchases", "GET", False, ("purchases_service",)),
    (purchases_api, "get_purchase", "GET", False, ("purchases_service",)),
    (purchases_api, "create_purchase", "POST", True, ("purchases_service",)),
    (purchases_api, "update_purchase_status", "POST", True, ("purchases_service",)),
    (purchases_api, "delete_purchase", "DELETE", True, ("purchases_service",)),
    (order_recovery_api, "recover_order_event", "POST", True, ("recovery_service",)),
    (public_events_api, "get_all_events", "GET", False, ("events_service",)),
    (public_events_api, "get_next_event", "GET", False, ("events_service",)),
    (public_events_api, "get_event_by_id", "GET", False, ("events_service",)),
    (public_events_api, "get_event_guide", "GET", False, ("guide_service",)),
    (events_tickets_api, "check_participants", "POST", True, ("participants_service",)),
    (event_payment_api, "create_order_event", "POST", True, ("event_payment_service",)),
    (event_payment_api, "capture_order_event", "POST", True, ("event_payment_service",)),
    (discount_code_public_api, "validate_discount_code", "POST", True,
     ("event_repository", "discount_code_service")),
    (entrance_api, "entrance_generate_scan_token", "POST", True, ("entrance_service",)),
    (entrance_api, "entrance_verify_scan_token", "GET", False, ("entrance_service",)),
    (entrance_api, "entrance_deactivate_scan_token", "POST", True, ("entrance_service",)),
    (entrance_api, "entrance_manual_entry", "POST", True, ("entrance_service",)),
    (entrance_api, "entrance_validate", "POST", True, ("entrance_service",)),
    (member_api, "member_get_me", "GET", False, ("member_service",)),
    (member_api, "member_get_events", "GET", False, ("member_service",)),
    (member_api, "member_get_purchases", "GET", False, ("member_service",)),
    (member_api, "member_get_ticket", "GET", False, ("member_service",)),
    (member_api, "member_patch_preferences", "PATCH", True, ("member_service",)),
)

BAD_BODIES = (
    pytest.param(None, id="missing"),
    pytest.param(b"{", id="malformed-json"),
    pytest.param(b"null", id="json-null"),
    pytest.param(b"{}", id="empty-object"),
    pytest.param(b"[1]", id="array"),
    pytest.param(b'"x"', id="string"),
    pytest.param(b"1", id="number"),
    pytest.param(b"true", id="boolean"),
)

REQUIRED_LOOKUPS = (
    (events_api, "admin_get_event_by_id", ("events_service",)),
    (members_api, "get_membership", ("memberships_service",)),
    (purchases_api, "get_purchase", ("purchases_service",)),
    (public_events_api, "get_event_by_id", ("events_service",)),
    (entrance_api, "entrance_verify_scan_token", ("entrance_service",)),
    (member_api, "member_get_ticket", ("member_service",)),
)


def _request_context(method, raw_body=None):
    app = Flask("ops02-contracts")
    request_args = {"method": method, "headers": {"Authorization": "Bearer contract-token"}}
    if raw_body is not None:
        request_args.update(data=raw_body, content_type="application/json")
    return app.test_request_context("/", **request_args)


@pytest.mark.parametrize("module,handler_name,method,has_body,boundaries", ENDPOINTS)
def test_exported_handler_rejects_wrong_http_method(module, handler_name, method, has_body, boundaries):
    wrong_method = "GET" if has_body else "POST"
    with _request_context(wrong_method):
        payload, status = unwrap_response(getattr(module, handler_name)(request))

    assert status == 405
    assert payload["error"]


@pytest.mark.parametrize(
    "module,handler_name,method,has_body,boundaries",
    [row for row in ENDPOINTS if row[3] and row[1] != "create_order_event"],
)
@pytest.mark.parametrize("raw_body", BAD_BODIES)
def test_body_dto_rejects_invalid_raw_json_before_persistence(
    monkeypatch, module, handler_name, method, has_body, boundaries, raw_body
):
    if module is member_api:
        monkeypatch.setattr(
            firebase_admin.auth,
            "verify_id_token",
            lambda token: {"uid": "member-1", "email": "member@example.test", "email_verified": True},
        )

    service_traps = {}
    for boundary in boundaries:
        trap = Mock(name=f"{module.__name__}.{boundary}")
        if module is members_api and handler_name == "create_membership":
            monkeypatch.setattr(module.memberships_service, boundary, trap)
        else:
            monkeypatch.setattr(module, boundary, trap)
        service_traps[boundary] = trap

    with _request_context(method, raw_body):
        payload, status = unwrap_response(getattr(module, handler_name)(request))

    assert status == 400, payload
    assert payload["error"]
    for trap in service_traps.values():
        assert trap.mock_calls == []


@pytest.mark.parametrize("module,handler_name,boundaries", REQUIRED_LOOKUPS)
def test_required_lookup_query_rejects_missing_fields_before_service_access(
    monkeypatch, module, handler_name, boundaries
):
    if module is member_api:
        monkeypatch.setattr(
            firebase_admin.auth,
            "verify_id_token",
            lambda token: {"uid": "member-1", "email": "member@example.test", "email_verified": True},
        )

    service_traps = {}
    for boundary in boundaries:
        trap = Mock(name=f"{module.__name__}.{boundary}")
        monkeypatch.setattr(module, boundary, trap)
        service_traps[boundary] = trap

    with _request_context("GET"):
        payload, status = unwrap_response(getattr(module, handler_name)(request))

    assert status == 400
    assert payload["error"]
    for trap in service_traps.values():
        assert trap.mock_calls == []
