from datetime import datetime

from .assets import resolve_instagram_url, resolve_logo_url

_FOOTER_LOGO = "https://musiconnectingpeople.com/secondaryLogoWhite.png"
_PROD_URL = "https://musiconnectingpeople.com"


def get_ticket_email_template(ticket_data, event_data, pdf_url=None, has_attachment=False):
    """Generates an HTML email for ticket confirmation."""

    logo_url = resolve_logo_url()
    instagram_url = resolve_instagram_url()
    year = datetime.now().year

    event_title = event_data.get("title", "")
    event_date = event_data.get("date", "")
    start_time = event_data.get("startTime", "")
    end_time = event_data.get("endTime", "")
    location = event_data.get("location", "")
    participant_name = ticket_data.get("name", "")
    participant_surname = ticket_data.get("surname", "")
    membership_id = ticket_data.get("membershipId")

    membership_row = ""
    if membership_id:
        membership_row = f"""
              <tr>
                <td style="padding:6px 0;border-top:1px solid #1e1e1e;">
                  <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Membership&nbsp;&nbsp;</span>
                  <span style="color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;">{membership_id}</span>
                </td>
              </tr>"""

    if has_attachment:
        pdf_block = """
            <p style="margin:24px 0 0;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.7;">
              La tua partecipazione in PDF è allegata a questa email.
            </p>"""
    elif pdf_url:
        pdf_block = f"""
            <!-- Divider -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:28px 0 0;">
              <tr><td style="border-top:1px solid #1e1e1e;">&nbsp;</td></tr>
            </table>
            <!-- PDF CTA -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-top:28px;">
              <tr>
                <td align="center">
                  <!--[if mso]>
                  <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word"
                    href="{pdf_url}" style="height:52px;v-text-anchor:middle;width:400px;" arcsize="15%" strokecolor="#f97316" fillcolor="#f97316">
                    <w:anchorlock/>
                    <center style="color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:15px;font-weight:700;">Scarica la tua partecipazione →</center>
                  </v:roundrect>
                  <![endif]-->
                  <!--[if !mso]><!-->
                  <a href="{pdf_url}"
                    style="display:block;width:100%;background:#f97316;color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:15px;font-weight:700;letter-spacing:0.02em;text-decoration:none;text-align:center;padding:17px 32px;border-radius:8px;">
                    Scarica la tua partecipazione &nbsp;&nbsp;→
                  </a>
                  <!--<![endif]-->
                </td>
              </tr>
            </table>"""
    else:
        pdf_block = ""

    is_community_event = event_data.get("type") in ["community", "custom_ep12"]
    community_block = ""
    if is_community_event:
        community_block = """
            <!-- Community notice -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:28px 0 0;">
              <tr>
                <td style="background:#1a1a1a;border:1px solid #2e2e2e;border-left:3px solid #f97316;border-radius:0 8px 8px 0;padding:16px 20px;">
                  <p style="margin:0;color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;line-height:1.7;">
                    <strong style="color:#f97316;">Importante:</strong> Questo evento è riservato ai soci dell'Associazione MCP. L'accesso è consentito esclusivamente ai partecipanti registrati. La location verrà comunicata via email il giorno dell'evento.
                  </p>
                </td>
              </tr>
            </table>"""

    return f"""<!DOCTYPE html>
<html lang="it" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="color-scheme" content="dark" />
  <meta name="supported-color-schemes" content="dark" />
  <title>Partecipazione confermata – {event_title}</title>
  <style>
    * {{ box-sizing:border-box; }}
    body {{ margin:0; padding:0; background-color:#050505; -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; }}
    img {{ border:0; outline:none; display:block; }}
    a {{ text-decoration:none; }}
    @media screen and (max-width:600px) {{
      .outer-pad  {{ padding:16px 8px !important; }}
      .headline   {{ font-size:26px !important; line-height:1.15 !important; }}
      .body-pad   {{ padding:28px 20px 32px !important; }}
      .footer-pad {{ padding:20px !important; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background-color:#050505;">

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#050505;">
  <tr>
    <td class="outer-pad" align="center" style="padding:40px 16px 48px;">

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:598px;">

        <!-- TOP ACCENT BAR -->
        <tr>
          <td style="background:linear-gradient(90deg,#f97316 0%,#fb923c 50%,#f97316 100%);height:3px;border-radius:3px 3px 0 0;font-size:0;line-height:0;">&nbsp;</td>
        </tr>

        <!-- HEADER – Logo -->
        <tr>
          <td style="background:#0e0e0e;border-left:1px solid #1e1e1e;border-right:1px solid #1e1e1e;padding:32px 40px 28px;text-align:center;">
            <a href="{_PROD_URL}">
              <img src="{logo_url}" alt="Music Connecting People" width="150"
                style="max-width:150px;height:auto;display:inline-block;" />
            </a>
          </td>
        </tr>

        <!-- BODY -->
        <tr>
          <td class="body-pad" style="background:#111111;border-left:1px solid #1e1e1e;border-right:1px solid #1e1e1e;padding:36px 40px 40px;">

            <!-- Eyebrow -->
            <p style="margin:0 0 16px;color:#f97316;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;">Partecipazione Confermata</p>

            <!-- Headline -->
            <h1 class="headline" style="margin:0 0 8px;color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:34px;font-weight:800;line-height:1.15;letter-spacing:-0.02em;">{event_title}</h1>

            <!-- Sub intro -->
            <p style="margin:0 0 28px;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;">
              Grazie per la tua partecipazione, {participant_name}! Il tuo posto è confermato.
            </p>

            <!-- Details card -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
              style="background:#1a1a1a;border:1px solid #2e2e2e;border-radius:10px;margin:0 0 4px;">
              <tr>
                <td style="padding:20px 24px;">
                  <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                      <td style="padding:6px 0;">
                        <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Data&nbsp;&nbsp;</span>
                        <span style="color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;">{event_date}</span>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0;border-top:1px solid #1e1e1e;">
                        <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Orario&nbsp;&nbsp;</span>
                        <span style="color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;">{start_time} – {end_time}</span>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0;border-top:1px solid #1e1e1e;">
                        <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Location&nbsp;&nbsp;</span>
                        <span style="color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;">{location}</span>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0;border-top:1px solid #1e1e1e;">
                        <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Partecipante&nbsp;&nbsp;</span>
                        <span style="color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;">{participant_name} {participant_surname}</span>
                      </td>
                    </tr>
                    {membership_row}
                  </table>
                </td>
              </tr>
            </table>

            {community_block}
            {pdf_block}

            <!-- Divider -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:32px 0 28px;">
              <tr><td style="border-top:1px solid #1e1e1e;">&nbsp;</td></tr>
            </table>

            <!-- Instagram -->
            <p style="margin:0;color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:13px;text-align:center;">
              Seguici su
              <a href="{instagram_url}" style="color:#f97316;font-weight:600;">Instagram</a>
              per aggiornamenti in tempo reale.
            </p>

          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td class="footer-pad" style="background:#0a0a0a;border:1px solid #1e1e1e;border-top:none;border-radius:0 0 12px 12px;padding:24px 40px;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td>
                  <p style="margin:0;color:#3a3a3a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;line-height:1.6;">
                    © {year} Music Connecting People. All rights reserved.
                  </p>
                </td>
                <td align="right" style="vertical-align:middle;">
                  <img src="{_FOOTER_LOGO}" alt="MCP" width="60"
                    style="max-width:60px;height:auto;opacity:0.3;" />
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>

</body>
</html>""".strip()


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
