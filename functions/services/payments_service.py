import os
import logging
import json
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

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO)

# --- Initialize PayPal Client ---
paypal_client = PaypalServersdkClient(
    client_credentials_auth_credentials=ClientCredentialsAuthCredentials(
        o_auth_client_id=os.getenv("PAYPAL_CLIENT_ID"),
        o_auth_client_secret=os.getenv("PAYPAL_CLIENT_SECRET"),
    ),
    environment=Environment.SANDBOX,
)

# PayPal Controllers
orders_controller: OrdersController = paypal_client.orders
payments_controller: PaymentsController = paypal_client.payments

def create_order_service(req_json):
    """Handles PayPal order creation"""
    try:
        cart = req_json.get("cart", [])
        if not cart:
            return jsonify({"error": "Cart is empty or missing"}), 400

        # Calculate total amount in EUR
        total_amount = 0
        for item in cart:
            ticket_price = item.get("ticketPrice")
            quantity = item.get("quantity")
            
            if ticket_price is None:
                return jsonify({"error": f"Ticket price is missing for event {item.get('eventId')}"}), 400
            
            if quantity is None:
                return jsonify({"error": f"Quantity is missing for event {item.get('eventId')}"}), 400
            
            try:
                total_amount += float(ticket_price) * float(quantity)
            except ValueError:
                return jsonify({"error": f"Invalid ticket price or quantity for event {item.get('eventId')}"}), 400

        formatted_amount = "{:.2f}".format(total_amount)
        
        event_id = cart[0].get("eventId")
        
        event_ref = db.collection('events').document(event_id)
        event = event_ref.get()
        if not event.exists:
            return jsonify({"error": "Event not found"}), 404
        
        event_data = event.to_dict()
        if not event_data.get('active', False):
            return jsonify({"error": "Event is inactive"}), 400

        # Create order request
        order_request = OrderRequest(
            intent=CheckoutPaymentIntent.CAPTURE,
            purchase_units=[
                PurchaseUnitRequest(
                    reference_id=event_id,
                    amount=AmountWithBreakdown(
                        currency_code="EUR",
                        value=formatted_amount
                    )
                )
            ],
        )

        order = orders_controller.orders_create({"body": order_request})

        if order.status_code in [200, 201]:
            return jsonify(ApiHelper.json_serialize(order.body)), order.status_code
        else:
            return jsonify({"error": "Failed to create order", "details": order.body}), order.status_code

    except Exception as e:
        logging.exception("Error creating order")
        return jsonify({"error": "An error occurred while creating the order", "details": str(e)}), 500

def capture_order_service(req_json):
    """Handles capturing a PayPal order"""
    try:
        order_id = req_json.get("order_id")
        if not order_id:
            return jsonify({"error": "Missing order_id in request body"}), 400

        order = orders_controller.orders_capture({"id": order_id, "prefer": "return=representation"})

        if not (200 <= order.status_code < 300):
            return jsonify({"error": "Failed to capture order", "status": order.status_code, "response": order.body}), order.status_code

        order_data = json.loads(ApiHelper.json_serialize(order.body))

        # Extract payer info
        payer = order_data.get("payer", {})
        name_info = payer.get("name", {})
        email = payer.get("email_address", "")

        # Extract event ID and payment details
        purchase_units = order_data.get("purchase_units", [])
        pu = purchase_units[0] if purchase_units else {}

        payments = pu.get("payments", {})
        captures = payments.get("captures", [])
        capture = captures[0] if captures else {}

        transaction_id = capture.get("id", "")
        amount_total = capture.get("amount", {}).get("value", "")
        currency = capture.get("amount", {}).get("currency_code", "")
        capture_time = capture.get("create_time", "")
        order_status = order_data.get("status", "")

        # PayPal fee details
        seller_receivable_breakdown = capture.get("seller_receivable_breakdown", {})
        paypal_fee = seller_receivable_breakdown.get("paypal_fee", {}).get("value", "")
        net_amount = seller_receivable_breakdown.get("net_amount", {}).get("value", "")

        event_id = pu.get("reference_id", "")

        # Create ticket object
        ticket = {
            "first_name": name_info.get("given_name", ""),
            "last_name": name_info.get("surname", ""),
            "email": email,
            "paid_amount_total": amount_total,
            "net_amount": net_amount,
            "paypal_fee": paypal_fee,
            "currency": currency,
            "transaction_id": transaction_id,
            "event_id": event_id,
            "order_status": order_status,
            "timestamp": capture_time,
            "ticket_sent": False
        }

        # Save the ticket to Firestore
        doc_ref = db.collection("tickets").add(ticket)

        return jsonify({
            "message": "Order captured and ticket created successfully",
            "ticket_id": doc_ref[1].id,
            "ticket": ticket
        }), 200

    except Exception as e:
        logging.exception("Error capturing order")
        return jsonify({"error": "An error occurred while capturing the order", "details": str(e)}), 500