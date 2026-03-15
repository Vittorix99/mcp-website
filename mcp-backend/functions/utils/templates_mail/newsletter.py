from datetime import datetime

from .assets import resolve_instagram_url, resolve_logo_url

_FOOTER_LOGO = "https://musiconnectingpeople.com/secondaryLogoWhite.png"
_PROD_URL = "https://musiconnectingpeople.com"


def _base_html(logo_url: str, eyebrow: str, headline: str, body_html: str, footer_note: str) -> str:
    year = datetime.now().year
    return f"""<!DOCTYPE html>
<html lang="it" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="color-scheme" content="dark" />
  <meta name="supported-color-schemes" content="dark" />
  <title>{eyebrow}</title>
  <style>
    * {{ box-sizing:border-box; }}
    body {{ margin:0; padding:0; background-color:#050505; -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; }}
    img {{ border:0; outline:none; display:block; }}
    a {{ text-decoration:none; }}
    @media screen and (max-width:600px) {{
      .outer-pad  {{ padding:16px 8px !important; }}
      .headline   {{ font-size:28px !important; line-height:1.15 !important; }}
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

            <p style="margin:0 0 16px;color:#f97316;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;">{eyebrow}</p>

            <h1 class="headline" style="margin:0 0 24px;color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:34px;font-weight:800;line-height:1.15;letter-spacing:-0.02em;">{headline}</h1>

            {body_html}

          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td class="footer-pad" style="background:#0a0a0a;border:1px solid #1e1e1e;border-top:none;border-radius:0 0 12px 12px;padding:24px 40px;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td>
                  <p style="margin:0 0 4px;color:#3a3a3a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;line-height:1.6;">{footer_note}</p>
                  <p style="margin:0;color:#2e2e2e;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;">
                    © {year} Music Connecting People
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


def get_newsletter_signup_template(email, logo_url=None, instagram_url=None):
    resolved_logo = logo_url or resolve_logo_url()
    resolved_instagram = instagram_url or resolve_instagram_url()

    body_html = f"""
            <p style="margin:0 0 20px;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;">
              Grazie per esserti iscritto. Riceverai aggiornamenti esclusivi sugli eventi MCP, annunci speciali e molto altro.
            </p>

            <p style="margin:0 0 32px;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;">
              Segui il nostro profilo Instagram per non perderti nessun aggiornamento in tempo reale.
            </p>

            <!-- Divider -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:0 0 28px;">
              <tr><td style="border-top:1px solid #1e1e1e;">&nbsp;</td></tr>
            </table>

            <!-- Instagram CTA -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td align="center">
                  <a href="{resolved_instagram}"
                    style="display:inline-block;background:#1a1a1a;border:1px solid #2e2e2e;color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;letter-spacing:0.04em;padding:14px 32px;border-radius:8px;">
                    Seguici su Instagram &nbsp;→
                  </a>
                </td>
              </tr>
            </table>"""

    return _base_html(
        logo_url=resolved_logo,
        eyebrow="Benvenuto",
        headline="Sei nella lista.",
        body_html=body_html,
        footer_note="Ricevi questa email perché ti sei iscritto alla newsletter di Music Connecting People.",
    )


def get_newsletter_signup_text(email):
    return f"""Benvenuto nella newsletter MCP!

Grazie per esserti iscritto, {email}. Riceverai aggiornamenti esclusivi sugli eventi, annunci speciali e molto altro.

Seguici su Instagram: https://www.instagram.com/musiconnectingpeople_/

© {datetime.now().year} Music Connecting People. All rights reserved.
"""
