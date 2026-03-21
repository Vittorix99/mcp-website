#!/usr/bin/env bash
set -euo pipefail

DEVELOPMENT=false
AUTH_EMULATOR=false
ENV_FILE=""
COMMON_ENV="mcp-website/.env"

usage() {
  cat <<'USAGE'
Usage: ./frontend-dev.sh [--development=true|false] [--auth-emulator=true|false]

--development=true   Sets NEXT_PUBLIC_ENV/NEXT_PUBLIC_PAYPAL_ENV to "development".
--development=false  Sets NEXT_PUBLIC_ENV/NEXT_PUBLIC_PAYPAL_ENV to "production" (default).
--auth-emulator=true  Sets NEXT_PUBLIC_AUTH_EMULATOR_HOST=127.0.0.1:9099.
--auth-emulator=false Clears NEXT_PUBLIC_AUTH_EMULATOR_HOST (default).
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --development=true) DEVELOPMENT=true ;;
    --development=false) DEVELOPMENT=false ;;
    --auth-emulator=true) AUTH_EMULATOR=true ;;
    --auth-emulator=false) AUTH_EMULATOR=false ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown arg: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

if [ "$DEVELOPMENT" = true ]; then
  ENV_FILE="mcp-website/.env.development"
else
  ENV_FILE="mcp-website/.env.production"
fi

set -a
# shellcheck disable=SC1090
if [ -f "$COMMON_ENV" ]; then
  . "$COMMON_ENV"
fi
if [ ! -f "$ENV_FILE" ]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi
. "$ENV_FILE"
set +a

if [ "$DEVELOPMENT" = true ]; then
  export NEXT_PUBLIC_ENV=development
  export NEXT_PUBLIC_PAYPAL_ENV=development
else
  export NEXT_PUBLIC_ENV=production
  export NEXT_PUBLIC_PAYPAL_ENV=production
fi

if [ "$AUTH_EMULATOR" = true ]; then
  export NEXT_PUBLIC_AUTH_EMULATOR_HOST=127.0.0.1:9099
else
  unset NEXT_PUBLIC_AUTH_EMULATOR_HOST
fi

export __NEXT_PROCESSED_ENV=true

cd mcp-website
npm run dev
