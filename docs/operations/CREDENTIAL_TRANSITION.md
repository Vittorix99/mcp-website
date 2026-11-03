# Transizione credenziali — Core WS1

**Stato:** Core WS1 verificato localmente (684 test backend, 21 frontend); gate cloud e CI remota ancora da eseguire. Nessuna modifica credenziale, rotazione, revoca o deployment attivo è autorizzato da questo documento.

L'inventario del manifest è basato su riferimenti di file e codice tracciati. I nomi riportati non attestano che i file esistano nel checkout o che siano correnti. Per i due file storici segnalati dall'audit sono stati estratti soltanto metadati non segreti (tipo e progetto); nessun valore di credenziale viene riportato. Non sono stati aperti `.env` o JSON locali ignorati per questo inventario.

**Referente confermato:** Vittorio Di Giorgio, unico sviluppatore con accesso a tutti i servizi (conferma in chat del 25 ottobre 2026). Le indicazioni di owner da assegnare nelle righe del manifest sono quindi risolte a livello di referente; rimangono da verificare le associazioni alle singole identità e i loro utilizzi. Le due chiavi private storiche, distinte, risultano associate a `mcp-website-2a1ad`: vedere la [decisione di gestione](SECURITY_HISTORY_REMEDIATION.md). Nessuna revoca o rotazione è autorizzata dalla sola conferma del referente.

## Identità legacy indicate da riferimenti tracciati

Il manifest `scripts/doppler/secrets_manifest.conf` elenca i seguenti percorsi JSON come sorgenti per il secret `FIREBASE_SERVICE_ACCOUNT_JSON` o `GMAIL_SERVICE_ACCOUNT_JSON`:

| Percorso indicato nel manifest | Ambito/config manifest | Scopo osservato | Progetto associato | Sostituzione proposta | Responsabile / stato |
|---|---|---|---|---|---|
| `mcp-backend/functions/service_account_test.json` | backend / dev | Iniezione `FIREBASE_SERVICE_ACCOUNT_JSON`; l'uso concreto e il progetto non sono verificati | Non verificato | ADC per identità cloud gestita; GitHub Actions con WIF per CI | Referente: Vittorio Di Giorgio; **blocked before staging activation** |
| `mcp-backend/functions/service_account.json` | backend / prod | Iniezione `FIREBASE_SERVICE_ACCOUNT_JSON`; l'uso concreto e il progetto non sono verificati | Non verificato | ADC per identità cloud gestita; GitHub Actions con WIF per CI | Referente: Vittorio Di Giorgio; **blocked before staging activation** |
| `mcp-backend/functions/service_account_gmail_test.json` | backend / dev | Iniezione `GMAIL_SERVICE_ACCOUNT_JSON`; il codice d'uso e il progetto non sono verificati | Non verificato | ADC per runtime cloud solo se compatibile con l'uso confermato; WIF per CI | Referente: Vittorio Di Giorgio; **blocked before staging activation** |
| `mcp-backend/functions/service_account_gmail_prod.json` | backend / prod | Iniezione `GMAIL_SERVICE_ACCOUNT_JSON`; il codice d'uso e il progetto non sono verificati | Non verificato | ADC per runtime cloud solo se compatibile con l'uso confermato; WIF per CI | Referente: Vittorio Di Giorgio; **blocked before staging activation** |

`mcp-backend/functions/mock_data.py` contiene un riferimento storico a `credentials.Certificate("service_account.json")`; il commento lo descrive come percorso da sostituire, ma non prova progetto, identità o uso corrente. La configurazione Firebase runtime corrente, `mcp-backend/functions/config/firebase_config.py`, usa credenziali anonime per emulatori e Application Default Credentials (ADC) in cloud. `runtime_settings.py` rifiuta `GOOGLE_APPLICATION_CREDENTIALS` in local/test e rifiuta le variabili JSON di service account.

Il manifest Doppler nomina anche `.env.integration`, `.env`, `.env.development`, `.env.production` e `.env` frontend. Sono fonti/target dichiarati dal manifest; contenuti e appartenenza a progetti non sono verificati qui. Doppler resta il meccanismo transitorio durante WS1: non sono autorizzati rimozione, sostituzione, upload o download di segreti.

## Percorso di transizione e gate

**Verifica storica autorizzata del 25 ottobre 2026:** tramite la sessione utente
`gcloud`, una delle due chiavi esposte risulta disabilitata per esposizione e
l'altra assente dall'elenco chiavi del rispettivo account. Gli account risultano
non disabilitati; non sono state modificate chiavi o policy. L'esito riguarda
esclusivamente le due chiavi storiche identificate, non certifica lo stato dei
file nominati nel manifest Doppler né delle altre segnalazioni.

1. Prima di ogni rotazione, verificare con il responsabile designato l'esistenza e l'uso di ciascuna identità, il progetto associato, gli ambiti IAM, i carichi e le dipendenze; assegnare un owner accountable. Finché questi dati mancano: **blocked before staging activation**.
2. Verificare che local/test operino solo con emulatori senza credenziali cloud e che l'applicazione cloud supporti ADC. Per workflow GitHub Actions, predisporre WIF con ambiente protetto e permessi minimi, senza chiavi persistenti.
3. Validare l'identità sostitutiva, i permessi minimi, i log senza segreti e il rollback in un gate separato autorizzato. Nessuna prova staging o produzione fa parte del presente passaggio.
4. Solo dopo una transizione verificata e un'autorizzazione separata, il responsabile credenziali può pianificare rotazione/revoca; conservare evidenza dell'esito e confermare che non restino dipendenze. Non eliminare file né revocare credenziali come parte di Core WS1.

| Gate | Stato |
|---|---|
| Identificazione di account, progetto, utilizzo e owner accountable | **blocked before staging activation** |
| Inventario Doppler, accessi, audit e integrazione GitHub Actions | Da completare prima dell'abilitazione di workflow cloud |
| Verifica ADC runtime e WIF CI | Boundary ADC verificato offline; prova cloud ADC/WIF e permessi reali ancora necessaria |
| Rotazione e revoca | Due token MailerLite eliminati dal proprietario; ulteriori interventi richiedono decisioni separate |
| Deployment cloud | Nessun deployment attivo o autorizzato da Core WS1 |

## Fonti tracciate

- `scripts/doppler/secrets_manifest.conf` per i nomi dei percorsi JSON e i secret name associati.
- `mcp-backend/functions/mock_data.py` per il riferimento storico a `service_account.json`.
- `mcp-backend/functions/config/firebase_config.py` e `mcp-backend/functions/config/runtime_settings.py` per ADC, modalità emulatori e rifiuto delle credenziali locali.
- `docs/superpowers/plans/2026-10-25-core-ws1-environment-provider-safety.md`, vincoli globali e Task 12; `docs/superpowers/specs/2026-10-24-ws1-environment-provider-safety-design.md`, sezioni 7.3, 14 e 22.
