import pytest

from config.environment import load_environment
from config.runtime_settings import RuntimeConfigurationError


def test_local_loads_only_explicit_mcp_env_file(tmp_path):
    selected = tmp_path / "chosen.env"
    selected.write_text("TEST_CONFIG_VALUE=from-file\nUNCHANGED=replaced\n")
    env = {"MCP_ENV": "local", "MCP_ENV_FILE": str(selected), "UNCHANGED": "process"}
    assert load_environment(env) == selected
    assert env["TEST_CONFIG_VALUE"] == "from-file"
    assert env["UNCHANGED"] == "process"


def test_no_implicit_dotenv_loading(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("UNEXPECTED=secret\n")
    (tmp_path / ".env.integration").write_text("UNEXPECTED=secret\n")
    env = {"MCP_ENV": "test"}
    assert load_environment(env) is None
    assert "UNEXPECTED" not in env


@pytest.mark.parametrize("environment", ["staging", "production", "prod"])
def test_cloud_runtime_rejects_mcp_env_file(environment):
    with pytest.raises(RuntimeConfigurationError) as error:
        load_environment({"MCP_ENV": environment, "MCP_ENV_FILE": "/secret/sentinel.env"})
    assert "sentinel" not in str(error.value)


def test_cloud_runtime_without_file_does_not_read_dotenv():
    env = {"MCP_ENV": "production", "K_SERVICE": "unit-test"}
    assert load_environment(env) is None
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in env


def test_missing_explicit_file_is_sanitized():
    with pytest.raises(RuntimeConfigurationError) as error:
        load_environment({"MCP_ENV": "test", "MCP_ENV_FILE": "/sentinel/missing.env"})
    assert "sentinel" not in str(error.value)
