import os

from config.environment import load_environment


def test_load_environment_skips_dotenv_in_cloud_runtime(monkeypatch):
    monkeypatch.setenv("K_SERVICE", "admin_rebuild_analytics")
    monkeypatch.delenv("STORAGE_BUCKET", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

    load_environment()

    assert "STORAGE_BUCKET" not in os.environ
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ
