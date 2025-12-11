from config.firebase_config import db
from models.settings import Setting


class SettingsService:
    def __init__(self):
        self.collection = db.collection("settings")

    def get_setting(self, key):
        try:
            doc = self.collection.document(key).get()
            if not doc.exists:
                return None
            return Setting.from_firestore(doc.to_dict() or {}, doc_id=doc.id)
        except Exception as e:
            raise Exception(f"[get_setting] Error fetching {key}: {str(e)}")

    def set_setting(self, key, value):
        try:
            setting = Setting(key=key, value=value)
            self.collection.document(key).set(setting.to_firestore())
            return setting
        except Exception as e:
            raise Exception(f"[set_setting] Error setting {key}: {str(e)}")

    def get_all_settings(self):
        try:
            entries = []
            for doc in self.collection.stream():
                entries.append(Setting.from_firestore(doc.to_dict() or {}, doc_id=doc.id))
            return entries
        except Exception as e:
            raise Exception(f"[get_all_settings] Error fetching all settings: {str(e)}")
