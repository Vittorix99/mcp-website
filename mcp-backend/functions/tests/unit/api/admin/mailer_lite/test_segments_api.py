import types

from api.admin.mailer_lite import segments_api
from tests.utils import DummyRequest, unwrap_response


def test_segments_get_calls_client(monkeypatch):
    monkeypatch.setattr(
        segments_api,
        "segments_client",
        types.SimpleNamespace(
            get=lambda segment_id, params=None: {"id": segment_id},
            list=lambda params=None: {"data": []},
        ),
    )

    req = DummyRequest(method="GET", args={"id": "99"})
    resp, status = unwrap_response(segments_api.admin_mailerlite_segments(req))
    assert status == 200
    assert resp["id"] == "99"


def test_segments_delete_missing_id():
    req = DummyRequest(method="DELETE", json={})
    resp, status = unwrap_response(segments_api.admin_mailerlite_segments(req))
    assert status == 400
    assert "Missing segment id" in resp["error"]


def test_segments_list(monkeypatch):
    monkeypatch.setattr(
        segments_api,
        "segments_client",
        types.SimpleNamespace(list=lambda params=None: {"data": []}),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(segments_api.admin_mailerlite_segments(req))
    assert status == 200
    assert resp == {"data": []}


def test_segments_update_missing_name():
    req = DummyRequest(method="PUT", json={"id": 1})
    resp, status = unwrap_response(segments_api.admin_mailerlite_segments(req))
    assert status == 400
    assert "Missing segment name" in resp["error"]


def test_segments_update_missing_id():
    req = DummyRequest(method="PUT", json={"name": "x"})
    resp, status = unwrap_response(segments_api.admin_mailerlite_segments(req))
    assert status == 400
    assert "Missing segment id" in resp["error"]


def test_segment_subscribers_missing_id():
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(segments_api.admin_mailerlite_segment_subscribers(req))
    assert status == 400
    assert "Missing segment_id" in resp["error"]


def test_segments_invalid_method():
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(segments_api.admin_mailerlite_segments(req))
    assert status == 405


def test_segment_subscribers_invalid_method():
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(segments_api.admin_mailerlite_segment_subscribers(req))
    assert status == 405


def test_segments_mailerlite_error(monkeypatch):
    def raise_error(*args, **kwargs):
        raise segments_api.MailerLiteError("boom", status=500, payload={"detail": "x"})

    monkeypatch.setattr(
        segments_api,
        "segments_client",
        types.SimpleNamespace(list=raise_error),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(segments_api.admin_mailerlite_segments(req))
    assert status == 500
    assert resp["error"] == "MailerLite request failed"
