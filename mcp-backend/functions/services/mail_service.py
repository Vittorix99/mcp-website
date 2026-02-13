import base64
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config.external_services import GMAIL_TOKEN_URL


logger = logging.getLogger("MailService")


@dataclass
class MailConfig:
    scopes: List[str]
    user_email: str
    refresh_token: str
    client_id: str
    client_secret: str
    service_account_file: Optional[str] = None


@dataclass
class EmailAttachment:
    content: bytes
    filename: str


@dataclass
class EmailMessage:
    to_email: str
    subject: str
    text_content: str
    html_content: Optional[str] = None
    attachment: Optional[EmailAttachment] = None


def get_mail_config() -> MailConfig:
    scopes = [scope for scope in os.environ.get("SCOPES", "").split(",") if scope]
    return MailConfig(
        scopes=scopes,
        service_account_file=os.environ.get("SERVICE_MAIL_FILE"),
        user_email=os.environ.get("USER_EMAIL", ""),
        refresh_token=os.environ.get("REFRESH_TOKEN", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", ""),
    )


def _build_credentials(config: MailConfig) -> Credentials:
    if not config.user_email or not config.refresh_token or not config.client_id or not config.client_secret:
        raise ValueError("Missing Gmail configuration values")
    creds = Credentials(
        None,
        refresh_token=config.refresh_token,
        client_id=config.client_id,
        client_secret=config.client_secret,
        token_uri=GMAIL_TOKEN_URL,
        scopes=config.scopes or None,
    )
    if creds.expired or not creds.valid:
        creds.refresh(Request())
    return creds


def _build_gmail_service(config: MailConfig):
    creds = _build_credentials(config)
    return build("gmail", "v1", credentials=creds)


def _encode_message(message: MIMEText) -> str:
    return base64.urlsafe_b64encode(message.as_bytes()).decode()


def _build_plain_message(email: EmailMessage, from_email: str) -> MIMEText:
    message = MIMEText(email.text_content)
    message["to"] = email.to_email
    message["from"] = from_email
    message["subject"] = email.subject
    return message


def _build_multipart_message(email: EmailMessage, from_email: str) -> MIMEMultipart:
    message = MIMEMultipart("mixed")
    message["to"] = email.to_email
    message["from"] = from_email
    message["subject"] = email.subject

    msg_alternative = MIMEMultipart("alternative")
    message.attach(msg_alternative)

    msg_alternative.attach(MIMEText(email.text_content, "plain"))
    if email.html_content:
        msg_alternative.attach(MIMEText(email.html_content, "html"))

    if email.attachment:
        part_pdf = MIMEApplication(email.attachment.content, Name=email.attachment.filename)
        part_pdf["Content-Disposition"] = f'attachment; filename="{email.attachment.filename}"'
        message.attach(part_pdf)

    return message


def _send_email_message(service, raw_message: str) -> bool:
    service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
    return True


class MailService(ABC):
    @abstractmethod
    def send(self, email: EmailMessage) -> bool:
        raise NotImplementedError


class GmailMailService(MailService):
    def send(self, email: EmailMessage) -> bool:
        try:
            config = get_mail_config()
            service = _build_gmail_service(config)

            if email.html_content or email.attachment:
                message = _build_multipart_message(email, config.user_email)
            else:
                message = _build_plain_message(email, config.user_email)

            raw_message = _encode_message(message)
            _send_email_message(service, raw_message)
            logger.info("Email sent successfully to %s", email.to_email)
            return True
        except Exception as exc:
            logger.exception("Error sending email to %s: %s", email.to_email, exc)
            return False


_mail_service: Optional[MailService] = None


def init_mail_service(service: Optional[MailService] = None) -> MailService:
    global _mail_service
    _mail_service = service or GmailMailService()
    return _mail_service


def get_mail_service() -> MailService:
    if _mail_service is None:
        init_mail_service()
    return _mail_service


mail_service = get_mail_service()
