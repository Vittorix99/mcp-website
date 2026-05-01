"""
MailerSend SDK import with offline/emulator fallback.
When the mailersend package is not installed (local dev, CI without extras),
a minimal stub that speaks the same REST API is used instead.
"""
import os
from typing import Optional

import requests

try:
    from mailersend import EmailBuilder, MailerSendClient  # type: ignore[import]
except ImportError:

    class EmailBuilder:  # type: ignore[no-redef]
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
            import base64

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

    class MailerSendClient:  # type: ignore[no-redef]
        def __init__(self, api_key: str):
            self.emails = _EmailSender(api_key)
