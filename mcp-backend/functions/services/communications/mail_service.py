import logging
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple
from copy import deepcopy

from config.runtime_settings import ProviderMode, RuntimeConfigurationError, get_runtime_settings

from clients.mailersend_client import (
    MailerSendClient,
    MailerSendEmailBuilder,
    MailerSendRequest,
    MailerSendRoutes,
)
from services.core.error_logs_service import log_external_error
from utils.safe_logging import mask_email, redact_sensitive


# Backward-compatible symbol expected by existing tests.
EmailBuilder = MailerSendEmailBuilder

logger = logging.getLogger("MailService")


@dataclass
class MailConfig:
    api_key: str
    from_email: str
    from_name: Optional[str] = None
    reply_to: Optional[str] = None


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
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    category: Optional[str] = None  # memberships, location, events, communication...


def _get_env_any(*keys: str) -> Optional[str]:
    for key in keys:
        value = os.environ.get(key)
        if value:
            return value
    return None


def get_mail_config() -> MailConfig:
    api_key = _get_env_any("MAILERSEND_API_KEY", "MAILERSEND_TOKEN", "MAILER_SEND_API_KEY")
    from_email = _get_env_any("MAILERSEND_FROM_EMAIL", "USER_EMAIL", "GMAIL_MAIL")
    from_name = _get_env_any("MAILERSEND_FROM_NAME", "SENDER_NAME")
    reply_to = _get_env_any("MAILERSEND_REPLY_TO")

    if not api_key:
        raise ValueError("Missing MailerSend API key (MAILERSEND_API_KEY).")
    if not from_email:
        raise ValueError("Missing sender email (MAILERSEND_FROM_EMAIL or USER_EMAIL).")

    return MailConfig(
        api_key=api_key,
        from_email=from_email,
        from_name=from_name,
        reply_to=reply_to,
    )


def _encode_attachment(attachment: EmailAttachment) -> dict:
    raw_name = (attachment.filename or "").strip()
    safe_name = os.path.basename(raw_name) or "attachment.bin"
    temp_dir = tempfile.mkdtemp(prefix="mailersend_att_")
    temp_path = os.path.join(temp_dir, safe_name)
    with open(temp_path, "wb") as handle:
        handle.write(attachment.content)
    return {"path": temp_path, "temp_dir": temp_dir}


def _sender_for_category(category: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    if not category:
        return None, None, None
    key = category.upper()
    return (
        _get_env_any(f"MAILERSEND_FROM_EMAIL_{key}"),
        _get_env_any(f"MAILERSEND_FROM_NAME_{key}"),
        _get_env_any(f"MAILERSEND_REPLY_TO_{key}"),
    )


class MailService(ABC):
    @abstractmethod
    def send(self, email: EmailMessage) -> bool:
        raise NotImplementedError


class MailerSendMailService(MailService):
    def __init__(self, config: Optional[MailConfig] = None, allowed_recipients=None):
        self.config = config
        self.allowed_recipients = allowed_recipients

    def send(self, email: EmailMessage) -> bool:
        if self.allowed_recipients is not None:
            recipient = email.to_email.strip().lower()
            single_recipient = recipient.count("@") == 1 and not any(char in recipient for char in ",;\r\n")
            allowed = single_recipient and any(
                recipient == entry or (entry.startswith("@") and recipient.endswith(entry))
                for entry in self.allowed_recipients)
            if not allowed:
                logger.warning("Email recipient denied by staging allowlist")
                return False
        try:
            config = self.config or get_mail_config()
        except Exception as exc:
            logger.error("Unable to load MailerSend configuration: %s", redact_sensitive(str(exc)))
            log_external_error(
                service="MailerSend",
                operation="send_email",
                source="services.communications.mail_service.send",
                message=f"Unable to load MailerSend configuration: {exc}",
                status_code=0,
                context={"to_email": email.to_email, "subject": email.subject},
            )
            return False

        cat_from_email, cat_from_name, cat_reply_to = _sender_for_category(email.category)
        from_email = email.from_email or cat_from_email or config.from_email
        from_name = email.from_name or cat_from_name or config.from_name
        reply_to = email.reply_to or cat_reply_to or config.reply_to

        temp_files = []
        temp_dirs = []
        try:
            attachment_paths = []
            if email.attachment:
                encoded = _encode_attachment(email.attachment)
                temp_files.append(encoded["path"])
                temp_dirs.append(encoded["temp_dir"])
                attachment_paths.append(encoded["path"])

            route_request = MailerSendRequest(
                from_email=from_email,
                from_name=from_name,
                to_email=email.to_email,
                subject=email.subject,
                text_content=email.text_content or "",
                html_content=email.html_content,
                reply_to=reply_to,
                attachment_paths=attachment_paths,
            )
            result = MailerSendRoutes.send_email(
                request=route_request,
                api_key=config.api_key,
                client_cls=MailerSendClient,
                builder_cls=EmailBuilder,
            )

            if result.success:
                logger.info("Email sent successfully to %s", mask_email(email.to_email))
                return True

            payload_preview = str(redact_sensitive(result.payload or result.error_message or ""))[:500]
            logger.error(
                "MailerSend error status %s for %s: %s",
                result.status_code or "unknown",
                mask_email(email.to_email),
                payload_preview,
            )
            log_external_error(
                service="MailerSend",
                operation="send_email",
                source="services.communications.mail_service.send",
                message=result.error_message or "MailerSend error",
                status_code=result.status_code,
                payload=result.payload,
                context={"to_email": email.to_email, "subject": email.subject},
            )
            return False
        except Exception as exc:
            logger.error("Error sending email to %s: %s", mask_email(email.to_email), redact_sensitive(str(exc)))
            log_external_error(
                service="MailerSend",
                operation="send_email",
                source="services.communications.mail_service.send",
                message=str(exc),
                status_code=0,
                context={"to_email": email.to_email, "subject": email.subject},
            )
            return False
        finally:
            for path in temp_files:
                try:
                    os.unlink(path)
                except OSError:
                    pass
            for path in temp_dirs:
                try:
                    os.rmdir(path)
                except OSError:
                    pass


GmailMailService = MailerSendMailService


class FakeMailService(MailService):
    def __init__(self):
        self.sent_messages = []

    def send(self, email: EmailMessage) -> bool:
        self.sent_messages.append(deepcopy(email))
        return True


class DisabledMailService(MailService):
    def send(self, email: EmailMessage) -> bool:
        return False


def build_mail_service(settings=None) -> MailService:
    settings = settings or get_runtime_settings()
    provider = settings.providers
    if provider.mail == ProviderMode.FAKE:
        return FakeMailService()
    if provider.mail == ProviderMode.DISABLED:
        return DisabledMailService()
    if provider.mail not in {ProviderMode.STAGING, ProviderMode.LIVE}:
        raise RuntimeConfigurationError("Unsupported mail mode")
    if not provider.mail_api_key or not provider.mail_from_email:
        raise RuntimeConfigurationError("Mail requires MAILERSEND_API_KEY and MAILERSEND_FROM_EMAIL")
    config = MailConfig(api_key=provider.mail_api_key.get_secret_value(),
                        from_email=provider.mail_from_email, from_name=provider.mail_from_name)
    allowlist = provider.mail_allowed_recipients if provider.mail == ProviderMode.STAGING else None
    return MailerSendMailService(config, allowed_recipients=allowlist)

_mail_service: Optional[MailService] = None
_mail_config_logged = False


def _log_mail_config(config: MailConfig) -> None:
    logger.info(
        "Mail service configured: from_set=%s from_name_set=%s reply_to_set=%s api_key_set=%s",
        bool(config.from_email),
        bool(config.from_name),
        bool(config.reply_to),
        bool(config.api_key),
    )


def _log_mail_config_once() -> None:
    global _mail_config_logged
    if _mail_config_logged:
        return
    try:
        _log_mail_config(get_mail_config())
        _mail_config_logged = True
    except Exception as exc:
        logger.debug("Unable to log mail config: %s", redact_sensitive(str(exc)))


def init_mail_service(service: Optional[MailService] = None) -> MailService:
    global _mail_service
    _mail_service = service if service is not None else build_mail_service()
    _log_mail_config_once()
    return _mail_service


def get_mail_service() -> MailService:
    if _mail_service is None:
        init_mail_service()
    return _mail_service


class MailServiceProxy(MailService):
    def send(self, email: EmailMessage) -> bool:
        return get_mail_service().send(email)


mail_service = MailServiceProxy()
