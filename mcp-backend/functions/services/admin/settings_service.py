from config.firebase_config import db

class SettingsService:
    def __init__(self):
        self.collection = db.collection("settings")

    def get_setting(self, key):
        try:
            doc = self.collection.document(key).get()
            if doc.exists:
                return doc.to_dict().get("value")
            return None
        except Exception as e:
            raise Exception(f"[get_setting] Error fetching {key}: {str(e)}")

    def set_setting(self, key, value):
        try:
            self.collection.document(key).set({"value": value})
            return True
        except Exception as e:
            raise Exception(f"[set_setting] Error setting {key}: {str(e)}")

    def get_all_settings(self):
        try:
            settings = {}
            for doc in self.collection.stream():
                settings[doc.id] = doc.to_dict().get("value")
            return settings
        except Exception as e:
            raise Exception(f"[get_all_settings] Error fetching all settings: {str(e)}")