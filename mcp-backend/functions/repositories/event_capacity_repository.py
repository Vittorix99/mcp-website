"""Seat holds fenced by the event version, also touched by participant writes."""
from datetime import datetime, timedelta, timezone
import datetime as datetime_types
from uuid import uuid4

from google.api_core.exceptions import Aborted, FailedPrecondition
from google.cloud import firestore

from config.firebase_config import db
from errors.service_errors import ConflictError, NotFoundError, ValidationError
from utils.events_utils import ensure_event_is_active


class EventCapacityRepository:
    @staticmethod
    def _reservations(event_id):
        return db.collection('event_capacity').document(event_id).collection('reservations')

    @staticmethod
    def _retry(operation):
        for _ in range(8):
            try:
                return operation()
            except (Aborted, FailedPrecondition):
                continue
        raise ConflictError('Disponibilità modificata contemporaneamente: riprova')

    @staticmethod
    def _validate_event(data):
        try:
            ensure_event_is_active(data)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        maximum = data.get('maxParticipants')
        if type(maximum) is not int or maximum <= 0:
            raise ConflictError('Vendite non disponibili: capienza non configurata')
        return maximum

    @staticmethod
    def _validate_hold(data):
        if (type(data.get('count')) is not int or data['count'] <= 0
                or data.get('state') not in ('reserved', 'capturing', 'consumed', 'released')
                or not isinstance(data.get('expiresAt'), datetime_types.datetime)
                or data['expiresAt'].tzinfo is None):
            raise ConflictError('Prenotazione posti non verificabile: gestione manuale richiesta')

    @staticmethod
    def _participants(event_id):
        return [doc.to_dict() or {} for doc in db.collection('participants')
                .document(event_id).collection('participants_event').stream()]

    @staticmethod
    def _commit(event, reservation_ref, data, *, create=False, previous=None, order=None, order_changes=None):
        batch = db.batch()
        batch.update(event.reference, {'capacityRevision': firestore.Increment(1)},
                     option=db.write_option(last_update_time=event.update_time))
        if create:
            batch.create(reservation_ref, data)
        else:
            batch.update(reservation_ref, data,
                         option=db.write_option(last_update_time=previous.update_time))
        if order is not None:
            batch.update(order.reference, order_changes,
                         option=db.write_option(last_update_time=order.update_time))
        batch.commit()

    def reserve(self, event_id: str, count: int) -> str:
        if type(count) is not int or count <= 0:
            raise ConflictError('Numero posti non valido')
        token = uuid4().hex
        def change():
            event = db.collection('events').document(event_id).get()
            if not event.exists:
                raise NotFoundError('Evento non trovato')
            maximum = self._validate_event(event.to_dict() or {})
            people = self._participants(event_id)
            now = datetime.now(timezone.utc)
            occupied = len(people)
            for doc in self._reservations(event_id).stream():
                hold = doc.to_dict() or {}
                self._validate_hold(hold)
                if hold['state'] in ('consumed', 'released'):
                    continue
                if hold['state'] == 'reserved' and hold['expiresAt'] <= now:
                    continue
                purchase_id = hold.get('purchaseId')
                materialized = sum(p.get('purchase_id') == purchase_id for p in people) if purchase_id else 0
                if materialized > hold['count']:
                    raise ConflictError('Partecipazioni incoerenti: verifica manuale richiesta')
                occupied += hold['count'] - materialized
            if occupied + count > maximum:
                raise ConflictError('Posti insufficienti per tutti i partecipanti')
            self._commit(event, self._reservations(event_id).document(token), {
                'count': count, 'state': 'reserved', 'createdAt': now,
                'expiresAt': now + timedelta(minutes=10), 'orderId': None, 'purchaseId': None,
            }, create=True)
            return token
        return self._retry(change)

    def bind(self, event_id: str, token: str, order_id: str) -> None:
        self._change(event_id, token, 'bind', order_id)

    def begin_capture(self, event_id: str, token: str, order_id: str) -> None:
        self._change(event_id, token, 'capture', order_id)

    def release(self, event_id: str, token: str, order_id=None) -> None:
        self._change(event_id, token, 'release', order_id)

    def attach_purchase(self, event_id: str, token: str, order_id: str, purchase_id: str) -> None:
        self._change(event_id, token, 'purchase', order_id, purchase_id)

    def complete(self, event_id: str, token: str, order_id: str, purchase_id: str) -> None:
        self._change(event_id, token, 'complete', order_id, purchase_id)

    def assert_recoverable(self, event_id: str, token: str, order_id: str) -> None:
        self._change(event_id, token, 'verify', order_id)

    def _change(self, event_id, token, operation, order_id, purchase_id=None):
        if not isinstance(token, str) or not token or '/' in token:
            raise ConflictError('Ordine senza prenotazione posti: nuovo checkout o gestione manuale richiesta')
        def change():
            event = db.collection('events').document(event_id).get()
            ref = self._reservations(event_id).document(token)
            previous = ref.get()
            if not event.exists or not previous.exists:
                raise ConflictError('Prenotazione posti non trovata')
            data = previous.to_dict() or {}
            self._validate_hold(data)
            state = data['state']
            if operation == 'release' and state == 'released':
                return
            order = None
            if order_id:
                order = db.collection('orders').document(order_id).get()
                raw = order.to_dict() or {}
                if not order.exists:
                    raise NotFoundError('Order not found')
                if (raw.get('eventId') != event_id
                        or raw.get('capacityReservationId') != token
                        or not isinstance(raw.get('participants'), list)
                        or len(raw['participants']) != data['count']):
                    raise ConflictError('Ordine e prenotazione posti non corrispondono')
            if operation == 'bind':
                if (state != 'reserved' or data.get('orderId') not in (None, order_id)
                        or data['expiresAt'] <= datetime.now(timezone.utc)):
                    raise ConflictError('Prenotazione posti scaduta o già utilizzata')
                data['orderId'] = order_id
            elif data.get('orderId') != order_id:
                raise ConflictError('Prenotazione collegata a un altro ordine')
            order_changes = {'captureStarted': raw.get('captureStarted')} if order else None
            if operation == 'capture':
                self._validate_event(event.to_dict() or {})
                if (state != 'reserved' or data['expiresAt'] <= datetime.now(timezone.utc)
                        or raw.get('captured') is not False or raw.get('captureStarted') is not False):
                    raise ConflictError('Prenotazione scaduta o pagamento già avviato: verifica ordine richiesta')
                data['state'] = 'capturing'
                order_changes = {'captureStarted': True}
            elif operation == 'release':
                if state not in ('reserved', 'capturing') or (order and raw.get('captured') is not False):
                    raise ConflictError('Pagamento non liberabile automaticamente')
                data['state'] = 'released'
            elif operation in ('purchase', 'complete', 'verify'):
                if state not in ('capturing', 'consumed'):
                    raise ConflictError('Prenotazione non attribuibile al pagamento')
                if operation == 'verify':
                    return
                if (raw.get('captured') is not True or raw.get('purchase_id') != purchase_id
                        or not purchase_id or data.get('purchaseId') not in (None, purchase_id)):
                    raise ConflictError('Acquisto e prenotazione posti non corrispondono')
                data['purchaseId'] = purchase_id
                if operation == 'complete':
                    people = self._participants(event_id)
                    if sum(p.get('purchase_id') == purchase_id for p in people) != data['count']:
                        raise ConflictError('Conversione posti incompleta: gestione manuale richiesta')
                    data['state'] = 'consumed'
            self._commit(event, ref, data, previous=previous, order=order, order_changes=order_changes)
        self._retry(change)
