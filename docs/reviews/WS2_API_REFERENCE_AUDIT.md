# WS2 — Inventario dei riferimenti API

Data: 2026-11-03. Base: `d8ac90e8` (merge WS1).
Controllo statico dell'intera mappa `mcp-website/config/endpoints.js` contro
gli handler HTTP importati da `mcp-backend/functions/main.py`.

Risultato: **130 riferimenti, 128 export HTTP, quattro riferimenti legacy
senza handler corrispondente**. Questi numeri non devono coincidere: esistono
funzioni backend senza riferimento nella mappa. Non dimostrano compatibilità
dei payload o raggiungibilità di ogni schermata.

| Riferimento frontend | Evidenza e consumatori | Disposizione |
|---|---|---|
| `newsletterParticipantsSignup` / `newsletter_participants` | Mappa, riga 18. Nessun uso della chiave trovato nei sorgenti frontend. | Eccezione nominata; nessuna cancellazione automatica. |
| `signupRequest` / `signup_request` | Mappa, riga 22; `services/signup.js:7` e `services/admin/signup.js:12`. Nessun import di questi servizi trovato in app/components. | Servizi legacy, uso da UI non dimostrato. Ripristino richiede decisione di prodotto. |
| `questions.getAll` / `get_all_questions` | Mappa, riga 44; `services/signup.js:40`. Nessun import del servizio trovato in app/components. | Come signup: non inventare un backend sostitutivo. |
| `admin.uploadEventPhoto` / `admin_upload_event_photo` | Mappa, riga 54. Nessun uso della chiave trovato nei sorgenti frontend. | Eccezione nominata; nessuna cancellazione automatica. |

La pagina `app/admin/signup-requests/page.jsx` mostra esplicitamente che la
sezione non è disponibile. Il servizio admin legacy accede anche a proprietà
non presenti nella mappa (`getSignupRequests`, `updateSignupRequest`,
`deleteSignupRequest`, `acceptSignupRequest`): incoerenza annotata, non riparata
in questo blocco. Il controllo globale copre le voci dichiarate nella mappa,
non ogni possibile accesso dinamico a proprietà da qualunque sorgente.

Le ricerche statiche di nomi e import non escludono caricamenti indiretti o
consumatori esterni. Per questo non sono state eliminate funzioni o chiavi.

## Regola del gate

`npm run check:contracts` elenca tutte le eccezioni a ogni esecuzione. Una
nuova destinazione assente fallisce. Se un'eccezione viene implementata o il
suo riferimento viene rimosso, il gate richiede di eliminare l'eccezione.
Sorgente non interpretabile, proprietà duplicate e route dinamiche non
supportate falliscono invece di essere saltate. Sono rifiutate anche mutazioni
successive della mappa, alias della mappa stessa e riassegnazioni delle funzioni
Python inventariate. Alias di export Python
sono risolti; callable, trigger e funzioni non esportate non soddisfano una route HTTP.

Restano fuori da questo gate: metodi, body, risposte, errori e autorizzazioni
di tutte le API. Questi contratti sono verificati in profondità sul primo
flusso eventi tramite lo smoke HTTP, separatamente dall'inventario.
