"""Unit tests for admin radio seasons API handlers."""
import types

import pytest

from api.admin import radio_seasons_api
from dto.radio.radio_season_dto import RadioSeasonResponseDTO
from errors.service_errors import RadioSeasonNotFoundError, ServiceError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def _season_dto(id_="s1", name="Summer 2026", year=2026):
    return RadioSeasonResponseDTO(id=id_, name=name, year=year)


# ---------------------------------------------------------------------------
# GET /admin/radio/seasons (list)
# ---------------------------------------------------------------------------

def test_get_seasons_happy_path(monkeypatch):
    monkeypatch.setattr(
        radio_seasons_api,
        "season_service",
        types.SimpleNamespace(get_all=lambda: [_season_dto()]),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(radio_seasons_api.admin_get_radio_seasons(req))

    assert status == 200
    assert isinstance(resp, list)
    assert resp[0]["id"] == "s1"


def test_get_seasons_service_error(monkeypatch):
    monkeypatch.setattr(
        radio_seasons_api,
        "season_service",
        types.SimpleNamespace(get_all=lambda: (_ for _ in ()).throw(ServiceError("boom"))),
    )
    req = DummyRequest(method="GET")
    resp, status = unwrap_response(radio_seasons_api.admin_get_radio_seasons(req))

    assert status == 500


# ---------------------------------------------------------------------------
# POST /admin/radio/seasons (create)
# ---------------------------------------------------------------------------

def test_create_season_happy_path(monkeypatch):
    monkeypatch.setattr(
        radio_seasons_api,
        "season_service",
        types.SimpleNamespace(create=lambda dto: _season_dto()),
    )
    req = DummyRequest(method="POST", json={"name": "Summer 2026", "year": 2026})
    resp, status = unwrap_response(radio_seasons_api.admin_create_radio_season(req))

    assert status == 201
    assert resp["name"] == "Summer 2026"


def test_create_season_missing_body():
    req = DummyRequest(method="POST", json=None)
    resp, status = unwrap_response(radio_seasons_api.admin_create_radio_season(req))

    assert status == 400
    assert resp["error"] == "Invalid request data"


def test_create_season_missing_name():
    req = DummyRequest(method="POST", json={"year": 2026})
    resp, status = unwrap_response(radio_seasons_api.admin_create_radio_season(req))

    assert status == 400


def test_create_season_wrong_method():
    req = DummyRequest(method="GET", json={"name": "X", "year": 2026})
    resp, status = unwrap_response(radio_seasons_api.admin_create_radio_season(req))

    assert status == 405


# ---------------------------------------------------------------------------
# GET /admin/radio/seasons?id=xxx (get by id)
# ---------------------------------------------------------------------------

def test_get_season_happy_path(monkeypatch):
    monkeypatch.setattr(
        radio_seasons_api,
        "season_service",
        types.SimpleNamespace(get_by_id=lambda id_: _season_dto(id_=id_)),
    )
    req = DummyRequest(method="GET", args={"id": "s1"})
    resp, status = unwrap_response(radio_seasons_api.admin_get_radio_season(req))

    assert status == 200
    assert resp["id"] == "s1"


def test_get_season_missing_id():
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(radio_seasons_api.admin_get_radio_season(req))

    assert status == 400
    assert "id" in resp["error"].lower() or resp["error"]


def test_get_season_not_found(monkeypatch):
    monkeypatch.setattr(
        radio_seasons_api,
        "season_service",
        types.SimpleNamespace(get_by_id=lambda id_: (_ for _ in ()).throw(RadioSeasonNotFoundError("missing"))),
    )
    req = DummyRequest(method="GET", args={"id": "ghost"})
    resp, status = unwrap_response(radio_seasons_api.admin_get_radio_season(req))

    assert status == 404


# ---------------------------------------------------------------------------
# PUT /admin/radio/seasons (update)
# ---------------------------------------------------------------------------

def test_update_season_happy_path(monkeypatch):
    monkeypatch.setattr(
        radio_seasons_api,
        "season_service",
        types.SimpleNamespace(update=lambda dto: _season_dto(name="Updated")),
    )
    req = DummyRequest(method="PUT", json={"id": "s1", "name": "Updated"})
    resp, status = unwrap_response(radio_seasons_api.admin_update_radio_season(req))

    assert status == 200
    assert resp["name"] == "Updated"


def test_update_season_missing_id():
    req = DummyRequest(method="PUT", json={"name": "No ID"})
    resp, status = unwrap_response(radio_seasons_api.admin_update_radio_season(req))

    assert status == 400


def test_update_season_not_found(monkeypatch):
    monkeypatch.setattr(
        radio_seasons_api,
        "season_service",
        types.SimpleNamespace(update=lambda dto: (_ for _ in ()).throw(RadioSeasonNotFoundError("gone"))),
    )
    req = DummyRequest(method="PUT", json={"id": "ghost", "name": "X"})
    resp, status = unwrap_response(radio_seasons_api.admin_update_radio_season(req))

    assert status == 404


# ---------------------------------------------------------------------------
# DELETE /admin/radio/seasons
# ---------------------------------------------------------------------------

def test_delete_season_happy_path(monkeypatch):
    monkeypatch.setattr(
        radio_seasons_api,
        "season_service",
        types.SimpleNamespace(delete=lambda id_: None),
    )
    req = DummyRequest(method="DELETE", json={"id": "s1"})
    resp, status = unwrap_response(radio_seasons_api.admin_delete_radio_season(req))

    assert status == 200
    assert resp["message"] == "Radio season deleted"


def test_delete_season_missing_id():
    req = DummyRequest(method="DELETE", json={})
    resp, status = unwrap_response(radio_seasons_api.admin_delete_radio_season(req))

    assert status == 400


def test_delete_season_not_found(monkeypatch):
    monkeypatch.setattr(
        radio_seasons_api,
        "season_service",
        types.SimpleNamespace(delete=lambda id_: (_ for _ in ()).throw(RadioSeasonNotFoundError("gone"))),
    )
    req = DummyRequest(method="DELETE", json={"id": "ghost"})
    resp, status = unwrap_response(radio_seasons_api.admin_delete_radio_season(req))

    assert status == 404
