from uuid import uuid4

import pytest

from repositories.settings_repository import SettingsRepository
from services.core.settings_service import SettingsService


@pytest.fixture
def settings_service():
    return SettingsService()


@pytest.fixture
def settings_repository():
    return SettingsRepository()


@pytest.fixture
def setting_key():
    return f"integration_setting_{uuid4().hex[:8]}"
