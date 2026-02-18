import types

from api.admin import setting_api
from services.service_errors import NotFoundError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def test_get_settings_with_key(monkeypatch):
    """Returns a single setting by key."""
    monkeypatch.setattr(
        setting_api,
        "settings_service",
        types.SimpleNamespace(
            get_setting=lambda key: types.SimpleNamespace(to_payload=lambda: {"key": key, "value": 1})
        ),
    )
    req = DummyRequest(method="GET", args={"key": "theme"})
    resp, status = unwrap_response(setting_api.get_settings(req))
    assert status == 200
    assert resp["key"] == "theme"


def test_get_settings_all(monkeypatch):
    """Returns all settings."""
    monkeypatch.setattr(
        setting_api,
        "settings_service",
        types.SimpleNamespace(
            get_all_settings=lambda: [
                types.SimpleNamespace(to_payload=lambda: {"key": "k", "value": 1})
            ]
        ),
    )
    req = DummyRequest(method="GET", args={})
    resp, status = unwrap_response(setting_api.get_settings(req))
    assert status == 200
    assert resp["settings"] == [{"key": "k", "value": 1}]


def test_get_settings_not_found(monkeypatch):
    """Maps not found errors to 404."""
    monkeypatch.setattr(
        setting_api,
        "settings_service",
        types.SimpleNamespace(get_setting=lambda key: (_ for _ in ()).throw(NotFoundError("missing"))),
    )
    req = DummyRequest(method="GET", args={"key": "missing"})
    resp, status = unwrap_response(setting_api.get_settings(req))
    assert status == 404
    assert resp["error"] == "missing"


def test_set_settings_validation_error(monkeypatch):
    """Maps validation errors to 400."""
    monkeypatch.setattr(
        setting_api,
        "settings_service",
        types.SimpleNamespace(set_setting=lambda key, value: (_ for _ in ()).throw(ValidationError("bad"))),
    )
    req = DummyRequest(method="POST", json={"key": "", "value": None})
    resp, status = unwrap_response(setting_api.set_settings(req))
    assert status == 400
    assert resp["error"] == "bad"


def test_set_settings_happy_path(monkeypatch):
    """Updates a setting successfully."""
    monkeypatch.setattr(
        setting_api,
        "settings_service",
        types.SimpleNamespace(
            set_setting=lambda key, value: types.SimpleNamespace(
                to_payload=lambda: {"key": key, "value": value}
            )
        ),
    )
    req = DummyRequest(method="POST", json={"key": "theme", "value": "dark"})
    resp, status = unwrap_response(setting_api.set_settings(req))
    assert status == 200
    assert resp["setting"]["key"] == "theme"
