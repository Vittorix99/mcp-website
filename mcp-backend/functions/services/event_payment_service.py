import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from flask import jsonify
from google.cloud import firestore
from paypalserversdk.api_helper import ApiHelper
from paypalserversdk.configuration import Environment
from paypalserversdk.controllers.orders_controller import OrdersController
from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
from paypalserversdk.models.amount_with_breakdown import AmountWithBreakdown
from paypalserversdk.models.checkout_payment_intent import CheckoutPaymentIntent
from paypalserversdk.models.order_request import OrderRequest
from paypalserversdk.models.purchase_unit_request import PurchaseUnitRequest
from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient
from config.firebase_config import db
from models import (
    Event,
    EventOrder,
    EventParticipant,
    EventPurchase,
    EventPurchaseAccessType,
    Membership,
    PurchaseTypes,
)
from utils.events_utils import (
    build_event_from_data,
    calculate_end_of_year,
    map_purchase_mode,
    normalize_email,
    normalize_phone,
)
from utils.participant_rules import run_basic_checks

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("EventPaymentService")


class EventPaymentService:
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
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
        self.debug = os.getenv("EVENT_PAYMENT_DEBUG", "true").lower() in {"1", "true", "yes"}

    def _debug(self, message: str, *args):
        if self.debug:
            try:
                print("[EventPaymentService DEBUG]", message % args if args else message)
            except Exception:
                print("[EventPaymentService DEBUG]", message, *args)

    # ------------------------------------------------------------------ #
    # Order creation
    # ------------------------------------------------------------------ #
    def create_order_event(self, payload: Dict, event_data: Optional[Dict] = None):
        try:
            cart = payload.get("cart", [])
            if not isinstance(cart, list) or len(cart) != 1:
                return jsonify({"error": "Only one cart item is allowed"}), 400

            cart_item = cart[0]
            event_id = cart_item.get("eventId")
            participants = cart_item.get("participants", [])
            membership_fee = cart_item.get("membershipFee")

            if not event_id or not isinstance(participants, list) or not participants:
                return jsonify({"error": "Missing eventId or participants"}), 400

            event_payload = event_data or {}
            if not event_payload:
                event_snapshot = db.collection("events").document(event_id).get()
                if not event_snapshot.exists:
                    return jsonify({"error": "Evento non trovato"}), 404
                event_payload = event_snapshot.to_dict() or {}
            self._debug("Processing order creation for event %s with %d participants", event_id, len(participants))

            event_model = build_event_from_data(event_payload, event_id)
            purchase_mode = event_model.purchase_mode

            normalized_participants = self._normalize_participants(participants)
            cart_item["participants"] = normalized_participants

            validation_result = run_basic_checks(event_id, normalized_participants, event_payload)
            if validation_result.errors:
                return jsonify({"error": "validation_error", "messages": validation_result.errors}), 400

            membership_targets, membership_lookup = self._determine_membership_targets(
                purchase_mode, normalized_participants, validation_result
            )
            if membership_targets and membership_fee is None:
                return jsonify({"error": "Missing membershipFee for membership creation"}), 400

            total = self._compute_total(event_model, normalized_participants, membership_targets, membership_fee)
            formatted_total = f"{total:.2f}"

            order_request = OrderRequest(
                intent=CheckoutPaymentIntent.CAPTURE,
                purchase_units=[
                    PurchaseUnitRequest(reference_id=event_id, amount=AmountWithBreakdown(currency_code="EUR", value=formatted_total))
                ],
            )
            order = self.orders_controller.orders_create({"body": order_request})
            if order.status_code not in (200, 201):
                return jsonify({"error": "Failed to create PayPal order"}), order.status_code

            body = json.loads(ApiHelper.json_serialize(order.body))
            self._debug("PayPal order created: %s (status %s)", body.get("id"), body.get("status"))

            cart_payload = [cart_item]
            event_order = EventOrder(
                order_id=body["id"],
                order_status=body.get("status", "CREATED"),
                purchase_type=PurchaseTypes.EVENT,
                cart=cart_payload,
                total=total,
                reference_id=event_id,
                event_meta=cart_item.get("eventMeta", {}),
                event_id=event_id,
                participants=normalized_participants,
                event_price=float(event_model.price or 0),
                event_fee=float(event_model.fee or 0),
                membership_targets=membership_targets,
                membership_fee=float(membership_fee) if membership_fee is not None else None,
                purchase_mode=purchase_mode,
                membership_lookup=membership_lookup,
            )

            db.collection("orders").document(body["id"]).set(event_order.to_firestore(include_none=True))
            self._debug("Order document stored for %s", body["id"])
            return jsonify(body), order.status_code

        except ValueError as ve:
            return jsonify({"error": "validation_error", "message": str(ve)}), 400
        except Exception as e:
            logger.exception("Error creating event order")
            return jsonify({"error": "Internal server error", "message": str(e)}), 500

    # ------------------------------------------------------------------ #
    # Order capture
    # ------------------------------------------------------------------ #
    def capture_order_event(self, payload: Dict):
        try:
            order_id = payload.get("order_id")
            if not order_id:
                return jsonify({"error": "Missing order_id in request body"}), 400

            order_data = self.capture_paypal_order(order_id)
            valid, validation_result = self.validate_capture_payload(order_data)
            if not valid:
                self._debug("Capture validation failed for %s: %s", order_id, validation_result)
                self._update_order_status(order_id, order_data.get("status") or "UNKNOWN")
                return jsonify(validation_result), 400

            order_snapshot = db.collection("orders").document(order_id).get()
            if not order_snapshot.exists:
                return jsonify({"error": "Order not found"}), 404
            order_data_dict = order_snapshot.to_dict() or {}
            event_order = EventOrder.from_firestore(order_data_dict, order_snapshot.id)

            event_id = event_order.event_id
            participants = event_order.participants or []
            membership_targets = event_order.membership_targets or []

            purchase_mode = event_order.purchase_mode or EventPurchaseAccessType.PUBLIC
            purchase, purchase_ref = self.save_purchase(
                order_id,
                order_data,
                order_data.get("status", ""),
                event_id,
                purchase_mode,
            )

            existing_memberships = event_order.membership_lookup or {}
            membership_refs = []
            if membership_targets:
                membership_refs = self.create_memberships_for_targets(
                    membership_targets,
                    event_order.membership_fee,
                    order_data,
                    purchase_ref,
                )

            self.handle_event_participants(
                event_id,
                participants,
                membership_refs,
                purchase_ref,
                event_order.event_price,
                existing_memberships,
            )

            db.collection("orders").document(order_id).delete()
            self._debug("Order %s processed and removed from staging", order_id)

            payment_source = order_data.get("payment_source", {})
            method_used = list(payment_source.keys())[0] if payment_source else "unknown"

            return jsonify(
                {
                    "message": "Order captured and processed successfully",
                    "purchase_id": purchase_ref.id,
                    "payment_method": method_used,
                }
            ), 200

        except Exception as e:
            logger.exception("Error capturing event order")
            return jsonify({"error": str(e)}), 500

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _normalize_participants(self, participants: List[Dict]) -> List[Dict]:
        normalized = []
        for p in participants:
            item = dict(p)
            item["email"] = normalize_email(item.get("email"))
            item["phone"] = normalize_phone(item.get("phone"))
            if item.get("name") is not None:
                item["name"] = str(item["name"]).strip()
            if item.get("surname") is not None:
                item["surname"] = str(item["surname"]).strip()
            normalized.append(item)
        return normalized

    def _determine_membership_targets(
        self,
        purchase_mode: EventPurchaseAccessType,
        participants: List[Dict],
        validation_result,
    ) -> Tuple[List[Dict], Dict[str, Dict]]:
        membership_lookup = validation_result.membership_docs or {}
        targets = []

        if purchase_mode == EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS and validation_result.non_members:
            raise ValueError(
                "Evento riservato ai membri: i seguenti partecipanti non risultano tesserati o attivi: "
                + ", ".join(validation_result.non_members)
            )

        if purchase_mode == EventPurchaseAccessType.ONLY_MEMBERS:
            for p in participants:
                email = normalize_email(p.get("email"))
                if not email or email not in membership_lookup:
                    targets.append(p)

        if purchase_mode == EventPurchaseAccessType.ON_REQUEST:
            raise ValueError("Acquisto non disponibile: evento on request")

        return targets, membership_lookup

    def _compute_total(self, event: Event, participants, membership_targets, membership_fee):
        price = float(event.price or 0)
        fee = float(event.fee or 0)
        count = len(participants)
        total = count * (price + fee)

        return total

    # ------------------------------------------------------------------ #
    # PayPal helpers (reuse existing logic)
    # ------------------------------------------------------------------ #
    def capture_paypal_order(self, order_id):
        order = self.orders_controller.orders_capture({"id": order_id, "prefer": "return=representation"})
        if not (200 <= order.status_code < 300):
            raise Exception(f"Failed to capture order (status: {order.status_code})")
        result = json.loads(ApiHelper.json_serialize(order.body))
        return result

    def validate_capture_payload(self, order_data):
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
            return False, {
                "error": "payment_not_completed",
                "message": f"Payment not completed (order={top_status}, capture={cap_status}, id={cap_id}).",
            }

        if not final_flag:
            logger.warning("Capture is not marked as final_capture=True (id=%s)", cap_id)

        return True, cap0

    def save_purchase(self, order_id, order_data, order_status, event_id, purchase_mode: EventPurchaseAccessType):
        payment_source = order_data.get("payment_source", {})
        method_used = list(payment_source.keys())[0] if payment_source else "unknown"
        method_data = payment_source.get(method_used, {})

        if method_used == "paypal":
            name_info = method_data.get("name", {})
            payer_name = name_info.get("given_name", "")
            payer_surname = name_info.get("surname", "")
            email = method_data.get("email_address", "")
        elif method_used == "apple_pay":
            full_name = method_data.get("name", "")
            name_parts = full_name.split(" ")
            payer_name = name_parts[0] if len(name_parts) > 0 else ""
            payer_surname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            email = method_data.get("email_address", "")
        else:
            payer = order_data.get("payer", {})
            name_info = payer.get("name", {})
            payer_name = name_info.get("given_name", "")
            payer_surname = name_info.get("surname", "")
            email = payer.get("email_address", "")

        pu = order_data.get("purchase_units", [])[0]
        captures = pu.get("payments", {}).get("captures", [])[0]
        capture_status = (captures.get("status") or "").upper()

        transaction_id = captures.get("id", "")
        amount_total = captures.get("amount", {}).get("value", "")
        currency = captures.get("amount", {}).get("currency_code", "")
        capture_time = captures.get("create_time", "")

        seller_receivable_breakdown = captures.get("seller_receivable_breakdown", {})
        paypal_fee = seller_receivable_breakdown.get("paypal_fee", {}).get("value", "")
        net_amount = seller_receivable_breakdown.get("net_amount", {}).get("value", "")

        purchase = EventPurchase(
            payer_name=payer_name,
            payer_surname=payer_surname,
            payer_email=email,
            amount_total=amount_total,
            currency=currency,
            paypal_fee=paypal_fee,
            net_amount=net_amount,
            transaction_id=transaction_id,
            order_id=order_id,
            status=order_status,
            timestamp=capture_time,
            ref_id=event_id,
            payment_method=method_used,
            capture_status=capture_status,
            event_id=event_id,
            event_purchase_type=purchase_mode,
        )

        purchase_ref = db.collection("purchases").add(purchase.to_firestore(include_none=True))[1]
        return purchase.to_firestore(include_none=True), purchase_ref

    def create_memberships_for_targets(self, targets, membership_fee, order_data, purchase_ref):
        capture_time = order_data["purchase_units"][0]["payments"]["captures"][0]["create_time"]
        membership_refs = []
        fee_value = float(membership_fee) if membership_fee is not None else None
        for person in targets:
            end_date = calculate_end_of_year(capture_time)
            if not end_date:
                fallback_year = datetime.utcnow().year
                end_date = f"31-12-{fallback_year}"
            membership = Membership(
                name=person.get("name"),
                surname=person.get("surname"),
                email=person.get("email"),
                phone=person.get("phone"),
                birthdate=person.get("birthdate"),
                start_date=capture_time,
                end_date=end_date,
                subscription_valid=True,
                membership_sent=False,
                send_card_on_create=True,
                membership_type=PurchaseTypes.EVENT.value,
                purchase_id=purchase_ref.id,
                purchases=[purchase_ref.id],
                attended_events=[],
                membership_fee=fee_value,
            )
            ref = db.collection("memberships").add(membership.to_firestore(include_none=True))[1]
            membership_refs.append({"email": normalize_email(person.get("email")), "membership_id": ref.id})
        return membership_refs

    def handle_event_participants(self, event_id, participants, membership_refs, purchase_ref, price, existing_memberships):
        membership_map = {ref["email"]: ref["membership_id"] for ref in (membership_refs or []) if ref.get("email")}
        existing_map = {}
        for email, payload in (existing_memberships or {}).items():
            if isinstance(payload, dict) and payload.get("id"):
                existing_map[normalize_email(email)] = payload["id"]

        for p in participants:
            normalized_email = normalize_email(p.get("email"))
            membership_id = membership_map.get(normalized_email) or existing_map.get(normalized_email)
            participant = EventParticipant(
                event_id=event_id,
                name=p.get("name"),
                surname=p.get("surname"),
                email=p.get("email"),
                phone=p.get("phone"),
                birthdate=p.get("birthdate"),
                membership_included=bool(membership_id),
                ticket_sent=False,
                location_sent=False,
                purchase_id=purchase_ref.id,
                price=price,
                newsletter_consent=p.get("newsletterConsent", False),
                created_at=firestore.SERVER_TIMESTAMP,
            )
            if membership_id:
                participant.membership_id = membership_id
                db.collection("memberships").document(membership_id).update(
                    {"attended_events": firestore.ArrayUnion([event_id]), "purchases": firestore.ArrayUnion([purchase_ref.id])}
                )

            db.collection("participants").document(event_id).collection("participants_event").add(
                participant.to_firestore(include_none=True)
            )

    def _update_order_status(self, order_id, status):
        try:
            db.collection("orders").document(order_id).update({"orderStatus": status})
        except Exception:
            logger.warning("Unable to update order status for %s", order_id)

def create_order_event_service(req_json, event_data=None):
    return EventPaymentService.instance().create_order_event(req_json, event_data)


def capture_order_event_service(req_json):
    return EventPaymentService.instance().capture_order_event(req_json)
