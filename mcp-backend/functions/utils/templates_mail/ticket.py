import os


def get_ticket_email_template(ticket_data, event_data, pdf_url=None):
    """Generates an HTML email for the ticket purchase confirmation, including a PDF link if available."""

    logo_url = os.getenv("LOGO_URL", "#")
    instagram_url = os.getenv("INSTAGRAM_URL", "#")

    pdf_download_html = f"""
        <p style="margin-top: 20px;">Clicca qui sotto per scaricare la tua partecipazione:</p>
        <a class="button" href="{pdf_url}" target="_blank">Scarica la tua partecipazione</a>
    """ if pdf_url else ""

    membership_line = f"<br>Membership ID: {ticket_data.get('membershipId')}" if ticket_data.get("membershipId") else ""

    is_community_event = event_data.get("type") in ["community", "custom_ep12"]
    extra_info = ""
    if is_community_event:
        extra_info = """
        <div class="notice">
            <p><strong>Important:</strong> This event is reserved for members of the MCP Association. Entry will be allowed only to registered participants. The event location will be sent to your email on the day of the event.</p>
        </div>
        """

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
                color: #999999
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
            .details {{
                margin: 30px 0;
                padding: 20px;
                border: 1px solid #ff4500;
                border-radius: 5px;
                text-align: left;
                color: #999999
                
            }}
            .button {{
                display: inline-block;
                margin-top: 10px;
                padding: 12px 24px;
                background-color: #ff4500;
                color: #000;
                font-weight: bold;
                text-decoration: none;
                border-radius: 5px;
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
            .notice {{
                margin: 20px 0;
                padding: 15px;
                background-color: #111;
                border: 1px dashed #ff4500;
                border-radius: 5px;
                font-size: 14px;
                color: #ffcccb;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="{logo_url}" alt="MCP Logo" class="logo">

            <div class="header">La tua partecipazione per {event_data.get("title")}</div>
            <p>Grazie per la tua partecipazione, {ticket_data.get("name")}!</p>

            <div class="details">
                <strong>Event Details:</strong><br>
                Date: {event_data.get("date")}<br>
                Time: {event_data.get("startTime")} - {event_data.get("endTime")}<br>
                Location: {event_data.get("location")}<br>
                <br>
                <strong>La tua partecipazione:</strong><br>
                Name: {ticket_data.get("name")} {ticket_data.get("surname")}<br>
                {membership_line}
            </div>

            {extra_info}
            {pdf_download_html}

            <div class="social-links">
                <p style="color: #999999;">Follow us on social media:</p>
                <a href="{instagram_url}">Instagram</a>
            </div>

            <div class="footer">
                <p>See you at the event!</p>
            </div>
        </div>
    </body>
    </html>
    """


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
