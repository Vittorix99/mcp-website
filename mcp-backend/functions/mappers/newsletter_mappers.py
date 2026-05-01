from __future__ import annotations

from dto.newsletter_api import (
    NewsletterConsentResponseDTO,
    NewsletterParticipantItemDTO,
    NewsletterSignupResponseDTO,
)
from models import NewsletterConsent, NewsletterParticipant, NewsletterSignup


def participant_item_to_model(item: NewsletterParticipantItemDTO, timestamp) -> NewsletterParticipant:
    payload = item.model_dump()
    email = str(payload.pop("email", "") or "")
    payload.pop("timestamp", None)
    return NewsletterParticipant(email=email, extra=payload, timestamp=timestamp)


def signup_to_response(signup: NewsletterSignup) -> NewsletterSignupResponseDTO:
    return NewsletterSignupResponseDTO(
        id=signup.id,
        email=signup.email,
        timestamp=signup.timestamp,
        active=signup.active,
        source=signup.source,
    )


def consent_to_response(consent: NewsletterConsent) -> NewsletterConsentResponseDTO:
    return NewsletterConsentResponseDTO(
        id=consent.id,
        name=consent.name,
        surname=consent.surname,
        email=consent.email,
        phone=consent.phone,
        birthdate=consent.birthdate,
        gender=consent.gender,
        gender_probability=consent.gender_probability,
        event_id=consent.event_id,
        participant_id=consent.participant_id,
        timestamp=consent.timestamp,
        source=consent.source,
        active=consent.active,
    )
