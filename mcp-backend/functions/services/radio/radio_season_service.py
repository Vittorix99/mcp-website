from __future__ import annotations

from typing import List, Optional

from firebase_admin import firestore

from dto.radio.radio_season_dto import (
    CreateRadioSeasonRequestDTO,
    RadioSeasonResponseDTO,
    UpdateRadioSeasonRequestDTO,
)
from mappers.radio import create_season_dto_to_model, season_to_response_dto
from repositories.radio import RadioSeasonRepository


class RadioSeasonService:
    def __init__(self, season_repository: Optional[RadioSeasonRepository] = None):
        self.season_repository = season_repository or RadioSeasonRepository()

    def create(self, dto: CreateRadioSeasonRequestDTO) -> RadioSeasonResponseDTO:
        model = create_season_dto_to_model(dto)
        created = self.season_repository.create_from_model(model)
        return season_to_response_dto(created)

    def get_all(self) -> List[RadioSeasonResponseDTO]:
        seasons = self.season_repository.get_all()
        return [season_to_response_dto(s) for s in seasons]

    def get_by_id(self, season_id: str) -> RadioSeasonResponseDTO:
        season = self.season_repository.get_by_id_or_raise(season_id)
        return season_to_response_dto(season)

    def update(self, dto: UpdateRadioSeasonRequestDTO) -> RadioSeasonResponseDTO:
        season = self.season_repository.get_by_id_or_raise(dto.id)
        for field_name, value in dto.changes().items():
            setattr(season, field_name, value)
        season.updated_at = firestore.SERVER_TIMESTAMP
        updated = self.season_repository.update_from_model(dto.id, season)
        return season_to_response_dto(updated)

    def delete(self, season_id: str) -> None:
        self.season_repository.get_by_id_or_raise(season_id)
        self.season_repository.delete(season_id)
