#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
case "${1:-}" in
  ""|--env=local) if [ "$#" -gt 0 ]; then shift; fi; exec "$PROJECT_DIR/scripts/dev-local.sh" "$@" ;;
  --env=test) shift; exec "$PROJECT_DIR/scripts/test-emulators.sh" "$@" ;;
  *) echo "Use emulator.sh [--env=local|--env=test]. Production emulator modes are disabled." >&2; exit 2 ;;
esac
