#!/usr/bin/env bash
set -euo pipefail

# Esempi comuni:
# - Build production usando i file/env locali gia presenti:
#   ./frontend-build.sh
#
# - Build production con Doppler come source of truth:
#   ./frontend-build.sh --doppler=true
#
# - Build production con progetto/config Doppler custom:
#   ./frontend-build.sh --doppler=true --doppler-project=mcp-frontend --doppler-config=prd_frontend

DOPPLER=false
DOPPLER_PROJECT="${DOPPLER_PROJECT:-mcp-frontend}"
DOPPLER_CONFIG="${DOPPLER_CONFIG:-prd_frontend}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'USAGE'
Usage: ./frontend-build.sh [--doppler=true|false] [--doppler-project=NAME] [--doppler-config=NAME]

--doppler=true          Runs the production build through Doppler.
--doppler-project=NAME  Doppler project. Default: mcp-frontend.
--doppler-config=NAME   Doppler config. Default: prd_frontend.
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --doppler=true) DOPPLER=true ;;
    --doppler=false) DOPPLER=false ;;
    --doppler-project=*) DOPPLER_PROJECT="${arg#*=}" ;;
    --doppler-config=*) DOPPLER_CONFIG="${arg#*=}" ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown arg: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

if [ "$DOPPLER" = true ] && [ "${MCP_USE_DOPPLER:-}" != "1" ]; then
  if ! command -v doppler >/dev/null 2>&1; then
    echo "Doppler CLI not found. Install/login Doppler or rerun with --doppler=false." >&2
    exit 1
  fi
  exec env MCP_USE_DOPPLER=1 doppler run --project "$DOPPLER_PROJECT" --config "$DOPPLER_CONFIG" -- "$SCRIPT_DIR/frontend-build.sh" "$@"
fi

export NEXT_PUBLIC_ENV=production
export NEXT_PUBLIC_PAYPAL_ENV=production
# Ensure auth emulator is disabled for production builds.
export NEXT_PUBLIC_AUTH_EMULATOR_HOST=

cd mcp-website
npm run build
