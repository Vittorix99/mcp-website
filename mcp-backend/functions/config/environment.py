import os
from pathlib import Path

from dotenv import load_dotenv

ENV_VAR = "MCP_ENV"
PROD_VALUE = "prod"


def _resolve_env_path() -> Path:
    base_dir = Path(__file__).resolve().parents[1]
    if os.environ.get(ENV_VAR, "").lower() == PROD_VALUE:
        return base_dir / ".env"
    return base_dir / ".env.integration"


def _should_override_env(override: bool) -> bool:
    if override:
        return True
    if os.environ.get("FIRESTORE_EMULATOR_HOST"):
        return True
    if os.environ.get("FIREBASE_EMULATOR_HUB") or os.environ.get("FUNCTIONS_EMULATOR"):
        return True
    return False


def load_environment(override: bool = False) -> Path:
    env_path = _resolve_env_path()
    # Quando il processo parte con Doppler, le variabili sono gia iniettate
    # nell'ambiente. In quel caso non carichiamo i file .env locali per evitare
    # che configurazioni obsolete sovrascrivano la source of truth.
    if (
        os.environ.get("MCP_USE_DOPPLER") == "1"
        or os.environ.get("DOPPLER_PROJECT")
        or os.environ.get("DOPPLER_CONFIG")
    ):
        return env_path
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=_should_override_env(override))
    return env_path
