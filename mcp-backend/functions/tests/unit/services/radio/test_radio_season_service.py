"""Unit tests for RadioSeasonService — no Firestore."""
import pytest
from firebase_admin import firestore

from dto.radio.radio_season_dto import CreateRadioSeasonRequestDTO, UpdateRadioSeasonRequestDTO
from errors.service_errors import RadioSeasonNotFoundError
from models.radio import RadioSeason
from services.radio.radio_season_service import RadioSeasonService


# ---------------------------------------------------------------------------
# Dummy repository
# ---------------------------------------------------------------------------

class _DummySeasonRepo:
    def __init__(self):
        self._store: dict[str, RadioSeason] = {}
        self._next_id = 1

    def _next(self):
        id_ = f"season-{self._next_id}"
        self._next_id += 1
        return id_

    def create_from_model(self, season: RadioSeason) -> RadioSeason:
        id_ = self._next()
        season.id = id_
        self._store[id_] = season
        return season

    def get_all(self) -> list:
        return list(self._store.values())

    def get_by_id_or_raise(self, season_id: str) -> RadioSeason:
        if season_id not in self._store:
            raise RadioSeasonNotFoundError(f"Not found: {season_id}")
        return self._store[season_id]

    def update_from_model(self, season_id: str, season: RadioSeason) -> RadioSeason:
        self._store[season_id] = season
        return season

    def delete(self, season_id: str) -> None:
        self._store.pop(season_id, None)


def _make_service():
    svc = RadioSeasonService()
    svc.season_repository = _DummySeasonRepo()
    return svc


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

def test_create_season_happy_path():
    svc = _make_service()
    dto = CreateRadioSeasonRequestDTO(name="Summer 2026", year=2026)

    result = svc.create(dto)

    assert result.id == "season-1"
    assert result.name == "Summer 2026"
    assert result.year == 2026


def test_create_season_stores_in_repo():
    svc = _make_service()
    dto = CreateRadioSeasonRequestDTO(name="Winter 2025", year=2025)
    svc.create(dto)

    assert len(svc.season_repository.get_all()) == 1


# ---------------------------------------------------------------------------
# get_all
# ---------------------------------------------------------------------------

def test_get_all_returns_empty_list_when_no_seasons():
    svc = _make_service()
    assert svc.get_all() == []


def test_get_all_returns_all_seasons():
    svc = _make_service()
    svc.create(CreateRadioSeasonRequestDTO(name="A", year=2025))
    svc.create(CreateRadioSeasonRequestDTO(name="B", year=2026))

    result = svc.get_all()

    assert len(result) == 2
    assert {r.name for r in result} == {"A", "B"}


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

def test_get_by_id_happy_path():
    svc = _make_service()
    svc.create(CreateRadioSeasonRequestDTO(name="Spring", year=2026))

    result = svc.get_by_id("season-1")

    assert result.name == "Spring"


def test_get_by_id_raises_not_found():
    svc = _make_service()
    with pytest.raises(RadioSeasonNotFoundError):
        svc.get_by_id("missing")


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def test_update_season_name():
    svc = _make_service()
    svc.create(CreateRadioSeasonRequestDTO(name="Old", year=2024))

    dto = UpdateRadioSeasonRequestDTO(id="season-1", name="New")
    result = svc.update(dto)

    assert result.name == "New"
    assert result.year == 2024
    assert result.updated_at == firestore.SERVER_TIMESTAMP


def test_update_season_year():
    svc = _make_service()
    svc.create(CreateRadioSeasonRequestDTO(name="Season", year=2024))

    dto = UpdateRadioSeasonRequestDTO(id="season-1", year=2026)
    result = svc.update(dto)

    assert result.year == 2026
    assert result.name == "Season"


def test_update_season_not_found():
    svc = _make_service()
    with pytest.raises(RadioSeasonNotFoundError):
        svc.update(UpdateRadioSeasonRequestDTO(id="ghost", name="X"))


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_season_happy_path():
    svc = _make_service()
    svc.create(CreateRadioSeasonRequestDTO(name="To Delete", year=2025))
    svc.delete("season-1")

    assert svc.season_repository.get_all() == []


def test_delete_season_not_found():
    svc = _make_service()
    with pytest.raises(RadioSeasonNotFoundError):
        svc.delete("ghost")
