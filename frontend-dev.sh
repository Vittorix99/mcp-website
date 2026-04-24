#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVELOPMENT=false
AUTH_EMULATOR=false
PROD_EMULATOR=false
ENV_FILE=""
COMMON_ENV="$SCRIPT_DIR/mcp-website/.env"

usage() {
  cat <<'USAGE'
Usage: ./frontend-dev.sh [--development=true|false] [--auth-emulator=true|false] [--prod-emulator=true|false]

--development=true     Sets NEXT_PUBLIC_ENV/NEXT_PUBLIC_PAYPAL_ENV to "development".
--development=false    Sets NEXT_PUBLIC_ENV/NEXT_PUBLIC_PAYPAL_ENV to "production" (default).
--auth-emulator=true   Sets NEXT_PUBLIC_AUTH_EMULATOR_HOST=127.0.0.1:9099.
--auth-emulator=false  Clears NEXT_PUBLIC_AUTH_EMULATOR_HOST (default).
--prod-emulator=true   Dev frontend + emulator running with --env=prod (project mcp-website-2a1ad on port 5002).
--prod-emulator=false  Use project ID from the loaded env file (default).
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --development=true) DEVELOPMENT=true ;;
    --development=false) DEVELOPMENT=false ;;
    --auth-emulator=true) AUTH_EMULATOR=true ;;
    --auth-emulator=false) AUTH_EMULATOR=false ;;
    --prod-emulator=true) PROD_EMULATOR=true ;;
    --prod-emulator=false) PROD_EMULATOR=false ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown arg: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

if [ "$DEVELOPMENT" = true ]; then
  ENV_FILE="$SCRIPT_DIR/mcp-website/.env.development"
else
  ENV_FILE="$SCRIPT_DIR/mcp-website/.env.production"
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

# Scrive .env.local con gli override — Next.js lo legge con priorità massima
# senza interferenze da process.env. Viene pulito all'uscita.
ENV_LOCAL="$SCRIPT_DIR/mcp-website/.env.local"
cleanup() { rm -f "$ENV_LOCAL"; }
trap cleanup EXIT

{
  if [ "$DEVELOPMENT" = true ]; then
    echo "NEXT_PUBLIC_ENV=development"
    echo "NEXT_PUBLIC_PAYPAL_ENV=development"
  else
    echo "NEXT_PUBLIC_ENV=production"
    echo "NEXT_PUBLIC_PAYPAL_ENV=production"
  fi

  if [ "$AUTH_EMULATOR" = true ]; then
    echo "NEXT_PUBLIC_AUTH_EMULATOR_HOST=127.0.0.1:9099"
  fi

  if [ "$PROD_EMULATOR" = true ]; then
    echo "NEXT_PUBLIC_BASE_URL=http://127.0.0.1:5002/mcp-website-2a1ad/us-central1"
    # Firebase config del progetto prod — necessario per autenticarsi col backend prod
    grep "^NEXT_PUBLIC_FIREBASE_" "$SCRIPT_DIR/mcp-website/.env.production" || true
    echo "[frontend-dev] prod-emulator: mcp-website-2a1ad:5002" >&2
  fi
} > "$ENV_LOCAL"

cd mcp-website
npm run dev
