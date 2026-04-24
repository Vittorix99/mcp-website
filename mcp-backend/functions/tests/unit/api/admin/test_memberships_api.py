import types

from api.admin import members_api
from errors.service_errors import NotFoundError, ValidationError
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

def test_get_membership_invalid_method():
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.get_membership(req))
    assert status == 405


def test_get_membership_happy_path(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(get_by_id=lambda membership_id, slug=None: {"id": membership_id}),
    )
    req = DummyRequest(method="GET", args={"id": "mem-1"})
    resp, status = unwrap_response(members_api.get_membership(req))
    assert status == 200
    assert resp["id"] == "mem-1"


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

def test_update_membership_happy_path(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(update=lambda membership_id, dto: {"id": membership_id}),
    )
    monkeypatch.setattr(
        members_api.request,
        "get_json",
        lambda: {"membership_id": "mem-1", "name": "Test"},
    )
    req = DummyRequest(method="PUT")
    resp, status = unwrap_response(members_api.update_membership(req))
    assert status == 200
    assert resp["id"] == "mem-1"


def test_merge_memberships_missing_ids(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.merge_memberships(req))
    assert status == 400
    assert resp["error"] == "Missing source_id or target_id"


def test_merge_memberships_happy_path(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "merge_service",
        types.SimpleNamespace(merge=lambda source_id, target_id: {"source": source_id, "target": target_id}),
    )
    monkeypatch.setattr(
        members_api.request,
        "get_json",
        lambda: {"source_id": "mem-old", "target_id": "mem-new"},
    )
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.merge_memberships(req))
    assert status == 200
    assert resp["source"] == "mem-old"
    assert resp["target"] == "mem-new"


def test_delete_membership_missing_id(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {})
    req = DummyRequest(method="DELETE")
    resp, status = unwrap_response(members_api.delete_membership(req))
    assert status == 400
    assert resp["error"] == "Missing membership_id"

def test_delete_membership_happy_path(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(delete=lambda membership_id: {"id": membership_id}),
    )
    monkeypatch.setattr(members_api.request, "get_json", lambda: {"membership_id": "mem-1"})
    req = DummyRequest(method="DELETE")
    resp, status = unwrap_response(members_api.delete_membership(req))
    assert status == 200
    assert resp["id"] == "mem-1"


def test_send_membership_card_missing_id(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.send_membership_card(req))
    assert status == 400
    assert resp["error"] == "Missing membership_id"

def test_send_membership_card_happy_path(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(send_card=lambda membership_id: {"id": membership_id}),
    )
    monkeypatch.setattr(members_api.request, "get_json", lambda: {"membership_id": "mem-1"})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.send_membership_card(req))
    assert status == 200
    assert resp["id"] == "mem-1"


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

def test_get_membership_events_happy_path(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(get_events=lambda membership_id: [{"id": "evt-1"}]),
    )
    req = DummyRequest(method="GET", args={"id": "mem-1"})
    resp, status = unwrap_response(members_api.get_membership_events(req))
    assert status == 200
    assert resp == [{"id": "evt-1"}]

def test_get_membership_events_slug(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(
            get_by_id=lambda _id, slug=None: {"id": "mem-1"},
            get_events=lambda membership_id: [{"id": "evt-1"}],
        ),
    )
    req = DummyRequest(method="GET", args={"slug": "slug-1"})
    resp, status = unwrap_response(members_api.get_membership_events(req))
    assert status == 200
    assert resp == [{"id": "evt-1"}]


def test_set_membership_price_missing_fee(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.set_membership_price(req))
    assert status == 400
    assert resp["error"] == "Missing membership_fee"

def test_set_membership_price_happy_path(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(set_membership_price=lambda fee, year=None: {"fee": fee, "year": year}),
    )
    monkeypatch.setattr(
        members_api.request,
        "get_json",
        lambda: {"membership_fee": 10, "year": "2026"},
    )
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.set_membership_price(req))
    assert status == 200
    assert resp["fee"] == 10
    assert resp["year"] == "2026"

def test_get_membership_price_happy_path(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(get_membership_price=lambda year=None: {"fee": 10, "year": year}),
    )
    req = DummyRequest(method="GET", args={"year": "2026"})
    resp, status = unwrap_response(members_api.get_membership_price(req))
    assert status == 200
    assert resp["fee"] == 10
    assert resp["year"] == "2026"

def test_get_memberships_report_missing_event_id():
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(members_api.get_memberships_report(req))
    assert status == 400
    assert resp["error"] == "Missing event_id"

def test_get_memberships_report_happy_path(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "membership_reports_service",
        types.SimpleNamespace(get_memberships_report=lambda event_id: {"event_id": event_id}),
    )
    req = DummyRequest(method="GET", args={"event_id": "evt-1"})
    resp, status = unwrap_response(members_api.get_memberships_report(req))
    assert status == 200
    assert resp["event_id"] == "evt-1"

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


def test_create_wallet_pass_missing_membership_id(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {})
    req = DummyRequest(method="POST", json={})
    resp, status = unwrap_response(members_api.create_wallet_pass(req))
    assert status == 400
    assert resp["error"] == "Missing membership_id"


def test_create_wallet_pass_happy_path(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(create_wallet_pass=lambda membership_id: {"id": membership_id, "ok": True}),
    )
    monkeypatch.setattr(members_api.request, "get_json", lambda: {"membership_id": "mem-1"})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.create_wallet_pass(req))
    assert status == 200
    assert resp["id"] == "mem-1"
    assert resp["ok"] is True


def test_invalidate_wallet_pass_missing_membership_id(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {})
    req = DummyRequest(method="POST", json={})
    resp, status = unwrap_response(members_api.invalidate_wallet_pass(req))
    assert status == 400
    assert resp["error"] == "Missing membership_id"


def test_invalidate_wallet_pass_happy_path(monkeypatch):
    monkeypatch.setattr(
        members_api,
        "memberships_service",
        types.SimpleNamespace(invalidate_wallet_pass=lambda membership_id: {"id": membership_id, "ok": True}),
    )
    monkeypatch.setattr(members_api.request, "get_json", lambda: {"membership_id": "mem-1"})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.invalidate_wallet_pass(req))
    assert status == 200
    assert resp["id"] == "mem-1"
    assert resp["ok"] is True


def test_get_wallet_model_happy_path(monkeypatch):
    monkeypatch.setattr(
        "services.memberships.pass2u_service.Pass2UService._get_model_id",
        lambda _self: "371225",
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(members_api.get_wallet_model(req))
    assert status == 200
    assert resp["model_id"] == "371225"


def test_set_wallet_model_missing_model_id(monkeypatch):
    monkeypatch.setattr(members_api.request, "get_json", lambda: {})
    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.set_wallet_model(req))
    assert status == 400
    assert resp["error"] == "Missing model_id"


def test_set_wallet_model_happy_path(monkeypatch):
    calls = {}

    class _Doc:
        def set(self, payload):
            calls["payload"] = payload

    class _Collection:
        def document(self, doc_id):
            calls["doc_id"] = doc_id
            return _Doc()

    class _DB:
        def collection(self, name):
            calls["collection"] = name
            return _Collection()

    monkeypatch.setattr("config.firebase_config.db", _DB())
    monkeypatch.setattr(members_api.request, "get_json", lambda: {"model_id": "371225"})

    req = DummyRequest(method="POST")
    resp, status = unwrap_response(members_api.set_wallet_model(req))
    assert status == 200
    assert resp["model_id"] == "371225"
    assert calls["collection"] == "membership_settings"
    assert calls["doc_id"] == "current_model"
    assert calls["payload"] == {"model_id": "371225"}
