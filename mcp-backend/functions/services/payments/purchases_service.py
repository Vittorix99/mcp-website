import logging
from typing import Dict, List, Optional

from dto import PurchaseDTO
from interfaces.repositories import PurchaseRepositoryProtocol
from models import Purchase
from models.enums import PurchaseTypes
from repositories.purchase_repository import PurchaseRepository
from errors.service_errors import NotFoundError, ValidationError


class PurchasesService:
    def __init__(self, purchase_repository: Optional[PurchaseRepositoryProtocol] = None):
        self.logger = logging.getLogger("PurchasesService")
        self.purchase_repository = purchase_repository or PurchaseRepository()

    def _serialize(self, purchase: Purchase) -> Dict:
        payload = PurchaseDTO.from_model(purchase).to_payload()
        payload["id"] = purchase.id
        return payload

    def _parse_purchase_type(self, value: Optional[str]) -> PurchaseTypes:
        if not value:
            return PurchaseTypes.EVENT
        try:
            return PurchaseTypes(str(value))
        except ValueError:
            return PurchaseTypes.EVENT

    def get_all(self) -> List[Dict]:
        purchases = [self._serialize(model) for model in self.purchase_repository.stream_models()]
        return purchases

    def get_by_id(self, purchase_id: Optional[str], slug: Optional[str] = None) -> Dict:
        model = None
        if slug:
            model = self.purchase_repository.get_model_by_slug(slug)
        if model is None and purchase_id:
            model = self.purchase_repository.get_model(purchase_id)
        if not model:
            raise NotFoundError("Purchase not found")
        return self._serialize(model)

    def create(self, dto: PurchaseDTO) -> Dict:
        error = dto.validate(is_update=False)
        if error:
            raise ValidationError(error)

        purchase = Purchase(
            payer_name=dto.payer_name or "",
            payer_surname=dto.payer_surname or "",
            payer_email=dto.payer_email or "",
            amount_total=dto.amount_total or "",
            currency=dto.currency or "",
            paypal_fee=dto.paypal_fee,
            net_amount=dto.net_amount,
            transaction_id=dto.transaction_id or "",
            order_id=dto.order_id or "",
            status=dto.status or "COMPLETED",
            timestamp=dto.timestamp,
            purchase_type=self._parse_purchase_type(dto.type),
            ref_id=dto.ref_id,
            payment_method=dto.payment_method,
            capture_status=dto.capture_status,
        )

        purchase_id = self.purchase_repository.create_from_model(purchase)
        self.logger.info("New purchase saved: %s", purchase_id)
        return {"message": "Purchase created", "id": purchase_id}

    def delete(self, purchase_id: str) -> Dict:
        deleted = self.purchase_repository.delete(purchase_id)
        if not deleted:
            raise NotFoundError("Purchase not found")
        self.logger.info("Purchase deleted: %s", purchase_id)
        return {"message": "Purchase deleted"}
