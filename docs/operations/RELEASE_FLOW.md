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

## Migrazione una tantum di staging (da fare)

Le 130 funzioni di staging portano ancora lo SHA e non riportano `backend_tree`: il `plan` le segna come cambiate e
lo `snapshot` si rifiuta (nessuna identità precedente leggibile). Serve **un solo aggiornamento sul posto** di backend e
sito con le credenziali dell'operatore (eccezione documentata, decisione 4), poi il flusso ordinario via OIDC.

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
