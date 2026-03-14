import os
from dataclasses import dataclass, field
from typing import Any, List, Optional, Type

import requests

try:
    from mailersend import EmailBuilder, MailerSendClient
except ImportError:  # Offline/emulator fallback without SDK installed
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
            payload = dict(request)
            paths = payload.pop("attachments", [])
            if paths:
                payload["attachments"] = []
                for path in paths:
                    with open(path, "rb") as fh:
                        import base64

                        payload["attachments"].append(
                            {
                                "content": base64.b64encode(fh.read()).decode("utf-8"),
                                "filename": os.path.basename(path),
                            }
                        )

            response = requests.post(
                os.environ.get("MAILERSEND_API_URL", "https://api.mailersend.com/v1/email"),
                json=payload,
                headers=headers,
                timeout=10,
            )

            class _Resp:
                def __init__(self, raw):
                    self.status_code = raw.status_code
                    self.success = 200 <= raw.status_code < 300
                    try:
                        self.data = raw.json() or {}
                    except Exception:
                        self.data = raw.text

            return _Resp(response)

    class MailerSendClient:
        def __init__(self, api_key: str):
            self.emails = _EmailSender(api_key)


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
            status_code = int(getattr(response, "status_code", 0) or 0)
            payload = getattr(response, "data", None)
            success = bool(getattr(response, "success", False) or 200 <= status_code < 300)
            error_message = None if success else cls._extract_error(payload)
            return MailerSendSendResult(
                success=success,
                status_code=status_code,
                payload=payload,
                error_message=error_message,
            )
        except Exception as exc:
            return MailerSendSendResult(
                success=False,
                status_code=0,
                payload=None,
                error_message=str(exc),
            )


# Stable aliases used by services/tests for dependency injection/monkeypatching.
MailerSendEmailBuilder = EmailBuilder
