import logging
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple

import requests

try:
    from mailersend import MailerSendClient, EmailBuilder
except ImportError:  # Fallback shim if SDK not installed (e.g., offline emulator)
    class EmailBuilder:
        def __init__(self):
            self._data = {}

        def from_email(self, email: str, name: Optional[str] = None):
            self._data["from"] = {"email": email}
            if name:
                self._data["from"]["name"] = name
            return self

        def to_many(self, recipients):
            self._data["to"] = recipients
            return self

        def subject(self, subject: str):
            self._data["subject"] = subject
            return self

        def html(self, html: str):
            self._data["html"] = html
            return self

        def text(self, text: str):
            self._data["text"] = text
            return self

        def reply_to(self, items):
            self._data["reply_to"] = items
            return self

        def attach_file(self, path: str):
            # store path; sender will open it
            self._data.setdefault("attachments", []).append(path)
            return self

        def build(self):
            return self._data

    class _EmailSender:
        def __init__(self, api_key: str):
            self.api_key = api_key

        def send(self, request):
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            # Convert attachment file paths to API payload
            payload = request.copy()
            paths = payload.pop("attachments", [])
            if paths:
                payload["attachments"] = []
                for path in paths:
                    with open(path, "rb") as fh:
                        import base64
                        payload["attachments"].append(
                            {"content": base64.b64encode(fh.read()).decode("utf-8"), "filename": os.path.basename(path)}
                        )

            resp = requests.post(os.environ.get("MAILERSEND_API_URL", "https://api.mailersend.com/v1/email"),
                                 json=payload, headers=headers, timeout=10)
            class _Resp:
                def __init__(self, r):
                    self.status_code = r.status_code
                    self.data = getattr(r, "json", lambda: {})() or {}
                    self.success = 200 <= r.status_code < 300
            return _Resp(resp)

    class MailerSendClient:
        def __init__(self, api_key: str):
            self.emails = _EmailSender(api_key)


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
    category: Optional[str] = None  # e.g., memberships, location, events


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
    # The MailerSend SDK expects a file path via attach_file, so we create a temp file.
    suffix = os.path.splitext(attachment.filename)[1] or ".bin"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(attachment.content)
    temp_file.flush()
    temp_file.close()
    return {"path": temp_file.name}


def _sender_for_category(category: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Resolve per-category sender overrides.
    Looks for env vars:
      MAILERSEND_FROM_EMAIL_{CATEGORY}
      MAILERSEND_FROM_NAME_{CATEGORY}
      MAILERSEND_REPLY_TO_{CATEGORY}
    where CATEGORY is upper-cased.
    """
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
    API_URL = os.environ.get("MAILERSEND_API_URL", "https://api.mailersend.com/v1/email")

    def send(self, email: EmailMessage) -> bool:
        try:
            config = get_mail_config()
        except Exception as exc:  # configuration errors
            logger.exception("Unable to load MailerSend configuration: %s", exc)
            return False

        # Sender selection priority: explicit on message > category override > default config
        cat_from_email, cat_from_name, cat_reply_to = _sender_for_category(email.category)
        from_email = email.from_email or cat_from_email or config.from_email
        from_name = email.from_name or cat_from_name or config.from_name
        reply_to = email.reply_to or cat_reply_to or config.reply_to

        temp_files = []
        try:
            client = MailerSendClient(config.api_key)
            builder = EmailBuilder().from_email(from_email, from_name)
            builder = builder.to_many([{"email": email.to_email}])
            builder = builder.subject(email.subject)

            if email.html_content:
                builder = builder.html(email.html_content)
            if email.text_content:
                builder = builder.text(email.text_content)
            if not email.html_content and not email.text_content:
                builder = builder.text("")

            if reply_to and hasattr(builder, "reply_to"):
                # Some SDK versions support reply_to([{email,name}])
                try:
                    builder = builder.reply_to([{"email": reply_to}])
                except Exception:
                    logger.debug("Reply-To not supported by current SDK version.")

            if email.attachment:
                encoded = _encode_attachment(email.attachment)
                temp_files.append(encoded["path"])
                builder = builder.attach_file(encoded["path"])

            request = builder.build()
            response = client.emails.send(request)

            if getattr(response, "success", False):
                logger.info("Email sent successfully to %s", email.to_email)
                return True

            status_code = getattr(response, "status_code", "unknown")
            data_preview = str(getattr(response, "data", ""))[:500]
            logger.error("MailerSend error status %s for %s: %s", status_code, email.to_email, data_preview)
            return False
        except Exception as exc:
            logger.exception("Error sending email to %s: %s", email.to_email, exc)
            return False
        finally:
            for path in temp_files:
                try:
                    os.unlink(path)
                except OSError:
                    pass


# Backward compatibility for existing imports/tests
GmailMailService = MailerSendMailService


_mail_service: Optional[MailService] = None


def _print_mail_config(config: MailConfig) -> None:
    print(
        "Mail config: "
        f"from={config.from_email}, "
        f"from_name={config.from_name or '-'}, "
        f"reply_to={config.reply_to or '-'}, "
        f"api_key_set={'yes' if config.api_key else 'no'}"
    )


def init_mail_service(service: Optional[MailService] = None) -> MailService:
    global _mail_service
    _mail_service = service or MailerSendMailService()
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
