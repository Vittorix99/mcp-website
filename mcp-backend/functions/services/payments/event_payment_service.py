import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Optional

from google.cloud import firestore
from paypalserversdk.api_helper import ApiHelper
from paypalserversdk.configuration import Environment
from paypalserversdk.controllers.orders_controller import OrdersController
from paypalserversdk.exceptions.api_exception import ApiException
from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
from paypalserversdk.models.amount_with_breakdown import AmountWithBreakdown
from paypalserversdk.models.checkout_payment_intent import CheckoutPaymentIntent
from paypalserversdk.models.order_request import OrderRequest
from paypalserversdk.models.purchase_unit_request import PurchaseUnitRequest
from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient
from dto import CheckoutParticipantDTO, PreOrderDTO, OrderCaptureDTO, EventDTO, MembershipDTO
from models import (
    Event,
    EventOrder,
    EventParticipant,
    EventPurchase,
    EventPurchaseAccessType,
    Membership,
    MembershipRef,
    PayPalCaptureInfo,
    PayPalOrderCreateResponse,
    PayPalOrderInfo,
    PayPalPayerInfo,
    PurchaseTypes,
)
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.membership_settings_repository import MembershipSettingsRepository
from repositories.order_repository import OrderRepository
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository
from errors.service_errors import ExternalServiceError, NotFoundError, ValidationError
from services.core.error_logs_service import log_external_error
from utils.events_utils import (
    calculate_end_of_year,
    normalize_email,
    normalize_phone,
)
from domain.participant_rules import run_basic_checks

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
        self.event_repository = EventRepository()
        self.membership_repository = MembershipRepository()
        self.membership_settings_repository = MembershipSettingsRepository()
        self.order_repository = OrderRepository()
        self.purchase_repository = PurchaseRepository()
        self.participant_repository = ParticipantRepository()

    def _get_membership_fee(self, year: Optional[int] = None) -> Optional[float]:
        target_year = str(year or datetime.now(timezone.utc).year)
        return self.membership_settings_repository.get_price_by_year(target_year)

    def _debug(self, message: str, *args):
        if self.debug:
            try:
                print("[EventPaymentService DEBUG]", message % args if args else message)
            except Exception:
                print("[EventPaymentService DEBUG]", message, *args)

    def _resolve_event_model(self, event_id: str, event_data: Optional[EventDTO]) -> Event:
        if event_data:
            resolved_id = event_data.id or event_id
            payload = event_data.to_payload()
            payload["id"] = resolved_id
            return Event.from_firestore(payload, resolved_id)
        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            raise NotFoundError("Evento non trovato")
        return event_model

    def _membership_lookup_to_dtos(self, lookup: Dict[str, Any]) -> Dict[str, MembershipDTO]:
        membership_dtos: Dict[str, MembershipDTO] = {}
        for email, payload in (lookup or {}).items():
            dto: Optional[MembershipDTO] = None
            if isinstance(payload, MembershipDTO):
                dto = payload
            elif isinstance(payload, Membership):
                dto = MembershipDTO.from_model(payload)
            elif isinstance(payload, dict):
                if isinstance(payload.get("data"), dict):
                    data = payload.get("data") or {}
                    if payload.get("id") and "id" not in data:
                        data = {**data, "id": payload.get("id")}
                    dto = MembershipDTO.from_payload(data)
                else:
                    dto = MembershipDTO.from_payload(payload)
            if dto:
                membership_dtos[normalize_email(email)] = dto
        return membership_dtos

    def _membership_lookup_to_payloads(self, lookup: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        payloads: Dict[str, Dict[str, Any]] = {}
        for email, payload in (lookup or {}).items():
            if isinstance(payload, MembershipDTO):
                payloads[email] = payload.to_payload()
            elif isinstance(payload, Membership):
                payloads[email] = MembershipDTO.from_model(payload).to_payload()
            elif isinstance(payload, dict):
                payloads[email] = dict(payload)
        return payloads

    # ------------------------------------------------------------------ #
    # Order creation
    # ------------------------------------------------------------------ #
    def create_order_event(self, payload: PreOrderDTO, event_data: Optional[EventDTO] = None) -> Dict[str, Any]:
        cart_items = payload.cart or []
        if not isinstance(cart_items, list) or len(cart_items) != 1:
            raise ValidationError("Only one cart item is allowed")

        cart_item = cart_items[0]
        event_id = cart_item.eventId
        participants = cart_item.participants or []
        membership_fee = None

        if not event_id or not isinstance(participants, list) or not participants:
            raise ValidationError("Missing eventId or participants")

        event_model = self._resolve_event_model(event_id, event_data)
        purchase_mode = event_model.purchase_mode or EventPurchaseAccessType.PUBLIC
        self._debug("Processing order creation for event %s with %d participants", event_id, len(participants))

        normalized_participants = self._normalize_participants(participants)
        cart_item_payload = cart_item.to_payload()
        cart_item_payload["participants"] = self._participants_to_payload(normalized_participants)

        validation_result = run_basic_checks(
            event_id,
            normalized_participants,
            event_model,
        )
        if validation_result.errors:
            err = ValidationError("validation_error")
            err.details = validation_result.errors
            raise err

        membership_targets, membership_lookup = self._determine_membership_targets(
            purchase_mode, normalized_participants, validation_result
        )
        membership_lookup_payload = self._membership_lookup_to_payloads(membership_lookup)
        if membership_targets:
            membership_fee = self._get_membership_fee()
            if membership_fee is None:
                raise ValidationError("Missing membership fee in settings")

        total = self._compute_total(event_model, normalized_participants, membership_targets, membership_fee)
        formatted_total = f"{total:.2f}"

        order_request = OrderRequest(
            intent=CheckoutPaymentIntent.CAPTURE,
            purchase_units=[
                PurchaseUnitRequest(
                    reference_id=event_id,
                    amount=AmountWithBreakdown(currency_code="EUR", value=formatted_total),
                )
            ],
        )
        try:
            order = self.orders_controller.orders_create({"body": order_request})
        except ApiException as exc:
            status = getattr(exc, "response_code", None)
            log_external_error(
                service="PayPal",
                operation="create_order_event",
                source="services.payments.event_payment_service.create_order_event",
                message=f"Failed to create PayPal order (status: {status})",
                status_code=status,
                payload=str(exc),
                context={"event_id": event_id},
            )
            raise ExternalServiceError(
                f"Failed to create PayPal order (status: {status})"
            ) from exc
        if order.status_code not in (200, 201):
            log_external_error(
                service="PayPal",
                operation="create_order_event",
                source="services.payments.event_payment_service.create_order_event",
                message="Failed to create PayPal order",
                status_code=order.status_code,
                payload=str(order.body),
                context={"event_id": event_id},
            )
            raise ExternalServiceError("Failed to create PayPal order")

        body = json.loads(ApiHelper.json_serialize(order.body))
        order_info = PayPalOrderCreateResponse.from_payload(body)
        if not order_info.order_id:
            raise ExternalServiceError("Missing PayPal order id")
        self._debug("PayPal order created: %s (status %s)", order_info.order_id, order_info.status)

        cart_payload = [cart_item_payload]
        participants_payload = self._participants_to_payload(normalized_participants)
        membership_targets_payload = self._participants_to_payload(membership_targets)
        event_order = EventOrder(
            order_id=order_info.order_id,
            order_status=order_info.status or "CREATED",
            purchase_type=PurchaseTypes.EVENT,
            cart=cart_payload,
            total=total,
            reference_id=event_id,
            event_meta=cart_item.eventMeta or {},
            event_id=event_id,
            participants=participants_payload,
            event_price=float(event_model.price or 0),
            event_fee=float(event_model.fee or 0),
            membership_targets=membership_targets_payload,
            membership_fee=float(membership_fee) if membership_fee is not None else None,
            purchase_mode=purchase_mode,
            membership_lookup=membership_lookup_payload,
        )

        self.order_repository.save(order_info.order_id, event_order)
        self._debug("Order document stored for %s", order_info.order_id)
        return order_info.payload

    # ------------------------------------------------------------------ #
    # Order capture
    # ------------------------------------------------------------------ #
    def capture_order_event(self, payload: OrderCaptureDTO) -> Dict[str, Any]:
        order_id = payload.order_id
        if not order_id:
            raise ValidationError("Missing order_id in request body")

        order_data = self.capture_paypal_order(order_id)
        order_info = PayPalOrderInfo.from_payload(order_data)
        try:
            self.validate_capture_payload(order_info)
        except ValidationError:
            self._debug("Capture validation failed for %s", order_id)
            self._update_order_status(order_id, order_info.status or "UNKNOWN")
            raise

        order_data_dict = self.order_repository.get(order_id)
        if not order_data_dict:
            raise NotFoundError("Order not found")
        event_order = EventOrder.from_firestore(order_data_dict, order_id)

        event_id = event_order.event_id
        participants = self._participants_from_payload(event_order.participants or [])
        membership_targets = self._participants_from_payload(event_order.membership_targets or [])

        purchase_mode = event_order.purchase_mode or EventPurchaseAccessType.PUBLIC
        purchase_id = self.save_purchase(
            order_id,
            order_info,
            event_id,
            purchase_mode,
        )

        existing_memberships = event_order.membership_lookup or {}
        membership_refs = []
        if membership_targets:
            membership_refs = self.create_memberships_for_targets(
                membership_targets,
                event_order.membership_fee,
                order_info.capture.create_time,
                purchase_id,
            )

        membership_ids = {
            dto.id
            for dto in self._membership_lookup_to_dtos(existing_memberships).values()
            if dto.id
        }
        membership_ids.update(ref.membership_id for ref in membership_refs if ref.membership_id)
        self.purchase_repository.update_participants(
            purchase_id,
            len(participants),
            sorted(membership_ids),
        )

        self.handle_event_participants(
            event_id,
            participants,
            membership_refs,
            purchase_id,
            event_order.event_price,
            existing_memberships,
        )

        self.order_repository.delete(order_id)
        self._debug("Order %s processed and removed from staging", order_id)

        return {
            "message": "Order captured and processed successfully",
            "purchase_id": purchase_id,
            "payment_method": order_info.payment_method or "unknown",
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _normalize_participants(
        self, participants: List[CheckoutParticipantDTO]
    ) -> List[CheckoutParticipantDTO]:
        normalized: List[CheckoutParticipantDTO] = []
        for participant in participants:
            normalized.append(
                CheckoutParticipantDTO(
                    name=participant.name.strip() if participant.name else "",
                    surname=participant.surname.strip() if participant.surname else "",
                    email=normalize_email(participant.email),
                    phone=normalize_phone(participant.phone),
                    birthdate=participant.birthdate,
                    newsletter_consent=participant.newsletter_consent,
                    gender=participant.gender,
                    gender_probability=participant.gender_probability,
                )
            )
        return normalized

    def _participants_to_payload(
        self, participants: List[CheckoutParticipantDTO]
    ) -> List[Dict[str, Any]]:
        return [participant.to_payload() for participant in participants]

    def _participants_from_payload(self, payloads: List[Dict[str, Any]]) -> List[CheckoutParticipantDTO]:
        participants: List[CheckoutParticipantDTO] = []
        for payload in payloads:
            if isinstance(payload, dict):
                participants.append(CheckoutParticipantDTO.from_payload(payload))
        return participants

    def _determine_membership_targets(
        self,
        purchase_mode: EventPurchaseAccessType,
        participants: List[CheckoutParticipantDTO],
        validation_result,
    ) -> Tuple[List[CheckoutParticipantDTO], Dict[str, Any]]:
        membership_lookup = validation_result.membership_docs or {}
        targets: List[CheckoutParticipantDTO] = []

        if purchase_mode == EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS and validation_result.non_members:
            raise ValidationError(
                "Evento riservato ai membri: i seguenti partecipanti non risultano tesserati o attivi: "
                + ", ".join(validation_result.non_members)
            )

        if purchase_mode == EventPurchaseAccessType.ONLY_MEMBERS:
            for p in participants:
                email = normalize_email(p.email)
                if not email or email not in membership_lookup:
                    targets.append(p)

        if purchase_mode == EventPurchaseAccessType.ON_REQUEST:
            raise ValidationError("Acquisto non disponibile: evento on request")

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
        try:
            order = self.orders_controller.orders_capture(
                {"id": order_id, "prefer": "return=representation"}
            )
        except ApiException as exc:
            status = getattr(exc, "response_code", None)
            log_external_error(
                service="PayPal",
                operation="capture_order_event",
                source="services.payments.event_payment_service.capture_paypal_order",
                message=f"Failed to capture order (status: {status})",
                status_code=status,
                payload=str(exc),
                context={"order_id": order_id},
            )
            raise ExternalServiceError(
                f"Failed to capture order (status: {status})"
            ) from exc
        if not (200 <= order.status_code < 300):
            log_external_error(
                service="PayPal",
                operation="capture_order_event",
                source="services.payments.event_payment_service.capture_paypal_order",
                message=f"Failed to capture order (status: {order.status_code})",
                status_code=order.status_code,
                payload=str(order.body),
                context={"order_id": order_id},
            )
            raise ExternalServiceError(f"Failed to capture order (status: {order.status_code})")
        result = json.loads(ApiHelper.json_serialize(order.body))
        return result

    def validate_capture_payload(self, order_info: PayPalOrderInfo) -> None:
        if order_info.status != "COMPLETED":
            raise ValidationError(
                f"Payment not completed (order={order_info.status}, capture={order_info.capture.status}, id={order_info.capture.capture_id})."
            )
        if order_info.capture.status != "COMPLETED" or not order_info.capture.capture_id:
            raise ValidationError(
                f"Payment not completed (order={order_info.status}, capture={order_info.capture.status}, id={order_info.capture.capture_id})."
            )
        if not order_info.capture.final_capture:
            logger.warning("Capture is not marked as final_capture=True (id=%s)", order_info.capture.capture_id)

    def save_purchase(
        self,
        order_id: str,
        order_info: PayPalOrderInfo,
        event_id: str,
        purchase_mode: EventPurchaseAccessType,
    ) -> str:
        purchase = EventPurchase(
            payer_name=order_info.payer.given_name,
            payer_surname=order_info.payer.surname,
            payer_email=order_info.payer.email,
            amount_total=order_info.capture.amount_value,
            currency=order_info.capture.currency_code,
            paypal_fee=order_info.capture.paypal_fee,
            net_amount=order_info.capture.net_amount,
            transaction_id=order_info.capture.capture_id,
            order_id=order_id,
            status=order_info.status,
            timestamp=order_info.capture.create_time,
            ref_id=event_id,
            payment_method=order_info.payment_method,
            capture_status=order_info.capture.status,
            event_id=event_id,
            event_purchase_type=purchase_mode,
        )

        purchase_id = self.purchase_repository.create(purchase)
        return purchase_id

    def create_memberships_for_targets(
        self,
        targets: List[CheckoutParticipantDTO],
        membership_fee,
        capture_time: str,
        purchase_id: str,
    ) -> List[MembershipRef]:
        membership_refs: List[MembershipRef] = []
        fee_value = float(membership_fee) if membership_fee is not None else None
        for person in targets:
            normalized_email = normalize_email(person.email)
            existing = self.membership_repository.find_model_by_email(normalized_email) if normalized_email else None

            end_date = calculate_end_of_year(capture_time)
            if not end_date:
                fallback_year = datetime.now(timezone.utc).year
                end_date = f"31-12-{fallback_year}"

            if existing:
                update_dto = MembershipDTO(
                    subscription_valid=True,
                    start_date=capture_time,
                    end_date=end_date,
                    membership_sent=False,
                    send_card_on_create=True,
                    membership_type=PurchaseTypes.EVENT.value,
                    membership_fee=fee_value,
                )
                if not existing.purchase_id:
                    update_dto.purchase_id = purchase_id
                if person.name and not existing.name:
                    update_dto.name = person.name
                if person.surname and not existing.surname:
                    update_dto.surname = person.surname
                if person.phone and not existing.phone:
                    update_dto.phone = person.phone
                if person.birthdate and not existing.birthdate:
                    update_dto.birthdate = person.birthdate

                self.membership_repository.update_from_model(existing.id, update_dto)
                self.membership_repository.append_purchase(existing.id, purchase_id)
                membership_refs.append(
                    MembershipRef(email=normalized_email, membership_id=existing.id)
                )
                continue

            membership = Membership(
                name=person.name,
                surname=person.surname,
                email=normalized_email,
                phone=person.phone,
                birthdate=person.birthdate,
                start_date=capture_time,
                end_date=end_date,
                subscription_valid=True,
                membership_sent=False,
                send_card_on_create=True,
                membership_type=PurchaseTypes.EVENT.value,
                purchase_id=purchase_id,
                purchases=[purchase_id],
                attended_events=[],
                membership_fee=fee_value,
            )
            membership_id = self.membership_repository.create_from_model(membership)
            membership_refs.append(
                MembershipRef(email=normalized_email, membership_id=membership_id)
            )
        return membership_refs

    def handle_event_participants(
        self,
        event_id,
        participants: List[CheckoutParticipantDTO],
        membership_refs,
        purchase_id,
        price,
        existing_memberships,
    ):
        membership_map = {
            ref.email: ref.membership_id for ref in (membership_refs or []) if ref.email
        }
        existing_map = {
            email: dto.id
            for email, dto in self._membership_lookup_to_dtos(existing_memberships).items()
            if dto.id
        }

        for p in participants:
            normalized_email = normalize_email(p.email)
            membership_id = membership_map.get(normalized_email) or existing_map.get(normalized_email)
            participant = EventParticipant(
                event_id=event_id,
                name=p.name,
                surname=p.surname,
                email=p.email,
                phone=p.phone,
                birthdate=p.birthdate,
                membership_included=bool(membership_id),
                ticket_sent=False,
                location_sent=False,
                purchase_id=purchase_id,
                price=price,
                payment_method="website",
                newsletter_consent=p.newsletter_consent,
                created_at=firestore.SERVER_TIMESTAMP,
            )
            if membership_id:
                participant.membership_id = membership_id
                self.membership_repository.add_attended_event_and_purchase(
                    membership_id,
                    event_id,
                    purchase_id,
                )

            self.participant_repository.create(event_id, participant.to_firestore(include_none=True))

    def _update_order_status(self, order_id, status):
        try:
            self.order_repository.update_status(order_id, status)
        except Exception:
            logger.warning("Unable to update order status for %s", order_id)

def create_order_event_service(req_json: PreOrderDTO, event_data: Optional[EventDTO] = None):
    return EventPaymentService.instance().create_order_event(req_json, event_data)


def capture_order_event_service(req_json: OrderCaptureDTO):
    return EventPaymentService.instance().capture_order_event(req_json)
