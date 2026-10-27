import types

from api.admin import setting_api
from dto.setting_api import (
    SetSettingResponseDTO,
    SettingResponseDTO,
    SettingsListResponseDTO,
)
from errors.service_errors import NotFoundError, ValidationError
from tests.utils import DummyRequest, unwrap_response


def test_get_settings_with_key(monkeypatch):
    captured = {}

    def get_setting(key):
        captured["key"] = key
        return SettingResponseDTO(key=key, value=1)

    monkeypatch.setattr(setting_api, "settings_service", types.SimpleNamespace(get_setting=get_setting))
    resp, status = unwrap_response(setting_api.get_settings(DummyRequest(method="GET", args={"key": "theme"})))
    assert status == 200
    assert resp["key"] == "theme"
    assert captured["key"] == "theme"


def test_get_settings_all(monkeypatch):
    monkeypatch.setattr(
        setting_api,
        "settings_service",
        types.SimpleNamespace(get_all_settings=lambda: SettingsListResponseDTO(settings=[SettingResponseDTO(key="k", value=1)])),
    )
    resp, status = unwrap_response(setting_api.get_settings(DummyRequest(method="GET", args={})))
    assert status == 200
    assert resp["settings"] == [{"key": "k", "value": 1}]


def test_get_settings_not_found(monkeypatch):
    def get_setting(_key):
        raise NotFoundError("missing")

    monkeypatch.setattr(setting_api, "settings_service", types.SimpleNamespace(get_setting=get_setting))
    resp, status = unwrap_response(setting_api.get_settings(DummyRequest(method="GET", args={"key": "missing"})))
    assert status == 404
    assert resp["error"] == "missing"


def test_set_settings_service_validation_error(monkeypatch):
    def set_setting(_dto):
        raise ValidationError("bad")

    monkeypatch.setattr(setting_api, "settings_service", types.SimpleNamespace(set_setting=set_setting))
    req = DummyRequest(method="POST", json={"key": "theme", "value": "invalid-for-service"})
    resp, status = unwrap_response(setting_api.set_settings(req))
    assert status == 400
    assert resp["error"] == "bad"


def test_set_settings_invalid_schema_does_not_call_service(monkeypatch):
    called = False

    def set_setting(_dto):
        nonlocal called
        called = True

    monkeypatch.setattr(setting_api, "settings_service", types.SimpleNamespace(set_setting=set_setting))
    resp, status = unwrap_response(setting_api.set_settings(DummyRequest(method="POST", json={"key": ""})))
    assert status == 400
    assert resp["error"] == "Invalid request data"
    assert called is False


def test_set_settings_happy_path(monkeypatch):
    captured = {}

    def set_setting(dto):
        captured["dto"] = dto
        setting = SettingResponseDTO(key=dto.key, value=dto.value)
        return SetSettingResponseDTO(message="updated", setting=setting)

    monkeypatch.setattr(setting_api, "settings_service", types.SimpleNamespace(set_setting=set_setting))
    req = DummyRequest(method="POST", json={"key": "theme", "value": "dark"})
    resp, status = unwrap_response(setting_api.set_settings(req))
    assert status == 200
    assert resp["setting"]["key"] == "theme"
    assert captured["dto"].key == "theme"
    assert captured["dto"].value == "dark"
