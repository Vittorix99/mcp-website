# WS1 Design — Environment, Credential, and Provider Safety

**Project:** MCP-WEB-PROJECT

**Status:** approved — implementation planning authorized

**Created:** 2026-10-24

**Last updated:** 2026-10-25

**Approved:** 2026-10-25, explicit project-owner approval recorded in the working session

**Parent intent:** `intent/intent.md`

**Evidence baseline:**

- `docs/architecture/CURRENT_STATE_ASSESSMENT_2026-10-24.md`;
- `docs/architecture/API_CONTRACT_INVENTORY_2026-10-24.md`;
- repository and local-runtime inspection performed on 2026-10-24.

## 1. Intent

WS1 establishes a fail-closed boundary between local, test, staging, and production before broader refactoring begins.

The work makes environment selection explicit, prevents non-production processes from using production Firebase resources or live write-capable providers, replaces local service-account dependencies with emulator-safe configuration and Application Default Credentials, and creates the minimum reproducible test/CI harness needed to prove those guarantees.

WS1 changes configuration and delivery safety. It does not change product behavior, API contracts, Firestore schemas, production data, or the long-term Firebase-versus-Supabase decision.

## 2. Goals

1. Define exactly four runtime environments: `local`, `test`, `staging`, and `production`.
2. Validate the complete environment/resource/provider matrix before application services initialize.
3. Make local and automated-test execution cloud-independent by default.
4. Make PayPal and other write-capable providers fail closed outside their approved environments.
5. Establish one canonical Firebase configuration, rules, indexes, and emulator topology.
6. Make Python and Node setup reproducible on a clean machine.
7. Remove the runtime requirement for repository-local service-account JSON files.
8. Introduce a small offline unit suite and emulator smoke suite that can become the first CI gate.
9. Preserve current public behavior while the safety boundary is introduced.

## 3. Non-goals

- Refactoring business domains or moving files into a new backend architecture.
- Changing endpoint request or response contracts.
- Optimizing Firestore queries or function performance.
- Migrating data to PostgreSQL or Supabase.
- Replacing Doppler before its ownership and access model have been reviewed.
- Deleting staging or production data.
- Rotating or revoking credentials without a separately approved operational step.
- Redesigning the frontend.
- Removing external providers whose business ownership is still unresolved.
- Solving the non-atomic PayPal capture/provisioning workflow; WS1 prevents wrong-environment use, while payment recovery belongs to a later dedicated workstream.

## 4. Anti-goals

WS1 is unsuccessful if it creates any of the following:

- a second environment abstraction alongside the old one;
- a hidden fallback from mock or sandbox to live services;
- a local workflow that still requires production credentials;
- a canonical Firebase file that silently changes based on the working directory;
- a CI job capable of writing to production;
- secrets copied into `NEXT_PUBLIC_*`, logs, artifacts, or Git;
- a large provider/domain rewrite disguised as configuration cleanup;
- credential revocation before the replacement path has been proven.

## 5. Constraints and verified starting conditions

| Evidence | Design consequence |
|---|---|
| `MCP_ENV` currently distinguishes only `test` and `prod`. | Environment semantics must be replaced, not extended with more implicit branches. |
| The backend loads `.env.integration` for every non-`prod` execution. | Local, automated test, and staging configuration need separate explicit sources. |
| PayPal uses sandbox only when `PAYPAL_ENV == "sandbox"`; every other value selects production. | Provider mode must be a validated enum with no live fallback. |
| The current emulator script permits a local Functions process configured for production. | Production project IDs and live provider modes must be denied in local/emulator commands. |
| Root and frontend Firebase configurations, indexes, and Storage rules diverge. | A single deploy root and canonical resource files are required. |
| Functions discovery fails in the current local Python environment because dependencies are not reproducible. | Toolchain recreation and dependency installation are WS1 acceptance requirements. |
| Frontend production builds can load `.env.local` and complete while backend requests fail. | Builds must validate their environment and fail on forbidden local URLs or incomplete required data. |
| Service-account JSON files exist locally and are represented in the Doppler manifest. | The target state uses emulator credentials locally and ADC/WIF in cloud/CI; JSON revocation is delayed until verified. |
| Provider clients are initialized through a mixture of globals, services, and direct environment reads. | WS1 introduces a narrow configuration/provider-selection seam without restructuring domain logic. |
| The repository has no CI workflow and the current lint command is interactive. | WS1 supplies only the minimum deterministic CI foundation needed for environment safety. |

## 6. Approaches considered

### Approach A — Patch individual hazards

Add isolated checks around PayPal, the emulator script, and credential loading while retaining the current environment loader, duplicated Firebase configuration, and provider-specific environment reads.

**Advantages:** smallest immediate diff.

**Disadvantages:** preserves multiple sources of truth; every new integration can bypass the checks; difficult to test as one policy; does not make clean-machine setup reproducible.

**Decision:** rejected. It reduces selected symptoms but does not establish the safety boundary WS1 exists to create.

### Approach B — Central validated runtime policy with incremental adapters

Introduce one typed runtime configuration and policy validator, make every entry point validate before initializing Firebase or external providers, select provider implementations through narrow factories, consolidate Firebase configuration, and add deterministic local/test commands and CI checks.

**Advantages:** fail-closed behavior is testable in one place; migration can be incremental; existing services and API contracts remain intact; creates seams useful for later restructuring and platform assessment.

**Disadvantages:** touches startup, scripts, provider construction, tests, and deployment configuration; requires a carefully ordered rollout.

**Decision:** recommended. This is the design specified below.

### Approach C — Rebuild development infrastructure first

Containerize the full stack, replace Doppler, redesign all provider adapters, upgrade runtimes, and introduce a complete CI/CD platform in one workstream.

**Advantages:** potentially cleaner final developer experience.

**Disadvantages:** large blast radius; mixes policy, tooling, providers, and delivery; delays the critical PayPal and production-isolation protections; hard to roll back.

**Decision:** rejected for WS1. Individual elements may be considered later using measured need.

## 7. Target operating model

### 7.1 Environment identities

| Environment | Purpose | Firebase target | Data policy | Network/provider default |
|---|---|---|---|---|
| `local` | Interactive development | Emulator-only demo project ID | Empty or optional deterministic synthetic seed | Offline mocks; no cloud writes |
| `test` | Automated unit/integration execution | Ephemeral emulator-only demo project ID | Test-owned fixtures, resettable | Offline mocks; network denied by default |
| `staging` | Persistent acceptance and E2E | Dedicated non-production Firebase project | Persistent synthetic scenarios plus tagged volumetric data | Sandbox or controlled staging integrations only |
| `production` | Live customer workload | Dedicated production Firebase project | Production data | Explicitly configured live integrations |

Cloud mapping adopted by this design:

- `staging` → `mcp-website-dev-39539`;
- `production` → `mcp-website-2a1ad`.

Local and test use Firebase demo project IDs that cannot resolve to cloud projects. No local command infers a cloud project from a credential file. WS1 treats all existing staging records, Auth users, Storage objects, and provider-linked identifiers as data to preserve until the later test-data workstream authorizes cleanup.

### 7.2 Configuration ownership

The backend receives one immutable `RuntimeSettings` object created during startup. It contains only validated values and capability decisions. Application services do not decide the environment by reading arbitrary environment variables.

Conceptual groups:

```text
RuntimeSettings
├── environment
├── firebase
│   ├── project_id
│   ├── storage_bucket
│   ├── emulator endpoints
│   └── credential mode
├── providers
│   ├── paypal mode
│   ├── mail mode
│   ├── sender mode
│   ├── pass provider mode
│   ├── gender enrichment mode
│   └── sound metadata mode
└── safety
    ├── network policy
    ├── allowed email recipients/domains
    └── production denylist
```

The frontend receives a separate public configuration containing only browser-safe values. Secret names and values are forbidden from the `NEXT_PUBLIC_*` namespace.

### 7.3 Configuration sources and precedence

| Runtime | Allowed source | Credential model |
|---|---|---|
| Local | Checked-in non-secret defaults plus optional developer-local secret injection for explicitly selected sandbox tests | No Google credential for emulators |
| Automated test | Test harness values generated by the test runner | No cloud credential |
| Staging runtime | Deployment environment and managed secret injection | Runtime ADC |
| Production runtime | Deployment environment and managed secret injection | Runtime ADC |
| CI deploy | CI environment plus approved secret provider | Workload Identity Federation or equivalent short-lived identity |

Rules:

1. Cloud runtimes never read repository `.env` files.
2. Local/test never load production `.env` files or service-account JSON.
3. Staging/production never infer environment from the presence of a secret.
4. Every required setting is validated before Firebase clients or provider clients are created.
5. Logs report setting presence and selected modes, never secret values.
6. Doppler remains the transitional secret-injection mechanism during WS1; replacing it is out of scope. Its access, audit, and CI policy must be inventoried before a cloud deployment workflow is activated.

## 8. Fail-closed policy

Startup validates the complete matrix. A violation terminates the process with a redacted, actionable error.

### 8.1 Required prohibitions

- `local` or `test` with a known staging/production Firebase project ID or bucket;
- `local` or `test` without the required emulator hosts for a Firebase capability being used;
- any non-production environment with PayPal live mode or live PayPal credentials selected;
- staging with the production project, bucket, backend URL, or production-only provider account;
- production with an emulator host, demo project ID, sandbox PayPal mode, or localhost backend URL;
- a browser-exposed variable whose name indicates a secret, private key, token, or credential;
- provider mode not present in the allowed enum;
- unknown environment names or legacy aliases after the atomic command/config migration;
- CI test jobs with cloud credentials or production project identifiers present.

### 8.2 Safe startup summary

After validation, startup emits one structured summary containing:

- environment;
- Firebase project ID and emulator/cloud mode;
- Storage emulator/cloud mode;
- provider mode names;
- whether required credentials are present;
- configuration source category;
- application version or commit when available.

It never emits credential paths containing sensitive names, secret values, tokens, payment data, or personal data.

## 9. Provider policy

Providers are selected through narrow factories or injected interfaces. WS1 does not redesign their business operations.

| Provider | Local | Test | Staging | Production |
|---|---|---|---|---|
| PayPal | Mock | Mock; optional separately invoked sandbox contract suite | Sandbox only | Live only |
| MailerSend | In-memory/file fake | Fake | Controlled staging sender with recipient allowlist | Live |
| Sender.net | Disabled/fake | Disabled/fake | Disabled by default; dedicated staging configuration only if explicitly approved | Live only if retained as a business dependency |
| Pass2U | Fake | Fake | Dedicated test configuration or disabled | Live |
| Genderize.io | Deterministic fixture | Deterministic fixture | Optional controlled integration | Live or explicitly disabled |
| SoundCloud | Fixture/cached sample | Fixture | Read-only staging credentials or fixture | Live read integration |

Every provider has an explicit mode such as `disabled`, `fake`, `sandbox`, `staging`, or `live`. Unsupported combinations fail startup. The mere presence of an API key never enables a provider.

Email delivery outside production requires an allowlist or sink so that synthetic tests cannot contact real customers.

Until dedicated staging capabilities are confirmed, the concrete staging defaults are:

- PayPal sandbox enabled only through protected staging secrets;
- MailerSend disabled except for an explicitly allowlisted staging sender and recipient domain;
- Sender.net disabled;
- Pass2U disabled;
- Genderize.io disabled and replaced by deterministic fixtures;
- SoundCloud read-only with a staging credential, or fixtures when no separate credential exists.

Enabling any disabled staging provider is a configuration change requiring an owner, credentials, an allowlist or test account, and a provider-specific smoke test. It does not require redesigning WS1.

## 10. Firebase configuration design

### 10.1 Canonical deploy root

The repository root becomes the only Firebase deploy root. It owns:

- `firebase.json`;
- `.firebaserc` aliases;
- `firestore.rules`;
- `firestore.indexes.json`;
- `storage.rules`;
- emulator ports and services.

Duplicate frontend Firebase resource files are removed only after their effective differences are reviewed and the canonical versions are covered by emulator tests.

### 10.2 Project aliases

The target aliases are explicit:

- `staging` → `mcp-website-dev-39539`;
- `production` → `mcp-website-2a1ad`.

Deploy and emulator commands always receive an explicit project or demo project ID. Scripts never rely on a production `default` alias.

### 10.3 Emulator topology

The standard local stack starts, as needed by the application:

- Functions;
- Firestore;
- Authentication;
- Storage;
- Pub/Sub;
- Emulator UI.

The default uses a demo project ID and does not import data. Optional import requires an explicit flag and accepts only a documented synthetic export location. Existing cloud-derived exports are not imported by default and are handled later by the test-data workstream.

## 11. Credential lifecycle design

### Target state

- Local and test: no service-account JSON; emulators and mock providers.
- Staging and production runtimes: platform-provided ADC.
- CI deployments: short-lived federated identity with environment-scoped permissions.
- Developer sandbox access, when explicitly required: user ADC or approved secret injection with least privilege.

### Transition sequence

1. Inventory each existing service account by project, IAM role, key age, API usage, and current caller.
2. Prove local and test operation without JSON credentials.
3. Prove staging deployment/runtime using ADC or WIF.
4. Prove production deployment/runtime using ADC or WIF without revoking the old key.
5. Rotate and then revoke legacy keys in a separately approved operational window.
6. Remove obsolete JSON entries from secret manifests only after usage evidence confirms they are unnecessary.
7. Record the outcome without storing key material.

No credential is deleted or revoked as part of a normal code commit.

## 12. Local developer experience

WS1 provides documented, deterministic entry points with these semantics:

| Command intent | Behavior |
|---|---|
| Install | Recreate pinned Python and Node dependencies on a clean machine. |
| Local empty | Start required emulators, mock providers, backend, and frontend with no seed. |
| Local seeded | Start the same stack and apply an optional deterministic synthetic seed. |
| Unit test | Run offline tests with network and cloud access denied. |
| Integration test | Start or require the emulator suite, reset fixtures, run tests, and report skipped/failed prerequisites clearly. |
| Sandbox contract test | Explicit opt-in command for approved provider sandboxes; never part of the default suite. |
| Production build | Build with validated production public configuration and no `.env.local` override. |

The exact command names belong in the implementation plan. The design requires one documented entry point per intent, not a particular task runner.

## 13. Minimum test and CI design

### 13.1 Characterization and policy tests

Before changing startup behavior, tests capture the current entry points and then define the target matrix.

Required unit cases include:

- every valid environment/resource/provider combination;
- unknown environment rejection;
- local/test rejection of cloud project IDs and buckets;
- local/test rejection of live provider modes;
- staging rejection of production resources;
- production rejection of emulator hosts, localhost URLs, and sandbox modes;
- provider disabled-by-default behavior;
- secret-shaped frontend variable rejection;
- safe redaction in configuration errors and startup summaries;
- cloud runtime uses ADC without a local credential path;
- emulator runtime does not require Google credentials.

### 13.2 Emulator smoke suite

The minimum smoke suite proves:

1. all required emulators start under a demo project ID;
2. Functions discovery imports successfully;
3. a public function can read/write test-owned Firestore data as designed;
4. Firebase Auth emulator token flow reaches an authenticated endpoint;
5. Storage emulator accepts an approved test operation under canonical rules;
6. a Pub/Sub or Firestore-triggered test proves required background wiring without external network calls;
7. shutdown is clean and test data is disposable.

### 13.3 Initial CI gates

GitHub Actions is the target CI/CD platform because the repository remote is hosted on GitHub and no competing pipeline configuration exists in the repository. A different platform requires a design amendment before implementation planning.

Pull-request CI initially requires:

- clean dependency installation from pinned manifests;
- secret scanning of repository and diff;
- backend environment-policy unit tests;
- frontend environment-policy tests;
- offline unit subset;
- emulator smoke suite;
- non-interactive frontend lint/type/build check;
- confirmation that test jobs contain no production project IDs or cloud credentials.

Pull-request frontend builds use a deterministic loopback fixture service and reject unexpected external network access. Staging release builds use the staging backend in a protected workflow. Production release builds may use the production backend only after production authorization; required fetch failures are fatal, and `.env.local` is forbidden. Moving all build-time reads to runtime is a later contract/performance decision, not part of WS1.

Staging and production deployment pipelines are designed in WS1 but activated only after their credentials, ownership, rollback, and approval mechanisms are accepted.

### 13.4 Toolchain baseline

- **Node.js 20** remains the frontend baseline because it is already declared by the project and satisfies the installed Next.js 15 line.
- **Python 3.11** becomes the Functions development and deployment target. Firebase currently supports Python 3.10–3.13, and 3.11 provides a conservative supported upgrade from the current 3.10 configuration.
- The Python 3.11 transition is an isolated compatibility slice: recreate the environment, pin dependencies, run import/unit/emulator checks, then change the Firebase runtime only after those checks pass.
- Runtime versions and support status are verified against the official [Firebase Functions runtime documentation](https://firebase.google.com/docs/functions/get-started) and [Next.js installation requirements](https://nextjs.org/docs/15/pages/getting-started/installation) when the implementation plan is executed.

## 14. Compatibility and rollout strategy

The design uses incremental slices so each step can be reviewed and reverted independently:

1. **Characterization:** add matrix and entry-point tests without changing runtime behavior.
2. **Runtime policy:** introduce validated settings and fail-closed checks; migrate existing entry points atomically.
3. **Firebase consolidation:** establish canonical root configuration and emulator commands; test rules/indexes before removing duplicates.
4. **Provider selection:** route PayPal and other write-capable providers through explicit modes and fakes.
5. **Reproducible toolchain:** pin supported runtimes/dependencies and provide clean-machine commands.
6. **CI foundation:** enforce offline policy, tests, build, and secret scanning.
7. **Staging proof:** deploy and smoke-test staging with sandbox/controlled providers.
8. **Credential transition:** introduce ADC/WIF, verify it, then schedule separately approved key rotation/revocation.

API routes, payloads, Firestore data, and frontend-visible behavior remain unchanged throughout WS1 unless a safety behavior is explicitly approved as a contract change.

### 14.1 Authorization boundary inside WS1

WS1 is deliberately split into three authorization levels:

| Level | Included activity | Authority required |
|---|---|---|
| Core WS1 | Tests, validated configuration, mocks, canonical local Firebase files, reproducible toolchain, local emulator flow, and PR CI. | Approved design and implementation plan. |
| Staging-gated WS1 | Staging configuration inventory, deployment workflow activation, staging deploy, provider sandbox activation, and smoke tests. | Separate explicit staging authorization after non-secret resource inventory and rollback review. |
| Production-deferred | Production deploy, runtime proof, credential rotation/revocation, and any live-provider change. | Production gate; not authorized by WS1 design or plan approval. |

The code and pipeline definitions may be made production-ready during Core WS1, but they must not execute a production deployment. Production ADC/WIF is validated by configuration tests and least-privilege review until a separately authorized production release can provide runtime proof.

## 15. Failure and rollback behavior

| Failure | Required behavior |
|---|---|
| Invalid environment matrix | Process exits before Firebase/provider initialization with a redacted error. |
| Mock provider failure | Test fails deterministically; no live fallback. |
| Staging provider unavailable | Operation reports a classified dependency error; no production-account fallback. |
| Emulator unavailable | Local/integration command fails with the missing dependency identified; it never connects to cloud. |
| ADC/WIF deployment failure | Deployment stops; legacy credential remains temporarily available until a separately approved transition succeeds. |
| Canonical rules/index regression | Revert the isolated configuration commit and redeploy the last verified artifact to the same environment. |
| Production configuration mismatch | Deployment or startup fails before serving traffic; rollback uses the previous immutable artifact/configuration. |

## 16. Security properties

The design must make these properties testable:

- a non-production process cannot select a production Firebase project or bucket;
- a non-production process cannot select PayPal live mode;
- credentials do not determine environment identity;
- provider keys do not enable providers implicitly;
- local/test execution succeeds without cloud credentials;
- browser configuration contains no secrets;
- logs and errors reveal modes and missing fields but not secret values;
- staging and production identities have separate least-privilege access;
- production release authority is distinct from pull-request test authority.

## 17. Observability included in WS1

WS1 adds only the observability required to prove configuration safety:

- one structured startup configuration summary;
- classified configuration-validation failures;
- provider mode and fake/sandbox/live selection;
- environment and project identity in logs;
- CI evidence for matrix tests and emulator startup.

Endpoint timing, cost dashboards, cold-start metrics, and full dependency tracing remain in the later observability workstream.

## 18. Acceptance criteria

Core WS1 is ready for completion review when criteria 1–12 and 15–16 are demonstrated. Criteria 13–14 close the staging-gated portion after separate authorization. Production runtime proof and credential revocation remain outside WS1 and require the production gate.

1. Only `local`, `test`, `staging`, and `production` are accepted runtime environments.
2. Automated negative tests prove that local/test cannot resolve production Firebase resources or live providers.
3. Staging cannot select production Firebase, Storage, backend URLs, or PayPal live mode.
4. Production cannot start with emulator hosts, localhost URLs, or sandbox PayPal mode.
5. Default local and unit-test workflows make no external network calls and need no service-account JSON.
6. A clean machine can install pinned dependencies and start the documented emulator stack.
7. Functions discovery succeeds in the supported Python environment.
8. The emulator smoke suite covers Firestore, Auth, Storage, Functions, and required trigger infrastructure.
9. One canonical Firebase configuration, rules, and indexes set is used by documented commands.
10. The production frontend build rejects local overrides and secret-shaped public configuration.
11. Pull-request CI runs non-interactively and blocks on policy tests, offline unit tests, emulator smoke tests, secret scanning, and frontend verification.
12. A versioned, non-secret resource catalog identifies staging and production projects, buckets, origins, backend URLs, and provider account identifiers before a cloud workflow is enabled.
13. After separate staging authorization, staging deploy and smoke test use the staging project and sandbox/controlled providers only. Until then, the workflow remains disabled and Core WS1 reports staging verification as pending rather than passed.
14. Staging runtime authentication uses ADC after its gated deployment; CI has an approved WIF design or verified equivalent. Production ADC/WIF configuration is testable and reviewable, but runtime proof remains deferred to the production gate.
15. Existing service-account keys have an owner, usage finding, rotation plan, and revocation gate; no key material appears in artifacts.
16. No API contract, Firestore schema, production data, or user-facing workflow changes without a separately approved design update.

## 19. Explicitly deferred work

- Full contract-test coverage for all 128 exports.
- Payment provisioning idempotency and reconciliation.
- General backend layering and provider-port refactoring.
- Performance optimization and function tuning.
- Full observability and cost dashboards.
- Synthetic staging dataset and volumetric generator beyond the minimal emulator seed.
- Image/CDN architecture.
- Firebase-versus-hybrid-versus-Supabase spikes and ADR.
- Production credential revocation, deploy, or data cleanup.

## 20. Open decisions and default design calls

### Decisions that require an owner before their gated implementation slice

1. Confirm the non-secret resource catalog for staging and production: buckets, origins, backend URLs, provider account identifiers, sender identities, and production-only identifiers.
2. Identify the owner and access policy for Doppler, including audit access and GitHub Actions integration.
3. Identify which staging provider accounts, sender identities, domains, recipients, templates, and quotas are available before enabling them.
4. Identify the named operator who can execute staging changes, service-account inventory, credential rotation/revocation, and production deployment.

### Default calls that do not need to block Design approval

- The repository root is the canonical Firebase deploy root.
- `mcp-website-dev-39539` is the staging project and `mcp-website-2a1ad` is production; all existing staging data is preserved during WS1.
- Local and test use demo project IDs and all required emulators.
- Default local/test providers are fake or disabled.
- Networked sandbox tests are separate opt-in commands.
- Existing service-account files are not deleted until ADC/WIF has been verified and revocation is separately approved.
- GitHub Actions is the CI/CD platform, with deployment jobs disabled until their environment gates and identities are configured.
- Doppler is retained as the transitional secret-injection mechanism during WS1.
- Node.js 20 and Python 3.11 are the toolchain targets.
- Pull-request frontend builds use deterministic local fixtures; staging and production builds are protected, environment-specific workflows and fail on required data-fetch errors.
- The implementation plan may choose the task runner and internal settings-library details as long as the contracts in this design are met.

## 21. Builder check

An independent builder review was performed on 2026-10-25. Its material findings were incorporated by:

- separating Core WS1, staging-gated work, and production-deferred operations;
- making the staging/production project mapping and preservation policy explicit;
- requiring a non-secret environment-to-resource catalog;
- defining safe staging defaults for every provider;
- selecting GitHub Actions and retaining Doppler during WS1;
- defining frontend build-time data behavior;
- selecting Node.js 20 and Python 3.11;
- making operational ownership a prerequisite for gated activities.

## 22. Gate 2

The project owner approved this design on 2026-10-25. The decision authorizes creation of the detailed Core WS1 implementation plan. It does not authorize code changes, credential revocation, Firebase deployment, staging-data cleanup, or production operations.
