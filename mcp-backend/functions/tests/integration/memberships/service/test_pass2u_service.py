"""Integration tests for Pass2UService.

These tests use the Firestore emulator for membership_settings reads,
and mock Pass2URoutes HTTP calls to avoid real external network calls.
"""
from unittest.mock import patch
from uuid import uuid4

import pytest

from config.firebase_config import db
from models import Membership, MembershipPassResult
from clients.pass2u_client import Pass2UApiResult
from services.memberships.pass2u_service import Pass2UService


_MODEL_ID = "integ-test-model-abc123"


# ─── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _seed_wallet_model():
    """Seed membership_settings/current_model in the Firestore emulator."""
    ref = db.collection("membership_settings").document("current_model")
    ref.set({"model_id": _MODEL_ID})
    yield
    ref.delete()


@pytest.fixture
def service():
    return Pass2UService()


@pytest.fixture
def membership():
    return Membership(
        name="Mario",
        surname="Rossi",
        email="mario.rossi@example.com",
        end_date="2026-12-31T23:59:59+00:00",
        start_date="2026-01-01T00:00:00+00:00",
        birthdate="01-01-1990",
        phone="+393331234567",
        subscription_valid=True,
        membership_type="manual",
    )


def _ok_result(pass_id: str) -> Pass2UApiResult:
    return Pass2UApiResult(status_code=200, payload={"passId": pass_id})


def _err_result(status: int, message: str = "Error") -> Pass2UApiResult:
    return Pass2UApiResult(status_code=status, error_message=message)


# ─── _get_model_id ────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_get_model_id_reads_from_firestore(service):
    """_get_model_id returns the model_id stored in Firestore."""
    model_id = service._get_model_id()
    assert model_id == _MODEL_ID


@pytest.mark.integration
def test_get_model_id_raises_when_doc_missing(service):
    """_get_model_id raises RuntimeError when document is absent."""
    db.collection("membership_settings").document("current_model").delete()
    with pytest.raises(RuntimeError, match="non trovato"):
        service._get_model_id()


@pytest.mark.integration
def test_get_model_id_raises_when_field_missing(service):
    """_get_model_id raises RuntimeError when model_id field is missing."""
    db.collection("membership_settings").document("current_model").set({"other_field": "x"})
    with pytest.raises(RuntimeError, match="model_id"):
        service._get_model_id()


# ─── create_membership_pass ───────────────────────────────────────────────────

@pytest.mark.integration
def test_create_membership_pass_success(service, membership):
    """Returns a MembershipPassResult with correct pass_id and wallet_url."""
    pass_id = f"pass_{uuid4().hex[:8]}"

    with patch("clients.pass2u_client.Pass2URoutes.create_pass", return_value=_ok_result(pass_id)):
        result = service.create_membership_pass("mem_001", membership)

    assert result is not None
    assert isinstance(result, MembershipPassResult)
    assert result.pass_id == pass_id
    assert result.wallet_url == f"https://www.pass2u.net/d/{pass_id}"


@pytest.mark.integration
def test_create_membership_pass_passes_correct_model_id(service, membership):
    """Passes the model_id read from Firestore to Pass2URoutes.create_pass."""
    pass_id = f"pass_{uuid4().hex[:8]}"
    captured = {}

    def _mock_create(model_id, api_key, body, **kwargs):
        captured["model_id"] = model_id
        return _ok_result(pass_id)

    with patch("clients.pass2u_client.Pass2URoutes.create_pass", side_effect=_mock_create):
        service.create_membership_pass("mem_model", membership)

    assert captured["model_id"] == _MODEL_ID


@pytest.mark.integration
def test_create_membership_pass_payload_structure(service, membership):
    """Verifies barcode and fields sent to Pass2U have the correct shape."""
    pass_id = f"pass_{uuid4().hex[:8]}"
    captured_body = {}

    def _mock_create(model_id, api_key, body, **kwargs):
        captured_body.update(body)
        return _ok_result(pass_id)

    with patch("clients.pass2u_client.Pass2URoutes.create_pass", side_effect=_mock_create):
        service.create_membership_pass("mem_payload", membership)

    assert captured_body["barcode"]["message"] == "mem_payload"
    assert captured_body["barcode"]["altText"] == "mem_payload"

    field_map = {f["key"]: f["value"] for f in captured_body["fields"]}
    assert field_map["name"] == "Mario Rossi"
    assert field_map["mail"] == "mario.rossi@example.com"
    assert "validity" in field_map
    # expirationDate must be present when end_date is a valid ISO datetime
    assert "expirationDate" in captured_body


@pytest.mark.integration
def test_create_membership_pass_409_returns_none(service, membership):
    """Returns None (non-blocking) when Pass2U responds 409 (pass already exists)."""
    with patch("clients.pass2u_client.Pass2URoutes.create_pass", return_value=_err_result(409)):
        result = service.create_membership_pass("mem_409", membership)

    assert result is None


@pytest.mark.integration
def test_create_membership_pass_http_error_returns_none(service, membership):
    """Returns None (non-blocking) on 4xx/5xx HTTP errors."""
    for status in (400, 422, 500, 503):
        with patch("clients.pass2u_client.Pass2URoutes.create_pass", return_value=_err_result(status)):
            result = service.create_membership_pass(f"mem_{status}", membership)
        assert result is None, f"Expected None for status {status}"


@pytest.mark.integration
def test_create_membership_pass_missing_pass_id_returns_none(service, membership):
    """Returns None when Pass2U 200 response does not include passId."""
    ok_no_id = Pass2UApiResult(status_code=200, payload={"unexpected": "data"})

    with patch("clients.pass2u_client.Pass2URoutes.create_pass", return_value=ok_no_id):
        result = service.create_membership_pass("mem_noid", membership)

    assert result is None


@pytest.mark.integration
def test_create_membership_pass_exception_returns_none(service, membership):
    """Returns None when Pass2URoutes raises an unexpected exception."""
    with patch("clients.pass2u_client.Pass2URoutes.create_pass", side_effect=RuntimeError("boom")):
        result = service.create_membership_pass("mem_exc", membership)

    assert result is None


# ─── invalidate_membership_pass ───────────────────────────────────────────────

@pytest.mark.integration
def test_invalidate_membership_pass_success(service):
    """Returns True on successful invalidation."""
    with patch("clients.pass2u_client.Pass2URoutes.invalidate_pass",
               return_value=Pass2UApiResult(status_code=200, payload={})):
        result = service.invalidate_membership_pass("pass_abc")

    assert result is True


@pytest.mark.integration
def test_invalidate_membership_pass_204_success(service):
    """Returns True for 204 No Content (also a success status)."""
    with patch("clients.pass2u_client.Pass2URoutes.invalidate_pass",
               return_value=Pass2UApiResult(status_code=204, payload=None)):
        result = service.invalidate_membership_pass("pass_204")

    assert result is True


@pytest.mark.integration
def test_invalidate_membership_pass_404_returns_true(service):
    """Returns True when pass not found on Pass2U (already deleted — idempotent)."""
    with patch("clients.pass2u_client.Pass2URoutes.invalidate_pass",
               return_value=_err_result(404, "Not Found")):
        result = service.invalidate_membership_pass("pass_gone")

    assert result is True


@pytest.mark.integration
def test_invalidate_membership_pass_server_error_returns_false(service):
    """Returns False on HTTP 5xx error."""
    with patch("clients.pass2u_client.Pass2URoutes.invalidate_pass",
               return_value=_err_result(500, "Internal Server Error")):
        result = service.invalidate_membership_pass("pass_err")

    assert result is False


@pytest.mark.integration
def test_invalidate_membership_pass_exception_returns_false(service):
    """Returns False (non-blocking) when Pass2URoutes raises an exception."""
    with patch("clients.pass2u_client.Pass2URoutes.invalidate_pass",
               side_effect=ConnectionError("timeout")):
        result = service.invalidate_membership_pass("pass_timeout")

    assert result is False


@pytest.mark.integration
def test_invalidate_membership_pass_passes_correct_pass_id(service):
    """Passes the correct pass_id to Pass2URoutes.invalidate_pass."""
    captured = {}

    def _mock_invalidate(pass_id, api_key, **kwargs):
        captured["pass_id"] = pass_id
        return Pass2UApiResult(status_code=200, payload={})

    with patch("clients.pass2u_client.Pass2URoutes.invalidate_pass", side_effect=_mock_invalidate):
        service.invalidate_membership_pass("pass_specific_123")

    assert captured["pass_id"] == "pass_specific_123"
