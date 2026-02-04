#!/usr/bin/env bash
set -euo pipefail

MODE="local"        # local | test | prod
AUTH=false
PROJECT_ID=""
CREDS=""
EXPORT_DIR="./emulator-data"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'USAGE'
Usage: ./emulator.sh --db=local|test|prod [--auth=true|false] [--project=ID] [--creds=/path/service_account.json]

Examples:
  ./emulator.sh --db=local
  ./emulator.sh --db=test --project=PROJECT_ID_TEST --creds=/path/service_account_test.json
  ./emulator.sh --db=prod --project=PROJECT_ID_PROD --creds=/path/service_account.json
  ./emulator.sh --db=test --auth=true --project=PROJECT_ID_TEST --creds=/path/service_account_test.json

Notes:
- For test/prod, you can also set env vars PROJECT_ID_TEST/PROJECT_ID_PROD and GOOGLE_APPLICATION_CREDENTIALS.
- For local, Firestore emulator runs at 127.0.0.1:8080.
- When --auth=true, emulator data is exported on exit to ./emulator-data (and imported on start if present).
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --db=local) MODE="local" ;;
    --db=test) MODE="test" ;;
    --db=prod|--db=production) MODE="prod" ;;
    --auth=true) AUTH=true ;;
    --auth=false) AUTH=false ;;
    --project=*) PROJECT_ID="${arg#*=}" ;;
    --creds=*) CREDS="${arg#*=}" ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown arg: $arg" >&2
      usage
      exit 1
      ;;
  esac
done

IMPORT_FLAG=""
EXPORT_FLAG=""
if [ "$AUTH" = true ]; then
  mkdir -p "$EXPORT_DIR"
  if [ -n "$(ls -A "$EXPORT_DIR" 2>/dev/null)" ]; then
    IMPORT_FLAG="--import=$EXPORT_DIR"
  fi
  EXPORT_FLAG="--export-on-exit=$EXPORT_DIR"
fi

if [ "$MODE" = "prod" ] || [ "$MODE" = "test" ]; then
  unset FIRESTORE_EMULATOR_HOST

  if [ -n "$CREDS" ]; then
    if [[ "$CREDS" != /* ]]; then
      CREDS="$SCRIPT_DIR/$CREDS"
    fi
    export GOOGLE_APPLICATION_CREDENTIALS="$CREDS"
  fi

  if [ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]; then
    echo "Missing GOOGLE_APPLICATION_CREDENTIALS. Use --creds=... or export it." >&2
    exit 1
  fi

  if [ -z "$PROJECT_ID" ]; then
    if [ "$MODE" = "prod" ] && [ -n "${PROJECT_ID_PROD:-}" ]; then
      PROJECT_ID="$PROJECT_ID_PROD"
    fi
    if [ "$MODE" = "test" ] && [ -n "${PROJECT_ID_TEST:-}" ]; then
      PROJECT_ID="$PROJECT_ID_TEST"
    fi
  fi

  if [ -z "$PROJECT_ID" ]; then
    echo "Missing project ID. Use --project=... or set PROJECT_ID_PROD/PROJECT_ID_TEST." >&2
    exit 1
  fi

  if [ "$AUTH" = true ]; then
    export FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099
    firebase emulators:start --only functions,auth --project "$PROJECT_ID" $IMPORT_FLAG $EXPORT_FLAG
  else
    unset FIREBASE_AUTH_EMULATOR_HOST
    firebase emulators:start --only functions --project "$PROJECT_ID"
  fi
else
  export FIRESTORE_EMULATOR_HOST=127.0.0.1:8080

  if [ "$AUTH" = true ]; then
    export FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099
    firebase emulators:start --only functions,firestore,auth $IMPORT_FLAG $EXPORT_FLAG
  else
    unset FIREBASE_AUTH_EMULATOR_HOST
    firebase emulators:start --only functions,firestore
  fi
fi
