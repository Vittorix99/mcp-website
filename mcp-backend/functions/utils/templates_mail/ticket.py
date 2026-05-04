from dto.templates import TicketEmailPayload
from services.templates import render_template

from .assets import resolve_instagram_url, resolve_logo_url


def get_ticket_email_template(ticket_data, event_data, pdf_url=None, has_attachment=False):
    """Generates an HTML email for ticket confirmation."""

    payload = TicketEmailPayload(
        logo_url=resolve_logo_url(),
        instagram_url=resolve_instagram_url(),
        event_title=event_data.get("title", ""),
        event_date=event_data.get("date", ""),
        start_time=event_data.get("startTime", ""),
        end_time=event_data.get("endTime", ""),
        location=event_data.get("location", ""),
        participant_name=ticket_data.get("name", ""),
        participant_surname=ticket_data.get("surname", ""),
        membership_id=ticket_data.get("membershipId") or None,
        pdf_url=pdf_url,
        has_attachment=has_attachment,
        is_community_event=event_data.get("type") in ["community", "custom_ep12"],
    )
    return render_template("emails/ticket.html", payload)


def get_ticket_email_text(ticket_data, event_data):
    name = ticket_data.get("name", "")
    surname = ticket_data.get("surname", "")
    event_title = event_data.get("title")
    date = event_data.get("date")
    time = f"{event_data.get('startTime')} - {event_data.get('endTime')}"
    location = event_data.get("location")
    membership_id = ticket_data.get("membershipId")

    membership_line = f"Membership ID: {membership_id}\n" if membership_id else ""

    return f"""
Grazie per la tua partecipazione, {name}!

Evento: {event_title}
Data: {date}
Orario: {time}
Location: {location}

Partecipazione:
Nome: {name} {surname}
{membership_line}

Ci vediamo lì!
""".strip()
