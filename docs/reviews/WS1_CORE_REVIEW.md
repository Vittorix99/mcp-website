# Core WS1 — revisione indipendente e correzioni

Data: 25 ottobre 2026. Revisore: agente distinto GPT-6.1 Sol, effort high,
contesto nuovo, checkout in sola lettura. Range: `719da2f1..6f0be3ef`.
Verifiche indipendenti: 68 test backend, 14 test frontend con Node20 e
validatore Firebase passati. Nessuna chiamata cloud, modifica o subdelega.

Verdetto originale: **With fixes**. Nessun rilievo Critical o Minor;
tre rilievi Important, corretti dal coordinatore in `9ece2609`.
Non è stata richiesta una seconda revisione: le correzioni sono verificate
tramite regressioni RED→GREEN e suite completa, come previsto dal processo.

| Rilievo | Effetto riprodotto | Correzione e prova |
|---|---|---|
| Credenziali controllate dopo Firebase (`config/runtime_settings.py`) | Il loader accettava produzione/staging senza credenziali; `main` sceglieva ADC e inizializzava client prima dell'errore mail; PayPal poteva fallire solo al checkout. | Il loader verifica prima del ritorno tutte le credenziali richieste dai provider selezionati e il mittente mail. 16 regressioni fallivano prima; 17 casi passano dopo, inclusi provider disabilitati e avvio con costruttori Firebase vietati. |
| Browser produzione poteva usare sandbox (`config/runtime-policy.cjs`) | Modalità PayPal omessa e client sandbox `sb` erano accettati anche in produzione. | Modalità canonica derivata dall'ambiente, ID pubblico richiesto per il modo selezionato, demo `sb` rifiutato in cloud e valori canonici iniettati. Regressioni di policy e import del modulo browser fallivano prima, passano dopo. |
| Checkout locale caricava SDK PayPal (`PayPalSection.jsx`) | Modalità fake trattata come sandbox: SDK remoto e ordini `FAKE-*` incompatibili. | In local/test il bottone simulato usa i callback create/capture esistenti, senza montare il provider SDK. Quattro regressioni fallivano prima; cinque test del componente passano dopo, inclusi disabled, errore senza capture e ramo sandbox reale. |

Verifiche finali dopo tutte le correzioni: **684 backend**, **21 frontend**,
lint **0 errori / 53 warning**, build fixture exit0, smoke emulatori
**2 Python + client Firestore/Auth/Storage/Functions PASS**.

## Ambiti non ricontrollati dal revisore

Il coordinatore mantiene i seguenti limiti e decisioni esplicite; non sono
stati trasformati in dichiarazioni di sicurezza o prontezza al deploy:

- Identità dei provider e proprietà sandbox: gate prima dello staging.
- Chiavi private storiche: evidenze IAM già raccolte, nessuna nuova query del revisore.
- Cancellazioni MailerLite/progetto OAuth: conferme del proprietario.
- Restrizioni chiave pubblica Firebase: intervento rinviato dal proprietario.
- Eventuale riuso cloud delle chiavi di vecchie build: gate di attivazione cloud.
- CORS wildcard e recupero pagamenti non atomico preesistenti: fuori dal presente workstream.
- Esposizione concreta delle vulnerabilità npm: valutazione ancora aperta prima del rilascio.
- GitHub Actions remoto, runner Linux e deploy: non eseguiti; i risultati locali non li dimostrano.
