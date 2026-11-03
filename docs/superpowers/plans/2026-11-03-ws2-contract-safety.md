# WS2 API Contract Safety Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Controllare tutti i riferimenti della mappa API frontend e provare
via HTTP il contratto di lettura eventi con autenticazione reale sugli emulatori.

**Architecture:** Analizzare la mappa JavaScript con Acorn già installato e
gli export Python con `ast`, senza importare Firebase. Estendere lo smoke
esistente riusandone evento, utenti, token e pulizia. Preservare i contratti
applicativi: le anomalie che richiedono decisioni di prodotto vengono documentate.

**Tech Stack:** Node.js 20, Python 3.11, Acorn, node:test, pytest,
Firebase CLI 14.26.0 ed emulatori già configurati.

**Spec:** [Design approvato](../specs/2026-11-03-ws2-contract-safety-proposal.md).

Stato: approvato dal proprietario in chat il 2026-11-03. Base: `d8ac90e8`.
Worktree `.worktrees/core-ws2`, branch `core-ws2-contract-safety`.
Metodo già scelto: esecuzione nativa; una review indipendente finale.

## Global Constraints

- Nessuna nuova dipendenza, provider, configurazione cloud o deploy.
- Nuove prove HTTP solo su `demo-mcp-test`, servizi loopback e provider fake/disabled.
- Nessun bypass di `verify_id_token` nei nuovi percorsi HTTP.
- Controllare tutta la mappa API; approfondire solo la lettura degli eventi.
- Eccezioni legacy esatte e motivate; vietato accettare genericamente endpoint mancanti.
- Nessun ripristino di signup, domande o foto senza decisione di prodotto.
- Preservare modifiche preesistenti ad AGENTS.md e ad altri worktree.
- Prove manuali iniziali e dashboard al proprietario, una attività alla volta.

## Review Focus

- Alias Python: contare il nome esportato, non soltanto quello della definizione.
- Endpoint solo definiti o callable: non considerarli funzioni HTTP esportate.
- Riferimenti JavaScript dinamici o non riconosciuti: errore esplicito, non omissione.
- Eccezione legacy riparata: richiederne la rimozione, evitando esclusioni permanenti.
- Token mancante, non-admin o non valido: nessun accesso ai dati admin.

## Task 1 — Inventario e controllo dell'intera mappa API

**Files:**
- Create `scripts/contracts/export_http_endpoints.py`.
- Create `mcp-website/scripts/check-api-contracts.mjs`.
- Create `mcp-website/tests/api-contracts.test.mjs`.
- Create `docs/reviews/WS2_API_REFERENCE_AUDIT.md`.
- Modify `mcp-website/package.json`.

**Interfaces:**
- Python `export_http_endpoints(root: Path) -> set[str]`; CLI `--root PATH`,
  stdout JSON ordinato, exit nonzero su input non leggibile/non interpretabile.
- Node `readFrontendRoutes(source: string) -> Map<string,string>`: chiave
  dotted (`admin.getAllEvents`), valore slug. Analisi AST dell'oggetto `endpoints`
  e delle chiamate `make("slug")`, incluse proprietà annidate.
- Node `checkApiContracts(routes: Map<string,string>, exports: Set<string>,
  legacy: Record<string,string>) -> {errors: string[], legacy: string[]}`.
- CLI Node senza argomenti: radice ricavata dal file, Python della `.venv`
  del worktree; inventario ottenuto senza import applicativi e senza rete.
- `npm run check:contracts`: exit 0 solo senza anomalie nuove; stampa anche
  le eccezioni note. Non dichiarare tutti i riferimenti validi se restano eccezioni.

- [x] **1.1 Ricostruire i quattro riferimenti noti**, ricercando chiavi e
  import dei servizi fino alle schermate; registrare file e linee nel rapporto.
  Se l'uso runtime non è dimostrato, scriverlo; assenza da una ricerca non
  dimostra raggiungibilità o assenza di uso dinamico.
- [x] **1.2 Scrivere e osservare fallire test comportamentali** usando piccoli
  repository temporanei. Casi: mappa annidata valida, nuovo slug mancante,
  alias `from api.example import original as exposed`, funzione non esportata,
  funzione callable e trigger non HTTP esclusi, sorgente malformata rifiutata,
  `make(variable)` rifiutato, eccezione scaduta e doppio slug rilevato senza
  perdere i percorsi frontend. Il test invoca realmente l'estrattore Python.
- [x] **1.3 Implementare gli estrattori e il confronto.** Seguire gli import
  `api.*` da `main.py`, verificando definizioni con decoratori HTTP noti:
  `public_endpoint`, `admin_endpoint`, `member_endpoint`, `https_fn.on_request`.
  Non includere funzioni solo definite, import di servizi o trigger.
- [x] **1.4 Dichiarare in `check-api-contracts.mjs` quattro eccezioni esatte**
  con motivazione e rimando al rapporto: `newsletter_participants`,
  `signup_request`, `get_all_questions`, `admin_upload_event_photo`.
  Confermarle sull'inventario corrente; qualsiasi quinto caso deve fallire.
  Le eccezioni non autorizzano cancellazioni o ricostruzioni funzionali.
- [x] **1.5 Collegare `api-contracts.test.mjs` a `test:config` e aggiungere
  `check:contracts`.** Verificare `npm run test:config && npm run check:contracts`.
  La mappa corrente deve riportare esplicitamente i quattro casi legacy.
- [x] **1.6 Commit mirato** del controllo, test e rapporto.

## Task 2 — Contratto HTTP degli eventi con token reali dell'emulatore

**Files:**
- Create `mcp-website/scripts/event-contract-smoke.mjs`.
- Create `mcp-website/tests/event-contract-smoke.test.mjs`.
- Modify `mcp-website/scripts/emulator-smoke.mjs`.
- Modify `mcp-website/tests/fixtures/emulator-seed.json`.
- Modify `mcp-website/package.json`.

**Interfaces:**
- `verifyEventReadContracts({base: string, eventId: string,
  adminToken: string, memberToken: string}) -> Promise<void>`: richieste HTTP
  e assert; non crea risorse o identità. Errori non devono riportare token.
- Lo smoke principale continua a possedere creazione e pulizia di evento,
  utenti Auth e risorse; chiama il verificatore dopo aver ottenuto entrambi
  i token. Non modificare i test legacy né i loro bypass per questo blocco.

**Contratti derivati dai controller e DTO attuali:**

| Richiesta | Risultato da provare |
|---|---|
| GET `get_all_events` | 200, array con evento seed; `id`, `title`, `price: 10`, `purchaseMode: "PUBLIC"`, `type: "PUBLIC"` |
| GET `get_all_events?view=card` | 200, evento con `id` e `title`; senza prezzo e metadati admin |
| GET `get_event_by_id?id=<seed>` | 200, oggetto pubblico con gli stessi valori |
| GET `get_event_by_id?id=<assente>` | 404, JSON `{"error":"Event not found"}` |
| GET `get_event_by_id` | 400, JSON con `error: "Invalid request data"` e array `details` |
| POST `get_all_events` | 405, JSON `{"error":"Invalid method"}` |
| GET `admin_get_all_events`, admin | 200, array contenente il seed |
| GET `admin_get_event_by_id?id=<seed>`, admin | 200, oggetto `{event: ...}` con `id` seed |
| Entrambi gli endpoint admin senza token, con token membro o invalido | 401; nessun payload dell'evento |

- [ ] **2.1 Scrivere test del verificatore con server HTTP loopback controllato.**
  Osservare RED. Casi: contratto atteso passa; dettaglio con envelope errato
  fallisce; errore 404 alterato fallisce; risposta admin 200 a membro fallisce;
  campo privato nella risposta pubblica fallisce; chiamata a host/progetto non
  demo rifiutata prima della rete. Testare comportamento, non testo sorgente.
- [ ] **2.2 Implementare il verificatore** con fetch/URL/assert standard;
  limitare base a `http://127.0.0.1:5001/demo-mcp-test/us-central1`.
  Nessuna richiesta invia un token a endpoint pubblici o a host esterni.
- [ ] **2.3 Arricchire il seed esistente con `createdBy` e `updatedBy` sintetici**
  per controllare che i DTO pubblici non espongano metadati admin presenti.
  Preservare titolo, data, prezzi e le altre aspettative WS1.
- [ ] **2.4 Integrare con utenti admin/membro già creati nello smoke.**
  Verificare assenza di `createdBy`, `updatedBy`, `participantsCount` nei
  payload pubblici; non imporre l'assenza di `createdAt`/`updatedAt`, previsti
  dal DTO corrente. Cercare il seed nell'array, senza assumerlo unico evento.
- [ ] **2.5 Eseguire test frontend e smoke reale sugli emulatori.** Il
  proprietario esegue `scripts/test-emulators.sh` quando guidato; nessun
  arresto automatico di emulatori già attivi né collisione con il suo dev.
  Un fallimento di permessi o risposta è un blocco da analizzare, non
  un motivo per allentare l'assert o cambiare il contratto silenziosamente.
- [ ] **2.6 Commit mirato** delle nuove prove, solo dopo esito verificato.

## Task 3 — CI e verifica finale

**Files:**
- Modify `.github/workflows/pr.yml`.
- Create `docs/reviews/WS2_CORE_VERIFICATION.md`.
- Modify `docs/process/GITHUB_ACTIONS_GUIDE.md`.
- Modify `docs/process/MODEL_USAGE_LOG.md` solo per deleghe effettive.

- [ ] **3.1 Inserire step `API reference contracts`** con
  `npm run check:contracts`, cartella `mcp-website`, dopo installazione
  e scansione. Lo step emulatori esistente include già il nuovo percorso:
  non duplicare l'avvio del Firebase CLI né aggiungere nuovi job/deploy.
- [ ] **3.2 Eseguire prove pertinenti:** test backend offline, test frontend,
  controllo contratti, lint, build controllata, validatore Firebase e scanner
  repository/diff. Riutilizzare il baseline WS1 solo per ciò che non cambia.
  Registrare comandi, exit code e warning; le prove del proprietario restano
  marcate come owner-reported.
- [ ] **3.3 Una review indipendente finale Sol high**, contesto fresco,
  limitata al diff e ai contratti; correggere i rilievi prima della consegna.
  Annunciare e registrare la delega; evitare review separate per ogni microtask.
- [ ] **3.4 Aggiornare documentazione, commit e consegnare la PR**, guidando
  il proprietario nel push e nella lettura dei risultati CI. Nessun merge
  automatico o attivazione staging/production.

## Arresto e rollback

Finito quando controllo globale e contratti eventi passano localmente e in CI,
con quattro anomalie legacy nominate e nessuna nuova anomalia ignorata.
Nessun claim di contratti completi per tutte le API o copertura browser generale.
Rollback: revert dei commit WS2; nessuna migrazione o credenziale da ripristinare.

## Autoverifica del piano

Coperti inventario globale, consumatori legacy, errori pubblici, permessi reali,
isolamento dei dati sintetici e CI esistente. Architettura senza dipendenze nuove.
Le funzionalità legacy mancanti richiedono decisione di prodotto separata;
documentarle non equivale a correggerle.
