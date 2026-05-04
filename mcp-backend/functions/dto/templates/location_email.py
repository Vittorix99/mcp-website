from typing import Optional

from .common import EmailTemplateBasePayload


class LocationEmailPayload(EmailTemplateBasePayload):
    participant_name: str
    event_title: str
    event_date: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    address: Optional[str] = None
    link: Optional[str] = None
    organizer_message: Optional[str] = None
