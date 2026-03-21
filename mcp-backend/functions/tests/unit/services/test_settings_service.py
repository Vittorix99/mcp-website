import pytest

from dto import SettingDTO
from models import Setting
from services.core.settings_service import SettingsService
from errors.service_errors import NotFoundError, ValidationError


class _DummySettingsRepo:
    def __init__(self):
        self.by_key = {}
        self.saved = []
        self.listed = []

    def get_dto(self, key):
        return self.by_key.get(key)

    def save(self, key, value):
        setting = Setting(key=key, value=value)
        self.saved.append(setting)
        return setting

    def list_dtos(self):
        return self.listed


def _make_service():
    service = SettingsService()
    service.settings_repository = _DummySettingsRepo()
    return service


def test_get_setting_requires_key():
    """Rejects missing key."""
    service = _make_service()
    with pytest.raises(ValidationError):
        service.get_setting("")


def test_get_setting_not_found():
    """Raises when setting does not exist."""
    service = _make_service()
    with pytest.raises(NotFoundError):
        service.get_setting("missing")


def test_get_setting_success():
    """Returns setting DTO."""
    service = _make_service()
    service.settings_repository.by_key["key"] = SettingDTO(key="key", value=1)
    setting = service.get_setting("key")
    assert setting.key == "key"
    assert setting.value == 1


def test_set_setting_requires_key():
    """Rejects missing key."""
    service = _make_service()
    with pytest.raises(ValidationError):
        service.set_setting("", 1)


def test_set_setting_requires_value():
    """Rejects missing value."""
    service = _make_service()
    with pytest.raises(ValidationError):
        service.set_setting("key", None)


def test_set_setting_success():
    """Saves and returns setting."""
    service = _make_service()
    setting = service.set_setting("key", 2)
    assert setting.key == "key"
    assert setting.value == 2


def test_get_all_settings():
    """Returns all settings."""
    service = _make_service()
    service.settings_repository.listed = [SettingDTO(key="k", value=1)]
    settings = service.get_all_settings()
    assert settings[0].key == "k"
