# MCP Web Project

## Overview

Questo repository contiene l'intero progetto MCP suddiviso in due componenti principali:

* **Backend (`mcp-backend`)**: Un'applicazione Flask integrata con Firebase Functions per gestire API, autenticazione, pagamenti, notifiche via mail, e varie funzionalità amministrative.
* **Frontend (`mcp-website`)**: Applicazione Next.js/React per l'interfaccia utente del sito MCP, responsabile della visualizzazione degli eventi, gestione dei pagamenti, autenticazione utente e amministrazione.

MCP (Music Connecting People) è un collettivo e brand che organizza eventi legati alla musica elettronica, house e techno, gestisce iscrizioni a newsletter, associazione, vendita biglietti e membership. Questa piattaforma è stata sviluppata per semplificare la gestione completa degli eventi, automatizzare processi amministrativi e migliorare l'esperienza utente.

## Struttura del Progetto

```
MCP-WEB-PROJECT/
├── mcp-backend/
│   └── functions/
│       ├── service_account.json
│       ├── service_mail.json
│       ├── requirements.txt
│       ├── .env
│       └── (codice Flask e funzioni Firebase)
│
└── mcp-website/
    ├── package.json
    ├── next.config.js
    ├── .env
    └── (codice Next.js frontend)
```

## Backend Setup

### Prerequisiti

* Python 3.10
* Firebase CLI

### Installazione

1. Naviga nella directory del backend:

   ```bash
   cd mcp-backend/functions
   ```

2. Crea un ambiente virtuale:

   ```bash
   python3.10 -m venv venv
   ```

3. Attiva l'ambiente virtuale:

   ```bash
   source venv/bin/activate  # macOS/Linux
   .\venv\Scripts\activate  # Windows
   ```

4. Installa le dipendenze:

   ```bash
   pip install -r requirements.txt
   ```

### Configurazione

Crea e popola i seguenti file con le tue credenziali:

* `mcp-backend/functions/.env`
* `mcp-backend/functions/service_account.json` (Firebase service account)
* `mcp-backend/functions/service_mail.json` (Google mail service account)

### Selezione DB (prod / test / locale)

Il backend sceglie il Firestore in base a queste variabili:

* **`FIRESTORE_EMULATOR_HOST`**: se settata, usa sempre il DB locale dell’emulatore.
* **`GOOGLE_APPLICATION_CREDENTIALS`**: se settata, usa il service account indicato (prod o test).
* **Default**: se `GOOGLE_APPLICATION_CREDENTIALS` non è settata, usa `mcp-backend/functions/service_account.json` (prod).

#### DB prod (cloud)
```bash
unset FIRESTORE_EMULATOR_HOST
export GOOGLE_APPLICATION_CREDENTIALS="/percorso/service_account.json"
firebase emulators:start --only functions --project <PROJECT_ID_PROD>
```

#### DB test (cloud)
```bash
unset FIRESTORE_EMULATOR_HOST
export GOOGLE_APPLICATION_CREDENTIALS="/percorso/service_.account_test.json"
firebase emulators:start --only functions --project <PROJECT_ID_TEST>
```

#### DB locale (emulatore)
```bash
export FIRESTORE_EMULATOR_HOST=127.0.0.1:8080
firebase emulators:start --only functions,firestore
```

### Auth emulator (opzionale)

Se vuoi usare l’Auth emulator con le funzioni locali:
```bash
FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099 \
firebase emulators:start --only functions,auth --project <PROJECT_ID_TEST>
```

Nel frontend:
* `NEXT_PUBLIC_AUTH_EMULATOR_HOST=127.0.0.1:9099`
* riavvia `npm run dev`

### Deploy Backend

Usa Firebase CLI per deployare:

```bash
firebase deploy --only functions
```

## Frontend Setup

### Prerequisiti

* Node.js (versione >=18 raccomandata)
* npm o yarn

### Installazione

1. Naviga nella directory del frontend:

   ```bash
   cd mcp-website
   ```

2. Installa le dipendenze:

   ```bash
   npm install
   ```

### Configurazione

Crea il file `.env` nella cartella del frontend:

```bash
NEXT_PUBLIC_ENV=local
NEXT_PUBLIC_BASE_URL=http://127.0.0.1:5001/mcp-website-2a1ad/us-central1
# Aggiungi ulteriori variabili necessarie
```

Se usi il Functions emulator con progetto test:
```
NEXT_PUBLIC_BASE_URL=http://127.0.0.1:5002/<PROJECT_ID_TEST>/us-central1
NEXT_PUBLIC_AUTH_EMULATOR_HOST=127.0.0.1:9099
```

### Esecuzione in locale

Per avviare il frontend in modalità sviluppo:

```bash
npm run dev
```

## Descrizione Generale del Progetto

MCP Web Project è stato creato per automatizzare e semplificare l'organizzazione di eventi e attività di gestione utenti per il collettivo Music Connecting People. Le funzionalità includono:

* **Gestione eventi**: creazione, modifica, eliminazione e visualizzazione eventi
* **Gestione utenti**: iscrizioni, gestione membri, newsletter e consenso GDPR
* **Pagamenti**: integrazione con PayPal, gestione acquisti e ordini
* **Automazione notifiche**: invio di email di conferma, notifiche amministrative e ticket PDF
* **Dashboard amministrativa**: gestione completa di utenti, eventi, messaggi e acquisti

Questa piattaforma è costruita con tecnologie moderne come Next.js, React, Firebase e Flask, ed è strutturata per garantire scalabilità, sicurezza e facilità d'uso sia per gli utenti finali che per gli amministratori.
