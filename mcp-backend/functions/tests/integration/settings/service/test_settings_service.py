import pytest

from services.service_errors import NotFoundError, ValidationError


@pytest.mark.integration
def test_settings_service_set_get(settings_service, settings_repository, setting_key):
    """Sets and retrieves a setting via the service layer."""
    try:
        dto = settings_service.set_setting(setting_key, "value-1")
        assert dto.key == setting_key
        assert dto.value == "value-1"

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
