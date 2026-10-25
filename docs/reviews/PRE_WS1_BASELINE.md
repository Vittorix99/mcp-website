# Pre-WS1 baseline review

Date: 2026-10-25. Base: `26e1e145`.

The owner requested inspection and separate versioning of the existing local
changes before executing the Core WS1 plan. This batch contains Sender API
corrections, provider enablement, validation error handling, payment capture
terminal records, and frontend mutation/coming-soon handling. These changes
precede WS1 and are not evidence of WS1 completion.

## Corrections during review

- Replaced credential-shaped Genderize test literals with a clearly synthetic
  fixture. No credential was used, rotated, or revoked.
- Required `RUN_LIVE_PROVIDER_TESTS=1` for the two new live Genderize tests.
- Recorded completed PayPal captures before local amount validation and added
  a stable request id for retries. Two regression tests were observed failing
  before the fix and passing afterward. Complete payment reconciliation,
  concurrency, and recovery remain deferred to the payment workstream.
- Added the project model-routing policy in `AGENTS.md`: Sol coordinates and
  reviews; Luna implements small, fully specified mechanical tasks.

## Verification

- Focused backend checks: **142 passed, 2 skipped**, exit 0. Includes payment,
  trigger, HTTP error, Sender service/sync/API, credential tests, and mocked
  Sender integration tests. The two live Genderize tests skip without opt-in.
- Python compilation of application packages: exit 0.
- Frontend `npm run build`: exit 0, with protobuf dependency warnings and
  failed localhost backend reads. This does not prove a deterministic build;
  the WS1 fixture-build task addresses it.
- Frontend `npm run lint`: exit 1, interactive ESLint setup prompt. WS1 task 1
  replaces this command with a configured non-interactive check.
- Full backend unit suite: interrupted after 125 seconds while retrying a
  Firestore operation; **28 failed, 72 passed**, remaining tests unexecuted.
  Failures are in `tests/unit/api/admin/test_events_api.py` (2) and
  `tests/unit/api/admin/test_memberships_api.py` (26): stale request fixtures,
  expected validation messages, and outdated service stubs. Re-running with
  a fresh bytecode cache reproduced these failures. The old directory shown
  in earlier tracebacks was embedded bytecode metadata, not proof of imports
  from a different checkout. WS1 must establish an offline suite and account
  for these failures before completion.
- Sender transactional contracts checked against official documentation:
  [create](https://api.sender.net/transactional-campaigns/create/),
  [send](https://api.sender.net/transactional-campaigns/send-campaign/),
  [delete](https://api.sender.net/transactional_campaigns/delete-campaign/).

## Preserved local artifacts

The Firebase export directory, zero-byte macOS Icon file, `skills-lock.json`,
ignored env files, and service-account files are excluded from this batch.
No cloud deployment, provider live test, credential revocation, or staging
data mutation is part of this review.

## Independent review

Sol independently reviewed the diff and ran 85 focused tests (all passed).
No introduced Critical, Important, or actionable Minor finding remains.
The baseline is approved within its scope. The review explicitly deferred
complete payment atomicity/recovery, live Sender delivery, global suite and
build/lint health, and existing backend coming-soon eligibility. These are
not completion claims for the baseline or WS1; the safety work proceeds
with the limitations above recorded.
