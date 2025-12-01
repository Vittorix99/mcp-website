


import os
import logging
import json
import requests
import pprint
from flask import jsonify
from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient
from paypalserversdk.controllers.orders_controller import OrdersController
from paypalserversdk.controllers.payments_controller import PaymentsController
from paypalserversdk.models.amount_with_breakdown import AmountWithBreakdown
from paypalserversdk.models.checkout_payment_intent import CheckoutPaymentIntent
from paypalserversdk.models.order_request import OrderRequest
from paypalserversdk.models.purchase_unit_request import PurchaseUnitRequest
from paypalserversdk.api_helper import ApiHelper
from paypalserversdk.configuration import Environment
from config.firebase_config import db
from utils.events_utils import is_minor, calculate_end_of_year as utils_calc_eoy
from google.cloud import firestore
from datetime import datetime
from config.purchase_types import PurchaseTypes

# --- Logging Configuration ---
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("CaptureOrderService")


class PaymentService:
    """Wrapper per la gestione degli ordini e dei pagamenti (creazione, cattura, salvataggi Firestore).
    Mantiene la compatibilità con le funzioni esistenti tramite delegatori a fondo file.
    """

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Inizializza PayPal client e controller
        self.paypal_client = PaypalServersdkClient(
            client_credentials_auth_credentials=ClientCredentialsAuthCredentials(
                o_auth_client_id=(
                    os.getenv("PAYPAL_CLIENT_ID")
                    if os.getenv("PAYPAL_ENV") == "sandbox"
                    else os.getenv("PAYPAL_LIVE_CLIENT_ID")
                ),
                o_auth_client_secret=(
                    os.getenv("PAYPAL_CLIENT_SECRET")
                    if os.getenv("PAYPAL_ENV") == "sandbox"
                    else os.getenv("PAYPAL_LIVE_CLIENT_SECRET")
                ),
            ),
            environment=Environment.SANDBOX
            if os.getenv("PAYPAL_ENV") == "sandbox"
            else Environment.PRODUCTION,
        )
        self.orders_controller: OrdersController = self.paypal_client.orders
        self.payments_controller: PaymentsController = self.paypal_client.payments

    # ------------------ Helpers ------------------
    @staticmethod
    def truncate_float(value, decimals=1):
        factor = 10 ** decimals
        return int(float(value) * factor) / factor

    @staticmethod
    def calculate_end_of_year(date_str):
        """Converte una ISO date in stringa gg-mm-YYYY di fine anno. Fallback a utils se fallisce."""
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", ""))
            return f"31-12-{dt.year}"
        except Exception:
            logging.exception("Failed to calculate end of year, using utils")
            try:
                return utils_calc_eoy(date_str)
            except Exception:
                return None

    @staticmethod
    def _normalize_text(value: str) -> str:
        import unicodedata
        if not value:
            return ""
        s = str(value).strip().lower()
        s = unicodedata.normalize("NFD", s)
        s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
        s = " ".join(s.split())
        return s

    @staticmethod
    def _normalize_email(value: str) -> str:
        return str(value).strip().lower() if value else ""

    @staticmethod
    def _normalize_phone(value: str) -> str:
        if not value:
            return ""
        import re
        s = str(value).strip().replace(" ", "")
        # Remove any leading alphabetic (non-numeric, non-+) characters from the start (e.g. 'IT', 'it', 'abc')
        s = re.sub(r"^[A-Za-z]+", "", s)
        return s
    
    
    def enforce_only_members_if_required(self, cart_item):
        """Se l'evento ha onlyMembers=True, verifica che TUTTI i partecipanti siano membri attivi.
        Altrimenti solleva ValueError. Va chiamato PRIMA di ramificare per purchase_type.
        """
        ev_id = cart_item.get("eventId")
        participants = cart_item.get("participants", [])
        print("[ONLYMEM] enter enforce_only_members_if_required ev_id=", ev_id)
        print("[ONLYMEM] participants_count=", len(participants))
        if not ev_id or not participants:
            print("[ONLYMEM] missing ev_id or participants -> skip check")
            return

        ev_doc = db.collection("events").document(ev_id).get()
        print("[ONLYMEM] event doc exists? ", ev_doc.exists)
        if not ev_doc.exists:
            raise ValueError("Invalid event")
        ev_data = ev_doc.to_dict() or {}
        print("[ONLYMEM] event.active=", ev_data.get("active"))
        print("[ONLYMEM] event.onlyMembers=", ev_data.get("onlyMembers"))
        if not ev_data.get("active", False):
            raise ValueError("Invalid or inactive event")

        if not bool(ev_data.get("onlyMembers", False)):
            print("[ONLYMEM] onlyMembers is False -> no constraints, exit")
            return  # nessun vincolo, esci

        non_members = []
        identity_mismatches = []
        for p in participants:
            raw_email = self._normalize_email(p.get("email"))
            raw_phone = self._normalize_phone(p.get("phone"))
            n_name = self._normalize_text(p.get("name"))
            n_surname = self._normalize_text(p.get("surname"))
            display = raw_email or raw_phone or f"{p.get('name','')} {p.get('surname','')}".strip()
            print(f"[ONLYMEM] checking participant email={raw_email} phone={raw_phone} nameNorm={n_name} surnameNorm={n_surname}")

            is_member = False
            if raw_email:
                try:
                    # Cerca membership attive per email
                    mem_by_email = list(
                        db.collection("memberships")
                          .where("subscription_valid", "==", True)
                          .where("email", "==", raw_email)
                          .stream()
                    )
                    print(f"[ONLYMEM] email lookup count={len(mem_by_email)}")
                    if mem_by_email:
                        for mdoc in mem_by_email:
                            md = mdoc.to_dict() or {}
                            m_name_norm = self._normalize_text(md.get("name"))
                            m_surname_norm = self._normalize_text(md.get("surname"))
                            if m_name_norm != n_name or m_surname_norm != n_surname:
                                identity_mismatches.append(display)
                                print(
                                    f"[ONLYMEM] ⚠️ identity mismatch for {raw_email}: got '{n_name} {n_surname}', member has '{m_name_norm} {m_surname_norm}'"
                                )
                                # mismatch: conta come NON conforme, non continuare altri check per questa persona
                                is_member = False
                                break
                            else:
                                is_member = True
                                break
                    else:
                        print("[ONLYMEM] no active membership found by email")
                except Exception:
                    logger.exception("[ONLYMEM] email lookup failed")

            if (not is_member) and raw_phone and not raw_email:
                # fallback solo se NON abbiamo email valida o match per email
                try:
                    mem_by_phone = list(
                        db.collection("memberships")
                          .where("subscription_valid", "==", True)
                          .where("phone", "==", raw_phone)
                          .stream()
                    )
                    print(f"[ONLYMEM] phone lookup count={len(mem_by_phone)}")
                    # Per il telefono non possiamo validare email, ma validiamo nome+cognome
                    if mem_by_phone:
                        for mdoc in mem_by_phone:
                            md = mdoc.to_dict() or {}
                            m_name_norm = self._normalize_text(md.get("name"))
                            m_surname_norm = self._normalize_text(md.get("surname"))
                            if m_name_norm == n_name and m_surname_norm == n_surname:
                                is_member = True
                                break
                except Exception:
                    logger.exception("[ONLYMEM] phone lookup failed")

            if not is_member:
                non_members.append(display)

        if identity_mismatches:
            raise ValueError(
                "Event is members-only. The following participants use an email already associated with a member but name/surname do not match: "
                + ", ".join(identity_mismatches)
            )

        print("[ONLYMEM] non_members computed=", non_members)
        if non_members:
            raise ValueError(f"Event is members-only. Non-members found: {non_members}")
    
    def validate_capture_payload(self, order_data):
        """
        Verifica che il payload PayPal contenga almeno una capture COMPLETED con id valido.
        Funziona sia per pagamenti PayPal "classici" che Apple Pay (che passano comunque dalle captures).
        Ritorna (True, cap0) se valido, altrimenti (False, error_json).
        """
        top_status = (order_data.get("status") or "").upper()
        try:
            pu0 = (order_data.get("purchase_units") or [])[0]
            cap0 = ((pu0.get("payments") or {}).get("captures") or [])[0]
        except Exception:
            logger.exception("Malformed capture payload")
            return False, {"error": "malformed_capture", "message": "Malformed capture payload"}

        cap_status = (cap0.get("status") or "").upper()
        cap_id = cap0.get("id")
        final_flag = bool(cap0.get("final_capture", False))

        if top_status != "COMPLETED" or cap_status != "COMPLETED" or not cap_id:
            logger.error("Payment not completed: order=%s capture=%s id=%s", top_status, cap_status, cap_id)
            return False, {
                "error": "payment_not_completed",
                "message": f"Payment not completed (order={top_status}, capture={cap_status}, id={cap_id}).",
            }

        if not final_flag:
            logger.warning("Capture is not marked as final_capture=True (id=%s)", cap_id)

        return True, cap0

    # ------------------ Validazioni ------------------
    def validate_event_item_fast(self, item):
        ev_id = item.get("eventId")
        participants = item.get("participants", [])
        price = item.get("price")
        qty = item.get("quantity")
        fee = item.get("fee", 0)

        if not ev_id or price is None or qty is None:
            raise ValueError("Missing eventId, price or quantity")

        # Cache evento
        ev_doc = db.collection("events").document(ev_id).get()
        if not ev_doc.exists:
            raise ValueError("Invalid event")
        ev_data = ev_doc.to_dict() or {}
        if not ev_data.get("active", False):
            raise ValueError("Invalid or inactive event")
        allow_duplicates = bool(ev_data.get("allowDuplicates", False))

        emails = [p.get("email") for p in participants if p.get("email")]
        phones = [p.get("phone") for p in participants if p.get("phone")]

        membership_docs = {}
        if emails:
            membership_docs = {
                doc.id: doc.to_dict()
                for doc in db.get_all([db.collection("memberships").document(email) for email in emails])
                if doc.exists
            }

        part_ref = db.collection("participants").document(ev_id).collection("participants_event")
        if allow_duplicates:
            existing_by_email = {}
            existing_by_phone = {}
        else:
            existing_by_email = (
                {doc.get("email"): True for doc in part_ref.where("email", "in", emails).stream()} if emails else {}
            )
            existing_by_phone = (
                {doc.get("phone"): True for doc in part_ref.where("phone", "in", phones).stream()} if phones else {}
            )

        non_soci = []
        minors = []
        duplicates = []

        for p in participants:
            email = p.get("email")
            phone = p.get("phone")
            birthdate = p.get("birthdate")

            if is_minor(birthdate):
                minors.append(f"{p.get('name', '')} {p.get('surname', '')}")
            if email and (email not in membership_docs or not membership_docs[email].get("subscription_valid", False)):
                non_soci.append(email)
            if not allow_duplicates:
                if email and existing_by_email.get(email):
                    duplicates.append(email)
                if phone and existing_by_phone.get(phone):
                    duplicates.append(phone)

        if minors:
            raise ValueError(f"Minors not allowed: {minors}")
        if duplicates:
            raise ValueError(f"Duplicates found: {duplicates}")

        # EP13: prezzo unico (nessun extra membership)
        total = (float(price) + float(fee)) * float(qty)
        return self.truncate_float(total)

    def validate_membership_fast(self, new_member, fee):
        if not new_member or fee is None:
            raise ValueError("Missing newMember or membershipFee")

        email = new_member.get("email")
        phone = new_member.get("phone")
        birthdate = new_member.get("birthdate")

        if not email and not phone:
            raise ValueError("newMember.email or phone required")

        if is_minor(birthdate):
            raise ValueError("User must be at least 18 years old")

        duplicates = []

        if email:
            doc_email = db.collection("memberships").document(email).get()
            if doc_email.exists and doc_email.to_dict().get("subscription_valid", False):
                duplicates.append(email)

        if phone:
            docs_phone = (
                db.collection("memberships").where("phone", "==", phone).where("subscription_valid", "==", True).stream()
            )
            for _ in docs_phone:
                duplicates.append(phone)

        if duplicates:
            raise ValueError(f"User is already an active member: {duplicates}")

        return float(fee)

    def validate_event_and_membership_fast(self, item, membership_fee):
        ev_id = item.get("eventId")
        participants = item.get("participants", [])
        price = item.get("price")
        qty = item.get("quantity")
        fee = item.get("fee", 0)

        if not ev_id or price is None or qty is None:
            raise ValueError("Missing eventId, price or quantity")

        ev_doc = db.collection("events").document(ev_id).get()
        ev_data = ev_doc.to_dict() if ev_doc.exists else None
        if not ev_data or ev_data.get("type") != "custom_ep12":
            raise ValueError("Invalid event type for event_and_membership")
        allow_duplicates = bool(ev_data.get("allowDuplicates", False))

        emails = [p.get("email") for p in participants if p.get("email")]
        phones = [p.get("phone") for p in participants if p.get("phone")]

        membership_docs = {}
        if emails:
            membership_docs = {
                doc.id: doc.to_dict()
                for doc in db.get_all([db.collection("memberships").document(email) for email in emails])
                if doc.exists
            }

        part_ref = db.collection("participants").document(ev_id).collection("participants_event")
        if allow_duplicates:
            existing_by_email = {}
            existing_by_phone = {}
        else:
            existing_by_email = (
                {doc.get("email"): True for doc in part_ref.where("email", "in", emails).stream()} if emails else {}
            )
            existing_by_phone = (
                {doc.get("phone"): True for doc in part_ref.where("phone", "in", phones).stream()} if phones else {}
            )

        duplicates = []
        minors = []

        for p in participants:
            email = p.get("email")
            phone = p.get("phone")
            birthdate = p.get("birthdate")

            if is_minor(birthdate):
                minors.append(f"{p.get('name', '')} {p.get('surname', '')}")
            # Se e' gia' membro attivo, EP12 non consente nuova tessera
            if email and membership_docs.get(email, {}).get("subscription_valid", False):
                duplicates.append(email)
            # Duplicati evento permessi solo se allowDuplicates=False
            if not allow_duplicates:
                if email and existing_by_email.get(email):
                    duplicates.append(email)
                if phone and existing_by_phone.get(phone):
                    duplicates.append(phone)

        if minors:
            raise ValueError(f"Minors not allowed: {minors}")
        if duplicates:
            raise ValueError(f"Duplicates found: {duplicates}")

        total_event = (float(price) + float(fee)) * float(qty)
        return self.truncate_float(total_event)

    # ------------------ Create-order dispatchers ------------------
    def _create_order_event(self, cart_item):
        total = self.validate_event_item_fast(cart_item)
        return total, cart_item["eventId"], cart_item.get("eventMeta") or {}

    def _create_order_membership(self, cart_item):
        total = self.validate_membership_fast(cart_item.get("newMember"), cart_item.get("membershipFee"))
        return total, None, cart_item.get("eventMeta") or {}

    def _create_order_event_and_membership(self, cart_item):
        total = self.validate_event_and_membership_fast(cart_item, cart_item.get("membershipFee"))
        return total, cart_item["eventId"], cart_item.get("eventMeta") or {}

    def _create_order_ep13_mixed(self, cart_item):
        total, updated_meta = self.validate_event_ep13_mixed(cart_item)
        # preferisci i meta validati lato backend
        return total, cart_item["eventId"], (updated_meta or (cart_item.get("eventMeta") or {}))

    # ------------------ Creazione Ordine ------------------
    def create_order(self, req_json):
        try:
            print("[TRACE] create_order payload:", req_json)
            purchase_type = req_json.get("purchase_type")
            try:
                purchase_type_enum = PurchaseTypes(purchase_type)
            except Exception:
                return jsonify({"error": "Invalid purchase_type"}), 400

            cart = req_json.get("cart", [])
            print("Cart Is:", cart)
            if not isinstance(cart, list) or len(cart) != 1:
                return jsonify({"error": "Only one cart item is allowed at the moment"}), 400

            cart_item = cart[0]
            print("[TRACE] purchase_type=", purchase_type)
            print("[TRACE] cart_item keys=", list(cart_item.keys()))
            # --- Normalize cart payload BEFORE any computation/enforcement ---
            try:
                # Normalize participants (email/phone + trim names)
                if isinstance(cart_item.get("participants"), list):
                    for p in cart_item["participants"]:
                        if isinstance(p, dict):
                            p["email"] = self._normalize_email(p.get("email"))
                            p["phone"] = self._normalize_phone(p.get("phone"))
                            if p.get("name") is not None:
                                p["name"] = str(p["name"]).strip()
                            if p.get("surname") is not None:
                                p["surname"] = str(p["surname"]).strip()
                # Normalize membership payload if present
                if isinstance(cart_item.get("newMember"), dict):
                    nm = cart_item["newMember"]
                    nm["email"] = self._normalize_email(nm.get("email"))
                    nm["phone"] = self._normalize_phone(nm.get("phone"))
                    if nm.get("name") is not None:
                        nm["name"] = str(nm["name"]).strip()
                    if nm.get("surname") is not None:
                        nm["surname"] = str(nm["surname"]).strip()
                # Normalize eventMeta lists (e.g., nonMembers/ep13NonMembers)
                #em = cart_item.get("eventMeta") or {}
                #if isinstance(em, dict):
                #    if isinstance(em.get("nonMembers"), list):
                 #       em["nonMembers"] = [self._normalize_email(x) for x in em["nonMembers"] if x is not None]
                  #  if isinstance(em.get("ep13NonMembers"), list):
                   #     em["ep13NonMembers"] = [self._normalize_email(x) for x in em["ep13NonMembers"] if x is not None]
                    #cart_item["eventMeta"] = em
                print("[TRACE] Normalized cart_item participants & meta")
            except Exception:
                logger.exception("[TRACE] Failed normalizing cart payload; proceeding with raw values")
            # Enforce only for purchases that include an event participation
            if cart_item.get("eventId") and purchase_type_enum in (
                PurchaseTypes.EVENT,
                PurchaseTypes.EVENT_AND_MEMBERSHIP,
                PurchaseTypes.EVENT_OR_EVENT_AND_MEMBERSHIP,
            ):
                print("[TRACE] Enforcement needed for event purchase types")
                self.enforce_only_members_if_required(cart_item)

            # --- Dispatch by purchase_type ---
            creators = {
                PurchaseTypes.EVENT: self._create_order_event,
                PurchaseTypes.MEMBERSHIP: self._create_order_membership,
                PurchaseTypes.EVENT_AND_MEMBERSHIP: self._create_order_event_and_membership,
                PurchaseTypes.EVENT_OR_EVENT_AND_MEMBERSHIP: self._create_order_ep13_mixed,
            }
            creator = creators.get(purchase_type_enum)
            if not creator:
                return jsonify({"error": "Invalid purchase_type"}), 400

            print("[TRACE] Using creator for purchase_type:", purchase_type_enum.value)
            total, ref_id, event_meta = creator(cart_item)
            print("[TRACE] Creator returned total=", total, "ref_id=", ref_id, "event_meta keys=", list((event_meta or {}).keys()))

            formatted = f"{total:.2f}"

            order_request = OrderRequest(
                intent=CheckoutPaymentIntent.CAPTURE,
                purchase_units=[
                    PurchaseUnitRequest(
                        reference_id=ref_id or "membership",
                        amount=AmountWithBreakdown(currency_code="EUR", value=formatted),
                    )
                ],
            )

            order = self.orders_controller.orders_create({"body": order_request})
            print("[TRACE] PayPal orders_create status=", order.status_code)
            if order.status_code not in (200, 201):
                return jsonify({"error": "Failed to create PayPal order"}), order.status_code

            body = json.loads(ApiHelper.json_serialize(order.body))
            print("[TRACE] PayPal orders_create body=", body)

            db.collection("orders").document(body["id"]).set( 
                {
                    "orderId": body["id"],
                    "orderStatus": body.get("status", "CREATED"),
                    "purchase_type": purchase_type_enum.value,
                    "cart": cart,
                    "total": total,
                    "reference_id": ref_id,
                    "eventMeta": event_meta,
                }
            )

            print("[TRACE] Order successfully created and saved with ID=", body.get("id"))
            return jsonify(body), order.status_code

        except ValueError as ve:
            return jsonify({"error": "validation_error", "message": str(ve)}), 400
        except Exception as e:
            logger.exception("Error creating order")
            return jsonify({"error": "Internal server error", "message": str(e)}), 500


    # ------------------ Capture-order dispatchers ------------------
    def _capture_event(self, cart, purchase_ref, order_data, event_meta):
        """Semplice acquisto evento: nessuna membership da creare; salva i partecipanti."""
        self.handle_event_participants(PurchaseTypes.EVENT, cart, [], purchase_ref)

    def _capture_membership(self, cart, purchase_ref, order_data, event_meta):
        """Acquisto della sola membership: crea la membership, nessun partecipante da salvare."""
        self.handle_membership_creation(PurchaseTypes.MEMBERSHIP.value, cart, purchase_ref, order_data)

    def _capture_event_and_membership(self, cart, purchase_ref, order_data, event_meta):
        """EP12: membership + evento nella stessa purchase: crea membership e poi salva partecipanti linkati."""
        membership_refs = self.handle_membership_creation(PurchaseTypes.EVENT_AND_MEMBERSHIP.value, cart, purchase_ref, order_data)
        self.handle_event_participants(PurchaseTypes.EVENT_AND_MEMBERSHIP, cart, membership_refs, purchase_ref)

    def _capture_event_ep13_mixed(self, cart, purchase_ref, order_data, event_meta):
        """EP13 misto: crea membership solo per i non soci verificati, poi salva tutti i partecipanti."""
        membership_refs = []
        try:
            print("[EP13] capture: incoming event_meta:", event_meta)
            non_members_list = (
                (event_meta.get("nonMembersVerified") or event_meta.get("nonMembers"))
            )
            print("[EP13] capture: non_members_list=", non_members_list)
            if non_members_list:
                nm_set = {str(e).lower() for e in non_members_list}
                print("[EP13] capture: nm_set(lower)=", nm_set)
                all_parts = (cart.get("participants") or [])
                people = [p for p in all_parts if (p.get("email") or "").lower() in nm_set]
                print(f"[EP13] capture: participants total={len(all_parts)}; matched non-members={len(people)}")
                print("[EP13] capture: matched emails=", [ (p.get("email") or "").lower() for p in people ])
                # Idempotenza: evita doppie tessere
                filtered = []
                
                for person in people:
                    existing = self.get_existing_membership_by_contact(person)
                    has_existing = bool(existing)
                    print(f"[EP13] capture: candidate {person.get('email')} existing_membership={has_existing}")
                    if existing:
                        # Check if membershipId is missing or empty, patch if needed
                        if not person.get("membershipId"):
                            person["membershipId"] = existing.id
                            print(f"[EP13][WARN] Participant {person.get('email')} was missing membershipId, patched with existing id {existing.id}")
                        continue
                    filtered.append(person)
                print(f"[EP13] capture: filtered non-members to create={len(filtered)}")
                if filtered:
                    membership_refs = self.handle_membership_creation(
                        purchase_type=PurchaseTypes.EVENT_OR_EVENT_AND_MEMBERSHIP.value,
                        cart=cart,
                        purchase_ref=purchase_ref,
                        order_data=order_data,
                        forced_people=filtered,
                        membership_type_override="event_ep13_mixed",
                    )
                    print(f"[EP13] capture: created memberships count={len(membership_refs)} -> ids={[m.get('membership_id') for m in (membership_refs or [])]}")
        except Exception:
            logger.exception("EP13 mixed: membership auto-creation failed (non-blocking)")
        print("[EP13] capture: proceeding to handle_event_participants with membership_refs count=", len(membership_refs))
        self.handle_event_participants(PurchaseTypes.EVENT_OR_EVENT_AND_MEMBERSHIP, cart, membership_refs, purchase_ref)

    # ------------------ Cattura Ordine ------------------
    def capture_order(self, req_json):
        try:
            logger.debug("capture_order_service called with: %s", req_json)

            order_id = req_json.get("order_id")
            if not order_id:
                logger.error("Missing order_id in request body")
                return jsonify({"error": "Missing order_id in request body"}), 400

            logger.debug(f"Attempting to capture PayPal order: {order_id}")
            order_data = self.capture_paypal_order(order_id)
            logger.debug("Order data received: %s", order_data)

            # --- Security validations: COMPLETED order & capture + valid capture id (works for PayPal and Apple Pay) ---
            valid, validation_result = self.validate_capture_payload(order_data)
            if not valid:
                try:
                    # Best-effort: persist latest order status
                    db.collection("orders").document(order_id).update({
                        "orderStatus": (order_data.get("status") or "UNKNOWN")
                    })
                except Exception:
                    logger.warning("Unable to update order status on Firestore for failed capture validation")
                return jsonify(validation_result), 400

            # cap0 is available if needed later
            cap0 = validation_result

            order_status = order_data.get("status", "")
            logger.debug(f"Order status from PayPal: {order_status}")

            logger.debug("Fetching order details from Firestore")
            cart, purchase_type_str, ref_id, order_rec = self.get_order_details_from_db(order_id)
            logger.debug(f"cart: {cart}")
            logger.debug(f"purchase_type: {purchase_type_str}")
            logger.debug(f"ref_id: {ref_id}")
            logger.debug(f"order_rec: {order_rec}")

            try:
                purchase_type_enum = PurchaseTypes(purchase_type_str)
            except Exception:
                logger.error("Unsupported purchase_type in capture: %s", purchase_type_str)
                return jsonify({"error": "Unsupported purchase_type in capture"}), 400

            event_meta = (order_rec or {}).get("eventMeta") or {}

            db.collection("orders").document(order_id).update({"orderStatus": order_status})
            logger.debug("Updated Firestore order with status: %s", order_status)

            logger.debug("Saving purchase...")
            purchase, purchase_ref = self.save_purchase(order_id, order_data, order_status, purchase_type_enum.value, ref_id)
            logger.debug("Purchase saved: %s", purchase)
            logger.debug("Purchase Firestore ID: %s", purchase_ref.id)

            # Derive payment_source and method_used for response after validations and save
            payment_source = order_data.get("payment_source", {})
            method_used = list(payment_source.keys())[0] if payment_source else "unknown"
            logger.debug(f"Payment method used: {method_used}")

            # --- Dispatch capture flow by purchase_type ---
            capture_handlers = {
                PurchaseTypes.EVENT: self._capture_event,
                PurchaseTypes.MEMBERSHIP: self._capture_membership,
                PurchaseTypes.EVENT_AND_MEMBERSHIP: self._capture_event_and_membership,
                PurchaseTypes.EVENT_OR_EVENT_AND_MEMBERSHIP: self._capture_event_ep13_mixed,
            }
            handler = capture_handlers.get(purchase_type_enum)
            if not handler:
                logger.error("Unsupported purchase_type in capture: %s", purchase_type_enum.value)
                return jsonify({"error": "Unsupported purchase_type in capture"}), 400

            handler(cart, purchase_ref, order_data, event_meta)

            logger.debug("Deleting order document from Firestore")
            db.collection("orders").document(order_id).delete()

            logger.info("Order captured and processed successfully")
            return jsonify({
                "message": "Order captured and processed successfully",
                "purchase_id": purchase_ref.id,
                "payment_method": method_used,
            }), 200

        except Exception as e:
            logger.exception("Error capturing order")
            return jsonify({"error": str(e)}), 500

    # ------------------ PayPal & DB helpers ------------------
    def capture_paypal_order(self, order_id):
        print(f"[DEBUG] Performing capture for order {order_id}")
        order = self.orders_controller.orders_capture({"id": order_id, "prefer": "return=representation"})
        print(f"[DEBUG] PayPal capture response status: {order.status_code}")
        if not (200 <= order.status_code < 300):
            raise Exception(f"Failed to capture order (status: {order.status_code})")

        result = json.loads(ApiHelper.json_serialize(order.body))
        print("[DEBUG] Serialized order body:", result)
        return result

    def get_order_details_from_db(self, order_id):
        print(f"[DEBUG] Fetching Firestore order document: {order_id}")
        snapshot = db.collection("orders").document(order_id).get()
        if not snapshot.exists:
            raise Exception("Order not found in DB")

        data = snapshot.to_dict()
        print("[DEBUG] Order document data:", data)
        return data["cart"][0], data["purchase_type"], data.get("reference_id"), data

    def save_purchase(self, order_id, order_data, order_status, purchase_type, ref_id):
        print("[DEBUG] Extracting PayPal/Apple Pay transaction data")

        # STEP 1: Detect payment method from payment_source
        payment_source = order_data.get("payment_source", {})
        print("[DEBUG] payment_source:", payment_source)

        method_used = list(payment_source.keys())[0] if payment_source else "unknown"
        method_data = payment_source.get(method_used, {})
        print("[DEBUG] Detected payment method:", method_used)
        print("[DEBUG] method_data:", method_data)

        # STEP 2: Estrarre nome e email dal metodo giusto
        if method_used == "paypal":
            name_info = method_data.get("name", {})
            print("[DEBUG] PayPal name_info:", name_info)

            payer_name = name_info.get("given_name", "")
            payer_surname = name_info.get("surname", "")
            email = method_data.get("email_address", "")

        elif method_used == "apple_pay":
            full_name = method_data.get("name", "")
            print("[DEBUG] ApplePay full name string:", full_name)

            name_parts = full_name.split(" ")
            payer_name = name_parts[0] if len(name_parts) > 0 else ""
            payer_surname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            email = method_data.get("email_address", "")

        else:
            payer = order_data.get("payer", {})
            print("[DEBUG] Fallback payer object:", payer)

            name_info = payer.get("name", {})
            print("[DEBUG] Fallback name_info:", name_info)

            payer_name = name_info.get("given_name", "")
            payer_surname = name_info.get("surname", "")
            email = payer.get("email_address", "")

        print("[DEBUG] payer_name:", payer_name)
        print("[DEBUG] payer_surname:", payer_surname)
        print("[DEBUG] payer_email:", email)

        # STEP 3: Dati dal primo purchase unit
        pu = order_data.get("purchase_units", [])[0]
        print("[DEBUG] purchase_unit:", pu)

        payments = pu.get("payments", {})
        captures = payments.get("captures", [])[0]
        print("[DEBUG] capture:", captures)

        # Defensive read for capture status
        capture_status = (captures.get("status") or "").upper()

        transaction_id = captures.get("id", "")
        amount_total = captures.get("amount", {}).get("value", "")
        currency = captures.get("amount", {}).get("currency_code", "")
        capture_time = captures.get("create_time", "")

        print("[DEBUG] transaction_id:", transaction_id)
        print("[DEBUG] amount_total:", amount_total)
        print("[DEBUG] currency:", currency)
        print("[DEBUG] capture_time:", capture_time)

        seller_receivable_breakdown = captures.get("seller_receivable_breakdown", {})
        paypal_fee = seller_receivable_breakdown.get("paypal_fee", {}).get("value", "")
        net_amount = seller_receivable_breakdown.get("net_amount", {}).get("value", "")

        print("[DEBUG] paypal_fee:", paypal_fee)
        print("[DEBUG] net_amount:", net_amount)

        # STEP 4: Costruzione oggetto finale
        purchase = {
            "payer_name": payer_name,
            "payer_surname": payer_surname,
            "payer_email": email,
            "amount_total": amount_total,
            "currency": currency,
            "paypal_fee": paypal_fee,
            "net_amount": net_amount,
            "transaction_id": transaction_id,
            "order_id": order_id,
            "status": order_status,
            "timestamp": capture_time,
            "type": purchase_type,
            "ref_id": ref_id,
            "payment_method": method_used,
            "capture_status": capture_status,
        }

        print("[DEBUG] Final purchase object to save:", purchase)

        # STEP 5: Save in Firestore
        purchase_ref = db.collection("purchases").add(purchase)[1]
        print(f"[DEBUG] Purchase saved with ID: {purchase_ref.id}")

        return purchase, purchase_ref

    def handle_membership_creation(self, purchase_type, cart, purchase_ref, order_data, forced_people=None, membership_type_override=None):
        print("[DEBUG] Starting membership creation...")
        # Normalize purchase_type to string if enum
        pt = purchase_type.value if hasattr(purchase_type, "value") else purchase_type
        print(f"[MEM] purchase_type={pt} forced_people={(forced_people is not None)}")
        capture_time = order_data["purchase_units"][0]["payments"]["captures"][0]["create_time"]
        members = forced_people if forced_people is not None else ([cart["newMember"]] if pt == "membership" else cart.get("participants", []))
        print(f"[MEM] capture_time={capture_time} members_count={len(members)}")

        membership_refs = []
        for person in members:
            email_dbg = (person.get("email") or "").lower()
            phone_dbg = (person.get("phone") or "").strip()
            print(f"[MEM] Creating membership for: email={email_dbg} phone={phone_dbg}")
            membership = {
                "name": person["name"],
                "surname": person["surname"],
                "email": person["email"],
                "phone": person["phone"],
                "birthdate": person.get("birthdate"),
                "start_date": capture_time,
                "end_date": self.calculate_end_of_year(capture_time),
                "subscription_valid": True,
                "membership_sent": False,
                "membership_type": (membership_type_override or pt),
                "purchase_id": purchase_ref.id,
                "purchases": [purchase_ref.id],
                "attended_events": [],
            }
            print("[MEM] membership payload keys=", list(membership.keys()))
            print(f"[MEM] membership end_date={membership['end_date']} type={membership['membership_type']}")

            ref = db.collection("memberships").add(membership)[1]
            print(f"[DEBUG] Membership saved with ID: {ref.id}")

            if pt == "membership":
                db.collection("purchases").document(purchase_ref.id).update({"ref_id": ref.id})
                print(f"[MEM] purchase linked to membership: {ref.id}")

            membership_refs.append({
                "email": person["email"],
                "phone": person["phone"],
                "membership_id": ref.id,
            })

        print(f"[MEM] membership_refs returned count={len(membership_refs)}")
        return membership_refs

    def validate_event_ep13_mixed(self, item):
        """
        EP13 mixed: consente gruppi misti (membri e non-membri) a prezzo unico.
        - Verifica che l'evento esista ed sia attivo;
        - Legge dal carrello i "nonMembers" dichiarati (in eventMeta.nonMembers/ep13NonMembers);
        - Controlla che i dichiarati nonMembers NON abbiano già membership valida;
        - Calcola il totale come evento (prezzo + fee) * qty;
        - Restituisce (total, updated_event_meta) dove updated_event_meta include una chiave
          "nonMembersVerified" con la lista effettivamente non-membri.
        """
        ev_id = item.get("eventId")
        participants = item.get("participants", [])
        price = item.get("price")
        qty = item.get("quantity")
        fee = item.get("fee", 0)
        event_meta = item.get("eventMeta") or {}

        if not ev_id or price is None or qty is None:
            raise ValueError("Missing eventId, price or quantity")

        ev_doc = db.collection("events").document(ev_id).get()
        if not ev_doc.exists:
            raise ValueError("Invalid event")
        ev_data = ev_doc.to_dict() or {}
        if not ev_data.get("active", False):
            raise ValueError("Invalid or inactive event")

        emails = [p.get("email") for p in participants if p.get("email")]
        phones = [p.get("phone") for p in participants if p.get("phone")]

        # Mappa email -> membership valida (normalize keys to lowercase)
        membership_docs = {}
        if emails:
            membership_docs = {
                (doc.id or "").lower(): (doc.to_dict() or {})
                for doc in db.get_all([db.collection("memberships").document(email) for email in emails])
                if doc.exists
            }

        # Enforce identity: if email belongs to an active member, provided name/surname must match
        identity_mismatches = []
        for p in participants:
            email_l = (p.get("email") or "").strip().lower()
            if not email_l:
                continue
            mdoc = membership_docs.get(email_l)
            if not mdoc:
                continue
            if bool(mdoc.get("subscription_valid", False)):
                provided_name = self._normalize_text(p.get("name"))
                provided_surname = self._normalize_text(p.get("surname"))
                member_name = self._normalize_text(mdoc.get("name"))
                member_surname = self._normalize_text(mdoc.get("surname"))
                if (member_name and member_surname) and (
                    member_name != provided_name or member_surname != provided_surname
                ):
                    identity_mismatches.append(
                        f"{p.get('name','')} {p.get('surname','')} <{email_l}> (atteso: {mdoc.get('name','')} {mdoc.get('surname','')})"
                    )
        if identity_mismatches:
            raise ValueError(
                "One or more participants use an email already associated with a member but name/surname do not match: "
                + ", ".join(identity_mismatches)
            )

        # Determina chi è non-membro realmente (serve per updated_meta)
        actually_non_members = []
        for p in participants:
            email_l = (p.get("email") or "").lower()
            is_valid_member = bool(membership_docs.get(email_l, {}).get("subscription_valid", False))
            if not is_valid_member:
                actually_non_members.append(email_l)

        # NonMembers dichiarati dal frontend (diversi possibili nomi)
        declared_non_members = event_meta.get("nonMembers") or event_meta.get("ep13NonMembers") or []
        declared_set = {str(e).lower() for e in declared_non_members if isinstance(e, str)}

        # Verifica: i dichiarati devono essere davvero non-membri
        mismatches = [
            e for e in declared_set
            if bool(membership_docs.get(e, {}).get("subscription_valid", False))
        ]
        if mismatches:
            raise ValueError(f"Some declared non-members are already members: {mismatches}")

        # Prepara metadati aggiornati per la capture (usa la lista REALMENTE non-membri)
        updated_meta = dict(event_meta)
        updated_meta["nonMembersVerified"] = actually_non_members

        total = (float(price) + float(fee)) * float(qty)
        return self.truncate_float(total), updated_meta

    def handle_event_participants(self, purchase_type, cart, membership_refs, purchase_ref):
        # normalize to enum for comparisons
        if isinstance(purchase_type, str):
            try:
                purchase_type = PurchaseTypes(purchase_type)
            except Exception:
                pass
        print("[DEBUG] Adding participants to event:", cart.get("eventId"))
        participants = cart.get("participants", [])
        for p in participants:
            print("[DEBUG] Processing participant:", p)
            membership_id = None

            if purchase_type == PurchaseTypes.EVENT_AND_MEMBERSHIP:
                match = next((m for m in membership_refs if m["email"] == p["email"]), None)
                if match:
                    membership_id = match["membership_id"]
                    print(f"[DEBUG] Matched membership for event_and_membership: {membership_id}")

            elif purchase_type == PurchaseTypes.EVENT:
                membership_doc = self.get_existing_membership_by_contact(p)
                if membership_doc:
                    membership_id = membership_doc.id
                    print(f"[DEBUG] Existing membership found for event: {membership_id}")

            elif purchase_type == PurchaseTypes.EVENT_OR_EVENT_AND_MEMBERSHIP:
                # Mixed EP13: some participants received a membership in this capture
                match = next((m for m in (membership_refs or []) if m.get("email") == p.get("email")), None)
                if match:
                    membership_id = match.get("membership_id")
                    print(f"[DEBUG] Matched membership for event_and_event_and_membership: {membership_id}")

            participant = {
                "event_id": cart["eventId"],
                "name": p["name"],
                "surname": p["surname"],
                "email": p["email"],
                "phone": p["phone"],
                "birthdate": p.get("birthdate"),
                "membership_included": (
                    (purchase_type == PurchaseTypes.EVENT_AND_MEMBERSHIP) or
                    (purchase_type == PurchaseTypes.EVENT_OR_EVENT_AND_MEMBERSHIP and any((m.get("email") == p.get("email")) for m in (membership_refs or [])))
                ),
                "ticket_sent": False,
                "location_sent": False,
                "purchase_id": purchase_ref.id,
                "price": cart["price"],
                "newsletterConsent": p.get("newsletterConsent", False),
                "createdAt": firestore.SERVER_TIMESTAMP,
            }

            if membership_id:
                participant["membershipId"] = membership_id
                update_data = {"attended_events": firestore.ArrayUnion([cart["eventId"]])}
                if purchase_type in (PurchaseTypes.EVENT, PurchaseTypes.EVENT_OR_EVENT_AND_MEMBERSHIP):
                    update_data["purchases"] = firestore.ArrayUnion([purchase_ref.id])

                db.collection("memberships").document(membership_id).update(update_data)
                print(f"[DEBUG] Updated membership {membership_id} with event participation")

            db.collection("participants").document(cart["eventId"]).collection("participants_event").add(participant)
            print(f"[DEBUG] Participant saved: {p['email']} membershipId={membership_id}")

    def get_existing_membership_by_contact(self, participant):
        print(f"[DEBUG] Searching membership for participant {participant['email']} or {participant.get('phone')}")
        membership_query = (
            db.collection("memberships")
            .where("subscription_valid", "==", True)
            .where("email", "==", participant["email"])
            .stream()
        )

        doc = next(membership_query, None)
        if not doc and participant.get("phone"):
            print("[DEBUG] Trying with phone")
            membership_query = (
                db.collection("memberships")
                .where("subscription_valid", "==", True)
                .where("phone", "==", participant["phone"])
                .stream()
            )
            doc = next(membership_query, None)

        if doc:
            print(f"[DEBUG] Found membership: {doc.id}")
        else:
            print("[DEBUG] No membership found")

        return doc


# ------------------ Delegatori per retrocompatibilità ------------------

def create_order_service(req_json):
    return PaymentService.instance().create_order(req_json)


def capture_order_service(req_json):
    return PaymentService.instance().capture_order(req_json)