from datetime import datetime

from dto.templates import NewsletterSignupEmailPayload
from services.templates import render_template

from .assets import resolve_instagram_url, resolve_logo_url


def get_newsletter_signup_template(email, logo_url=None, instagram_url=None):
    payload = NewsletterSignupEmailPayload(
        email=email,
        logo_url=logo_url or resolve_logo_url(),
        instagram_url=instagram_url or resolve_instagram_url(),
    )
    return render_template("emails/newsletter_signup.html", payload)


def get_newsletter_signup_text(email):
    return f"""Benvenuto nella newsletter MCP!

Grazie per esserti iscritto, {email}. Riceverai aggiornamenti esclusivi sugli eventi, annunci speciali e molto altro.

Seguici su Instagram: https://www.instagram.com/musiconnectingpeople_/

© {datetime.now().year} Music Connecting People. All rights reserved.
"""
