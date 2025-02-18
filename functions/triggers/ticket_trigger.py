from firebase_functions import firestore_fn
from google.cloud import firestore
from services.ticket_service import process_new_ticket, log_failed_ticket_email

import os
import sys
import datetime

db = firestore.Client()


@firestore_fn.on_document_created(document="tickets/{ticketId}")
def on_ticket_created(event: firestore_fn.Event[firestore_fn.DocumentSnapshot | None]):
    """Trigger when a new ticket is created."""
    print("🔔 New ticket created!")

    snapshot = event.data
    if snapshot is None:
        print("❌ Document no longer exists!")
        return

    try:
        # 🔥 Extract ticketId manually from event.params
        ticket_id = event.params["ticketId"]
        print(f"📌 Ticket ID: {ticket_id}")

        ticket_data = snapshot.to_dict()
        
        order_status = ticket_data.get("order_status")
        if order_status != "COMPLETED":
            print(f"⚠️ Order status is not COMPLETED: {order_status}")
            return
        print(f"✅ New ticket received: {ticket_data}")

        # ✅ Process ticket and send email
        result = process_new_ticket(ticket_id, ticket_data)

        if not result.get("success", False):
            # ❌ If sending failed, log the issue in `contact_messages`
            log_failed_ticket_email(ticket_id, ticket_data, result.get("error", "Unknown error"))

    except Exception as e:
        print(f"❌ Error processing ticket trigger: {str(e)}")
        log_failed_ticket_email(ticket_id, ticket_data, str(e)) 