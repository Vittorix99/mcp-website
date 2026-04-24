from typing import Optional

from dto import SettingDTO
from interfaces.repositories import SettingsRepositoryProtocol
from repositories.settings_repository import SettingsRepository
from errors.service_errors import NotFoundError, ValidationError


class SettingsService:
    def __init__(self, settings_repository: Optional[SettingsRepositoryProtocol] = None):
        self.settings_repository = settings_repository or SettingsRepository()

    def get_setting(self, key):
        if not key:
            raise ValidationError("Missing key")
        setting = self.settings_repository.get_dto(key)
        if not setting:
            raise NotFoundError("Setting not found")
        return setting

    def set_setting(self, key, value):
        if not key:
            raise ValidationError("Missing key")
        if value is None:
            raise ValidationError("Missing value")
        setting = self.settings_repository.save(key, value)
        return SettingDTO.from_model(setting)

    def get_all_settings(self):
        return self.settings_repository.list_dtos()
