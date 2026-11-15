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

- OPS-10 COMPLETE,2026-11-13: owner replied “tutto passa” to local purchases block:reset7061;exact member00000=17/gross997€;absent search0;event000=1700/gross58344€;invalid0;2026datewindow4878;first dates desc12/11/2026/asc29/10/2025. Owner-reported UI evidence, not independently reproduced. Together with recorded agent UI pagination/filter proofs and exact-ID API proof, closes scopedOPS10; earlier partial checkpoints are historical. Post-agent UI check:53749datasetdocs+2testsettings unchanged. Existing50script tests and new-corpus full API case1PASS reused;370suite refers to previous corpus. Sol high review already accepted/fixed; no further dispatch/frontend change. Preserve3preexistingunstagedownerdocs. Worktree .worktrees/core-ws2,branch core-concurrency-api-scenarios,prior commits26ee2e7/f3bbe90/f57ccfb. Next scope: reconcile branch dependencies before push/PR; no push/merge/deploy performed.

- Integration checkpoint,2026-11-13: branch core-concurrency-api-scenarios,worktree .worktrees/core-ws2. Merged published discount history61dc187 (PR#9 head8bcccb7,includes#10) and backend documentation1a11ad5 (0c5457f). Only conflict was add/add MODEL_USAGE_LOG: retained extended history after verifying every original dispatch row. Application tree identical to OPS10 checkpoint36a5561. Main2a4fb1d and all these dependencies are ancestors; no rebase/force-push/deletion. Three preexisting owner edits backed up privately, temporarily stashed, restored and patch-hash verified unchanged; excluded from publication.
- Final integration checks:1274 backend units,50 tooling,42 frontend policy,370 API in91.78s,57 real-token Auth in1.11s PASS; both emulator runners exit0/clean shutdown and JUnit zero errors/failures/skips. API references126/exports129/errors0; Firebase config valid; secret scan0/diff clean. Logs .local/staging/reconcile-*.log. Existing per-block Sol reviews retained; no extra dispatch for history/document reconciliation. Full build/lint/HTTP emulator smoke remain CI gates; pending CI is not passed.
- Integration PR targets main and depends on draft#9:merge#9 first, then the hardening PR after review/CI. Owner monitors final CI result. No merge/deploy/cloud/provider operation performed. OPS10 closed; birth years1985–2008; current corpus4000members/50events/7061purchases/21751participants. Unknown payment/mail outcomes and legacy unreserved orders require manual handling; rollout must avoid mixed workers. Remaining statistics/calendar stories and authorized real-mail OPS04 are separate.

## Attività da fare — piano approvato il 13 novembre 2026

Segreti e deploy automatici: **approvato, da implementare**. Il proprietario
ha chiesto di inserirlo in lista, non di avviare ora l'implementazione.
Piano: [CREDENTIAL_TRANSITION.md](../operations/CREDENTIAL_TRANSITION.md#piano-operativo-segreti-e-deploy-automatici--2026-11-13).
Branch di preparazione `ci/staging-deployment`, base `0b85eb7`, piano `67962f7`;
dipendenza d'integrazione #9 → #11. Non richiedere di nuovo l'approvazione del
medesimo piano; accessi cloud e rilasci mantengono i gate concreti previsti.

- [ ] Inventario variabili/segreti e separazione staging/produzione; transizione dagli env verificata.
- [ ] Binding Secret Manager e inizializzazione runtime dei provider compatibile con discovery Firebase.
- [ ] Identità temporanee WIF, Environment GitHub e deploy staging automatico dopo i controlli su main.
- [ ] Test post-deploy e E2E staging con dati sintetici e provider controllati.
- [ ] Produzione con approvazione manuale, rollout compatibile e rollback verificato.
- [ ] Review finale Sol high e verifiche del blocco prima dell'attivazione.


## Checkpoint corrente — segreti/deploy, 13 novembre 2026

Worktree `.worktrees/core-ws2`, branch `ci/staging-deployment`; base0b85eb7
(PR#11, dipendenza #9), piano67962f7/6f48eb4. Richiesta owner ha ripreso
lo sviluppo: il precedente stato «solo backlog» è storico.

Preparazione repository: SecretParam per funzione, policy/discovery senza
chiavi provider, validazione runtime mirata, provider lazy, identità runtime
esplicita, health SHA/digest backend/frontend. Pipeline main richiama CI PR,
poi staging e produzione protetta; flag repository deploy assenti/defaultskip.
Build frontend separata per ambiente. Snapshot/rollback usa revisioni Python
e SSR, versione Hosting e riferimenti secret numerici delle revisioni attive.
Topologia diversa o prima baseline legacy richiede bootstrap controllato.

Evidenze:1297 unitari,87 strumenti,48 frontend,lint/build fixture PASS;
API370/Auth57 emulatori precedenti validi per fake invariati; smoke completo
2Python+clientHTTP PASS su porte dedicate (copie temporanee con sole porte
sostituite, eliminate). Actionlint1.7.12/Firebase/contratti130export/scanner0
e diff check passati. Review unica Sol high:4 rilievi accettati/corretti,
regressioni passate;1 Luna inventario e1 Sol high dispatch, costi non disponibili.

Nessuna CI del nuovo ramo attestata, nessun deploy/provider reale o mutazione
IAM/API/credenziali. Prossimo gate: inventario risorse/identità build e piano
IAM concreto; poi autorizzazione cloud separata, bootstrap staging, E2E sandbox
e prova rollback. Produzione e Sender restano spenti. Non riapprovare il piano
già approvato, non confondere preparazione con attivazione. Dettagli e limiti:
`docs/operations/CREDENTIAL_TRANSITION.md`. Preservare i3 owner diff in AGENTS,
MODEL_USAGE_LOG e NEXT_SESSION; pubblicare solo i nuovi append propri.


## Aggiornamento owner — integrazione sospesa e proposta Q-04

Il13 novembre l'owner ha unito PR#9 in main8cfc8c68. Ha poi chiarito che
la restante ristrutturazione va integrata alla fine: PR#11 nuovamente draft,
aperta, auto-merge assente. Non eseguire altri merge main. Protezione main
attiva/verificata: PR,verify GitHub Actions15368,strict/admins,conversazioni
risolte; force/deletion vietati; reviewer aggiuntivi0. Nessun deploy attivato.

Proposta prossimo blocco Q-04: criteri degli incassi online nei tre servizi
statistici. Riproduzione offline conferma generale include COMPLETED/DECLINED
mentre evento/snapshot escludono; tutti includono PENDING e stati vuoti.
Richiesta preferenza owner: entrambi COMPLETED oppure compatibilità con
COMPLETED legacy senza capture_status. Domanda in attesa: non modificare
formule prima della risposta. Perimetro proposto aggiunto al piano sintetico
esistente; niente dati/provider reali o nuove chiamate cloud. Nessun dispatch.
Il piano staging/WIF andrà riallineato al nuovo ordine d'integrazione prima
dell'attivazione. Preservare sempre i3 owner diff già presenti.


## Checkpoint Q-04 — criterio online implementato,13 novembre2026

Branch `core-stats-payment-eligibility`, worktree `.worktrees/core-ws2`,
base39e5f3e (include preparazione deploy57c2cc3 e cronologia PR#11). Owner
ha scelto «primo criterio»: entrambi status/capture_status COMPLETED. Regola
condivisa nei3 servizi statistiche; vincoli tipo/ref/count restano evento,
tessere standalone incluse nel generale. Stato null reso vuoto solo in
risposta per evitare500 su ultimo acquisto; sorgente immutata. Generatore
usa general_purchases=-1 nei casi invalidi; baseline dati invariata.

Finali1337 unitari (+40),87 strumenti,384API (+14) in93.08s PASS;JUnit
0failure/error/skip e runnerexit0/shutdownpulito. API handler+Firestore
emulato,auth simulata.26RED prima della regola,1RED generatore e1RED mapper.
Review unica Sol high senza P1/P2 accettata; caso mapper emerso dopo corretto
con regressione e suite ripetute. Scanner0,Firebase/contratti130export/diff
puliti. Log privati stats-q04-*. Nessun dispatch Luna;1 Sol high, costi ignoti.

Solo primo blocco Q-04 chiuso: metriche manuali/omaggi ancora da definire.
Snapshot salvati richiedono rebuild dopo futuro rollout; nessun rebuildcloud,
migrazione,provider reale,CI remota o push. PR#11 rimane draft senza
automerge; niente altri merge main fino a fine ristrutturazione. Q-05 ingressi,
Q-06 età,Q-07 riferimenti,Q-08 duplicati e gate cloud restano aperti.
Preservare3owner diff in AGENTS,MODEL_USAGE_LOG,NEXT_SESSION.


## Q-04 — ricevuti manuali e totali separati, 13 novembre 2026

Branch `core-stats-manual-receipts`, base d5a10c9, worktree `.worktrees/core-ws2`.
Owner: manuale a prezzo positivo significa pagamento ricevuto fuori dal sito.
Metodi: cash/iban/private_paypal; importo finito, positivo, in centesimi;
purchase_id solo None/vuoto. Qualunque riferimento impedisce il fallback
manuale anche se orfano. Website orfano e metodi ignoti esclusi; omaggi a zero.
Nuovi campi manuali e totale lordo nei tre servizi e negli snapshot. Netto e
fee online separati. Generale comprende tessere; dashboard solo eventi.
Totale prossimo evento da acquisti confermati e manuali, senza sommare di
nuovo i prezzi dei partecipanti website.

UI con etichette separate e «Da ricalcolare» per snapshot senza nuovi campi.
KPI/filtro acquisti confermati richiede entrambi gli stati COMPLETED. Il
decoder EventParticipant riconosce maiuscole/spazi dei metodi noti su copia
del payload. Varianti riprodotte con fixture, presenza reale non verificata.

Finali:1372 unitari,87 strumenti,50 frontend,lint/build fixture PASS;392 API
in99.74s,JUnit senza failure/error/skip,runner exit0 e shutdown pulito.
1 Luna medium per6 file UI accettata;1 Sol high con1 P2 corretto:4RED poi
6 casi modello e4 API aggiuntivi verdi;29RED iniziali. Nessuna seconda review.
Firebase/contratti130export/scanner0/diff puliti. Log privati manual-receipts-*.
Browser, carico, cloud, provider e CI remota non verificati.

PR#11 resta draft senza auto-merge. Nessun merge main fino alla fine della
ristrutturazione. Snapshot cloud da ricostruire al futuro rollout autorizzato.
Q05 ingressi,Q06 calendario,Q07 coerenza,Q08 duplicati e gate cloud aperti.
Preservare i3 owner diff: AGENTS,MODEL_USAGE_LOG,NEXT_SESSION.


## Aggiornamento Q-04: solo metodi canonici

Owner ha chiesto di evitare compatibilità legacy. Rimosso l'override
EventParticipant.from_firestore e strip/lower nei manuali: solo valori
PaymentMethod canonici; nessun adapter per CASH/spazi. Il decoder generico
preesistente resta invariato: formati non riconosciuti non entrano nei
manuali e possono perdere la classificazione omaggio. Verificare conformità
dei dati prima del rilascio; eventuale bonifica separata, non automatica.
Nessuna presenza reale delle varianti verificata e nessun dato reale toccato.
8RED poi1381unitari/392API in99.67s PASS,JUnit0failure/error/skip,runnerexit0
e shutdown pulito;scanner0/diff pulito. Nessun nuovo dispatch per questo
follow-up circoscritto. PR#11 draft, main congelato, nessun push/deploy.


## Q-06 checkpoint locale e scelte Q-07/Q-08 — 15 novembre 2026

Branch `core-age-data-integrity`, base c647ea9, worktree `.worktrees/core-ws2`.
Q-06: helper calendar_age comune a controlli ammissione e analytics diretto/
snapshot. Età compiuta oggi Europe/Rome,18/21 inclusivi,29febbraio dal1marzo
negli anni non bisestili come nelle statistiche preesistenti. Parser/formati
e limite120anni analytics preservati; invalidi/futuri non passano ammissione.
4RED prima del fix;1399 unitari e399API in100.29s PASS,JUnit senza
failure/error/skip,runnerexit0/shutdownpulito,scanner0/diff pulito. Nessun
provider reale,cloud o merge. Review finale dell'intero blocco ancora aperta.

Domande owner pendenti, non dedurre risposta dal tempo trascorso:
Q-07 bloccare eliminazioni con storico economico/ingressi (proposto), oppure
aggiungere archiviazione. Q-08 mantenere iscrizioni multiple con un ingresso
per socio/evento (proposto), vietare duplicati, oppure nuovi QR per iscrizione.
Codice attuale elimina solo record principali e merge non riallinea scan/
purchase.membership_ids. Nessuna modifica Q-07/Q-08 finché regole indefinite.

Luna q06_age_inventory fallita per limite utilizzo:nessun file o risultato
accettato, inventario svolto da Sol.1 dispatch fallito,0 review delegate;
costi non disponibili. PR#11 draft/noautomerge; main resta congelato.
Preservare3owner diff in AGENTS,MODEL_USAGE_LOG,NEXT_SESSION.


## Checkpoint Q-06 e cancellazioni Q-07 / ingressi Q-08 — 15 novembre 2026

Worktree `.worktrees/core-ws2`, branch `core-age-data-integrity`, base c647ea9.
Q-06 già staged ripresa senza alterazioni funzionali: anni compiuti a Roma.
Q-08 approvata: iscrizioni multiple, unico ingresso socio/evento; QR, manuale,
undo e retry sincronizzano tutti i flag e timestamp dalla stessa fonte scan.
I conteggi distinguono righe iscritte e scan unici. Le sovrapposizioni con
undo/delete non ripristinano flag obsoleti o scan orfani.

Q-07: owner approva blocco delete con storico e cascata dei soli gratuiti.
Conservati anche acquisti rimborsati, link orfani, importi nonzero/invalidi,
ordini e prenotazioni incerte. Free delete atomico: iscrizioni, link soci
(attended_events solo dopo ultima iscrizione), token, luogo, guida, snapshot
e contenitori locali. Oltre400scritture:409 senza cancellazioni parziali.
Creazione iscrizione/link socio atomica; scan/token ricontrollano esistenza.
Rebuild concorrenti producono solo tombstone esclusi dall'indice per eventi
cancellati; il contratto exists:false resta disponibile dopo i trigger.

Finali:1399 unitari e449 API in108.89s PASS; JUnit0 failure/error/skip,
runnerexit0 e shutdown emulatore pulito. Scanner0, Firebase valido,130export,
diff pulito. Una review Sol high:2P2 corretti con4RED poiGREEN e suite
ripetute; nessuna seconda review.0 Luna in questa ripresa; costi ignoti.
Log privati q06-q08-*-reviewed.log e q07-review-{red,green}.log.

Q-07 riassegnazione socio/merge e riferimenti scan/purchase.membership_ids
restano aperti, fuori dalle scelte delete di questa ripresa. Q-05 e gate cloud
restano aperti. PR#11 draft, nessun push/merge/deploy o dato reale modificato.
CI remota, provider reali e browser non verificati. Preservati i tre diff owner
in AGENTS.md, MODEL_USAGE_LOG.md e NEXT_SESSION.md; nell'indice solo append agente.


## Q-08 nominativa: decisione superata e nuova regola — 15 novembre 2026

Worktree `.worktrees/core-ws2`, branch `core-age-data-integrity`, base7a5fd0d.
Owner revoca la precedente scelta delle iscrizioni multiple: per gli eventi
associativi una sola iscrizione per socio/evento. Rimosso Consenti duplicati
da UI, DTO, modello, mapper e generatore; il vecchio flag nei documenti
non può aggirare il controllo. Le richieste API con il campo rimosso sono
rifiutate. Nessuna bonifica dei duplicati storici: scanner/undo conservano
la difesa precedente dell'ingresso unico.

Vincolo su socio e contatti anche per admin, modifica/assegnazione tessera
e riallineamento riferimenti. Hold capienza con hash identità e fence evento
impediscono checkout/admin concorrenti duplicati prima delle chiamate
provider. Identità dei soci scaduti inclusa senza cambiare criteri rinnovo.
Capture ricontrolla identità correnti; hold vecchie non verificabili richiedono
nuovo checkout o gestione manuale. Recovery dello stesso ordine idempotente;
merge con collisioni note rifiutato prima di cambiare altri riferimenti.
Q-07 riallineamento generale scan/purchase e storico soci resta aperto.

Finali1399unitari,466API in109.36s,87strumenti,50frontend PASS. JUnit0
failure/error/skip,runnerexit0/shutdown pulito;lint0errori/53warning esistenti,
scanner0,Firebase valido,130export,diff puliti. Review unica Sol high:1P1
corretto con2RED poi19GREEN e suite ripetute; nessuna seconda review.
Log locali q08-unique-*.0Luna/1Sol high; costi non disponibili.

Futuro concordato:eventi non associativi senza tessera e integrazioni
Eventbrite/Xceed dopo ristrutturazione backend e frontend. Nessuna modalità
o integrazione futura implementata adesso. Nessun push,merge,deploy,dato
reale o gate cloud eseguito. PR#11 draft; tre diff owner preservati.
Browser,CI remota e provider reali non verificati.


## Q-07 integrità soci e partecipanti — 15 novembre 2026

Worktree `.worktrees/core-ws2`, branch `core-age-data-integrity`, base eae983d.
Owner approva e richiede implementazione/verifica: partecipante collegato
non può cambiare identità, socio o scollegarsi; correggere dal socio con
cascata alle iscrizioni. Manuali senza membership ammessi e modificabili,
anche agli eventi associativi; email facoltativa. Collegamento esplicito
successivo definitivo; ingressi già presenti richiedono verifica manuale.
Create manuale con socio esistente, nuovo socio contestuale o senza socio;
rinnovo contestuale e riferimenti nella stessa batch, nessun orfano al retry.

Merge atomico sul target scelto: partecipanti, scan, purchase.membership_ids,
coupon vincolati al socio e storico; sorgente rimossa solo al consolidamento.
Operatore e snapshot originali nel registro membership_operations. Pagante,
importi, transazioni e timestamp ingresso preservati. Collisioni di evento,
scan legacy inconsistenti, account source con UID diverso, checkout aperti
e oltre400scritture bloccano senza parziali. Delete socio referenziato bloccato
prima di provider/storage. Contatti canonici controllati prima di PayPal;
fence tecnici separati lasciano immutate le schede socio prima dell'incasso.

Finali1399unitari e503API in115.45s PASS;37scenari Q-07. JUnit0failure/error/
skip,runnerexit0/shutdown pulito.87strumenti/50frontend PASS;build fixture
Node20 PASS;contratti126riferimenti/130export/0errori;lint0errori/53warning
esistenti. Review unica Sol high:7rilievi accettati e corretti con regressioni
RED/GREEN;nessuna seconda review.1task Luna+1follow-up UI accettati;
1review Sol high;token/costi non disponibili. Log privati q07-*.

PR#11 draft;nessun push/merge/deploy/dato reale o bonifica autorizzato.
Provider reali,CI remota e browser non verificati. Eventi non associativi
senza tessera e integrazioni Eventbrite/Xceed restano rinviati. Prossimo
blocco da discutere con owner;non avviare automaticamente altro workstream.
Preservare i tre diff proprietario in AGENTS.md,MODEL_USAGE_LOG.md e
NEXT_SESSION.md;staging dei documenti condivisi limitato alle append agente.

Auth finale:57 scenari con token reali degli emulatori PASS, JUnit0failure/error/skip.
