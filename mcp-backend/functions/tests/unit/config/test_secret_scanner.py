"""CLI behavior tests for the repository's stdlib secret scanner."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[5]
SCANNER = PROJECT_ROOT / "scripts" / "security" / "scan_secrets.py"


def synthetic_token() -> str:
    """Build a scanner fixture without embedding a credential-shaped literal."""
    return "gh" + "p_" + "A" * 36


def run_scanner(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCANNER), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def init_repo(path: Path) -> Path:
    path.mkdir()
    git(path, "init", "-q")
    git(path, "config", "user.name", "Secret Scanner Tests")
    git(path, "config", "user.email", "scanner-tests@example.invalid")
    return path


def assert_redacted_json(result: subprocess.CompletedProcess[str], token: str) -> list[dict]:
    assert result.returncode == 1
    assert token not in result.stdout
    assert token not in result.stderr
    findings = json.loads(result.stdout)
    assert findings
    assert all(set(finding) == {"path", "line", "pattern"} for finding in findings)
    return findings


def test_path_mode_reports_secret_and_clean_file_as_redacted_json(tmp_path: Path) -> None:
    secret = synthetic_token()
    flagged = tmp_path / "config.txt"
    clean = tmp_path / "notes.txt"
    flagged.write_text(f"API token: {secret}\n", encoding="utf-8")
    clean.write_text("ordinary configuration\n", encoding="utf-8")

    result = run_scanner("--path", str(flagged), "--path", str(clean), "--json", cwd=tmp_path)

    findings = assert_redacted_json(result, secret)
    assert findings == [{"path": str(flagged), "line": 1, "pattern": "github-token"}]


def test_staged_mode_reports_only_added_secret_and_redacts_json(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    secret = synthetic_token()
    (repo / "clean.txt").write_text("committed clean baseline\n", encoding="utf-8")
    git(repo, "add", "clean.txt")
    git(repo, "commit", "-qm", "clean baseline")

    (repo / "added.txt").write_text(f"new value: {secret}\n", encoding="utf-8")
    (repo / "clean.txt").write_text("still ordinary\n", encoding="utf-8")
    git(repo, "add", "added.txt", "clean.txt")

    result = run_scanner("--staged", "--repo", str(repo), "--json", cwd=repo)

    findings = assert_redacted_json(result, secret)
    assert findings == [{"path": "added.txt", "line": 1, "pattern": "github-token"}]


def test_base_head_mode_scans_committed_secret_against_clean_ancestor(tmp_path: Path) -> None:
    repo = init_repo(tmp_path / "repo")
    (repo / "clean.txt").write_text("ordinary baseline\n", encoding="utf-8")
    git(repo, "add", "clean.txt")
    git(repo, "commit", "-qm", "clean baseline")
    base = git(repo, "rev-parse", "HEAD")

    secret = synthetic_token()
    (repo / "committed.txt").write_text(f"key = {secret}\n", encoding="utf-8")
    git(repo, "add", "committed.txt")
    git(repo, "commit", "-qm", "add synthetic scanner fixture")
    head = git(repo, "rev-parse", "HEAD")

    result = run_scanner("--base", base, "--head", head, "--repo", str(repo), "--json", cwd=repo)

    findings = assert_redacted_json(result, secret)
    assert findings == [{"path": "committed.txt", "line": 1, "pattern": "github-token"}]


@pytest.mark.parametrize(
    "line",
    [
        'api_key = "placeholder-value-for-docs"',
        f"example token: {synthetic_token()}  # gitleaks:allow",
    ],
)
def test_path_mode_ignores_placeholder_and_inline_suppression(tmp_path: Path, line: str) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text(line + "\n", encoding="utf-8")

    result = run_scanner("--path", str(sample), "--json", cwd=tmp_path)

    assert result.returncode == 0
    assert json.loads(result.stdout) == []
    assert result.stderr == ""
