import base64
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2 import service_account
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
    access_token: Optional[str] = None


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


def _split_scopes(raw_value: str) -> List[str]:
    if not raw_value:
        return []
    if "," in raw_value:
        parts = raw_value.split(",")
    else:
        parts = raw_value.split()
    return [scope.strip() for scope in parts if scope.strip()]


def _load_json_file(path: Optional[str]) -> Optional[dict]:
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, ValueError, OSError):
        return None


def _extract_oauth_client_info(payload: Optional[dict]) -> Optional[dict]:
    if not isinstance(payload, dict):
        return None
    section = payload.get("web") or payload.get("installed")
    if not isinstance(section, dict):
        return None
    return {
        "client_id": section.get("client_id"),
        "client_secret": section.get("client_secret"),
    }


def get_mail_config() -> MailConfig:
    service_file = (
        os.environ.get("SERVICE_MAIL_FILE")
        or os.environ.get("GMAIL_SERVICE_FILE_PATH")
    )
    service_payload = _load_json_file(service_file)
    oauth_client_info = _extract_oauth_client_info(service_payload)
    service_account_file = service_file if service_payload and service_payload.get("type") == "service_account" else None

    scopes = _split_scopes(
        os.environ.get("GMAIL_SCOPES", "")
        or os.environ.get("GOOGLE_MAIL_SCOPES", "")
        or os.environ.get("SCOPES", "")
    )
    return MailConfig(
        scopes=scopes,
        service_account_file=service_account_file,
        user_email=os.environ.get("USER_EMAIL", "") or os.environ.get("GMAIL_MAIL", ""),
        refresh_token=(
            os.environ.get("REFRESH_TOKEN", "")
            or os.environ.get("GOOGLE_MAIL_REFRESH_TOKEN", "")
            or os.environ.get("GMAIL_REFRESH_TOKEN", "")
        ),
        client_id=(
            os.environ.get("CLIENT_ID", "")
            or os.environ.get("GOOGLE_MAIL_CLIENT_ID", "")
            or os.environ.get("GMAIL_CLIENT_ID", "")
            or (oauth_client_info.get("client_id") if oauth_client_info else "")
        ),
        client_secret=(
            os.environ.get("CLIENT_SECRET", "")
            or os.environ.get("GOOGLE_MAIL_CLIENT_SECRET", "")
            or os.environ.get("GMAIL_CLIENT_SECRET", "")
            or (oauth_client_info.get("client_secret") if oauth_client_info else "")
        ),
        access_token=(
            os.environ.get("ACCESS_TOKEN", "")
            or os.environ.get("GOOGLE_MAIL_ACCESS_TOKEN", "")
            or os.environ.get("GMAIL_ACCESS_TOKEN", "")
        ),
    )


def _build_credentials(config: MailConfig) -> Credentials:
    if config.service_account_file:
        creds = service_account.Credentials.from_service_account_file(
            config.service_account_file,
            scopes=config.scopes or None,
        )
        if config.user_email:
            creds = creds.with_subject(config.user_email)
        return creds

    if not config.user_email or not config.refresh_token or not config.client_id or not config.client_secret:
        if config.access_token:
            return Credentials(token=config.access_token, scopes=config.scopes or None)
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


def _print_mail_config(config: MailConfig) -> None:
    service_file = os.environ.get("SERVICE_MAIL_FILE", "")
    gmail_service_file = os.environ.get("GMAIL_SERVICE_FILE_PATH", "")
    scopes_count = len(config.scopes)
    print(
        "Mail config: "
        f"user={config.user_email}, "
        f"scopes={scopes_count}, "
        f"service_file={service_file}, "
        f"gmail_service_file={gmail_service_file}"
    )


def init_mail_service(service: Optional[MailService] = None) -> MailService:
    global _mail_service
    _mail_service = service or GmailMailService()
    try:
        _print_mail_config(get_mail_config())
    except Exception as exc:
        logger.debug("Unable to print mail config: %s", exc)
    return _mail_service


def get_mail_service() -> MailService:
    if _mail_service is None:
        init_mail_service()
    return _mail_service


mail_service = get_mail_service()
