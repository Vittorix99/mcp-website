# Flusso di rilascio: staging → produzione

Stato: 25/11/2026. La Fase 1 del
[rilascio incrementale](../superpowers/specs/2026-11-22-incremental-release-design.md) è implementata nel codice
(identità per componente, passo `plan`, deploy solo dei componenti cambiati, manifest di release), ma **mai eseguita
su un ambiente reale**. Oggi i flag `ENABLE_STAGING_DEPLOY` e `ENABLE_PRODUCTION_DEPLOY` sono spenti: nessun deploy parte da solo.

## Schema

```
SVILUPPO
  branch ─► PR ─► CI "verify" ─► merge su main
                                      │
                                      ▼
                         push su main: "Release main"
                                      │
                                      ▼
                            CI "verify" (di nuovo)
                                      │
                                      ▼
╔═══════════════════════════ 1. STAGING ═══════════════════════════╗
║  (se ENABLE_STAGING_DEPLOY=true)                                 ║
║  a. Controllo sorgente e flag                                    ║
║  b. PLAN: cosa è cambiato? (backend / sito)                   ║
║  c. Login OIDC                                                   ║
║  d. Snapshot stato attuale (per rollback)                        ║
║  e. Deploy backend (solo se cambiato) + sito (solo se cambiato)║
║  f. Verifica: identità, segreti, health, smoke                   ║
║  g. Manifest di release                                       ║
╚══════════════════════════════════════════════════════════════════╝
                                      │
                       ┌──────────────┴──────────────┐
                       ▼                             ▼
                 staging OK                    staging FALLITO
                       │                             │
                       ▼                             ▼
            ⏸ APPROVAZIONE UMANA          STOP: produzione non parte
              (reviewer obbligatorio)       (rollback manuale se serve)
                       │
                       ▼
╔══════════════════════ 2. PRODUZIONE ═════════════════════════════╗
║  (se ENABLE_PRODUCTION_DEPLOY=true)                              ║
║  Stessi passi a-g di staging, con provider live                  ║
╚══════════════════════════════════════════════════════════════════╝

OPERAZIONI MANUALI (mai automatiche)
  • verify   → prova OIDC in sola lettura (solo staging)
  • rollback → ripristino dallo snapshot
```

## Identità per componente

| Componente | Identità | Cambia quando |
|---|---|---|
| Backend (130 funzioni) | impronta git di `mcp-backend/functions` + digest della configurazione pubblica del backend | cambia il codice o la configurazione del backend |
| Sito (SSR + Hosting) | impronta di `mcp-website` e `firebase.json` + digest della configurazione pubblica del sito | cambia il sito, la configurazione Hosting o le variabili pubbliche |

- Il commit **non** è scritto nelle funzioni del backend: un commit che non tocca il backend non cambia le sue 130 funzioni.
- Il sito riporta il commit solo come provenienza (`release_sha`), non come identità.
- `deployment_health` (backend) riporta `backend_tree` e `configuration_digest`;
  `/api/deployment-health` (sito) riporta `site_tree`, `configuration_digest` e `release_sha`.
- **Passo `plan`:** confronta le identità in produzione/staging con quelle del commit. Se lo stato live non è leggibile,
  la release si ferma (nessun deploy "alla cieca"). Solo documentazione, test o tooling: non si deploya nulla.
- **Manifest:** `release-<ambiente>.json` (commit, identità, cosa è stato deployato e cosa saltato), artifact per 90 giorni.

### Profilo di staging: HTTP e SSR esistenti

Staging mantiene il perimetro del bootstrap e della migrazione: 130 funzioni HTTP Python e una SSR;
gli 8 trigger e i 3 scheduler presenti nel sorgente non vengono distribuiti.
Lo snapshot confronta l'inventario live con la discovery SDK offline filtrata alle HTTP,
prima dei controlli individuali sulle revisioni. Funzioni mancanti o aggiuntive fermano il rilascio.
Il deploy backend ordinario OIDC usa gli stessi selettori HTTP del bootstrap, verificati con
firebase-tools 14.26.0 anche contro collisioni di prefisso. Il guard consente solo aggiornamenti
alle HTTP approvate e alla SSR esistente; rifiuta creazioni, cancellazioni, endpoint non HTTP,
scritture IAM dei segreti e modifiche alla retention. Non vengono abilitate nuove funzioni.
Produzione conserva la discovery completa e il selettore dell'intera codebase, con i propri gate.
Attivare trigger o scheduler su staging richiede una baseline controllata separatamente approvata.

### Limiti noti (dalla revisione indipendente)

- **Segreti ruotati:** le funzioni usano una versione numerica del segreto fissata al deploy e l'identità del backend
  la ignora. Il deploy controlla le revisioni attive e, se una usa una versione più vecchia dell'ultima, aggiorna il
  backend. Se firebase-tools salta comunque le funzioni invariate lo dirà l'esperimento E1 dopo la migrazione.
- **Baseline controllata** (cambio a trigger/decorator/`function_secrets.py`/`firebase.json`): deve ridepoyare **entrambi**
  i componenti, così il commit del sito (usato come riferimento di topologia) avanza; altrimenti i rilasci successivi si
  fermano in modo sicuro ma permanente.
- **Tooling di deploy** (versione di firebase-tools, `.python-version`, workflow, `scripts/deployment`): volutamente fuori
  dall'identità, perché una modifica solo al tooling non deve deployare niente. Un upgrade di firebase-tools richiede un
  rilascio forzato dei due componenti.
- **Hosting vs SSR:** il sito è verificato solo tramite l'endpoint SSR. Dopo un rollback fallito a metà
  ("intervento dell'owner") una versione Hosting non allineata non verrebbe rilevata dal `plan`.
- **Health endpoint pubblico (debito, decisione owner 2026-11-25):** `deployment_health` è raggiungibile senza token
  (come le altre funzioni HTTP; la protezione è nei decorator). Espone solo ambiente, progetto, impronta del codice e
  digest della configurazione, nessun segreto. Da rendere privato dopo la prima release: richiede IAM dedicato su quella
  funzione, adeguamento dei guard di deploy e token per `plan` e smoke.

## Migrazione una tantum di staging

Le 130 funzioni di staging portano ancora lo SHA e non riportano `backend_tree`: il `plan` le segna come cambiate e
lo `snapshot` si rifiuta (nessuna identità precedente leggibile). Serve **un solo aggiornamento sul posto** di backend e
sito con le credenziali personali dell'operatore (eccezione documentata, decisione 4 del 25/11/2026), poi il flusso
ordinario via OIDC.

- Strumento: `scripts/deployment/migrate_staging.py` (`prepare`, `apply`) + `firebase-migrate.cjs`.
- Protezioni: solo staging; commit pulito di `origin/main` approvato; operatore con OAuth personale verificato;
  `MIGRATION_APPROVED=true` (consenso distinto da quelli del bootstrap); l'inventario cloud deve coincidere
  esattamente con le 130 funzioni HTTP + 1 SSR create dal bootstrap.
- Può solo **aggiornare** le funzioni approvate: creare, cancellare, trigger e scheduler sono rifiutati dalle guardie;
  concorrenza 3. Fasi: backend, verifica di tutti gli stamp, sito, verifica con smoke.
- Prima del primo aggiornamento controlla anche identità di build/runtime delle funzioni e la retention del registro
  (nessuna policy che possa cancellare immagini, salvo dry run); non può scrivere IAM dei segreti.
- Va eseguita da un checkout pulito di `origin/main` con le proprie dipendenze installate (`npm ci`), non da un
  collegamento a un altro checkout.
- Esito pubblico in `.local/release/migration-result.json`. In caso di errore si ferma: nessun rollback né retry
  automatici. Non produce una baseline di rollback (`ROLLBACK_BASELINE_VERIFIED` resta falso).
- Poi: due rilasci ordinari via OIDC, un rollback provato, e solo allora il flag baseline.

Regole: staging sempre prima; produzione solo dopo staging riuscito e approvazione di una persona;
ogni ambiente ha il proprio snapshot di rollback.

## Rollback

**Snapshot (prima di ogni deploy, passo d).** Salva, per ogni servizio Cloud Run, le revisioni attive e le
percentuali di traffico; la versione di Hosting; le versioni dei segreti usate; l'elenco delle funzioni;
SHA e digest. Resta come artifact `rollback-<ambiente>` per 30 giorni.

**Rollback (avvio manuale con l'ID della run dello snapshot).**
1. Controlla che la run sia una release fidata di `main` di questo repository.
2. Controlla **tutti** i bersagli prima di cambiare qualcosa: servizi, funzioni, versioni dei segreti ancora attive.
3. Riporta il traffico Cloud Run alle revisioni salvate e Hosting alla versione salvata.
4. Verifica che il traffico coincida con lo snapshot ed esegue lo smoke sull'identità precedente.

**Limiti**
- I dati dell'applicazione non vengono ripristinati.
- Non ripristina filtri Eventarc, definizioni Scheduler, regole e indici Firestore: se cambiano, il rilascio
  automatico si rifiuta (serve una baseline controllata).

**Stato della prova: NON ancora provato su un ambiente reale.** Esistono solo test con simulazioni.
`ROLLBACK_BASELINE_VERIFIED=false` significa esattamente questo; diventa vero solo dopo un rollback reale su staging.

### Prima prova reale su staging

Per evitare il requisito circolare di una baseline già provata prima del primo rollback,
il consenso temporaneo `STAGING_RELEASE_PROOF_APPROVED=true` nell'Environment `staging`
consente le prove **solo con avvio manuale** (`workflow_dispatch`) e solo su staging.
Non certifica la baseline, non sostituisce `PAYMENT_ROLLOUT_APPROVED` e non disabilita
reviewer, vincolo `main`, CI, WIF, inventario, snapshot, controlli dei segreti o smoke.
Produzione richiede sempre `ROLLBACK_BASELINE_VERIFIED=true` nel proprio Environment.
Il consenso temporaneo e `ENABLE_STAGING_DEPLOY` richiedono autorizzazione dell'owner;
`ENABLE_PRODUCTION_DEPLOY` resta disabilitato durante queste prove.

Sequenza del blocco approvato il 26/11/2026:
Il dataset ridotto è già caricato: il loader entra nella PR come strumento della precedente
importazione una tantum, senza rieseguirlo durante queste prove. Non controlla la topologia cloud:
un futuro riuso richiede nuova verifica dell'assenza di trigger/scheduler e nuova approvazione;
i flag di consegna disabilitati nei dati non escludono ogni effetto dei trigger.

1. Merge del loader sintetico, correzione del gate e commento nel sorgente sito:
   il backend deve avere la stessa identità della migrazione, il sito deve cambiare.
2. Con CI verde, avvio manuale `deploy`, approvazione Environment `staging`:
   piano solo sito, snapshot conservato, manifest con backend escluso, smoke riuscito.
3. Secondo merge con sola modifica minima al backend, poi rilascio manuale:
   piano solo backend, sito escluso, snapshot e smoke riusciti; raccogliere evidenze E3.
4. Avvio manuale `rollback`, ambiente `staging`, ID della run del secondo rilascio:
   ripristinare lo stato precedente al secondo rilascio e verificare traffico, Hosting e identità.
5. Solo dopo esito verificato, owner imposta la baseline a `true` e rimuove il consenso temporaneo.

I due merge sono necessari per avere due stati successivi di `main` con componenti differenti.
E1/E2 richiedono una prova dedicata approvata: un rilascio senza cambi viene escluso dal
`plan` e non esercita il salto delle funzioni invariate dentro firebase-tools.

**Tentativo iniziale del 26/11/2026:** PR #28 unita in `134bb5c`; run `45780635762`
con CI riuscita e piano solo sito. Snapshot fermato dal confronto errato fra le 141 funzioni
del sorgente e le 130 HTTP previste su staging. Upload snapshot, deploy e produzione saltati;
health live ancora sulla migrazione `817af53`. Rimossi entrambi i flag temporanei
(`ENABLE_STAGING_DEPLOY`, `STAGING_RELEASE_PROOF_APPROVED`); baseline ancora falsa.
La correzione del profilo deve superare test, review e CI prima del nuovo tentativo.
