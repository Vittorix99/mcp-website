# Release incrementale: disegno per approvazione

Stato: **approvato dall'owner il 22/11/2026 per le decisioni 1-3** (Fase 1, identità per componente, Fase 2 rimandata all'ADR).
Decisione 4 (25/11/2026): migrazione una tantum con credenziali operatore, come eccezione documentata.
Fase 1 implementata il 25/11/2026 (PR "per-component release identity"); non ancora eseguita su un ambiente reale.
Raffinamento rispetto al testo originale: l'identità del sito è l'impronta di `mcp-website` + `firebase.json` e non il
commit (che resta come provenienza), così un commit che non tocca il sito non lo ridepoya. Regole/indici Firestore
restano fuori dal flusso (non sono deployati da questi workflow).

Collocazione nel programma: questo lavoro è un **abilitatore**, non una nuova workstream. Serve a rendere staging un
ambiente affidabile e rilasciabile in modo ripetibile, da cui raccogliere le evidenze (WS3 osservabilità/costi, WS7 scenari,
benchmark) che alimentano l'ADR (Firebase ristrutturato / ibrido / Supabase) e il gate umano che precede lo Stage 3.
Il disegno è volutamente **neutro rispetto all'architettura**: identità per componente e passo `plan` valgono anche se l'ADR
cambia il backend; la Fase 2 dipende dall'ADR e resta fuori finché non c'è.
Contesto: primo staging HTTP+SSR verificato il 22/11/2026 (backend `b35a7d2`, sito `a4b5f75`).

## Problema

Il flusso attuale è "una release = un SHA per tutto":

- `release.py:97` scrive `MCP_RELEASE_SHA` e `MCP_CONFIG_DIGEST` nel `.env` di **tutte le 130 funzioni**.
  Il file `.env` fa parte del sorgente impacchettato, quindi ogni commit cambia ogni funzione.
- `release.py deploy` esegue sempre `backend` e poi `hosting`, e `verify_function_releases`
  pretende che **ogni** revisione abbia lo SHA della release.
- firebase-tools 14.26 salta le funzioni invariate solo se l'hash coincide
  (`release/planner.js:18-22`) **e** la funzione non è esplicitamente indicata da `--only`
  (`prepare.js:235`, `targetedByOnly`). Il tooling oggi passa i nomi di tutte le funzioni, quindi non salta nulla.
- Il bootstrap crea soltanto (vieta `updateFunction` e richiede un cloud vuoto): non è un flusso di rilascio.

Effetto: anche un cambio di una riga nel sito costa un redeploy di 130 funzioni (35-40 min, rischio quota),
e un cambio solo al tooling di deploy cambia comunque tutti gli stamp.

## Obiettivi

1. Un cambio al sito deploya **solo** SSR/Hosting (~10 min); un cambio al tooling o alla documentazione non deploya nulla.
2. Un cambio al backend aggiorna **sul posto** (mai cancellazione), con concorrenza limitata.
3. Si mantiene: deploy solo di commit su `main` con CI verde, verifica per componente, rollback, nessun segreto nei log.
4. Produzione usa lo stesso flusso di staging, con approvazione umana.

Fuori scopo adesso: spezzare il backend in più codebase. Dipende dall'ADR (WS4/WS5), vedi Fase 2.

## Disegno

### 1. Identità per componente, non per commit

| Componente | Identità | Cambia quando |
|---|---|---|
| Backend | `backend_tree` = hash git di `mcp-backend/functions` (`git rev-parse HEAD:mcp-backend/functions`) + `config_digest` | cambia il codice del backend o la sua configurazione pubblica |
| Sito (SSR + Hosting) | commit SHA + `config_digest` frontend | cambia `mcp-website/`, la config hosting o le variabili pubbliche |
| Regole e indici Firestore/Storage | hash dei file | cambiano i file |

- Il **backend smette di portare lo SHA**: i suoi stamp diventano `MCP_BACKEND_TREE` e `MCP_CONFIG_DIGEST`
  (digest calcolato solo sui valori di backend, senza SHA). Stesso codice e stessa config danno stesso sorgente e stesso hash.
- `deployment_health` riporta `backend_tree` e `config_digest`; `/api/deployment-health` riporta lo SHA del sito.
  "Quale commit è live" si legge dall'unione dei due, e dal manifest di release (punto 4).
- Lo SHA resta **solo come controllo prima del deploy**: il commit deve essere su `main` con CI verde e checkout pulito.

### 2. Rilevamento di cosa deployare

Un passo `plan` confronta lo stato live (health + Hosting) con HEAD e produce un piano con tre flag:
`backend`, `hosting`, `rules`. Se nessuno è attivo, la release termina senza toccare il cloud.
Cambi solo a `docs/`, test o tooling di CI non attivano nulla.

La verifica dopo il deploy è **per componente**: backend contro `backend_tree/config_digest`,
sito contro SHA/digest, e smoke tollerante all'ambiente vuoto (nessun episodio radio è valido).

### 3. Deploy del backend sul posto

- Percorso ordinario (`firebase.cjs`), con **lo stesso limite di concorrenza** del bootstrap
  (`limitDeployConcurrency` condiviso, oggi presente solo nel bootstrap).
- Snapshot e rollback restano per revisione Cloud Run, ma si applicano solo ai componenti toccati.
- `verify_function_releases` confronta con l'identità del backend, non con lo SHA.

### 4. Manifest di release

Ogni release produce `release-<env>.json` (artifact + GitHub Deployment): commit, identità dei componenti,
cosa è stato deployato e cosa è stato saltato. Serve a rispondere a "cosa gira in staging/produzione"
e come ancora del rollback.

### 5. Ruolo del bootstrap

Solo creazione di un ambiente nuovo. Documentato esplicitamente: **non si cancella mai per aggiornare**.

## Fasi

| Fase | Contenuto | Esito |
|---|---|---|
| 1 | Punti 1-5 sopra; sito indipendente dal backend; backend aggiornato sul posto con concorrenza 3 | Release del sito in ~10 min; release backend ~35-40 min ma senza cancellazioni |
| 2 | Deploy per singola funzione: o `--only` calcolato dai file cambiati, o codebase separate per dominio (public, member, admin, trigger/job). Da decidere **dopo l'ADR** WS4/WS5, perché dipende dalla struttura finale del backend | Release backend proporzionale al cambio |
| 3 | Rollback per componente; baseline di rollback mantenuta a ogni release | `ROLLBACK_BASELINE_VERIFIED` automatico |

La Fase 2 non va anticipata: il codice condiviso (`services/`, `repositories/`, `models/`) rende il rilevamento
per singola funzione non banale, e spezzare in codebase prima dell'ADR rischia lavoro buttato.

## Verifiche prima di fidarsi (esperimenti su staging)

- **E1 – salto delle invariate:** dopo la migrazione, rilanciare il deploy del backend a sorgente identico e
  controllare che firebase-tools stampi "Skipping the deploy of unchanged functions" e non scriva su Cloud Run.
  Fonti esterne segnalano un bug storico (v11.19) di hash di configurazione non deterministico; va verificato su 14.26.
- **E2 – effetto di `--only`:** verificare se il selettore per codebase marca le funzioni come `targetedByOnly`
  (e quindi mai saltate). Se sì, il piano usa nessun filtro funzioni o filtri per codebase.
- **E3 – quota:** misurare le scritture Cloud Run di un aggiornamento completo con concorrenza 3.

Se E1 fallisce, la Fase 1 resta valida (si evita comunque il redeploy per i cambi solo-sito) e la Fase 2 diventa prioritaria.

## Migrazione (una tantum)

1. Merge del tooling con i nuovi stamp.
2. Un primo rilascio che aggiorna le 130 funzioni di staging per togliere lo SHA dall'ambiente
   (e riallinea l'eccezione "SHA misti" di oggi). Richiede il percorso ordinario con credenziali OIDC/WIF,
   quindi dipende dalla prova OIDC reale (vedi sotto).
3. Esecuzione di E1-E3 su staging.
4. Solo dopo, abilitazione delle variabili `ENABLE_STAGING_DEPLOY` (mai prima delle prove, nessun flag per aggirarle).

## Prerequisiti ancora aperti (indipendenti da questo disegno)

- Prova reale OIDC/STS con l'Environment protetto.
- Decisione `PAYMENT_ROLLOUT_APPROVED` e baseline di rollback verificata.
- Caricamento dei dati sintetici su staging (approvazione esplicita dell'owner).
- Il percorso ordinario non è ancora mai stato eseguito su un ambiente reale.

## Decisioni richieste all'owner

1. Approvare la Fase 1 come prossimo lavoro (con una PR e una revisione finale).
2. Confermare l'identità per componente (`backend_tree` + digest) al posto dello SHA nelle funzioni.
3. Rimandare la Fase 2 (codebase per dominio o `--only`) all'esito dell'ADR.
4. Confermare che la migrazione richiede prima la prova OIDC, oppure autorizzare una migrazione con credenziali
   dell'operatore come eccezione una tantum documentata.

## Rischi

| Rischio | Mitigazione |
|---|---|
| firebase-tools non salta le invariate | E1/E2; la Fase 1 porta comunque il beneficio sito-indipendente |
| Aggiornamento sul posto fallisce a metà | Concorrenza 3, rollback per revisione già progettato, un solo deploy per volta (concurrency del workflow) |
| Deploy del sito con backend vecchio incompatibile | Il piano segnala se cambia un contratto API (`check:contracts`) e in quel caso richiede anche il backend |
| Lo stato live non è leggibile (health giù) | Il piano fallisce chiuso: nessun deploy senza identità attuale verificata |
