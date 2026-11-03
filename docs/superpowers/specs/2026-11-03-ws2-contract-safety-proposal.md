# WS2 — Proposta del primo blocco: contratti API e permessi

Stato: approccio A e perimetro approvati dal proprietario in chat il 2026-11-03.
Base: `origin/main`, commit `d8ac90e8`, dopo il merge di WS1.

## Punto di partenza

WS1 ha già introdotto unit test, test frontend, build controllata e smoke
con emulatori nel workflow PR. Evitare di ricostruire questa infrastruttura.

Evidenze ancora presenti nella base:

- `mcp-website/config/endpoints.js` contiene quattro slugs senza una funzione
  esportata corrispondente: `newsletter_participants`, `signup_request`,
  `get_all_questions`, `admin_upload_event_photo`.
- `signup_request` e `get_all_questions` sono richiamati da servizi frontend;
  il loro utilizzo effettivo dalle schermate resta da ricostruire.
- `tests/integration/conftest.py` sostituisce automaticamente la verifica
  del token admin. Questi test non provano i permessi reali.
- Lo smoke WS1 usa token dell'emulatore, ma verifica solo pochi percorsi.

## Approcci

A. Contratti API prima dei test browser (raccomandato): riusare Node/Python
ed emulatori esistenti; individuare riferimenti mancanti e verificare il
contratto di lettura degli eventi, compresi i permessi admin.

B. Test browser prima dei contratti: automatizzare login e navigazione.
Richiede valutare e predisporre un runner browser, con maggiore superficie
di manutenzione. Utile successivamente per provare le interazioni UI.

## Perimetro proposto per A

1. Ricostruire i consumatori dei quattro riferimenti mancanti. Distinguere
   codice inutilizzato da funzionalità effettivamente esposte; documentare
   le decisioni di prodotto necessarie senza inventare endpoint sostitutivi.
2. Aggiungere un controllo riproducibile di coerenza tra mappa frontend e
   funzioni HTTP esportate. Eventuali eccezioni legacy devono essere nominate
   e motivate: nessuna esclusione generica dei fallimenti.
3. Verificare un solo flusso tramite HTTP ed emulatori: lettura degli eventi.
   Controllare risposta pubblica, dettaglio esistente/assente, accesso admin
   consentito con claim e rifiutato senza token o con utente normale.
4. Eseguire queste prove nel workflow PR esistente.

Prima del codice, il piano deve fissare endpoint, payload e status osservati.
Se un riferimento richiede ripristinare una funzionalità, fermare quella
correzione per una decisione di prodotto e proseguire le prove indipendenti.

## Successo e limiti

I controlli devono rilevare un nuovo endpoint frontend inesistente e un
accesso admin indebitamente consentito. Dati sintetici isolati nel progetto
demo, nessun bypass dell'autenticazione nel nuovo flusso HTTP.

Nessun nuovo provider, dipendenza, deploy o modifica cloud. Nessun nuovo
comportamento di pagamento. Esclusi dal primo blocco: contratti completi di
tutte le API, copertura browser generale e generatori volumetrici.

## Passo successivo

Preparare il piano implementativo con file, prove e criteri di arresto;
attendere la sua revisione prima dell'implementazione. Nessun codice
applicativo modificato durante il design.
