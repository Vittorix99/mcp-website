from datetime import datetime

from .assets import resolve_instagram_url, resolve_logo_url

_FOOTER_LOGO = "https://musiconnectingpeople.com/secondaryLogoWhite.png"
_PROD_URL = "https://musiconnectingpeople.com"


def _dark_template(logo_url: str, instagram_url: str, eyebrow: str, headline: str, body_html: str) -> str:
    year = datetime.now().year
    return f"""<!DOCTYPE html>
<html lang="it" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="color-scheme" content="dark" />
  <meta name="supported-color-schemes" content="dark" />
  <title>{eyebrow} – Music Connecting People</title>
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
            <p style="margin:0 0 16px;color:#f97316;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;">{eyebrow}</p>

            <!-- Headline -->
            <h1 class="headline" style="margin:0 0 24px;color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:34px;font-weight:800;line-height:1.15;letter-spacing:-0.02em;">{headline}</h1>

            {body_html}

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


def get_signup_request_template(first_name):
    logo_url = resolve_logo_url()
    instagram_url = resolve_instagram_url()

    body_html = f"""
            <p style="margin:0 0 20px;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;">
              Grazie per il tuo interesse nella community di Music Connecting People.
            </p>
            <p style="margin:0 0 0;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;">
              Abbiamo ricevuto la tua richiesta — il nostro team la sta valutando. Riceverai una risposta via email non appena la tua candidatura sarà processata.
            </p>"""

    return _dark_template(
        logo_url=logo_url,
        instagram_url=instagram_url,
        eyebrow="Richiesta Ricevuta",
        headline=f"Ciao {first_name}, ci siamo.",
        body_html=body_html,
    )


def get_welcome_email_template(first_name):
    logo_url = resolve_logo_url()
    instagram_url = resolve_instagram_url()

    body_html = f"""
            <p style="margin:0 0 20px;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;">
              Sei ufficialmente parte della community MCP. Da adesso hai accesso agli eventi esclusivi, alle opportunità di networking e a tutto ciò che ruota intorno alla nostra associazione.
            </p>
            <p style="margin:0 0 0;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;">
              Tieni d'occhio la tua inbox — gli aggiornamenti sugli eventi arrivano presto.
            </p>"""

    return _dark_template(
        logo_url=logo_url,
        instagram_url=instagram_url,
        eyebrow="Benvenuto nella Community",
        headline=f"Benvenuto, {first_name}.",
        body_html=body_html,
    )


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
