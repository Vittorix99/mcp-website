from google.cloud import firestore
import os
from services.mail_service import gmail_send_email_template
from config.email_templates import get_ticket_email_template
import sys
from datetime import datetime
from config.pdf_template import generate_ticket_pdf
from config.firebase_config import db, bucket, cors





def process_new_ticket(ticket_id, ticket_data):
    """Handles retrieving event details, saving a PDF, and sending an email with the ticket."""
    try:
        event_id = ticket_data.get("event_id")
        if not event_id:
            print("⚠️ Missing event_id in ticket!")
            return {"success": False, "error": "Missing event_id in ticket"}

        # Retrieve event details from Firestore
        event_ref = db.collection("events").document(event_id)
        event_doc = event_ref.get()

        if not event_doc.exists:
            print(f"⚠️ Event with ID {event_id} not found!")
            return {"success": False, "error": f"Event with ID {event_id} not found"}

        event_data = event_doc.to_dict()
        print(f"📅 Event retrieved: {event_data}")
        
        brand_logo_path = "logos/logonew.png"

        # Generate PDF ticket
        pdf_buffer = generate_ticket_pdf(ticket_data, event_data, brand_logo_path)
        name_surname = f"{ticket_data.get('first_name')}_{ticket_data.get('last_name')}"
        title_event = event_data.get("title")   


        # 🔥 Save PDF to Firebase Storage
        pdf_filename = f"tickets/{title_event}/{name_surname}_ticket.pdf"
        blob = bucket.blob(pdf_filename)
        blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")
        pdf_url = blob.public_url  # Public URL to download the ticket

        print(f"✅ Ticket PDF saved to Storage: {pdf_url}")

        # Prepare email content
        user_email = ticket_data.get("email")
        subject = f"🎟️ Your Ticket for {event_data.get('title')}"

        html_content = get_ticket_email_template(ticket_data, event_data, pdf_url)  # Pass PDF URL
        text_content = f"""
        Thank you for your purchase! 🎉
        
        Event: {event_data.get("title")}
        Date: {event_data.get("date")}
        Location: {event_data.get("location")}
        
        Ticket Details:
        - Name: {ticket_data.get("first_name")} {ticket_data.get("last_name")}
        - Ticket ID: {ticket_id}
        - Paid: {ticket_data.get("paid_amount_total")} {ticket_data.get("currency")}
        
        Please find your ticket attached to this email. You can also download it here:
        {pdf_url}

        See you there! 🎶
        """
        html_content = get_ticket_email_template(ticket_data, event_data)
        text_content = f"""
        Thank you for your purchase! 🎉
        
        Event: {event_data.get("title")}
        Date: {event_data.get("date")}
        Location: {event_data.get("location")}
        
        Ticket Details:
        - Name: {ticket_data.get("first_name")} {ticket_data.get("last_name")}
        - Ticket ID: {ticket_id}
        - Paid: {ticket_data.get("paid_amount_total")} {ticket_data.get("currency")}
        
        Your ticket is attached to this email.

        See you there! 🎶
        """

        # Send email with PDF attachment
        sent_message = gmail_send_email_template(user_email, subject, text_content, html_content, pdf_buffer, f"ticket_{name_surname}.pdf")

        if sent_message is not None:
            # ✅ Update Firestore document: Mark ticket as sent
            db.collection("tickets").document(ticket_id).update({
                "ticket_sent": True,
                "ticket_pdf_url": pdf_url  # Store the PDF URL in Firestore
            })
            print(f"✅ Ticket email sent to {user_email}")
            return {"success": True, "message": "Email sent successfully", "pdf_url": pdf_url}
        else:
            print(f"❌ Error sending email to {user_email}")
            return {"success": False, "error": "Failed to send email"}
    
    except Exception as e:
        print(f"❌ Error processing ticket {ticket_id}: {str(e)}")
        return {"success": False, "error": str(e)}

def log_failed_ticket_email(ticket_id, ticket_data, error_message):
    """Logs a failed ticket email attempt in the 'contact_messages' collection"""
    try:
        contact_message = {
            "subject": "⚠️ Ticket Email Failed",
            "message": f"Ticket ID {ticket_id} for {ticket_data.get('email')} was not sent correctly.",
            "ticket_id": ticket_id,
            "payer_email": ticket_data.get("email"),
            "first_name": ticket_data.get("first_name"),
            "last_name": ticket_data.get("last_name"),
            "error_message": error_message,
            "timestamp": datetime.now()
        }
        
        db.collection("contact_messages").add(contact_message)
        print(f"✅ Logged failed ticket email for {ticket_id}")
    
    except Exception as e:
        print(f"❌ Failed to log contact message for {ticket_id}: {str(e)}")
        
        
    
def create_ticket_service(ticket_data, admin_uid):
    """Create a new ticket"""
    required_fields = ['first_name', 'last_name', 'email', 'paid_amount_total', 'currency', 'transaction_id', 'event_id']
    if not all(field in ticket_data for field in required_fields):
        raise ValueError('Missing required fields')

    ticket = {
        'first_name': ticket_data['first_name'],
        'last_name': ticket_data['last_name'],
        'email': ticket_data['email'],
        'paid_amount_total': float(ticket_data['paid_amount_total']),
        'net_amount': float(ticket_data.get('net_amount', 0)),
        'paypal_fee': float(ticket_data.get('paypal_fee', 0)),
        'currency': ticket_data['currency'],
        'transaction_id': ticket_data['transaction_id'],
        'event_id': ticket_data['event_id'],
        'order_status': ticket_data.get('order_status', 'COMPLETED'),
        'timestamp': firestore.SERVER_TIMESTAMP,
        'ticket_sent': False,
        'created_by': admin_uid
    }

    doc_ref = db.collection('tickets').add(ticket)
    ticket_id = doc_ref[1].id
    
    # Process the new ticket
    process_result = process_new_ticket(ticket_id, ticket)
    
    if not process_result['success']:
        log_failed_ticket_email(ticket_id, ticket, process_result['error'])

    return {
        'message': 'Ticket created successfully',
        'ticket_id': ticket_id,
        'ticket': ticket,
        'process_result': process_result
    }

def get_tickets_service(ticket_id=None, event_id=None):
    """Get all tickets or a specific ticket"""
    if ticket_id:
        ticket_doc = db.collection('tickets').document(ticket_id).get()
        if not ticket_doc.exists:
            raise ValueError('Ticket not found')
        ticket_data = ticket_doc.to_dict()
        ticket_data['id'] = ticket_doc.id
        return ticket_data
    elif event_id:
        tickets_ref = db.collection('tickets').where('event_id', '==', event_id).get()
    else:
        tickets_ref = db.collection('tickets').get()

    tickets = []
    for doc in tickets_ref:
        ticket_data = doc.to_dict()
        ticket_data['id'] = doc.id
        tickets.append(ticket_data)
    return {'tickets': tickets}

def update_ticket_service(ticket_data, admin_uid):
    """Update an existing ticket"""
    ticket_id = ticket_data.pop('id', None)
    if not ticket_id:
        raise ValueError('Missing ticket ID')

    ticket_ref = db.collection('tickets').document(ticket_id)
    ticket_doc = ticket_ref.get()
    if not ticket_doc.exists:
        raise ValueError('Ticket not found')

    # Ensure certain fields can't be updated
    protected_fields = ['transaction_id', 'event_id', 'timestamp', 'created_by']
    for field in protected_fields:
        if field in ticket_data:
            del ticket_data[field]

    # Convert numeric fields to float
    numeric_fields = ['paid_amount_total', 'net_amount', 'paypal_fee']
    for field in numeric_fields:
        if field in ticket_data:
            ticket_data[field] = float(ticket_data[field])

    ticket_data['updated_at'] = firestore.SERVER_TIMESTAMP
    ticket_data['updated_by'] = admin_uid

    ticket_ref.update(ticket_data)

    return {
        'message': 'Ticket updated successfully',
        'ticket_id': ticket_id
    }

def delete_ticket_service(ticket_id):
    """Delete a ticket"""
    ticket_ref = db.collection('tickets').document(ticket_id)
    ticket_doc = ticket_ref.get()
    
    if not ticket_doc.exists:
        raise ValueError('Ticket not found')

    ticket_ref.delete()

    return {
        'message': 'Ticket deleted successfully',
        'ticket_id': ticket_id
    }
    
    
def send_pdf_ticket_service(ticket_id):
    """Sends the PDF ticket to the user's email"""
    try:
        # Fetch the ticket data
        ticket_doc = db.collection("tickets").document(ticket_id).get()
        if not ticket_doc.exists:
            return {"success": False, "error": "Ticket not found"}

        ticket_data = ticket_doc.to_dict()
        
        # Check if PDF already exists
        if "ticket_pdf_url" in ticket_data and ticket_data["ticket_pdf_url"]:
            pdf_url = ticket_data["ticket_pdf_url"]
        else:
            # If PDF doesn't exist, create it
            event_id = ticket_data.get("event_id")
            if not event_id:
                return {"success": False, "error": "Missing event_id in ticket"}

            event_doc = db.collection("events").document(event_id).get()
            if not event_doc.exists:
                return {"success": False, "error": f"Event with ID {event_id} not found"}

            event_data = event_doc.to_dict()
            
            # Generate and save PDF
            pdf_buffer = generate_ticket_pdf(ticket_data, event_data)
            name_surname = f"{ticket_data.get('first_name')}_{ticket_data.get('last_name')}"
            title_event = event_data.get("title")   

            pdf_filename = f"tickets/{title_event}/{name_surname}_ticket.pdf"
            blob = bucket.blob(pdf_filename)
            blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")
            pdf_url = blob.public_url

            # Update ticket with PDF URL
            db.collection("tickets").document(ticket_id).update({
                "ticket_pdf_url": pdf_url
            })

        # Prepare email content
        user_email = ticket_data.get("email")
        subject = f"🎟️ Your Ticket (Resend)"
        
        html_content = get_ticket_email_template(ticket_data, event_data, pdf_url)
        text_content = f"""
        Here's your ticket for the event!
        
        You can download your ticket using this link: {pdf_url}

        See you there! 🎶
        """

        # Send email with PDF attachment
        sent_message = gmail_send_email_template(user_email, subject, text_content, html_content)

        if sent_message is not None:
            return {"success": True, "message": "Ticket PDF sent successfully"}
        else:
            return {"success": False, "error": "Failed to send email"}

    except Exception as e:
        print(f"❌ Error sending PDF ticket {ticket_id}: {str(e)}")
        return {"success": False, "error": str(e)}

def download_pdf_ticket_service(ticket_id):
    """Returns the PDF ticket for download"""
    try:
        # Fetch the ticket data
        ticket_doc = db.collection("tickets").document(ticket_id).get()
        if not ticket_doc.exists:
            return None, "Ticket not found"

        ticket_data = ticket_doc.to_dict()
        
        # Check if PDF already exists
        if "ticket_pdf_url" in ticket_data and ticket_data["ticket_pdf_url"]:
            pdf_url = ticket_data["ticket_pdf_url"]
            blob = bucket.blob(pdf_url.split("/o/")[1].split("?")[0])
            pdf_content = blob.download_as_bytes()
            return pdf_content, None
        else:
            # If PDF doesn't exist, create it
            event_id = ticket_data.get("event_id")
            if not event_id:
                return None, "Missing event_id in ticket"

            event_doc = db.collection("events").document(event_id).get()
            if not event_doc.exists:
                return None, f"Event with ID {event_id} not found"

            event_data = event_doc.to_dict()
            
            # Generate PDF
            pdf_buffer = generate_ticket_pdf(ticket_data, event_data)
            name_surname = f"{ticket_data.get('first_name')}_{ticket_data.get('last_name')}"
            title_event = event_data.get("title")   

            pdf_filename = f"tickets/{title_event}/{name_surname}_ticket.pdf"
            blob = bucket.blob(pdf_filename)
            blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")
            pdf_url = blob.public_url

            # Update ticket with PDF URL
            db.collection("tickets").document(ticket_id).update({
                "ticket_pdf_url": pdf_url
            })

            return pdf_buffer.getvalue(), None

    except Exception as e:
        print(f"❌ Error downloading PDF ticket {ticket_id}: {str(e)}")
        return None, str(e)
    
    
def create_new_pdf_ticket_service(ticket_id, admin_uid):
            """Create a new PDF ticket if it doesn't already exist"""
            try:
                ticket_doc = db.collection("tickets").document(ticket_id).get()
                if not ticket_doc.exists:
                    return {"success": False, "error": "Ticket not found"}

                ticket_data = ticket_doc.to_dict()
                
                # Check if PDF already exists
                if "ticket_pdf_url" in ticket_data and ticket_data["ticket_pdf_url"]:
                    return {"success": False, "error": "PDF ticket already exists for this ticket"}

                event_id = ticket_data.get("event_id")
                if not event_id:
                    return {"success": False, "error": "Missing event_id in ticket"}

                event_doc = db.collection("events").document(event_id).get()
                if not event_doc.exists:
                    return {"success": False, "error": f"Event with ID {event_id} not found"}

                event_data = event_doc.to_dict()
                
                # Generate PDF
                pdf_buffer = generate_ticket_pdf(ticket_data, event_data)
                name_surname = f"{ticket_data.get('first_name')}_{ticket_data.get('last_name')}"
                title_event = event_data.get("title")   

                pdf_filename = f"tickets/{title_event}/{name_surname}_ticket.pdf"
                blob = bucket.blob(pdf_filename)
                blob.upload_from_string(pdf_buffer.getvalue(), content_type="application/pdf")
                pdf_url = blob.public_url

                # Update ticket with PDF URL
                db.collection("tickets").document(ticket_id).update({
                    "ticket_pdf_url": pdf_url,
                    "pdf_created_by": admin_uid,
                    "pdf_created_at": firestore.SERVER_TIMESTAMP
                })

                return {"success": True, "message": "PDF ticket created successfully", "pdf_url": pdf_url}

            except Exception as e:
                print(f"❌ Error creating new PDF ticket {ticket_id}: {str(e)}")
                return {"success": False, "error": str(e)}

def delete_existing_pdf_ticket_service(ticket_id, admin_uid):
    """Delete an existing PDF ticket from storage"""
    try:
        ticket_doc = db.collection("tickets").document(ticket_id).get()
        if not ticket_doc.exists:
            return {"success": False, "error": "Ticket not found"}

        ticket_data = ticket_doc.to_dict()
        
        if "ticket_pdf_url" not in ticket_data or not ticket_data["ticket_pdf_url"]:
            return {"success": False, "error": "No PDF ticket found for this ticket"}

        pdf_url = ticket_data["ticket_pdf_url"]
        blob = bucket.blob(pdf_url.split("/o/")[1].split("?")[0])
        
        # Delete the PDF from storage
        blob.delete()

        # Update ticket to remove PDF URL
        db.collection("tickets").document(ticket_id).update({
            "ticket_pdf_url": firestore.DELETE_FIELD,
            "pdf_deleted_by": admin_uid,
            "pdf_deleted_at": firestore.SERVER_TIMESTAMP
        })

        return {"success": True, "message": "PDF ticket deleted successfully"}

    except Exception as e:
        print(f"❌ Error deleting existing PDF ticket {ticket_id}: {str(e)}")
        return {"success": False, "error": str(e)}