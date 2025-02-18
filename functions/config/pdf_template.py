from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch    
from reportlab.platypus import Spacer
from reportlab.platypus import Image
import tempfile
from config.firebase_config import bucket, db
from io import BytesIO
def download_image_from_firebase(image_path):
    blob = bucket.blob(image_path)
    
    _, temp_local_filename = tempfile.mkstemp()
    blob.download_to_filename(temp_local_filename)
    
    return temp_local_filename



def generate_ticket_pdf(ticket_data, event_data, logo_path):
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