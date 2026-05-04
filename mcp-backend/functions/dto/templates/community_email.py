from typing import Literal

from .common import EmailTemplateBasePayload


class CommunityEmailPayload(EmailTemplateBasePayload):
    first_name: str
    variant: Literal["signup_request", "welcome"]
    eyebrow: str
    headline: str
