# Doppler Secrets

Doppler deve essere la fonte di verita delle variabili, non un backup base64 dei file `.env`.

Gli script in `scripts/doppler/` servono per due casi:

- import iniziale dei `.env` locali dentro Doppler come variabili reali;
- bootstrap di una macchina di sviluppo, ricreando i file locali quando serve.

In produzione non bisogna ripristinare `.env`: il processo deve partire con `doppler run -- ...` o con integrazione runtime/CI.

## Struttura

Il manifest e `scripts/doppler/secrets_manifest.conf`.

La separazione del manifest e per scope e environment logico:

- `backend` + `dev`
- `backend` + `prod`
- `frontend` + `dev`
- `frontend` + `prod`

I file `.env` indicati come `env_source` vengono parsati e ogni `KEY=VALUE` diventa un secret Doppler separato.

I file indicati come `env_target` sono solo destinazioni di restore locale. Questo evita di dipendere da `.env` gia presenti su un computer nuovo.

I service account JSON vengono salvati come valore JSON grezzo in una variabile, non in base64:

- `FIREBASE_SERVICE_ACCOUNT_JSON`
- `GMAIL_SERVICE_ACCOUNT_JSON`

`.env.local` non e incluso per scelta: deve restare un override locale temporaneo, non una fonte di verita condivisa.

## Setup Doppler

Esempio con due progetti Doppler separati:

```bash
doppler projects create mcp-backend
doppler projects create mcp-frontend
doppler configs create dev_backend --project mcp-backend --environment dev
doppler configs create prd_backend --project mcp-backend --environment prd
doppler configs create dev_frontend --project mcp-frontend --environment dev
doppler configs create prd_frontend --project mcp-frontend --environment prd
```

Doppler impone il prefisso della config in base all'environment: per `dev` usa `dev_*`, per produzione di solito usa l'environment id `prd` e config `prd_*`.

## Push Iniziale

Backend dev:

```bash
scripts/doppler/push_secrets.sh --project=mcp-backend --config=dev_backend --scope=backend
```

Backend prod:

```bash
scripts/doppler/push_secrets.sh --project=mcp-backend --config=prd_backend --scope=backend --env=prod
```

Frontend dev:

```bash
scripts/doppler/push_secrets.sh --project=mcp-frontend --config=dev_frontend --scope=frontend
```

Frontend prod:

```bash
scripts/doppler/push_secrets.sh --project=mcp-frontend --config=prd_frontend --scope=frontend --env=prod
```

Prima di caricare puoi controllare cosa verrebbe preparato senza inviare segreti:

```bash
scripts/doppler/push_secrets.sh --project=mcp-backend --config=dev_backend --scope=backend --dry-run
```

## Sviluppo Locale

Approccio preferito: lanciare i processi con Doppler, senza `.env`.

Backend:

```bash
./emulator.sh --env=test --auth=true --firestore-emulator=true --doppler=true
```

Frontend:

```bash
./frontend-dev.sh --development=true --auth-emulator=true --doppler=true
```

Build frontend production:

```bash
./frontend-build.sh --doppler=true
```

Se invece devi ricreare i file locali su una nuova macchina:

```bash
scripts/doppler/pull_secrets.sh --project=mcp-backend --config=dev_backend --scope=backend
scripts/doppler/pull_secrets.sh --project=mcp-frontend --config=dev_frontend --scope=frontend
```

Per sovrascrivere file gia esistenti:

```bash
scripts/doppler/pull_secrets.sh --project=mcp-backend --config=dev_backend --scope=backend --overwrite
```

## Produzione

Non usare `.env` in produzione.

Esempio runtime:

```bash
doppler run --project mcp-backend --config prd_backend -- npm start
```

Il pull di `prod` e bloccato di default per evitare di scrivere segreti di produzione su disco.
Se serve davvero un restore locale controllato, va esplicitato:

```bash
scripts/doppler/pull_secrets.sh --project=mcp-backend --config=prd_backend --scope=backend --env=prod --allow-prod-file
```

## Note Operative

- Gli script non stampano i valori dei segreti.
- `push_secrets.sh` carica su Doppler variabili reali, non payload base64.
- `pull_secrets.sh` non sovrascrive file esistenti salvo `--overwrite`.
- Quando aggiungi un nuovo file sorgente, aggiorna `scripts/doppler/secrets_manifest.conf`.
