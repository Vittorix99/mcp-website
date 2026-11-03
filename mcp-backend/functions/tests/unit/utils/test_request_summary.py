import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import pytest


SCRIPT = Path(__file__).resolve().parents[5] / "scripts/observability/summarize_requests.py"


def _summary(lines):
    assert SCRIPT.exists(), "Request log summary not implemented"
    spec = importlib.util.spec_from_file_location("request_summary", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.summarize_requests(lines)


def _row(duration, status=200, environment="test", function="get_all_events"):
    return {"event": "http_request_completed", "environment": environment,
            "function": function, "request_id": str(uuid4()), "method": "GET",
            "status_code": status, "duration_ms": duration, "severity": "INFO"}


def test_groups_request_times_and_separates_client_and_server_errors():
    rows = [_row(10), _row(20, 404), _row(30, 500), _row(40, 503)]
    lines = ["Starting emulator", '{"event":"unrelated"}', json.dumps(rows[0])]
    lines += ["> " + json.dumps(row) for row in rows[1:]]
    assert _summary(lines) == [{"environment": "test", "function": "get_all_events",
        "requests": 4, "client_errors": 1, "server_errors": 2,
        "p50_ms": 20, "p95_ms": 40, "p99_ms": 40, "max_ms": 40}]


def test_environments_and_functions_are_never_combined():
    rows = [_row(900, environment="local"), _row(10), _row(20, function="get_event_by_id")]
    result = _summary(map(json.dumps, rows))
    assert [(r["environment"], r["function"], r["requests"], r["p95_ms"]) for r in result] == [
        ("local", "get_all_events", 1, 900), ("test", "get_all_events", 1, 10),
        ("test", "get_event_by_id", 1, 20),
    ]


def test_duplicate_exports_do_not_inflate_request_counts():
    row = _row(10)
    assert _summary([json.dumps(row), json.dumps(row)])[0]["requests"] == 1
    changed = {**row, "duration_ms": 100}
    with pytest.raises(ValueError, match="line 2"):
        _summary([json.dumps(row), json.dumps(changed)])


@pytest.mark.parametrize("patch", [
    {"duration_ms": -1}, {"duration_ms": float("nan")}, {"duration_ms": float("inf")},
    {"duration_ms": True}, {"duration_ms": "10"}, {"status_code": True},
    {"status_code": 99}, {"status_code": 600}, {"environment": "unknown"},
    {"function": "private-email@example.test"}, {"request_id": "not-a-uuid"},
])
def test_invalid_records_fail_without_echoing_the_input(patch):
    with pytest.raises(ValueError, match="line 1") as error:
        _summary([json.dumps({**_row(10), **patch})])
    assert "private-email" not in str(error.value)


def test_malformed_target_records_fail_while_unrelated_log_noise_is_ignored():
    assert _summary(["unrelated malformed output"]) == []
    with pytest.raises(ValueError, match="line 1"):
        _summary(['> {"event":"http_request_completed",'])


def test_cli_reads_stdin_and_excludes_private_fields():
    row = {**_row(12), "email": "private-email@example.test", "body": "private-body"}
    result = subprocess.run([sys.executable, str(SCRIPT), "-"],
                            input=json.dumps(row), text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["p50_ms"] == 12
    assert "private-email" not in result.stdout
    assert "private-body" not in result.stdout


def test_cli_does_not_present_an_empty_log_as_success():
    result = subprocess.run([sys.executable, str(SCRIPT), "-"], input="No request records",
                            text=True, capture_output=True)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "No request records" in result.stderr
