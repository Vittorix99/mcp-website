import pytest
from pydantic import ValidationError as PydanticValidationError

from dto.setting_api import SetSettingRequestDTO
from models import Setting
from services.core.settings_service import SettingsService
from errors.service_errors import NotFoundError, ValidationError


class _DummySettingsRepo:
    def __init__(self):
        self.by_key = {}
        self.saved = []
        self.listed = []

    def get(self, key):
        return self.by_key.get(key)

    def save(self, key, value):
        setting = Setting(key=key, value=value)
        self.saved.append(setting)
        return setting

    def list(self):
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
    service.settings_repository.by_key["key"] = Setting(key="key", value=1)
    setting = service.get_setting("key")
    assert setting.key == "key"
    assert setting.value == 1


def test_set_setting_requires_key():
    """Rejects missing key."""
    with pytest.raises(PydanticValidationError):
        SetSettingRequestDTO(key="", value=1)


def test_set_setting_requires_value():
    """Rejects missing value."""
    with pytest.raises(PydanticValidationError):
        SetSettingRequestDTO.model_validate({"key": "key"})


def test_set_setting_success():
    """Saves and returns setting."""
    service = _make_service()
    response = service.set_setting(SetSettingRequestDTO(key="key", value=2))
    assert response.setting.key == "key"
    assert response.setting.value == 2


def test_get_all_settings():
    """Returns all settings."""
    service = _make_service()
    service.settings_repository.listed = [Setting(key="k", value=1)]
    response = service.get_all_settings()
    assert response.settings[0].key == "k"
