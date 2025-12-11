from typing import Dict, Iterable, List, Optional, Union

from config.firebase_config import db
from dto import NewsletterConsentDTO, NewsletterSignupDTO
from models import NewsletterConsent, NewsletterSignup


class NewsletterRepository:
    def __init__(self):
        self.signup_collection = db.collection("newsletter_signups")
        self.consents_collection = db.collection("newsletter_consents")

    def list_signups(self) -> List[NewsletterSignupDTO]:
        return [
            NewsletterSignupDTO.from_model(
                NewsletterSignup.from_firestore(doc.to_dict() or {}, doc.id)
            )
            for doc in self.signup_collection.stream()
        ]

    def list_consents(self) -> List[NewsletterConsentDTO]:
        return [
            NewsletterConsentDTO.from_model(
                NewsletterConsent.from_firestore(doc.to_dict() or {}, doc.id)
            )
            for doc in self.consents_collection.stream()
        ]

    def add_signup(self, payload: Union[Dict[str, Optional[str]], NewsletterSignupDTO]) -> str:
        data = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self.signup_collection.add(data)[1].id

    def add_consent(self, payload: Union[Dict[str, Optional[str]], NewsletterConsentDTO]) -> str:
        data = payload.to_payload() if hasattr(payload, "to_payload") else payload
        return self.consents_collection.add(data)[1].id
