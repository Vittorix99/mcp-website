from pathlib import Path


def _load_functions_without_init():
    path = Path(__file__).resolve().parents[3] / "config" / "firebase_config.py"
    source = path.read_text(encoding="utf-8")
    source = source.split("if not firebase_admin._apps:", 1)[0]
    namespace = {
        "__file__": str(path),
        "json": __import__("json"),
        "os": __import__("os"),
        "firebase_admin": object(),
        "credentials": None,
        "firestore": object(),
        "storage": object(),
        "options": object(),
        "load_environment": lambda: None,
    }

    exec(compile(source, str(path), "exec"), namespace)

    class _Credentials:
        @staticmethod
        def Certificate(payload):
            return ("certificate", payload)

        @staticmethod
        def ApplicationDefault():
            return "application_default"

    namespace["credentials"] = _Credentials
    return namespace


def test_cloud_runtime_ignores_missing_local_google_application_credentials(monkeypatch):
    monkeypatch.setenv("K_SERVICE", "admin_rebuild_analytics")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "./missing_service_account.json")

    module = _load_functions_without_init()

    assert module["_load_credentials"]() == "application_default"
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in __import__("os").environ


def test_local_missing_google_application_credentials_error_is_sanitized(monkeypatch):
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "./missing_service_account.json")

    module = _load_functions_without_init()

    try:
        module["_load_credentials"]()
    except FileNotFoundError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")

    assert "missing_service_account.json" not in message
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in message
