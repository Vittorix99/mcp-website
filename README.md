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
