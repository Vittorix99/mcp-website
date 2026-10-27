import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
CHECKER = ROOT / "scripts/docs/check-links.py"


def _run(paths):
    return subprocess.run(
        [sys.executable, str(CHECKER), *(str(path) for path in paths)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_checker_accepts_resolved_local_and_external_links(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide with space.md").write_text("# Guide\n")
    (docs / "index.md").write_text(
        "[relative](guide%20with%20space.md#guide) "
        "[web](https://example.test/a) [email](mailto:a@example.test) "
        "[anchor](#here) [plugin](plugin://tool/id) [app](app://tool/id)\n"
        "```md\n[example](does-not-exist.md)\n```\n"
    )

    result = _run([docs])

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""


def test_checker_recurses_and_reports_missing_target_with_source(tmp_path):
    docs = tmp_path / "docs"
    nested = docs / "nested"
    nested.mkdir(parents=True)
    source = nested / "page.md"
    source.write_text("[missing](../missing%20page.md)\n")

    result = _run([docs])

    assert result.returncode == 1
    assert "page.md" in result.stdout
    assert "missing page.md" in result.stdout


def test_checker_supports_angle_bracket_space_paths(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "file name.md").write_text("# Target\n")
    (docs / "index.md").write_text("[target](<file name.md>)\n")

    result = _run([docs])

    assert result.returncode == 0, result.stdout + result.stderr
