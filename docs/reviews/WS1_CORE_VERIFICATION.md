# Core WS1 — evidenze di verifica

Data: 25 ottobre 2026. Branch: `core-ws1-environment-safety`.
Base approvata: `719da2f198a4e0a6a2512552bdcd749fd1935612`.
Stato: Core WS1 implementato e verificato localmente; tre rilievi della revisione indipendente corretti. Pronto per la revisione del proprietario, senza integrazione o deploy.
Questo documento non autorizza merge, push, esecuzione remota della CI o deploy.

## Ambiente e comandi

Python 3.11.17 nel virtualenv root, Node 20.19.6, Firebase CLI 14.26.0,
Java 21; dipendenze Python installate dai lock con hash e frontend tramite
`npm ci`. Le verifiche applicative usano `demo-mcp-test`, provider fake o
Sender disabilitato, senza credenziali operative.

| Verifica | Esito osservato |
|---|---|
| `scripts/validate-firebase-config.py` | Configurazione canonica valida |
| `scripts/ci/assert-safe-environment.py` con profilo test/demo | Passato |
| `scripts/test-unit.sh` | **684 passati**, zero fallimenti; un warning WeasyPrint/HarfBuzz |
| `.venv/bin/python -m pip check` | Nessuna dipendenza incompatibile |
| `npm ci` con Node 20 | Exit 0 |
| `npm run test:config` dopo installazione pulita | **21 passati**, zero fallimenti |
| `npm run lint` | Exit 0, **0 errori / 53 warning** preesistenti |
| `npm run build` dopo installazione pulita | Exit 0, fixture backend locale e guardia rete attiva |
| `scripts/test-emulators.sh`, prima esecuzione finale | Exit 0; **2 test Python** + smoke client Firestore/Auth/Storage/Functions PASS |
| `scripts/test-emulators.sh`, ripetizione finale | Stesso esito, exit 0 e shutdown pulito |
| Scanner stdlib checkout, staged e diff base..HEAD | Zero segnalazioni |
| Link locali documentazione | Tutti risolti |
| `git diff --check` | Pulito |

Gli smoke test verificano anche il rifiuto di una scrittura Storage senza
privilegio admin; il relativo messaggio di diniego è atteso. I dati sintetici
sono eliminati con l'arresto degli emulatori. Le suite di integrazione verso
provider reali e il deploy di staging/produzione non sono stati eseguiti.

## Audit e limiti operativi

- Gitleaks sull'intera cronologia: exit 1 con **12 segnalazioni**, tutte classificate
  nel [rapporto separato](../operations/SECURITY_HISTORY_REMEDIATION.md).
  Lo storico non è dichiarato privo di segreti né riscritto. Una chiave privata
  è disabilitata per esposizione e l'altra è assente secondo IAM. Il proprietario
  conferma la cancellazione dei due token MailerLite e del progetto OAuth legacy.
- Le modifiche alle restrizioni della chiave pubblica Firebase sono **rinviate
  esplicitamente dal proprietario**. L'eventuale riuso di vecchie build distribuite
  resta da chiarire prima di attivare operazioni cloud.
- `npm audit`: **49 vulnerabilità** (4 critical, 29 high, 14 moderate, 2 low).
  La valutazione e gli aggiornamenti compatibili restano aperti prima di un
  rilascio cloud; nessun `audit fix --force` o upgrade maggiore automatico.
- I 53 warning lint non sono stati nascosti; le violazioni cosmetiche pregresse
  di `react/no-unescaped-entities` sono warning, mentre gli altri errori restano
  bloccanti. La copertura lint include JS, JSX, CJS e MJS.
- PR workflow preparato con permessi di lettura e azioni fissate a commit;
  **non pubblicato e non eseguito su GitHub**. L'esecuzione locale non prova
  ancora la compatibilità del runner Ubuntu ospitato.
- I template staging/production sono documentazione inattiva: job disabilitati,
  blocchi espliciti, nessun comando di deploy. ADC/WIF cloud, owner/resource
  inventory e protezioni degli ambienti richiedono i relativi gate.
- Il bridge di discovery usa un dettaglio interno della CLI Firebase bloccata
  alla versione installata; un upgrade richiede revisione e smoke test.
  Il bypass dotenv del build usa un flag interno della versione Next bloccata;
  un upgrade richiede la stessa rivalutazione.

## Aggiornamento seed locale — 2026-10-27

`scripts/dev-local.sh --seed` crea o ripristina `admin@test.it` con password
pubblica di prova `admin123` e claim `admin: true`, solo in `demo-mcp-local`
sull'emulatore Auth loopback. L'avvio attende Firestore e Auth prima del seed.
Review indipendente Sol high: una segnalazione Important sull'attesa di Auth,
corretta con regressione RED→GREEN. Suite rieseguite: 685 test backend e
24 frontend passati; lint mirato senza errori. Rimane il warning preesistente
WeasyPrint/HarfBuzz. Il proprietario conferma login e accesso alla dashboard;
questa prova browser è owner-reported. CI remota ancora non eseguita.

## Prima esecuzione GitHub Actions — 2026-10-27

La PR #1 ha avviato [Core WS1 checks, run 1](https://github.com/Vittorix99/mcp-website/actions/runs/40584476687).
Checkout fallito prima dei test: gitlink storico `.claude/worktrees/reverent-rubin`
senza una voce `.gitmodules`, presente anche nel branch base. Riproduzione locale:
`git submodule foreach --recursive true`, exit 128. Rimosso il solo gitlink
dall'indice, preservando la directory locale; `.claude` è già ignorata.
Lo stesso comando ora termina con exit 0. La suite CI resta da rieseguire
con il commit correttivo: i test remoti del primo tentativo non sono partiti.

## Revisione e gate

Revisione indipendente Sol high sul range `719da2f1..6f0be3ef`: nessun Critical o Minor, tre Important. Tutti corretti in `9ece2609`, con regressioni RED→GREEN e suite finale verde. Il [rapporto di review](WS1_CORE_REVIEW.md) mantiene il verdetto originale e le evidenze delle correzioni; nessuna seconda review è stata simulata o delegata. Staging: **pending authorization**. Produzione: **deferred**.

## Registro completo delle decisioni

Tutte le decisioni discrezionali e i costi se errate, nell’ordine registrato.
Nessun rilievo Minor da differire.

- Ruling: proceed from the documented non-green legacy global suite under the owner's instruction to continue — reproduce and account for baseline failures while building the deterministic offline suite — cost if wrong: a baseline regression could remain hidden until full-suite verification; completion is blocked until failures are resolved or explicitly dispositioned.

- Ruling: installed skill scripts lack executable bits, so invoke scripts via bash and use task-brief directly where task-start executes a non-executable helper — same brief/base semantics, no changes to installed skills — cost if wrong: bookkeeping could drift; record BASE explicitly for every task.

- Task 1: Ruling: add .eslintrc.json and pin Firebase CLI transitive cloud-sql-connector=1.10.0 and universal-analytics=0.5.3 — necessary to make the planned lint command non-interactive and CLI dependencies Node20-compatible — cost if wrong: pinned development tooling may need a later security update.

- Task 1: Ruling: use --allow-unsafe to hash/pin setuptools/pip required by the resolved tooling. The installed pip-tools 7.6.2 metadata helper requests https://pypi.org/numpy/json (verified 404), rather than /pypi/numpy/json (verified 200). Correct the metadata base URL in the one-shot compiler process only; keep pip-tools output and pip --require-hashes verification unchanged — avoids downloading every cross-platform wheel to compute already-published hashes — cost if wrong: metadata could be incomplete; actual hashed install must succeed before task completion. Installed skill/tool files remain untouched.

- Ruling: expand lint extensions (.js,.jsx,.cjs,.mjs); react/no-unescaped-entities is a warning because typography escaping is outside this safety workstream; all other Next preset errors remain blocking — cost if wrong: cosmetic JSX issues persist, explicitly reported as warnings rather than hidden.

- Ruling: use pinned Next15 __NEXT_PROCESSED_ENV to bypass implicit dotenv in sanitized builds; verify with actual build and inherited synthetic secret. Add preload network/fetch guard so swallowed external/required-fetch failures still fail the parent build — cost if wrong: future Next loader changes could reintroduce dotenv overrides; locked dependency and real build verification must cover this seam.

- Ruling: normalize only loopback http:// STORAGE_EMULATOR_HOST to internal host:port, then expose http:// to Python Storage SDK — CLI/SDK format mismatch — cost if wrong: Storage emulator routing fails; actual client smoke must pass.

- Ruling: pinned Firebase CLI14.26.0 runWithVirtualEnv drops parent custom env during discovery (installed source functionsEmulator.js:326–335). Add a version-checked, process-local bridge that forwards only the validated demo profile and removes CLI-injected Google credential variables. Leave app MCP_ENV/credential prohibitions intact — cost if wrong: a future CLI upgrade requires bridge review; version mismatch fails and Node tests exercise secret exclusion/cloud identity rejection. Installed dependency files are not edited.

- Ruling: overlap independent Task 2 tests with Task 1 dependency generation, keeping commits and evidence separate — avoids idle dependency-download time — cost if wrong: attribution may be confusing; stage only task-owned files.

- Ruling: replace source-text assertions in the plan's toolchain tests with behavioral bootstrap tests using controlled executable stubs and temporary projects; keep version/lock parsing as configuration-contract checks — avoids tautological tests — cost if wrong: stubs might miss real installer behavior; run actual installation and CLI checks as required.

- Ruling: owner explicitly defers Firebase API-key restriction changes; preserve current cloud configuration and record deferred hardening. Resume authorized local WS1 test/CI work: historical credential dispositions documented, Next historical manifests empty and local build uses fresh keys. Cost if wrong: undiscovered old deployed build/dependencies need validation before cloud activation; no claim of complete historical-risk elimination. No staging/production mutation authorized.

- Final: Ruling: Live provider identities and sandbox ownership — retain as staging-activation gate; Core verifies offline boundaries — cost if wrong: wrong ownership/account selection could break or misroute a later cloud activation.

- Final: Ruling: Historical private-key status — retain the successful read-only IAM evidence, without a second cloud query — cost if wrong: key state can change after inspection; revalidate before cloud operations.

- Final: Ruling: MailerLite tokens and legacy OAuth deletion — retain explicitly owner-reported deletions, not independent verification — cost if wrong: an incorrect owner report could leave legacy credentials in another account.

- Final: Ruling: Firebase public-key restrictions — honor explicit owner deferral and preserve the live configuration — cost if wrong: broader API allowlist and quota exposure remain until future hardening.

- Final: Ruling: Historical Next build-key deployment reuse — require verification before cloud activation; local build uses new key and old manifests have no actions — cost if wrong: an undiscovered deployed old build might still reuse historical encryption material.

- Final: Ruling: Existing wildcard CORS and non-atomic payment recovery — keep baseline behavior outside this configuration workstream; not declared fixed — cost if wrong: existing origin policy and partial-provisioning recovery risks remain for a later workstream.

- Final: Ruling: npm audit exploitability — record49 findings and require assessment before cloud release; do not infer exploitability from counts or force major upgrades — cost if wrong: potentially exploitable dependencies remain pending assessment and compatible upgrades.

- Final: Ruling: Remote CI/Linux/deployment execution — report local evidence only and keep cloud/remote integration gated — cost if wrong: Ubuntu or remote workflows may expose portability failures not observed on this Mac.
