from .assets import resolve_logo_url, resolve_logo_black_url, resolve_apple_wallet_url, resolve_google_wallet_url


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

    apple_wallet_img = resolve_apple_wallet_url()
    google_wallet_img = resolve_google_wallet_url()

    wallet_buttons = ""
    if wallet_url:
        apple_btn = (
            f'<img src="{apple_wallet_img}" alt="Aggiungi ad Apple Wallet" height="44" style="border: none; display: block;">'
            if apple_wallet_img
            else '<span style="display:inline-block;padding:12px 20px;background:#000;color:#fff;border-radius:8px;font-family:Arial,sans-serif;font-size:14px;font-weight:bold;">Aggiungi ad Apple Wallet</span>'
        )
        google_btn = (
            f'<img src="{google_wallet_img}" alt="Aggiungi a Google Wallet" height="44" style="border: none; display: block;">'
            if google_wallet_img
            else '<span style="display:inline-block;padding:12px 20px;background:#fff;color:#333;border:2px solid #ccc;border-radius:8px;font-family:Arial,sans-serif;font-size:14px;font-weight:bold;">Salva su Google Wallet</span>'
        )
        wallet_buttons = f"""
        <div style="margin: 24px 0; text-align: center;">
          <table role="presentation" cellpadding="0" cellspacing="0" style="margin: 0 auto;">
            <tr>
              <td style="padding: 0 8px;">
                <a href="{wallet_url}" style="display: inline-block;">{apple_btn}</a>
              </td>
              <td style="padding: 0 8px;">
                <a href="{wallet_url}" style="display: inline-block;">{google_btn}</a>
              </td>
            </tr>
          </table>
        </div>
        <p style="font-size: 12px; color: #666; text-align: center;">
          Apri questa email dal tuo smartphone per aggiungere la tessera al wallet.
        </p>
        """

    logo_white = resolve_logo_url()
    logo_black = resolve_logo_black_url()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #ffffff;
                font-family: Arial, sans-serif;
                color: #1f2937;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 40px 20px;
                background-color: #ffffff;
                text-align: center;
            }}
            .logo {{
                max-width: 110px;
                margin-bottom: 30px;
            }}
            /* Dark mode: sfondo scuro → logo bianco visibile, logo nero nascosto */
            .logo-for-light {{ display: inline; }}
            .logo-for-dark  {{ display: none; }}
            @media (prefers-color-scheme: dark) {{
                .logo-for-light {{ display: none !important; }}
                .logo-for-dark  {{ display: inline !important; }}
            }}
            .header {{
                font-size: 24px;
                font-weight: bold;
                color: #ff4500;
                margin-bottom: 20px;
            }}
            .details {{
                font-size: 16px;
                line-height: 1.5;
                margin-bottom: 30px;
                color: #1f2937;
            }}
            .button {{
                display: inline-block;
                margin-top: 20px;
                padding: 12px 24px;
                background-color: #ff4500;
                color: #ffffff;
                text-decoration: none;
                font-weight: bold;
                border-radius: 5px;
            }}
            .footer {{
                margin-top: 40px;
                font-size: 12px;
                color: #6b7280;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Logo light mode (sfondo chiaro → logo scuro) -->
            <img src="{logo_black}" alt="MCP Logo" class="logo logo-for-light" />
            <!-- Logo dark mode (sfondo scuro → logo bianco) -->
            <img src="{logo_white}" alt="MCP Logo" class="logo logo-for-dark" />
            <div class="header">Tessera Associativa {year} </div>

            <div class="details">
                Ciao {full_name},<br><br>
                grazie per esserti iscritto alla nostra Associazione.<br>
                Di seguito i tuoi dati di iscrizione:<br><br>
                <strong>Membership ID:</strong> {membership_id}<br>
                <strong>Validità:</strong> fino al {expiry_date}<br>
            </div>

            {wallet_buttons}

            <div class="footer">
                Membro dell'Associazione Music Connecting People ETS – Anno {year}
            </div>
        </div>
    </body>
    </html>
    """


def get_membership_email_text(membership_data):
    full_name = f"{membership_data.get('name', '')} {membership_data.get('surname', '')}".strip()
    membership_id = membership_data.get("membership_id", "")
    expiry_date = membership_data.get("end_date") or "N/A"
    year = _extract_year(expiry_date)
    wallet_url = membership_data.get("wallet_url") or ""

    wallet_section = ""
    if wallet_url:
        wallet_section = f"""
Aggiungi la tua tessera al wallet (apri dal tuo smartphone):
{wallet_url}
"""

    return f"""
Ciao {full_name},

grazie per esserti iscritto alla nostra Associazione!

Di seguito i tuoi dati di iscrizione:

Membership ID: {membership_id}
Validità: fino al {expiry_date}
{wallet_section}
Membro dell'Associazione Music Connecting People ETS – Anno {year}
"""
