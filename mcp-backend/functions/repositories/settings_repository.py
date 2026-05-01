from typing import List, Optional

from models import Setting
from repositories.base import BaseRepository


class SettingsRepository(BaseRepository[Setting]):
    def __init__(self):
        super().__init__("settings", Setting)

    def get(self, key: str) -> Optional[Setting]:
        if not key:
            return None
        doc = self.collection.document(key).get()
        if not doc.exists:
            return None
        return self._model_from_snapshot(doc)

    def list(self) -> List[Setting]:
        return [self._model_from_snapshot(doc) for doc in self.collection.stream()]

    def save(self, key: str, value) -> Setting:
        setting = Setting(key=key, value=value)
        self.collection.document(key).set(setting.to_firestore())
        return setting
