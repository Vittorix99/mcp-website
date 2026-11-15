"""Approved Q-07 contract against the isolated Firestore emulator."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from config.firebase_config import db
from dto.participant_api import ParticipantCreateRequestDTO, ParticipantUpdateRequestDTO
from dto.membership_api import UpdateMembershipRequestDTO
from errors.service_errors import ConflictError
from models import EventParticipant, PaymentMethod
from repositories.membership_repository import MembershipRepository
from repositories.participant_repository import ParticipantRepository
from services.events.participants_service import ParticipantsService
from services.memberships.merge_service import MergeService
from services.memberships.memberships_service import MembershipsService
from .test_unique_registration import database_state


def register(sample, member=None, identifier='registration', **overrides):
    member = member or sample.people[0]
    data = EventParticipant(name=member.name, surname=member.surname, email=member.email,
        phone=member.phone, birthdate=member.birthdate, membership_id=member.id,
        membership_included=True, price=0, payment_method=PaymentMethod.OMAGGIO).to_firestore()
    data.update(overrides)
    ref = db.document(f'participants/{sample.event.id}/participants_event/{identifier}')
    ref.set(data)
    return ref


def wallet():
    calls = []
    return calls, SimpleNamespace(invalidate_membership_pass=lambda identifier: calls.append(identifier),
        create_membership_pass=lambda *_: None)


def test_merge_moves_scans_purchase_links_and_keeps_payment_evidence(sample):
    source, target = sample.people
    participant = register(sample)
    scan = db.document(f'entrance_scans/{sample.event.id}/scans/{source.id}')
    scan.set({'scanned_at': sample.now, 'manual': True, 'operator': 'original-admin'})
    purchase = db.document('purchases/original')
    original = {'membership_ids': [source.id], 'amount_total': '20.00', 'payer_email': source.email,
                'transaction_id': 'original-transaction'}
    purchase.set(original)
    calls, provider = wallet()
    MergeService(pass2u_service=provider).merge(source.id, target.id)
    assert participant.get().to_dict()['membershipId'] == target.id
    assert not scan.get().exists
    moved = db.document(f'entrance_scans/{sample.event.id}/scans/{target.id}').get()
    assert moved.exists and moved.to_dict()['scanned_at'] == sample.now
    assert moved.to_dict()['operator'] == 'original-admin'
    assert purchase.get().to_dict() == {**original, 'membership_ids': [target.id]}
    assert not db.document('memberships/' + source.id).get().exists
    result = MembershipRepository().get(target.id)
    assert sample.event.id in result.attended_events and 'original' in result.purchases
    assert participant.get().to_dict()['email'] == target.email
    assert participant.get().to_dict()['entered'] is True


def test_collision_leaves_database_and_wallet_unchanged(sample):
    source, target = sample.people
    register(sample, source, 'source')
    register(sample, target, 'target')
    db.document('memberships/' + source.id).update({'wallet_pass_id': 'source-wallet'})
    calls, provider = wallet()
    before = database_state()
    with pytest.raises(ConflictError):
        MergeService(pass2u_service=provider).merge(source.id, target.id)
    assert calls == []
    assert database_state() == before


@pytest.mark.parametrize('changes', [{'name': 'Other'}, {'email': 'other@example.com'},
    {'membership_id': None}, {'membership_id': 'case-member-b'}, {'birthdate': '01-01-1990'}])
def test_linked_participant_cannot_change_identity_or_membership(sample, changes):
    ref = register(sample)
    before = database_state()
    dto = ParticipantUpdateRequestDTO(event_id=sample.event.id, participant_id=ref.id, **changes)
    with pytest.raises(ConflictError):
        ParticipantsService().update(sample.event.id, ref.id, dto)
    assert database_state() == before


def test_unlinked_identity_edit_does_not_implicitly_link_by_email(sample):
    ref = register(sample, membershipId=None, membership_included=False)
    target = sample.people[1]
    ParticipantsService().update(sample.event.id, ref.id, ParticipantUpdateRequestDTO(
        event_id=sample.event.id, participant_id=ref.id, name='Lista manuale', email=target.email))
    assert ref.get().to_dict()['name'] == 'Lista manuale'
    assert not ref.get().to_dict().get('membershipId')


def test_member_edit_updates_linked_identity_without_touching_entry_or_purchase(sample):
    source = sample.people[0]
    ref = register(sample, entered=True, entered_at=sample.now, purchase_id='original')
    purchase = db.document('purchases/original')
    purchase.set({'payer_email': source.email, 'amount_total': '20.00', 'membership_ids': [source.id]})
    before_purchase = purchase.get().to_dict()
    MembershipsService().update(source.id, UpdateMembershipRequestDTO(
        membership_id=source.id, name='Nome corretto', email='corrected@example.com'))
    data = ref.get().to_dict()
    assert data['name'] == 'Nome corretto' and data['email'] == 'corrected@example.com'
    assert data['entered'] is True and data['entered_at'] == sample.now
    assert purchase.get().to_dict() == before_purchase


def test_member_edit_collision_rolls_back_everything(sample):
    source = sample.people[0]
    register(sample)
    register(sample, sample.people[1], 'unlinked', membershipId=None, email='collision@example.com')
    before = database_state()
    with pytest.raises(ConflictError):
        MembershipsService().update(source.id, UpdateMembershipRequestDTO(
            membership_id=source.id, email='collision@example.com'))
    assert database_state() == before


def test_manual_creation_failure_does_not_leave_new_membership(sample, monkeypatch):
    repository = ParticipantRepository()
    def fail(*args, **kwargs):
        raise ConflictError('Concurrent duplicate')
    monkeypatch.setattr(ParticipantRepository, '_write_once', fail)
    service = ParticipantsService(participant_repository=repository)
    before = database_state()
    with pytest.raises(ConflictError):
        service.create(ParticipantCreateRequestDTO(event_id=sample.event.id,
            name='Manuale', surname='Bonifico', email='wire@example.com', birthdate='01-01-1990',
            membership_included=True, price=20, payment_method='iban'))
    assert database_state() == before


def test_manual_new_member_and_participant_commit_together_and_retry_does_not_duplicate(sample):
    service = ParticipantsService()
    dto = ParticipantCreateRequestDTO(event_id=sample.event.id, name='Manuale', surname='Bonifico',
        email='wire@example.com', birthdate='01-01-1990', membership_included=True, price=20, payment_method='iban')
    result = service.create(dto)
    row = db.document(f'participants/{sample.event.id}/participants_event/{result.id}').get().to_dict()
    member = MembershipRepository().get(row['membershipId'])
    assert member.name == row['name'] == 'Manuale'
    assert sample.event.id in member.attended_events
    before = database_state()
    with pytest.raises(ConflictError):
        service.create(dto)
    assert database_state() == before


def test_explicit_link_copies_member_identity_and_preserves_purchase(sample):
    ref = register(sample, membershipId=None, membership_included=False, purchase_id='wire')
    db.document('purchases/wire').set({'membership_ids': [], 'payer_email': 'payer@example.com', 'amount_total': '20.00'})
    target = sample.people[1]
    ParticipantsService().update(sample.event.id, ref.id, ParticipantUpdateRequestDTO(
        event_id=sample.event.id, participant_id=ref.id, membership_id=target.id))
    data = ref.get().to_dict()
    assert data['name'] == target.name and data['email'] == target.email
    assert data['membershipId'] == target.id
    assert db.document('purchases/wire').get().to_dict() == {
        'membership_ids': [target.id], 'payer_email': 'payer@example.com', 'amount_total': '20.00'}
    assert sample.event.id in MembershipRepository().get(target.id).attended_events


def test_unlinked_manual_entry_is_persisted_and_blocks_identity_transfer(sample):
    ref = register(sample, membershipId=None, membership_included=False)
    ParticipantsService().update(sample.event.id, ref.id, ParticipantUpdateRequestDTO(
        event_id=sample.event.id, participant_id=ref.id, entered=True))
    assert ref.get().to_dict()['entered'] is True
    assert ref.get().to_dict()['entered_at'] is not None
    before = database_state()
    with pytest.raises(ConflictError):
        ParticipantsService().update(sample.event.id, ref.id, ParticipantUpdateRequestDTO(
            event_id=sample.event.id, participant_id=ref.id, membership_id=sample.people[1].id))
    assert database_state() == before


def test_large_merge_refuses_before_any_write_or_provider(sample):
    source = sample.people[0]
    batch = db.batch()
    for index in range(400):
        batch.set(db.document(f'purchases/p-{index}'), {'membership_ids': [source.id], 'amount_total': '1.00'})
    batch.commit()
    before = database_state()
    calls, provider = wallet()
    with pytest.raises(ConflictError):
        MergeService(pass2u_service=provider).merge(source.id, sample.people[1].id)
    assert database_state() == before and calls == []


def test_stale_member_update_cannot_resurrect_deleted_source(sample):
    repo = MembershipRepository()
    source = repo.get(sample.people[0].id)
    _, provider = wallet()
    MergeService(pass2u_service=provider).merge(source.id, sample.people[1].id)
    before = database_state()
    source.name = 'Stale writer'
    with pytest.raises(ConflictError):
        repo.update_from_model(source.id, source)
    assert database_state() == before


def test_stale_source_entry_sync_does_not_clear_survivor_entry_after_merge(sample, monkeypatch):
    source, target = sample.people
    ref = register(sample)
    db.document(f'entrance_scans/{sample.event.id}/scans/{source.id}').set({'scanned_at': sample.now})
    original = db.transaction
    triggered = False
    _, provider = wallet()
    def transaction_after_merge(*args, **kwargs):
        nonlocal triggered
        if not triggered:
            triggered = True
            MergeService(pass2u_service=provider).merge(source.id, target.id)
        return original(*args, **kwargs)
    monkeypatch.setattr(db, 'transaction', transaction_after_merge)
    ParticipantRepository().sync_entered_by_membership_id(sample.event.id, source.id)
    assert ref.get().to_dict()['membershipId'] == target.id
    assert ref.get().to_dict()['entered'] is True
    assert ref.get().to_dict()['entered_at'] == sample.now


def test_failed_renewal_does_not_invalidate_wallet(sample):
    from services.memberships.renewal_command import RenewMembershipCommand
    repo = MembershipRepository()
    ref = db.document('memberships/' + sample.people[0].id)
    ref.update({'wallet_pass_id': 'original-wallet'})
    stale = repo.get(ref.id)
    ref.update({'name': 'Concurrent edit'})
    calls, provider = wallet()
    before = database_state()
    with pytest.raises(ConflictError):
        MembershipsService(pass2u_service=provider).renew_existing(stale, RenewMembershipCommand(
            membership_id=ref.id, start_date=sample.now.isoformat(), end_date=f'31-12-{sample.now.year}',
            invalidate_wallet=True, create_wallet=False, send_card=False))
    assert database_state() == before and calls == []


def test_merge_relinks_member_restricted_discount_without_rewriting_usage(sample):
    source, target = sample.people
    coupon = db.document('discount_codes/member-coupon')
    original = {'restrictedMembershipId': source.id, 'usedCount': 2, 'code': 'PERSONAL'}
    coupon.set(original)
    _, provider = wallet()
    MergeService(pass2u_service=provider).merge(source.id, target.id)
    assert coupon.get().to_dict() == {**original, 'restrictedMembershipId': target.id}


def test_concurrent_manual_new_memberships_with_same_contact_do_not_duplicate(sample, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, Lock
    second = db.document('events/second-event')
    second.set(db.document('events/' + sample.event.id).get().to_dict())
    barrier, lock, calls = Barrier(2), Lock(), 0
    original = ParticipantRepository._assert_available
    def synchronize(*args, **kwargs):
        nonlocal calls
        original(*args, **kwargs)
        with lock:
            calls += 1
            should_wait = calls <= 2
        if should_wait:
            barrier.wait(timeout=10)
    monkeypatch.setattr(ParticipantRepository, '_assert_available', staticmethod(synchronize))
    def create(event_id):
        try:
            ParticipantsService().create(ParticipantCreateRequestDTO(event_id=event_id, name='Manuale',
                surname='Bonifico', email='concurrent@example.com', birthdate='01-01-1990',
                membership_included=True, price=20, payment_method='iban'))
            return 'created'
        except ConflictError:
            return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(create, [sample.event.id, second.id]))
    assert sorted(results) == ['conflict', 'created']
    members = [row for row in db.collection('memberships').stream()
               if row.to_dict().get('email') == 'concurrent@example.com']
    assert len(members) == 1


def test_operational_edit_cannot_overwrite_an_entry_committed_after_read(sample, monkeypatch):
    ref = register(sample)
    repository = ParticipantRepository()
    original = repository.get
    def stale_get(event_id, participant_id):
        model = original(event_id, participant_id)
        ref.update({'entered': True, 'entered_at': sample.now})
        return model
    monkeypatch.setattr(repository, 'get', stale_get)
    with pytest.raises(ConflictError):
        ParticipantsService(participant_repository=repository).update(sample.event.id, ref.id,
            ParticipantUpdateRequestDTO(event_id=sample.event.id, participant_id=ref.id, riduzione=True))
    assert ref.get().to_dict()['entered'] is True
    assert ref.get().to_dict()['entered_at'] == sample.now
    assert ref.get().to_dict().get('riduzione') is False


@pytest.mark.parametrize('collision', [False, True])
def test_manual_renewal_cascades_filled_identity_or_rolls_back(sample, collision):
    source = sample.people[0]
    db.document('memberships/' + source.id).update({'phone': '', 'subscription_valid': False,
        'membership_years': [sample.now.year - 1]})
    old = register(sample, phone='')
    if collision:
        register(sample, sample.people[1], 'other', membershipId=None, phone='+999123456')
    db.document('events/new-event').set(db.document('events/' + sample.event.id).get().to_dict())
    dto = ParticipantCreateRequestDTO(event_id='new-event', name=source.name, surname=source.surname,
        email=source.email, phone='+999123456', birthdate=source.birthdate, membership_included=True,
        price=20, payment_method='iban')
    before = database_state()
    if collision:
        with pytest.raises(ConflictError):
            ParticipantsService().create(dto)
        assert database_state() == before
    else:
        ParticipantsService().create(dto)
        assert old.get().to_dict()['phone'] == '+999123456'
        assert MembershipRepository().get(source.id).phone == '+999123456'


def test_location_completion_cannot_erase_concurrent_entry(sample):
    from mappers.participant_mappers import mark_participant_location_sent
    ref = register(sample)
    repo = ParticipantRepository()
    stale = repo.get(sample.event.id, ref.id)
    ref.update({'entered': True, 'entered_at': sample.now})
    location = mark_participant_location_sent(stale, sent_at=sample.now, job_id='job')
    with pytest.raises(ConflictError):
        repo.update_from_model(sample.event.id, ref.id, location)
    assert ref.get().to_dict()['entered'] is True
    assert ref.get().to_dict()['entered_at'] == sample.now


def test_merge_refuses_entry_evidence_without_scan_before_changes(sample):
    ref = register(sample, entered=True, entered_at=sample.now)
    before = database_state()
    calls, provider = wallet()
    with pytest.raises(ConflictError):
        MergeService(pass2u_service=provider).merge(sample.people[0].id, sample.people[1].id)
    assert database_state() == before and calls == []
    assert ref.get().to_dict()['entered_at'] == sample.now


@pytest.mark.parametrize('missing', ['email', 'phone'])
def test_nullable_member_contacts_do_not_break_participant_get(sample, missing):
    member = sample.people[0]
    db.document('memberships/' + member.id).update({missing: None})
    service = ParticipantsService()
    result = service.create(ParticipantCreateRequestDTO(event_id=sample.event.id,
        membership_id=member.id, name=member.name, surname=member.surname,
        email=None if missing == 'email' else member.email,
        phone=None if missing == 'phone' else member.phone,
        birthdate=member.birthdate, price=0, payment_method='omaggio'))
    response = service.get_by_id(sample.event.id, result.id)
    assert getattr(response, missing) == ''
    assert service.get_all(sample.event.id)[0].membership_id == member.id


def test_member_phone_edit_with_pending_checkout_is_rejected_before_capture(http, sample, gateway):
    from tests.synthetic_api.test_purchase_entrance_stats import create_order
    register(sample, sample.people[1], 'unlinked', membershipId=None, phone='+999987654')
    sample.people = [sample.people[0]]
    create_order(http, sample)
    before = database_state()
    with pytest.raises(ConflictError):
        MembershipsService().update(sample.people[0].id, UpdateMembershipRequestDTO(
            membership_id=sample.people[0].id, phone='+999987654'))
    assert database_state() == before
    assert gateway.capture_calls == 0


def test_member_delete_rejects_references_before_wallet_or_storage(sample):
    member = sample.people[0]
    ref = register(sample)
    db.document('memberships/' + member.id).update({'wallet_pass_id': 'wallet-to-keep'})
    db.document('purchases/receipt').set({'membership_ids': [member.id]})
    db.document(f'entrance_scans/{sample.event.id}/scans/{member.id}').set({'scanned_at': sample.now})
    calls, provider = wallet()
    before = database_state()
    with pytest.raises(ConflictError):
        MembershipsService(pass2u_service=provider).delete(member.id)
    assert database_state() == before and calls == []


@pytest.mark.parametrize('operation', ['create', 'update'])
def test_coupon_cannot_reintroduce_merged_source_reference(sample, operation):
    from repositories.discount_code_repository import DiscountCodeRepository
    source, target = sample.people
    repository = DiscountCodeRepository()
    code = repository.create(sample.event.id, {'code': 'PERSONAL', 'discount_type': 'FIXED',
        'discount_value': 1, 'max_uses': 5}, 'admin')
    _, provider = wallet()
    MergeService(pass2u_service=provider).merge(source.id, target.id)
    before = database_state()
    with pytest.raises(ConflictError):
        if operation == 'create':
            repository.create(sample.event.id, {'code': 'STALE', 'discount_type': 'FIXED',
                'discount_value': 1, 'max_uses': 5, 'restricted_membership_id': source.id}, 'admin')
        else:
            repository.update(code.id, {'restricted_membership_id': source.id}, 'admin')
    assert database_state() == before


def test_reservation_cannot_commit_stale_member_identity_before_provider(http, sample, gateway, monkeypatch):
    from repositories.event_capacity_repository import EventCapacityRepository
    from tests.synthetic_api.test_purchase_entrance_stats import order_payload
    original = EventCapacityRepository._commit
    changed = False
    def change_before_commit(*args, **kwargs):
        nonlocal changed
        if not changed and kwargs.get('create'):
            changed = True
            member = sample.people[0]
            MembershipsService().update(member.id, UpdateMembershipRequestDTO(
                membership_id=member.id, phone='+999456789'))
        return original(*args, **kwargs)
    monkeypatch.setattr(EventCapacityRepository, '_commit', staticmethod(change_before_commit))
    response = http.post('/orders', json=order_payload(sample))
    assert response.status_code == 409, response.get_json()
    assert gateway.create_calls == 0 and gateway.capture_calls == 0
    assert not list(db.collection('orders').stream())
    assert not list(db.collection_group('reservations').stream())


def test_merge_keeps_account_bindings_unchanged_on_conflict(sample):
    source, target = sample.people
    db.document('memberships/' + source.id).update({'uid': 'source-account'})
    db.document('memberships/' + target.id).update({'uid': 'target-account'})
    before = database_state()
    calls, provider = wallet()
    with pytest.raises(ConflictError):
        MergeService(pass2u_service=provider).merge(source.id, target.id)
    assert database_state() == before and calls == []


def test_merge_records_operator_and_original_source_for_history(http, sample, monkeypatch):
    from flask import request
    from api.admin import members_api
    _, provider = wallet()
    monkeypatch.setattr(members_api, 'merge_service', MergeService(pass2u_service=provider))
    http.application.add_url_rule('/merge-q07', 'merge-q07',
        lambda: members_api.merge_memberships(request), methods=['POST'])
    source, target = sample.people
    response = http.post('/merge-q07', json={'source_id': source.id, 'target_id': target.id})
    assert response.status_code == 200, response.get_json()
    operations = list(db.collection('membership_operations').stream())
    assert len(operations) == 1
    operation = operations[0].to_dict()
    assert operation['source_id'] == source.id and operation['target_id'] == target.id
    assert operation['source_snapshot']['email'] == source.email
    assert operation['operator_uid'] == 'test-admin' and operation['created_at'] is not None


@pytest.mark.parametrize('operation', ['create', 'update'])
def test_coupon_write_started_before_merge_cannot_commit_dangling_reference(sample, monkeypatch, operation):
    from repositories.discount_code_repository import DiscountCodeRepository
    repository = DiscountCodeRepository()
    code = repository.create(sample.event.id, {'code': 'INITIAL', 'discount_type': 'FIXED',
        'discount_value': 1, 'max_uses': 5}, 'admin')
    source, target = sample.people
    original_batch = db.batch
    triggered = False
    _, provider = wallet()
    class Batch:
        def __init__(self):
            self.inner = original_batch()
        def __getattr__(self, key):
            return getattr(self.inner, key)
        def commit(self, *args, **kwargs):
            nonlocal triggered
            if not triggered:
                triggered = True
                MergeService(pass2u_service=provider).merge(source.id, target.id)
            return self.inner.commit(*args, **kwargs)
    monkeypatch.setattr(db, 'batch', Batch)
    with pytest.raises(ConflictError):
        if operation == 'create':
            repository.create(sample.event.id, {'code': 'LATE', 'discount_type': 'FIXED',
                'discount_value': 1, 'max_uses': 5, 'restricted_membership_id': source.id}, 'admin')
        else:
            repository.update(code.id, {'restricted_membership_id': source.id}, 'admin')
    assert triggered
    assert all(row.to_dict().get('restrictedMembershipId') != source.id
               for row in db.collection('discount_codes').stream())


def test_checkout_checks_canonical_member_contacts_before_provider(http, sample, gateway):
    from tests.synthetic_api.test_purchase_entrance_stats import order_payload
    source = sample.people[0]
    register(sample, sample.people[1], 'other-list', membershipId=None,
        email='other-list@example.com', phone=source.phone)
    sample.people = [source]
    payload = order_payload(sample)
    payload['cart'][0]['participants'][0]['phone'] = '+999111222'
    response = http.post('/orders', json=payload)
    assert response.status_code == 409, response.get_json()
    assert gateway.create_calls == 0 and gateway.capture_calls == 0
    assert not list(db.collection('orders').stream())
