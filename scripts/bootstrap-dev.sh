#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_PYTHON="$(tr -d '[:space:]' < "$ROOT_DIR/.python-version")"
EXPECTED_NODE="$(tr -d '[:space:]' < "$ROOT_DIR/.nvmrc")"
PYTHON_BIN="${PYTHON_BIN:-python${EXPECTED_PYTHON}}"

fail() {
  printf 'bootstrap-dev: %s\n' "$1" >&2
  exit 1
}

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  fail "Python $EXPECTED_PYTHON is required; install it or set PYTHON_BIN to its executable."
fi
python_version="$("$PYTHON_BIN" --version 2>&1)"
if [[ ! "$python_version" =~ ^Python\ ${EXPECTED_PYTHON//./\.}([.]|$) ]]; then
  fail "Python $EXPECTED_PYTHON is required (found: $python_version). Install Python $EXPECTED_PYTHON or set PYTHON_BIN."
fi

if ! command -v node >/dev/null 2>&1; then
  fail "Node.js $EXPECTED_NODE is required; install Node.js $EXPECTED_NODE and ensure node is on PATH."
fi
node_version="$(node --version 2>&1)"
if [[ ! "$node_version" =~ ^v?${EXPECTED_NODE}([.]|$) ]]; then
  fail "Node.js $EXPECTED_NODE is required (found: $node_version). Install Node.js $EXPECTED_NODE and ensure node is on PATH."
fi
if ! command -v npm >/dev/null 2>&1; then
  fail "npm is required to install website dependencies; install npm and ensure it is on PATH."
fi

venv="$ROOT_DIR/.venv"
venv_python="$venv/bin/python"
if [[ -e "$venv_python" ]]; then
  venv_version="$("$venv_python" --version 2>&1)"
  if [[ ! "$venv_version" =~ ^Python\ ${EXPECTED_PYTHON//./\.}([.]|$) ]]; then
    fail "Existing .venv uses the wrong Python version (found: $venv_version; expected $EXPECTED_PYTHON). Remove .venv and rerun."
  fi
else
  "$PYTHON_BIN" -m venv "$venv"
fi

"$venv_python" -m pip install --require-hashes -r "$ROOT_DIR/mcp-backend/functions/requirements-dev.txt"
(cd -- "$ROOT_DIR/mcp-website" && npm ci)
