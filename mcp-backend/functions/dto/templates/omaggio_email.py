from typing import Optional

from .common import EmailTemplateBasePayload


class OmaggioEmailPayload(EmailTemplateBasePayload):
    participant_name: str
    event_title: str
    event_date: str
    event_location: str
    entry_time: Optional[str] = None
    location_label: Optional[str] = None
    location_address: Optional[str] = None
    location_url: Optional[str] = None
