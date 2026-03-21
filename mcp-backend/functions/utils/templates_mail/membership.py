from datetime import datetime

from .assets import resolve_apple_wallet_url, resolve_google_wallet_url, resolve_logo_url

_FOOTER_LOGO = "https://musiconnectingpeople.com/secondaryLogoWhite.png"
_PROD_URL = "https://musiconnectingpeople.com"


def _extract_year(expiry_date: str) -> str:
    if isinstance(expiry_date, str) and "-" in expiry_date:
        return expiry_date.split("-")[-1]
    return "N/A"


def get_membership_email_template(membership_data, pdf_url=None):
    full_name = f"{membership_data.get('name', '')} {membership_data.get('surname', '')}".strip()
    membership_id = membership_data.get("membership_id", "")
    expiry_date = membership_data.get("end_date") or "N/A"
    year = _extract_year(expiry_date)
    wallet_url = membership_data.get("wallet_url") or ""
    current_year = datetime.now().year

    logo_url = resolve_logo_url()
    apple_wallet_img = resolve_apple_wallet_url()
    google_wallet_img = resolve_google_wallet_url()

    wallet_block = ""
    if wallet_url:
        apple_btn = (
            f'<img src="{apple_wallet_img}" alt="Aggiungi ad Apple Wallet" height="44" style="border:none;display:block;" />'
            if apple_wallet_img
            else '<span style="display:inline-block;padding:12px 20px;background:#000;color:#fff;border-radius:8px;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;">Aggiungi ad Apple Wallet</span>'
        )
        google_btn = (
            f'<img src="{google_wallet_img}" alt="Aggiungi a Google Wallet" height="44" style="border:none;display:block;" />'
            if google_wallet_img
            else '<span style="display:inline-block;padding:12px 20px;background:#1a1a1a;color:#e8e8e8;border:1px solid #2e2e2e;border-radius:8px;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;">Salva su Google Wallet</span>'
        )
        wallet_block = f"""
            <!-- Wallet buttons -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:28px 0 0;">
              <tr>
                <td align="center">
                  <table role="presentation" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="padding:0 8px;">
                        <a href="{wallet_url}" style="display:inline-block;">{apple_btn}</a>
                      </td>
                      <td style="padding:0 8px;">
                        <a href="{wallet_url}" style="display:inline-block;">{google_btn}</a>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
            <p style="margin:12px 0 0;color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;text-align:center;line-height:1.5;">
              Apri questa email dal tuo smartphone per aggiungere la tessera al wallet.
            </p>"""

    pdf_block = ""
    if pdf_url:
        pdf_block = f"""
            <!-- PDF download -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin:28px 0 0;">
              <tr>
                <td align="center">
                  <!--[if mso]>
                  <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word"
                    href="{pdf_url}" style="height:52px;v-text-anchor:middle;width:400px;" arcsize="15%" strokecolor="#f97316" fillcolor="#f97316">
                    <w:anchorlock/>
                    <center style="color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:15px;font-weight:700;">Scarica la tessera PDF →</center>
                  </v:roundrect>
                  <![endif]-->
                  <!--[if !mso]><!-->
                  <a href="{pdf_url}"
                    style="display:block;width:100%;background:#f97316;color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:15px;font-weight:700;letter-spacing:0.02em;text-decoration:none;text-align:center;padding:17px 32px;border-radius:8px;">
                    Scarica la tessera PDF &nbsp;&nbsp;→
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
  <title>Tessera Associativa {year} – Music Connecting People</title>
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
            <p style="margin:0 0 16px;color:#f97316;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:11px;font-weight:700;letter-spacing:0.16em;text-transform:uppercase;">Tessera Associativa {year}</p>

            <!-- Headline -->
            <h1 class="headline" style="margin:0 0 8px;color:#ffffff;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:34px;font-weight:800;line-height:1.15;letter-spacing:-0.02em;">Benvenuto nell'Associazione.</h1>

            <!-- Intro -->
            <p style="margin:0 0 28px;color:#9a9a9a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;">
              Ciao {full_name}, grazie per esserti iscritto all'Associazione Music Connecting People. Di seguito i tuoi dati di iscrizione.
            </p>

            <!-- Membership card -->
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
              style="background:#1a1a1a;border:1px solid #2e2e2e;border-radius:10px;">
              <tr>
                <td style="padding:20px 24px;">
                  <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                      <td style="padding:6px 0;">
                        <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Membership ID&nbsp;&nbsp;</span>
                        <span style="color:#f97316;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:15px;font-weight:700;letter-spacing:0.04em;">{membership_id}</span>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0;border-top:1px solid #1e1e1e;">
                        <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Validità&nbsp;&nbsp;</span>
                        <span style="color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;">fino al {expiry_date}</span>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0;border-top:1px solid #1e1e1e;">
                        <span style="color:#555555;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">Intestatario&nbsp;&nbsp;</span>
                        <span style="color:#e8e8e8;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:14px;font-weight:600;">{full_name}</span>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>

            {wallet_block}
            {pdf_block}

          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td class="footer-pad" style="background:#0a0a0a;border:1px solid #1e1e1e;border-top:none;border-radius:0 0 12px 12px;padding:24px 40px;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
              <tr>
                <td>
                  <p style="margin:0 0 4px;color:#3a3a3a;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;line-height:1.6;">
                    Membro dell'Associazione Music Connecting People ETS – Anno {year}
                  </p>
                  <p style="margin:0;color:#2e2e2e;font-family:Helvetica Neue,Helvetica,Arial,sans-serif;font-size:12px;">
                    © {current_year} Music Connecting People
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


def get_membership_email_text(membership_data):
    full_name = f"{membership_data.get('name', '')} {membership_data.get('surname', '')}".strip()
    membership_id = membership_data.get("membership_id", "")
    expiry_date = membership_data.get("end_date") or "N/A"
    year = _extract_year(expiry_date)
    wallet_url = membership_data.get("wallet_url") or ""

    wallet_section = ""
    if wallet_url:
        wallet_section = f"\nAggiungi la tua tessera al wallet (apri dal tuo smartphone):\n{wallet_url}\n"

    return f"""Ciao {full_name},

grazie per esserti iscritto all'Associazione Music Connecting People!

Membership ID: {membership_id}
Validità: fino al {expiry_date}
{wallet_section}
Membro dell'Associazione Music Connecting People ETS – Anno {year}
"""
