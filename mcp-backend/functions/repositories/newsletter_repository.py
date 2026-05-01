from __future__ import annotations

from typing import Iterable, List, Optional

from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter

from config.firebase_config import db
from models import NewsletterConsent, NewsletterParticipant, NewsletterSignup


class NewsletterRepository:
    def __init__(self):
        self.signup_collection = db.collection("newsletter_signups")
        self.consents_collection = db.collection("newsletter_consents")
        self.participants_collection = db.collection("newsletter_participants")

    def _signup_from_snapshot(self, snapshot) -> NewsletterSignup:
        return NewsletterSignup.from_firestore(snapshot.to_dict() or {}, snapshot.id)

    def _consent_from_snapshot(self, snapshot) -> NewsletterConsent:
        return NewsletterConsent.from_firestore(snapshot.to_dict() or {}, snapshot.id)

    def stream_signups(self) -> Iterable[NewsletterSignup]:
        for doc in self.signup_collection.order_by("timestamp").stream():
            yield self._signup_from_snapshot(doc)

    def stream_consents(self) -> Iterable[NewsletterConsent]:
        for doc in self.consents_collection.order_by("timestamp").stream():
            yield self._consent_from_snapshot(doc)

    def get_signup(self, signup_id: str) -> Optional[NewsletterSignup]:
        doc = self.signup_collection.document(signup_id).get()
        if not doc.exists:
            return None
        return self._signup_from_snapshot(doc)

    def find_signup_by_email(self, email: str) -> Optional[NewsletterSignup]:
        matches = (
            self.signup_collection
            .where(filter=FieldFilter("email", "==", email))
            .limit(1)
            .get()
        )
        if not matches:
            return None
        return self._signup_from_snapshot(matches[0])

    def add_signup_from_model(self, signup: NewsletterSignup) -> str:
        ref = self.signup_collection.document()
        ref.set(signup.to_firestore(include_none=True))
        return ref.id

    def update_signup_from_model(self, signup_id: str, signup: NewsletterSignup) -> None:
        self.signup_collection.document(signup_id).set(
            signup.to_firestore(include_none=True), merge=True
        )

    def delete_signup(self, signup_id: str) -> None:
        self.signup_collection.document(signup_id).delete()

    def unsubscribe_by_email(self, email: str) -> None:
        for doc in self.signup_collection.where(filter=FieldFilter("email", "==", email)).stream():
            doc.reference.update({"active": False})
        for doc in self.consents_collection.where(filter=FieldFilter("email", "==", email)).stream():
            doc.reference.update({"active": False})

    def add_participants_batch(self, participants: List[NewsletterParticipant]) -> None:
        batch = db.batch()
        for participant in participants:
            doc_ref = self.participants_collection.document()
            batch.set(doc_ref, participant.to_firestore(include_none=True))
        batch.commit()
