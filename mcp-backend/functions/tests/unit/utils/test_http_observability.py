import importlib
import json
from uuid import UUID

from flask import Flask, Response, abort, jsonify, request
import pytest


FIELDS = {"event", "severity", "environment", "function", "request_id", "method", "status_code", "duration_ms"}


def _module():
    try:
        return importlib.import_module("utils.http_observability")
    except ModuleNotFoundError as error:
        if error.name != "utils.http_observability":
            raise
        pytest.fail("HTTP observation wrapper not implemented")


def _app(handler, decorator=None):
    app = Flask("http-observation")
    observed = (decorator or _module().observe_http_request)(handler)
    app.add_url_rule("/events", view_func=lambda: observed(request), methods=["GET", "POST", "SECRET_METHOD"])
    return app


def _record(capfd, response=None):
    lines = capfd.readouterr().out.splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert set(record) == FIELDS
    assert record["event"] == "http_request_completed"
    assert record["environment"] == "test"
    assert record["duration_ms"] >= 0
    assert UUID(record["request_id"]).version == 4
    if response is not None:
        assert response.headers["X-Request-ID"] == record["request_id"]
        assert response.status_code == record["status_code"]
    return record


@pytest.mark.parametrize("status", [200, 201, 400, 401, 404, 405, 500])
def test_response_and_tuple_contracts_are_preserved_and_logged_once(capfd, status):
    def event_list(_req):
        return jsonify({"result": "unchanged"}), status, {"Cache-Control": "no-store"}

    response = _app(event_list).test_client().get("/events")
    assert response.json == {"result": "unchanged"}
    assert response.content_type == "application/json"
    assert response.headers["Cache-Control"] == "no-store"
    record = _record(capfd, response)
    assert record["function"] == "event_list"
    assert record["method"] == "GET"
    assert record["severity"] == ("ERROR" if status >= 500 else "WARNING" if status >= 400 else "INFO")


def test_response_objects_keep_body_status_and_headers_with_distinct_request_ids(capfd):
    def event_list(_req):
        return Response("unchanged", status=202, headers={"ETag": '"original"'}, mimetype="text/plain")

    client = _app(event_list).test_client()
    identifiers = []
    for _ in range(2):
        response = client.get("/events")
        assert response.data == b"unchanged"
        assert response.status_code == 202
        assert response.headers["ETag"] == '"original"'
        identifiers.append(_record(capfd, response)["request_id"])
    assert identifiers[0] != identifiers[1]


def test_unhandled_exception_is_unchanged_and_logged_once_without_sensitive_values(capfd):
    failure = RuntimeError("private-email@example.test Bearer sensitive-value")

    def event_list(_req):
        raise failure

    app = _app(event_list)
    app.testing = True
    with pytest.raises(RuntimeError) as raised:
        app.test_client().get("/events?email=private-email@example.test", headers={"Authorization": "Bearer sensitive-value"})
    assert raised.value is failure
    record = _record(capfd)
    assert record["status_code"] == 500
    assert record["severity"] == "ERROR"
    assert "private-email" not in json.dumps(record)
    assert "sensitive-value" not in json.dumps(record)


def test_http_exception_uses_its_actual_status(capfd):
    def event_list(_req):
        abort(404)

    response = _app(event_list).test_client().get("/events")
    assert _record(capfd, response)["status_code"] == 404


def test_unhandled_error_finalization_does_not_duplicate_logs(capfd):
    def event_list(_req):
        raise RuntimeError("synthetic failure")

    response = _app(event_list).test_client().get("/events")
    assert response.status_code == 500
    assert _record(capfd)["status_code"] == 500


def test_request_values_and_custom_method_do_not_enter_the_log(capfd):
    def event_list(_req):
        return "ok"

    response = _app(event_list).test_client().open(
        "/events?private=sentinel-query", method="SECRET_METHOD", data="sentinel-body",
        headers={"Authorization": "Bearer sentinel-token", "X-Request-ID": "sentinel-id", "Cookie": "private=sentinel-cookie"},
    )
    record = _record(capfd, response)
    assert record["method"] == "OTHER"
    assert "sentinel" not in json.dumps(record)


@pytest.mark.parametrize("raises", [False, True])
def test_stdout_failure_preserves_original_result_or_exception(monkeypatch, raises):
    module = _module()
    failure = RuntimeError("original failure")

    def fail_output(*_args, **_kwargs):
        raise OSError("stdout unavailable")

    monkeypatch.setattr(module, "print", fail_output, raising=False)

    def event_list(_req):
        if raises:
            raise failure
        return "unchanged", 202

    app = _app(event_list)
    app.testing = True
    if raises:
        with pytest.raises(RuntimeError) as raised:
            app.test_client().get("/events")
        assert raised.value is failure
    else:
        response = app.test_client().get("/events")
        assert response.status_code == 202
        assert response.data == b"unchanged"


@pytest.mark.parametrize("kind,method,auth,status", [
    ("public", "GET", None, 200), ("public", "POST", None, 405),
    ("admin", "GET", None, 401), ("admin", "GET", "member", 401),
    ("admin", "GET", "admin", 200), ("admin", "POST", "admin", 405),
    ("member", "GET", None, 401), ("member", "GET", "invalid", 401),
    ("member", "GET", "member", 200),
])
def test_common_wrappers_log_successes_and_denials_without_changing_permissions(capfd, monkeypatch, kind, method, auth, status):
    _module()
    from api import decorators
    import firebase_admin.auth as firebase_auth

    def verify(token):
        if token == "invalid":
            raise ValueError("invalid token")
        return {"uid": "sensitive-user", "admin": token == "admin"}

    monkeypatch.setattr(firebase_auth, "verify_id_token", verify)
    calls = []

    def event_list(_req):
        calls.append(True)
        return jsonify({"result": "unchanged"})

    decorator = getattr(decorators, f"{kind}_endpoint")(methods=("GET",))
    response = _app(event_list, decorator).test_client().open(
        "/events", method=method, headers={"Authorization": f"Bearer {auth}"} if auth else {},
    )
    assert response.status_code == status
    assert bool(calls) == (status == 200)
    record = _record(capfd, response)
    assert record["function"] == "event_list"
    assert "sensitive-user" not in json.dumps(record)
