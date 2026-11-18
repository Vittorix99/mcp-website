# Catalogo ambienti e risorse — Core WS1

**Stato aggiornato al 2026-11-13:** CI della PR #11 passata (offline/emulatori/build fixture). Il ramo prepara binding e workflow release disabilitati per default; attivazione e verifica cloud restano aperte. Nessuna mutazione cloud è autorizzata dalla sola presenza di questo catalogo. Piano e riscontri correnti in [CREDENTIAL_TRANSITION.md](CREDENTIAL_TRANSITION.md#piano-operativo-segreti-e-deploy-automatici--2026-11-13).

Questo catalogo riporta valori non segreti presenti nel catalogo runtime tracciato e nella policy frontend. Vittorio Di Giorgio ha confermato il 25 ottobre 2026 di essere l'unico sviluppatore e avere accesso a tutti i servizi: è il referente per completare l'inventario. Le indicazioni di owner mancante nelle tabelle restano richieste di associazione alle singole risorse, non di individuazione di un altro responsabile. Gli identificativi di account provider e le conferme operative non risultano verificabili dal repository: sono **blocked before staging activation**. Le configurazioni di staging e produzione sono riferimenti di policy, non prova di risorse verificate.

## Ambienti Firebase e applicazione

| Ambiente | Progetto Firebase | Bucket | Backend URL | Origini consentite | Credenziali | Dati e uso |
|---|---|---|---|---|---|---|
| `local` | `demo-mcp-local` | `demo-mcp-local.appspot.com` | `http://127.0.0.1:5001` | `http://localhost:3000`, `http://127.0.0.1:3000` | Emulatori su loopback; nessun JSON service account | Dati locali/emulati; non usare dati cloud |
| `test` | `demo-mcp-test` | `demo-mcp-test.appspot.com` | `http://127.0.0.1:5001` | `http://localhost:3000`, `http://127.0.0.1:3000` | Emulatori su loopback; nessun JSON service account | Dati sintetici di test; non usare dati cloud |
| `staging` | `mcp-website-dev-39539` | `mcp-website-dev-39539.appspot.com` | `https://us-central1-mcp-website-dev-39539.cloudfunctions.net` | `https://mcp-website-dev-39539.web.app` | ADC a runtime, solo dopo autorizzazione separata | Preservare dati, utenti Auth, oggetti Storage e identificativi provider esistenti; nessuna mutazione in Core WS1 |
| `production` | `mcp-website-2a1ad` | `mcp-website-2a1ad.appspot.com` | `https://us-central1-mcp-website-2a1ad.cloudfunctions.net` | `https://mcp-website-2a1ad.web.app` | ADC a runtime; prova operativa differita al gate produzione | Dati di produzione; operazioni e deployment esclusi da Core WS1 |

Gli host emulatori di `local` e `test` sono Firestore `127.0.0.1:8080`, Auth `127.0.0.1:9099`, Storage `127.0.0.1:9199` e Pub/Sub `127.0.0.1:8085`. Le origini sopra sono quelle ammesse dalla policy runtime; `cors` nel backend è configurato separatamente con wildcard nel codice osservato e non costituisce una conferma di origini operative.

## Provider

| Provider | local / test | staging | production | Account/identità e proprietario |
|---|---|---|---|---|
| PayPal | `fake` | `sandbox` | `live` | ID account non presente nei riferimenti tracciati: **blocked before staging activation**. Referente: Vittorio Di Giorgio. |
| MailerSend (`mail`) | `fake` | `disabled` (invio staging richiede allowlist esplicita) | `live` | Account e mittente da confermare: **blocked before staging activation**. Referente: Vittorio Di Giorgio. |
| Sender.net | `disabled` | `disabled` | `disabled` | Servizio non pagato e sospeso su conferma del proprietario; non riattivare. Eventuale futura proprietà: **blocked before staging activation**. |
| Pass2U | `fake` | `disabled` | `live` | Account non presente nei riferimenti tracciati: **blocked before staging activation**. Referente: Vittorio Di Giorgio. |
| Genderize.io (`gender`) | `fake` | `fake` | `disabled` | Identificativo account non richiesto dalla configurazione attuale; qualsiasi attivazione staging resta **blocked before staging activation**. |
| SoundCloud | `fake` | `fake` | `live` | Account/identità non presenti nei riferimenti tracciati: **blocked before staging activation**. Referente: Vittorio Di Giorgio. |

La sola presenza di una chiave non abilita un provider. Sender è disabilitato in tutti gli ambienti e il relativo codice rimane disponibile per test offline; la sospensione riguarda il servizio, non autorizza eliminazioni o revoche.

## Responsabilità e conferme mancanti

| Voce | Stato |
|---|---|
| Ruolo responsabile dei progetti, bucket e origini staging | Vittorio Di Giorgio, confermato dal proprietario |
| Ruolo responsabile degli account provider e mittente staging | Vittorio Di Giorgio; identità e mittente da confermare |
| Conferma di progetto, bucket, URL e origini effettivamente attivi | **blocked before staging activation** |
| Inventario non segreto di account/identità provider | **blocked before staging activation** |
| Inventario e policy di accesso/audit Doppler | Da completare prima dell'attivazione di workflow cloud; Doppler resta l'iniettore transitorio durante WS1 |

## Evidenza tracciata

- `mcp-backend/functions/config/environment_catalog.json`: progetti, bucket, backend URL, origini, emulatori, modalità provider e credenziali runtime.
- `mcp-backend/functions/config/runtime_settings.py`: validazione fail-closed di ambienti, provider e URL; Sender attivo viene rifiutato.
- `mcp-website/config/runtime-policy.cjs`: validazione della configurazione pubblica frontend, progetti/bucket, backend, emulatori e PayPal.
- `mcp-backend/functions/config/firebase_config.py`: emulatori in locale/test e ADC per cloud.
- `docs/superpowers/specs/2026-10-24-ws1-environment-provider-safety-design.md`, sezioni 7.3, 9 e 23: fonti, modalità provider e sospensione Sender.

## Inventario variabili di deployment

La tabella descrive i nomi letti dalla configurazione tracciata, non la presenza
né la verifica di valori nei sistemi di deployment. I valori fissi di progetto,
bucket e backend restano definiti dal catalogo sopra.

| Variabile | Categoria / destinazione | Differenze staging / produzione |
|---|---|---|
| `MCP_ENV`, `*_MODE`, `BACKEND_URL`, `ALLOWED_ORIGINS`, `MAIL_ALLOWED_RECIPIENTS`, `MAILERSEND_FROM_EMAIL`, `MAILERSEND_FROM_NAME` | Backend environment; modalità e URL vincolati dalla policy | `MCP_ENV=staging` o `production`; PayPal sandbox/live. Mail e Pass2U disabilitati in staging: nessuna chiave attiva richiesta per default. |
| `GCLOUD_PROJECT`, `GOOGLE_CLOUD_PROJECT`, `FIREBASE_PROJECT_ID`, `STORAGE_BUCKET`, `FIREBASE_CONFIG` | Backend environment; devono corrispondere al catalogo | Valori attesi specifici per ciascun ambiente; URL e origini cloud sono fissi. |
| `FIRESTORE_EMULATOR_HOST`, `FIREBASE_AUTH_EMULATOR_HOST`, `STORAGE_EMULATOR_HOST`, `PUBSUB_EMULATOR_HOST`, `FUNCTIONS_EMULATOR`, `FIREBASE_EMULATOR_HUB` | Backend environment, solo local/test | Emulatori rifiutati in staging/produzione. JSON legacy service account rifiutati. `GOOGLE_APPLICATION_CREDENTIALS` vietato in local/test; discovery/deploy cloud usa ADC WIF effimero, runtime cloud l'identità gestita. |
| `PAYPAL_CLIENT_ID`, `PAYPAL_LIVE_CLIENT_ID` | Backend environment e PayPal client identifier pubblico; `NEXT_PUBLIC_PAYPAL_CLIENT_ID` / `NEXT_PUBLIC_PAYPAL_LIVE_CLIENT_ID` sono frontend build e pubblici | Staging usa solo ID sandbox; ID live solo produzione. |
| `PAYPAL_CLIENT_SECRET`, `PAYPAL_LIVE_CLIENT_SECRET` | Backend environment, privati | Segreto sandbox staging e live produzione; variabili live rifiutate fuori produzione. |
| `MAILERSEND_API_KEY`, `PASS2U_API_KEY` | Backend environment, private | MailerSend e Pass2U disabilitati in staging, live in produzione. |
| `SOUNDCLOUD_CLIENT_ID`, `SOUNDCLOUD_CLIENT_SECRET` | Backend environment; client ID è configurazione backend, non automaticamente esposto nel browser; secret privato | Fake in staging, live in produzione. |
| `GENDER_API_KEY` | Backend environment, privata | Gender fake in staging, disabilitato in produzione. |
| `SENDER_API_KEY`, `SENDER_WEBHOOK_SECRET` | Backend environment, private | Sender disabilitato in tutti gli ambienti; non servono segreti attivi per default. Ogni modalità diversa da disabled è rifiutata. |
| `NEXT_PUBLIC_ENV`, `NEXT_PUBLIC_BASE_URL` / `BACKEND_BASE_URL`, `NEXT_PUBLIC_FIREBASE_PROJECT_ID`, `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`, `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`, `NEXT_PUBLIC_FIREBASE_API_KEY`, `NEXT_PUBLIC_FIREBASE_APP_ID`, `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`, `NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID` | Frontend build; configurazione pubblica | Project, bucket, auth domain e backend devono corrispondere all'ambiente. Release richiede API key e app ID Firebase pubblici. |
| `NEXT_PUBLIC_AUTH_EMULATOR_HOST`, `NEXT_PUBLIC_FIRESTORE_EMULATOR_HOST`, `NEXT_PUBLIC_STORAGE_EMULATOR_HOST`, `NEXT_PUBLIC_FUNCTIONS_EMULATOR_HOST`, `NEXT_PUBLIC_PAYPAL_ENV` | Frontend build; host emulatori solo local/test, modalità PayPal pubblica | Emulatori assenti in cloud; PayPal sandbox in staging e production/live in produzione. |
| `WIF_PROVIDER`, `DEPLOY_SERVICE_ACCOUNT` | Variabili pubbliche GitHub Environment, riferimenti usati dai template workflow; non sono JSON service account | Devono essere configurate nell'environment GitHub corrispondente; la loro presenza e i relativi target non risultano verificati qui. |

`build-safe.mjs` trasferisce nel build release solo le variabili `NEXT_PUBLIC_*`
validate; il backend acquisisce le credenziali runtime dall'ambiente. I segreti
privati sono destinati a Secret Manager/runtime injection quando questa verrà
configurata. `WIF_PROVIDER` e `DEPLOY_SERVICE_ACCOUNT` sono riferimenti di
configurazione GitHub, non segreti. Questo inventario non conferma risorse cloud
né l'effettiva configurazione di GitHub Environments o Secret Manager.



## Riscontro metadati del 2026-11-13

Lettura GitHub: nessun Environment, variabile Actions repository o secret
Actions repository configurato. Lettura Google Cloud staging: nessun workload
identity pool globale. Questo non inventaria i valori Doppler o Secret Manager,
non verifica account provider e non abilita deploy. Nessuna credenziale letta
o modificata. L'attivazione richiede il piano IAM e le prove del documento di
transizione; il catalogo runtime non sostituisce la verifica delle risorse.
