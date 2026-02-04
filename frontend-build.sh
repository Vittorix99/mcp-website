#!/usr/bin/env bash
set -euo pipefail

export NEXT_PUBLIC_ENV=production
export NEXT_PUBLIC_PAYPAL_ENV=production
# Ensure auth emulator is disabled for production builds.
export NEXT_PUBLIC_AUTH_EMULATOR_HOST=

cd mcp-website
npm run build
