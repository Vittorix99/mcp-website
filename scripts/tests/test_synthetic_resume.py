import importlib.util
import json
import os
from datetime import date
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = ROOT


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/staging/{name}.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


generator = module("generate")
loader = module("load_emulator")


def dataset(seed=42):
    return generator.generate(
        seed=seed,
        as_of=date(2026, 11, 12),
        email_base="owner@example.com",
        member_count=30,
        event_count=12,
    )


def private_output(tmp_path, monkeypatch):
    plan = PROJECT_ROOT / "docs/superpowers/plans/2026-11-04-staging-synthetic-data.md"
    staged_plan = tmp_path / "docs/superpowers/plans/2026-11-04-staging-synthetic-data.md"
    staged_plan.parent.mkdir(parents=True, exist_ok=True)
    staged_plan.write_bytes(plan.read_bytes())
    monkeypatch.setattr(generator, "ROOT", tmp_path)
    return tmp_path / ".local/staging/output"


def artifact_bytes(output):
    return {
        name: (output / name).read_bytes()
        for name in ("records.jsonl", "isolated-cases.json", "manifest.json")
    }


def test_repeated_export_is_byte_deterministic_and_readable(tmp_path, monkeypatch):
    output = private_output(tmp_path, monkeypatch)
    data = dataset()

    generator.write_export(data, output)
    first = artifact_bytes(output)
    rows, manifest = loader.read_export(output)
    assert len(rows) == manifest["document_count"]

    generator.write_export(data, output)
    assert artifact_bytes(output) == first
    rows, manifest = loader.read_export(output)
    assert len(rows) == manifest["document_count"]


def test_partial_mixed_export_is_rejected_and_valid_rerun_recovers(tmp_path, monkeypatch):
    output = private_output(tmp_path, monkeypatch)
    original = dataset(seed=42)
    replacement = dataset(seed=43)
    generator.write_export(original, output)

    (output / "records.jsonl").write_text(
        "".join(generator.encode(row) + "\n" for row in replacement["records"])
    )
    with pytest.raises(ValueError):
        loader.read_export(output)

    generator.write_export(original, output)
    rows, manifest = loader.read_export(output)
    assert len(rows) == manifest["document_count"]


@pytest.mark.parametrize("stale_name", ["records.jsonl.tmp", "manifest.json.tmp"])
def test_stale_temporary_file_does_not_block_safe_export_and_is_preserved(
    tmp_path, monkeypatch, stale_name
):
    output = private_output(tmp_path, monkeypatch)
    output.mkdir(parents=True)
    stale = output / stale_name
    stale.write_text("left by interrupted producer\n")
    before = stale.read_bytes()

    generator.write_export(dataset(), output)

    assert stale.read_bytes() == before
    rows, manifest = loader.read_export(output)
    assert len(rows) == manifest["document_count"]
    assert os.stat(output).st_mode & 0o777 == 0o700
    for name in ("records.jsonl", "isolated-cases.json", "manifest.json"):
        assert os.stat(output / name).st_mode & 0o777 == 0o600


def test_apply_failure_redacts_exception_and_warns_writes_may_be_partial(
    tmp_path, monkeypatch, capsys
):
    output = private_output(tmp_path, monkeypatch)
    generator.write_export(dataset(), output)
    monkeypatch.setattr(
        loader,
        "load",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            ValueError("owner@example.com syn-member-00001")
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["load_emulator.py", "--directory", str(output), "--apply"],
    )

    with pytest.raises(SystemExit) as error:
        loader.main()

    captured = capsys.readouterr()
    assert error.value.code == 2
    assert captured.out == ""
    assert "owner@example.com" not in captured.err
    assert "syn-member-00001" not in captured.err
    assert "ValueError" in captured.err
    assert "partial" in captured.err.lower()


def test_default_loader_mode_is_offline_and_never_calls_load(
    tmp_path, monkeypatch, capsys
):
    output = private_output(tmp_path, monkeypatch)
    generator.write_export(dataset(), output)

    def unexpected_load(*args, **kwargs):
        pytest.fail("offline validation must not invoke emulator loading")

    monkeypatch.setattr(loader, "load", unexpected_load)
    monkeypatch.setattr("sys.argv", ["load_emulator.py", "--directory", str(output)])

    loader.main()

    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "offline-check"
    assert result["verified_documents"] == 0
