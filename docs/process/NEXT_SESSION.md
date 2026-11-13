# Passaggio di consegne — 9 novembre 2026

- Worktree: `/Users/vittoriodigiorgio/Desktop/Projects/MCP-WEB-PROJECT/.worktrees/core-ws2`.
- Branch `core-concurrency-api-scenarios`, base locale `a8e8702`
  (`chore/reduce-agent-overhead`). Modifiche non committate.
- PAY-12 / DIS-06 approvati: due nuovi test controllati, nessun codice
  applicativo modificato. Review Sol **medium** fino a nuova indicazione
  del proprietario; regola aggiornata in AGENTS.md.
- Unica review medium conclusa: corretti ID partecipanti vs membershipId
  e timeout executor; coordinatore accetta le correzioni. Deadline processo
  45s verificata offline con worker bloccati, exit 124.
- Offline: 66 API raccolti, 34 unitari collegati passati, scanner zero
  segnalazioni e whitespace pulito.
- Proprietario ha eseguito il runner emulatori e riportato exit 1. JUnit
  locale del 2026-11-09T21:43:48+01:00 ispezionato: **65 passati, 1 failure,
  zero error/skipped**. PAY-12 persiste due purchase per un ordine, con due
  richieste fake che restituiscono lo stesso capture ID. Duplicazione locale
  riprodotta; non prova di doppio addebito PayPal reale. Dettagli pytest
  abbreviati: duplicazione partecipanti/ricavi non quantificata.
- DIS-06 passa: un vincitore, contatore al limite; perdente già catturato
  senza purchase e retry senza nuova capture. Rischio post-incasso aperto.
- Bug riportato al proprietario prima di qualsiasi fix. Prossimo perimetro
  da approvare: claim atomico ordine/provisioning per PAY-12; recupero del
  perdente DIS-06 da discutere separatamente. Non mascherare la failure.
- Ultimo stato remoto noto: PR #9 e #10 aperte, #10 dipende da #9. Nessun
  nuovo controllo remoto, merge, push, deploy o operazione cloud/credenziali.
- Matrice/evidenze: `docs/superpowers/plans/2026-11-04-staging-synthetic-data.md`;
  dispatch: `docs/process/MODEL_USAGE_LOG.md`. Suite completa futura in CI,
  monitoraggio proprietario; nessuna CI del nuovo blocco dichiarata verde.

## Aggiornamento — PAY-12 corretto (2026-11-09, approvato dal proprietario)

- `OrderRepository.mark_captured` ora è un compare-and-set sull'`update_time`
  (nessun lock, nessun nuovo flag): chi trova `captured` già vero riceve
  `ConflictError` `ORDER_CAPTURE_CONFLICT`; interferenze non legate (es. stato)
  ritentate al massimo 3 volte, poi `ORDER_CAPTURE_RETRY`.
- Prima versione con transazione scartata: deadlock `Transaction lock timeout`
  (due 500 dopo 10 s) in ~1 corsa su 20 sull'emulatore.
- Prove: 749 unitari, 39 strumenti, PAY-12 60/60 in ciclo sull'emulatore e
  batteria sintetica 66/66 per 8 corse complete. Solo emulatore, non Firestore reale.
- Review Sol medium (sotto-agente, modello predefinito dell'host): nessun
  Critical; 2 Important e 2 Minor, tre corretti. Resta: la barriera di PAY-12
  sincronizza solo la lettura, quindi il ramo `FailedPrecondition` reale dipende
  dal timing (coperto dai test unitari e dalle corse ripetute).
- DIS-06 (perdente già catturato senza acquisto) resta aperto, fuori perimetro.


- OPS-02 completed2026-11-12:58 core handlers,352 new unit cases and42 API cases; malformed checkout body/cart values now fail400 before event lookup. Uses PreOrderDTO-normalized ID (alias/trim); DTO extra-ignore remains supported, valid totals stay44EUR. Scope is the explicit table, not all exported APIs/field combinations.
- Final OPS-02:1240 unit,44 scripts,329 API passed; API JUnit zero failure/error/skip, runner exit0/clean shutdown.2 Python smokes +client HTTP Functions/Auth/Firestore/Storage PASS. One Sol high review without findings, accepted. Modified source scanner0/diff clean; whole-tree scanner only flags two lines in old ignored member-auth-red.log. Evidence `.local/staging/ops02-*`.
- OPS-02 dispatches:1 Luna matrix batch (coordinator corrected test assumption on optional membership DTO; accepted),1 Sol high review. No deploy/cloud/provider/remoteCI proof. Preserve preexisting unstaged AGENTS/process edits. Next scope requires owner discussion: remaining permissions, Q04/05 statistics, Q06 calendar, Q07/08 consistency or other OPS scenarios.


- OPS-03/05 completed2026-11-12 (latest local commit): trigger recipient/send flags now use current document. Membership trigger_processed claim uses CAS with4 bounded rereads; ticket_delivery_started is sticky before mail, automatic replay suppressed after uncertain outcome; explicit admin resend remains available. Owner chose manual resend for uncertain outcomes. Legacy attempts without marker cannot be inferred; no migration/reset/deploy.
- Ticket/omaggio delivery writes target only metadata, preserve concurrent entered/price/membershipId/gender and don't recreate deleted participants. PDF-only generation preserves confirmed ticket_sent. Bulk omaggio counters/retry and explicit single resend verified with fake mail/docs; rendering failure keeps existing attachment-free fallback. Two concurrent ticket/member triggers send once in controlled emulator tests.
- Final OPS-03/05:1243 unit,348 API (19 new), API JUnit zero failure/error/skip, exit0/clean shutdown;2 Python smokes +client HTTP Functions/Auth/Firestore/Storage PASS. Source scanner0/diff clean.44 unchanged script tests reused from OPS-02. Evidence `.local/staging/ops03-*`, `ops03-05-*`, `ops05-luna.log`.
- Dispatches1 Luna test batch accepted after Sol's persistence fix;1 Sol high review found P2 unrelated-writer claim collision, reproduced with2 RED and fixed by coordinator; no second review. No actual PDF/Storage-volume QA, live providers, distributed retry guarantee, cloud or remoteCI proof. Avoid mixed workers at eventual rollout. OPS-04 real sending stays gated. Next scope must be discussed; preserve existing unstaged owner edits.


- OPS-06 completed2026-11-12 (latest local commit): wallet disabled/fake, Sender disabled and gender fake/disabled tested through registration handlers +real Firestore emulator. One actual RED fixed: hardcoded Andrea override now respects disabled gender (N/A/0.0); other modes and checkout rules unchanged.
- 10 new API cases verify no requests HTTP attempts, no mail for false flags, deterministic fake wallet/local URL, disabled wallet preserving member, and wallet/gender failures preserving membership/UID/participant/entered/price/membershipId. Auth provisioning excluded via prebound synthetic UID. PDF/render/upload stub only.14 new Sender unit cases use real disabled settings, no enabled-predicate bypass; explicit key/enabled=True cannot reach transport.
- Final OPS-06:1257 unit,358 API,14 focused Sender,2 Python smokes +client HTTP Functions/Auth/Firestore/Storage PASS; API JUnit zero failure/error/skip, exit0/clean shutdown, source scanner0/diff clean.44 unchanged script tests reused. Evidence `.local/staging/ops06-*`. One Luna batch accepted, one Sol high review without findings; no reviewer reruns.
- Order cleanup already exported/scheduled daily03:00 Europe/Rome, conservative >24h abandoned-only OPS-07 criteria unchanged. No cloud scheduler activation proof or deployment performed. No actual provider calls/cloud/config mutations/remoteCI proof. Next scope needs owner discussion; preserve preexisting unstaged AGENTS/process edits.


- OPS-08 completed2026-11-12 (latest local commit): scanner cleanup retains malformed/missing expires_at and deletes only datetime expiry strictly older than7 days; exact boundary/future retained, naive UTC convention unchanged. Per-document update_time conditional delete protects renewals/other changes after snapshot; skips FailedPrecondition/Aborted/NotFound without stale retries, counts only success. Entrance scan history remains unchanged. Orders/jobs/schedule untouched.
- Final OPS-08:1274 unit (17 new),364 API (6 new), API JUnit zero failure/error/skip, runner exit0/clean shutdown.2 Python smokes +client HTTP Functions/Auth/Firestore/Storage PASS; source scanner0/diff clean.44 unchanged script tests reused. Evidence `.local/staging/ops08-*`. Cases include expiry boundaries, malformed fields, real concurrent renewal/removal, idempotency and501 expired tokens with history preserved.
- Dispatches1 Luna test batch accepted after coordinator corrected is_active fixture and added missing-field case;1 Sol high review without findings. Conditional deletes use more RPCs than old batch; no production throughput/cloud scheduler proof. No cloud cleanup/deploy/provider/remoteCI proof. Next scope requires owner discussion (OPS-09 seed/recovery, OPS-10 app dataset, statistics/calendar/consistency); preserve preexisting unstaged owner edits.


- OPS-09 completed2026-11-12 (latest local commit): export now uses unique exclusive mode600 temporary files under private mode700 output, so stale producer temps cannot block retry; stale files are preserved, manifest still published last. Loader --apply errors keep type-only redaction/exit2 and now warn writes may be partial, directing retry of same export. Offline default unchanged. No import algorithm/guard changes.
- Six new script tests cover byte-repeatability, mixed export checksum rejection/recovery, stale temp names/permissions, partial-error redaction and offline no-load. Five real Firestore scenarios use120 members/12 events/1147 documents: repeated import, before-commit interruption400, lost second-commit acknowledgement800, readback interruption1147, resume exact data/pathset and closed clients, foreign-document prewrite rejection. AnonymousCredentials; no Functions.
- Final OPS-09:50 scripts,369 emulator scenarios, API JUnit zero failure/error/skip, exit0/clean shutdown, source scanner0/diff clean. Evidence `.local/staging/ops09-*`. Backend1274 and full smoke OPS-08 reused unchanged. One Luna batch accepted, one Sol high review without findings; no reviewer reruns.
- Controlled SDK exceptions are not real process-kill/network proof. Same-export replay rewrites expected synthetic documents; manual edits there are not merged. No cloud/provider/account/Storage/deploy/UI/remoteCI proof. Next bounded scope requires owner discussion, notably OPS-10 app on full dataset or remaining statistics/calendar/consistency. Preserve preexisting unstaged owner edits.


- OPS-10 API checkpoint (UI incomplete), 2026-11-12: worktree `.worktrees/core-ws2`, branch `core-concurrency-api-scenarios`; depends on65064cf. New full-corpus test:4000members/50events/7076purchases/21701participants/53684docs; exact IDs/years/counts/per-purchase event mappings, unchangedDB. Full370API suite passed before review tightening; focused updated case verification recorded in MODEL_USAGE_LOG. Auth simulated in API tests. One Luna medium test batch and one Sol high review; aggregate purchase mapping finding fixed by coordinator.
- UI partial proof: realNext/AuthEmulator with private read-onlyFlask harness (not Functions);2025members4000/valid2800,2026members3200/valid2800;40pages100 with4000uniqueemails sortedA-Z. Remaining UI search/status/reverse-sort/participant-pagination/event/purchasefilters OPEN after native browser control unavailable/interference. Local servers restarted at owner request:Next3000/harness5001/Firestore8080/Auth9099/Storage9199, demo-mcp-local. Admin publicfixture admin@test.it/admin123. Private scripts/data/results in ignored `.local/staging/ops10-*`; no real provider/mail/cloud/deploy. Preserve3preexistingunstagedownerfiles. Resume OPS-10 UI before declaring complete; test-mail recipient provided in chat for separately authorized OPS-04.

- OPS-10 birth-year update, 2026-11-13: owner requested users born1985–2008. Generator now samples those24 years uniformly; test enforces bounds/coverage and matching member/participant dates. RED then50 script tests PASS; updated full-corpus API case1PASS/369deselected in40.69s, exit0/JUnit clean. Reloaded own disposable local Firestore corpus:4000members/50events/7061purchases/21751participants/53749docs. Prior corpus counts/UI evidence remain historical; remaining participant and purchase UI checks continue on new corpus. No new dispatch (tiny inline edit), no live data/provider/mail/cloud changes.

- OPS-10 UI checkpoint, 2026-11-13: new-corpus event000 regular3854 across39 pages100 (last54), contiguous ranges/date order and visible-name multiset match; exact unique IDs proved by API, since regular table has no IDs/email. Female1932;female without member0. Omaggi146 across6 pages25 (last21),146uniqueemails/name multiset match. Purchases UI once showed7061/lordo346371€/fee10591.50€/net335779.50€; AX snapshot capped499rows. Later new local window stayed at0 counters despite200 API logs; cause unresolved amid noWindowsAvailable/native input failures. Remaining: stable purchase loading/search/event/status/date filters/sort; do not markOPS10 complete or call tool limit an app diagnosis. Servers left running as requested. No further dispatch or frontend edits; private evidence ops10-ui-results.json.
