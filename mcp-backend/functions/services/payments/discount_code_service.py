from __future__ import annotations

from typing import Dict, Optional

from dto.discount_code_dto import DiscountCodeResponseDTO, ValidateDiscountCodeResponseDTO
from errors.service_errors import ValidationError
from models import DiscountCode, DiscountType
from repositories.discount_code_repository import DiscountCodeRepository
from repositories.membership_repository import MembershipRepository
from utils.events_utils import normalize_email


def discount_code_to_response(model: DiscountCode) -> DiscountCodeResponseDTO:
    return DiscountCodeResponseDTO(
        id=model.id or "",
        event_id=model.event_id or "",
        code=model.code or "",
        discount_type=model.discount_type.value if isinstance(model.discount_type, DiscountType) else str(model.discount_type or ""),
        discount_value=float(model.discount_value or 0),
        max_uses=int(model.max_uses or 0),
        used_count=int(model.used_count or 0),
        is_active=bool(model.is_active),
        restricted_membership_id=model.restricted_membership_id,
        restricted_email=model.restricted_email,
        created_at=_serialize_timestamp(model.created_at),
        updated_at=_serialize_timestamp(model.updated_at),
    )


def _serialize_timestamp(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return None
    if hasattr(value, "to_datetime"):
        try:
            return value.to_datetime().isoformat()
        except Exception:
            return None
    return value if isinstance(value, (str, int, float, bool)) else None


class DiscountCodeService:
    def __init__(
        self,
        discount_code_repository: Optional[DiscountCodeRepository] = None,
        membership_repository: Optional[MembershipRepository] = None,
    ):
        self.discount_code_repository = discount_code_repository or DiscountCodeRepository()
        self.membership_repository = membership_repository or MembershipRepository()

    def apply_discount(
        self,
        original_price: float,
        discount_type: str,
        discount_value: float,
    ) -> Dict[str, float]:
        original = round(float(original_price or 0), 2)
        value = round(float(discount_value or 0), 2)
        type_value = DiscountType(discount_type).value

        if original < 0:
            raise ValidationError("Prezzo evento non valido")
        if value < 0:
            raise ValidationError("Codice sconto non valido per questo importo")

        if type_value == DiscountType.PERCENTAGE.value:
            if value <= 0 or value > 100:
                raise ValidationError("Codice sconto non valido per questo importo")
            discount_amount = round(original * value / 100, 2)
            final_price = round(original - discount_amount, 2)
        elif type_value == DiscountType.FIXED.value:
            if value <= 0 or value > original:
                raise ValidationError("Codice sconto non valido per questo importo")
            discount_amount = round(value, 2)
            final_price = round(original - discount_amount, 2)
        elif type_value == DiscountType.FIXED_PRICE.value:
            if value < 0 or value > original:
                raise ValidationError("Codice sconto non valido per questo importo")
            final_price = round(value, 2)
            discount_amount = round(original - final_price, 2)
        else:
            raise ValidationError("Tipo codice sconto non valido")

        if final_price < 0 or discount_amount < 0:
            raise ValidationError("Codice sconto non valido per questo importo")

        return {"final_price": final_price, "discount_amount": discount_amount}

    def validate_discount_code(
        self,
        *,
        event_id: str,
        code: str,
        participants_count: int,
        payer_email: str,
        event_price: float,
        payer_membership_id: Optional[str] = None,
    ) -> ValidateDiscountCodeResponseDTO:
        normalized_code = (code or "").strip().upper()
        discount_code = self.discount_code_repository.get_by_code_and_event(normalized_code, event_id)
        if not discount_code:
            return self._invalid("Codice sconto non valido")

        if not discount_code.is_active:
            return self._invalid("Codice sconto non più disponibile")

        if int(discount_code.used_count or 0) >= int(discount_code.max_uses or 0):
            return self._invalid("Codice sconto non più disponibile")

        if int(participants_count or 0) != 1:
            return self._invalid("Il codice sconto è valido solo per acquisti singoli")

        normalized_payer_email = normalize_email(payer_email)
        if discount_code.restricted_membership_id:
            if payer_membership_id and payer_membership_id != discount_code.restricted_membership_id:
                return self._invalid("Codice sconto non disponibile per questo account")
            membership = self.membership_repository.get(discount_code.restricted_membership_id)
            if not membership or normalize_email(membership.email or "") != normalized_payer_email:
                return self._invalid("Codice sconto non disponibile per questo account")

        if discount_code.restricted_email:
            if normalized_payer_email != normalize_email(discount_code.restricted_email):
                return self._invalid("Codice sconto non disponibile per questa email")

        try:
            applied = self.apply_discount(
                event_price,
                discount_code.discount_type.value if isinstance(discount_code.discount_type, DiscountType) else str(discount_code.discount_type),
                float(discount_code.discount_value or 0),
            )
        except (ValueError, ValidationError):
            return self._invalid("Codice sconto non valido per questo importo")

        return ValidateDiscountCodeResponseDTO(
            valid=True,
            discount_code_id=discount_code.id,
            code=discount_code.code,
            discount_type=discount_code.discount_type.value if isinstance(discount_code.discount_type, DiscountType) else str(discount_code.discount_type),
            discount_value=float(discount_code.discount_value or 0),
            discount_amount=applied["discount_amount"],
            final_price=applied["final_price"],
        )

    def _invalid(self, message: str) -> ValidateDiscountCodeResponseDTO:
        return ValidateDiscountCodeResponseDTO(valid=False, error_message=message)
