import pytest

from dto.setting_api import SetSettingRequestDTO
from errors.service_errors import NotFoundError, ValidationError


@pytest.mark.integration
def test_settings_service_set_get(settings_service, settings_repository, setting_key):
    """Sets and retrieves a setting via the service layer."""
    try:
        dto = SetSettingRequestDTO(key=setting_key, value="value-1")
        result = settings_service.set_setting(dto)
        assert result.setting.key == setting_key
        assert result.setting.value == "value-1"

        fetched = settings_service.get_setting(setting_key)
        assert fetched.key == setting_key
        assert fetched.value == "value-1"
    finally:
        settings_repository.collection.document(setting_key).delete()


@pytest.mark.integration
def test_settings_service_missing_key(settings_service):
    """Rejects missing key."""
    with pytest.raises(ValidationError):
        settings_service.get_setting("")


@pytest.mark.integration
def test_settings_service_not_found(settings_service):
    """Raises NotFoundError for missing setting."""
    with pytest.raises(NotFoundError):
        settings_service.get_setting("missing-key-xyz")
