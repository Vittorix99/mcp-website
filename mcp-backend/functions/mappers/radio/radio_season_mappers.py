from __future__ import annotations

from firebase_admin import firestore

from dto.radio.radio_season_dto import CreateRadioSeasonRequestDTO, RadioSeasonResponseDTO
from models.radio import RadioSeason


def create_season_dto_to_model(dto: CreateRadioSeasonRequestDTO) -> RadioSeason:
    return RadioSeason(
        name=dto.name,
        year=dto.year,
        description=dto.description,
        created_at=firestore.SERVER_TIMESTAMP,
        updated_at=firestore.SERVER_TIMESTAMP,
    )


def season_to_response_dto(season: RadioSeason) -> RadioSeasonResponseDTO:
    return RadioSeasonResponseDTO(
        id=season.id,
        name=season.name,
        year=season.year,
        description=season.description,
        created_at=season.created_at,
        updated_at=season.updated_at,
    )
