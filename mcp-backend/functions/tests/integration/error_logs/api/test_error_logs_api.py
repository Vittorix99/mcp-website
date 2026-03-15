import uuid

import pytest

from api.admin import error_logs_api
from config.firebase_config import db
from tests.utils import DummyRequest, unwrap_response


def _create_error_log(payload):
    req = DummyRequest(method="POST", json=payload)
    resp, status = unwrap_response(error_logs_api.admin_error_logs(req))
    assert status == 201
    return resp.get("id")


def _delete_direct(error_log_id: str):
    if error_log_id:
        db.collection("error_logs").document(error_log_id).delete()


@pytest.mark.integration
def test_error_logs_api_crud_flow():
    """End-to-end CRUD on admin_error_logs endpoint."""
    created_id = None
    try:
        created_id = _create_error_log(
            {
                "service": "Sender",
                "operation": "campaign_send",
                "source": "integration_test",
                "message": f"Sender failure {uuid.uuid4().hex[:6]}",
                "status_code": 422,
                "context": {"campaign_id": "camp-1"},
            }
        )
        assert created_id

        get_req = DummyRequest(method="GET", args={"id": created_id})
        get_resp, get_status = unwrap_response(error_logs_api.admin_error_logs(get_req))
        assert get_status == 200
        assert get_resp.get("service") == "Sender"
        assert get_resp.get("resolved") is False

        update_req = DummyRequest(method="PUT", json={"id": created_id, "resolved": True})
        update_resp, update_status = unwrap_response(error_logs_api.admin_error_logs(update_req))
        assert update_status == 200
        assert update_resp.get("resolved") is True

        delete_req = DummyRequest(method="DELETE", args={"id": created_id})
        delete_resp, delete_status = unwrap_response(error_logs_api.admin_error_logs(delete_req))
        assert delete_status == 200
        assert delete_resp == {"deleted": True}
        created_id = None

        not_found_req = DummyRequest(method="GET", args={"id": created_id or "deleted-id"})
        _, nf_status = unwrap_response(error_logs_api.admin_error_logs(not_found_req))
        assert nf_status == 404
    finally:
        _delete_direct(created_id)


@pytest.mark.integration
def test_error_logs_api_filters_by_service_and_resolved():
    """Verifies list filters (`service`, `resolved`) on error logs API."""
    ids = []
    try:
        sender_id = _create_error_log(
            {
                "service": "Sender",
                "message": f"Sender error {uuid.uuid4().hex[:6]}",
                "resolved": False,
            }
        )
        pass2u_id = _create_error_log(
            {
                "service": "Pass2U",
                "message": f"Pass2U error {uuid.uuid4().hex[:6]}",
                "resolved": True,
            }
        )
        ids.extend([sender_id, pass2u_id])

        sender_req = DummyRequest(method="GET", args={"service": "Sender", "limit": "50"})
        sender_resp, sender_status = unwrap_response(error_logs_api.admin_error_logs(sender_req))
        assert sender_status == 200
        sender_rows = sender_resp.get("error_logs", [])
        assert any(row.get("id") == sender_id for row in sender_rows)

        resolved_req = DummyRequest(method="GET", args={"resolved": "true", "limit": "50"})
        resolved_resp, resolved_status = unwrap_response(error_logs_api.admin_error_logs(resolved_req))
        assert resolved_status == 200
        resolved_rows = resolved_resp.get("error_logs", [])
        assert any(row.get("id") == pass2u_id for row in resolved_rows)
    finally:
        for entry_id in ids:
            _delete_direct(entry_id)
