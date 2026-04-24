import os

# External API endpoints used across services
GMAIL_TOKEN_URL = os.environ.get("GMAIL_TOKEN_URL", "https://oauth2.googleapis.com/token")
GENDER_API_URL = os.environ.get("GENDER_API_URL", "https://api.genderize.io")


PASS2U_API_KEY = os.environ.get("PASS2U_API_KEY")
PASS2U_BASE_URL = "https://api.pass2u.net/v2"

SENDER_API_KEY = os.environ.get("SENDER_API_KEY")
SENDER_BASE_URL = "https://api.sender.net/v2"
SENDER_GROUP_NEWSLETTER = os.environ.get("SENDER_GROUP_NEWSLETTER")
SENDER_GROUP_MEMBERS = os.environ.get("SENDER_GROUP_MEMBERS")
SENDER_GROUP_TICKET_BUYERS = os.environ.get("SENDER_GROUP_TICKET_BUYERS")
SENDER_WEBHOOK_SECRET = os.environ.get("SENDER_WEBHOOK_SECRET")

__all__ = [
    "GMAIL_TOKEN_URL",
    "GENDER_API_URL",
    "PASS2U_API_KEY",
    "PASS2U_BASE_URL",
    "SENDER_API_KEY",
    "SENDER_BASE_URL",
    "SENDER_GROUP_NEWSLETTER",
    "SENDER_GROUP_MEMBERS",
    "SENDER_GROUP_TICKET_BUYERS",
    "SENDER_WEBHOOK_SECRET",
]
