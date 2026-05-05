from __future__ import annotations

from typing import List

from errors.service_errors import RadioSeasonNotFoundError
from models.radio import RadioSeason
from repositories.base import BaseRepository


class RadioSeasonRepository(BaseRepository[RadioSeason]):
    def __init__(self):
        super().__init__("radio_seasons", RadioSeason)

    def create_from_model(self, season: RadioSeason) -> RadioSeason:
        doc_id = self.create(season)
        return self.get_by_id_or_raise(doc_id)

    def get_all(self) -> List[RadioSeason]:
        return super().get_all()

    def get_by_id_or_raise(self, season_id: str) -> RadioSeason:
        season = self.get_by_id(season_id)
        if season is None:
            raise RadioSeasonNotFoundError(f"Radio season '{season_id}' not found")
        return season

    def update_from_model(self, season_id: str, season: RadioSeason) -> RadioSeason:
        self.update(season_id, season)
        return self.get_by_id_or_raise(season_id)

    def delete(self, season_id: str) -> None:
        self.collection.document(season_id).delete()
