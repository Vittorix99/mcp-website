# WS3 — Primo blocco: tempi ed errori HTTP

Stato: approvato dal proprietario in chat il 2026-11-03.
Esecuzione nativa; una sola review finale. Base: `f1d70ffe` più le regole lean approvate e la pulizia `e320e55`
già verificata (PR #3). Nessuna modifica a `main` eseguita dall’agente.

## Obiettivo

Sapere quale funzione risponde, quanto impiega e con quale esito. Nessun
deploy o servizio di monitoraggio aggiuntivo in questo blocco.

## Perimetro e soluzione

I 128 endpoint HTTP esportati passano già dai decoratori comuni:
20 pubblici, 102 admin e 6 member. Integrare lì una funzione condivisa,
senza riscrivere controller o modificare le verifiche di autenticazione.

Per ogni invocazione produrre un record JSON su stdout con soli campi:
`event`, `severity`, `environment`, `function`, `request_id`, `method`,
`status_code`, `duration_ms`. Generare un UUID nuovo; metodo limitato ai
verbi HTTP standard, altrimenti `OTHER`. Non acquisire body, query, URL,
header ricevuti, token, email, identità utente o messaggi delle eccezioni.

Restituire `X-Request-ID` nelle risposte gestite, preservando status, body,
content-type e header esistenti. Registrare anche rifiuti 401, metodi 405
ed eccezioni non gestite; queste ultime mantengono la propagazione attuale
e sono classificate 500 nel log. La scrittura dei log non deve causare errori
applicativi né duplicare record attraverso il logger root.

## Implementazione e prove

1. Aggiungere il wrapper in `mcp-backend/functions/utils/http_observability.py`
   e i test in `tests/unit/utils/test_http_observability.py`.
2. Integrarlo in `api/decorators/__init__.py`, all'interno del wrapper Firebase
   ma all'esterno dell'autenticazione admin. Stessi nomi esportati e permessi.
3. Provare successi, risposte tuple/Response, errori 400/401/404/405/500,
   tempi non negativi, UUID validi/distinti e campi JSON limitati alla lista.
   Inserire valori sentinella sensibili in richiesta/eccezione e provare che
   non compaiano nei nuovi log. Provare fallimenti del logging senza alterare
   risposta o eccezione originale.
4. Eseguire test mirati durante il lavoro; una verifica finale backend completa,
   gate contratti e smoke emulatori. La CI ripete l'intera pipeline.
5. Unica review indipendente Sol high su privacy, autenticazione e compatibilità;
   commit e PR. Aggiornare questo piano con le evidenze, senza rapporti duplicati.

## Criterio di completamento e limiti

I test provano un solo record per invocazione, permessi invariati e nessuna
esposizione dei dati sentinella. Smoke e CI verdi prima dell'integrazione.

Esclusi: tempi delle singole query/provider, conteggi Firestore, dashboard,
billing export, soglie di allarme e ottimizzazioni. Non copre richieste
rifiutate dalla piattaforma o CORS prima dell'ingresso negli handler.
Il request ID non viene ancora propagato ai log preesistenti dei servizi;
per eccezioni non gestite resta disponibile nel log, non nella risposta.
Rollback: revert del commit, senza migrazioni o cambi di configurazione cloud.

Decisione implementativa: usare `after_this_request` di Flask per misurare
la risposta effettiva e aggiungere il request ID, preservando il tipo di ritorno
originale dei controller, usato anche dai test esistenti. Eccezioni non gestite
registrate una sola volta prima della propagazione. JSON scritto direttamente
su stdout, senza handler aggiuntivi o propagazione nel logger root.

Lo smoke HTTP esistente verifica anche presenza, formato UUIDv4 e unicità
di X-Request-ID, con due regressioni del verificatore RED→GREEN.

## Evidenze locali finali

- RED: 23 nuovi casi backend prima del wrapper; GREEN: 23/23.
- Suite backend completa: 709 passati; warning HarfBuzz preesistente.
- RED: 2 casi HTTP su ID mancanti/ripetuti; GREEN: suite frontend 42/42.
- Gate: 126 riferimenti, 128 export HTTP, zero eccezioni e zero errori.
- Lint JavaScript mirato, validatore Firebase e scanner repository passati.
- Prova Firebase reale eseguita dal proprietario: PASS e exit 0. Il log
  riportato include record JSON per i rifiuti 401; il verificatore HTTP ha
  controllato ID validi e distinti. Evidenza owner-reported, non esecuzione
  indipendente dell’agente.
- Review indipendente Sol high: pulita, nessun rilievo. Rieseguiti dal
  revisore 23 test backend mirati e 9 test del verificatore HTTP.
- CI remota WS3: [run 7](https://github.com/Vittorix99/mcp-website/actions/runs/41735828308)
  tutta verde; PR #4 integrata dal proprietario in `main` (`b93b742`).
  Nessun deploy eseguito.
- Non ripetuta la build frontend locale: codice UI e fixture di build invariati;
  la CI esegue comunque la pipeline completa.


## Seguito circoscritto — riepilogo offline dei log

`scripts/observability/summarize_requests.py` legge JSONL WS3 oppure stdout
emulatori (prefisso `> `), raggruppa per ambiente e funzione e restituisce
richieste, conteggi 4xx/5xx, p50/p95/p99 e massimo in millisecondi. Percentili
nearest-rank; il numero di campioni resta visibile. ID duplicati non aumentano
le richieste; duplicati discordanti e record invalidi fanno fallire il comando
senza stampare il contenuto. Altri log vengono ignorati; un input senza record
non produce un falso successo. Nessuna rete, dipendenza o modifica applicativa.

Uso dalla radice, con un log già salvato:

```sh
.venv/bin/python scripts/observability/summarize_requests.py /percorso/log-emulatori.txt
```

Sono supportati anche stdin con `-` e JSONL grezzo. Non legge direttamente
export Cloud Logging annidati o l'intero log di un job CI. Gli ambienti non
vengono mescolati; campi extra come email/body non compaiono nel report.
I conteggi 4xx/5xx includono le prove negative intenzionali dei test.
Campioni degli emulatori e percentili con pochi dati non sono una misura
rappresentativa delle prestazioni o dei costi di produzione.

Verifica: 17 test mirati RED prima del codice, GREEN dopo. Prova con record
estratti dalla CI reale WS3: 22 richieste e 6 gruppi API, ambiente `test`.
CI del riepilogo offline: run 8 completata con successo; PR #5 integrata
dal proprietario in `main` (`146b3c68`). Nessun codice HTTP modificato.


## Prossimo blocco proposto — tempi PayPal e MailerSend

Stato: approvato dal proprietario in chat il 2026-11-04. Scopo: collegare il tempo delle chiamate SDK al request ID
HTTP, distinguendolo dal tempo totale già registrato. Nessuna chiamata reale
aggiuntiva e nessuna attivazione di provider.

- Riutilizzare il writer JSON con un contesto temporale condiviso. Propagare
  il request ID durante l'esecuzione sincrona tramite ContextVar, ripristinato
  anche su eccezione; fuori da una richiesta usare `null`, senza ID inventati.
- Instrumentare soltanto i confini SDK esistenti: `SdkPayPalGateway.create_order`,
  `SdkPayPalGateway.capture_order` e `MailerSendRoutes.send_email`.
- Nuovi record `dependency_completed`: ambiente, request ID, provider,
  operazione costante, durata, stato HTTP quando disponibile e categoria di
  esito. Vietati URL, ordine/pagamento ID, destinatari, messaggi d'errore,
  payload e credenziali. I record delle chiamate API restano compatibili.
- Preservare argomenti SDK, timeout, ritorni, eccezioni e chiavi di idempotenza.
  Nessun nuovo retry o pagamento/invio prodotto dalla strumentazione.
- Test mirati con controller/client finti: successi, errori restituiti,
  eccezioni, ID correlati e separati tra richieste, contesto ripristinato,
  log senza sentinelle sensibili e guasti del writer senza effetti applicativi.
- Verifica finale backend completa e smoke emulatori; una sola review finale
  Sol high perché vengono toccati confini di pagamenti e dati personali.
  Evidenze aggiornate qui, commit e PR, senza rapporti separati.

Limiti: emulatori e stub provano l'instrumentazione, non la latenza reale
PayPal/MailerSend. Questa si misurerà in staging dopo il gate cloud.
Sono esclusi Firestore, dashboard, billing export e modifiche al riepilogo
CLI, che continua a leggere soltanto i record HTTP di completamento.

Decisione del proprietario (2026-11-04): l'estensione di
`summarize_requests.py` ai record `dependency_completed` è rinviata a un
blocco separato, da fare quando esisteranno misure reali in staging. Nel
frattempo i record si leggono direttamente nel log.

Nota di implementazione: `send_email` cattura già le eccezioni SDK e restituisce
un esito, quindi i suoi fallimenti sono registrati come `error`; `exception`
resta per PayPal, dove l'eccezione risale al chiamante.

La durata di `send_email` include la costruzione del messaggio, la lettura
degli allegati e, in caso di errore, il log esterno: in errore è un po'
sovrastimata rispetto al solo `emails.send`. Differenza accettata e nota.

Review indipendente (sotto-agente, modello predefinito dell'host, non
`gpt-6.1-sol`): nessun Critical né Important; 5 Minor. Corretti: `classify`
isolata dal risultato, firma posizionale di `send_email` ripristinata, test su
`response_code` delle eccezioni, su guasti di writer/impostazioni e sul
risultato con classificazione fallita. Verifica: 739 test unitari passati.
Smoke emulatori non eseguito dall'agente.

