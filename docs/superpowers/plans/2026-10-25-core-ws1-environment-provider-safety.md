# Core WS1 Environment and Provider Safety Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Core WS1 safety boundary so local/test execution is deterministic and offline, environment/provider combinations fail closed, Firebase configuration has one source of truth, and pull requests receive repeatable safety checks.

**Architecture:** A typed backend `RuntimeSettings` model reads a non-secret environment catalog and validates the complete Firebase/provider matrix before any client initializes. Narrow provider factories select fake, disabled, sandbox, staging, or live adapters explicitly; frontend builds use a separate public-runtime validator. Root Firebase configuration, safe local commands, emulator smoke tests, and GitHub Actions consume the same policy without performing staging or production operations.

**Tech Stack:** Python 3.11, Pydantic 2, Firebase Admin/Functions, Firebase Emulator Suite, Node.js 20, Next.js 15, Node built-in test runner, GitHub Actions, Gitleaks, Doppler as a transitional injector.

**Spec:** `docs/superpowers/specs/2026-10-24-ws1-environment-provider-safety-design.md`

## Global Constraints

- Accept only `local`, `test`, `staging`, and `production`; reject the legacy `prod` alias and the old implicit “anything non-prod means test” behavior once entry points migrate atomically.
- `local` and `test` use demo Firebase project IDs, all required emulators, fake/disabled providers, and no Google service-account JSON.
- `staging` maps to `mcp-website-dev-39539`; `production` maps to `mcp-website-2a1ad`.
- Preserve all existing staging data, Auth users, Storage objects, and provider identifiers; Core WS1 performs no staging deployment or data mutation.
- Production deployment, live-provider changes, key rotation/revocation, and runtime proof are deferred to separately authorized gates.
- Keep Doppler as the transitional secret injector; do not replace it or upload/download secrets during Core WS1.
- Use Node.js 20 and Python 3.11.
- Keep API contracts, Firestore schemas, and user-visible business behavior unchanged.
- Never print secret values, payment data, tokens, private keys, or unnecessary personal data.
- Use the repository root as the only Firebase deploy root.
- Do not delete service-account files or revoke credentials during this plan.
- The current worktree contains uncommitted changes overlapping `external_services.py`, PayPal, Sender, triggers, and tests. Before execution, use `using-git-worktrees` and obtain an explicit decision about which existing changes form the base. Never stash, reset, overwrite, or silently exclude them.

## Review Focus

1. **Unknown or legacy environment name:** startup must fail before Firebase/provider initialization; Task 2 adds matrix tests.
2. **Production identifier or live credential in local/test:** validation must reject the process without echoing the value; Tasks 2–3 add negative and redaction tests.
3. **Import-time provider singleton bypassing the factory:** no request may reach a live provider because a module imported too early; Tasks 4–6 add construction and no-network tests.
4. **Frontend `.env.local`, localhost, or secret-shaped `NEXT_PUBLIC_*`:** PR/release validation must reject unsafe configuration; Task 7 adds Node tests and deterministic build fixtures.
5. **Missing emulator silently falling back to cloud:** commands must terminate before tests/functions run; Tasks 3, 9, and 10 add host and smoke checks.

---

## File Structure

### Shared backend policy

- `mcp-backend/functions/config/environment_catalog.json` — non-secret environment/resource/provider defaults used by backend, scripts, and frontend validation.
- `mcp-backend/functions/config/runtime_settings.py` — enums, typed settings, catalog loading, matrix validation, cache, and safe summary.
- `mcp-backend/functions/config/environment.py` — explicit local/test env-file loading only; no implicit `.env`/`.env.integration` selection.
- `mcp-backend/functions/config/firebase_config.py` — Firebase initialization from validated settings and ADC/emulator mode.

### Provider boundaries

- `mcp-backend/functions/services/payments/paypal_gateway.py` — PayPal gateway protocol, SDK adapter, deterministic fake, and factory.
- `mcp-backend/functions/services/communications/mail_service.py` — stable proxy plus fake/live mail factory.
- `mcp-backend/functions/services/memberships/pass2u_service.py` — real/fake Pass2U factory.
- `mcp-backend/functions/services/gender/gender_service.py` — deterministic/HTTP gender lookup boundary.
- `mcp-backend/functions/services/soundcloud/soundcloud_service.py` — fixture/live SoundCloud factory.
- Existing Sender service/sync modules — explicit settings-based enablement.

### Frontend safety

- `mcp-website/config/runtime-policy.cjs` — public environment validation usable from Node and `next.config.js`.
- `mcp-website/tests/runtime-policy.test.cjs` — Node built-in tests for environment and secret rules.
- `mcp-website/scripts/build-fixture-server.mjs` — loopback-only deterministic backend used by PR builds.
- `mcp-website/tests/fixtures/build-backend-responses.json` — explicit responses for build-time public reads.

### Tooling, Firebase, CI, and operations

- `.python-version`, `.nvmrc`, Python input/lock files — reproducible toolchain.
- Root `firebase.json`, `.firebaserc`, Firestore/Storage rules and indexes — canonical Firebase configuration.
- `scripts/dev-local.sh`, `scripts/test-unit.sh`, `scripts/test-emulators.sh` — safe entry points.
- `mcp-website/scripts/emulator-smoke.mjs` — client/Auth/Firestore/Storage smoke path.
- `.github/workflows/pr.yml` — pull-request verification only.
- `.gitleaks.toml` — redacted secret-scanning configuration.
- `docs/operations/ENVIRONMENT_RESOURCE_CATALOG.md`, `CREDENTIAL_TRANSITION.md`, and `GITHUB_ACTIONS_GUIDE.md` — non-secret operational records and user guide.

---

### Task 1: Pin the toolchain and deterministic test entry points

**Files:**
- Create: `.python-version`
- Create: `.nvmrc`
- Create: `mcp-backend/functions/requirements.in`
- Create: `mcp-backend/functions/requirements-dev.in`
- Modify: `mcp-backend/functions/requirements.txt`
- Modify: `mcp-backend/functions/requirements-dev.txt`
- Modify: `.gitignore`
- Create: `scripts/bootstrap-dev.sh`
- Create: `scripts/tests/test_toolchain_contract.py`
- Modify: `mcp-website/package.json:5-14`
- Modify: `mcp-website/package-lock.json`

**Interfaces:**
- Consumes: the approved Node.js 20 and Python 3.11 design constraints.
- Produces: `.venv/bin/python`, locked Python requirements, local `firebase` CLI through the frontend package, and stable `test:config`, `lint`, and build script names used by later tasks/CI.

- [ ] **Step 1: Write the failing toolchain contract test**

Create a stdlib `unittest` module with tests named `test_python_version_is_311`, `test_node_version_is_20`, `test_requirements_are_generated_from_inputs`, and `test_bootstrap_does_not_reference_service_account_files`. Assert exact version-file contents and that bootstrap uses `.venv` plus lock files; this test must run before project dependencies exist.

- [ ] **Step 2: Run the test and confirm the contract is absent**

Run: `python3 scripts/tests/test_toolchain_contract.py`

Expected: FAIL because `.python-version`, `.nvmrc`, input files, and bootstrap script do not exist.

- [ ] **Step 3: Add version files and dependency inputs**

Set `.python-version` to `3.11` and `.nvmrc` to `20`. Move current direct Python requirements into `requirements.in`; add `-r requirements.in`, `pytest==8.3.2`, and `pip-tools>=7.4,<8` to `requirements-dev.in`.

- [ ] **Step 4: Compile reproducible Python lock files**

Create a temporary Python 3.11 virtualenv, install the bounded `pip-tools`, and run:

```bash
python -m piptools compile --generate-hashes --output-file requirements.txt requirements.in
python -m piptools compile --generate-hashes --output-file requirements-dev.txt requirements-dev.in
```

Expected: both output files contain exact transitive versions and hashes.

- [ ] **Step 5: Add the clean-machine bootstrap**

Create `scripts/bootstrap-dev.sh` to verify Python 3.11 and Node 20, create `.venv`, install `requirements-dev.txt` with hashes, run `npm ci` in `mcp-website`, and never read service-account JSON. Add `.venv/` to `.gitignore`.

- [ ] **Step 6: Make frontend scripts deterministic**

In `package.json`, add `firebase-tools` version `14.26.0` as an exact dev dependency, add `test:config` using `node --test tests/runtime-policy.test.cjs`, and replace interactive `next lint` with `eslint .`. Keep `build:next` as the raw `next build` command; Task 7 will define safe wrapper scripts.

- [ ] **Step 7: Verify the toolchain contract**

Run:

```bash
python3 scripts/tests/test_toolchain_contract.py
cd mcp-website && npm ci && npm exec firebase -- --version
```

Expected: toolchain tests PASS, `npm ci` succeeds, and Firebase CLI reports the lockfile-pinned version.

- [ ] **Step 8: Commit**

```bash
git add .python-version .nvmrc .gitignore scripts/bootstrap-dev.sh scripts/tests/test_toolchain_contract.py mcp-backend/functions/requirements.in mcp-backend/functions/requirements-dev.in mcp-backend/functions/requirements.txt mcp-backend/functions/requirements-dev.txt mcp-website/package.json mcp-website/package-lock.json
git commit -m "build: pin WS1 toolchains"
```

---

### Task 2: Implement the typed runtime catalog and fail-closed matrix

**Files:**
- Create: `mcp-backend/functions/config/environment_catalog.json`
- Create: `mcp-backend/functions/config/runtime_settings.py`
- Create: `mcp-backend/functions/tests/unit/config/test_runtime_settings.py`
- Modify: `mcp-backend/functions/config/__init__.py`

**Interfaces:**
- Consumes: environment variables as an injected `Mapping[str, str]` and the versioned JSON catalog.
- Produces:
  - `RuntimeEnvironment`, `ProviderMode`, and `CredentialMode` string enums;
  - immutable `FirebaseRuntimeSettings`, `ProviderRuntimeSettings`, and `RuntimeSettings` Pydantic models;
  - `load_runtime_settings(environ: Mapping[str, str] | None = None) -> RuntimeSettings`;
  - `get_runtime_settings() -> RuntimeSettings`;
  - `clear_runtime_settings_cache() -> None` for tests;
  - `safe_runtime_summary(settings: RuntimeSettings) -> dict[str, object]`.

- [ ] **Step 1: Write failing environment-matrix tests**

Add parameterized tests covering all four valid environments and these exact failures:

```python
def test_unknown_environment_is_rejected(): ...
def test_local_rejects_production_project_and_bucket(): ...
def test_test_rejects_live_provider_mode_even_when_key_exists(): ...
def test_staging_rejects_production_project(): ...
def test_production_rejects_emulator_host_localhost_and_paypal_sandbox(): ...
def test_provider_key_does_not_enable_provider(): ...
def test_safe_summary_contains_modes_but_no_secret_values(): ...
```

Use sentinel secret values and assert that none appear in exception text or summaries.

- [ ] **Step 2: Run the tests and confirm the module is missing**

Run: `cd mcp-backend/functions && ../../.venv/bin/python -m pytest tests/unit/config/test_runtime_settings.py -q`

Expected: FAIL with import/module errors.

- [ ] **Step 3: Add the non-secret environment catalog**

Create schema version `1` with exact entries for:

- `local`: `demo-mcp-local`, loopback emulator hosts, all providers `fake` or `disabled`;
- `test`: `demo-mcp-test`, loopback emulator hosts, all providers `fake` or `disabled`;
- `staging`: `mcp-website-dev-39539`, staging bucket, PayPal `sandbox`, safe defaults for other providers;
- `production`: `mcp-website-2a1ad`, production bucket, explicitly configured live modes.

The catalog contains identifiers and modes only—never keys, tokens, passwords, or personal data.

- [ ] **Step 4: Implement the typed settings and validation API**

Use Pydantic models with `extra="forbid"` and frozen instances. `load_runtime_settings` merges catalog defaults with the injected mapping, then validates cross-field rules. Unknown environment/provider values and forbidden combinations raise a single redacted `RuntimeConfigurationError`.

- [ ] **Step 5: Implement the safe summary and cache controls**

Return environment, project ID, emulator/cloud booleans, provider modes, credential-presence booleans, and configuration-source category. Never return credential values or local credential paths.

- [ ] **Step 6: Run focused and existing configuration tests**

Run:

```bash
cd mcp-backend/functions
../../.venv/bin/python -m pytest tests/unit/config/test_runtime_settings.py tests/unit/config/test_environment.py tests/unit/config/test_firebase_config_credentials.py -q
```

Expected: all selected tests PASS.

- [ ] **Step 7: Commit**

```bash
git add mcp-backend/functions/config/__init__.py mcp-backend/functions/config/environment_catalog.json mcp-backend/functions/config/runtime_settings.py mcp-backend/functions/tests/unit/config/test_runtime_settings.py
git commit -m "feat: add fail-closed runtime policy"
```

---

### Task 3: Enforce settings before Firebase and service initialization

**Files:**
- Modify: `mcp-backend/functions/config/environment.py:1-47`
- Modify: `mcp-backend/functions/config/firebase_config.py:1-114`
- Modify: `mcp-backend/functions/main.py:8-27`
- Modify: `mcp-backend/functions/tests/unit/config/test_environment.py`
- Replace: `mcp-backend/functions/tests/unit/config/test_firebase_config_credentials.py`
- Create: `mcp-backend/functions/tests/unit/config/test_startup_policy.py`
- Modify: `mcp-backend/functions/tests/conftest.py`
- Modify: `mcp-backend/functions/tests/unit/conftest.py`
- Modify: `mcp-backend/functions/tests/integration/conftest.py`
- Create: `mcp-backend/functions/.env.example`

**Interfaces:**
- Consumes: `get_runtime_settings()` and `safe_runtime_summary()` from Task 2.
- Produces:
  - `load_environment(environ: MutableMapping[str, str] | None = None) -> Path | None`;
  - `initialize_firebase(settings: RuntimeSettings) -> tuple[firestore.Client, storage.Bucket | None]`;
  - module-compatible exports `db`, `bucket`, `cors`, and `region`.

- [ ] **Step 1: Write failing loader/startup tests**

Add tests named:

```python
def test_local_loads_only_explicit_mcp_env_file(): ...
def test_cloud_runtime_rejects_mcp_env_file(): ...
def test_local_startup_requires_all_selected_emulators(): ...
def test_emulator_startup_does_not_read_service_account_json(): ...
def test_cloud_startup_uses_application_default_credentials(): ...
def test_startup_summary_is_redacted(): ...
```

Patch Firebase constructors; assert validation happens before any constructor is called.

- [ ] **Step 2: Run tests and confirm current implicit loading fails the contract**

Run: `cd mcp-backend/functions && ../../.venv/bin/python -m pytest tests/unit/config/test_environment.py tests/unit/config/test_firebase_config_credentials.py tests/unit/config/test_startup_policy.py -q`

Expected: FAIL because `.env.integration`/service-account fallbacks are still implicit.

- [ ] **Step 3: Replace implicit dotenv selection**

Allow `MCP_ENV_FILE` only for `local` and `test`. Do not infer `.env` or `.env.integration`; do not override explicit process values; reject any env file in cloud/staging/production runtime. Document non-secret keys in `.env.example`.

- [ ] **Step 4: Refactor Firebase initialization around validated settings**

Local/test initialize against demo IDs and emulator hosts without resolving JSON files. Staging/production use ADC. Remove `FIREBASE_SERVICE_ACCOUNT_JSON`, default `service_account.json`, path searching, and credential-path logging from runtime initialization.

- [ ] **Step 5: Make `main.py` validate before importing provider/API modules**

Load the optional explicit env file, create/cache settings, emit the safe structured summary, initialize Firebase, then initialize services. Unknown/unsafe configuration must abort module discovery.

- [ ] **Step 6: Make test bootstrap explicit before application imports**

Set `MCP_ENV=test`, `GCLOUD_PROJECT=demo-mcp-test`, `STORAGE_BUCKET=demo-mcp-test.appspot.com`, and all required loopback emulator hosts in the top-level test bootstrap before importing APIs, repositories, or `firebase_config`. Remove implicit loading of `.env` and `.env.integration` from test conftest files.

- [ ] **Step 7: Verify startup behavior**

Run:

```bash
cd mcp-backend/functions
../../.venv/bin/python -m pytest tests/unit/config/test_environment.py tests/unit/config/test_firebase_config_credentials.py tests/unit/config/test_startup_policy.py -q
```

Expected: all selected tests PASS; no test requires a credential file.

- [ ] **Step 8: Commit**

```bash
git add mcp-backend/functions/.env.example mcp-backend/functions/config/environment.py mcp-backend/functions/config/firebase_config.py mcp-backend/functions/main.py mcp-backend/functions/tests/conftest.py mcp-backend/functions/tests/unit/conftest.py mcp-backend/functions/tests/integration/conftest.py mcp-backend/functions/tests/unit/config/test_environment.py mcp-backend/functions/tests/unit/config/test_firebase_config_credentials.py mcp-backend/functions/tests/unit/config/test_startup_policy.py
git commit -m "feat: enforce runtime policy at startup"
```

---

### Task 4: Replace PayPal fallback logic with an explicit gateway

**Files:**
- Create: `mcp-backend/functions/services/payments/paypal_gateway.py`
- Modify: `mcp-backend/functions/services/payments/event_payment_service.py:79-137,260-285,510-545`
- Modify: `mcp-backend/functions/api/public/event_payment_api.py:1-20`
- Modify: `mcp-backend/functions/tests/unit/services/test_event_payment_service.py`
- Create: `mcp-backend/functions/tests/unit/services/payments/test_paypal_gateway.py`
- Modify: relevant integration payment fixtures that inject `paypal_client`

**Interfaces:**
- Consumes: `RuntimeSettings.providers.paypal` from Task 2.
- Produces:
  - immutable `PayPalGatewayResponse(status_code: int, payload: dict)`;
  - `PayPalGateway` protocol with `create_order(request: OrderRequest) -> PayPalGatewayResponse` and `capture_order(order_id: str) -> PayPalGatewayResponse`;
  - `SdkPayPalGateway`, `FakePayPalGateway`, and `build_paypal_gateway(settings: RuntimeSettings) -> PayPalGateway`;
  - backward-compatible `paypal_client` injection only through a temporary SDK adapter used by existing tests.

- [ ] **Step 1: Write failing gateway policy tests**

Test that local/test return `FakePayPalGateway`, staging returns an SDK gateway configured for sandbox credentials only, production returns live only, and every missing/forbidden credential combination raises a redacted configuration error. Assert fake order IDs start with `FAKE-` and create/capture never call the SDK.

- [ ] **Step 2: Run the gateway tests and confirm failure**

Run: `cd mcp-backend/functions && ../../.venv/bin/python -m pytest tests/unit/services/payments/test_paypal_gateway.py -q`

Expected: FAIL because the gateway module does not exist.

- [ ] **Step 3: Implement gateway protocol, SDK adapter, and deterministic fake**

The fake returns PayPal-compatible dictionaries for `CREATED` and `COMPLETED` without network access. The SDK adapter is the only code allowed to select `Environment.SANDBOX` or `Environment.PRODUCTION`.

- [ ] **Step 4: Inject the gateway into `EventPaymentService`**

Add `paypal_gateway: PayPalGateway | None = None`. Remove `_build_paypal_client` and direct `PAYPAL_ENV` reads. Preserve the existing public service methods and response DTOs.

- [ ] **Step 5: Run payment unit tests**

Run:

```bash
cd mcp-backend/functions
../../.venv/bin/python -m pytest tests/unit/services/payments/test_paypal_gateway.py tests/unit/services/test_event_payment_service.py -q
```

Expected: PASS; no default test reaches PayPal.

- [ ] **Step 6: Commit**

```bash
git add mcp-backend/functions/services/payments/paypal_gateway.py mcp-backend/functions/services/payments/event_payment_service.py mcp-backend/functions/api/public/event_payment_api.py mcp-backend/functions/tests/unit/services/payments/test_paypal_gateway.py mcp-backend/functions/tests/unit/services/test_event_payment_service.py mcp-backend/functions/tests/integration/event_payment/api/test_event_payment_api.py mcp-backend/functions/tests/integration/event_payment/conftest.py mcp-backend/functions/tests/integration/event_payment/service/test_discount_code_event_flow.py mcp-backend/functions/tests/integration/event_payment/service/test_event_payment_service.py mcp-backend/functions/tests/integration/event_payment/service/test_membership_renewal_flow_integration.py
git commit -m "feat: make PayPal mode explicit"
```

---

### Task 5: Make MailerSend and Sender construction environment-aware

**Files:**
- Modify: `mcp-backend/functions/services/communications/mail_service.py:1-238`
- Modify: `mcp-backend/functions/services/communications/__init__.py`
- Modify: `mcp-backend/functions/services/sender/sender_service.py:1-60`
- Modify: `mcp-backend/functions/services/sender/sender_sync.py:1-180`
- Modify: `mcp-backend/functions/config/external_services.py`
- Modify: `mcp-backend/functions/main.py:20-23`
- Modify: `mcp-backend/functions/tests/unit/services/test_mail_service.py`
- Modify: `mcp-backend/functions/tests/unit/services/sender/test_sender_service.py`
- Modify: `mcp-backend/functions/tests/unit/services/sender/test_sender_sync.py`
- Create: `mcp-backend/functions/tests/unit/services/test_provider_network_defaults.py`

**Interfaces:**
- Consumes: runtime provider modes from Task 2.
- Produces:
  - `FakeMailService(MailService)` with in-memory `sent_messages` and no logging of message bodies;
  - `MailServiceProxy(MailService)` as the stable imported `mail_service` object;
  - `build_mail_service(settings: RuntimeSettings) -> MailService`;
  - `SenderService(..., settings: RuntimeSettings | None = None)` that cannot infer enablement from key presence.

- [ ] **Step 1: Write failing construction/no-network tests**

Assert local/test mail returns `FakeMailService`; staging mail is disabled unless explicitly configured with an allowlist; Sender stays disabled even when a key exists unless mode permits it; monkeypatch `requests.sessions.Session.request` to raise and prove local/test calls remain offline.

- [ ] **Step 2: Run focused tests and observe unsafe defaults**

Run: `cd mcp-backend/functions && ../../.venv/bin/python -m pytest tests/unit/services/test_mail_service.py tests/unit/services/sender/test_sender_service.py tests/unit/services/sender/test_sender_sync.py tests/unit/services/test_provider_network_defaults.py -q`

Expected: FAIL because the live mail singleton and key-driven Sender behavior are still reachable.

- [ ] **Step 3: Add the stable mail proxy and mode factory**

The exported `mail_service` object must delegate every call to `get_mail_service()` so modules that imported it before `main.py` initialization still observe the selected fake/live implementation.

- [ ] **Step 4: Enforce Sender mode independently of credentials**

Replace module-level `SENDER_ENABLED` decisions with validated settings. Explicit test keys remain usable only when a test passes an explicit settings object or injected route; normal construction follows runtime policy.

- [ ] **Step 5: Run communication/provider tests**

Run the command from Step 2.

Expected: all selected tests PASS and the no-network sentinel remains untouched.

- [ ] **Step 6: Commit**

```bash
git add mcp-backend/functions/config/external_services.py mcp-backend/functions/main.py mcp-backend/functions/services/communications/mail_service.py mcp-backend/functions/services/communications/__init__.py mcp-backend/functions/services/sender/sender_service.py mcp-backend/functions/services/sender/sender_sync.py mcp-backend/functions/tests/unit/services/test_mail_service.py mcp-backend/functions/tests/unit/services/sender/test_sender_service.py mcp-backend/functions/tests/unit/services/sender/test_sender_sync.py mcp-backend/functions/tests/unit/services/test_provider_network_defaults.py
git commit -m "feat: isolate mail and Sender by environment"
```

---

### Task 6: Add safe factories for Pass2U, gender enrichment, and SoundCloud

**Files:**
- Modify: `mcp-backend/functions/interfaces/services.py`
- Modify: `mcp-backend/functions/services/memberships/pass2u_service.py`
- Modify: `mcp-backend/functions/services/memberships/memberships_service.py:61-84`
- Modify: `mcp-backend/functions/services/memberships/merge_service.py`
- Create: `mcp-backend/functions/services/gender/__init__.py`
- Create: `mcp-backend/functions/services/gender/gender_service.py`
- Modify: `mcp-backend/functions/domain/participant_rules.py:1-70`
- Modify: `mcp-backend/functions/triggers/registration_trigger.py:1-80,140-200`
- Modify: `mcp-backend/functions/services/soundcloud/soundcloud_service.py`
- Modify: `mcp-backend/functions/services/radio/radio_episode_service.py`
- Modify: Pass2U, registration-trigger, participant, SoundCloud, and radio unit tests

**Interfaces:**
- Consumes: Task 2 settings and existing service protocols.
- Produces:
  - `FakePass2UService` and `build_pass2u_service(settings) -> Pass2UServiceProtocol`;
  - `GenderLookupProtocol.lookup(name: str) -> tuple[str, float]`;
  - `DeterministicGenderLookup`, `HttpGenderLookup`, and `build_gender_lookup(settings)`;
  - `FixtureSoundCloudService`, `SoundCloudServiceProtocol`, and `build_soundcloud_service(settings)`.

- [ ] **Step 1: Write failing fake/provider tests**

Cover deterministic Pass2U IDs and invalidation, gender fixtures without HTTP, SoundCloud fixture resolution, disabled staging behavior, and production-only real adapters. Add a no-network test that exercises all three local factories while `requests` is forbidden.

- [ ] **Step 2: Run the selected tests and confirm real constructors remain reachable**

Run:

```bash
cd mcp-backend/functions
../../.venv/bin/python -m pytest tests/unit/services/test_pass2u_service.py tests/unit/triggers/test_registration_trigger.py tests/unit/services/radio/test_soundcloud_service.py tests/unit/services/radio/test_radio_episode_service.py tests/unit/services/test_provider_network_defaults.py -q
```

Expected: FAIL on missing factories/fakes.

- [ ] **Step 3: Implement Pass2U real/fake selection**

Keep the existing live service behavior unchanged. The fake creates deterministic local-only pass IDs and returns successful invalidation without using `Pass2URoutes`.

- [ ] **Step 4: Extract the gender provider boundary**

Remove direct `requests` calls from `participant_rules.py` and `registration_trigger.py`; both consume an injected or factory-selected `GenderLookupProtocol`. Preserve the current fallback of `("N/A", 0.0)` on non-critical failures.

- [ ] **Step 5: Implement SoundCloud fixture/live selection**

The fixture returns deterministic track metadata and never reads/writes the Firestore token document. Production construction preserves the live service.

- [ ] **Step 6: Run provider and affected service tests**

Run the command from Step 2 plus `tests/unit/services/test_memberships_service.py`.

Expected: all selected tests PASS with no network calls.

- [ ] **Step 7: Commit**

```bash
git add mcp-backend/functions/interfaces/services.py mcp-backend/functions/services/memberships/pass2u_service.py mcp-backend/functions/services/memberships/memberships_service.py mcp-backend/functions/services/memberships/merge_service.py mcp-backend/functions/services/gender/__init__.py mcp-backend/functions/services/gender/gender_service.py mcp-backend/functions/services/soundcloud/soundcloud_service.py mcp-backend/functions/services/radio/radio_episode_service.py mcp-backend/functions/domain/participant_rules.py mcp-backend/functions/triggers/registration_trigger.py mcp-backend/functions/tests/unit/services/test_pass2u_service.py mcp-backend/functions/tests/unit/services/test_memberships_service.py mcp-backend/functions/tests/unit/triggers/test_registration_trigger.py mcp-backend/functions/tests/unit/services/radio/test_soundcloud_service.py mcp-backend/functions/tests/unit/services/radio/test_radio_episode_service.py mcp-backend/functions/tests/unit/services/test_provider_network_defaults.py
git commit -m "feat: isolate remaining external providers"
```

---

### Task 7: Validate frontend public configuration and make PR builds deterministic

**Files:**
- Create: `mcp-website/config/runtime-policy.cjs`
- Create: `mcp-website/tests/runtime-policy.test.cjs`
- Create: `mcp-website/tests/fixtures/build-backend-responses.json`
- Create: `mcp-website/scripts/build-fixture-server.mjs`
- Create: `mcp-website/scripts/build-safe.mjs`
- Create: `mcp-website/.env.example`
- Modify: `mcp-website/next.config.js:1-29`
- Modify: `mcp-website/config/firebase.js:1-50`
- Modify: `mcp-website/package.json:8-15`
- Modify: `mcp-website/package-lock.json`
- Modify: `frontend-dev.sh`
- Modify: `frontend-build.sh`

**Interfaces:**
- Consumes: `environment_catalog.json` from Task 2.
- Produces:
  - `validatePublicRuntime(environ: NodeJS.ProcessEnv, catalog: object) -> object`;
  - `findForbiddenPublicKeys(environ: NodeJS.ProcessEnv) -> string[]`;
  - `npm run build` for loopback-fixture PR builds;
  - `npm run build:release` for protected staging/production builds.

- [ ] **Step 1: Write failing Node policy tests**

Use `node:test` and `node:assert/strict` to cover unknown environments, project/bucket mismatches, production localhost/emulator rejection, staging production-resource rejection, and names matching `NEXT_PUBLIC_*_(SECRET|PRIVATE_KEY|TOKEN|PASSWORD|CREDENTIAL)`.

- [ ] **Step 2: Run tests and confirm the policy module is missing**

Run: `cd mcp-website && npm run test:config`

Expected: FAIL because `runtime-policy.cjs` does not exist.

- [ ] **Step 3: Implement public-runtime validation and wire it into Next**

`next.config.js` validates before returning configuration. `firebase.js` consumes only validated public fields. Error messages list forbidden key names but never values.

- [ ] **Step 4: Add deterministic build fixtures**

The fixture JSON explicitly defines responses for `get_all_events`, `get_next_event`, `get_membership_price_public`, `get_published_radio_episodes`, `get_latest_radio_episode`, and `get_radio_seasons`. The server binds to `127.0.0.1` on an ephemeral port, rejects unknown paths, and shuts down after the child build exits.

- [ ] **Step 5: Add safe build wrappers**

`build-safe.mjs` removes inherited environment values not allowed by the selected mode, rejects `.env.local` for release builds, and invokes either the fixture server or raw `next build`. Required backend fetch failures are fatal.

- [ ] **Step 6: Handle existing forbidden local keys without exposing values**

Run a key-name-only audit. If ignored local env files contain forbidden public keys, stop and request explicit authorization before removing those lines; never print or copy their values. Confirm application source does not consume the removed secret variables.

- [ ] **Step 7: Verify policy and builds**

Run:

```bash
cd mcp-website
npm run test:config
npm run lint
npm run build
```

Expected: config tests PASS, lint is non-interactive, and the fixture-backed build exits 0 without external backend traffic.

- [ ] **Step 8: Commit**

```bash
git add mcp-website/.env.example mcp-website/config/firebase.js mcp-website/config/runtime-policy.cjs mcp-website/tests mcp-website/scripts mcp-website/next.config.js mcp-website/package.json mcp-website/package-lock.json frontend-dev.sh frontend-build.sh
git commit -m "feat: validate frontend environment"
```

---

### Task 8: Consolidate Firebase configuration at the repository root

**Files:**
- Modify: `firebase.json`
- Modify: `.firebaserc`
- Modify: `storage.rules`
- Preserve: `firestore.rules`
- Preserve: `firestore.indexes.json`
- Delete: `mcp-website/firebase.json`
- Delete: `mcp-website/.firebaserc`
- Delete: `mcp-website/firestore.rules`
- Delete: `mcp-website/firestore.indexes.json`
- Delete: `mcp-website/storage.rules`
- Create: `scripts/validate-firebase-config.py`
- Create: `mcp-backend/functions/tests/unit/config/test_firebase_manifest.py`

**Interfaces:**
- Consumes: canonical project IDs/catalog from Task 2.
- Produces: one Firebase CLI root with explicit `staging` and `production` aliases, Python 3.11 Functions source, frontend source `mcp-website`, and the full emulator set.

- [ ] **Step 1: Write failing manifest tests**

Assert one `firebase.json`, no nested Firebase/rules/index files, no `default` production alias, exact staging/production mappings, Functions source `mcp-backend/functions`, runtime `python311`, hosting source `mcp-website`, and Auth/Functions/Firestore/PubSub/Storage emulators.

- [ ] **Step 2: Run the tests and confirm duplicate/drift failures**

Run: `cd mcp-backend/functions && ../../.venv/bin/python -m pytest tests/unit/config/test_firebase_manifest.py -q`

Expected: FAIL on duplicate files, alias policy, runtime, and hosting source.

- [ ] **Step 3: Consolidate manifests and aliases**

Remove the invalid Functions `region` manifest property; keep region ownership in decorators/options. Require explicit `--project` in documented commands. Preserve root composite indexes.

- [ ] **Step 4: Adopt and test the stricter Storage rules**

Use the existing frontend rule intent as the canonical policy: admin-only writes for event/photos/assets, public reads for event/photo/logo/pattern paths, authenticated membership-card reads, admin-only ticket reads/writes, and no broad authenticated event writes. Task 10 pins these decisions with positive and negative client tests.

- [ ] **Step 5: Add the standalone validator**

`scripts/validate-firebase-config.py` parses JSON, checks file uniqueness/paths/aliases, and exits non-zero without invoking Firebase or accessing the network.

- [ ] **Step 6: Verify schema and manifest tests**

Run:

```bash
.venv/bin/python scripts/validate-firebase-config.py
cd mcp-backend/functions && ../../.venv/bin/python -m pytest tests/unit/config/test_firebase_manifest.py -q
cd ../../mcp-website && npm exec firebase -- emulators:exec --only firestore --project demo-mcp-test "true"
```

For the last command, confirm configuration parsing reaches emulator startup without the previous manifest schema warning, then terminate it cleanly.

- [ ] **Step 7: Commit**

```bash
git add firebase.json .firebaserc firestore.rules firestore.indexes.json storage.rules scripts/validate-firebase-config.py mcp-backend/functions/tests/unit/config/test_firebase_manifest.py
git rm mcp-website/firebase.json mcp-website/.firebaserc mcp-website/firestore.rules mcp-website/firestore.indexes.json mcp-website/storage.rules
git commit -m "chore: consolidate Firebase configuration"
```

---

### Task 9: Replace unsafe local entry points with guarded commands

**Files:**
- Create: `scripts/lib/runtime_guard.py`
- Create: `scripts/dev-local.sh`
- Create: `scripts/test-unit.sh`
- Create: `scripts/test-emulators.sh`
- Modify: `emulator.sh`
- Modify: `frontend-dev.sh`
- Modify: `frontend-build.sh`
- Create: `mcp-backend/functions/tests/unit/config/test_runtime_guard_cli.py`
- Modify: `README.md` or the repository's existing developer-start document if present

**Interfaces:**
- Consumes: Task 2 catalog and Task 8 root Firebase configuration.
- Produces:
  - `validate_command_environment(name: str, environ: Mapping[str, str]) -> None` in `runtime_guard.py`;
  - empty and seeded local commands using `demo-mcp-local`;
  - unit and emulator test commands using `demo-mcp-test`;
  - compatibility wrappers that reject old `--env=prod`/`--prod-emulator` modes.

- [ ] **Step 1: Write failing CLI guard tests**

Test production project IDs, buckets, backend URLs, credential-file variables, missing emulator hosts, and legacy production flags. Assert errors mention key names/modes but not values.

- [ ] **Step 2: Run tests and confirm current scripts permit unsafe modes**

Run: `cd mcp-backend/functions && ../../.venv/bin/python -m pytest tests/unit/config/test_runtime_guard_cli.py -q`

Expected: FAIL because the guard does not exist and current scripts expose production modes.

- [ ] **Step 3: Implement guarded local/unit/emulator commands**

`dev-local.sh` starts the full emulator set and frontend under `MCP_ENV=local`. `test-unit.sh` forces `MCP_ENV=test` and denies network/cloud variables. `test-emulators.sh` uses `firebase emulators:exec --project demo-mcp-test` and never imports data unless `--seed` is explicit.

- [ ] **Step 4: Convert legacy scripts into safe compatibility wrappers**

Keep familiar filenames but forward only safe local/test options. Remove or reject production-emulator paths. Do not infer a project ID from service-account files.

- [ ] **Step 5: Verify CLI guards and dry-run output**

Run:

```bash
cd mcp-backend/functions && ../../.venv/bin/python -m pytest tests/unit/config/test_runtime_guard_cli.py -q
cd ../../.. && scripts/dev-local.sh --dry-run
scripts/test-unit.sh --dry-run
scripts/test-emulators.sh --dry-run
```

Expected: tests PASS; dry runs show demo IDs/emulator hosts and no credential path or production identifier.

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/runtime_guard.py scripts/dev-local.sh scripts/test-unit.sh scripts/test-emulators.sh emulator.sh frontend-dev.sh frontend-build.sh mcp-backend/functions/tests/unit/config/test_runtime_guard_cli.py README.md
git commit -m "chore: add safe local commands"
```

---

### Task 10: Add the full emulator smoke suite

**Files:**
- Create: `mcp-website/scripts/emulator-smoke.mjs`
- Create: `mcp-website/tests/fixtures/emulator-seed.json`
- Create: `mcp-backend/functions/tests/smoke/test_functions_discovery.py`
- Create: `mcp-backend/functions/tests/smoke/test_trigger_wiring.py`
- Modify: `scripts/test-emulators.sh`
- Modify: `firebase.json`

**Interfaces:**
- Consumes: the safe test command, canonical rules, full emulator topology, and fake providers.
- Produces: one command that proves Functions discovery, Firestore/Auth/Storage client rules, one background trigger path, clean shutdown, and zero cloud/provider traffic.

- [ ] **Step 1: Write failing Functions discovery and trigger tests**

`test_functions_discovery.py` imports `main` under `MCP_ENV=test` with complete emulator hosts and asserts representative exported functions exist. `test_trigger_wiring.py` writes a minimal `purchases/smoke-purchase` document with `ref_id="smoke-event"`, then polls the emulator for the analytics rebuild job enqueued by `on_purchase_written`.

- [ ] **Step 2: Write the client smoke script**

Using installed Firebase client/Admin SDKs, create an emulator-only admin user with claims, sign in through Auth emulator, verify public Firestore read, admin Firestore write, approved Storage write/read, and non-admin rejection for an admin-only Storage path. Delete created fixtures before exit.

- [ ] **Step 3: Run against no emulators and confirm fast failure**

Run: `scripts/test-emulators.sh`

Expected before implementation completion: FAIL with a specific missing-emulator or Functions-discovery error, never a cloud request.

- [ ] **Step 4: Complete orchestration and run the smoke suite**

Use `firebase emulators:exec --only functions,firestore,auth,storage,pubsub --project demo-mcp-test`. Run Python smoke tests and the Node client script inside the emulator lifecycle.

- [ ] **Step 5: Verify repeatability**

Run: `scripts/test-emulators.sh && scripts/test-emulators.sh`

Expected: both runs PASS from a clean emulator state and shut down without retained test data.

- [ ] **Step 6: Commit**

```bash
git add firebase.json scripts/test-emulators.sh mcp-website/scripts/emulator-smoke.mjs mcp-website/tests/fixtures/emulator-seed.json mcp-backend/functions/tests/smoke
git commit -m "test: add emulator smoke suite"
```

---

### Task 11: Add pull-request CI and secret scanning

**Files:**
- Create: `.github/workflows/pr.yml`
- Create: `.secretsignore`
- Create: `scripts/security/scan_secrets.py`
- Create: `scripts/ci/assert-safe-environment.py`
- Create: `mcp-backend/functions/tests/unit/config/test_ci_environment.py`
- Modify: `scripts/test-unit.sh`
- Modify: `scripts/test-emulators.sh`

**Interfaces:**
- Consumes: Tasks 1–10 verification commands.
- Produces: a PR workflow with no deploy permission, no cloud credential, concurrency cancellation, deterministic redacted secret scanning, offline unit/config checks, frontend verification, and emulator smoke tests.

- [ ] **Step 1: Write failing CI-environment tests**

Test that the CI guard rejects staging/production IDs, `GOOGLE_APPLICATION_CREDENTIALS`, raw service-account JSON variables, live provider modes, and missing demo IDs. Assert values are never printed.

- [ ] **Step 2: Run tests and confirm the guard is missing**

Run: `cd mcp-backend/functions && ../../.venv/bin/python -m pytest tests/unit/config/test_ci_environment.py -q`

Expected: FAIL because the guard does not exist.

- [ ] **Step 3: Implement the CI guard and PR workflow**

Copy the deterministic stdlib-only scanner from the installed AI-Native SDLC skill into `scripts/security/scan_secrets.py` and verify its `--path`, `--staged`, and `--base/--head` modes. Grant workflow permissions `contents: read` only. Pin actions by full commit SHA: `actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09`, `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`, and `actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444`. Use Node 20 and Python 3.11, dependency caches, `npm ci`, hashed Python locks, the redacted scanner, backend policy/offline tests, frontend config/lint/fixture-build, and the emulator smoke command. Do not define deploy jobs or environment secrets.

- [ ] **Step 4: Run the workflow commands locally**

Run:

```bash
.venv/bin/python scripts/ci/assert-safe-environment.py
.venv/bin/python scripts/security/scan_secrets.py --path . --config .secretsignore --quiet
scripts/test-unit.sh
cd mcp-website && npm run test:config && npm run lint && npm run build
cd .. && scripts/test-emulators.sh
```

Expected: every command exits 0 with demo IDs and no cloud/provider credentials.

- [ ] **Step 5: Run redacted repository/history scanning**

Run the deterministic scanner against the working tree and PR diff. Then perform the one-time full-history audit with `gitleaks detect --source . --redact --no-banner`. If Gitleaks is unavailable, record that history audit as a blocked operational prerequisite rather than weakening the PR gate. If a real historical secret is detected, stop, report only the finding type/path/commit, and create a separate rotation/remediation decision—never paste the value or rewrite history automatically.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/pr.yml .secretsignore scripts/security/scan_secrets.py scripts/ci/assert-safe-environment.py scripts/test-unit.sh scripts/test-emulators.sh mcp-backend/functions/tests/unit/config/test_ci_environment.py
git commit -m "ci: add WS1 pull request gates"
```

---

### Task 12: Record the resource, credential, and GitHub Actions operating model

**Files:**
- Create: `docs/operations/ENVIRONMENT_RESOURCE_CATALOG.md`
- Create: `docs/operations/CREDENTIAL_TRANSITION.md`
- Create: `docs/process/GITHUB_ACTIONS_GUIDE.md`
- Create: `docs/operations/workflow-templates/staging.yml`
- Create: `docs/operations/workflow-templates/production.yml`
- Create: `scripts/docs/check-links.py`
- Modify: `docs/README.md`
- Modify: `docs/process/DEVELOPMENT_METHODOLOGY.md`
- Modify: `docs/superpowers/specs/2026-10-24-ws1-environment-provider-safety-design.md` only if implementation evidence requires an approved clarification

**Interfaces:**
- Consumes: the implemented catalog, commands, CI workflow, and credential findings.
- Produces: human-readable non-secret ownership/resource tables, an ADC/WIF transition and revocation gate, a user guide for GitHub Actions, and inactive deployment templates for future gates.

- [ ] **Step 1: Create the non-secret resource catalog**

Record environment, Firebase project/bucket, allowed origins/backend URLs, provider mode/account identifier, data policy, and owner role. Mark unknown provider identifiers as `blocked before staging activation`, never with a secret placeholder.

- [ ] **Step 2: Create the credential transition record**

For each local JSON/service identity, record project, purpose, observed code reference, proposed ADC/WIF replacement, accountable owner role, rotation prerequisite, revocation gate, and status. Do not include key IDs when they are not needed for ownership/revocation coordination.

- [ ] **Step 3: Write the GitHub Actions user guide requested by the owner**

Explain workflow triggers, PR checks, status/log navigation, safe reruns, artifacts, environment protection, future staging/production approvals, WIF at a conceptual level, failure escalation, and the fact that no deployment workflow is active in Core WS1.

- [ ] **Step 4: Add inactive deployment workflow templates**

Templates show required future jobs and gates but live under `docs/operations/workflow-templates/`, not `.github/workflows/`; therefore GitHub cannot execute them. They must use environment-scoped WIF and immutable artifact references when later activated.

- [ ] **Step 5: Update documentation indexes and methodology status**

Link all new artifacts from `docs/README.md`. Record Core WS1 as implemented only after Task 13 verification; staging remains pending and production deferred.

- [ ] **Step 6: Verify documentation links and secret hygiene**

Implement `scripts/docs/check-links.py PATH...` to URL-decode and resolve repository-local Markdown targets while skipping HTTP(S), mailto, and anchor-only links. Run:

```bash
.venv/bin/python scripts/docs/check-links.py docs/README.md docs/process docs/operations docs/superpowers
.venv/bin/python scripts/security/scan_secrets.py --path docs --config .secretsignore --quiet
```

Expected: all local links resolve and no secret-shaped material is present.

- [ ] **Step 7: Commit**

```bash
git add docs/README.md docs/process/DEVELOPMENT_METHODOLOGY.md docs/process/GITHUB_ACTIONS_GUIDE.md docs/operations/ENVIRONMENT_RESOURCE_CATALOG.md docs/operations/CREDENTIAL_TRANSITION.md docs/operations/workflow-templates/staging.yml docs/operations/workflow-templates/production.yml scripts/docs/check-links.py docs/superpowers/specs/2026-10-24-ws1-environment-provider-safety-design.md
git commit -m "docs: add WS1 operating runbooks"
```

---

### Task 13: Run the Core WS1 completion verification and review gate

**Files:**
- Create: `docs/reviews/WS1_CORE_VERIFICATION.md`
- Modify: only files required to fix failures discovered by the commands below; keep fixes within their owning task boundaries.

**Interfaces:**
- Consumes: every task output and the Definition of Done in `docs/process/DEVELOPMENT_METHODOLOGY.md`.
- Produces: a fresh, reproducible evidence record for human review; no staging or production action.

- [ ] **Step 1: Verify repository policy and generated-file consistency**

Run:

```bash
.venv/bin/python scripts/validate-firebase-config.py
.venv/bin/python scripts/ci/assert-safe-environment.py
git diff --check
```

Expected: all exit 0.

- [ ] **Step 2: Run the complete offline backend unit suite**

Run: `scripts/test-unit.sh`

Expected: exit 0, no network calls, no emulator retries, and zero failures.

- [ ] **Step 3: Run frontend verification**

Run:

```bash
cd mcp-website
npm ci
npm run test:config
npm run lint
npm run build
```

Expected: all commands exit 0; build traffic remains loopback-only.

- [ ] **Step 4: Run the emulator suite twice**

Run: `cd .. && scripts/test-emulators.sh && scripts/test-emulators.sh`

Expected: both runs exit 0 with clean startup/shutdown and disposable data.

- [ ] **Step 5: Run secret scanning**

Run:

```bash
.venv/bin/python scripts/security/scan_secrets.py --path . --config .secretsignore --quiet
.venv/bin/python scripts/security/scan_secrets.py --staged --config .secretsignore --quiet
gitleaks detect --source . --redact --no-banner
```

Expected: no unresolved secret finding. A historical finding blocks completion and triggers a separate credential-remediation decision; history is not rewritten automatically.

- [ ] **Step 6: Perform plan-versus-diff review**

Confirm every changed file belongs to a task, no API/schema/user-flow contract changed, duplicate Firebase files are gone, no deployment workflow is active, and staging/production operations remain unexecuted.

- [ ] **Step 7: Request code review and resolve findings**

Use `requesting-code-review`; apply `receiving-code-review` to verified findings. Rerun every affected verification after corrections.

- [ ] **Step 8: Write the evidence record**

Record commands, exit codes, test counts, expected skips, environment/demo IDs, known limitations, staging status `pending authorization`, and production status `deferred`. Include no secrets or personal data.

- [ ] **Step 9: Commit**

```bash
git add docs/reviews/WS1_CORE_VERIFICATION.md
git commit -m "docs: record Core WS1 verification"
```

---

## Plan Self-Review

### Spec coverage

- Environment identities, catalog, and fail-closed matrix: Tasks 2–3.
- Provider fake/disabled/sandbox/live selection: Tasks 4–6.
- Frontend public configuration and deterministic builds: Task 7.
- Canonical Firebase configuration and rules/indexes: Task 8.
- Reproducible toolchain and safe commands: Tasks 1 and 9.
- Full emulator topology and smoke proof: Task 10.
- PR CI, no production credentials, and secret scanning: Task 11.
- Resource catalog, credential transition, GitHub education, and inactive deploy designs: Task 12.
- Fresh completion evidence and independent review: Task 13.
- Staging deploy and production operations: deliberately excluded by the approved authorization boundary.

### Type and interface consistency

- All backend factories consume the single `RuntimeSettings` type from Task 2.
- `get_runtime_settings()` is the only default runtime settings accessor.
- Provider modes originate in the catalog/settings models; keys never enable providers.
- Local/test fakes implement the same protocols consumed by existing services.
- Frontend policy reads the same JSON catalog but exposes browser-safe fields only.
- Every command after Task 1 uses `.venv`, Node 20, locked Python files, and `npm ci`.

### Execution precondition

The plan is ready, but implementation must not begin in the current dirty worktree. At the execution gate, first identify whether the existing uncommitted Sender/PayPal/configuration changes are intended prerequisites, unrelated parallel work, or changes to be completed separately. Create the isolated worktree only after that decision; preserve all user changes in place.
