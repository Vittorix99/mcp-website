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
from services.events.ticket_service import TicketService
from services.events.documents_service import DocumentsService
from services.communications.mail_service import EmailAttachment, EmailMessage, mail_service
from io import BytesIO
import datetime
from config.firebase_config import region, db
from dto import MembershipDTO
from utils.events_utils import is_valid_email
from utils.templates_mail import get_membership_email_template, get_membership_email_text
from config.external_services import GENDER_API_URL
from models import EventParticipant, Membership as MembershipModel
from services.mailer_lite import SubscribersClient
from services.sender.sender_sync import sync_participant_to_sender, sync_membership_to_sender
from services.core.error_logs_service import log_external_error


ticket_service = TicketService()


def _coerce_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", ""}:
            return False
    return bool(value)


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
        result = ticket_service.process_new_ticket(participant_id, participant_data, send)
        if not result.get("success", False):
            ticket_service.log_failed_ticket_email(
                participant_id,
                participant_data,
                result.get("error", "Unknown error"),
            )

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

        # Sender sync for newsletter consent
        if newsletter_consent and is_valid_email(email):
            try:
                participant_model = EventParticipant.from_firestore(participant_data, doc_id=participant_id)
                event_doc = db.collection("events").document(event_id).get()
                event_title = (event_doc.to_dict() or {}).get("title", "") if event_doc.exists else ""
                sync_participant_to_sender(participant_id, participant_model, event_id, event_title=event_title)
            except Exception as e:
                print(f"Sender sync failed for {email}: {e}")
                log_external_error(
                    service="Sender",
                    operation="participant_trigger_sync",
                    source="triggers.registration_trigger.on_participant_created",
                    message=str(e),
                    status_code=0,
                    context={"participant_id": participant_id, "event_id": event_id, "email": email},
                )

    except Exception as e:
        print(f"Error in participant trigger: {str(e)}")
        ticket_service.log_failed_ticket_email(
            participant_id,
            snapshot.to_dict() if snapshot else {},
            str(e),
        )



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
        send_card = _coerce_bool(
            membership_data.get("send_card_on_create", membership_data.get("sendCardOnCreate")),
            default=False,
        )
        if not send_card:
            print("Skipping membership email send (send_card_on_create=False)")

        membership_dto = MembershipDTO.from_payload(membership_data)

        # [WALLET MIGRATION] Generazione PDF tessera commentata: sostituita da Pass2U wallet
        # documents_service = DocumentsService()
        # document = None
        # card_url = membership_data.get("card_url")
        # storage_path = membership_data.get("card_storage_path")
        #
        # if not card_url:
        #     try:
        #         document = documents_service.create_membership_card(membership_id, membership_dto)
        #     except Exception as exc:
        #         print(f"Failed to generate membership card: {exc}")
        #     else:
        #         card_url = document.public_url
        #         storage_path = document.storage_path
        #         snapshot.reference.update(
        #             {
        #                 "card_url": card_url,
        #                 "card_storage_path": storage_path,
        #                 "membership_sent": False,
        #             }
        #         )
        #         print(f"Membership processed successfully, PDF URL: {card_url}")
        # else:
        #     print("Membership already has a card_url, skipping card generation")

        wallet_url = None
        try:
            from services.memberships.pass2u_service import Pass2UService
            pass2u = Pass2UService()
            membership_model = MembershipModel(
                name=membership_data.get("name", ""),
                surname=membership_data.get("surname", ""),
                email=membership_data.get("email", ""),
                end_date=membership_data.get("end_date", ""),
                start_date=membership_data.get("start_date", ""),
                birthdate=membership_data.get("birthdate", ""),
                phone=membership_data.get("phone", ""),
                subscription_valid=membership_data.get("subscription_valid", True),
                membership_type=membership_data.get("membership_type", "manual"),
                membership_fee=membership_data.get("membership_fee"),
            )
            wallet = pass2u.create_membership_pass(membership_id, membership_model)
            if wallet:
                wallet_url = wallet.wallet_url
                snapshot.reference.update({
                    "wallet_pass_id": wallet.pass_id,
                    "wallet_url": wallet_url,
                })
                print(f"[Pass2U] Wallet pass created: {wallet_url}")
        except Exception as e:
            print(f"[Pass2U] Wallet creation failed (non-blocking): {e}")
            log_external_error(
                service="Pass2U",
                operation="membership_trigger_create_wallet",
                source="triggers.registration_trigger.on_membership_created",
                message=str(e),
                status_code=0,
                context={"membership_id": membership_id},
            )

        if send_card:
            payload = membership_dto.to_payload()
            payload["membership_id"] = membership_id
            payload["wallet_url"] = wallet_url
            subject = "Tessera Associativa MCP"
            html_content = get_membership_email_template(payload)
            text_content = get_membership_email_text(payload)

            # [WALLET MIGRATION] Recupero PDF e costruzione allegato commentati
            # pdf_buffer = document.buffer if document and document.buffer else None
            # if pdf_buffer is None:
            #     if not storage_path and "memberships/cards/" in (card_url or ""):
            #         storage_path = card_url[card_url.find("memberships/cards/"):]
            #     if storage_path:
            #         blob = documents_service.storage.blob(storage_path)
            #         pdf_buffer = BytesIO(blob.download_as_bytes())
            #
            # attachment = None
            # if pdf_buffer:
            #     attachment = EmailAttachment(
            #         content=pdf_buffer.getvalue(),
            #         filename=f"{membership_data.get('name', 'user')}_{membership_data.get('surname', '')}_{membership_id}_tessera.pdf",
            #     )

            sent = mail_service.send(
                EmailMessage(
                    to_email=membership_data.get("email"),
                    subject=subject,
                    text_content=text_content,
                    html_content=html_content,
                    attachment=None,
                )
            )
            if sent:
                snapshot.reference.update({"membership_sent": True})
                print(f"Membership card sent to {membership_data.get('email')}")
            else:
                print("Membership card email failed to send")

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

        # Sender sync for memberships
        try:
            email = (membership_data.get("email") or "").strip().lower()
            if is_valid_email(email):
                membership_model_for_sender = MembershipModel.from_firestore(membership_data, doc_id=membership_id)
                sync_membership_to_sender(membership_id, membership_model_for_sender)
        except Exception as e:
            print(f"Sender sync failed for membership {membership_id}: {e}")
            log_external_error(
                service="Sender",
                operation="membership_trigger_sync",
                source="triggers.registration_trigger.on_membership_created",
                message=str(e),
                status_code=0,
                context={"membership_id": membership_id},
            )

    except Exception as e:
        print(f"Error handling membership creation: {str(e)}")
