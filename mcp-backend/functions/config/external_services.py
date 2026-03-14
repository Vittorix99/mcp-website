import os

# External API endpoints used across services
GMAIL_TOKEN_URL = os.environ.get("GMAIL_TOKEN_URL", "https://oauth2.googleapis.com/token")
GENDER_API_URL = os.environ.get("GENDER_API_URL", "https://api.genderize.io")

MAILERLITE_BASE_URL = os.environ.get("MAILERLITE_BASE_URL", "https://connect.mailerlite.com/api")
MAILERLITE_API_KEY = os.environ.get("MAILERLITE_API_KEY")

PASS2U_API_KEY = os.environ.get("PASS2U_API_KEY")
PASS2U_BASE_URL = "https://api.pass2u.net/v2"

__all__ = [
    "GMAIL_TOKEN_URL",
    "GENDER_API_URL",
    "MAILERLITE_BASE_URL",
    "MAILERLITE_API_KEY",
    "PASS2U_API_KEY",
    "PASS2U_BASE_URL",
]
