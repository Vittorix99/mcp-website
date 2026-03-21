from typing import List, Optional

from dto import SettingDTO
from models import Setting
from repositories.base import BaseRepository


class SettingsRepository(BaseRepository[Setting, SettingDTO]):
    def __init__(self):
        super().__init__("settings", Setting, SettingDTO)

    def get_model(self, key: str) -> Optional[Setting]:
        if not key:
            return None
        doc = self.collection.document(key).get()
        if not doc.exists:
            return None
        return self._model_from_snapshot(doc)

    def get_dto(self, key: str) -> Optional[SettingDTO]:
        model = self.get_model(key)
        if not model:
            return None
        return SettingDTO.from_model(model)

    def list_models(self) -> List[Setting]:
        return [self._model_from_snapshot(doc) for doc in self.collection.stream()]

    def list_dtos(self) -> List[SettingDTO]:
        return [SettingDTO.from_model(model) for model in self.list_models()]

    def save(self, key: str, value) -> Setting:
        setting = Setting(key=key, value=value)
        self.collection.document(key).set(setting.to_firestore())
        return setting
