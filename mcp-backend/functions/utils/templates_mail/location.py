from datetime import datetime
from typing import Optional, Tuple

from dto import EventDTO
from .assets import resolve_instagram_url, resolve_logo_url

_FOOTER_LOGO = "https://musiconnectingpeople.com/secondaryLogoWhite.png"
_PROD_URL = "https://musiconnectingpeople.com"


def append_organizer_message(html_content: str, message: Optional[str]) -> str:
    if not message:
        return html_content
    escaped = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        html_content
        + f"""
<!-- Organizer message appended -->
<table role="presentation" cellpadding="0" cellspacing="0" width="100%"
  style="background:#111111;border-left:1px solid #1e1e1e;border-right:1px solid #1e1e1e;padding:0 40px 32px;">
  <tr>
    <td style="border-top:1px solid #1e1e1e;padding-top:24px;">
      <p style="margin:0 0 8px;color:#f97316;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;">Messaggio dagli organizzatori</p>
      <p style="margin:0;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.7;white-space:pre-wrap;">{escaped}</p>
    </td>
  </tr>
</table>"""
    )


def get_location_email_template(
    participant_name: str,
    event_data: EventDTO,
    address: Optional[str] = None,
    link: Optional[str] = None,
) -> str:
    """Generates an HTML email to send the location of the event."""

    logo_url = resolve_logo_url()
    instagram_url = resolve_instagram_url()
    year = datetime.now().year

    address_row = ""
    if address:
        address_row = f"""
                    <tr>
                      <td style="padding:6px 0;border-top:1px solid #1e1e1e;">
                        <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Indirizzo&nbsp;&nbsp;</span>
                        <span style="color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;">{address}</span>
                      </td>
                    </tr>"""

    map_block = ""
    if link:
        map_block = f"""
            <!-- Map CTA -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:28px 0 0;">
              <tr>
                <td align="center">
                  <!--[if mso]>
                  <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word"
                    href="{link}" style="height:52px;v-text-anchor:middle;width:400px;" arcsize="15%" strokecolor="#f97316" fillcolor="#f97316">
                    <w:anchorlock/>
                    <center style="color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:15px;font-weight:700;">Apri su Maps →</center>
                  </v:roundrect>
                  <![endif]-->
                  <!--[if !mso]><!-->
                  <a href="{link}"
                    style="display:block;width:100%;background:#f97316;color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:15px;font-weight:700;letter-spacing:0.02em;text-decoration:none;text-align:center;padding:17px 32px;border-radius:8px;">
                    Apri su Maps &nbsp;&nbsp;→
                  </a>
                  <!--<![endif]-->
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
  <title>Location svelata – {event_data.title}</title>
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
            <p style="margin:0 0 16px;color:#f97316;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;">Location Svelata</p>

            <!-- Headline -->
            <h1 class="headline" style="margin:0 0 8px;color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:34px;font-weight:800;line-height:1.15;letter-spacing:-0.02em;">{event_data.title}</h1>

            <!-- Intro -->
            <p style="margin:0 0 28px;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;">
              Ciao {participant_name}, ecco i dettagli della location per l'evento.
            </p>

            <!-- Location card -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
              style="background:#1a1a1a;border:1px solid #2e2e2e;border-radius:10px;">
              <tr>
                <td style="padding:20px 24px;">
                  <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                      <td style="padding:6px 0;">
                        <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Data&nbsp;&nbsp;</span>
                        <span style="color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;">{event_data.date}</span>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0;border-top:1px solid #1e1e1e;">
                        <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Orario&nbsp;&nbsp;</span>
                        <span style="color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;">{event_data.start_time} – {event_data.end_time}</span>
                      </td>
                    </tr>
                    {address_row}
                  </table>
                </td>
              </tr>
            </table>

            {map_block}

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
    text_content = f"""Ciao {name},

Ecco i dettagli della location per l'evento "{event_dict.title}":

Data: {event_dict.date}
Orario: {event_dict.start_time} - {event_dict.end_time}
{f"Indirizzo: {address}" if address else ""}
{f"Link: {link}" if link else ""}"""
    if message:
        text_content += f"\n\nMessaggio dagli organizzatori:\n{message}"
    text_content += "\n\nA presto!\n"
    return subject, text_content, html_content
