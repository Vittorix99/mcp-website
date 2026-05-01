import logging
from dataclasses import dataclass, field
from typing import Any, List, Optional, Type

from clients._mailersend_sdk import EmailBuilder, MailerSendClient
from services.core.error_logs_service import log_external_error

logger = logging.getLogger("mailersend_client")

# Alias stabile per injection/monkeypatch nei test senza dipendere dal SDK reale.
MailerSendEmailBuilder = EmailBuilder


class _Endpoints:
    SEND_EMAIL = "https://api.mailersend.com/v1/email"


@dataclass(frozen=True)
class MailerSendSendResult:
    success: bool
    status_code: int
    payload: Optional[Any] = None
    error_message: Optional[str] = None


@dataclass(frozen=True)
class MailerSendRequest:
    from_email: str
    to_email: str
    subject: str
    text_content: str
    html_content: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    attachment_paths: List[str] = field(default_factory=list)


class MailerSendRoutes:
    """Client MailerSend: costruisce la request SDK e normalizza l'esito."""

    @staticmethod
    def _extract_error(payload: Any) -> str:
        if isinstance(payload, dict):
            return str(payload.get("message") or payload.get("error") or payload)
        return str(payload)

    @classmethod
    def send_email(
        cls,
        request: MailerSendRequest,
        api_key: str,
        client_cls: Type = MailerSendClient,
        builder_cls: Type = EmailBuilder,
    ) -> MailerSendSendResult:
        try:
            # Il service passa contenuti gia' pronti; qui traduciamo solo verso il formato SDK.
            builder = builder_cls().from_email(request.from_email, request.from_name)
            builder = builder.to_many([{"email": request.to_email}])
            builder = builder.subject(request.subject)

            if request.html_content:
                builder = builder.html(request.html_content)
            if request.text_content:
                builder = builder.text(request.text_content)
            if not request.html_content and not request.text_content:
                builder = builder.text("")

            if request.reply_to and hasattr(builder, "reply_to"):
                try:
                    builder = builder.reply_to([{"email": request.reply_to}])
                except Exception:
                    pass

            for path in request.attachment_paths:
                builder = builder.attach_file(path)

            raw_request = builder.build()
            response = client_cls(api_key).emails.send(raw_request)
            # Il wrapper SDK puo' esporre success/status/data: li comprimiamo in un result stabile.
            status_code = int(getattr(response, "status_code", 0) or 0)
            payload = getattr(response, "data", None)
            success = bool(getattr(response, "success", False) or 200 <= status_code < 300)
            error_message = None if success else cls._extract_error(payload)

            if success:
                logger.info("send_email: sent to %s (status=%d)", request.to_email, status_code)
            else:
                log_external_error(
                    service="MailerSend",
                    operation="send_email",
                    source="clients.mailersend_client.send_email",
                    message=error_message or "MailerSend send failed",
                    status_code=status_code,
                    payload=payload,
                    context={"to_email": request.to_email, "subject": request.subject},
                )

            return MailerSendSendResult(
                success=success,
                status_code=status_code,
                payload=payload,
                error_message=error_message,
            )
        except Exception as exc:
            log_external_error(
                service="MailerSend",
                operation="send_email",
                source="clients.mailersend_client.send_email",
                message=str(exc),
                status_code=0,
                context={"to_email": request.to_email, "subject": request.subject},
            )
            return MailerSendSendResult(
                success=False,
                status_code=0,
                payload=None,
                error_message=str(exc),
            )
