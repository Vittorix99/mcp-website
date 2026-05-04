from typing import Optional

from .common import EmailTemplateBasePayload


class TicketEmailPayload(EmailTemplateBasePayload):
    event_title: str
    event_date: str
    start_time: str
    end_time: str
    location: str
    participant_name: str
    participant_surname: str = ""
    membership_id: Optional[str] = None
    pdf_url: Optional[str] = None
    has_attachment: bool = False
    is_community_event: bool = False
