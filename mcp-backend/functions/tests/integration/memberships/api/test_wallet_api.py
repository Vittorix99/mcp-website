"""Integration tests for wallet pass API endpoints.

Tests create_wallet_pass and invalidate_wallet_pass endpoints end-to-end
against the Firestore emulator, with Pass2U HTTP calls mocked.
"""
from unittest.mock import patch
from uuid import uuid4

import pytest

from api.admin import members_api
from dto import MembershipDTO
from routes.pass2u_routes import Pass2UApiResult
from tests.utils import DummyRequest, unwrap_response


_MODEL_ID = "integ-api-model-xyz"
_PASS_ID = f"pass_{uuid4().hex[:8]}"
_WALLET_URL = f"https://www.pass2u.net/d/{_PASS_ID}"


# ─── helpers ─────────────────────────────────────────────────────────────────

def _pass2u_create_ok():
    return Pass2UApiResult(status_code=200, payload={"passId": _PASS_ID})


def _pass2u_invalidate_ok():
    return Pass2UApiResult(status_code=200, payload={})


def _patch_pass2u_create():
    return patch("routes.pass2u_routes.Pass2URoutes.create_pass", return_value=_pass2u_create_ok())


def _patch_pass2u_invalidate():
    return patch("routes.pass2u_routes.Pass2URoutes.invalidate_pass", return_value=_pass2u_invalidate_ok())


def _patch_model_id():
    return patch("services.memberships.pass2u_service.Pass2UService._get_model_id", return_value=_MODEL_ID)


# ─── create_wallet_pass ───────────────────────────────────────────────────────

@pytest.mark.integration
def test_create_wallet_pass_success(membership_payload, create_membership, membership_repository, monkeypatch):
    """Creates a wallet pass for an existing membership and persists it to Firestore."""
    membership_id = create_membership(membership_payload)

    monkeypatch.setattr(members_api.request, "get_json", lambda: {"membership_id": membership_id})

    with _patch_model_id(), _patch_pass2u_create():
        req = DummyRequest(method="POST")
        resp, status = unwrap_response(members_api.create_wallet_pass(req))

    assert status == 200
    assert resp.get("wallet_pass_id") == _PASS_ID
    assert resp.get("wallet_url") == _WALLET_URL

    # Verify persisted in Firestore
    saved = membership_repository.get_model(membership_id)
    assert saved.wallet_pass_id == _PASS_ID
    assert saved.wallet_url == _WALLET_URL


@pytest.mark.integration
def test_create_wallet_pass_missing_membership_id(monkeypatch):
    """Returns 400 when membership_id is absent from the request."""
    monkeypatch.setattr(members_api.request, "get_json", lambda: {})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.create_wallet_pass(req))
    assert status == 400
    assert resp.get("error")


@pytest.mark.integration
def test_create_wallet_pass_wrong_method():
    """Returns 405 for non-POST methods."""
    req = DummyRequest(method="GET")
    _, status = unwrap_response(members_api.create_wallet_pass(req))
    assert status == 405


@pytest.mark.integration
def test_create_wallet_pass_membership_not_found(monkeypatch):
    """Returns 404 when membership does not exist in Firestore."""
    monkeypatch.setattr(
        members_api.request,
        "get_json",
        lambda: {"membership_id": "non-existent-000"},
    )
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.create_wallet_pass(req))
    assert status == 404
    assert resp.get("error")


@pytest.mark.integration
def test_create_wallet_pass_pass2u_failure_returns_500(
    membership_payload, create_membership, monkeypatch
):
    """Returns 500 when Pass2U fails to create the pass."""
    membership_id = create_membership(membership_payload)
    monkeypatch.setattr(members_api.request, "get_json", lambda: {"membership_id": membership_id})

    failing_result = Pass2UApiResult(status_code=500, error_message="Pass2U unavailable")
    with _patch_model_id(), patch("routes.pass2u_routes.Pass2URoutes.create_pass", return_value=failing_result):
        req = DummyRequest(method="POST")
        resp, status = unwrap_response(members_api.create_wallet_pass(req))

    assert status == 500
    assert resp.get("error")


# ─── invalidate_wallet_pass ───────────────────────────────────────────────────

@pytest.mark.integration
def test_invalidate_wallet_pass_success(
    membership_payload, create_membership, membership_repository, monkeypatch
):
    """Invalidates a wallet pass and clears wallet fields from Firestore."""
    membership_id = create_membership(membership_payload)

    # Pre-load wallet data
    membership_repository.update_from_model(
        membership_id,
        MembershipDTO(wallet_pass_id=_PASS_ID, wallet_url=_WALLET_URL),
    )

    monkeypatch.setattr(members_api.request, "get_json", lambda: {"membership_id": membership_id})

    with _patch_pass2u_invalidate():
        req = DummyRequest(method="POST")
        resp, status = unwrap_response(members_api.invalidate_wallet_pass(req))

    assert status == 200
    assert "message" in resp

    # Verify wallet fields cleared in Firestore
    saved = membership_repository.get_model(membership_id)
    assert saved.wallet_pass_id is None
    assert saved.wallet_url is None


@pytest.mark.integration
def test_invalidate_wallet_pass_no_existing_pass(
    membership_payload, create_membership, monkeypatch
):
    """Returns 200 with a message when membership has no wallet pass (idempotent)."""
    membership_id = create_membership(membership_payload)
    monkeypatch.setattr(members_api.request, "get_json", lambda: {"membership_id": membership_id})

    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.invalidate_wallet_pass(req))

    assert status == 200
    assert "message" in resp


@pytest.mark.integration
def test_invalidate_wallet_pass_missing_membership_id(monkeypatch):
    """Returns 400 when membership_id is absent from the request."""
    monkeypatch.setattr(members_api.request, "get_json", lambda: {})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.invalidate_wallet_pass(req))
    assert status == 400
    assert resp.get("error")


@pytest.mark.integration
def test_invalidate_wallet_pass_wrong_method():
    """Returns 405 for non-POST methods."""
    req = DummyRequest(method="GET")
    _, status = unwrap_response(members_api.invalidate_wallet_pass(req))
    assert status == 405


@pytest.mark.integration
def test_invalidate_wallet_pass_membership_not_found(monkeypatch):
    """Returns 404 when membership does not exist in Firestore."""
    monkeypatch.setattr(
        members_api.request,
        "get_json",
        lambda: {"membership_id": "non-existent-999"},
    )
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.invalidate_wallet_pass(req))
    assert status == 404
    assert resp.get("error")


@pytest.mark.integration
def test_invalidate_wallet_pass_pass2u_404_still_clears_firestore(
    membership_payload, create_membership, membership_repository, monkeypatch
):
    """When Pass2U returns 404 (pass already gone), wallet fields are still cleared."""
    membership_id = create_membership(membership_payload)
    membership_repository.update_from_model(
        membership_id,
        MembershipDTO(wallet_pass_id="stale_pass_id", wallet_url="https://www.pass2u.net/d/stale"),
    )

    monkeypatch.setattr(members_api.request, "get_json", lambda: {"membership_id": membership_id})

    not_found = Pass2UApiResult(status_code=404, error_message="Not Found")
    with patch("routes.pass2u_routes.Pass2URoutes.invalidate_pass", return_value=not_found):
        req = DummyRequest(method="POST")
        resp, status = unwrap_response(members_api.invalidate_wallet_pass(req))

    assert status == 200
    saved = membership_repository.get_model(membership_id)
    assert saved.wallet_pass_id is None
    assert saved.wallet_url is None
