from typing import Optional

from dto.setting_api import (
    SetSettingRequestDTO,
    SetSettingResponseDTO,
    SettingResponseDTO,
    SettingsListResponseDTO,
)
from errors.service_errors import NotFoundError, ValidationError
from interfaces.repositories import SettingsRepositoryProtocol
from repositories.settings_repository import SettingsRepository


class SettingsService:
    def __init__(self, settings_repository: Optional[SettingsRepositoryProtocol] = None):
        self.settings_repository = settings_repository or SettingsRepository()

    def get_setting(self, key: str) -> SettingResponseDTO:
        if not key:
            raise ValidationError("Missing key")
        setting = self.settings_repository.get(key)
        if not setting:
            raise NotFoundError("Setting not found")
        return SettingResponseDTO(key=setting.key, value=setting.value)

    def get_all_settings(self) -> SettingsListResponseDTO:
        settings = self.settings_repository.list()
        return SettingsListResponseDTO(
            settings=[SettingResponseDTO(key=s.key, value=s.value) for s in settings]
        )

    def set_setting(self, dto: SetSettingRequestDTO) -> SetSettingResponseDTO:
        setting = self.settings_repository.save(dto.key, dto.value)
        return SetSettingResponseDTO(
            message=f"Setting '{dto.key}' updated",
            setting=SettingResponseDTO(key=setting.key, value=setting.value),
        )
