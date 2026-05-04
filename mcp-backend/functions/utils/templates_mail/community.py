from datetime import datetime

from dto.templates import CommunityEmailPayload
from services.templates import render_template

from .assets import resolve_instagram_url, resolve_logo_url


def get_signup_request_template(first_name):
    payload = CommunityEmailPayload(
        logo_url=resolve_logo_url(),
        instagram_url=resolve_instagram_url(),
        first_name=first_name,
        variant="signup_request",
        eyebrow="Richiesta Ricevuta",
        headline=f"Ciao {first_name}, ci siamo.",
    )
    return render_template("emails/community.html", payload)


def get_welcome_email_template(first_name):
    payload = CommunityEmailPayload(
        logo_url=resolve_logo_url(),
        instagram_url=resolve_instagram_url(),
        first_name=first_name,
        variant="welcome",
        eyebrow="Benvenuto nella Community",
        headline=f"Benvenuto, {first_name}.",
    )
    return render_template("emails/community.html", payload)


def get_signup_request_text(first_name):
    return f"""Ciao {first_name}!

Grazie per il tuo interesse nella community di Music Connecting People.

Abbiamo ricevuto la tua richiesta e il nostro team la sta valutando.
Riceverai una risposta via email non appena la tua candidatura sarà processata.

Il team MCP

© {datetime.now().year} Music Connecting People. All rights reserved.
"""


def get_welcome_email_text(first_name):
    return f"""Benvenuto nella community MCP, {first_name}!

Sei ufficialmente parte della community MCP.
Da adesso hai accesso agli eventi esclusivi, alle opportunità di networking e a tutto ciò che ruota intorno alla nostra associazione.

Tieni d'occhio la tua inbox — gli aggiornamenti sugli eventi arrivano presto.

Il team MCP

© {datetime.now().year} Music Connecting People. All rights reserved.
"""
