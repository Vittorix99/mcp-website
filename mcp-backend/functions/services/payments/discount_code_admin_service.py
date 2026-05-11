from __future__ import annotations

from typing import List, Optional

from dto.discount_code_dto import CreateDiscountCodeRequestDTO, DiscountCodeResponseDTO, UpdateDiscountCodeRequestDTO
from errors.service_errors import NotFoundError, ValidationError
from models import DiscountCode, DiscountType
from repositories.discount_code_repository import DiscountCodeRepository
from repositories.event_repository import EventRepository
from services.payments.discount_code_service import DiscountCodeService, discount_code_to_response


class DiscountCodeAdminService:
    def __init__(
        self,
        discount_code_repository: Optional[DiscountCodeRepository] = None,
        event_repository: Optional[EventRepository] = None,
        discount_code_service: Optional[DiscountCodeService] = None,
    ):
        self.discount_code_repository = discount_code_repository or DiscountCodeRepository()
        self.event_repository = event_repository or EventRepository()
        self.discount_code_service = discount_code_service or DiscountCodeService(
            discount_code_repository=self.discount_code_repository
        )

    def create_discount_code(
        self,
        event_id: str,
        dto: CreateDiscountCodeRequestDTO,
        admin_uid: str,
    ) -> DiscountCodeResponseDTO:
        event = self.event_repository.get_model(event_id)
        if not event:
            raise NotFoundError("Evento non trovato")

        self._validate_discount_config(dto.discount_type, dto.discount_value, float(event.price or 0))
        model = self.discount_code_repository.create(event_id, dto.to_repository_data(), admin_uid)
        return discount_code_to_response(model)

    def update_discount_code(
        self,
        discount_code_id: str,
        dto: UpdateDiscountCodeRequestDTO,
        admin_uid: str,
    ) -> DiscountCodeResponseDTO:
        current = self.discount_code_repository.get_by_id(discount_code_id)
        if not current:
            raise NotFoundError("Codice sconto non trovato")

        event = self.event_repository.get_model(current.event_id or "")
        if not event:
            raise NotFoundError("Evento non trovato")

        changes = dto.changes()
        final_restricted_membership_id = (
            changes["restricted_membership_id"]
            if "restricted_membership_id" in changes
            else current.restricted_membership_id
        )
        final_restricted_email = (
            changes["restricted_email"]
            if "restricted_email" in changes
            else current.restricted_email
        )
        if final_restricted_membership_id and final_restricted_email:
            raise ValidationError("restricted_membership_id e restricted_email sono mutualmente esclusivi")

        final_type = changes.get(
            "discount_type",
            current.discount_type.value if isinstance(current.discount_type, DiscountType) else current.discount_type,
        )
        final_value = changes.get("discount_value", current.discount_value)
        self._validate_discount_config(str(final_type), float(final_value or 0), float(event.price or 0))

        if "max_uses" in changes and int(changes["max_uses"]) < int(current.used_count or 0):
            raise ValidationError("max_uses non può essere minore degli utilizzi già consumati")

        updated = self.discount_code_repository.update(discount_code_id, changes, admin_uid)
        return discount_code_to_response(updated)

    def list_discount_codes(self, event_id: str) -> List[DiscountCodeResponseDTO]:
        if not self.event_repository.get_model(event_id):
            raise NotFoundError("Evento non trovato")
        return [discount_code_to_response(model) for model in self.discount_code_repository.list_by_event(event_id)]

    def get_discount_code(self, discount_code_id: str) -> DiscountCodeResponseDTO:
        model = self.discount_code_repository.get_by_id(discount_code_id)
        if not model:
            raise NotFoundError("Codice sconto non trovato")
        return discount_code_to_response(model)

    def disable_discount_code(self, discount_code_id: str, admin_uid: str) -> DiscountCodeResponseDTO:
        model = self.discount_code_repository.get_by_id(discount_code_id)
        if not model:
            raise NotFoundError("Codice sconto non trovato")
        updated = self.discount_code_repository.update(discount_code_id, {"is_active": False}, admin_uid)
        return discount_code_to_response(updated)

    def _validate_discount_config(self, discount_type: str, discount_value: float, event_price: float) -> None:
        try:
            self.discount_code_service.apply_discount(event_price, discount_type, discount_value)
        except ValueError as exc:
            raise ValidationError("Tipo codice sconto non valido") from exc
