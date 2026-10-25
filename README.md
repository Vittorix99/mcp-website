# MCP-WEB-PROJECT

The approved Core WS1 work runs on Node.js 20 and Python 3.11. It is in
progress; staging and production operations require separate authorization.

```sh
nvm use
PYTHON_BIN=python3.11 scripts/bootstrap-dev.sh
scripts/dev-local.sh --dry-run
scripts/dev-local.sh
scripts/test-unit.sh
scripts/test-emulators.sh
cd mcp-website && npm run test:config && npm run lint && npm run build
```

The bootstrap installs hash-locked Python requirements into root `.venv` and
locked npm dependencies. Emulator commands create an ignored
`mcp-backend/functions/venv` symlink to that environment because Firebase CLI
14 requires this path. Existing unrelated environments are preserved and a
conflicting path is reported rather than overwritten.

Local development uses `demo-mcp-local`; tests use `demo-mcp-test`. All five
Firebase emulators bind to loopback. Provider calls use fakes, and Sender is
suspended in every environment. No export is imported automatically.
`scripts/dev-local.sh --seed` is reserved for the checked-in synthetic seed;
existing Firebase exports are never accepted by these commands.

Default frontend builds use a deterministic loopback fixture server. Release
builds require explicit approved staging/production public configuration and
reject `.env.local`; they do not themselves deploy anything. Secret values
must never be placed in `NEXT_PUBLIC_*` variables. The PayPal browser SDK uses
public client IDs; client secrets belong only to backend secret injection.

See `docs/process/DEVELOPMENT_METHODOLOGY.md` and
`docs/superpowers/plans/2026-10-25-core-ws1-environment-provider-safety.md`
for approval boundaries, pending work, and verification requirements.
