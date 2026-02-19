#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="test"   # test | prod
AUTH=false
USE_FIRESTORE_EMULATOR=false
USE_PUBSUB_EMULATOR=false
PUBSUB_FLAG_SET=false
EXPORT_DIR="./emulator-data"
PROJECT_ID=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'USAGE'
Usage: ./emulator.sh [--env=test|prod] [--firestore-emulator=true|false] [--auth=true|false]

Examples:
  ./emulator.sh
  ./emulator.sh --env=prod
  ./emulator.sh --env=test --firestore-emulator=true
  ./emulator.sh --env=test --auth=true --firestore-emulator=true

Notes:
- Default environment is test (loads .env.integration).
- When --env=prod, MCP_ENV=prod is exported (loads .env).
- Project ID is inferred from the Firebase service account JSON when available.
- Firestore emulator can only be enabled in test.
- When --auth=true, emulator data is exported on exit to ./emulator-data
  (and imported on start if present).
USAGE
}

get_project_id() {
  local sa_file="$1"
  if [ -f "$sa_file" ]; then
    python3 - <<PY
import json
with open("${sa_file}", "r", encoding="utf-8") as handle:
    data = json.load(handle)
print(data.get("project_id", ""))
PY
  fi
}

for arg in "$@"; do
  case "$arg" in
    --env=test) ENVIRONMENT="test" ;;
    --env=prod) ENVIRONMENT="prod" ;;
    --firestore-emulator=true) USE_FIRESTORE_EMULATOR=true ;;
    --firestore-emulator=false) USE_FIRESTORE_EMULATOR=false ;;
    --pubsub-emulator=true) USE_PUBSUB_EMULATOR=true; PUBSUB_FLAG_SET=true ;;
    --pubsub-emulator=false) USE_PUBSUB_EMULATOR=false; PUBSUB_FLAG_SET=true ;;
    --auth=true) AUTH=true ;;
    --auth=false) AUTH=false ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown arg: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

if [ "$ENVIRONMENT" = "prod" ]; then
  export MCP_ENV=prod
  PROJECT_ID="$(get_project_id "$SCRIPT_DIR/mcp-backend/functions/service_account.json")"
else
  export MCP_ENV=test
  PROJECT_ID="$(get_project_id "$SCRIPT_DIR/mcp-backend/functions/service_account_test.json")"
fi

if [ "$ENVIRONMENT" = "prod" ] && [ "$USE_FIRESTORE_EMULATOR" = true ]; then
  echo "Firestore emulator can only be enabled in test." >&2
  exit 1
fi

if [ "$USE_FIRESTORE_EMULATOR" = true ] && [ "$PUBSUB_FLAG_SET" = false ]; then
  USE_PUBSUB_EMULATOR=true
fi

IMPORT_FLAG=""
EXPORT_FLAG=""
if [ "$AUTH" = true ]; then
  mkdir -p "$EXPORT_DIR"
  if [ -n "$(ls -A "$EXPORT_DIR" 2>/dev/null)" ]; then
    IMPORT_FLAG="--import=$EXPORT_DIR"
  fi
  EXPORT_FLAG="--export-on-exit=$EXPORT_DIR"
fi

ONLY_SERVICES="functions"
if [ "$AUTH" = true ]; then
  export FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099
  ONLY_SERVICES="$ONLY_SERVICES,auth"
else
  unset FIREBASE_AUTH_EMULATOR_HOST
fi

if [ "$USE_FIRESTORE_EMULATOR" = true ]; then
  export FIRESTORE_EMULATOR_HOST=127.0.0.1:8080
  ONLY_SERVICES="$ONLY_SERVICES,firestore"
else
  unset FIRESTORE_EMULATOR_HOST
fi

if [ "$USE_PUBSUB_EMULATOR" = true ]; then
  export PUBSUB_EMULATOR_HOST=127.0.0.1:8085
  ONLY_SERVICES="$ONLY_SERVICES,pubsub"
else
  unset PUBSUB_EMULATOR_HOST
fi

if [ -n "$PROJECT_ID" ]; then
  firebase emulators:start --only "$ONLY_SERVICES" --project "$PROJECT_ID" $IMPORT_FLAG $EXPORT_FLAG
else
  firebase emulators:start --only "$ONLY_SERVICES" $IMPORT_FLAG $EXPORT_FLAG
fi
