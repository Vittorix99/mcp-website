from __future__ import annotations

from dto.membership_api import (
    CreateMembershipRequestDTO,
    MembershipResponseDTO,
    UpdateMembershipRequestDTO,
)
from models import Membership


def create_membership_dto_to_model(
    dto: CreateMembershipRequestDTO,
    *,
    start_date: str,
    end_date: str,
    start_year: int | None,
) -> Membership:
    return Membership(
        name=dto.name or "",
        surname=dto.surname or "",
        email=dto.email,
        phone=dto.phone,
        birthdate=dto.birthdate,
        start_date=start_date,
        end_date=end_date,
        subscription_valid=True,
        membership_sent=False,
        membership_type=dto.membership_type or "manual",
        purchase_id=None,
        send_card_on_create=bool(dto.send_card_on_create) if dto.send_card_on_create is not None else False,
        membership_fee=dto.membership_fee,
        renewals=[],
        membership_years=[start_year] if start_year else [],
    )


def apply_membership_update_dto_to_model(
    membership: Membership,
    dto: UpdateMembershipRequestDTO,
) -> Membership:
    for field_name, value in dto.changes().items():
        setattr(membership, field_name, value)
    return membership


def membership_to_response(membership: Membership) -> MembershipResponseDTO:
    return MembershipResponseDTO(
        id=membership.id,
        name=membership.name,
        surname=membership.surname,
        slug=membership.slug,
        email=membership.email,
        phone=membership.phone,
        birthdate=membership.birthdate,
        start_date=membership.start_date,
        end_date=membership.end_date,
        subscription_valid=membership.subscription_valid,
        membership_sent=membership.membership_sent,
        membership_type=membership.membership_type,
        purchase_id=membership.purchase_id,
        purchases=membership.purchases or [],
        attended_events=membership.attended_events or [],
        renewals=membership.renewals or [],
        membership_years=membership.membership_years or [],
        card_url=membership.card_url,
        card_storage_path=membership.card_storage_path,
        send_card_on_create=membership.send_card_on_create,
        membership_fee=membership.membership_fee,
        wallet_pass_id=membership.wallet_pass_id,
        wallet_url=membership.wallet_url,
    )
