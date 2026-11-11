"""Admin-only recovery of verified captures; never issues a capture or refund."""
from datetime import datetime
from decimal import Decimal, InvalidOperation

from paypalserversdk.exceptions.api_exception import ApiException

from errors.service_errors import ConflictError, ExternalServiceError, NotFoundError
from mappers.purchase_mappers import order_capture_to_response
from models import EventPurchaseAccessType, PayPalOrderInfo, PurchaseTypes
from repositories.participant_repository import ParticipantRepository
from repositories.purchase_repository import PurchaseRepository
from services.payments.event_payment_service import EventPaymentService
from utils.events_utils import ensure_event_is_active, normalize_email


class EventOrderRecoveryService:
    def __init__(self, payments=None):
        self.payments = payments or EventPaymentService.instance()

    @staticmethod
    def _money(value):
        try:
            result = Decimal(str(value))
            if not result.is_finite() or result < 0 or result != result.quantize(Decimal('0.01')):
                raise ValueError()
            return result
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ConflictError('Invalid payment amount: manual verification required') from exc

    def _read_capture(self, order):
        try:
            response = self.payments._get_paypal_gateway().get_order(order.order_id)
        except ApiException as exc:
            raise ExternalServiceError('Unable to verify PayPal order') from exc
        if not 200 <= response.status_code < 300:
            raise ExternalServiceError('Unable to verify PayPal order')
        try:
            body = response.payload
            units = body['purchase_units']
            if body['id'] != order.order_id or len(units) != 1 or units[0]['reference_id'] != order.event_id:
                raise ValueError()
            captures = units[0]['payments']['captures']
            if len(captures) != 1 or captures[0].get('final_capture') is not True:
                raise ValueError()
            info = PayPalOrderInfo.from_payload(body)
            if info.status != 'COMPLETED' or info.capture.status != 'COMPLETED' or not info.capture.capture_id:
                raise ValueError()
            if info.capture.currency_code != 'EUR':
                raise ValueError()
            gross = self._money(info.capture.amount_value)
            if gross != self._money(order.total):
                raise ValueError()
            if self._money(info.capture.paypal_fee) + self._money(info.capture.net_amount) != gross:
                raise ValueError()
            breakdown = captures[0]['seller_receivable_breakdown']
            for field in ('paypal_fee', 'net_amount'):
                if breakdown[field].get('currency_code') != 'EUR':
                    raise ValueError()
            paid_at = datetime.fromisoformat(info.capture.create_time.replace('Z', '+00:00'))
            if paid_at.tzinfo is None or not info.payer.email:
                raise ValueError()
            return info
        except (KeyError, TypeError, ValueError, AttributeError, IndexError) as exc:
            raise ConflictError('Payment is not a verified final capture for this order') from exc

    def recover_order(self, order_id):
        payments = self.payments
        order = payments.order_repository.get_model(order_id)
        if not order:
            raise NotFoundError('Order not found')
        if order.order_id != order_id or order.purchase_type != PurchaseTypes.EVENT or not order.event_id:
            raise ConflictError('Invalid event order: manual verification required')
        if order.membership_targets:
            raise ConflictError('Membership creation or renewal is outside recovery scope')
        if not isinstance(order.participants, list) or any(not isinstance(p, dict) for p in order.participants):
            raise ConflictError('Malformed stored checkout participants')
        try:
            participants = payments._participants_from_payload(order.participants)
        except ValueError as exc:
            raise ConflictError('Malformed stored checkout participant') from exc
        emails = {normalize_email(p.email) for p in participants}
        if not participants or len(emails) != len(participants):
            raise ConflictError('Missing or ambiguous checkout participants')
        lookup = order.membership_lookup
        if not isinstance(lookup, dict) or any(
            not isinstance(key, str) or not isinstance(value, dict) or normalize_email(key) not in emails
            for key, value in lookup.items()
        ) or len({normalize_email(key) for key in lookup}) != len(lookup):
            raise ConflictError('Malformed or unrelated stored membership lookup')
        price = self._money(order.event_price)
        fee = self._money(order.event_fee)
        original = self._money(order.original_price) if order.original_price is not None else None
        discount = self._money(order.discount_amount) if order.discount_amount is not None else None
        if order.discount_code_id:
            if original is None or discount is None or discount > original or len(participants) != 1:
                raise ConflictError('Invalid stored discount pricing')
            price = original - discount
        elif discount is not None:
            raise ConflictError('Discount amount without discount code')
        if (price + fee) * len(participants) != self._money(order.total):
            raise ConflictError('Stored ticket pricing does not match order total')
        price = float(price)
        try:
            ensure_event_is_active(payments._resolve_event_model(order.event_id, None))
        except ValueError as exc:
            raise ConflictError('Event is no longer available for recovery') from exc
        memberships = payments._membership_lookup_to_models(order.membership_lookup or {})
        for email, member in memberships.items():
            current = payments.membership_repository.get(member.id) if member.id else None
            if not current or normalize_email(current.email) != normalize_email(email):
                raise ConflictError('Missing or inconsistent membership reference')
        existing = payments.purchase_repository.find_by_order(order_id)
        if order.purchase_id and (not existing or order.purchase_id != existing.id):
            raise ConflictError('Order purchase link is inconsistent')
        if order.captured and order.order_status == 'COMPLETED' and existing:
            return order_capture_to_response(purchase_id=existing.id, payment_method=order.payment_method)

        info = self._read_capture(order)
        mode = order.purchase_mode or EventPurchaseAccessType.PUBLIC
        expected = payments._purchase_model(order_id, info, order.event_id, mode,
            order.discount_code_id, order.discount_code, order.discount_amount)
        if existing:
            PurchaseRepository.assert_same_checkout(existing, expected)
            expected_people = payments._event_participants(order.event_id, participants, [], existing.id,
                price, memberships, order.original_price,
                order.discount_code_id, order.discount_code)
            by_email = {p.email: p for p in expected_people}
            seen = set()
            for person in payments.participant_repository.list(order.event_id):
                if person.purchase_id != existing.id:
                    continue
                if person.email not in by_email or person.email in seen:
                    raise ConflictError('Unexpected or duplicate participants for this purchase')
                ParticipantRepository.assert_same_checkout(person, by_email[person.email])
                seen.add(person.email)

        if order.discount_code_id:
            payments.discount_code_repository.reconcile_usage(order.discount_code_id, order_id)
        if not order.captured:
            try:
                payments.order_repository.mark_captured(order_id, info.payment_method)
            except ConflictError:
                # Another verified capture/recovery can win this claim; materializers
                # below share stable IDs and reject incompatible persisted records.
                current = payments.order_repository.get_model(order_id)
                if not current or not current.captured:
                    raise
        purchase_id = payments.save_purchase(order_id, info, order.event_id, mode,
            discount_code_id=order.discount_code_id, discount_code=order.discount_code,
            discount_amount=order.discount_amount)
        payments.order_repository.set_purchase_id(order_id, purchase_id)
        payments.purchase_repository.update_participants(purchase_id, len(participants),
            sorted({member.id for member in memberships.values() if member.id}))
        payments.handle_event_participants(order.event_id, participants, [], purchase_id,
            price, memberships,
            price_original=order.original_price, discount_code_id=order.discount_code_id,
            discount_code=order.discount_code)
        payments.order_repository.update_status(order_id, 'COMPLETED')
        return order_capture_to_response(purchase_id=purchase_id, payment_method=info.payment_method)
