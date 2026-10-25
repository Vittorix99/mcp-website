#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR/mcp-website"
case "${1:-}" in
  "") exec npm run build ;;
  --release) exec npm run build:release ;;
  *) echo "Use frontend-build.sh [--release]; release requires explicit validated environment." >&2; exit 2 ;;
esac
