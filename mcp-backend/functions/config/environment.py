"""Explicit, opt-in dotenv loading for emulator runtimes only."""

import os
from pathlib import Path
from typing import MutableMapping

from dotenv import dotenv_values


def load_environment(environ: MutableMapping[str, str] | None = None) -> Path | None:
    from config.runtime_settings import RuntimeConfigurationError

    env = os.environ if environ is None else environ
    requested = env.get("MCP_ENV_FILE")
    if not requested:
        return None
    if env.get("MCP_ENV") not in {"local", "test"} or env.get("K_SERVICE"):
        raise RuntimeConfigurationError("MCP_ENV_FILE is allowed only in local/test emulator runtimes")
    path = Path(requested)
    try:
        if not path.is_file():
            raise OSError
        values = dotenv_values(path, interpolate=False)
    except (OSError, ValueError):
        raise RuntimeConfigurationError("MCP_ENV_FILE could not be read") from None
    for key, value in values.items():
        if value is not None:
            env.setdefault(key, value)
    return path
