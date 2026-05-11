from typing import Optional

from dto.templates import OmaggioEmailPayload
from services.templates import render_template

from .assets import resolve_instagram_url, resolve_logo_url


def get_omaggio_email_template(
    participant_name: str,
    event_title: str,
    event_date: str,
    event_location: str,
    entry_time: Optional[str] = None,
    location_label: Optional[str] = None,
    location_address: Optional[str] = None,
    location_url: Optional[str] = None,
) -> str:
    payload = OmaggioEmailPayload(
        logo_url=resolve_logo_url(),
        instagram_url=resolve_instagram_url(),
        participant_name=participant_name,
        event_title=event_title,
        event_date=event_date,
        event_location=event_location,
        entry_time=entry_time,
        location_label=location_label,
        location_address=location_address,
        location_url=location_url,
    )
    return render_template("emails/omaggio.html", payload)


def get_omaggio_email_text(
    participant_name: str,
    event_title: str,
    event_date: str,
    event_location: str,
    entry_time: Optional[str] = None,
    location_label: Optional[str] = None,
    location_address: Optional[str] = None,
    location_url: Optional[str] = None,
) -> str:
    venue = location_label or event_location
    text = f"""Ciao {participant_name},

sei stato invitato come nostro ospite speciale all'evento "{event_title}".

Data: {event_date}
Luogo: {venue}
"""
    if location_address:
        text += f"Indirizzo: {location_address}\n"
    if entry_time:
        text += f"Orario di entrata: entro le {entry_time}\n"
    if location_url:
        text += f"\nApri in Google Maps: {location_url}\n"

    text += "\nTi aspettiamo!\n\nMusic Connecting People"
    return text
