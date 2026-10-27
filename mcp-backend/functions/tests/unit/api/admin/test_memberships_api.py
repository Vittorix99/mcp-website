import types

from api.admin import members_api
from dto.membership_api import (
    MembershipActionResponseDTO,
    MembershipPriceResponseDTO,
    MembershipResponseDTO,
    MembershipWalletPassResponseDTO,
    WalletModelResponseDTO,
)
from errors.service_errors import NotFoundError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def _membership(membership_id="mem-1", **fields):
    return MembershipResponseDTO(id=membership_id, name="Ada", surname="Lovelace", **fields)


def test_get_memberships_invalid_method():
    resp, status = unwrap_response(members_api.get_memberships(DummyRequest(method="POST")))
    assert status == 405


def test_get_memberships_happy_path(monkeypatch):
    calls = {}
    result = [_membership()]
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        get_all=lambda **kwargs: (calls.update(kwargs), result)[1]
    ))
    resp, status = unwrap_response(members_api.get_memberships(DummyRequest(method="GET", args={"year": "2026"})))
    assert status == 200
    assert resp[0]["id"] == "mem-1"
    assert resp[0]["name"] == "Ada"
    assert calls == {"year": 2026}


def test_get_membership_missing_params():
    resp, status = unwrap_response(members_api.get_membership(DummyRequest(method="GET", args={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert resp["details"]


def test_get_membership_invalid_method():
    resp, status = unwrap_response(members_api.get_membership(DummyRequest(method="POST")))
    assert status == 405


def test_get_membership_happy_path(monkeypatch):
    calls = {}
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        get_by_id=lambda membership_id, slug=None: (calls.update(id=membership_id, slug=slug), _membership(membership_id))[1]
    ))
    resp, status = unwrap_response(members_api.get_membership(DummyRequest(method="GET", args={"id": "mem-1"})))
    assert status == 200
    assert resp["id"] == "mem-1"
    assert calls == {"id": "mem-1", "slug": None}


def test_create_membership_missing_body(monkeypatch):
    calls = []
    def create(dto):
        calls.append(dto)
        raise ValidationError("Utente minorenne non ammesso")
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(create=create))
    resp, status = unwrap_response(members_api.create_membership(DummyRequest(method="POST", json=None)))
    assert status == 400
    assert resp["error"] == "Utente minorenne non ammesso"
    assert len(calls) == 1
    assert calls[0].birthdate is None


def test_create_membership_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        create=lambda dto: (calls.append(dto), MembershipActionResponseDTO(message="created", id="mem-1"))[1]
    ))
    req = DummyRequest(method="POST", json={"birthdate": "01-01-1990", "email": "ADA@example.com", "name": "Ada"})
    resp, status = unwrap_response(members_api.create_membership(req))
    assert status == 201
    assert resp["id"] == "mem-1"
    assert calls[0].birthdate == "01-01-1990"
    assert calls[0].email == "ada@example.com"
    assert calls[0].name == "Ada"


def test_create_membership_maps_service_rejection_for_minor(monkeypatch):
    calls = []
    def create(dto):
        calls.append(dto)
        raise ValidationError("Utente minorenne non ammesso")
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(create=create))
    resp, status = unwrap_response(members_api.create_membership(DummyRequest(method="POST", json={"birthdate": "01-01-2015"})))
    assert status == 400
    assert resp["error"] == "Utente minorenne non ammesso"
    assert len(calls) == 1
    assert calls[0].birthdate == "01-01-2015"


def test_update_membership_missing_id(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(update=lambda *args: calls.append(args)))
    resp, status = unwrap_response(members_api.update_membership(DummyRequest(method="PUT", json={"name": "Test"})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert calls == []


def test_update_membership_validation_error(monkeypatch):
    calls = []
    def update(membership_id, dto):
        calls.append((membership_id, dto))
        raise ValidationError("bad")
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(update=update))
    resp, status = unwrap_response(members_api.update_membership(DummyRequest(method="PUT", json={"membership_id": "mem-1", "name": "Ada"})))
    assert status == 400
    assert resp["error"] == "bad"
    assert calls[0][0] == "mem-1"
    assert calls[0][1].name == "Ada"


def test_update_membership_invalid_dto_does_not_call_service(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(update=lambda *args: calls.append(args)))
    resp, status = unwrap_response(members_api.update_membership(DummyRequest(method="PUT", json={"membership_id": "mem-1"})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert calls == []


def test_update_membership_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        update=lambda membership_id, dto: (calls.append((membership_id, dto)), MembershipActionResponseDTO(message="updated", id=membership_id))[1]
    ))
    resp, status = unwrap_response(members_api.update_membership(DummyRequest(method="PUT", json={"membership_id": "mem-1", "name": "Test"})))
    assert status == 200
    assert resp["id"] == "mem-1"
    assert calls[0][0] == "mem-1"
    assert calls[0][1].name == "Test"


def test_merge_memberships_missing_ids(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "merge_service", types.SimpleNamespace(merge=lambda *args: calls.append(args)))
    resp, status = unwrap_response(members_api.merge_memberships(DummyRequest(method="POST", json={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert calls == []


def test_merge_memberships_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "merge_service", types.SimpleNamespace(
        merge=lambda source_id, target_id: (calls.append((source_id, target_id)), {"source": source_id, "target": target_id})[1]
    ))
    resp, status = unwrap_response(members_api.merge_memberships(DummyRequest(method="POST", json={"source_id": "mem-old", "target_id": "mem-new"})))
    assert status == 200
    assert resp == {"source": "mem-old", "target": "mem-new"}
    assert calls == [("mem-old", "mem-new")]


def test_delete_membership_missing_id(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(delete=lambda value: calls.append(value)))
    resp, status = unwrap_response(members_api.delete_membership(DummyRequest(method="DELETE", json={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert calls == []


def test_delete_membership_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        delete=lambda membership_id: (calls.append(membership_id), MembershipActionResponseDTO(message="deleted", id=membership_id))[1]
    ))
    resp, status = unwrap_response(members_api.delete_membership(DummyRequest(method="DELETE", json={"membership_id": "mem-1"})))
    assert status == 200
    assert resp["id"] == "mem-1"
    assert calls == ["mem-1"]


def test_send_membership_card_missing_id(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(send_card=lambda value: calls.append(value)))
    resp, status = unwrap_response(members_api.send_membership_card(DummyRequest(method="POST", json={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert calls == []


def test_send_membership_card_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        send_card=lambda membership_id: (calls.append(membership_id), MembershipActionResponseDTO(message="sent", id=membership_id))[1]
    ))
    resp, status = unwrap_response(members_api.send_membership_card(DummyRequest(method="POST", json={"membership_id": "mem-1"})))
    assert status == 200
    assert resp["id"] == "mem-1"
    assert calls == ["mem-1"]


def test_get_membership_purchases_slug(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        get_by_id=lambda membership_id, slug=None: (calls.append((membership_id, slug)), _membership("mem-1"))[1],
        get_purchases=lambda membership_id: (calls.append(membership_id), [{"id": "pur-1"}])[1],
    ))
    resp, status = unwrap_response(members_api.get_membership_purchases(DummyRequest(method="GET", args={"slug": "slug-1"})))
    assert status == 200
    assert resp == [{"id": "pur-1"}]
    assert calls == [(None, "slug-1"), "mem-1"]


def test_get_membership_events_missing_params():
    resp, status = unwrap_response(members_api.get_membership_events(DummyRequest(method="GET", args={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"


def test_get_membership_events_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        get_events=lambda membership_id: (calls.append(membership_id), [{"id": "evt-1"}])[1]
    ))
    resp, status = unwrap_response(members_api.get_membership_events(DummyRequest(method="GET", args={"id": "mem-1"})))
    assert status == 200
    assert resp == [{"id": "evt-1"}]
    assert calls == ["mem-1"]


def test_get_membership_events_slug(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        get_by_id=lambda membership_id, slug=None: (calls.append((membership_id, slug)), _membership("mem-1"))[1],
        get_events=lambda membership_id: (calls.append(membership_id), [{"id": "evt-1"}])[1],
    ))
    resp, status = unwrap_response(members_api.get_membership_events(DummyRequest(method="GET", args={"slug": "slug-1"})))
    assert status == 200
    assert resp == [{"id": "evt-1"}]
    assert calls == [(None, "slug-1"), "mem-1"]


def test_set_membership_price_missing_fee(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(set_membership_price=lambda *args, **kwargs: calls.append((args, kwargs))))
    resp, status = unwrap_response(members_api.set_membership_price(DummyRequest(method="POST", json={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert calls == []


def test_set_membership_price_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        set_membership_price=lambda fee, year=None: (calls.append((fee, year)), MembershipPriceResponseDTO(year=str(year), price=fee))[1]
    ))
    resp, status = unwrap_response(members_api.set_membership_price(DummyRequest(method="POST", json={"membership_fee": 10, "year": "2026"})))
    assert status == 200
    assert resp["price"] == 10
    assert resp["year"] == "2026"
    assert calls == [(10.0, 2026)]


def test_get_membership_price_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        get_membership_price=lambda year=None: (calls.append(year), MembershipPriceResponseDTO(year=str(year), price=10))[1]
    ))
    resp, status = unwrap_response(members_api.get_membership_price(DummyRequest(method="GET", args={"year": "2026"})))
    assert status == 200
    assert resp["price"] == 10
    assert resp["year"] == "2026"
    assert calls == [2026]


def test_get_memberships_report_missing_event_id(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "membership_reports_service", types.SimpleNamespace(get_memberships_report=lambda **kwargs: calls.append(kwargs)))
    resp, status = unwrap_response(members_api.get_memberships_report(DummyRequest(method="GET", args={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert calls == []


def test_get_memberships_report_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "membership_reports_service", types.SimpleNamespace(
        get_memberships_report=lambda **kwargs: (calls.append(kwargs), {"event_id": kwargs["event_id"]})[1]
    ))
    resp, status = unwrap_response(members_api.get_memberships_report(DummyRequest(method="GET", args={"event_id": "evt-1"})))
    assert status == 200
    assert resp["event_id"] == "evt-1"
    assert calls == [{"event_id": "evt-1"}]


def test_set_membership_price_happy_path_legacy_scenario(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        set_membership_price=lambda fee, year=None: (calls.append((fee, year)), MembershipPriceResponseDTO(year=str(year), price=fee, message="saved"))[1]
    ))
    resp, status = unwrap_response(members_api.set_membership_price(DummyRequest(method="POST", json={"membership_fee": 20, "year": 2026})))
    assert status == 200
    assert resp["price"] == 20
    assert resp["message"] == "saved"
    assert calls == [(20.0, 2026)]


def test_get_membership_price_not_found(monkeypatch):
    calls = []
    def get_membership_price(year=None):
        calls.append(year)
        raise NotFoundError("missing")
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(get_membership_price=get_membership_price))
    resp, status = unwrap_response(members_api.get_membership_price(DummyRequest(method="GET", args={"year": "2026"})))
    assert status == 404
    assert resp["error"] == "missing"
    assert calls == [2026]


def test_get_memberships_report_missing_event():
    resp, status = unwrap_response(members_api.get_memberships_report(DummyRequest(method="GET", args={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"


def test_get_memberships_report_happy_path_legacy_scenario(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "membership_reports_service", types.SimpleNamespace(
        get_memberships_report=lambda **kwargs: (calls.append(kwargs), {"rows": []})[1]
    ))
    resp, status = unwrap_response(members_api.get_memberships_report(DummyRequest(method="GET", args={"event_id": "evt-1"})))
    assert status == 200
    assert resp == {"rows": []}
    assert calls == [{"event_id": "evt-1"}]


def test_create_wallet_pass_missing_membership_id(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(create_wallet_pass=lambda value: calls.append(value)))
    resp, status = unwrap_response(members_api.create_wallet_pass(DummyRequest(method="POST", json={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert calls == []


def test_create_wallet_pass_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        create_wallet_pass=lambda membership_id: (calls.append(membership_id), MembershipWalletPassResponseDTO(wallet_pass_id="pass-1", wallet_url="https://example.test/pass"))[1]
    ))
    resp, status = unwrap_response(members_api.create_wallet_pass(DummyRequest(method="POST", json={"membership_id": "mem-1"})))
    assert status == 200
    assert resp["wallet_pass_id"] == "pass-1"
    assert resp["wallet_url"] == "https://example.test/pass"
    assert calls == ["mem-1"]


def test_invalidate_wallet_pass_missing_membership_id(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(invalidate_wallet_pass=lambda value: calls.append(value)))
    resp, status = unwrap_response(members_api.invalidate_wallet_pass(DummyRequest(method="POST", json={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert calls == []


def test_invalidate_wallet_pass_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        invalidate_wallet_pass=lambda membership_id: (calls.append(membership_id), MembershipActionResponseDTO(message="invalidated", id=membership_id))[1]
    ))
    resp, status = unwrap_response(members_api.invalidate_wallet_pass(DummyRequest(method="POST", json={"membership_id": "mem-1"})))
    assert status == 200
    assert resp["id"] == "mem-1"
    assert calls == ["mem-1"]


def test_get_wallet_model_happy_path(monkeypatch):
    # The service also reads the saved model from Firestore; supply the production-shaped response at service boundary.
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(get_wallet_model=lambda: WalletModelResponseDTO(model_id="371225")))
    resp, status = unwrap_response(members_api.get_wallet_model(DummyRequest(method="GET")))
    assert status == 200
    assert resp["model_id"] == "371225"


def test_set_wallet_model_missing_model_id(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(set_wallet_model=lambda value: calls.append(value)))
    resp, status = unwrap_response(members_api.set_wallet_model(DummyRequest(method="POST", json={})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert calls == []


def test_set_wallet_model_happy_path(monkeypatch):
    calls = []
    monkeypatch.setattr(members_api, "memberships_service", types.SimpleNamespace(
        set_wallet_model=lambda model_id: (calls.append(model_id), WalletModelResponseDTO(model_id=model_id, message="updated"))[1]
    ))
    resp, status = unwrap_response(members_api.set_wallet_model(DummyRequest(method="POST", json={"model_id": "371225"})))
    assert status == 200
    assert resp == {"model_id": "371225", "message": "updated"}
    assert calls == ["371225"]
