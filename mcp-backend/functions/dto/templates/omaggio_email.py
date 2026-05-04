from typing import Optional

from .common import EmailTemplateBasePayload


class OmaggioEmailPayload(EmailTemplateBasePayload):
    participant_name: str
    event_title: str
    event_date: str
    event_location: str
    entry_time: Optional[str] = None
