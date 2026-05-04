"""Integration tests for RadioSeasonService — hits the Firestore emulator."""
import pytest

from dto.radio.radio_season_dto import CreateRadioSeasonRequestDTO, UpdateRadioSeasonRequestDTO
from errors.service_errors import RadioSeasonNotFoundError


@pytest.mark.integration
def test_season_crud(season_service, season_dto):
    """Full create → get → update → delete lifecycle."""
    season_id = None
    try:
        created = season_service.create(season_dto)
        season_id = created.id
        assert season_id
        assert created.name == season_dto.name
        assert created.year == season_dto.year

        fetched = season_service.get_by_id(season_id)
        assert fetched.id == season_id
        assert fetched.name == season_dto.name

        update_dto = UpdateRadioSeasonRequestDTO.model_validate(
            {"id": season_id, "name": "Updated Name", "year": 2027}
        )
        updated = season_service.update(update_dto)
        assert updated.name == "Updated Name"
        assert updated.year == 2027

        season_service.delete(season_id)
        season_id = None

        with pytest.raises(RadioSeasonNotFoundError):
            season_service.get_by_id(season_id or "deleted")
    finally:
        if season_id:
            season_service.delete(season_id)


@pytest.mark.integration
def test_get_all_includes_created_season(season_service, season_dto):
    season_id = None
    try:
        created = season_service.create(season_dto)
        season_id = created.id

        all_seasons = season_service.get_all()
        assert any(s.id == season_id for s in all_seasons)
    finally:
        if season_id:
            season_service.delete(season_id)


@pytest.mark.integration
def test_get_by_id_not_found(season_service):
    with pytest.raises(RadioSeasonNotFoundError):
        season_service.get_by_id("nonexistent-season-id")


@pytest.mark.integration
def test_update_partial_fields(season_service, season_dto):
    """Update only the name, year should remain unchanged."""
    season_id = None
    try:
        created = season_service.create(season_dto)
        season_id = created.id
        original_year = created.year

        update_dto = UpdateRadioSeasonRequestDTO.model_validate(
            {"id": season_id, "name": "Partial Update"}
        )
        updated = season_service.update(update_dto)

        assert updated.name == "Partial Update"
        assert updated.year == original_year
    finally:
        if season_id:
            season_service.delete(season_id)


@pytest.mark.integration
def test_delete_not_found(season_service):
    with pytest.raises(RadioSeasonNotFoundError):
        season_service.delete("nonexistent-season-id")
