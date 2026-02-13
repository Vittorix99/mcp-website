import os


def get_membership_email_template(membership_data, pdf_url=None):
    full_name = f"{membership_data.get('name', '')} {membership_data.get('surname', '')}".strip()
    membership_id = membership_data.get("membership_id", "")
    expiry_date = membership_data.get("end_date", "N/A")
    year = expiry_date.split("-")[2] if expiry_date else "N/A"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #000000;
                font-family: Arial, sans-serif;
                color: #ffffff;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 40px 20px;
                background-color: #000;
                text-align: center;
            }}
            .logo {{
                max-width: 160px;
                margin-bottom: 30px;
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
                color: #999;
            }}
            .button {{
                display: inline-block;
                margin-top: 20px;
                padding: 12px 24px;
                background-color: #ff4500;
                color: #000;
                text-decoration: none;
                font-weight: bold;
                border-radius: 5px;
            }}
            .footer {{
                margin-top: 40px;
                font-size: 12px;
                color: #999;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="{os.getenv('LOGO_URL', '#')}" alt="MCP Logo" class="logo" />
            <div class="header">Tessera Associativa {year} </div>

            <div class="details">
                Ciao {full_name},<br><br>
                grazie per esserti iscritto alla nostra Associazione.<br>
                Di seguito i tuoi dati di iscrizione:<br><br>
                <strong>Membership ID:</strong> {membership_id}<br>
                <strong>Validità:</strong> fino al {expiry_date}<br>
            </div>

     

            <div class="footer">
                Membro dell’Associazione Music Connecting People ETS – Anno {year}
            </div>
        </div>
    </body>
    </html>
    """


def get_membership_email_text(membership_data):
    full_name = f"{membership_data.get('name', '')} {membership_data.get('surname', '')}".strip()
    membership_id = membership_data.get("membership_id", "")
    expiry_date = membership_data.get("end_date", "N/A")
    year = expiry_date.split("-")[0] if expiry_date else "N/A"

    return f"""
Ciao {full_name},

grazie per esserti iscritto alla nostra Associazione!

Di seguito i tuoi dati di iscrizione:

Membership ID: {membership_id}
Validità: fino al {expiry_date}

Membro dell’Associazione Music Connecting People ETS – Anno {year}
"""
