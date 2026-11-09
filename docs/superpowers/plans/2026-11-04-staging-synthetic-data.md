# Staging — Sostituzione dei dati legacy con dati sintetici

Stato: inventario e matrice definiti; generatore offline implementato.
Importazione/rilettura Firestore emulatori confermata da Vittorio; reset/seed cloud non autorizzati.
Progetto: `mcp-website-dev-39539`.
Il proprietario conferma che contiene un vecchio backup di produzione,
inadeguato per i test. Nessuna scrittura cloud autorizzata da questo file.

## Risultato

Staging ripetibile, con persone e dati inventati. Solo alcune caselle realmente
controllate dal proprietario ricevono email di prova. Casella comunicata dal
proprietario il 2026-11-05, con autorizzazione all’uso di plus addressing.
Riutilizzare `MAIL_ALLOWED_RECIPIENTS`, già supportato. Niente wildcard o domini
interi: gli indirizzi approvati devono essere espliciti e non versionati in Git.

## Dimensione del dataset approvata — 2026-11-05

L'ultima richiesta di Vittorio sostituisce la proposta precedente di 10000
utenti, 100 eventi e 50000 acquisti. Obiettivo: coprire i casi applicativi
attualmente disponibili con dati collegati e risultati verificabili.

| Entità | Quantità |
| --- | ---: |
| Profili socio in `memberships` | 4000 |
| Eventi sintetici | 50 |
| Iscrizioni agli eventi | Da 1 a N per ogni socio, con distribuzione variabile |
| Acquisti e ordini | Derivati dagli scenari, senza un totale prefissato di 50000 |
| Ingressi e scansioni | Derivati dalle iscrizioni e dagli scenari di accesso |

4000 membri significa 4000 profili socio, non 4000 partecipazioni né
automaticamente 4000 account Firebase Auth. Il numero di account Auth per
le prove di login va esplicitato nel dry-run; mantenere i quattro ruoli
manuali già previsti. Ogni socio ha un alias progressivo distinto, per
esempio `+staging-user-00001`, costruito dalla casella approvata configurata
localmente. Gli indirizzi completi restano fuori da Git.

Ogni socio ha almeno un'iscrizione storica; N dipende dagli eventi compatibili
con date e modalità di accesso. Lo stesso socio può comparire in eventi diversi.
Il numero di iscrizioni non coincide con quello degli ingressi: includere
iscritti mai entrati e ingressi effettuati. Un socio oggi scaduto può avere
partecipazioni passate quando era valido. Le prove su un socio senza iscrizione
usano un evento diverso da quelli ai quali è iscritto.

Mantenere coerenti soci, eventuali account Auth, tessere, acquisti, partecipanti
e scansioni. Gli acquisti storici del seed non creano ordini presso i provider.

Il caricamento massivo non invia email. Generare un alias non lo aggiunge
automaticamente a `MAIL_ALLOWED_RECIPIENTS`: solo destinatari selezionati
vengono abilitati per le prove di ricezione. I quattro alias iniziali restano
disponibili per le prove manuali dei ruoli.

### Verifica con molti dati e prova di carico

1. Negli emulatori verificare generazione, relazioni, permessi e caricamento
   ripetibile senza duplicati, mantenendo gli invii disabilitati.
2. Dopo approvazione del rapporto di reset, caricare il dataset su staging.
3. Su staging provare login, ricerca, filtri, paginazione e statistiche con
   il dataset completo. Provare separatamente ordini sandbox e ricezione
   email/tessere su pochi destinatari esplicitamente consentiti.
4. Preparare una prova distinta con utenti simultanei in aumento graduale:
   misurare tempi di risposta, errori e correttezza dei dati. Definire prima
   limiti di concorrenza, durata, spesa e criteri di arresto. Non sono ancora
   stati scelti numeri di concorrenza o soglie prestazionali, né eseguito carico.

L'approvazione delle quantità autorizza la preparazione del dataset e delle
prove; non sostituisce l'approvazione concreta per reset, scritture cloud,
deploy o invii. Un database popolato non dimostra da solo la tenuta sotto
richieste concorrenti.

## Matrice dei casi richiesta da Vittorio — 2026-11-05

La matrice seguente deriva dalla lettura di modelli, regole, servizi, API e
test del checkout eventi, soci, partecipanti, ingressi e statistiche.
È completa come specifica operativa del perimetro indicato; non è una prova
che i casi siano già passati, né una copertura di ogni possibile input.

**Stati originari della matrice (5 novembre):** `D` = definito, da eseguire;
`Q` = definito, con discrepanza o contratto da chiarire; `X` = definito,
prova esterna rinviata. Questi stati non certificano l'esito attuale:
le evidenze successive e i limiti di copertura sono riportati sotto.

**Prove:** `Seed` = scenario persistente nel dataset; `API` = azione tramite
servizi/HTTP con verifica delle scritture; `Locale` = clock, concorrenza o
provider controllati negli emulatori/test; `UI` = prova manuale/browser.
Ogni variante elencata nella stessa riga è un'istanza distinta da generare
e verificare. I casi negativi o mutanti usano copie isolate del dataset.

**Invarianti del dataset:** 4000 soci distinti e 50 eventi; per ogni socio
almeno una iscrizione storica e da 1 a N iscrizioni totali compatibili con
le regole. Un'iscrizione non implica ingresso, pagamento online o account
Auth. Acquisti di gruppo possono creare più partecipanti; inserimenti manuali
possono non avere un documento `Purchase`. Conteggi derivati, non un target
fisso di acquisti/scansioni. Congelare la data di riferimento del generatore
e indicarla nel manifesto, insieme agli scenari che diventano obsoleti col tempo.

### Soci, anni associativi e account

Fonti: [membership_rules.py](../../../mcp-backend/functions/domain/membership_rules.py),
[memberships_service.py](../../../mcp-backend/functions/services/memberships/memberships_service.py),
[member_service.py](../../../mcp-backend/functions/services/memberships/member_service.py),
[merge_service.py](../../../mcp-backend/functions/services/memberships/merge_service.py),
[new_year_trigger.py](../../../mcp-backend/functions/triggers/new_year_trigger.py).

| ID | Preparazione e operazione | Esito da verificare e impatto sui dati/statistiche | Prova/stato |
| --- | --- | --- | --- |
| MEM-01 | Socio adulto, anno corrente presente, flag valido; lettura e checkout | Profilo leggibile; riconosciuto come socio nel checkout; incluso negli attivi. | Seed/API D |
| MEM-02 | Socio solo anni precedenti, flag falso e tessera scaduta | Storico preservato; escluso dagli attivi; rinnovo possibile. Le vecchie partecipazioni restano. | Seed/API D |
| MEM-03 | Anno corrente presente ma flag falso | Checkout classifica per `membership_years`; scanner rifiuta per flag. Attivi e soci riconosciuti possono divergere: Q-01. | Seed/API Q |
| MEM-04 | Date scadute, flag vero, anno corrente assente; poi variante inversa | Dimostrare separatamente filtro annuale, attivi e scanner; nessuna presunta invalidazione automatica dalla sola data: Q-01. | Locale Q |
| MEM-05 | Nuova iscrizione adulta, email o solo telefono; entrambi mancanti | Nei primi casi crea socio con primo rinnovo e anno corrente; senza contatti errore e nessun nuovo socio. Variante solo telefono isolata dal dataset con alias. | API D |
| MEM-06 | Data nascita minorenne, mancante, invalida; confine dei 18 anni | Rifiuto dove richiesto; nessuna creazione/rinnovo. Confrontare il compleanno reale con il calcolo attuale a giorni/365: Q-06. | Locale Q |
| MEM-07 | Nuova create con email o telefono appartenenti a socio di anno precedente | Rinnova lo stesso ID; nessun socio duplicato; attivi aumentano solo se prima falso. | API D |
| MEM-08 | Stessi contatti di socio già coperto nell'anno corrente | Conflitto; nessuna nuova membership né doppia quota/storia. | API D |
| MEM-09 | Rinnovo con storico assente, pluriennale o anni duplicati | Preserva anno precedente; una voce completa per anno; `membership_years` deduplicato e coerente; acquisti senza duplicati. | Seed/API D |
| MEM-10 | Update con contatto già usato da altro socio | Conflitto secondo ramo email/telefono, eventuale proposta di merge; nessuna sostituzione silenziosa. | API D |
| MEM-11 | Socio senza Auth; poi login di account con email corrispondente e uid assente | Socio resta distinto da account; lettura area personale collega uid se possibile; liste acquisti/eventi proprie. Login senza socio restituisce not found. | Seed/API D |
| MEM-12 | Merge di due soci con eventi/acquisti/anni sovrapposti | Target con riferimenti deduplicati, contatti target preservati, partecipanti riallineati e source eliminato; soci -1, partecipazioni non raddoppiate. | Locale D |
| MEM-13 | Merge su se stesso, ID mancanti/inesistenti; guasto durante merge | Rifiuto nei casi invalidi; errore parziale esplicito e flag merging ripulito dove previsto. Nessuna asserzione di rollback atomico. | Locale D |
| MEM-14 | Invalidazione di inizio anno con oltre 500 soci validi | Tutti i flag attivi diventano falsi, anche nei batch successivi; soci/storico conservati; QR rifiutato finché non rinnovato. Solo clock/trigger locale. | Locale D |
| MEM-15 | Consenso newsletter vero/falso e modifica preferenze | Profilo conserva il consenso; nessun invio massivo dal seed e nessuna attivazione Sender. Testare il ramo locale senza provider live. | Seed/API D |

### Eventi, date e disponibilità

Fonti: [event_rules.py](../../../mcp-backend/functions/domain/event_rules.py),
[events_utils.py](../../../mcp-backend/functions/utils/events_utils.py),
[events_service.py](../../../mcp-backend/functions/services/events/events_service.py),
[active_event.py](../../../mcp-backend/functions/api/decorators/active_event.py),
[event_api.py](../../../mcp-backend/functions/dto/event_api.py).

| ID | Preparazione e operazione | Esito da verificare e impatto sui dati/statistiche | Prova/stato |
| --- | --- | --- | --- |
| EVT-01 | Eventi `active`, `coming_soon`, `sold_out`, `ended`; listing admin/pubblico | Stati serializzati correttamente; admin vede conteggi reali; verificare distinzioni UI. Il listing pubblico attuale non filtra tutti gli stati. | Seed/API/UI D |
| EVT-02 | Checkout su evento ended o temporalmente concluso anche se active | Rifiuto prima di chiamare il provider; zero ordini/acquisti/partecipanti nuovi. | API D |
| EVT-03 | Checkout su coming_soon o sold_out non concluso | Guard attuale blocca ended/tempo, non questi stati: rilevare accettazione o rifiuto API/UI e confrontare disponibilità desiderata, Q-02. | API/UI Q |
| EVT-04 | Evento con 0 iscritti, capienza parziale, esatta e richiesta oltre capienza | Conteggi/fill rate esatti; verificare blocco oltre capienza. Nessun controllo di capienza trovato nel checkout esaminato: Q-02. | Seed/API Q |
| EVT-05 | Capienza assente o zero; report con nessun acquisto/ingresso | Nessuna divisione per zero o NaN; percentuali secondo contratto attuale a zero; nessun prezzo medio inventato. | Seed/API D |
| EVT-06 | Evento 23:00-05:00; fine uguale all'inizio; fine non parsabile | Fine al giorno successivo per orario <= inizio; fallback 12 ore se fine non parsabile; checkout prima/al/dopo termine. | Locale D |
| EVT-07 | Date supportate, data invalida, cambio anno e ora legale Europe/Rome | Normalizzazione DTO; confronto con clock esplicito; errore/fallback documentato per forma legacy, senza scambiare UTC e ora locale. | Locale D |
| EVT-08 | Eventi passati, in corso e futuri; prossimo evento e limite lista | Esclude ended/conclusi nel ramo upcoming, ordina per inizio e rispetta limite; verificare lista completa separatamente. | Seed/API D |
| EVT-09 | Get per ID/slug inesistente; create/update/delete admin | 404 dove previsto; create/update persistono campi; delete attuale elimina evento senza prova di cascata su documenti collegati: Q-07. | API Q |
| EVT-10 | Lettura evento pubblico e admin dello stesso ID | Pubblico non espone campi riservati/location completa; admin conserva dati e conteggi previsti dai rispettivi DTO. | API D |

### Partecipanti e combinazioni di checkout

Fonti: [participant_rules.py](../../../mcp-backend/functions/domain/participant_rules.py),
[participants_service.py](../../../mcp-backend/functions/services/events/participants_service.py),
[event_payment_service.py](../../../mcp-backend/functions/services/payments/event_payment_service.py),
[preorder.py](../../../mcp-backend/functions/dto/preorder.py).

| ID | Preparazione e operazione | Esito da verificare e impatto sui dati/statistiche | Prova/stato |
| --- | --- | --- | --- |
| PAR-01 | PUBLIC con socio valido, scaduto o nuovo partecipante | Nessuna tessera creata automaticamente da questa modalità; partecipanti collegati solo dove il flusso lo prevede. | Seed/API D |
| PAR-02 | ONLY_ALREADY_REGISTERED_MEMBERS con tutti soci correnti; poi almeno uno non corrente | Primo caso prosegue; secondo rifiuta l'intero checkout prima di PayPal, senza partecipanti parziali. | API D |
| PAR-03 | ONLY_MEMBERS con tutti soci correnti; poi nuovi/scaduti o gruppo misto | Crea/rinnova soltanto i target necessari dopo capture; preserva ID dei soci esistenti. Importo atteso trattato in Q-03. | Seed/API Q |
| PAR-04 | ON_REQUEST: verifica partecipanti e checkout | Check restituisce elenchi; checkout rifiuta acquisto online. Inserimento admin è un percorso distinto. | API D |
| PAR-05 | Gruppo con più persone; payer PayPal diverso da partecipanti | Un acquisto, più iscrizioni; `participants_count` e collegamenti corretti; non attribuire automaticamente a ogni partecipante l'identità del payer. | Seed/API D |
| PAR-06 | Email/telefono duplicati nel payload oppure già nell'evento; flag allow_duplicates falso/vero | Falso: rifiuto per contatto già presente; vero: ramo consente duplicati. Con stesso socio più iscrizioni, scan resta uno per socio/evento: Q-08. | API Q |
| PAR-07 | Stessa email di socio corrente con nome/cognome diversi; poi accenti/case/spazi equivalenti | Identità diversa rifiutata; normalizzazione equivalente riconosciuta; nessuna nuova tessera per aggirare il conflitto. | API D |
| PAR-08 | Email/telefono/data nascita mancanti o formato email invalido; body vuoto, carrello 0/>1 elementi | Errore DTO/regola 400; nessuna chiamata provider o scrittura. Verificare singole varianti. | API D |
| PAR-09 | Over21 disabilitato/abilitato con 18-20, confine 21, >21 | Adulti sotto 21 consentiti solo senza restrizione; confine età verificato col calendario, Q-06. Minorenni sempre rifiutati. | Locale Q |
| PAR-10 | Only_females con gender fake female/male/unknown ed errore lookup | Solo female passa il ramo restrittivo; dato input gender non sostituisce il lookup della regola; nessuna chiamata provider live. | Locale D |
| PAR-11 | Admin crea partecipante con tessera inclusa: socio attivo/scaduto/assente | Attivo senza ID esplicito: conflitto; scaduto: rinnovo; assente: creazione. Una sola iscrizione e ID tessera coerenti. | API D |
| PAR-12 | Admin passa membershipId esplicito esistente/inesistente | Esistente: collega senza rinnovare e membership_included viene azzerato nel ramo; inesistente: 404. Verificare anche flag socio falso. | API D |
| PAR-13 | Admin aggiunge non socio a evento riservato | Percorso manuale attuale consente l'override senza regola checkout; UI e risultato devono distinguerlo dal pagamento pubblico. | API D |
| PAR-14 | Prezzo manuale positivo/zero e metodi cash/iban/private_paypal/omaggio | Valori validi persistiti; zero risolto a omaggio; metodo mancante/invalido rifiutato dove richiesto; nessun Purchase online inventato. | Seed/API D |
| PAR-15 | Partecipante collegato a purchase: update prezzo/metodo; variante manuale | Sul collegato entrambi vietati; sul manuale aggiornamenti consentiti dal DTO; niente variazione silenziosa dei conti dell'acquisto. | API D |
| PAR-16 | Assegna, sostituisce o svuota membershipId manuale; ID sconosciuto | Riferimento aggiornato o rimosso; ID sconosciuto rifiutato; verificare statistiche utenti unici e vecchi ingressi, Q-07. | API Q |
| PAR-17 | Delete partecipante già entrato o con purchase | Verificare cosa resta in scan/purchase/attended_events e come cambiano i conti; non assumere cascata o rimborso: Q-07. | API Q |
| PAR-18 | Varianti riduzione, consenso, genere e probabilità assenti/presenti | Campi persistiti come da DTO; riduzione non equivale a inventare un nuovo importo; distribuzioni senza moltiplicare i soci. | Seed/API D |

### Acquisti, cattura e idempotenza

Fonti: [event_payment_service.py](../../../mcp-backend/functions/services/payments/event_payment_service.py),
[order.py](../../../mcp-backend/functions/models/order.py),
[event_purchase.py](../../../mcp-backend/functions/models/event_purchase.py),
[enums.py](../../../mcp-backend/functions/models/enums.py),
[purchases_service.py](../../../mcp-backend/functions/services/payments/purchases_service.py).

| ID | Preparazione e operazione | Esito da verificare e impatto sui dati/statistiche | Prova/stato |
| --- | --- | --- | --- |
| PAY-01 | Create ordine con gateway fake riuscito | Persistenza ordine non catturato e totale; nessun acquisto/partecipante/ingresso ancora creato. | API D |
| PAY-02 | Capture COMPLETED/COMPLETED con ID e importo uguale | Ordine captured e purchase_id collegato; un acquisto e i partecipanti previsti; tessere solo per target; statistiche eleggibili aumentano. | API D |
| PAY-03 | Ogni stato `FAILED`, `CANCELLED`, `VOIDED`, `REFUNDED`, `DECLINED`, `ERROR` in status; poi solo in capture_status | Fixture storiche isolate per verificare esclusioni; non creare iscrizioni riuscite da un tentativo fallito. Differenza generale/evento in Q-04. | Seed/API Q |
| PAY-04 | Rimborso sintetico dopo acquisto completato con partecipanti preesistenti | Metriche acquisti escludono la riga secondo filtro; non presumere cancellazione automatica dei partecipanti/scan. Riconciliare biglietti, iscritti e ingressi. | API D |
| PAY-05 | Capture con status non completato, capture ID assente o capture_status non COMPLETED | Rifiuto, aggiornamento stato ordine dove previsto; nessun nuovo acquisto/provisioning. Gateway fake, non richieste live invalide. | Locale D |
| PAY-06 | Ritenta capture di ordine terminale COMPLETED con purchase_id | Stesso purchase_id; nessuna seconda capture, quota, iscrizione o incremento dello sconto. | API D |
| PAY-07 | captured vero ma purchase assente/provisioning incompleto | Conflitto `ORDER_PROVISIONING_INCOMPLETE`; nessuna nuova capture o tentativo automatico di incassare. | Locale D |
| PAY-08 | Provider create/capture fallisce, HTTP non riuscito o create senza order ID | 502 per errore provider gestito; nessuna falsa conferma di acquisto. Conservare fatti già catturati se fallisce un passo successivo. | Locale D |
| PAY-09 | Importo capture diverso dall'ordine oltre 0,01; confine tolleranza | Dopo capture riuscita persiste captured prima dell'errore; non crea acquisto/provisioning e non ricattura al retry. Verificare esattamente il confine. | Locale D |
| PAY-10 | Importo catturato non parsabile, totale assente o final_capture falso | Codice attuale salta certi controlli o avvisa: non considerarli una validazione riuscita degli importi. Casi di anomalia Q-03. | Locale Q |
| PAY-11 | Evento termina tra create e capture; ordine mancante o senza eventId | Evento concluso bloccato prima di PayPal; ordine mancante 404, evento ordine mancante errore; nessun nuovo incasso fake. | Locale D |
| PAY-12 | Due capture simultanee dello stesso ordine non ancora catturato | Una sola cattura/provisioning come requisito; verificare idempotency key e scritture, non basta retry sequenziale. Non dimostrato dalla lettura. | Locale D |
| PAY-13 | Status/capture_status vuoti, PENDING o sconosciuti; ref_id o participants_count assenti/zero | Caratterizzare eleggibilità attuale, che non richiede sempre COMPLETED e diverge fra servizi; rifiutare false equivalenze con incassi definitivi: Q-04. | Locale Q |
| PAY-14 | Create/update stato/delete acquisto tramite admin | Risultati e 404/validazioni da DTO; trigger ricalcola statistiche. Non presumere che aggiornare stato avvii PayPal, annulli biglietti o faccia rimborso. | API D |

### Sconti e importi

Fonti: [discount_code_service.py](../../../mcp-backend/functions/services/payments/discount_code_service.py),
[discount_code_repository.py](../../../mcp-backend/functions/repositories/discount_code_repository.py),
[event_payment_service.py](../../../mcp-backend/functions/services/payments/event_payment_service.py).

| ID | Preparazione e operazione | Esito da verificare e impatto sui dati/statistiche | Prova/stato |
| --- | --- | --- | --- |
| DIS-01 | Percentuale 50% su 20; fisso 5 su 20; prezzo fisso 10 su 25 | Prezzi finali 10, 15, 10; sconti 10, 5, 15. Fee separata e arrotondamenti espliciti. | Seed/API D |
| DIS-02 | Percentuali 0/100/>100; fisso 0/=prezzo/>prezzo; prezzo fisso 0/=prezzo/>prezzo; valori negativi | 100%, fisso uguale prezzo e prezzo fisso 0 ammessi dal calcolo; invalidi rifiutati senza totale negativo. Verificare esito checkout a totale zero separatamente. | Locale D |
| DIS-03 | Codice inesistente, altro evento, inattivo, esaurito; maiuscole/spazi | Invalidi non applicati; normalizzazione codice corretta; nessuna scrittura usedCount durante sola validazione. | API D |
| DIS-04 | Codice con 1 partecipante; poi 2 o più | Singolo ammesso se altri requisiti validi; gruppo rifiutato. Non applicare sconto del singolo a tutto il gruppo. | API D |
| DIS-05 | Codice riservato a email/socio; identità corretta, diversa o socio assente | Solo destinatario corrispondente ammesso; email normalizzata; mismatch e membershipId incompatibile rifiutati. | API D |
| DIS-06 | Ultimo utilizzo disponibile; due capture concorrenti | usedCount non supera maxUses; errore su ultimo claim perso; rilevare eventuale incasso già avvenuto prima del claim e provisioning incompleto. | Locale D |
| DIS-07 | Capture riuscita, fallita, retry terminale | Incremento solo al claim nel flusso; nessun doppio utilizzo al retry terminale; guasto dopo claim documentato senza fingere rollback. | Locale D |
| DIS-08 | Nuovo socio ONLY_MEMBERS, quota tessera configurata, con/senza sconto e fee | Verificare formula corrente: `_compute_total` usa solo prezzo+fee; con sconto totale final_price+fee. Decidere intenzione della quota, Q-03. | Locale Q |

### QR, scanner, ingressi e annullamenti

Fonti: [entrance_service.py](../../../mcp-backend/functions/services/entrance_service.py),
[entrance_scan_repository.py](../../../mcp-backend/functions/repositories/entrance_scan_repository.py),
[entrance_api.py](../../../mcp-backend/functions/api/entrance/entrance_api.py),
[scanner UI](../../../mcp-website/app/scan/%5Btoken%5D/route.js).
Il QR contiene l'ID socio. Il token scanner associa la sessione a un evento;
non è il biglietto e non autorizza da solo l'ingresso.

| ID | Preparazione e operazione | Esito da verificare e impatto sui dati/statistiche | Prova/stato |
| --- | --- | --- | --- |
| QR-01 | Admin genera token per evento esistente; evento inesistente | 201 con token opaco e scadenza 12 ore; inesistente 404; nessun ingresso ancora registrato. | API D |
| QR-02 | Verify token valido, inesistente, disattivato, scaduto | Valido 200; altri 401 con reason not_found/inactive/expired. Confine expires_at e fuso in clock locale. | Locale D |
| QR-03 | Socio valido, iscritto all'evento dello scanner, mai entrato | validate HTTP 200 result valid; un solo scan e participant.entered vero; conteggi iscritti invariati, ingressi +1. | API D |
| QR-04 | Seconda scansione sequenziale; poi due scanner simultanei | already_scanned sul duplicato; un solo documento per socio/evento; mai doppio ingresso. Verificare anche HTTP/result e timestamp. | Locale D |
| QR-05 | Token non valido; ID socio inesistente; flag socio falso; socio non iscritto a questo evento | HTTP 200 con result rispettivamente invalid_token/invalid_member_not_found/invalid_membership/invalid_no_purchase; nessuno scan creato. | API D |
| QR-06 | Socio iscritto altrove; stesso QR usato negli eventi A e B | Rifiuto nel non iscritto; ingressi indipendenti dove iscritto; nessun blocco globale del QR. | API D |
| QR-07 | Admin ingresso manuale, ripetizione, undo, nuovo ingresso | result entered/already_entered/undone/entered; manual+operator persistiti; scan e flag riallineati; conteggio +1/0/-1/+1. | API D |
| QR-08 | Manuale per socio non valido ma partecipante esistente; partecipante assente | Il manuale attuale non applica check del flag socio; assente 404. Override distinto dal rifiuto scanner. | API D |
| QR-09 | Disattiva token già attivo/inattivo; poi scanner riprova | Token inattivo, seconda chiamata già inattivo; ingressi precedenti conservati, nuove scansioni rifiutate. | API D |
| QR-10 | participant.entered vero senza scan; scan presente con entered falso | Scanner usa lo scan come fonte anti-duplicato; verificare riallineamento o divergenza anziché contare due ingressi. Anomalie isolate, Q-05. | Locale Q |
| QR-11 | Stesso socio con più partecipazioni consentite nello stesso evento | Un solo scan per socio/evento; controllare quale participant riceve entered e come differiscono iscritti/biglietti/ingressi, Q-08. | Locale Q |
| QR-12 | Guasto dopo create_scan ma prima di update_entered; retry | Nessun secondo scan; rilevare flag rimasto falso e conteggi differenti. Non assumere transazione tra le due scritture. | Locale Q |
| QR-13 | QR illeggibile, valore vuoto, testo arbitrario/URL invece di ID socio | UI nessuna falsa conferma; API errore DTO o socio non trovato; il testo QR non viene interpretato come URL da seguire. | API/UI D |
| QR-14 | Scanner senza permesso camera, rete assente, token invalidato mentre aperto | UI mostra errore/riattivazione prevista; nessun ingresso locale inventato. Test camera su dispositivo necessario oltre alle API. | UI D |
| QR-15 | Ingressi storici distribuiti prima/dentro/dopo finestra, mezzanotte, bordo dei 30 minuti | Conteggi e cumulativi per finestra/fuso esatti; fuori finestra esclusi dal grafico ma non dal totale scan raw: Q-05. | Seed/API Q |

### Statistiche: oracoli e riconciliazione

Fonti: [stats_service.py](../../../mcp-backend/functions/services/core/stats_service.py),
[analytics_service.py](../../../mcp-backend/functions/services/core/analytics_service.py),
[analytics_snapshot_service.py](../../../mcp-backend/functions/services/core/analytics_snapshot_service.py),
[analytics_trigger.py](../../../mcp-backend/functions/triggers/analytics_trigger.py).
Le formule attuali sono specifiche per endpoint: non chiamare tutte le metriche
«vendite» e non imporre uguaglianze fra grandezze diverse.

| ID | Preparazione e operazione | Esito da verificare e impatto sui dati/statistiche | Prova/stato |
| --- | --- | --- | --- |
| STA-01 | Conta soci totali, flag validi e membership_years per anno | Totale iniziale 4000; attivi = flag veri; filtro annuale = anno nell'indice, non numero di rinnovi/partecipazioni. | Seed/API D |
| STA-02 | Conta eventi, iscrizioni, soci unici e biglietti acquistati | Eventi iniziali 50; iscritti = documenti participant; unici deduplicati per socio/email; biglietti da participants_count degli acquisti eleggibili. | Seed/API D |
| STA-03 | Matrice status/capture_status, tipo event/membership, ref_id presente/assente e count >0/0 | Filtro evento richiede tipo evento, ref_id e count positivo e nessuno stato invalido; legacy generale controlla solo status: Q-04. | Locale Q |
| STA-04 | Un acquisto gruppo da 2 biglietti, lordo 44, fee sintetica 1,50, netto 42,50 | Acquisti +1; biglietti +2; lordo +44, netto +42,50, commissioni +1,50; nessun raddoppio per le due persone. | Seed/API D |
| STA-05 | Stessa riga completata diventa REFUNDED o capture_status DECLINED | Metriche evento escludono lordo/netto/biglietti; iscrizioni e scan non spariscono per il solo cambio stato. Ricalcolo senza saldi residui. | API D |
| STA-06 | Omaggi, inserimenti manuali pagati e biglietti website nello stesso evento | Omaggi da payment_method; incassi online da Purchase eleggibili. Non inventare acquisti per contanti/iban; chiarire se metriche incassi desiderate devono includerli: Q-04. | Seed/API Q |
| STA-07 | Nessun acquisto valido, nessun ingresso, capienza zero/assente | Totali zero, nessuna divisione per zero; media unitario e percentuali secondo formula; confrontare null/zero dei DTO. | Seed/API D |
| STA-08 | Ticket tiers con 1/2/3/4 prezzi, prezzi vicini, gruppi e sconto | Classificazione e tolleranze come da algoritmo; somme tier = biglietti/lordo/netto eleggibili, senza sommare anche la membership come biglietto. | Locale D |
| STA-09 | Vendite su giorni/mesi diversi, cambio mese/anno Europe/Rome | Bucket temporali e this_month corretti; nessuna inclusione per sola ora ignorando la data della vendita. | Seed/API D |
| STA-10 | Ingressi scanner/manuali più flag entered e scan fuori finestra | Riconciliare conteggio raw, flag, grafico e KPI snapshot; finestra snapshot 22:00-06:00 distinta da endpoint configurabile: Q-05. | Seed/API Q |
| STA-11 | Membri nuovi/ritornanti, anni diversi; persone ripetute in più eventi | Retention e trend secondo fonte di ciascun endpoint; persone uniche non equivalgono al totale iscrizioni; verificare ordinamento eventi e anni. | Seed/API D |
| STA-12 | Età nelle fasce previste, genere male/female/unknown, birthdate mancante/invalida | Distribuzioni con bucket unknown e percentuali coerenti; nessun provider di genere live; confini d'età confrontati indipendentemente, Q-06. | Locale Q |
| STA-13 | Create/update/delete purchase, participant, membership, scan; retry trigger | Snapshot ricalcolati dopo job completato, nessun doppio incremento. Azione rifiutata lascia conti invariati; distinguere lettura stale da finale. | Locale D |
| STA-14 | Rebuild completo ripetuto; job già queued/processing/stale/failed | Deduplica/ripresa secondo contratto job; stessi aggregati a dati invariati; errore non dichiarato PASS. | Locale D |
| STA-15 | Evento cancellato con snapshot esistente | Rebuild restituisce exists false e grafici vuoti; verificare indice/dashboard e dati figli separatamente, Q-07. | API Q |

### Permessi, comunicazioni e manutenzione dei dati di prova

Fonti: [decoratori API](../../../mcp-backend/functions/api/decorators/__init__.py),
[auth_service.py](../../../mcp-backend/functions/services/core/auth_service.py),
[registration_trigger.py](../../../mcp-backend/functions/triggers/registration_trigger.py),
[cleanup_trigger.py](../../../mcp-backend/functions/triggers/cleanup_trigger.py).

| ID | Preparazione e operazione | Esito da verificare e impatto sui dati/statistiche | Prova/stato |
| --- | --- | --- | --- |
| OPS-01 | Admin, socio autenticato, account senza socio, anonimo e token invalido su rispettive API | Ruoli rispettati; admin assente/non admin rifiutato come da decorator (attualmente 401); nessuna scrittura non autorizzata. Scanner pubblico richiede proprio token, non claim admin. | API D |
| OPS-02 | GET/POST errato e JSON mancante/invalido/campi extra sugli endpoint esaminati | 405 o 400 secondo contratto; messaggio e nessun side effect; non estendere genericamente extra=forbid ai DTO che ignorano extra. | API D |
| OPS-03 | Tessera/ticket non inviato, già inviato, flag invio falso; retry trigger | Nessuna mail durante seed; test locale della deduplica e dei flag. PDF può essere generato anche con send falso: prevedere volumi e metadati Storage. | Locale D |
| OPS-04 | Invio ticket/tessera a alias consentito; destinatario escluso; errore provider | Su staging solo selezionati; escluso bloccato; errore non segnato come consegna; ricezione/allegati verificati in casella dopo autorizzazione invii. | API/casella X |
| OPS-05 | Omaggi: bulk con già inviato/non inviato; resend singolo | Bulk salta già inviati, singolo può reinviare; controllare sent/skipped/failed e flag con provider fake. | Locale D |
| OPS-06 | Wallet/Sender disabilitati e gender fake durante seed | Nessuna attività live su Pass2U/Sender; guasti fake non cancellano soci/partecipazioni. Verifica wallet live separata e rinviata. | Locale D |
| OPS-07 | Ordine non catturato prima/al/dopo 24 ore; captured; timestamp assente | Pulizia locale preserva captured; verificare confine e chiavi `createdAt`/`created_at`, attualmente discordanti, Q-09. | Locale Q |
| OPS-08 | Token scanner scaduto da meno/esattamente/più di 7 giorni | Cleanup rimuove solo oltre soglia; scan storici non eliminati dal cleanup token. | Locale D |
| OPS-09 | Rigenera seed con stesso seed RNG, poi interruzione e ripresa | Stessi ID/relazioni/conteggi; no duplicati; errore parziale esplicito; guard progetto/bucket rifiuta produzione. Test locale prima di cloud. | Locale D |
| OPS-10 | App su dataset completo: ricerca, filtri, ordinamento, paginazione | Risultati completi senza perdere/duplicare righe fra pagine; filtri socio/anno/evento/stato confrontati col manifesto. Misurare tempi, senza chiamarla ancora prova concorrente. | API/UI D |

### Contratti da caratterizzare prima di dichiarare i casi superati

Questi rilievi derivano dalla lettura, non da riproduzioni runtime. Non sono
correzioni incluse nella matrice; il generatore non deve nasconderli scegliendo
solo dati che li evitano. La prova deve riportare comportamento osservato e
regola richiesta separatamente; finché divergono il caso non è PASS.

| Punto | Evidenza attuale e decisione/verifica necessaria | Casi collegati |
| --- | --- | --- |
| Q-01 | Checkout usa anno in membership_years, scanner e attivi usano subscription_valid. Date non sono un controllo unico di scadenza. Testare combinazioni e chiarire la regola uniforme desiderata. | MEM-03, MEM-04 |
| Q-02 | Guard attiva evento blocca ended/termine temporale; nessun blocco sold_out/coming_soon o capienza trovato nel checkout esaminato. Distinguere blocco UI e garanzia backend. | EVT-03, EVT-04 |
| Q-03 | `_compute_total` non somma membership_fee; importi non parsabili possono saltare controllo capture. Verificare intenzione quota tessera e comportamento ai confini, senza assumere di dover aggiungere una quota. | PAR-03, PAY-10, DIS-08 |
| Q-04 | StatsService filtra solo status, analytics evento/snapshot filtrano anche capture_status, tipo, ref_id e count. Stati vuoti/non definitivi possono passare i filtri; incassi manuali da participant non sono automaticamente Purchase. Stabilire significato di ogni metrica. | PAY-03, PAY-13, STA-03, STA-06 |
| Q-05 | Entrate raw, flag participant e scansioni nella finestra non sono lo stesso insieme. Snapshot usa finestra fissa 22:00-06:00 e KPI entered dalla somma bucket; endpoint diretto può contare flag/scan differenti. Scritture scan/flag separate. | QR-10, QR-12, QR-15, STA-10 |
| Q-06 | Diverse funzioni età usano giorni/365; verificare maggiorenne/over21 e fasce statistiche rispetto al calendario, non copiando la formula come oracolo. | MEM-06, PAR-09, STA-12 |
| Q-07 | Delete evento/partecipante e riassegnazione socio non dimostrano cascata su scan, purchase e storico. Merge esaminato riallinea partecipanti; verificare anche scan e membership_ids degli acquisti. Nessuna cancellazione reale in questa fase. | EVT-09, PAR-16, PAR-17, STA-15 |
| Q-08 | allow_duplicates permette più righe socio/evento, ma scan ha chiave membershipId/evento e update_entered lavora su un participant. Definire rapporto biglietti, persone e ingressi. | PAR-06, QR-11 |
| Q-09 | Order serializza createdAt, cleanup legge created_at e considera timestamp assente eliminabile per non captured. Riprodurre con un ordine fresco negli emulatori. | OPS-07 |

### Combinazioni obbligatorie e prove esistenti

Non basta generare ogni flag separatamente. Espandere almeno questi incroci:

- Le quattro modalità evento con socio corrente, scaduto e assente; gruppi
  omogenei e misti; percorso pubblico rispetto all'override admin.
- Flag subscription_valid vero/falso con anno corrente presente/assente;
  applicare gli stessi dati a checkout, QR e statistiche attivi.
- Stato acquisto valido/invalido con capture_status valido/invalido; tutte le
  sei varianti invalidate singolarmente, poi entrambe invalide; ref_id/count
  mancanti in fixture isolate. Rimborso dopo partecipazione/ingresso già presenti.
- Iscrizione presente/assente con scan presente/assente e flag entered vero/falso;
  solo combinazioni realistiche nel seed ordinario, incoerenze in copie isolate.
- Acquisto singolo/gruppo con sconto e tessera necessaria/non necessaria;
  allow_duplicates vero/falso con contatti duplicati e QR condiviso per socio.
- Confini cronologici: cambio anno, compleanno, mezzanotte/ora legale, termine
  evento, scadenza token, bucket ingresso, cleanup ordine e token.

I test esistenti sono evidenza delle aspettative già scritte, non un esito
attuale. Fonti controllate: test unitari di participants, discount_code,
event_payment, memberships, analytics_snapshot; integrazioni entrance,
participants e stats. Esempi rintracciabili:
`test_capture_order_event_completed_retry_is_idempotent`,
`test_capture_order_event_partial_capture_fails_without_recapturing`,
`test_manual_entry_undo_clears_both_collections`,
`test_participant_check_detects_duplicate_in_payload`,
`test_validate_discount_code_rejects_multi_participant_purchase`,
`test_enqueue_deduplicates_queued_jobs`.
Mappare ciascuna istanza al test riutilizzato o alla nuova prova, registrando
PASS/FAIL solo con comando/azione, data ed evidenza effettiva. Prove nuove
richieste soprattutto per incroci, errori parziali, concorrenza e rilievi Q.

### Come dimostrare gli esiti

- Separare dati storici persistenti e azioni da eseguire. Una seconda scansione,
  una race o un pagamento rifiutato non sono dimostrati inserendo documenti:
  richiedono richieste ai servizi/API e verifica degli effetti.
- `EntranceScan` rappresenta l'ingresso accettato, non un audit di ogni tentativo
  QR. Non aggiungere falsi record di ingresso per le scansioni rifiutate; gli
  esiti dei tentativi appartengono al rapporto del test.
- Incrociare le variabili che cambiano le regole, includendo combinazioni limite.
  Mantenere il dataset ordinario coerente; anomalie intenzionali e dati non
  validi devono essere casi identificati e isolati, con pulizia dopo la prova.
- Preparare insieme al dataset un prospetto indipendente dei conteggi e importi
  attesi per evento e globali. Usare importi in centesimi/Decimal nel generatore;
  serializzare secondo i tipi dei modelli, senza errori da somme in virgola mobile.
- Confrontare risposte API e snapshot statistici dopo il completamento dei
  ricalcoli. Verificare anche aggiornamento/cancellazione, retry e assenza di
  duplicati. Non usare la stessa funzione di analytics per calcolare l'atteso.
- Non assumere come corretta ogni risposta attuale: una divergenza tra regola
  attesa, codice e dati deve diventare una segnalazione, non essere nascosta
  adattando i conteggi del seed. Le correzioni applicative restano separate.
- Consegnare una matrice con coperto, fallito o non ancora verificato per ogni
  caso individuato. Nessuna promessa di coprire ogni combinazione cartesiana
  prima di avere mappato rami e vincoli effettivi.

Riferimenti iniziali: `models/enums.py`, `models/membership.py`,
`models/event_participant.py`, `models/order.py`, `models/event_purchase.py`,
`models/entrance_scan.py`, `models/scan_token.py`, `domain/event_rules.py`,
`domain/membership_rules.py`, `services/entrance_service.py`,
`services/events/participants_service.py`, `services/payments/event_payment_service.py`,
`services/core/analytics_service.py`, `services/core/analytics_snapshot_service.py`
e relativi test, tutti sotto `mcp-backend/functions/`.

## Sequenza operativa

1. Preparare strumenti locali e dataset senza accessi cloud in scrittura.
   Utente admin e soci campione; tessere valide/scadute; eventi attivi, conclusi
   e sold-out; acquisti storici sintetici con esiti differenti. Relazioni tra
   Auth, soci, acquisti ed eventi coerenti. Nessun ID reale PayPal/Pass2U copiato.
   Per testare un pagamento, creare un nuovo ordine PayPal sandbox tramite l'app.
   Confrontare modelli, DTO, lettori e scrittori della versione da collaudare
   con un campione limitato dei documenti di produzione: i dati esistenti
   possono includere forme legacy, non sono da soli il contratto del seed.
2. Produrre un inventario in sola lettura di Firestore, Auth e Storage:
   collezioni, conteggi e risorse interessate, senza esportare dati personali
   nel rapporto. Verificare anche Functions/trigger e configurazione attualmente
   distribuita: il codice locale non dimostra come il vecchio staging opera.
3. Eseguire dry-run: progetto e bucket esatti, operazioni previste, quantità
   di elementi rimossi e creati, gestione delle interruzioni. Preparare e
   dimostrare negli emulatori reset e caricamento ripetibili.
4. Presentare il rapporto concreto al proprietario. Solo dopo autorizzazione
   eseguire le operazioni cloud: isolare prima gli effetti dei trigger/provider,
   sostituire il dataset e verificare il risultato. Eventuale snapshot di
   recupero dei dati legacy deve restare fuori da Git e dai dati di test.
5. Pubblicare una versione precisa approvata e provare login, ruoli, eventi,
   acquisto sandbox e tessera PDF/email su destinatari consentiti. MailerSend
   inizialmente disabilitato, poi modalità staging con allowlist verificata.
   Wallet Pass2U resta separato finché account/modalità di prova non sono validati.

## Implementazione locale — 2026-11-07

`scripts/staging/generate.py` usa esclusivamente un RNG locale con seed e data
espliciti e i model del backend, senza client Firebase o chiamate ai provider.
Genera il dataset ordinario collegato, un manifesto con contatori in centesimi
e hash dei documenti, e 12 sostituzioni isolate per i sei stati acquisto
invalidi applicati separatamente a `status` e `capture_status`.

Gli output sono privati sotto `.local/staging/dataset/`, esclusi da Git:
`records.jsonl`, `manifest.json`, `isolated-cases.json`. I timestamp nativi
sono serializzati con il tag `$timestamp` per conservarne il tipo durante
l'importazione. Nomi/cognomi provengono da liste inventate; telefono con
prefisso sintetico, email costruite dalla configurazione locale approvata.
Nessun valore personale di produzione viene usato. Nessuna allowlist è ampliata.

Esecuzione dalla cartella `core-ws2`:

```bash
.venv/bin/python scripts/staging/generate.py --seed 42 --as-of 2026-11-07 --recipients-config .local/staging/recipients.json
```

Verifica offline dell'export, senza scrivere su alcun database:

```bash
.venv/bin/python scripts/staging/load_emulator.py --directory .local/staging/dataset
```

Il caricatore accetta solo `demo-mcp-local`/`demo-mcp-test` e IP letterale
`127.0.0.1`. Prima di importare richiede il relativo emulator hub e rifiuta
una sessione con Functions attive. Il solo flag email falso non impedirebbe
infatti ai trigger di generare migliaia di PDF o arricchire i partecipanti.
Usa credenziali anonime, verifica hash/namespace e rilegge i documenti scritti.
Non cancella dati, non pulisce altri namespace e non crea account Auth.
L'upsert è ripetibile per gli stessi ID; documenti preesistenti non presenti
nell'export fanno fallire il controllo prima delle scritture. Il controllo
viene ripetuto dopo l'importazione per non dichiarare successo con residui.
Usare l'emulatore dedicato vuoto, non un database con altri dataset sintetici.

Prima prova reale affidata a Vittorio, un'attività alla volta:

```bash
nvm use && .venv/bin/python scripts/staging/test_emulator.py
```

Avvia solo Firestore su 8180 e hub su 4480, progetto demo, importa l'export,
verifica dati e conteggi rileggendo e spegne i servizi. Se le porte sono
occupate si ferma; non termina processi già attivi. Questa prova non testa
ancora Functions, Auth, API, invii, PDF o gli esiti dei 105 scenari.
La configurazione `firebase.synthetic-emulator.json` risiede nella radice
per riutilizzare `firestore.rules` senza violare i limiti della CLI sui percorsi.

Verifiche offline eseguite dal coordinatore: 33 test degli strumenti passati,
configurazione risolta dalla CLI Firebase installata, scanner segreti senza
finding. Unica review Sol high conclusa; corretti percorso regole, residui
tra dataset e durata/cronologia dei token. I token esportati esistono solo
per eventi storici, sono disattivati e hanno durata di 12 ore effettive.

Export prodotto con seed 42 e riferimento 2026-11-07: 4000 soci, 50 eventi,
21701 partecipanti, 7076 acquisti completati, 13751 ingressi, per 53684
documenti totali. Non includono le 12 sostituzioni isolate. Nessuna scrittura cloud.

Prima prova riferita da Vittorio: fallita con `PermissionDenied` nella query
iniziale, prima dei batch di importazione. Log e SDK installato mostrano che
la chiamata RunQuery diretta ometteva i metadati emulatori aggiunti normalmente
dal client. Corretta propagazione di `client._rpc_metadata`, senza modificare
le regole. Regressione vista fallire e poi passare; suite strumenti aggiornata
a 34 test passati. Successiva prova reale riuscita, come riportato sotto.

Limiti espliciti di questa prima implementazione: gli stati pagamento invalidi
sono fixture isolate da applicare a una copia del baseline; sconti, guasti,
concorrenza e casi Q richiedono le successive prove/API. Il manifesto mantiene
tutte le righe API come `not_run`; rappresentare dati di uno scenario non
equivale a superare il test. Nessun writer cloud o reset staging implementato.

## Prima batteria API e statistiche — 2026-11-07

Preparati 23 test parametrizzati in
`mcp-backend/functions/tests/synthetic_api/test_purchase_entrance_stats.py`,
con fixture dedicate in `tests/synthetic_api/conftest.py`.

| Famiglia | Prove preparate | Matrice interessata |
| --- | ---: | --- |
| Checkout gruppo, capture, retry e snapshot | 1 sequenza | PAY-01/02/06, PAR-05, STA-02/04/13 |
| Cambio stato acquisto, esclusione e ripristino conti | 6 stati | PAY-03/04/14, STA-05 |
| Solo capture_status invalido e confronto statistiche | 6 stati | PAY-03, STA-03; caratterizzazione Q-04 |
| Risposta provider non completata | 2 varianti | PAY-05 |
| QR valido, duplicato, manuale, undo e nuovo ingresso | 1 sequenza | QR-03/04/07, STA-10 |
| Token/socio/iscrizione non validi | 6 varianti | QR-02/05/06 |
| Evento vuoto e capienza zero | 1 caso | EVT-05, STA-07 |

Le richieste passano dal test client Flask agli handler HTTP decorati,
con vere letture/scritture Firestore nell'emulatore. I valori attesi
finanziari sono espliciti (44,00 lordi, 1,50 commissioni, 42,50 netti,
2 biglietti e 1 acquisto), non ricavati dalle funzioni di analytics.
L'admin è simulato dalle fixture test esistenti: non si verificano token JWT,
trasporto di Functions distribuite o provider reali. Non vengono avviate
Functions né trigger e non si carica il dataset massivo in questa prova.
I ricalcoli degli snapshot sono espliciti prima della lettura dell'API.

Ogni caso parte con database dedicato vuoto; le fixture verificano progetto
demo, endpoint loopback e hub privo di Functions prima delle mutazioni.
Pulizia limitata ai documenti creati dal caso nel database già verificato.
PayPal usa esclusivamente un gateway fake con esiti controllati; nessuna
email o credenziale live. CI aggiunta per questa batteria oltre allo smoke
Firebase già esistente, che resta una prova diversa.

Comando per Vittorio, dalla cartella `core-ws2`:

```bash
nvm use && .venv/bin/python scripts/staging/test_emulator.py --api
```

Avvia solo Firestore 8180/hub 4480, esegue le prove, produce
`.local/staging/api-results.xml` e spegne gli emulatori. Atteso: 23 test
passati, nessun errore e codice 0. La sola raccolta dei test non è esecuzione;
l'esito reale resta da confermare. I 6 casi di caratterizzazione Q-04 possono
passare dimostrando la differenza fra metriche: non risolvono la divergenza
e non chiudono la relativa decisione di prodotto. Le 23 istanze non equivalgono
automaticamente a 23 righe complete della matrice da 105 scenari.

### Ripresa e verifica offline — 2026-11-09

Il rilievo parziale della review interrotta è confermato: le due famiglie
sugli stati non devono ricavare i casi da `PurchaseStatus.invalid_statuses()`.
Ora parametrizzano esplicitamente FAILED, CANCELLED, VOIDED, REFUNDED,
DECLINED ed ERROR; un'omissione nella funzione applicativa non può più
eliminare il relativo scenario.

Verifiche del coordinatore: 39 test strumenti e 35 test unitari collegati
ad acquisti/statistiche passati; 23 casi API raccolti senza esecuzione;
scanner segreti zero segnalazioni e `git diff --check` pulito. Warning delle
dipendenze: deprecazione HarfBuzz e fine supporto futuro Python 3.11 negli SDK
Google. Review finale Sol high conclusa senza rilievi e accettata dal
coordinatore; il revisore ha rieseguito i 5 test del runner, passati. Prova
API negli emulatori eseguita da Vittorio con il comando sopra: **23 passati**,
un warning HarfBuzz, codice 0 e arresto pulito degli emulatori. Esito riportato
dal proprietario, non rieseguito dal coordinatore. Prima batteria verificata;
le 23 istanze non chiudono automaticamente 23 righe della matrice completa
né la decisione Q-04. Nessuna scrittura cloud.

### Copertura dopo la prima batteria — 2026-11-09

I 105 ID descrivono scenari con più varianti; i 23 test eseguiti non sono
23 righe complete e non consentono di dedurre «82 scenari mancanti».
Il caricamento/rilettura dei 53684 documenti prova il dataset, non i flussi
API sul dataset completo. I test unitari preesistenti sono evidenze distinte.

| Area e perimetro | Dimostrato dalla prima batteria API | Ancora da verificare nel perimetro della matrice |
| --- | --- | --- |
| Soci, 15 ID MEM-01…15 | Due soci validi usati come fixture; non è una prova completa dei flussi membership. | Create/rinnovi, contatti duplicati, anni/flag/date, età, account, merge, invalidazione annuale e consenso. |
| Eventi, 10 ID EVT-01…10 | EVT-05: evento vuoto con capienza zero e percentuali finite. | Variante capienza assente; stati, fine evento, capienza, fusi/date, listing, CRUD e distinzione DTO pubblico/admin. |
| Partecipanti, 18 ID PAR-01…18 | PAR-05: un acquisto con due partecipanti, payer distinto e nessun raddoppio dei totali. | Riferimenti e identità completi, modalità evento, soci nuovi/scaduti, duplicati, DTO, età/genere, inserimenti manuali, update/delete e campi facoltativi. |
| Pagamenti, 14 ID PAY-01…14 | PAY-01/02: create/capture riuscite su gruppo di soci esistenti; PAY-06: retry terminale senza seconda capture; PAY-03/04: esclusione dei sei stati invalidi e ripristino; PAY-05: due stati provider rifiutati; PAY-14: update stato. | Totale/riferimenti ordine e provisioning tessere completo, ID capture assente, errori provider, provisioning interrotto, importi/tolleranza, evento scaduto, capture simultanee, stati vuoti/PENDING/sconosciuti e CRUD admin completo. Le fixture di rimborso non eseguono un rimborso PayPal. |
| Sconti, 8 ID DIS-01…08 | Nessun flusso con sconto nella batteria API. | Formule, limiti, destinatari, gruppi, ultimo utilizzo concorrente, claim/retry e quota tessera. |
| Scanner, 15 ID QR-01…15 | QR-03/05: ingresso valido e rifiuti senza ingresso; QR-04: duplicato sequenziale; QR-07: manuale/ripetizione/undo/nuovo ingresso. | Token: contratto di generazione, verify e revoca; metadati manuali; concorrenza, stesso socio fra eventi, override manuale, incoerenze scan/flag, guasti intermedi, duplicati socio, finestre orarie, QR malformato e camera/rete UI. QR-02/06 non sono chiusi dai soli rifiuti su `/scan`. |
| Statistiche, 15 ID STA-01…15 | STA-04: 44 lordi, 1.50 fee, 42.50 netti e 2 biglietti; STA-02/05: conteggi del piccolo caso e variazioni stato; STA-03: divergenza capture_status fra generale/evento; STA-07: zeri; STA-10: flag/scan del caso base; STA-13: snapshot ricostruito esplicitamente. | Aggregati del dataset completo, matrice eleggibilità completa, omaggi/manuali, tiers, bucket temporali, retention, demografia, finestre ingressi, trigger reali/retry/job, rebuild ripetuti e cancellazioni. Il rebuild esplicito non verifica l'attivazione dei trigger. |
| Operazioni e permessi, 10 ID OPS-01…10 | Runner locale con provider fake e guardie; generatore/caricatore verificati separatamente. | Auth reale/ruoli, metodi/DTO, mail/PDF e flag invio, provider disabilitati nei singoli flussi, cleanup, ripresa dopo interruzione e app sul dataset completo. L'admin simulato non chiude OPS-01; guardie e importazione non chiudono tutte le varianti OPS-09. |

Priorità proposte per i prossimi blocchi, da discutere col proprietario prima
dell'implementazione:

1. **Pagamenti e sconti:** PAY-07…13, varianti PAY-05/08/09 e DIS-01…08.
   Prima errori e recupero sequenziali; capture e ultimo sconto concorrenti
   richiedono prove dedicate, non riuso del retry sequenziale.
2. **Permessi e ammissione:** OPS-01/02, EVT-02…04, PAR-02…10 e MEM-03…08.
   Distinguere regole attuali da quelle desiderate prima di cambiare comportamento.
3. **Coerenza dati e statistiche:** Q-04/05/07/08, scan/flag, trigger/job,
   merge/delete e riconciliazione sul dataset completo.
4. **Tempo e manutenzione:** Q-06/09, confini anagrafici, fine evento,
   cambio anno/ora legale e cleanup di ordini/token.
5. **Prove esterne:** UI camera/rete e dataset completo; Auth/trasporto
   distribuiti, sandbox PayPal, mail/PDF in staging solo ai relativi gate.

Decisioni aperte: Q-01 validità tessera; Q-02 disponibilità/capienza;
Q-03 quota tessera/importi; Q-04 significato delle metriche (divergenza
capture_status ora riprodotta); Q-05 ingressi e finestre; Q-06 età;
Q-07 cascata/riferimenti; Q-08 più iscrizioni per socio; Q-09 cleanup ordini.
Le caratterizzazioni non autorizzano correzioni implicite alle regole di prodotto.

### Blocco approvato — errori pagamenti API, 2026-11-09

Il proprietario ha approvato in chat il perimetro PAY-07, varianti PAY-05/08
e PAY-09. Esecuzione nativa nel worktree esistente, branch
`core-payment-failure-scenarios`, base `3690479` dopo merge PR #7.

- Estendere solo il gateway di test in `tests/synthetic_api/conftest.py`
  per risposte provider controllate e importi espliciti.
- Aggiungere scenari API nello stesso file di test: guasto locale prima/dopo
  creazione purchase con retry senza ricattura; create/capture provider
  fallite e ID assenti; importi 43.98/43.99/44.01/44.02 contro totale 44.00.
- Verificare HTTP, ordine persistito, purchase/partecipanti, statistiche e
  assenza di ulteriori chiamate capture nei retry di un incasso già registrato.
- Raccolta e test unitari offline, una review finale Sol high; Vittorio
  esegue la batteria negli emulatori. Commit dopo esito runtime.
- Nessuna modifica applicativa, concorrenza, sconti o operazione cloud.
  Eventuali bug applicativi vengono riportati prima della correzione.

Preparati 12 nuovi casi (35 totali): 2 interruzioni locali, 4 errori
provider HTTP/SDK, 2 identificativi assenti e 4 importi al confine.
Verifica offline del coordinatore: 29 test unitari collegati passati,
35 casi raccolti, scanner zero segnalazioni e whitespace pulito. Review
Sol high conclusa senza rilievi e accettata; confermati offline costruzione
ApiException, confini importi e correttezza dei conti quando la purchase
esiste ma i partecipanti non sono ancora creati.

Vittorio ha eseguito `scripts/staging/test_emulator.py --api`: **35 passati**,
un warning HarfBuzz, codice 0 e arresto pulito degli emulatori. Esito del
proprietario, non rieseguito dal coordinatore. Le 12 nuove istanze verificano
PAY-07 prima/dopo creazione purchase, le varianti PAY-05/08 con ID assenti
ed errori HTTP/SDK e PAY-09 ai quattro importi espliciti sopra. Nessuna
anomalia applicativa emersa da questi casi; restano fuori concorrenza,
sconti, provider reali e altre varianti della matrice. Nessuna modifica
alla CI: il runner esistente scopre automaticamente tutti i 35 casi.

## Vincoli generali e prove

- I comandi di reset/seed rifiutano ogni progetto/bucket diverso dallo staging
  indicato; il lettore di inventario produzione è separato e non scrive dati.
- Il seed non invia messaggi o crea pagamenti/pass esterni direttamente.
- Prima di ogni scrittura cloud, verificare o isolare i trigger esistenti:
  impostare `MAIL_MODE=disabled` sul computer non disabilita Functions già online.
- Nessuna password fissa locale o credenziale viene pubblicata o stampata.
- Re-run senza duplicati; fallimenti parziali espliciti; pulizie successive
  limitate al namespace sintetico, senza eliminare nuovi dati sconosciuti.
- Provare blocco dei destinatari non consentiti e assenza di dati personali
  del vecchio backup nel dataset nuovo. Inventariare anche altri canali di invio.
- Una review finale Sol high su Auth, destinatari e limiti della cancellazione.

Per ora: preparazione e piano. Le risorse online rimangono invariate.

Destinatari predisposti in `.local/staging/recipients.json`, escluso da Git:
casella base e quattro alias esatti per admin, socio valido, socio scaduto e
nuovo acquirente. Nessun indirizzo personale è riportato nel piano versionato.
La configurazione non crea account Auth né attiva invii o provider.

## Requisiti aggiunti dal proprietario — 2026-11-05

- Autorizzata la lettura della casella di test per verificare ricezione delle
  email. Collegare e verificare l'account corretto soltanto prima dei primi
  invii; limitare le ricerche ai destinatari staging e alla finestra della
  prova. Verificare arrivo, destinatario, contenuto atteso e allegati/link.
  Nessuna modifica di messaggi o etichette, nessun invio dalla casella e
  nessuna apertura automatica di link che attivino operazioni applicative.
- Proposta esplicita del proprietario: inventario in sola lettura del progetto
  produzione `mcp-website-2a1ad` per osservare la forma corrente dei dati.
  Campione limitato; rapporto aggregato con campi, tipi e varianti, evitando
  valori personali, ID dei documenti, URL e copie grezze nei log o in Git.
  Il seed contiene esclusivamente valori inventati e le caselle approvate.
- Il lettore produzione deve essere separato dagli strumenti di reset/seed,
  che continuano a rifiutare ogni progetto diverso dallo staging. Non
  allentare la protezione del writer per consentire l'inventario produzione.

Nessun accesso alla casella o al database di produzione è stato eseguito
durante questo aggiornamento del piano.

## Inventario in sola lettura — 2026-11-05

Autenticazione ADC verificata. Successivamente sono stati letti un campione
limitato di produzione e i metadati dello staging. Nessuna scrittura cloud
e nessun accesso alla casella email sono stati eseguiti.

- Produzione: 50 documenti campionati tra eventi, soci, acquisti, ordini e
  partecipanti. Rapporto locale con campi e tipi, senza valori o ID personali.
  Rilevate varianti legacy: il seed deve seguire anche i contratti correnti.
- Staging Firestore: 20 collezioni radice, 3607 documenti di primo livello;
  inoltre 1065 documenti nel gruppo `participants_event`. Inventario delle
  sottocollezioni ancora incompleto: questi conteggi non rappresentano il
  totale definitivo da cancellare.
- Staging Auth: 2 utenti, nessuno corrispondente ai destinatari di test.
- Il bucket Firebase dichiarato dalla configurazione SDK online è
  `mcp-website-dev-39539.firebasestorage.app`: 88 oggetti attivi osservati.
  Il riferimento locale al bucket `.appspot.com` restituisce NotFound e va
  corretto prima del collaudo. Un secondo bucket del progetto contiene 28
  oggetti attivi, incluso un marcatore di export; non presumere che sia
  interamente destinato al seed. Entrambi dichiarano soft delete di 7 giorni.
- Inventario Functions v1/v2 bloccato da HTTP 403 `SERVICE_DISABLED`.
  Questo non è una verifica dell'assenza di trigger. Non è stata attivata
  alcuna API. Verificare lo stato dal pannello del progetto prima del reset.
- Verifica manuale successiva del proprietario: nessuna Function distribuita
  su dev. Esito riferito dal proprietario, non verificato tramite API.
  Non serve attivare l'API per ripetere questo controllo. Resta da completare
  l'inventario dei dati e preparare il rapporto di reset prima delle scritture.

Rapporti dettagliati e script temporanei rimangono sotto `.local/staging/`,
esclusi da Git. Reset, seed cloud e deploy restano da preparare e autorizzare.

## Inventario completo — 2026-11-05

Questa rilevazione sostituisce i conteggi parziali precedenti. Ambito:
database Firestore del progetto, utenti Firebase Auth e oggetti nei bucket
Storage. Nessuna scrittura cloud, lettura aggiuntiva di produzione o accesso
alla casella email durante questo completamento.

### Firestore

Un solo database, `(default)`. Query globale su tutti i discendenti, con
proiezione del solo percorso documento: nessun campo applicativo scaricato.
Conteggio concluso senza troncamento, con un unico timestamp di lettura.

| Risorsa | Documenti |
| --- | ---: |
| Primo livello, su 20 collezioni radice elencate | 3607 |
| `participants/{contenitore}/participants_event` | 1065 |
| **Totale documenti esistenti** | **4672** |

Nessun altro livello o tipo di sottocollezione rilevato. I 17 documenti padre
dei contenitori partecipanti non esistono: Firestore conserva ugualmente i
discendenti. Questi percorsi padre non sono documenti da aggiungere al totale.
Una cancellazione limitata ai documenti padre esistenti perderebbe questi
partecipanti; il reset deve attraversare anche i discendenti senza padre.

### Firebase Auth

2 utenti, entrambi abilitati; 1 con claim `admin`. Nessuno usa gli indirizzi
di test approvati. Conteggio aggiornato e completo, senza salvare email o UID.

### Storage

Inventario paginato dei bucket, degli oggetti attivi, di tutte le versioni e
degli oggetti in soft delete. Nessun nome file o contenuto nel rapporto.

| Bucket | Oggetti attivi | Byte | Versioni non correnti | Soft deleted |
| --- | ---: | ---: | ---: | ---: |
| `mcp-website-dev-39539.firebasestorage.app` | 88 | 168438114 | 0 | 0 |
| `mcp-website-dev-39539` | 28 | 2914380 | 0 | 0 |
| **Totale** | **116** | **171352494** | **0** | **0** |

Il primo è il bucket Firebase confermato dalla configurazione SDK online.
Il secondo contiene un marcatore di export: decidere esplicitamente il destino
di tale archivio nel rapporto di reset; non è stato aperto o ripristinato.
Entrambi hanno versioning disattivato, nessuna retention policy vincolante
rilevata e soft delete di 604800 secondi (7 giorni). Un futuro delete degli
oggetti attivi non equivale quindi alla loro immediata eliminazione definitiva.

### Esito e limiti

- Inventario Firestore/Auth/Storage completato senza limiti raggiunti o errori.
- Assenza di Functions distribuite confermata dal proprietario; l'API resta
  disabilitata e non costituisce una verifica indipendente di questo punto.
- Il riferimento locale al bucket `.appspot.com` va ancora corretto.
- Inventario dei dati, non backup o prova di ripristino. Prima di eseguire il
  reset, ricontrollare eventuali variazioni rispetto a questi conteggi.
- Prossimo passo: dataset sintetico e simulazione del reset, poi rapporto
  concreto da approvare prima delle scritture su staging.

### Prova Firestore emulatori confermata da Vittorio

Esito riferito da Vittorio dopo la correzione dei metadati: comando concluso
con codice 0, 53684 documenti importati e 53684 verificati tramite rilettura
completa dei valori. Dataset: 4000 soci e 50 eventi. Lo script riporta zero
scritture cloud, account Auth creati e cancellazioni. Emulatori spenti al
termine. Esito eseguito e riportato da Vittorio, non rieseguito dall'agente.

Questa prova dimostra importazione e corrispondenza dell'export su Firestore
locale. Non dimostra gli esiti dei 105 scenari API, il comportamento di Auth,
i trigger, le statistiche applicative o la consegna email. Le successive
prove devono usare scenari controllati, senza attivare invii sul dataset
massivo o cambiare i contratti Q per far coincidere artificialmente i conti.
