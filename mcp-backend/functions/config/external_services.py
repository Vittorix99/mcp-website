import os

# External API endpoints used across services
GMAIL_TOKEN_URL = os.environ.get("GMAIL_TOKEN_URL", "https://oauth2.googleapis.com/token")
GENDER_API_URL = os.environ.get("GENDER_API_URL", "https://api.genderize.io")

__all__ = ["GMAIL_TOKEN_URL", "GENDER_API_URL"]
