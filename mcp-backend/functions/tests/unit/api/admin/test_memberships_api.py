import types

from api.admin import members_api
from services.service_errors import NotFoundError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def test_get_memberships_invalid_method():
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.get_memberships(req))
    assert status == 405


def test_get_memberships_happy_path(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(get_all=lambda: [{"id": "mem-1"}]),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(members_api.get_memberships(req))
    assert status == 200
    assert resp == [{"id": "mem-1"}]


def test_get_membership_missing_params():
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(members_api.get_membership(req))
    assert status == 400
    assert resp["error"] == "Missing membership ID or slug"


def test_create_membership_missing_body(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: None)
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.create_membership(req))
    assert status == 400
    assert resp["error"] == "Missing JSON body"


def test_create_membership_happy_path(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {"birthdate": "01-01-1990"})
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(create=lambda dto: {"id": "mem-1"}),
    )
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.create_membership(req))
    assert status == 201
    assert resp["id"] == "mem-1"


def test_update_membership_missing_id(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {"name": "Test"})
    req = DummyRequest(method="PUT")
    resp, status = unwrap_response(members_api.update_membership(req))
    assert status == 400
    assert resp["error"] == "Missing membership_id or body"


def test_update_membership_validation_error(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(update=lambda membership_id, dto: (_ for _ in ()).throw(ValidationError("bad"))),
    )
    monkeypatch.setattr(members_api.request, "get_json", lambda: {"membership_id": "mem-1"})
    req = DummyRequest(method="PUT")
    resp, status = unwrap_response(members_api.update_membership(req))
    assert status == 400
    assert resp["error"] == "bad"


def test_delete_membership_missing_id(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {})
    req = DummyRequest(method="DELETE")
    resp, status = unwrap_response(members_api.delete_membership(req))
    assert status == 400
    assert resp["error"] == "Missing membership_id"


def test_send_membership_card_missing_id(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.send_membership_card(req))
    assert status == 400
    assert resp["error"] == "Missing membership_id"


def test_get_membership_purchases_slug(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(
            get_by_id=lambda _id, slug=None: {"id": "mem-1"},
            get_purchases=lambda membership_id: [{"id": "pur-1"}],
        ),
    )
    req = DummyRequest(method="GET", args={"slug": "slug-1"})
    resp, status = unwrap_response(members_api.get_membership_purchases(req))
    assert status == 200
    assert resp == [{"id": "pur-1"}]


def test_get_membership_events_missing_params():
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(members_api.get_membership_events(req))
    assert status == 400
    assert resp["error"] == "Missing membership_id or slug"


def test_set_membership_price_missing_fee(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.set_membership_price(req))
    assert status == 400
    assert resp["error"] == "Missing membership_fee"


def test_set_membership_price_happy_path(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {"membership_fee": 20, "year": 2026})
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(set_membership_price=lambda fee, year=None: {"ok": True}),
    )
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.set_membership_price(req))
    assert status == 200
    assert resp["ok"] is True


def test_get_membership_price_not_found(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(get_membership_price=lambda year=None: (_ for _ in ()).throw(NotFoundError("missing"))),
    )
    req = DummyRequest(method="GET", args={"year": "2026"})
    resp, status = unwrap_response(members_api.get_membership_price(req))
    assert status == 404
    assert resp["error"] == "missing"


def test_get_memberships_report_missing_event():
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(members_api.get_memberships_report(req))
    assert status == 400
    assert resp["error"] == "Missing event_id"


def test_get_memberships_report_happy_path(monkeypatch):
    """Returns membership report payload."""
    monkeypatch.setattr(
        members_api,
        "membership_reports_service",
        types.SimpleNamespace(get_memberships_report=lambda event_id: {"rows": []}),
    )
    req = DummyRequest(method="GET", args={"event_id": "evt-1"})
    resp, status = unwrap_response(members_api.get_memberships_report(req))
    assert status == 200
    assert resp == {"rows": []}
