from datetime import datetime
from typing import Optional

from .assets import resolve_instagram_url, resolve_logo_url

_FOOTER_LOGO = "https://musiconnectingpeople.com/secondaryLogoWhite.png"
_PROD_URL = "https://musiconnectingpeople.com"


def get_omaggio_email_template(
    participant_name: str,
    event_title: str,
    event_date: str,
    event_location: str,
    entry_time: Optional[str] = None,
) -> str:
    """Genera un'email HTML per i partecipanti omaggio con orario di entrata."""

    logo_url = resolve_logo_url()
    instagram_url = resolve_instagram_url()
    year = datetime.now().year

    entry_time_row = ""
    if entry_time:
        entry_time_row = f"""
                    <tr>
                      <td style="padding:6px 0;border-top:1px solid #1e1e1e;">
                        <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Orario di entrata&nbsp;&nbsp;</span>
                        <span style="color:#f97316;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;">Entro le {entry_time}</span>
                      </td>
                    </tr>"""

    return f"""<!DOCTYPE html>
<html lang="it" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="color-scheme" content="dark" />
  <meta name="supported-color-schemes" content="dark" />
  <title>Il tuo invito – {event_title}</title>
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
            <p style="margin:0 0 16px;color:#f97316;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;">Il tuo invito</p>

            <!-- Headline -->
            <h1 class="headline" style="margin:0 0 8px;color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:34px;font-weight:800;line-height:1.15;letter-spacing:-0.02em;">{event_title}</h1>

            <!-- Intro -->
            <p style="margin:0 0 28px;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;">
              Ciao {participant_name}, sei stato invitato come nostro ospite speciale all'evento. Ti aspettiamo!
            </p>

            <!-- Event details card -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
              style="background:#1a1a1a;border:1px solid #2e2e2e;border-radius:10px;">
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
                        <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Luogo&nbsp;&nbsp;</span>
                        <span style="color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;">{event_location}</span>
                      </td>
                    </tr>
                    {entry_time_row}
                  </table>
                </td>
              </tr>
            </table>

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


def get_omaggio_email_text(
    participant_name: str,
    event_title: str,
    event_date: str,
    event_location: str,
    entry_time: Optional[str] = None,
) -> str:
    text = f"""Ciao {participant_name},

sei stato invitato come nostro ospite speciale all'evento "{event_title}".

Data: {event_date}
Luogo: {event_location}
"""
    if entry_time:
        text += f"Orario di entrata: entro le {entry_time}\n"

    text += "\nTi aspettiamo!\n\nMusic Connecting People"
    return text
