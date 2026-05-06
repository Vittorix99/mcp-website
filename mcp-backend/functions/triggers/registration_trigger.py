import logging

import requests
from firebase_functions.firestore_fn import on_document_created, Event, DocumentSnapshot

from config.external_services import GENDER_API_URL
from config.firebase_config import region, db
from models import EventParticipant, Membership as MembershipModel
from services.communications.mail_service import EmailMessage, mail_service
from services.core.error_logs_service import log_external_error
from services.events.ticket_service import TicketService
from services.memberships.pass2u_service import Pass2UService
from services.sender.sender_sync import sync_membership_to_sender, sync_participant_to_sender
from utils.events_utils import is_valid_email
from utils.safe_logging import mask_email, redact_sensitive
from utils.templates_mail import get_membership_email_template, get_membership_email_text

logger = logging.getLogger("registration_trigger")

ticket_service = TicketService()


@on_document_created(document="participants/{eventId}/participants_event/{participantId}", region=region)
def on_participant_created(event: Event[DocumentSnapshot | None]):
    # Trigger post-create: arricchisce il partecipante senza bloccare la scrittura principale.
    snapshot = event.data
    if snapshot is None:
        logger.warning("on_participant_created: empty snapshot, skipping")
        return

    participant_id = event.params["participantId"]
    event_id = event.params["eventId"]

    try:
        logger.info("on_participant_created: %s for event %s", participant_id, event_id)

        # Rileggiamo il documento corrente per evitare di lavorare su snapshot ormai obsolete.
        current_doc = snapshot.reference.get()
        if not current_doc.exists:
            logger.warning("on_participant_created: document no longer exists, skipping")
            return
        current_data = current_doc.to_dict() or {}
        ticket_already_sent = current_data.get("ticket_sent", False)

        participant_data = snapshot.to_dict()
        participant_model = EventParticipant.from_firestore(participant_data, doc_id=participant_id)

        # Arricchimento non critico: se il provider gender fallisce, il partecipante resta valido.
        name = (participant_model.name or "").split(" ")[0].strip().lower()
        gender = "N/A"
        probability = 0.0

        if name == "andrea":
            gender = "male"
            probability = 1.0
        elif name:
            try:
                response = requests.get(GENDER_API_URL, params={"name": name})
                response.raise_for_status()
                gender_info = response.json()
                gender = gender_info.get("gender") or "N/A"
                probability = round(float(gender_info.get("probability", 0.0)), 1)
            except Exception as exc:
                logger.warning("on_participant_created: gender API failed: %s", redact_sensitive(str(exc)))

        snapshot.reference.update({"gender": gender, "gender_probability": probability})
        logger.info("on_participant_created: gender=%s (%.1f) for %s", gender, probability, participant_id)

        # Generazione ticket: idempotente lato trigger grazie al flag ticket_sent.
        send = participant_model.send_ticket_on_create
        if ticket_already_sent:
            logger.info("on_participant_created: ticket already sent for %s, skipping", participant_id)
        elif not send:
            logger.info("on_participant_created: send_ticket_on_create=False for %s, skipping", participant_id)
        else:
            result = ticket_service.process_new_ticket(participant_id, participant_data, send)
            if not result.get("success", False):
                ticket_service.log_failed_ticket_email(
                    participant_id,
                    participant_data,
                    result.get("error", "Unknown error"),
                )

        # Sync newsletter: parte solo se il partecipante ha dato consenso e l'email e' valida.
        email = (participant_model.email or "").strip().lower()
        if participant_model.newsletter_consent and is_valid_email(email):
            try:
                event_doc = db.collection("events").document(event_id).get()
                event_title = (event_doc.to_dict() or {}).get("title", "") if event_doc.exists else ""
                sync_participant_to_sender(participant_id, participant_model, event_id, event_title=event_title)
            except Exception as exc:
                logger.error("on_participant_created: Sender sync failed for %s: %s", mask_email(email), redact_sensitive(str(exc)))
                log_external_error(
                    service="Sender",
                    operation="participant_trigger_sync",
                    source="triggers.registration_trigger.on_participant_created",
                    message=str(exc),
                    status_code=0,
                    context={"participant_id": participant_id, "event_id": event_id, "email": email},
                )

    except Exception as exc:
        logger.error("on_participant_created: unhandled error for %s: %s", participant_id, redact_sensitive(str(exc)))
        ticket_service.log_failed_ticket_email(
            participant_id,
            snapshot.to_dict() if snapshot else {},
            str(exc),
        )


@on_document_created(document="memberships/{membershipId}", region=region)
def on_membership_created(event: Event[DocumentSnapshot | None]):
    # Trigger post-create membership: crea wallet, invia tessera e sincronizza provider esterni.
    snapshot = event.data
    if snapshot is None:
        logger.warning("on_membership_created: empty snapshot, skipping")
        return

    membership_id = event.params["membershipId"]

    try:
        logger.info("on_membership_created: %s", membership_id)

        current_doc = snapshot.reference.get()
        if not current_doc.exists:
            logger.warning("on_membership_created: document no longer exists, skipping")
            return
        current_data = current_doc.to_dict() or {}

        # Guard di idempotenza: evita doppio wallet/doppia email in caso di retry del trigger.
        if current_data.get("trigger_processed"):
            logger.info("on_membership_created: already processed for %s, skipping", membership_id)
            return
        snapshot.reference.update({"trigger_processed": True})

        membership_data = snapshot.to_dict()
        membership_model = MembershipModel.from_firestore(membership_data, doc_id=membership_id)

        send_card = bool(membership_model.send_card_on_create)
        if not send_card:
            logger.info("on_membership_created: send_card_on_create=False for %s, skipping card", membership_id)

        # Wallet pass: generato prima dell'email, cosi' la tessera inviata contiene il link wallet.
        wallet_url = current_data.get("wallet_url")
        if current_data.get("wallet_pass_id"):
            logger.info("on_membership_created: wallet pass already exists for %s, skipping", membership_id)
        else:
            try:
                pass2u = Pass2UService()
                wallet = pass2u.create_membership_pass(membership_id, membership_model)
                if wallet:
                    wallet_url = wallet.wallet_url
                    snapshot.reference.update({
                        "wallet_pass_id": wallet.pass_id,
                        "wallet_url": wallet_url,
                    })
                    logger.info("on_membership_created: wallet pass created for %s", membership_id)
            except Exception as exc:
                logger.error("on_membership_created: Pass2U creation failed for %s: %s", membership_id, redact_sensitive(str(exc)))
                log_external_error(
                    service="Pass2U",
                    operation="membership_trigger_create_wallet",
                    source="triggers.registration_trigger.on_membership_created",
                    message=str(exc),
                    status_code=0,
                    context={"membership_id": membership_id},
                )

        # Email tessera: opzionale e separata dal create della membership.
        if send_card and current_data.get("membership_sent"):
            logger.info("on_membership_created: card already sent for %s, skipping", membership_id)
            send_card = False

        if send_card:
            payload = {
                "name": membership_model.name,
                "surname": membership_model.surname,
                "email": membership_model.email,
                "end_date": membership_model.end_date,
                "membership_id": membership_id,
                "wallet_url": wallet_url,
            }
            sent = mail_service.send(
                EmailMessage(
                    to_email=membership_model.email,
                    subject="Tessera Associativa MCP",
                    text_content=get_membership_email_text(payload),
                    html_content=get_membership_email_template(payload),
                    attachment=None,
                )
            )
            if sent:
                snapshot.reference.update({"membership_sent": True})
                logger.info("on_membership_created: card sent to %s", mask_email(membership_model.email))
            else:
                logger.error("on_membership_created: card email failed for %s", membership_id)

        # Sender sync: aggiorna il CRM/newsletter senza influenzare la validita' della membership.
        try:
            email = (membership_model.email or "").strip().lower()
            if is_valid_email(email):
                sync_membership_to_sender(membership_id, membership_model)
        except Exception as exc:
            logger.error("on_membership_created: Sender sync failed for %s: %s", membership_id, redact_sensitive(str(exc)))
            log_external_error(
                service="Sender",
                operation="membership_trigger_sync",
                source="triggers.registration_trigger.on_membership_created",
                message=str(exc),
                status_code=0,
                context={"membership_id": membership_id},
            )

    except Exception as exc:
        logger.error("on_membership_created: unhandled error for %s: %s", membership_id, redact_sensitive(str(exc)))
