#!/usr/bin/env bash
set -euo pipefail

# Sincronizza docs/ nella GitHub Wiki.
#
# Casistiche comuni:
# - Preparare/aggiornare la wiki locale senza push:
#   scripts/wiki/sync_docs_to_wiki.sh
#
# - Pubblicare davvero su GitHub Wiki:
#   scripts/wiki/sync_docs_to_wiki.sh --push=true
#
# - Usare un repository wiki custom:
#   scripts/wiki/sync_docs_to_wiki.sh --wiki-repo=https://github.com/OWNER/REPO.wiki.git
#
# Note:
# - GitHub Wiki e un repository Git separato: <repo>.wiki.git.
# - docs/ resta la fonte di verita nel codice.
# - Lo script aggiorna solo pagine generate con marker AUTO-GENERATED-FROM-DOCS.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCS_DIR="$REPO_ROOT/docs"
WORKTREE="$REPO_ROOT/runtime-data/github-wiki"
PUSH=false
WIKI_REPO=""

usage() {
  cat <<'USAGE'
Usage: scripts/wiki/sync_docs_to_wiki.sh [--wiki-repo=URL] [--worktree=PATH] [--push=true|false]

Options:
  --wiki-repo=URL   GitHub Wiki repo. Default: derived from origin remote.
  --worktree=PATH   Local wiki clone. Default: runtime-data/github-wiki.
  --push=true       Commit and push generated wiki pages.
  --push=false      Generate locally only. Default.

Examples:
  scripts/wiki/sync_docs_to_wiki.sh
  scripts/wiki/sync_docs_to_wiki.sh --push=true
  scripts/wiki/sync_docs_to_wiki.sh --wiki-repo=https://github.com/Vittorix99/mcp-website.wiki.git --push=true
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --wiki-repo=*) WIKI_REPO="${arg#*=}" ;;
    --worktree=*) WORKTREE="${arg#*=}" ;;
    --push=true) PUSH=true ;;
    --push=false) PUSH=false ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown arg: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

if [ ! -d "$DOCS_DIR" ]; then
  echo "Docs directory not found: $DOCS_DIR" >&2
  exit 1
fi

if [ -z "$WIKI_REPO" ]; then
  ORIGIN_URL="$(git -C "$REPO_ROOT" remote get-url origin)"
  case "$ORIGIN_URL" in
    *.git) WIKI_REPO="${ORIGIN_URL%.git}.wiki.git" ;;
    *) WIKI_REPO="${ORIGIN_URL}.wiki.git" ;;
  esac
fi

if [ ! -d "$WORKTREE/.git" ]; then
  mkdir -p "$(dirname "$WORKTREE")"
  git clone "$WIKI_REPO" "$WORKTREE"
else
  git -C "$WORKTREE" pull --ff-only
fi

DOCS_DIR="$DOCS_DIR" WIKI_DIR="$WORKTREE" python3 - <<'PY'
from __future__ import annotations

import re
from pathlib import Path

docs_dir = Path(__import__("os").environ["DOCS_DIR"]).resolve()
wiki_dir = Path(__import__("os").environ["WIKI_DIR"]).resolve()
marker_prefix = "<!-- AUTO-GENERATED-FROM-DOCS:"


def title_from_markdown(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("_", " ").replace("-", " ").title()


def page_name_for(path: Path) -> str:
    rel = path.relative_to(docs_dir)
    if rel.as_posix() == "README.md":
        return "Home"
    parts = list(rel.with_suffix("").parts)
    if parts[-1].lower() == "readme":
        parts = parts[:-1]
    readable = []
    for part in parts:
        cleaned = re.sub(r"[^A-Za-z0-9]+", " ", part).strip()
        readable.append("-".join(word.capitalize() for word in cleaned.split()))
    return "-".join(readable)


source_files = sorted(docs_dir.rglob("*.md"))
page_map = {path.relative_to(docs_dir).as_posix(): page_name_for(path) for path in source_files}


def rewrite_links(source: Path, content: str) -> str:
    def replace(match: re.Match[str]) -> str:
        label = match.group("label")
        target = match.group("target")
        if "://" in target or target.startswith("#"):
            return match.group(0)
        path_part, _, anchor = target.partition("#")
        if not path_part.endswith(".md"):
            return match.group(0)
        normalized = (source.parent / path_part).resolve()
        try:
            rel = normalized.relative_to(docs_dir).as_posix()
        except ValueError:
            return match.group(0)
        page = page_map.get(rel)
        if not page:
            return match.group(0)
        suffix = f"#{anchor}" if anchor else ""
        return f"[{label}]({page}{suffix})"

    return re.sub(r"\[(?P<label>[^\]]+)\]\((?P<target>[^)]+)\)", replace, content)


# Puliamo solo file gia generati in precedenza, preservando pagine manuali della wiki.
for existing in wiki_dir.glob("*.md"):
    try:
        first_line = existing.read_text(encoding="utf-8").splitlines()[0]
    except IndexError:
        continue
    if first_line.startswith(marker_prefix):
        existing.unlink()

sidebar_lines = [f"{marker_prefix} _Sidebar.md -->", "", "# Docs", ""]

for source in source_files:
    rel = source.relative_to(docs_dir).as_posix()
    page_name = page_map[rel]
    title = title_from_markdown(source)
    raw = source.read_text(encoding="utf-8")
    body = rewrite_links(source, raw)
    target = wiki_dir / f"{page_name}.md"
    target.write_text(f"{marker_prefix} {rel} -->\n\n{body.rstrip()}\n", encoding="utf-8")
    sidebar_lines.append(f"- [{title}]({page_name})")
    print(f"synced {rel} -> {target.name}")

(wiki_dir / "_Sidebar.md").write_text("\n".join(sidebar_lines) + "\n", encoding="utf-8")
PY

git -C "$WORKTREE" status --short

if [ "$PUSH" = true ]; then
  if git -C "$WORKTREE" diff --quiet && git -C "$WORKTREE" diff --cached --quiet; then
    echo "Wiki already up to date."
    exit 0
  fi
  git -C "$WORKTREE" add .
  git -C "$WORKTREE" commit -m "Sync project docs"
  git -C "$WORKTREE" push
else
  echo "Generated wiki pages locally in: $WORKTREE"
  echo "Review, then publish with: scripts/wiki/sync_docs_to_wiki.sh --push=true"
fi
