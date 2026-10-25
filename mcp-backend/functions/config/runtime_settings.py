"""One validated, immutable environment policy. This module initializes no clients."""

from enum import Enum
from functools import lru_cache
import ipaddress
import json
import os
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError


class RuntimeConfigurationError(ValueError):
    """Configuration failure containing setting names, never supplied values."""


class RuntimeEnvironment(str, Enum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class ProviderMode(str, Enum):
    DISABLED = "disabled"
    FAKE = "fake"
    SANDBOX = "sandbox"
    STAGING = "staging"
    LIVE = "live"


class CredentialMode(str, Enum):
    EMULATOR = "emulator"
    ADC = "adc"


class _ImmutableSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FirebaseRuntimeSettings(_ImmutableSettings):
    project_id: str
    storage_bucket: str
    credential_mode: CredentialMode
    firestore_emulator_host: str | None = None
    auth_emulator_host: str | None = None
    storage_emulator_host: str | None = None
    pubsub_emulator_host: str | None = None


class ProviderRuntimeSettings(_ImmutableSettings):
    paypal: ProviderMode
    mail: ProviderMode
    sender: ProviderMode
    pass2u: ProviderMode
    gender: ProviderMode
    soundcloud: ProviderMode
    paypal_client_id: SecretStr | None = Field(default=None, repr=False)
    paypal_client_secret: SecretStr | None = Field(default=None, repr=False)
    mail_api_key: SecretStr | None = Field(default=None, repr=False)
    sender_api_key: SecretStr | None = Field(default=None, repr=False)
    sender_webhook_secret: SecretStr | None = Field(default=None, repr=False)
    pass2u_api_key: SecretStr | None = Field(default=None, repr=False)
    gender_api_key: SecretStr | None = Field(default=None, repr=False)
    soundcloud_client_id: SecretStr | None = Field(default=None, repr=False)
    soundcloud_client_secret: SecretStr | None = Field(default=None, repr=False)
    mail_allowed_recipients: tuple[str, ...] = ()
    mail_from_email: str = ""
    mail_from_name: str = ""


class RuntimeSettings(_ImmutableSettings):
    environment: RuntimeEnvironment
    firebase: FirebaseRuntimeSettings
    providers: ProviderRuntimeSettings
    backend_url: str
    allowed_origins: tuple[str, ...]
    configuration_source: str = "process_and_catalog"


_EMULATOR_KEYS = {
    "firestore": "FIRESTORE_EMULATOR_HOST",
    "auth": "FIREBASE_AUTH_EMULATOR_HOST",
    "storage": "STORAGE_EMULATOR_HOST",
    "pubsub": "PUBSUB_EMULATOR_HOST",
}
_PROVIDERS = ("paypal", "mail", "sender", "pass2u", "gender", "soundcloud")
_CATALOG = Path(__file__).with_name("environment_catalog.json")


def _reject(name: str) -> None:
    raise RuntimeConfigurationError(f"Unsafe or invalid runtime setting: {name}") from None


def _loopback(hostname: str | None) -> bool:
    if hostname == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname or "").is_loopback
    except ValueError:
        return False


def _validate_host(value: str, key: str) -> None:
    try:
        parsed = urlsplit("//" + value)
        valid = (bool(value) and _loopback(parsed.hostname) and parsed.port is not None
                 and 0 < parsed.port < 65536 and not parsed.path and not parsed.query
                 and not parsed.fragment and not parsed.username and not parsed.password)
    except (ValueError, TypeError):
        valid = False
    if not valid:
        _reject(key)


def _validate_url(value: str, key: str, offline: bool) -> None:
    try:
        parsed = urlsplit(value)
        valid = (parsed.scheme in {"http", "https"} and bool(parsed.hostname)
                 and not parsed.username and not parsed.password)
        if offline:
            valid = valid and _loopback(parsed.hostname)
        else:
            valid = valid and parsed.scheme == "https" and not _loopback(parsed.hostname)
    except (ValueError, TypeError):
        valid = False
    if not valid:
        _reject(key)


def load_runtime_settings(environ: Mapping[str, str] | None = None) -> RuntimeSettings:
    env = dict(os.environ if environ is None else environ)
    try:
        environment = RuntimeEnvironment(env.get("MCP_ENV", ""))
    except (TypeError, ValueError):
        _reject("MCP_ENV (choose local, test, staging, production)")
    try:
        catalog = json.loads(_CATALOG.read_text(encoding="utf-8"))
        if catalog["schema_version"] != 1:
            _reject("environment_catalog schema_version")
        defaults = catalog["environments"][environment.value]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        _reject("environment_catalog")

    offline = environment in {RuntimeEnvironment.LOCAL, RuntimeEnvironment.TEST}
    project = defaults["project_id"]
    bucket = defaults["storage_bucket"]
    for key in ("GCLOUD_PROJECT", "GOOGLE_CLOUD_PROJECT", "FIREBASE_PROJECT_ID"):
        if key in env and env[key] != project:
            _reject(key)
    if "STORAGE_BUCKET" in env and env["STORAGE_BUCKET"] != bucket:
        _reject("STORAGE_BUCKET")
    if env.get("FIREBASE_CONFIG"):
        try:
            firebase_config = json.loads(env["FIREBASE_CONFIG"])
            if not isinstance(firebase_config, dict):
                _reject("FIREBASE_CONFIG")
        except (TypeError, ValueError):
            _reject("FIREBASE_CONFIG")
        for key, wanted in (("projectId", project), ("storageBucket", bucket)):
            if key in firebase_config and firebase_config[key] != wanted:
                _reject("FIREBASE_CONFIG." + key)

    for key in ("FIREBASE_SERVICE_ACCOUNT_JSON", "FIREBASE_SERVICE_ACCOUNT"):
        if env.get(key):
            _reject(key)
    if offline:
        for key in ("GOOGLE_APPLICATION_CREDENTIALS", "PAYPAL_LIVE_CLIENT_ID", "PAYPAL_LIVE_CLIENT_SECRET"):
            if env.get(key):
                _reject(key)
    elif environment == RuntimeEnvironment.STAGING:
        for key in ("PAYPAL_LIVE_CLIENT_ID", "PAYPAL_LIVE_CLIENT_SECRET"):
            if env.get(key):
                _reject(key)

    hosts = {}
    for provider, key in _EMULATOR_KEYS.items():
        host = env.get(key, defaults["emulators"].get(provider))
        if offline:
            _validate_host(host or "", key)
        elif host:
            _reject(key)
        hosts[provider] = host or None
    for key in ("FUNCTIONS_EMULATOR", "FIREBASE_EMULATOR_HUB"):
        if not offline and env.get(key):
            _reject(key)

    modes = {}
    for provider in _PROVIDERS:
        key = provider.upper() + "_MODE"
        try:
            mode = ProviderMode(env.get(key, defaults["providers"][provider]))
        except (ValueError, TypeError):
            _reject(key)
        if provider == "sender" and mode != ProviderMode.DISABLED:
            _reject("SENDER_MODE (integration suspended by project owner)")
        allowed = {ProviderMode.FAKE, ProviderMode.DISABLED}
        if environment == RuntimeEnvironment.STAGING:
            allowed |= {ProviderMode.SANDBOX} if provider == "paypal" else {ProviderMode.STAGING}
        elif environment == RuntimeEnvironment.PRODUCTION:
            allowed = {ProviderMode.LIVE, ProviderMode.DISABLED}
        if provider == "paypal" and not offline:
            allowed = {ProviderMode.SANDBOX if environment == RuntimeEnvironment.STAGING else ProviderMode.LIVE}
        if mode not in allowed:
            _reject(key)
        modes[provider] = mode
    if "PAYPAL_ENV" in env:
        expected = "sandbox" if modes["paypal"] == ProviderMode.SANDBOX else "live"
        if offline or env["PAYPAL_ENV"] != expected:
            _reject("PAYPAL_ENV (use PAYPAL_MODE)")

    backend_url = env.get("BACKEND_URL", defaults["backend_url"])
    _validate_url(backend_url, "BACKEND_URL", offline)
    if not offline and backend_url.rstrip("/") != defaults["backend_url"]:
        _reject("BACKEND_URL")
    origins = tuple(filter(None, (item.strip() for item in env.get("ALLOWED_ORIGINS", ",".join(defaults["allowed_origins"])).split(","))))
    for origin in origins:
        _validate_url(origin, "ALLOWED_ORIGINS", offline)
        if environment == RuntimeEnvironment.STAGING and origin not in defaults["allowed_origins"]:
            _reject("ALLOWED_ORIGINS")
    recipients = tuple(item.strip().lower() for item in env.get("MAIL_ALLOWED_RECIPIENTS", "").split(",") if item.strip())
    if environment == RuntimeEnvironment.STAGING and modes["mail"] == ProviderMode.STAGING and not recipients:
        _reject("MAIL_ALLOWED_RECIPIENTS")
    secret_names = {
        "paypal_client_id": "PAYPAL_CLIENT_ID",
        "paypal_client_secret": "PAYPAL_CLIENT_SECRET",
        "mail_api_key": "MAILERSEND_API_KEY",
        "sender_api_key": "SENDER_API_KEY",
        "sender_webhook_secret": "SENDER_WEBHOOK_SECRET",
        "pass2u_api_key": "PASS2U_API_KEY",
        "gender_api_key": "GENDER_API_KEY",
        "soundcloud_client_id": "SOUNDCLOUD_CLIENT_ID",
        "soundcloud_client_secret": "SOUNDCLOUD_CLIENT_SECRET",
    }
    secrets = {field: SecretStr(env[key]) if env.get(key) else None for field, key in secret_names.items()}
    if environment == RuntimeEnvironment.PRODUCTION:
        for field, key in (("paypal_client_id", "PAYPAL_LIVE_CLIENT_ID"), ("paypal_client_secret", "PAYPAL_LIVE_CLIENT_SECRET")):
            if env.get(key):
                secrets[field] = SecretStr(env[key])
    try:
        return RuntimeSettings(
            environment=environment,
            firebase=FirebaseRuntimeSettings(project_id=project, storage_bucket=bucket,
                credential_mode=defaults["credential_mode"],
                firestore_emulator_host=hosts["firestore"], auth_emulator_host=hosts["auth"],
                storage_emulator_host=hosts["storage"], pubsub_emulator_host=hosts["pubsub"]),
            providers=ProviderRuntimeSettings(**modes, **secrets, mail_allowed_recipients=recipients,
                mail_from_email=env.get("MAILERSEND_FROM_EMAIL", ""),
                mail_from_name=env.get("MAILERSEND_FROM_NAME", "")),
            backend_url=backend_url, allowed_origins=origins,
        )
    except ValidationError:
        _reject("runtime settings schema")


@lru_cache(maxsize=1)
def get_runtime_settings() -> RuntimeSettings:
    return load_runtime_settings()


def clear_runtime_settings_cache() -> None:
    get_runtime_settings.cache_clear()


def safe_runtime_summary(settings: RuntimeSettings) -> dict[str, object]:
    providers = settings.providers
    return {
        "environment": settings.environment.value,
        "firebase_project_id": settings.firebase.project_id,
        "firebase_emulator": settings.firebase.credential_mode == CredentialMode.EMULATOR,
        "storage_emulator": bool(settings.firebase.storage_emulator_host),
        "providers": {name: getattr(providers, name).value for name in _PROVIDERS},
        "credential_presence": {
            "paypal": bool(providers.paypal_client_id and providers.paypal_client_secret),
            "mail": bool(providers.mail_api_key), "sender": bool(providers.sender_api_key),
            "pass2u": bool(providers.pass2u_api_key), "gender": bool(providers.gender_api_key),
            "soundcloud": bool(providers.soundcloud_client_id and providers.soundcloud_client_secret),
        },
        "configuration_source": settings.configuration_source,
    }
