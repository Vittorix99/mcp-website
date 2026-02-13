from dto import SettingDTO
from repositories.settings_repository import SettingsRepository
from services.service_errors import NotFoundError, ValidationError


class SettingsService:
    def __init__(self):
        self.settings_repository = SettingsRepository()

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
