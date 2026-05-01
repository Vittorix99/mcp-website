import logging
from typing import List, Optional

from dto.purchase import CreatePurchaseRequestDTO, PurchaseActionResponseDTO, PurchaseDTO
from errors.service_errors import NotFoundError
from interfaces.repositories import PurchaseRepositoryProtocol
from mappers.purchase_mappers import create_purchase_dto_to_model, purchase_to_response
from repositories.purchase_repository import PurchaseRepository


class PurchasesService:
    def __init__(
        self,
        purchase_repository: Optional[PurchaseRepositoryProtocol] = None,
    ):
        self.logger = logging.getLogger("PurchasesService")
        self.purchase_repository = purchase_repository or PurchaseRepository()

    def get_all(self) -> List[PurchaseDTO]:
        return [
            purchase_to_response(model)
            for model in self.purchase_repository.stream_models()
        ]

    def get_by_id(
        self,
        purchase_id: Optional[str],
        slug: Optional[str] = None,
    ) -> PurchaseDTO:
        model = None
        if slug:
            model = self.purchase_repository.get_model_by_slug(slug)
        if model is None and purchase_id:
            model = self.purchase_repository.get_model(purchase_id)
        if not model:
            raise NotFoundError("Purchase not found")
        return purchase_to_response(model)

    def create(self, dto: CreatePurchaseRequestDTO) -> PurchaseActionResponseDTO:
        purchase = create_purchase_dto_to_model(dto)
        purchase_id = self.purchase_repository.create_from_model(purchase)
        self.logger.info("New purchase saved: %s", purchase_id)
        return PurchaseActionResponseDTO(message="Purchase created", id=purchase_id)

    def delete(self, purchase_id: str) -> PurchaseActionResponseDTO:
        deleted = self.purchase_repository.delete(purchase_id)
        if not deleted:
            raise NotFoundError("Purchase not found")
        self.logger.info("Purchase deleted: %s", purchase_id)
        return PurchaseActionResponseDTO(message="Purchase deleted", id=purchase_id)
