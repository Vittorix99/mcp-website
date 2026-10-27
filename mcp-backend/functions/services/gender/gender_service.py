from typing import Protocol

import requests

from config.runtime_settings import ProviderMode, RuntimeConfigurationError, get_runtime_settings


class GenderLookupProtocol(Protocol):
    def lookup(self, name: str) -> tuple[str, float]: ...


class DeterministicGenderLookup:
    _fixtures = {"giulia": "female", "federica": "female", "anna": "female",
                 "mario": "male", "marco": "male", "luca": "male", "andrea": "male"}

    def lookup(self, name: str) -> tuple[str, float]:
        key = (name or "").strip().split(" ")[0].lower()
        gender = self._fixtures.get(key)
        return (gender, 1.0) if gender else ("N/A", 0.0)


class DisabledGenderLookup:
    def lookup(self, name: str) -> tuple[str, float]:
        return "N/A", 0.0


class HttpGenderLookup:
    def __init__(self, api_key=None):
        self.api_key = api_key

    def lookup(self, name: str) -> tuple[str, float]:
        key = (name or "").strip().split(" ")[0].lower()
        if not key:
            return "N/A", 0.0
        params = {"name": key}
        if self.api_key:
            params["apikey"] = self.api_key
        try:
            response = requests.get("https://api.genderize.io", params=params, timeout=5)
            response.raise_for_status()
            data = response.json() or {}
            return data.get("gender") or "N/A", round(float(data.get("probability") or 0), 2)
        except (requests.RequestException, TypeError, ValueError):
            return "N/A", 0.0


def build_gender_lookup(settings=None) -> GenderLookupProtocol:
    settings = settings or get_runtime_settings()
    provider = settings.providers
    if provider.gender == ProviderMode.FAKE:
        return DeterministicGenderLookup()
    if provider.gender == ProviderMode.DISABLED:
        return DisabledGenderLookup()
    if provider.gender not in {ProviderMode.STAGING, ProviderMode.LIVE}:
        raise RuntimeConfigurationError("Unsupported gender provider mode")
    return HttpGenderLookup(provider.gender_api_key.get_secret_value() if provider.gender_api_key else None)
