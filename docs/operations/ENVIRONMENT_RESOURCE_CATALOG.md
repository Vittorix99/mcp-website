# Catalogo ambienti e risorse — Core WS1

**Stato:** Core WS1 in corso; gate di test/CI ancora da chiudere. Nessuna attivazione staging o deployment è autorizzata da questo documento.

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
| PayPal | `fake` | `sandbox` | `live` | ID account non presente nei riferimenti tracciati: **blocked before staging activation**. Ruolo owner: **blocked before staging activation**. |
| MailerSend (`mail`) | `fake` | `disabled` (invio staging richiede allowlist esplicita) | `live` | Account e mittente da confermare: **blocked before staging activation**. Ruolo owner: **blocked before staging activation**. |
| Sender.net | `disabled` | `disabled` | `disabled` | Servizio non pagato e sospeso su conferma del proprietario; non riattivare. Eventuale futura proprietà: **blocked before staging activation**. |
| Pass2U | `fake` | `disabled` | `live` | Account non presente nei riferimenti tracciati: **blocked before staging activation**. Ruolo owner: **blocked before staging activation**. |
| Genderize.io (`gender`) | `fake` | `fake` | `disabled` | Identificativo account non richiesto dalla configurazione attuale; qualsiasi attivazione staging resta **blocked before staging activation**. |
| SoundCloud | `fake` | `fake` | `live` | Account/identità non presenti nei riferimenti tracciati: **blocked before staging activation**. Ruolo owner: **blocked before staging activation**. |

La sola presenza di una chiave non abilita un provider. Sender è disabilitato in tutti gli ambienti e il relativo codice rimane disponibile per test offline; la sospensione riguarda il servizio, non autorizza eliminazioni o revoche.

## Responsabilità e conferme mancanti

| Voce | Stato |
|---|---|
| Ruolo responsabile dei progetti, bucket e origini staging | **blocked before staging activation** |
| Ruolo responsabile degli account provider e mittente staging | **blocked before staging activation** |
| Conferma di progetto, bucket, URL e origini effettivamente attivi | **blocked before staging activation** |
| Inventario non segreto di account/identità provider | **blocked before staging activation** |
| Inventario e policy di accesso/audit Doppler | Da completare prima dell'attivazione di workflow cloud; Doppler resta l'iniettore transitorio durante WS1 |

## Evidenza tracciata

- `mcp-backend/functions/config/environment_catalog.json`: progetti, bucket, backend URL, origini, emulatori, modalità provider e credenziali runtime.
- `mcp-backend/functions/config/runtime_settings.py`: validazione fail-closed di ambienti, provider e URL; Sender attivo viene rifiutato.
- `mcp-website/config/runtime-policy.cjs`: validazione della configurazione pubblica frontend, progetti/bucket, backend, emulatori e PayPal.
- `mcp-backend/functions/config/firebase_config.py`: emulatori in locale/test e ADC per cloud.
- `docs/superpowers/specs/2026-10-24-ws1-environment-provider-safety-design.md`, sezioni 7.3, 9 e 23: fonti, modalità provider e sospensione Sender.

