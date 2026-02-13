import os
from typing import Optional, Tuple

from dto import EventDTO


def append_organizer_message(html_content: str, message: Optional[str]) -> str:
    if not message:
        return html_content
    return (
        html_content
        + f"""
<hr style="margin:16px 0; border:none; border-top:1px solid #e5e5e5;" />
<p style="margin:0;"><strong>Messaggio dagli organizzatori:</strong></p>
<p style="white-space:pre-wrap; margin-top:4px;">{message}</p>
"""
    )


def get_location_email_template(
    participant_name: str,
    event_data: EventDTO,
    address: Optional[str] = None,
    link: Optional[str] = None,
) -> str:
    """Generates an HTML email to send the location of the event."""

    logo_url = os.getenv("LOGO_URL", "#")
    instagram_url = os.getenv("INSTAGRAM_URL", "#")

    address_line = f"<p><strong>Address:</strong> {address}</p>" if address else ""
    link_line = f"""<p><strong>Map Link:</strong> 
        <a href="{link}" style="color:#ff4500;" target="_blank">{link}</a></p>""" if link else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #000000;
                font-family: Arial, sans-serif;
                color: #999999;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 40px 20px;
                background-color: #000000;
                text-align: center;
            }}
            .logo {{
                max-width: 200px;
                margin-bottom: 30px;
            }}
            .header {{
                font-size: 24px;
                font-weight: bold;
                color: #ff4500;
                margin-bottom: 20px;
            }}
            .location-box {{
                margin: 30px 0;
                padding: 20px;
                border: 1px solid #ff4500;
                border-radius: 5px;
                background-color: #111;
                color: #dddddd;
                text-align: left;
                font-size: 15px;
            }}
            .footer {{
                margin-top: 40px;
                font-size: 12px;
                color: #666;
            }}
            .social-links {{
                margin-top: 20px;
            }}
            .social-links a {{
                color: #ff4500;
                margin: 0 10px;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="{logo_url}" alt="MCP Logo" class="logo">

            <div class="header">Location Details for {event_data.title}</div>
            <p>Hello {participant_name}, here are the details for the event location:</p>

            <div class="location-box">
                <p><strong>Date:</strong> {event_data.date}</p>
                <p><strong>Time:</strong> {event_data.start_time} - {event_data.end_time}</p>
                {address_line}
                {link_line}
            </div>

            <div class="social-links">
                <p style="color: #999999;">Follow us on social media:</p>
                <a href="{instagram_url}">Instagram</a>
            </div>

            <div class="footer">
                <p>See you soon!</p>
            </div>
        </div>
    </body>
    </html>
    """


def build_location_email_payload(
    name: str,
    event_dict: EventDTO,
    address: Optional[str] = None,
    link: Optional[str] = None,
    message: Optional[str] = None,
) -> Tuple[str, str, str]:
    subject = f"Location per l'evento {event_dict.title}"
    html_content = get_location_email_template(name, event_dict, address, link)
    html_content = append_organizer_message(html_content, message)
    text_content = f"""
Ciao {name},

Ecco i dettagli della location per l'evento \"{event_dict.title}\":

Data: {event_dict.date}
Orario: {event_dict.start_time} - {event_dict.end_time}
{f"Indirizzo: {address}" if address else ""}
{f"Link: {link}" if link else ""}
"""
    if message:
        text_content += f"\n\nMessaggio dagli organizzatori:\n{message}"
    text_content += "\n\nA presto!\n"
    return subject, text_content, html_content
