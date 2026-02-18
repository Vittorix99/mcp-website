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


def load_environment(override: bool = False) -> Path:
    env_path = _resolve_env_path()
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=override)
    return env_path

