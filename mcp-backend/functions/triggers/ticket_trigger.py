from firebase_functions.firestore_fn import (
  on_document_created,
  on_document_deleted,
  on_document_updated,
  on_document_written,
  Event,
  Change,
  DocumentSnapshot,
)
import requests

from google.cloud import firestore
from services.ticket_service import process_new_ticket, log_failed_ticket_email

from utils.membership_cards import process_new_membership
import datetime
from config.firebase_config import region, db
from utils.events_utils import is_valid_email
from config.external_services import GENDER_API_URL


@on_document_created(document="participants/{eventId}/participants_event/{participantId}", region=region)
def on_participant_created(event: Event[DocumentSnapshot | None]):
    print("🔔 New participant document created!")

    snapshot = event.data
    if snapshot is None:
        print("❌ Document snapshot is empty!")
        return

    try:
        participant_id = event.params["participantId"]
        event_id = event.params["eventId"]
        print(f"📌 New participant registered: {participant_id} for event {event_id}")

        participant_data = snapshot.to_dict()
        print(f"✅ Participant data: {participant_data}")

        # 👉 Gender detection
        name = participant_data.get("name", "").split(" ")[0].strip().lower()
        gender = "N/A"
        probability = 0.0

        if name == "andrea":
            gender = "male"
            probability = 1.0
            print("🎯 Name is 'andrea' → gender forced to 'male'")
        elif name:
            try:
                response = requests.get("https://api.genderize.io", params={"name": name})
                response.raise_for_status()
                gender_info = response.json()
                gender = gender_info.get("gender") or "N/A"
                probability = round(float(gender_info.get("probability", 0.0)), 1)
                print("[DEBUG] Gender API result:", gender_info)
            except Exception as e:
                print(f"[ERROR] Gender API failed: {str(e)}")

        # ✍️ Update gender in Firestore
        snapshot.reference.update({
            "gender": gender,
            "gender_probability": probability
        })
        print(f"✅ Gender saved: {gender} ({probability})")

        # 🎫 Ticket sending
        send = participant_data.get("send_ticket_on_create", True)
        if not send:
            print("⏭️ Skipping ticket send")
        result = process_new_ticket(participant_id, participant_data, send)
        if not result.get("success", False):
            log_failed_ticket_email(participant_id, participant_data, result.get("error", "Unknown error"))

        # 📧 Newsletter consent handling
        email = participant_data.get("email", "").strip().lower()
        newsletter_consent = participant_data.get("newsletterConsent", False)

        if newsletter_consent and is_valid_email(email):
            newsletter_ref = db.collection("newsletter_consents")
            existing = newsletter_ref.where("email", "==", email).limit(1).get()
            if not existing:
                full_data = {
                        "name": participant_data.get("name"),
                        "surname": participant_data.get("surname"),
                        "email": participant_data.get("email"),
                        "phone": participant_data.get("phone"),
                        "birthdate": participant_data.get("birthdate"),
                        "gender": gender,
                        "gender_probability": probability,
                        "event_id": event_id,
                        "participant_id": participant_id,
                        "timestamp": firestore.SERVER_TIMESTAMP,
                        "source": "participant_event",
                    }
                newsletter_ref.add(full_data)
                print(f"📬 Added to newsletter_consents: {email}")
            else:
                print(f"⚠️ Already subscribed: {email}")
        else:
            print("❎ No consent or invalid email")

    except Exception as e:
        print(f"❌ Error in participant trigger: {str(e)}")
        log_failed_ticket_email(participant_id, snapshot.to_dict() if snapshot else {}, str(e))



@on_document_created(document="memberships/{membershipId}", region=region)
def on_membership_created(event: Event[DocumentSnapshot | None]):
    """Trigger when a new membership is created."""
    print("🔔 New membership document created!")

    snapshot = event.data
    if snapshot is None:
        print("❌ Document snapshot is empty!")
        return

    try:
        membership_id = event.params["membershipId"]
        membership_data = snapshot.to_dict()

        print(f"✅ Membership data for {membership_id}: {membership_data}")

        # 🔍 Determina se inviare la tessera basandosi sul campo `send_card_on_create`
        send_card = membership_data.get("send_card_on_create", True)

        result = process_new_membership(membership_id, membership_data, sent_on_create=True)

        if not result.get("success", False):
            print(f"❌ Failed to process membership: {result.get('error', 'Unknown error')}")
        else:
            print(f"✅ Membership processed successfully, PDF URL: {result['pdf_url']}")

    except Exception as e:
        print(f"❌ Error handling membership creation: {str(e)}")
