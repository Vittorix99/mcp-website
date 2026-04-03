"""Mail template builders."""

from .community import (
    get_signup_request_template,
    get_signup_request_text,
    get_welcome_email_template,
    get_welcome_email_text,
)
from .location import build_location_email_payload
from .membership import get_membership_email_template, get_membership_email_text
from .newsletter import get_newsletter_signup_template, get_newsletter_signup_text
from .ticket import get_ticket_email_template, get_ticket_email_text
from .omaggio import get_omaggio_email_template, get_omaggio_email_text

__all__ = [
    "build_location_email_payload",
    "get_newsletter_signup_template",
    "get_newsletter_signup_text",
    "get_ticket_email_template",
    "get_ticket_email_text",
    "get_signup_request_template",
    "get_signup_request_text",
    "get_welcome_email_template",
    "get_welcome_email_text",
    "get_membership_email_template",
    "get_membership_email_text",
    "get_omaggio_email_template",
    "get_omaggio_email_text",
]
