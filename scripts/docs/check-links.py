#!/usr/bin/env python3
"""Check local Markdown links without making network requests."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


REPO_ROOT = Path(__file__).resolve().parents[2]
LINK_RE = re.compile(
    r"!?\[[^\]]*\]\(\s*(<[^>]*>|(?:\\.|[^\s)])+)(?:\s+[^)]*)?\s*\)"
)
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


def markdown_files(paths: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            files.update(item for item in path.rglob("*") if item.is_file() and item.suffix.lower() == ".md")
        elif path.is_file() and path.suffix.lower() == ".md":
            files.add(path)
    return sorted(files)


def link_targets(markdown: str):
    fence_char = None
    fence_size = 0
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        fence = FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            if fence_char is None:
                fence_char, fence_size = marker[0], len(marker)
                continue
            if marker[0] == fence_char and len(marker) >= fence_size:
                fence_char = None
                fence_size = 0
                continue
        if fence_char is not None:
            continue
        for match in LINK_RE.finditer(line):
            target = match.group(1)
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            target = target.replace(r"\ ", " ").replace(r"\(", "(").replace(r"\)", ")")
            yield line_number, target


def resolve_target(source: Path, target: str) -> Path | None:
    decoded = unquote(target)
    parts = urlsplit(decoded)
    scheme = parts.scheme.lower()
    if not parts.path or scheme in {"http", "https", "mailto", "plugin", "app"}:
        return None
    if scheme:
        return None
    path = Path(parts.path)
    if path.is_absolute():
        return (REPO_ROOT / str(path).lstrip("/")).resolve()
    return (source.parent / path).resolve()


def check(paths: list[Path]) -> list[str]:
    errors = []
    for source in markdown_files(paths):
        try:
            content = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"{source}: cannot read Markdown: {error}")
            continue
        for line_number, target in link_targets(content):
            resolved = resolve_target(source, target)
            if resolved is not None and not resolved.exists():
                errors.append(f"{source}:{line_number}: missing local target {unquote(target)!r}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Markdown files or directories to scan")
    args = parser.parse_args(argv)
    missing_inputs = [path for path in args.paths if not path.exists()]
    if missing_inputs:
        for path in missing_inputs:
            print(f"{path}: input path does not exist", file=sys.stderr)
        return 1
    errors = check(args.paths)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
