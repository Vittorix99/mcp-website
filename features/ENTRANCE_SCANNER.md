# MCP Entrance Scanner — Documentazione tecnica

## Panoramica

Sistema di scansione QR per l'ingresso agli eventi MCP. Permette a un operatore di aprire un link sul telefono e scansionare le tessere dei partecipanti in tempo reale, ricevendo un feedback visivo immediato (verde/giallo/rosso).

---

## Architettura del flusso

```
Admin Panel (web)
    │
    ├─ genera scan_token → Firestore (scan_tokens/{token})
    │
    └─ costruisce URL: https://<dominio>/scan/<token>
                            │
                            ▼
                  Scanner App (telefono)
                    │
                    ├─ verifica token → entrance_verify_scan_token
                    ├─ avvia fotocamera (getUserMedia)
                    ├─ scansiona QR tessera → membership_id
                    └─ valida ingresso → entrance_validate
                                            │
                                            ▼
                                   Firestore: entrance_scans/{event_id}/scans/{membership_id}
```

---

## Componenti implementati

### 1. Admin Panel — Generazione token (`content.jsx`)

**File:** `mcp-website/app/admin/events/[id]/content.jsx`

Tab "In the event" nella pagina dettaglio evento. Permette all'admin di:
- Generare un **scan token** monouso (scadenza 12h)
- Copiare il link negli appunti
- Condividerlo via Web Share API (nativo mobile)
- Disattivare il token

Il link è costruito con `window.location.origin` per funzionare sia in dev che in prod:
```js
function buildScanUrl(tok) {
  return `${window.location.origin}/scan/${tok}`;
}
```

Il token è persistito in `localStorage` con chiave `mcp_scan_token_${eventId}` per sopravvivere ai refresh di pagina.

**Servizi admin:** `mcp-website/services/admin/entrance.js`
```js
generateScanToken(event_id)   // POST entrance_generate_scan_token
verifyScanToken(token)        // GET  entrance_verify_scan_token?token=...
deactivateScanToken(token)    // POST entrance_deactivate_scan_token
```

**Endpoints config:** `mcp-website/config/endpoints.js`
```js
entrance: {
  generateScanToken:   make("entrance_generate_scan_token"),
  verifyScanToken:     make("entrance_verify_scan_token"),
  deactivateScanToken: make("entrance_deactivate_scan_token"),
}
```

---

### 2. Scanner App — Route Handler

**File:** `mcp-website/app/scan/[token]/route.js`

Next.js Route Handler che restituisce una **pagina HTML autonoma** (non usa React/Next.js client-side). Il token è iniettato server-side:

```js
const SCAN_TOKEN = ${JSON.stringify(token)};
```

#### Flusso stati della pagina

```
loading → (verifica token) → tap → (utente tocca) → idle (scanner attivo)
                                                          │
                                                          ▼
                                                     overlay (3s feedback)
                                                          │
                                                          ▼
                                                     idle (riprende scan)
```

#### Libreria QR: Nimiq `qr-scanner`

Dopo test falliti con jsQR e BarcodeDetector API, la soluzione definitiva è **Nimiq qr-scanner v1.4.2**:

| Libreria | Problema su iOS Safari |
|---|---|
| `jsQR` | Bug confermato `RangeError` dopo ~30s, non mantenuto dal 2021 |
| `BarcodeDetector` | Rotto su iOS 18, solo flag sperimentale su iOS 17 |
| **`@nimiq/qr-scanner`** | ✅ WASM + Web Worker, gestisce quirk Safari, attivamente mantenuto |

I file sono serviti staticamente da Next.js:
- `public/qr-scanner.umd.min.js`
- `public/qr-scanner-worker.min.js`

```js
QrScanner.WORKER_PATH = '/qr-scanner-worker.min.js';
qrScanner = new QrScanner(videoEl, result => onQrResult(result.data), {
  preferredCamera: 'environment',
  returnDetailedScanResult: true,
});
await qrScanner.start();
```

#### Requisito HTTPS

`getUserMedia` è bloccato dai browser mobile su HTTP (eccetto localhost). In produzione Firebase Hosting usa HTTPS automaticamente. Per sviluppo locale serve un tunnel:

```bash
# Installa cloudflared
brew install cloudflare/cloudflare/cloudflared

# Avvia tunnel (con Next.js già in esecuzione su :3000)
npm run tunnel   # → cloudflared tunnel --url http://localhost:3000
```

#### Guard desktop

La pagina blocca l'accesso da desktop (UA + viewport width):
```js
function isDesktop() {
  const hasMobileUA = /Android|iPhone|iPad|iPod|Mobile/.test(navigator.userAgent);
  return !hasMobileUA && window.innerWidth > 1024;
}
```

#### Tap-to-start

iOS Safari richiede che `getUserMedia` venga chiamato dentro un gestore di evento touch/click. La pagina mostra quindi uno stato intermedio "Avvia scanner" prima di aprire la fotocamera.

---

### 3. Struttura Firestore

```
scan_tokens/
  {token}
    event_id: string
    created_by: string
    created_at: timestamp
    expires_at: timestamp
    is_active: boolean

entrance_scans/
  {event_id}/
    scans/
      {membership_id}
        scanned_at: timestamp
        scan_token: string

membership_settings/
  price
    price_by_year: { "2026": 10.0 }
```

---

### 4. Backend — Cloud Functions

| Function | Metodo | Descrizione |
|---|---|---|
| `entrance_generate_scan_token` | POST | Crea token con scadenza 12h |
| `entrance_verify_scan_token` | GET | Verifica token e restituisce `event_title` |
| `entrance_deactivate_scan_token` | POST | Disattiva token |
| `entrance_validate` | POST | Valida membership_id + scan_token, registra ingresso |

**Risultati possibili da `entrance_validate`:**

| result | Significato | Overlay |
|---|---|---|
| `valid` | Primo ingresso confermato | 🟢 Verde |
| `already_scanned` | Già entrato (con orario) | 🟡 Giallo |
| `invalid_no_purchase` | Membership valida ma nessun biglietto | 🔴 Rosso |
| `invalid_member_not_found` | QR non corrisponde a nessuna tessera | 🔴 Rosso |
| `invalid_token` | Token scaduto o disattivato | Stato errore terminale |

---

### 5. Script di seed test

**File:** `mcp-backend/functions/scripts/seed_entrance_test.py`

Popola il Firestore emulator con tutti i dati necessari per testare i 5 scenari:

```bash
cd mcp-backend/functions
python scripts/seed_entrance_test.py          # seed
python scripts/seed_entrance_test.py --reset --event-id <id> --token <tok>  # reset + reseed
```

**Scenari coperti:**

| Tessera | Scenario | Risultato atteso |
|---|---|---|
| `KmSbPtCkafBLaoF9zGr4` | Membership valida + biglietto | ✅ valid |
| `HIWVbeT2RfjSv9jZGY9y` | Membership valida + biglietto | ✅ valid |
| `test_no_purchase_001` | Membership valida, nessun biglietto | ❌ invalid_no_purchase |
| `test_double_scan_002` | Già scansionato 30min fa | 🟡 already_scanned |
| (tessera inesistente) | Nessun documento Firestore | ❌ invalid_member_not_found |

Lo script crea anche il documento `membership_settings/price` con il prezzo dell'anno corrente (richiesto dall'endpoint `/api/proxy/get_membership_price`).

---

## Setup sviluppo

### Prerequisiti

```bash
# Frontend
cd mcp-website && npm install

# Backend emulator
firebase emulators:start --only firestore
# oppure
export FIRESTORE_EMULATOR_HOST=127.0.0.1:8080

# Seed dati test
cd mcp-backend/functions
python scripts/seed_entrance_test.py
```

### Avvio

```bash
# Terminal 1 — Frontend
cd mcp-website && npm run dev

# Terminal 2 — Backend Flask (test)
cd mcp-backend/functions && python main.py

# Terminal 3 — Tunnel HTTPS (per test su telefono)
cd mcp-website && npm run tunnel
# → copia URL https://xxx.trycloudflare.com
```

### Aprire lo scanner sul telefono

1. Dall'admin panel, vai su un evento → tab "In the event"
2. Clicca "Genera link scanner"
3. Copia il link o usa "Condividi"
4. Se in sviluppo, sostituisci il dominio con l'URL cloudflare:
   - `https://xxx.trycloudflare.com/scan/<token>`
5. Apri sul telefono → tocca "Avvia scanner" → consenti fotocamera

---

## Tecnologie usate

| Tecnologia | Uso |
|---|---|
| **Next.js 15 Route Handler** | Scanner app servita come HTML puro (no React client) |
| **Nimiq qr-scanner v1.4.2** | Decodifica QR via WASM + Web Worker (iOS Safari compatibile) |
| **Firebase Firestore** | Storage token, scan, membership, entrance_scans |
| **Cloud Functions (Flask/Python)** | Backend API per generazione/validazione token e ingressi |
| **Cloudflare Quick Tunnel** | HTTPS locale per test fotocamera su telefono |
| **Web Share API** | Condivisione link nativa da mobile |
| **Clipboard API** | Copia link negli appunti |
| **navigator.vibrate** | Feedback aptico su scansione |
| **localStorage** | Persistenza scan token tra refresh pagina |
