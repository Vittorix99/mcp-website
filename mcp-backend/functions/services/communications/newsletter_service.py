from __future__ import annotations

import logging
import os
from typing import Optional

from firebase_admin import firestore

from models import NewsletterSignup
from dto.newsletter_api import (
    NewsletterActionResponseDTO,
    NewsletterConsentsListResponseDTO,
    NewsletterParticipantsRequestDTO,
    NewsletterSignupEnvelopeResponseDTO,
    NewsletterSignupRequestDTO,
    NewsletterSignupsListResponseDTO,
    NewsletterUpdateRequestDTO,
)
from errors.service_errors import NotFoundError
from interfaces.repositories import NewsletterRepositoryProtocol
from mappers.newsletter_mappers import consent_to_response, participant_item_to_model, signup_to_response
from repositories.newsletter_repository import NewsletterRepository
from services.communications.mail_service import EmailMessage, MailService, mail_service
from utils.templates_mail import get_newsletter_signup_template, get_newsletter_signup_text
from utils.safe_logging import mask_email, redact_sensitive

logger = logging.getLogger("NewsletterService")


class NewsletterService:
    def __init__(
        self,
        newsletter_repository: Optional[NewsletterRepositoryProtocol] = None,
        mail_service_instance: Optional[MailService] = None,
    ):
        self.newsletter_repository = newsletter_repository or NewsletterRepository()
        self.mail_service = mail_service_instance or mail_service

    def signup(self, dto: NewsletterSignupRequestDTO) -> NewsletterActionResponseDTO:
        existing = self.newsletter_repository.find_signup_by_email(dto.email)
        if not existing:
            signup = NewsletterSignup(email=dto.email, timestamp=firestore.SERVER_TIMESTAMP)
            self.newsletter_repository.add_signup_from_model(signup)
            logger.info("New newsletter signup: %s", mask_email(dto.email))

        self._send_welcome_email(dto.email)
        return NewsletterActionResponseDTO(message="Signed up for newsletter successfully")

    def _send_welcome_email(self, email: str) -> None:
        try:
            logo_url = "https://musiconnectingpeople.com/logonew.png"
            instagram_url = os.environ.get("INSTAGRAM_URL")
            html = get_newsletter_signup_template(email, logo_url, instagram_url)
            text = get_newsletter_signup_text(email)
            self.mail_service.send(
                EmailMessage(
                    to_email=email,
                    subject="Welcome to MCP Newsletter!",
                    text_content=text,
                    html_content=html,
                )
            )
            logger.info("Newsletter welcome email sent to %s", mask_email(email))
        except Exception as exc:
            logger.error("[NewsletterService] Welcome email failed for %s: %s", mask_email(email), redact_sensitive(str(exc)))

    def get_signup_by_id(self, signup_id: str) -> NewsletterSignupEnvelopeResponseDTO:
        signup = self.newsletter_repository.get_signup(signup_id)
        if not signup:
            raise NotFoundError("Newsletter signup not found")
        return NewsletterSignupEnvelopeResponseDTO(signup=signup_to_response(signup))

    def get_all_signups(self) -> NewsletterSignupsListResponseDTO:
        signups = [signup_to_response(s) for s in self.newsletter_repository.stream_signups()]
        return NewsletterSignupsListResponseDTO(signups=signups)

    def get_all_consents(self) -> NewsletterConsentsListResponseDTO:
        consents = [consent_to_response(c) for c in self.newsletter_repository.stream_consents()]
        return NewsletterConsentsListResponseDTO(consents=consents)

    def update_signup(self, dto: NewsletterUpdateRequestDTO) -> NewsletterActionResponseDTO:
        signup = self.newsletter_repository.get_signup(dto.id)
        if not signup:
            raise NotFoundError("Newsletter signup not found")
        signup.active = dto.active
        self.newsletter_repository.update_signup_from_model(dto.id, signup)
        logger.info("Newsletter signup %s updated (active=%s)", dto.id, dto.active)
        return NewsletterActionResponseDTO(message="Newsletter signup updated successfully")

    def delete_signup(self, signup_id: str) -> NewsletterActionResponseDTO:
        signup = self.newsletter_repository.get_signup(signup_id)
        if not signup:
            raise NotFoundError("Newsletter signup not found")
        self.newsletter_repository.delete_signup(signup_id)
        logger.info("Newsletter signup %s deleted", signup_id)
        return NewsletterActionResponseDTO(message="Newsletter signup deleted successfully")

    def add_participants(self, dto: NewsletterParticipantsRequestDTO) -> NewsletterActionResponseDTO:
        participants = [
            participant_item_to_model(p, firestore.SERVER_TIMESTAMP)
            for p in dto.participants
        ]
        self.newsletter_repository.add_participants_batch(participants)
        logger.info("Added %d participants to newsletter_participants", len(participants))
        return NewsletterActionResponseDTO(message="Participants added successfully")
