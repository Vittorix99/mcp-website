from typing import Optional, Protocol, Tuple

from dto.templates import LocationEmailPayload
from services.templates import render_template

from .assets import resolve_instagram_url, resolve_logo_url


class EventLocationPayload(Protocol):
    title: str
    date: str
    start_time: Optional[str]
    end_time: Optional[str]


def get_location_email_template(
    participant_name: str,
    event_data: EventLocationPayload,
    label: Optional[str] = None,
    address: Optional[str] = None,
    link: Optional[str] = None,
    message: Optional[str] = None,
) -> str:
    """Generates an HTML email to send the location of the event."""

    payload = LocationEmailPayload(
        logo_url=resolve_logo_url(),
        instagram_url=resolve_instagram_url(),
        participant_name=participant_name,
        event_title=event_data.title,
        event_date=event_data.date,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        label=label,
        address=address,
        link=link,
        organizer_message=message,
    )
    return render_template("emails/location.html", payload)


def build_location_email_payload(
    name: str,
    event_dict: EventLocationPayload,
    label: Optional[str] = None,
    address: Optional[str] = None,
    link: Optional[str] = None,
    message: Optional[str] = None,
) -> Tuple[str, str, str]:
    subject = f"Location per l'evento {event_dict.title}"
    html_content = get_location_email_template(name, event_dict, label, address, link, message)
    text_content = f"""Ciao {name},

Ecco i dettagli della location per l'evento "{event_dict.title}":

Data: {event_dict.date}
Orario: {event_dict.start_time} - {event_dict.end_time}
{f"Venue: {label}" if label else ""}
{f"Indirizzo: {address}" if address else ""}
{f"Link: {link}" if link else ""}"""
    if message:
        text_content += f"\n\nMessaggio dagli organizzatori:\n{message}"
    text_content += "\n\nA presto!\n"
    return subject, text_content, html_content
