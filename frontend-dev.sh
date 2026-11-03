#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
for argument in "$@"; do
  case "$argument" in
    --development=true|--auth-emulator=true) ;;
    *) echo "Only local development is supported. Start scripts/dev-local.sh for the full stack." >&2; exit 2 ;;
  esac
done
cd "$PROJECT_DIR/mcp-website"
export NEXT_PUBLIC_ENV=local
export NEXT_PUBLIC_BASE_URL=http://127.0.0.1:5001/demo-mcp-local/us-central1
export NEXT_PUBLIC_FIREBASE_PROJECT_ID=demo-mcp-local
export NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=demo-mcp-local.appspot.com
export NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=demo-mcp-local.firebaseapp.com
export NEXT_PUBLIC_FIREBASE_API_KEY=demo-api-key
export NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:localfixture
export NEXT_PUBLIC_AUTH_EMULATOR_HOST=127.0.0.1:9099
export NEXT_PUBLIC_FIRESTORE_EMULATOR_HOST=127.0.0.1:8080
export NEXT_PUBLIC_STORAGE_EMULATOR_HOST=127.0.0.1:9199
export NEXT_PUBLIC_FUNCTIONS_EMULATOR_HOST=127.0.0.1:5001
export NEXT_PUBLIC_ENABLE_ANALYTICS=false
export NEXT_PUBLIC_PAYPAL_ENV=fake
export NEXT_PUBLIC_PAYPAL_CLIENT_ID=sb
export __NEXT_PROCESSED_ENV=true
exec npm run dev
