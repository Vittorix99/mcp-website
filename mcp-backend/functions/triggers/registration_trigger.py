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
from services.mailer_lite import SubscribersClient


@on_document_created(document="participants/{eventId}/participants_event/{participantId}", region=region)
def on_participant_created(event: Event[DocumentSnapshot | None]):
    print("New participant document created")

    snapshot = event.data
    if snapshot is None:
        print("Document snapshot is empty")
        return

    try:
        participant_id = event.params["participantId"]
        event_id = event.params["eventId"]
        print(f"New participant registered: {participant_id} for event {event_id}")

        participant_data = snapshot.to_dict()
        print(f"Participant data: {participant_data}")

        # Gender detection
        name = participant_data.get("name", "").split(" ")[0].strip().lower()
        gender = "N/A"
        probability = 0.0

        if name == "andrea":
            gender = "male"
            probability = 1.0
            print("Name is 'andrea' -> gender forced to 'male'")
        elif name:
            try:
                response = requests.get(GENDER_API_URL, params={"name": name})
                response.raise_for_status()
                gender_info = response.json()
                gender = gender_info.get("gender") or "N/A"
                probability = round(float(gender_info.get("probability", 0.0)), 1)
                print("[DEBUG] Gender API result:", gender_info)
            except Exception as e:
                print(f"[ERROR] Gender API failed: {str(e)}")

        # Update gender in Firestore
        snapshot.reference.update({
            "gender": gender,
            "gender_probability": probability
        })
        print(f"Gender saved: {gender} ({probability})")

        # Ticket sending
        send = participant_data.get("send_ticket_on_create", True)
        if not send:
            print("Skipping ticket send")
        result = process_new_ticket(participant_id, participant_data, send)
        if not result.get("success", False):
            log_failed_ticket_email(participant_id, participant_data, result.get("error", "Unknown error"))

        # Newsletter consent handling
        email = participant_data.get("email", "").strip().lower()
        newsletter_consent = participant_data.get("newsletterConsent", False)

        consent_timestamp = None
        if newsletter_consent and is_valid_email(email):
            # Newsletter consents insertion disabled for now.
            print("Skipping newsletter_consents insert")
        else:
            print("No consent or invalid email")

        # MailerLite sync for newsletter consent
        if newsletter_consent and is_valid_email(email):
            try:
                sync_service = SubscribersClient()
                membership_id = participant_data.get("membershipId") or participant_data.get("membership_id")
                fields = {
                    "name": participant_data.get("name"),
                    "last_name": participant_data.get("surname"),
                    "phone": participant_data.get("phone"),
                    "birthdate": participant_data.get("birthdate"),
                    "gender": gender,
                    "membership_id": membership_id,
                    "participant_id": participant_id,
                }
                opted_in_at = None
                if consent_timestamp:
                    try:
                        opted_in_at = consent_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        opted_in_at = None
                sync_service.sync_newsletter_consent(email, fields, opted_in_at=opted_in_at)
            except Exception as e:
                print(f"MailerLite sync failed for {email}: {e}")

    except Exception as e:
        print(f"Error in participant trigger: {str(e)}")
        log_failed_ticket_email(participant_id, snapshot.to_dict() if snapshot else {}, str(e))



@on_document_created(document="memberships/{membershipId}", region=region)
def on_membership_created(event: Event[DocumentSnapshot | None]):
    """Trigger when a new membership is created."""
    print("New membership document created")

    snapshot = event.data
    if snapshot is None:
        print("Document snapshot is empty")
        return

    try:
        membership_id = event.params["membershipId"]
        membership_data = snapshot.to_dict()

        print(f"Membership data for {membership_id}: {membership_data}")

        # Determine whether to send the card based on `send_card_on_create`
        send_card = membership_data.get("send_card_on_create") is True
        if not send_card:
            print("Skipping membership email send (send_card_on_create=False)")

        result = process_new_membership(membership_id, membership_data, sent_on_create=send_card)

        if not result.get("success", False):
            print(f"Failed to process membership: {result.get('error', 'Unknown error')}")
        else:
            print(f"Membership processed successfully, PDF URL: {result['pdf_url']}")

        # MailerLite sync for memberships
        try:
            email = (membership_data.get("email") or "").strip().lower()
            if is_valid_email(email):
                sync_service = SubscribersClient()
                fields = {
                    "name": membership_data.get("name"),
                    "last_name": membership_data.get("surname"),
                    "phone": membership_data.get("phone"),
                    "birthdate": membership_data.get("birthdate"),
                    "membership_id": membership_id,
                }
                sync_service.sync_membership(email, fields)
        except Exception as e:
            print(f"MailerLite sync failed for membership {membership_id}: {e}")

    except Exception as e:
        print(f"Error handling membership creation: {str(e)}")
