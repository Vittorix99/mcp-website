import os
from pathlib import Path

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
from models import EventPurchaseAccessType
from utils.events_utils import map_purchase_mode
from dto.templates import MembershipCardPdfPayload, TicketPdfPayload
from services.templates import render_template

_ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"


def _resolve_local_asset(image_path):
    if not image_path:
        return None
    if os.path.isabs(image_path) and os.path.exists(image_path):
        return image_path
    candidate = _ASSETS_DIR / image_path
    if candidate.exists():
        return str(candidate)
    candidate = _ASSETS_DIR / os.path.basename(image_path)
    if candidate.exists():
        return str(candidate)
    return None



def generate_ticket_pdf(ticket_data, event_data, logo_path):
    purchase_mode = map_purchase_mode(event_data.get("purchaseMode") or event_data.get("type"))

    if purchase_mode in (
        EventPurchaseAccessType.ONLY_MEMBERS,
        EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS,
    ):
        local_logo_path = download_image_from_firebase(logo_path)
        html = generate_member_ticket_pdf_html(ticket_data, event_data, local_logo_path)
        buffer = BytesIO()
        HTML(string=html, base_url=".").write_pdf(buffer)
        buffer.seek(0)
        return buffer

    buffer = generate_ticket_pdf_reportlab(ticket_data=ticket_data, event_data=event_data, logo_path=logo_path)
    return buffer 


def generate_membership_pdf(membership_data, logo_path, pattern_path):
    if not membership_data.get("subscription_valid"):
        return None



    # Scarica solo il logo: il pattern non viene usato nel template HTML corrente.
    local_logo_path = download_image_from_firebase(logo_path)

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
    membership_id = ticket_data.get("membershipId") or None
    date = event_data.get("date")
    time = f"{event_data.get('startTime')} - {event_data.get('endTime')}"
    location = event_data.get("location")
    title = event_data.get("title", "Event Title")
    payload = TicketPdfPayload(
        logo_url=logo_url,
        title=title,
        full_name=full_name,
        membership_id=membership_id,
        date=date or "",
        time=time,
        location=location or "",
    )
    return render_template("pdf/member_ticket.html", payload)

def generate_membership_card_html(member_data, logo_url):
    full_name = f"{member_data.get('name', '')} {member_data.get('surname', '')}".strip()
    membership_id = member_data.get("membership_id", "N/A")
    raw_expiry_date = member_data.get("end_date")
    expiry_date = raw_expiry_date or "N/A"
    expiry_year = ""
    if isinstance(raw_expiry_date, str) and "-" in raw_expiry_date:
        expiry_year = raw_expiry_date.split("-")[-1]

    payload = MembershipCardPdfPayload(
        logo_url=logo_url,
        full_name=full_name,
        membership_id=membership_id,
        expiry_date=expiry_date,
        expiry_year=expiry_year,
    )
    return render_template("pdf/membership_card.html", payload)
def download_image_from_firebase(image_path):
    local_asset = _resolve_local_asset(image_path)
    if local_asset:
        return local_asset

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
