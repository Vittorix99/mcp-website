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
from utils.events_utils import is_minor, calculate_end_of_year
from google.cloud import firestore


# --- Logging Configuration ---
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("CaptureOrderService")
# --- Initialize PayPal Client ---
paypal_client = PaypalServersdkClient(
    client_credentials_auth_credentials=ClientCredentialsAuthCredentials(
        o_auth_client_id=os.getenv("PAYPAL_CLIENT_ID") if os.getenv("PAYPAL_ENV") == "sandbox" else os.getenv("PAYPAL_LIVE_CLIENT_ID"),
        o_auth_client_secret=os.getenv("PAYPAL_CLIENT_SECRET") if os.getenv("PAYPAL_ENV") == "sandbox" else os.getenv("PAYPAL_LIVE_CLIENT_SECRET"),
    ),
    environment=Environment.SANDBOX if os.getenv("PAYPAL_ENV") == "sandbox" else Environment.PRODUCTION,
)

# Print PayPal environment info

# PayPal Controllers
orders_controller: OrdersController = paypal_client.orders
payments_controller: PaymentsController = paypal_client.payments


from datetime import datetime
def truncate_float(value, decimals=1):
    factor = 10 ** decimals
    return int(float(value) * factor) / factor

def calculate_end_of_year(date_str):
    """
    Riceve una data in formato ISO (es: "2025-06-23T15:00:00Z") 
    e restituisce la stringa della fine dell'anno ("2025-12-31")
    """
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", ""))
        return f"31-12-{dt.year}"
    except Exception as e:
        logging.exception("Failed to calculate end of year")
        return None


def validate_event_item_fast(item):
    ev_id = item.get("eventId")
    participants = item.get("participants", [])
    price = item.get("price")
    qty = item.get("quantity")
    fee = item.get("fee", 0)

    if not ev_id or price is None or qty is None:
        raise ValueError("Missing eventId, price or quantity")

    # Cache evento
    ev_doc = db.collection("events").document(ev_id).get()
    if not ev_doc.exists or not ev_doc.to_dict().get("active", False):
        raise ValueError("Invalid or inactive event")

    emails = [p["email"] for p in participants if "email" in p]
    phones = [p["phone"] for p in participants if "phone" in p]

    membership_docs = {doc.id: doc.to_dict() for doc in db.get_all(
        [db.collection("memberships").document(email) for email in emails])}

    part_ref = db.collection("participants").document(ev_id).collection("participants_event")
    existing_by_email = {doc.get("email"): True for doc in part_ref.where("email", "in", emails).stream()} if emails else {}
    existing_by_phone = {doc.get("phone"): True for doc in part_ref.where("phone", "in", phones).stream()} if phones else {}

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
        if email and existing_by_email.get(email):
            duplicates.append(email)
        if phone and existing_by_phone.get(phone):
            duplicates.append(phone)

    if minors:
        raise ValueError(f"Minors not allowed: {minors}")
    if non_soci:
        raise ValueError(f"Some participants are not active members: {non_soci}")
    if duplicates:
        raise ValueError(f"Duplicates found: {duplicates}")

    total = (float(price) + float(fee)) * float(qty)
    return truncate_float(total)


def validate_membership_fast(new_member, fee):
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

    docs_to_check = []
    if email:
        docs_to_check.append(db.collection("memberships").document(email))
    if phone:
        docs_to_check.append(
            db.collection("memberships")
              .where("phone", "==", phone)
              .where("subscription_valid", "==", True)
        )

    # Batch get (solo se entrambi presenti)
    if email:
        doc_email = db.collection("memberships").document(email).get()
        if doc_email.exists and doc_email.to_dict().get("subscription_valid", False):
            duplicates.append(email)

    if phone:
        docs_phone = db.collection("memberships") \
            .where("phone", "==", phone) \
            .where("subscription_valid", "==", True) \
            .stream()
        for doc in docs_phone:
            duplicates.append(phone)

    if duplicates:
        raise ValueError(f"User is already an active member: {duplicates}")

    return float(fee)



def validate_event_and_membership_fast(item, membership_fee):
    ev_id = item.get("eventId")
    participants = item.get("participants", [])
    price = item.get("price")
    qty = item.get("quantity")
    fee = item.get("fee", 0)

    if not ev_id or price is None or qty is None:
        raise ValueError("Missing eventId, price or quantity")

    ev_doc = db.collection("events").document(ev_id).get()
    if not ev_doc.exists or ev_doc.to_dict().get("type") != "custom_ep12":
        raise ValueError("Invalid event type for event_and_membership")

    emails = [p["email"] for p in participants if p.get("email")]
    phones = [p["phone"] for p in participants if p.get("phone")]

    membership_docs = {}
    if emails:
        membership_docs = {
            doc.id: doc.to_dict()
            for doc in db.get_all([db.collection("memberships").document(email) for email in emails])
            if doc.exists
        }

    part_ref = db.collection("participants").document(ev_id).collection("participants_event")
    existing_by_email = {doc.get("email"): True for doc in part_ref.where("email", "in", emails).stream()} if emails else {}
    existing_by_phone = {doc.get("phone"): True for doc in part_ref.where("phone", "in", phones).stream()} if phones else {}

    duplicates = []
    minors = []

    for p in participants:
        email = p.get("email")
        phone = p.get("phone")
        birthdate = p.get("birthdate")

        if is_minor(birthdate):
            minors.append(f"{p.get('name', '')} {p.get('surname', '')}")
        if email and membership_docs.get(email, {}).get("subscription_valid", False):
            duplicates.append(email)
        if email and existing_by_email.get(email):
            duplicates.append(email)
        if phone and existing_by_phone.get(phone):
            duplicates.append(phone)

    if minors:
        raise ValueError(f"Minors not allowed: {minors}")
    if duplicates:
        raise ValueError(f"Duplicates found: {duplicates}")

    total_event = (float(price) + float(fee)) * float(qty)
    
    return truncate_float(total_event)


def create_order_service(req_json):
    try:
        purchase_type = req_json.get("purchase_type")
        if purchase_type not in ("event", "membership", "event_and_membership"):
            return jsonify({"error": "Invalid purchase_type"}), 400

        cart = req_json.get("cart", [])
        if not isinstance(cart, list) or len(cart) != 1:
            return jsonify({"error": "Only one cart item is allowed at the moment"}), 400

        cart_item = cart[0]
        total = 0
        ref_id = None

        if purchase_type == "event":
            total = validate_event_item_fast(cart_item)
            ref_id = cart_item["eventId"]

        elif purchase_type == "membership":
            total = validate_membership_fast(cart_item.get("newMember"), cart_item.get("membershipFee"))
            ref_id = None

        elif purchase_type == "event_and_membership":
            total = validate_event_and_membership_fast(cart_item, cart_item.get("membershipFee"))
            ref_id = cart_item["eventId"]

        formatted = f"{total:.2f}"

        order_request = OrderRequest(
            intent=CheckoutPaymentIntent.CAPTURE,
            purchase_units=[PurchaseUnitRequest(
                reference_id=ref_id or "membership",
                amount=AmountWithBreakdown(currency_code="EUR", value=formatted)
            )]
        )

        order = orders_controller.orders_create({"body": order_request})
        if order.status_code not in (200, 201):
            return jsonify({"error": "Failed to create PayPal order"}), order.status_code

        body = json.loads(ApiHelper.json_serialize(order.body))

        db.collection("orders").document(body["id"]).set({
            "orderId": body["id"],
            "orderStatus": body.get("status", "CREATED"),
            "purchase_type": purchase_type,
            "cart": cart,
            "total": total,
            "reference_id": ref_id,
        })

        return jsonify(body), order.status_code

    except ValueError as ve:
        return jsonify({
            "error": "validation_error",
            "message": str(ve)
        }), 400
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500





def capture_order_service(req_json):
    try:
        logger.debug("capture_order_service called with: %s", req_json)

        order_id = req_json.get("order_id")
        if not order_id:
            logger.error("Missing order_id in request body")
            return jsonify({"error": "Missing order_id in request body"}), 400

        logger.debug(f"Attempting to capture PayPal order: {order_id}")
        order_data = capture_paypal_order(order_id)
        logger.debug("Order data received: %s", order_data)

        payment_source = order_data.get("payment_source", {})
        method_used = list(payment_source.keys())[0] if payment_source else "unknown"
        logger.debug(f"Payment method used: {method_used}")

        order_status = order_data.get("status", "")
        logger.debug(f"Order status from PayPal: {order_status}")

        logger.debug("Fetching order details from Firestore")
        cart, purchase_type, ref_id, order_rec = get_order_details_from_db(order_id)
        logger.debug(f"cart: {cart}")
        logger.debug(f"purchase_type: {purchase_type}")
        logger.debug(f"ref_id: {ref_id}")
        logger.debug(f"order_rec: {order_rec}")

        db.collection("orders").document(order_id).update({"orderStatus": order_status})
        logger.debug("Updated Firestore order with status: %s", order_status)

        logger.debug("Saving purchase...")
        purchase, purchase_ref = save_purchase(order_id, order_data, order_status, purchase_type, ref_id)
        logger.debug("Purchase saved: %s", purchase)
        logger.debug("Purchase Firestore ID: %s", purchase_ref.id)

        membership_refs = []
        if purchase_type in ("membership", "event_and_membership"):
            logger.debug("Creating membership(s)")
            membership_refs = handle_membership_creation(purchase_type, cart, purchase_ref, order_data)
            logger.debug("Membership refs: %s", membership_refs)

        if purchase_type in ("event", "event_and_membership"):
            logger.debug("Saving participants")
            handle_event_participants(purchase_type, cart, membership_refs, purchase_ref)
            logger.debug("Participants saved")

        logger.debug("Deleting order document from Firestore")
        db.collection("orders").document(order_id).delete()

        logger.info("Order captured and processed successfully")
        return jsonify({
            "message": "Order captured and processed successfully",
            "purchase_id": purchase_ref.id,
            "payment_method": method_used
        }), 200

    except Exception as e:
        logger.exception("Error capturing order")
        return jsonify({"error": str(e)}), 500


def capture_paypal_order(order_id):
    print(f"[DEBUG] Performing capture for order {order_id}")
    order = orders_controller.orders_capture({"id": order_id, "prefer": "return=representation"})
    print(f"[DEBUG] PayPal capture response status: {order.status_code}")
    if not (200 <= order.status_code < 300):
        raise Exception(f"Failed to capture order (status: {order.status_code})")

    result = json.loads(ApiHelper.json_serialize(order.body))
    print("[DEBUG] Serialized order body:", result)
    return result


def get_order_details_from_db(order_id):
    print(f"[DEBUG] Fetching Firestore order document: {order_id}")
    snapshot = db.collection("orders").document(order_id).get()
    if not snapshot.exists:
        raise Exception("Order not found in DB")

    data = snapshot.to_dict()
    print("[DEBUG] Order document data:", data)
    return data["cart"][0], data["purchase_type"], data.get("reference_id"), data


from config.firebase_config import db

def save_purchase(order_id, order_data, order_status, purchase_type, ref_id):
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
    }

    print("[DEBUG] Final purchase object to save:", purchase)

    # STEP 5: Save in Firestore
    purchase_ref = db.collection("purchases").add(purchase)[1]
    print(f"[DEBUG] Purchase saved with ID: {purchase_ref.id}")

    return purchase, purchase_ref


def handle_membership_creation(purchase_type, cart, purchase_ref, order_data):
    print("[DEBUG] Starting membership creation...")
    capture_time = order_data["purchase_units"][0]["payments"]["captures"][0]["create_time"]
    members = [cart["newMember"]] if purchase_type == "membership" else cart.get("participants", [])

    membership_refs = []
    for person in members:
        print("[DEBUG] Creating membership for person:", person)
        membership = {
            "name": person["name"],
            "surname": person["surname"],
            "email": person["email"],
            "phone": person["phone"],
            "birthdate": person.get("birthdate"),
            "start_date": capture_time,
            "end_date": calculate_end_of_year(capture_time),
            "subscription_valid": True,
            "membership_sent": False,
            "membership_type": purchase_type,
            "purchase_id": purchase_ref.id,
            "purchases": [purchase_ref.id],
            "attended_events": []
        }

        ref = db.collection("memberships").add(membership)[1]
        print(f"[DEBUG] Membership saved with ID: {ref.id}")

        if purchase_type == "membership":
            db.collection("purchases").document(purchase_ref.id).update({"ref_id": ref.id})
            print(f"[DEBUG] Updated purchase {purchase_ref.id} with membership ID {ref.id}")

        membership_refs.append({
            "email": person["email"],
            "phone": person["phone"],
            "membership_id": ref.id
        })

    return membership_refs


def handle_event_participants(purchase_type, cart, membership_refs, purchase_ref):
    print("[DEBUG] Adding participants to event:", cart.get("eventId"))
    participants = cart.get("participants", [])
    for p in participants:
        print("[DEBUG] Processing participant:", p)
        membership_id = None

        if purchase_type == "event_and_membership":
            match = next((m for m in membership_refs if m["email"] == p["email"]), None)
            if match:
                membership_id = match["membership_id"]
                print(f"[DEBUG] Matched membership for event_and_membership: {membership_id}")

        elif purchase_type == "event":
            membership_doc = get_existing_membership_by_contact(p)
            if membership_doc:
                membership_id = membership_doc.id
                print(f"[DEBUG] Existing membership found for event: {membership_id}")

        participant = {
            "event_id": cart["eventId"],
            "name": p["name"],
            "surname": p["surname"],
            "email": p["email"],
            "phone": p["phone"],
            "birthdate": p.get("birthdate"),
            "membership_included": purchase_type == "event_and_membership",
            "ticket_sent": False,
            "location_sent": False,
            "purchase_id": purchase_ref.id,
            "price": cart["price"],
            "newsletterConsent": p.get("newsletterConsent", False),
            "createdAt": firestore.SERVER_TIMESTAMP
        }

        if membership_id:
            participant["membershipId"] = membership_id
            update_data = {
                "attended_events": firestore.ArrayUnion([cart["eventId"]])
            }
            if purchase_type == "event":
                update_data["purchases"] = firestore.ArrayUnion([purchase_ref.id])

            db.collection("memberships").document(membership_id).update(update_data)
            print(f"[DEBUG] Updated membership {membership_id} with event participation")

        db.collection("participants") \
            .document(cart["eventId"]) \
            .collection("participants_event") \
            .add(participant)
        print(f"[DEBUG] Participant saved: {p['email']} membershipId={membership_id}")


def get_existing_membership_by_contact(participant):
    print(f"[DEBUG] Searching membership for participant {participant['email']} or {participant.get('phone')}")
    membership_query = db.collection("memberships") \
        .where("subscription_valid", "==", True) \
        .where("email", "==", participant["email"]) \
        .stream()

    doc = next(membership_query, None)
    if not doc and participant.get("phone"):
        print("[DEBUG] Trying with phone")
        membership_query = db.collection("memberships") \
            .where("subscription_valid", "==", True) \
            .where("phone", "==", participant["phone"]) \
            .stream()
        doc = next(membership_query, None)

    if doc:
        print(f"[DEBUG] Found membership: {doc.id}")
    else:
        print("[DEBUG] No membership found")

    return doc