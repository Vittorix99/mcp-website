from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch    
from reportlab.platypus import Spacer
from reportlab.platypus import Image
import tempfile
from config.firebase_config import bucket
from io import BytesIO
from weasyprint import HTML
from config.event_types import EventTypes



def generate_ticket_pdf(ticket_data, event_data, logo_path):
    print("Event data is:", event_data)
    ev_type = (event_data.get("type") or "").lower()
    if ev_type in (EventTypes.COMMUNITY.value, EventTypes.CUSTOM_EP12.value, EventTypes.CUSTOM_EP13.value ):
        local_logo_path = download_image_from_firebase(logo_path)
        html = generate_member_ticket_pdf_html(ticket_data, event_data, local_logo_path)
        buffer = BytesIO()
        HTML(string=html, base_url=".").write_pdf(buffer)
        buffer.seek(0)
        return buffer
    else:
        buffer = generate_ticket_pdf_reportlab(ticket_data=ticket_data, event_data=event_data, logo_path=logo_path)
        return buffer 


def generate_membership_pdf(membership_data, logo_path, pattern_path):
    if not membership_data.get("subscription_valid"):
        print("❌ Subscription is not valid, no membership card generated.")
        return None



    # Scarica logo e pattern
    local_logo_path = download_image_from_firebase(logo_path)
    local_pattern_path = download_image_from_firebase(pattern_path)

    # Genera HTML
    html = generate_membership_card_html(membership_data, local_logo_path)

    # Genera PDF
    buffer = BytesIO()
    HTML(string=html, base_url=".").write_pdf(buffer)
    buffer.seek(0)
    return buffer



def generate_member_ticket_pdf_html(ticket_data, event_data, logo_url):
    first_name = ticket_data.get("name", "")
    last_name = ticket_data.get("surname", "")
    full_name = f"{first_name} {last_name}".strip()
    ticket_id = ticket_data.get("purchase_id", "N/A")
    membership_id = ticket_data.get("membershipId") or None
    price = f"{ticket_data.get('price')} EUR"
    date = event_data.get("date")
    time = f"{event_data.get('startTime')} - {event_data.get('endTime')}"
    location = event_data.get("location")
    title = event_data.get("title", "Event Title")

    return f"""
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: A4 portrait;
            margin: 0;
        }}
        body {{
            background: #000;
            color: #fff;
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 2cm;
        }}
        .ticket {{
            border: 3px solid #ff0000;
            border-radius: 12px;
            padding: 2cm;
            height: 100%;
        }}
        .logo {{
            display: block;
            margin: 0 auto 30px auto;
            
            width: 160px;
        }}
        .event-title {{
            font-size: 36px;
            color: #ff0000;
            font-weight: bold;
            text-align: center;
            margin-bottom: 10px;
        }}
        .event-subtitle {{
            font-size: 18px;
            color: #ccc;
            text-align: center;
            margin-bottom: 30px;
        }}
        .notice {{
            font-size: 14px;
            background-color: #111;
            border: 1px dashed #ff0000;
            padding: 10px 20px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .info-block {{
            margin-top: 20px;
            font-size: 16px;
            line-height: 1.6;
        }}
        .label {{
            font-weight: bold;
            color: #999;
        }}
        .value {{
            color: #fff;
        }}
        .membership {{
            margin-top: 30px;
            font-style: italic;
            font-size: 13px;
            color: #ccc;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="ticket">
        <img src="{logo_url}" class="logo" alt="MCP Logo">

        <h1 class="event-title">{title}</h1>
        <p class="event-subtitle">Sunrise Chasers Edition</p>

        <div class="notice">
            Questo è un <strong>invito nominale</strong> valido solo per la persona registrata.<br>
            L'ingresso sarà consentito solo al nominativo indicato qui sotto.
        </div>

        <div class="info-block">
            <p><span class="label">Nominativo:</span> <span class="value">{full_name}</span></p>
            {f'<p><span class="label">Membership ID:</span> <span class="value">{membership_id}</span></p>' if membership_id else ""}
        </div>

        <div class="info-block">
            <p><span class="label">Data:</span> <span class="value">{date}</span></p>
            <p><span class="label">Orario:</span> <span class="value">{time}</span></p>
            <p><span class="label">Location:</span> <span class="value">{location}</span></p>
        </div>

        <div class="membership">
            Evento riservato ai soci dell’Associazione Music Connecting People ETS.
        </div>
    </div>
</body>
</html>
"""

def generate_membership_card_html(member_data, logo_url):
    full_name = f"{member_data.get('name', '')} {member_data.get('surname', '')}".strip()
    membership_id = member_data.get("membership_id", "N/A")
    expiry_date = member_data.get("end_date", "N/A")
    expiry_year = expiry_date.split("-")[2] if expiry_date else ""

    return f"""
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8" />
  <style>
    @page {{
      size: 200mm 100mm;
      margin: 10mm;
    }}
    body {{
      margin: 0;
      background-color: white;
      font-family: Helvetica, Arial, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
    }}
    .card {{
       width: 375px;
      height: 240px;
      padding: 30px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: linear-gradient(150deg, #ff6600, #b0002a, #1a0010, #000);
      border: 0.2px solid #ff6600;
      border-radius: 12px;
      text-align: center;
    }}
    .logo {{
      width: 120px;
      margin-bottom: 18px;
      
     
      background-clip: text;
      -webkit-background-clip: text;
      -webkit-text-fill-color: #ffffff;
      animation: shine 5s linear infinite;
      text-shadow: 0 0 0.8px rgba(255,255,255,0.4)
    }}
    .metallic {{
      font-weight: bold;
      color: #ddd;
      background-size: 200% auto;
      background-clip: text;
      -webkit-background-clip: text;
      -webkit-text-fill-color: #ffffff;
      animation: shine 5s linear infinite;
      text-shadow: 0 0 0.8px rgba(255,255,255,0.4);
    }}
    .name {{
      font-size: 23px;
      margin-bottom: 25px;
      margin-top: 28px;
    }}
    .info {{
      font-size: 12px;
      margin-bottom: 8px;
    }}
    .footer {{
      font-size: 11px;
      margin-top: 18px;
      font-style: italic;
      margin-bottom: -10px;
    }}
    @keyframes shine {{
      0% {{ background-position: 200% center; }}
      100% {{ background-position: 0% center; }}
    }}
  </style>
</head>
<body>
  <div class="card">
    <img class="logo metallic" src="{logo_url}" alt="Logo MCP" />
    <div class="name metallic">{full_name}</div>
    <div class="info metallic">Membership ID: {membership_id}</div>
    <div class="info metallic">Valida fino al: {expiry_date}</div>
    <div class="footer metallic">* Music Connecting People ETS – Anno {expiry_year} *</div>
  </div>
</body>
</html>
"""
def download_image_from_firebase(image_path):
    blob = bucket.blob(image_path)
    
    _, temp_local_filename = tempfile.mkstemp()
    blob.download_to_filename(temp_local_filename)
    
    return temp_local_filename



def generate_ticket_pdf_reportlab(ticket_data, event_data, logo_path):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            rightMargin=72, leftMargin=72, 
                            topMargin=72, bottomMargin=18)
    elements = []

    # Download and add logo
    local_logo_path = download_image_from_firebase(logo_path)
    logo = Image(local_logo_path, width=2*inch, height=1*inch)
    elements.append(logo)
    elements.append(Spacer(1, 12))
    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center alignment

    # Title
    elements.append(Paragraph(f"Ticket for {event_data.get('title')}", title_style))

    # Ticket data
    data = [
        ["Event Details", ""],
        ["Date", event_data.get("date")],
        ["Time", f"{event_data.get('startTime')} - {event_data.get('endTime')}"],
        ["Location", event_data.get("location")],
        ["Lineup", ", ".join(event_data.get("lineup", []))],
        ["", ""],
        ["Ticket Details", ""],
        ["Name", f"{ticket_data.get('first_name')} {ticket_data.get('last_name')}"],
        ["Ticket ID", ticket_data.get("transaction_id")],
        ["Price", f"{ticket_data.get('paid_amount_total')} {ticket_data.get('currency')}"]
    ]

    table = Table(data, colWidths=[200, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 6), (-1, 6), colors.lightgrey),
    ]))

    elements.append(table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer