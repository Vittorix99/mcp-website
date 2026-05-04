import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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

from domain.membership_rules import build_renewal_record, membership_years_from_renewals
from domain.participant_rules import run_basic_checks
from dto.preorder import (
    CheckoutParticipantDTO,
    EventOrderCreateResponseDTO,
    OrderCaptureDTO,
    OrderCaptureResponseDTO,
    PreOrderDTO,
)
from errors.service_errors import ExternalServiceError, NotFoundError, ValidationError
from interfaces.repositories import (
    EventRepositoryProtocol,
    MembershipRepositoryProtocol,
    MembershipSettingsRepositoryProtocol,
    OrderRepositoryProtocol,
    ParticipantRepositoryProtocol,
    PurchaseRepositoryProtocol,
)
from interfaces.services import MembershipsServiceProtocol
from mappers.payment_mappers import create_event_order_model
from mappers.purchase_mappers import order_capture_to_response, paypal_order_create_to_response
from models import (
    Event,
    EventOrder,
    EventParticipant,
    EventPurchase,
    EventPurchaseAccessType,
    Membership,
    MembershipRef,
    PaymentMethod,
    PayPalOrderCreateResponse,
    PayPalOrderInfo,
    PurchaseTypes,
)
from repositories.event_repository import EventRepository
from repositories.membership_repository import MembershipRepository
from repositories.membership_settings_repository import MembershipSettingsRepository
from repositories.order_repository import OrderRepository
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository
from services.core.error_logs_service import log_external_error
from services.memberships.renewal_command import RenewMembershipCommand
from utils.events_utils import calculate_end_of_year, ensure_event_is_active, normalize_email, normalize_phone


logger = logging.getLogger("EventPaymentService")


class EventPaymentService:
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(
        self,
        event_repository: Optional[EventRepositoryProtocol] = None,
        membership_repository: Optional[MembershipRepositoryProtocol] = None,
        membership_settings_repository: Optional[MembershipSettingsRepositoryProtocol] = None,
        order_repository: Optional[OrderRepositoryProtocol] = None,
        purchase_repository: Optional[PurchaseRepositoryProtocol] = None,
        participant_repository: Optional[ParticipantRepositoryProtocol] = None,
        memberships_service: Optional[MembershipsServiceProtocol] = None,
        paypal_client: Optional[PaypalServersdkClient] = None,
    ):
        self.paypal_client = paypal_client or PaypalServersdkClient(
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
        self.event_repository = event_repository or EventRepository()
        self.membership_repository = membership_repository or MembershipRepository()
        self.membership_settings_repository = membership_settings_repository or MembershipSettingsRepository()
        self.order_repository = order_repository or OrderRepository()
        self.purchase_repository = purchase_repository or PurchaseRepository()
        self.participant_repository = participant_repository or ParticipantRepository()
        if memberships_service is None:
            from services.memberships.memberships_service import MembershipsService

            memberships_service = MembershipsService(
                membership_repository=self.membership_repository,
                settings_repository=self.membership_settings_repository,
                purchase_repository=self.purchase_repository,
                participant_repository=self.participant_repository,
                event_repository=self.event_repository,
            )
        self.memberships_service = memberships_service

    def _get_membership_fee(self, year: Optional[int] = None) -> Optional[float]:
        target_year = str(year or datetime.now(timezone.utc).year)
        return self.membership_settings_repository.get_price_by_year(target_year)

    def _debug(self, message: str, *args):
        if self.debug:
            try:
                print("[EventPaymentService DEBUG]", message % args if args else message)
            except Exception:
                print("[EventPaymentService DEBUG]", message, *args)

    def _resolve_event_model(self, event_id: str, event_data: Optional[Event]) -> Event:
        if event_data:
            return event_data
        event_model = self.event_repository.get_model(event_id)
        if not event_model:
            raise NotFoundError("Evento non trovato")
        return event_model

    def _membership_lookup_to_models(self, lookup: Dict[str, Any]) -> Dict[str, Membership]:
        membership_models: Dict[str, Membership] = {}
        for email, payload in (lookup or {}).items():
            if not isinstance(payload, dict):
                continue
            data = dict(payload)
            membership_id = data.pop("id", None)
            membership = Membership.from_firestore(data, membership_id)
            membership_models[normalize_email(email)] = membership
        return membership_models

    def _membership_lookup_to_payloads(self, lookup: Dict[str, Membership]) -> Dict[str, Dict[str, Any]]:
        payloads: Dict[str, Dict[str, Any]] = {}
        for email, membership in (lookup or {}).items():
            payload = membership.to_firestore(include_none=True)
            if membership.id:
                payload["id"] = membership.id
            payloads[normalize_email(email)] = payload
        return payloads

    def _get_memberships_service(self) -> MembershipsServiceProtocol:
        memberships_service = getattr(self, "memberships_service", None)
        if memberships_service is None:
            from services.memberships.memberships_service import MembershipsService

            memberships_service = MembershipsService(
                membership_repository=self.membership_repository,
                settings_repository=self.membership_settings_repository,
                purchase_repository=self.purchase_repository,
                participant_repository=self.participant_repository,
                event_repository=self.event_repository,
            )
            self.memberships_service = memberships_service
        return memberships_service

    def create_order_event(
        self,
        payload: PreOrderDTO,
        event_data: Optional[Event] = None,
    ) -> EventOrderCreateResponseDTO:
        cart_item = payload.cart[0]
        event_id = cart_item.event_id
        participants = cart_item.participants or []
        membership_fee = None

        event_model = self._resolve_event_model(event_id, event_data)
        purchase_mode = event_model.purchase_mode or EventPurchaseAccessType.PUBLIC
        self._debug(
            "Processing order creation for event %s with %d participants",
            event_id,
            len(participants),
        )

        normalized_participants = self._normalize_participants(participants)
        validation_result = run_basic_checks(
            event_id,
            normalized_participants,
            event_model,
            participant_repository=self.participant_repository,
            membership_repository=self.membership_repository,
        )
        if validation_result.errors:
            err = ValidationError("validation_error")
            err.details = validation_result.errors
            raise err

        membership_targets, membership_lookup = self._determine_membership_targets(
            purchase_mode,
            normalized_participants,
            validation_result,
        )
        membership_lookup_payload = self._membership_lookup_to_payloads(membership_lookup)

        if membership_targets:
            membership_fee = self._get_membership_fee()
            if membership_fee is None:
                raise ValidationError("Missing membership fee in settings")

        total = self._compute_total(
            event_model,
            normalized_participants,
            membership_targets,
            membership_fee,
        )
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
        self._debug(
            "PayPal order created: %s (status %s)",
            order_info.order_id,
            order_info.status,
        )

        event_order = create_event_order_model(
            order_id=order_info.order_id,
            order_status=order_info.status or "CREATED",
            cart_item=cart_item,
            total=total,
            event=event_model,
            participants=normalized_participants,
            membership_targets=membership_targets,
            membership_fee=float(membership_fee) if membership_fee is not None else None,
            purchase_mode=purchase_mode,
            membership_lookup=membership_lookup_payload,
        )

        self.order_repository.save(order_info.order_id, event_order)
        self._debug("Order document stored for %s", order_info.order_id)
        return paypal_order_create_to_response(order_info)

    def capture_order_event(self, payload: OrderCaptureDTO) -> OrderCaptureResponseDTO:
        order_id = payload.order_id

        stored_order = self.order_repository.get_model(order_id)
        if not stored_order:
            raise NotFoundError("Order not found")

        if stored_order.captured and stored_order.purchase_id:
            self._debug(
                "Order %s already processed, returning existing purchase %s",
                order_id,
                stored_order.purchase_id,
            )
            return order_capture_to_response(
                purchase_id=stored_order.purchase_id,
                payment_method=stored_order.payment_method or "unknown",
            )

        order_data = self.capture_paypal_order(order_id)
        order_info = PayPalOrderInfo.from_payload(order_data)
        try:
            self.validate_capture_payload(order_info)
            self._validate_capture_amount(order_info, stored_order)
        except ValidationError:
            self._debug("Capture validation failed for %s", order_id)
            self._update_order_status(order_id, order_info.status or "UNKNOWN")
            raise

        self.order_repository.mark_captured(order_id, order_info.payment_method or "unknown")

        event_id = stored_order.event_id
        if not event_id:
            raise ValidationError("Missing event_id in stored order")
        # Anche se l'ordine PayPal era stato creato prima, non catturiamo pagamenti dopo fine evento.
        ensure_event_is_active(self._resolve_event_model(event_id, None))

        participants = self._participants_from_payload(stored_order.participants or [])
        membership_targets = self._participants_from_payload(stored_order.membership_targets or [])

        purchase_mode = stored_order.purchase_mode or EventPurchaseAccessType.PUBLIC
        purchase_id = self.save_purchase(
            order_id,
            order_info,
            event_id,
            purchase_mode,
        )
        self.order_repository.set_purchase_id(order_id, purchase_id)

        existing_memberships = self._membership_lookup_to_models(stored_order.membership_lookup or {})
        membership_refs = []
        if membership_targets:
            membership_refs = self.create_memberships_for_targets(
                membership_targets,
                stored_order.membership_fee,
                order_info.capture.create_time,
                purchase_id,
            )

        membership_ids = {
            membership.id
            for membership in existing_memberships.values()
            if membership.id
        }
        membership_ids.update(
            ref.membership_id for ref in membership_refs if ref.membership_id
        )
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
            stored_order.event_price,
            existing_memberships,
        )

        self.order_repository.delete(order_id)
        self._debug("Order %s processed and removed from staging", order_id)

        return order_capture_to_response(
            purchase_id=purchase_id,
            payment_method=order_info.payment_method or "unknown",
        )

    def _normalize_participants(
        self,
        participants: List[CheckoutParticipantDTO],
    ) -> List[CheckoutParticipantDTO]:
        normalized: List[CheckoutParticipantDTO] = []
        for participant in participants:
            normalized.append(
                CheckoutParticipantDTO.model_validate(
                    {
                        "name": participant.name.strip(),
                        "surname": participant.surname.strip(),
                        "email": normalize_email(participant.email),
                        "phone": normalize_phone(participant.phone),
                        "birthdate": participant.birthdate,
                        "newsletterConsent": participant.newsletter_consent,
                        "gender": participant.gender,
                        "gender_probability": participant.gender_probability,
                    }
                )
            )
        return normalized

    def _participants_from_payload(
        self,
        payloads: List[Dict[str, Any]],
    ) -> List[CheckoutParticipantDTO]:
        participants: List[CheckoutParticipantDTO] = []
        for payload in payloads:
            if isinstance(payload, dict):
                participants.append(CheckoutParticipantDTO.model_validate(payload))
        return participants

    def _determine_membership_targets(
        self,
        purchase_mode: EventPurchaseAccessType,
        participants: List[CheckoutParticipantDTO],
        validation_result,
    ) -> Tuple[List[CheckoutParticipantDTO], Dict[str, Membership]]:
        membership_lookup = validation_result.membership_docs or {}
        targets: List[CheckoutParticipantDTO] = []

        if (
            purchase_mode == EventPurchaseAccessType.ONLY_ALREADY_REGISTERED_MEMBERS
            and validation_result.non_members
        ):
            raise ValidationError(
                "Evento riservato ai membri: i seguenti partecipanti non risultano tesserati o attivi: "
                + ", ".join(validation_result.non_members)
            )

        if purchase_mode == EventPurchaseAccessType.ONLY_MEMBERS:
            for participant in participants:
                email = normalize_email(participant.email)
                if not email or email not in membership_lookup:
                    targets.append(participant)

        if purchase_mode == EventPurchaseAccessType.ON_REQUEST:
            raise ValidationError("Acquisto non disponibile: evento on request")

        return targets, membership_lookup

    def _compute_total(
        self,
        event: Event,
        participants: List[CheckoutParticipantDTO],
        membership_targets: List[CheckoutParticipantDTO],
        membership_fee: Optional[float],
    ) -> float:
        price = float(event.price or 0)
        fee = float(event.fee or 0)
        count = len(participants)
        total = count * (price + fee)
        return total

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
            raise ExternalServiceError(
                f"Failed to capture order (status: {order.status_code})"
            )
        result = json.loads(ApiHelper.json_serialize(order.body))
        return result

    def validate_capture_payload(self, order_info: PayPalOrderInfo) -> None:
        if order_info.status != "COMPLETED":
            raise ValidationError(
                f"Payment not completed (order={order_info.status}, capture={order_info.capture.status}, id={order_info.capture.capture_id})."
            )
        if (
            order_info.capture.status != "COMPLETED"
            or not order_info.capture.capture_id
        ):
            raise ValidationError(
                f"Payment not completed (order={order_info.status}, capture={order_info.capture.status}, id={order_info.capture.capture_id})."
            )
        if not order_info.capture.final_capture:
            logger.warning(
                "Capture is not marked as final_capture=True (id=%s)",
                order_info.capture.capture_id,
            )

    def _validate_capture_amount(
        self,
        order_info: PayPalOrderInfo,
        stored_order: EventOrder,
    ) -> None:
        expected = stored_order.total
        if expected is None:
            logger.warning(
                "No stored total found for order — skipping amount validation"
            )
            return
        try:
            captured = float(order_info.capture.amount_value)
            expected = float(expected)
        except (TypeError, ValueError):
            logger.warning(
                "Amount validation skipped — could not parse values (captured=%s, expected=%s)",
                order_info.capture.amount_value,
                expected,
            )
            return
        if abs(captured - expected) > 0.01:
            logger.error(
                "Amount mismatch: captured=%.2f expected=%.2f (order_id=%s)",
                captured,
                expected,
                order_info.capture.capture_id,
            )
            raise ValidationError(
                f"Captured amount ({captured:.2f}) does not match expected amount ({expected:.2f})"
            )

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
        return self.purchase_repository.create_from_model(purchase)

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
            # I target sono i partecipanti che devono ottenere o rinnovare la membership dal pagamento evento.
            normalized_email = normalize_email(person.email)
            existing = (
                self.membership_repository.find_by_email(normalized_email)
                if normalized_email
                else None
            )

            end_date = calculate_end_of_year(capture_time)
            if not end_date:
                fallback_year = datetime.now(timezone.utc).year
                end_date = f"31-12-{fallback_year}"

            if existing:
                # Il payment decide che serve un rinnovo, ma la regola resta nel MembershipsService.
                renewed = self._get_memberships_service().renew_existing(
                    existing,
                    RenewMembershipCommand(
                        membership_id=existing.id,
                        start_date=capture_time,
                        end_date=end_date,
                        purchase_id=purchase_id,
                        fee=fee_value,
                        membership_type=PurchaseTypes.EVENT.value,
                        send_card=True,
                        invalidate_wallet=True,
                        create_wallet=False,
                        name=person.name,
                        surname=person.surname,
                        phone=person.phone,
                        birthdate=person.birthdate,
                    ),
                )
                membership_refs.append(
                    MembershipRef(
                        email=normalized_email,
                        membership_id=renewed.id or existing.id,
                    )
                )
                continue

            # Nessuna membership trovata: dal target pagamento nasce una nuova membership completa.
            renewal_record = build_renewal_record(
                start_date=capture_time,
                end_date=end_date,
                purchase_id=purchase_id,
                fee=fee_value,
            )
            membership = Membership(
                renewals=[renewal_record],
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
                membership_years=membership_years_from_renewals(
                    [renewal_record],
                    fallback_start_date=capture_time,
                    fallback_end_date=end_date,
                ),
            )
            membership_id = self.membership_repository.create_from_model(membership)
            membership_refs.append(
                MembershipRef(email=normalized_email, membership_id=membership_id)
            )
        return membership_refs

    def handle_event_participants(
        self,
        event_id: str,
        participants: List[CheckoutParticipantDTO],
        membership_refs: List[MembershipRef],
        purchase_id: str,
        price: float,
        existing_memberships: Dict[str, Membership],
    ):
        membership_map = {
            ref.email: ref.membership_id
            for ref in (membership_refs or [])
            if ref.email
        }
        existing_map = {
            email: membership.id
            for email, membership in existing_memberships.items()
            if membership.id
        }

        for participant_dto in participants:
            normalized_email = normalize_email(participant_dto.email)
            membership_id = (
                membership_map.get(normalized_email)
                or existing_map.get(normalized_email)
            )
            participant = EventParticipant(
                event_id=event_id,
                name=participant_dto.name,
                surname=participant_dto.surname,
                email=participant_dto.email,
                phone=participant_dto.phone,
                birthdate=participant_dto.birthdate,
                membership_included=bool(membership_id),
                ticket_sent=False,
                location_sent=False,
                purchase_id=purchase_id,
                price=price,
                payment_method=PaymentMethod.WEBSITE,
                newsletter_consent=participant_dto.newsletter_consent,
                created_at=firestore.SERVER_TIMESTAMP,
            )
            if membership_id:
                participant.membership_id = membership_id
                self.membership_repository.add_attended_event_and_purchase(
                    membership_id,
                    event_id,
                    purchase_id,
                )

            self.participant_repository.create_from_model(event_id, participant)

    def _update_order_status(self, order_id, status):
        try:
            self.order_repository.update_status(order_id, status)
        except Exception:
            logger.warning("Unable to update order status for %s", order_id)


def create_order_event_service(
    req_json: PreOrderDTO,
    event_data: Optional[Event] = None,
):
    return EventPaymentService.instance().create_order_event(req_json, event_data)


def capture_order_event_service(req_json: OrderCaptureDTO):
    return EventPaymentService.instance().capture_order_event(req_json)
