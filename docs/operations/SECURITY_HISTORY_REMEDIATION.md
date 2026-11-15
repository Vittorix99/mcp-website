# Decisione di gestione dei segreti nella cronologia Git

Data: 25 ottobre 2026. Stato: classificazione completata; restrizioni Firebase rinviate dal proprietario. Core WS1 continua con verifiche locali; nessuna attivazione cloud.

## Risultato verificato

`gitleaks detect --source . --redact --no-banner` ha terminato con exit code 1: 12 segnalazioni su tutta la cronologia. Il checkout corrente passa lo scanner stdlib. Il rapporto seguente contiene esclusivamente tipo, percorso storico e commit; non contiene valori o fingerprint di credenziali.

| Tipo | Percorso storico | Commit |
|---|---|---|
| `generic-api-key` | `mcp-backend/BACKEND_USE_CASES.md` | `8536aba1778f894e4bd713d0356c483c9b241e79` |
| `jwt` | `mcp-backend/functions/scripts/mailer_lite_bootstrap.py` | `4b8b9c84e14b184b0f8a73a8ae73a3a0f753dbe7` |
| `generic-api-key` | `functions/service_mail.json` | `69ee20c6257935b052145b03295181b925486541` |
| `generic-api-key` | `functions/mail_env.json` | `a388c9313c61db70d859680726dae29f7994c646` |
| `private-key` | `functions/service-account.json` | `a388c9313c61db70d859680726dae29f7994c646` |
| `generic-api-key` | `.next/cache/.rscinfo` | `afc7f83fa07cd909e4fcbfe5f49e6ca6a5f23b69` |
| `generic-api-key` | `.next/server/server-reference-manifest.json` | `afc7f83fa07cd909e4fcbfe5f49e6ca6a5f23b69` |
| `gcp-api-key` | `out/_next/static/chunks/307-c14da5e3332e876f.js` | `afc7f83fa07cd909e4fcbfe5f49e6ca6a5f23b69` |
| `private-key` | `service-account.json` | `afc7f83fa07cd909e4fcbfe5f49e6ca6a5f23b69` |
| `generic-api-key` | `.next/cache/.rscinfo` | `636982e329353283dad3b2658f5598e90d06942d` |
| `generic-api-key` | `.next/server/server-reference-manifest.json` | `636982e329353283dad3b2658f5598e90d06942d` |
| `gcp-api-key` | `firebase.js` | `e6f268a37a081b2135e6057c96acdc431d9ec312` |

Le due segnalazioni `private-key` riguardano file service-account storici. Dai soli metadati JSON sono confermati il tipo `service_account` e il progetto `mcp-website-2a1ad` per entrambi. Un confronto locale senza output dei valori conferma che si tratta di due chiavi diverse. Al momento della scoperta, validità, stato attivo e utilizzi non erano verificati; l'esito della successiva verifica IAM è riportato sotto. Non sono stati effettuati tentativi di autenticazione con le chiavi storiche. I segnali `gcp-api-key` possono riferirsi a configurazioni Firebase pubbliche e vanno classificati separatamente; le restanti segnalazioni non sono automaticamente credenziali operative.

Il 25 ottobre 2026 il proprietario ha confermato in chat di essere l'unico sviluppatore e di avere accesso a tutti i servizi: Vittorio Di Giorgio è il referente per Google Cloud e account email. Questa conferma identifica il responsabile; non autorizza revoche, rotazioni o modifiche IAM.

## Verifica IAM in sola lettura — 25 ottobre 2026

Il proprietario ha autorizzato la verifica. È stata usata la sessione utente
`gcloud` già presente, senza impersonazione né override di credenziali e senza
autenticarsi con le chiavi esposte. Le richieste `service-accounts describe`
e `service-accounts keys list --managed-by=user` sono riuscite per entrambi
gli account nel progetto `mcp-website-2a1ad`. La corrispondenza è stata verificata
tramite l'identificativo della chiave, senza riportarlo nel documento.

| File storico | Stato dell'account | Stato della chiave storica |
|---|---|---|
| `functions/service-account.json` | Non disabilitato | Presente, **disabilitata**; Google riporta `SERVICE_ACCOUNT_KEY_DISABLE_REASON_EXPOSED` e il marcatore di esposizione |
| `service-account.json` | Non disabilitato | **Assente** dall'elenco completo delle chiavi gestite dall'utente per il relativo account |

Nessuna delle due risulta una chiave attualmente abilitata. L'assenza dalla lista
non stabilisce quando o da chi la chiave sia stata rimossa. Questi controlli
non dimostrano l'assenza di un utilizzo improprio precedente e non revocano
eventuali token già emessi. Nessuna rotazione o revoca è stata eseguita.

Fonte per l'interpretazione degli stati: [documentazione Google IAM](https://docs.cloud.google.com/iam/docs/keys-list-get).

L'elenco Functions del progetto contiene 141 funzioni; 140 espongono un campo
esplicito dell'account di esecuzione e nessuna di queste usa i due account storici.
Per la funzione priva del campo non viene dedotta alcuna identità. Il controllo
non copre altri carichi cloud, credenziali in configurazioni applicative o script
locali e non dimostra che non esistano altre dipendenze.

La classificazione delle altre dieci segnalazioni è riportata nella sezione
seguente. Restano decisioni e verifiche aperte; questa verifica non dichiara
WS1 completo.

## Classificazione delle altre dieci segnalazioni — 25 ottobre 2026

| Quantità | Segnalazione | Verifica ed esito | Stato residuo |
|---|---|---|---|
| 1 | `BACKEND_USE_CASES.md`, regola `generic-api-key` | La riga è una freccia di un diagramma Mermaid con etichetta API; nessuna assegnazione di credenziale. | Falso positivo classificato; nessuna rotazione richiesta. |
| 1 | `scripts/mailer_lite_bootstrap.py`, JWT | Provider confermato dal codice storico: `connect.mailerlite.com`. Le dichiarazioni del JWT indicano emissione l'11 febbraio 2026 e scadenza l'11 febbraio 2126; decodifica locale, senza verifica della firma né autenticazione. Nel pannello dell'account MCP sono presenti due token `VittorioDev`, entrambi creati l'11 febbraio 2026, con ultimi utilizzi mostrati il 12 febbraio e il 20 aprile 2026. | Non è possibile associare univocamente il JWT a una delle due righe dal nome/data. Il proprietario conferma che MailerLite è dismesso e, successivamente, di aver eliminato entrambi i token. Voce chiusa su conferma del proprietario; nessuna verifica indipendente successiva alla cancellazione e nessun token sostitutivo necessario. |
| 1 | `functions/service_mail.json`, OAuth web Google | Contiene un client secret per il progetto storico `mcp-project-451121`. Il progetto non è visibile nella lista progetti dell'utente CLI; `projects describe` fallisce e la console segnala accesso mancante. | Dopo il controllo manuale richiesto, il proprietario conferma che il progetto non esiste più. Voce chiusa su conferma del proprietario; la cancellazione non è stata verificata indipendentemente tramite IAM. |
| 1 | `functions/mail_env.json`, OAuth Gmail | Il file include client secret, access token e refresh token; il client è diverso da quello di `service_mail.json`. La ricerca per numero progetto lo associa a `mcp-website-2a1ad`. Nella console Google Auth Platform risulta un solo client corrente, `MCP PROD`, diverso dall'identificativo storico. | Il vecchio client non compare nell'elenco attuale. Non sono stati usati i token storici, né è stato verificato il loro precedente uso; nessuna modifica al client corrente. |
| 4 | Due `.next/cache/.rscinfo` e due `.next/server/server-reference-manifest.json` | Sono due chiavi AES di build Next.js, ciascuna duplicata tra cache e manifest. Le scadenze cache sono dicembre 2024; entrambi i manifest hanno mappe `node` e `edge` vuote, senza Server Actions registrate. La build locale corrente non riusa nessuna delle due chiavi. | Materiale interno di vecchie build, non chiavi di accesso a provider. La scadenza cache non dimostra revoca in un server già avviato; non è stata verificata l'eventuale persistenza di una vecchia build in produzione. Gli artefatti generati devono restare esclusi dai commit. |
| 2 | `firebase.js` e chunk statico `out/`, regola `gcp-api-key` | Due copie della medesima chiave pubblica Firebase. Confronto in memoria con il risultato API Keys letto tramite la sessione utente: corrisponde a `Browser key (auto created by Firebase)` del progetto di produzione, non eliminata. | La natura pubblica è prevista da Firebase, non è una credenziale privata da revocare automaticamente. La chiave ha restrizioni API ma nessuna restrizione browser; l'allowlist include anche Gmail e Cloud SQL. Verificare la necessità di queste API prima di restringerla; nessuna modifica eseguita. |

### Conferma del proprietario e chiusura MailerLite

Il proprietario dichiara: non usa più MailerLite, utilizza solo MailerSend.
La ricerca del codice applicativo corrente e degli script non trova riferimenti
operativi a `mailerlite`/`mailer_lite`; l'integrazione è documentata nella
cronologia. Non è necessario introdurre un nuovo token MailerLite nel progetto.
Il 25 ottobre 2026 il proprietario conferma in chat di aver eliminato entrambi
i token `VittorioDev` dall'account MCP. La voce MailerLite è chiusa sulla base
della conferma del proprietario, senza una nuova verifica indipendente del
pannello e senza tentativi di autenticazione con il JWT storico. MailerLite
resta dismesso; nessun token sostitutivo è necessario nel progetto.
L'agente ha soltanto letto il pannello e chiuso i dettagli con Cancel: nessuna
credenziale modificata dall'agente e nessun invio email.

### Conferma del progetto storico e revisione restrizioni Firebase

Dopo aver ricevuto le istruzioni per il controllo in Gestisci risorse, il
proprietario conferma che `mcp-project-451121` non esiste più. La voce è chiusa
su questa conferma, senza trasformarla in una verifica indipendente della
cancellazione tramite API.

Nel codice del progetto non risultano chiamate applicative a Cloud SQL Admin
né a Gmail. Le integrazioni Gmail rimaste nei test sono disabilitate esplicitamente
dopo la migrazione a MailerSend; i riferimenti Gmail del manifest Doppler sono
legacy. L'override `cloud-sql-connector` serve al tool Firebase CLI, non prova
un uso di Cloud SQL tramite la chiave pubblica browser.

Proposta da eseguire manualmente dal proprietario: nella chiave **Browser key
(auto created by Firebase)** di `mcp-website-2a1ad`, rimuovere soltanto
`gmail.googleapis.com` e `sqladmin.googleapis.com` dalla lista **API restrictions**.
Conservare le altre voci. La proposta restringe la singola chiave, non disabilita
le API nel progetto. Il proprietario ha chiesto di evitare per ora queste
modifiche: proposta rinviata, restrizioni attuali conservate. Nessuna modifica
eseguita dall'agente. La revisione resta documentata per un intervento futuro.

### Fonti e limiti

- [Firebase: natura pubblica e restrizioni delle API key](https://firebase.google.com/docs/projects/api-keys).
- [Google Cloud: gestione e restrizioni delle API key](https://docs.cloud.google.com/docs/authentication/api-keys).
- [Next.js: cifratura delle Server Actions](https://nextjs.org/docs/app/guides/data-security), confrontata con il codice installato `encryption-utils-server.js` per la struttura `.rscinfo`.
- [MailerLite: elenco dei token API](https://www.mailerlite.com/help/where-to-find-the-mailerlite-api-key-groupid-and-documentation). Il pannello mostra soltanto i token creati dal relativo utente; la verifica riguarda la sessione aperta dal proprietario.

Tutte le dieci segnalazioni sono classificate. La classificazione non equivale
a dichiararle tutte innocue o risolte: MailerLite è chiuso su conferma del
proprietario; anche il vecchio progetto OAuth è chiuso su sua conferma. Restano le verifiche di riuso delle
vecchie build/restrizioni Firebase. Nessuna autenticazione con credenziali
storiche e nessuna mutazione cloud o provider sono state effettuate dall'agente.

## Decisione proposta e limiti

1. Responsabile identificato: Vittorio Di Giorgio. Associare ogni segnale a progetto, scopo e uso attuale tramite metadati non segreti; le due chiavi private storiche sono associate al progetto di produzione. Verificare stato e dipendenze tramite l'accesso ordinario del proprietario, senza autenticarsi con le chiavi trovate.
2. Classificare i risultati: chiave privata, token provider, configurazione pubblica oppure falso positivo. Registrare le evidenze senza valori; non introdurre esclusioni generiche negli scanner.
3. Per credenziali operative esposte, preparare una proposta separata di sostituzione, verifica delle dipendenze, rollback e rotazione/revoca. Eseguire solo dopo autorizzazione esplicita e verifica del sostituto.
4. Riscrittura della cronologia, revoca, eliminazione di file credenziali e mutazioni cloud non sono eseguite né autorizzate dal presente documento.

Il piano approvato richiede di fermare il lavoro in caso di segreti storici reali: [Task 11, passo 5](../superpowers/plans/2026-10-25-core-ws1-environment-provider-safety.md). I segnali di chiave privata vengono trattati come esposizioni da accertare prima di riprendere; nessuna prova di attività della chiave è stata eseguita.

## Decisione di prosecuzione locale

Il proprietario rinvia esplicitamente l'intervento sulle restrizioni Firebase.
La chiave è pubblica per progettazione; il rinvio non viene classificato come
un'ulteriore esposizione di una credenziale privata. Le chiavi private storiche
sono disabilitata/assente secondo IAM; i token MailerLite sono stati eliminati
dal proprietario; il progetto OAuth legacy è dichiarato non più esistente dal
proprietario e il client OAuth storico di produzione non compare nella console.
Le chiavi Next.js riguardano artefatti storici senza azioni registrate nei
manifest e non sono riusate nella build locale attuale.

Si riprendono i test e l'implementazione locale di Core WS1; nessuna modifica
cloud viene dedotta da questa decisione. La verifica di eventuali vecchie build
ancora distribuite resta un prerequisito da chiarire prima dell'attivazione
cloud, senza dichiarare eliminata la cronologia o esclusi utilizzi passati.

## Lavoro preservato

Controlli CI, scanner, documentazione operativa e template inattivi implementati. Verifica locale finale: 684 test backend e 21 frontend passati, lint senza errori, build ed emulatori passati. Tre rilievi della review indipendente corretti in `9ece2609`; evidenze nel [rapporto Core WS1](../reviews/WS1_CORE_VERIFICATION.md). Staging, produzione e CI remota non sono dichiarati completati.

Audit dipendenze separato: npm segnala 49 vulnerabilità (4 critical, 29 high, 14 moderate, 2 low); valutazione e aggiornamenti non ancora eseguiti. Nessun force-fix o upgrade maggiore automatico.


## Prerequisito rilascio: audit dipendenze aggiornato — 15 novembre 2026

Il precedente conteggio WS1 di 49 rilievi è storico. Sul lockfile corrente
(commit applicativo `9374efb`, nessuna modifica alle dipendenze), eseguiti:

| Comando, da `mcp-website/` | Esito | Pacchetti segnalati |
|---|---|---|
| `npm audit --json` | exit 1, report valido | 62: 4 critical, 25 high, 31 moderate, 2 low |
| `npm audit --omit=dev --json` | exit 1, report valido | 33: 3 critical, 18 high, 10 moderate, 2 low |

Report locali ignorati: `.local/staging/precloud-npm-audit.json` e
`precloud-npm-audit-prod.json`. Comandi eseguiti con Node25.2.1/npm11.6.2;
questo è un controllo del lockfile, non una build sul runtime supportato.
Installazione/build/test delle correzioni devono usare Node20 (`.nvmrc`;
versione locale disponibile20.19.6). Nessuna dipendenza modificata.
I conteggi sono pacchetti segnalati da npm, non vulnerabilità sfruttabili
indipendenti; `--omit=dev` non dimostra che un pacchetto sia raggiungibile
nel bundle SSR o nel browser.

Valutazione iniziale:
- Next15.5.19 nel lockfile è incluso nelle advisory correnti. Le advisory
  ufficiali [Image Optimization RCE](https://github.com/vercel/next.js/security/advisories/GHSA-2464-fhr4-w9xw)
  e [Server Actions DoS](https://github.com/vercel/next.js/security/advisories/GHSA-p3m5-59mp-jv5r)
  indicano15.5.28 come versione corretta nello stesso ramo. La configurazione
  repository usa `images.unoptimized=true` e la ricerca in app/components/lib
  non rileva direttive `use server`: limita l'applicabilità di quei due vettori,
  non chiude tutte le advisory Next né prova il comportamento del deploy live.
- Altri critical segnalati nel grafo: protobufjs, websocket-driver e tar
  (quest'ultimo non nel report `--omit=dev`). Valutare percorsi e versioni
  annidate prima di dedurre impatto o forzare risoluzioni.
- npm propone anche major upgrade o downgrade di firebase-admin,
  firebase-tools, firebase-frameworks ed exceljs. Non accettarli in automatico:
  CLI14.26.0 e adattatori discovery/rollback hanno contratti da preservare.

Piano del blocco dipendenze, approvato dall'owner il15novembre2026:
1. Separare runtime SSR/browser, tool build/deploy e dipendenze inutilizzate;
   verificare i percorsi dei rilievi critical/high e gli aggiornamenti compatibili.
2. Correggere prima nello stesso major, senza `audit fix --force`, downgrade
   automatici o override non verificati. Eventuali major necessari richiedono
   un perimetro esplicito con preservazione dei contratti Firebase/release.
3. Installazione pulita Node20, test frontend/contratti/lint/build fixture e
   regressioni deployment/discovery pertinenti; rieseguire audit completo e
   produzione. Unica review indipendente Sol high su Codex; CI finale owner.
4. Chiudere solo con evidenza delle correzioni e valutazione esplicita di ogni
   residuo pertinente al rilascio. Nessuna accettazione implicita del rischio.

Stato: **aperto; aggiornamenti compatibili applicati, residui da risolvere**.
La verifica delle vecchie build distribuite resta il punto successivo.


### Primo passaggio compatibile — 15 novembre 2026

Owner approva il blocco. Modificato solo `mcp-website/package-lock.json`:
`npm audit fix --package-lock-only --ignore-scripts`, seguito da
`npm install --package-lock-only --ignore-scripts --no-audit` per riconciliare
le dipendenze optional mancanti segnalate dal primo `npm ci`. Il secondo
`npm ci --no-audit` passa con Node20.19.6/npm10.8.2. Nessuna modifica al
manifest, ai pin CLI14.26.0, agli override esistenti o al codice applicativo;
nessun force-fix, major diretto, downgrade imposto o nuovo override.
Ripristino locale: ripristinare il lockfile del commit precedente e rieseguire
`npm ci` con Node20; nessuna modifica a dati o servizi distribuiti.

Tra gli aggiornamenti: Next15.5.19→15.5.29, axios1.17.0→1.21.1,
body-parser1.20.5→1.20.9, markdown-it14.2.0→14.3.3,
PostCSS root8.5.15→8.5.33, protobufjs root7.6.2→7.6.6,
websocket-driver0.7.4→0.7.5. Le copie annidate restano oggetto dell'audit.

Audit finali Node20, entrambi exit1 per residui:

| Ambito | Prima | Dopo |
|---|---|---|
| Completo | 62 (4critical/25high/31moderate/2low) | 50 (2critical/18high/29moderate/1low) |
| `--omit=dev` | 33 (3critical/18high/10moderate/2low) | 22 (1critical/12high/8moderate/1low) |

I nuovi report includono anche segnalazioni ereditate dai genitori e variazioni
del grafo dopo la riconciliazione: il conteggio non è una prova di sicurezza.
Report ignorati `precloud-npm-audit-after.json` e
`precloud-npm-audit-prod-after.json` in `.local/staging/`.

Valutazione dei residui e confine del prossimo passaggio:

| Gruppo | Percorso/uso osservato | Stato |
|---|---|---|
| protobufjs7.2.4, protobufjs-cli, google-gax3, Firestore server, busboy1, Storage/teeny-request, uuid | Firebase Admin11.11.1; import diretti solo nello smoke JS, ma codice Firebase framework usa API Admin nell'SSR generato | Non considerato automaticamente solo dev. Il pin protobufjs di google-gax3 e gli altri vincoli richiedono aggiornamento Admin oppure override mirati con verifica esplicita. |
| grpc-js, Firestore web/compat, firebase | SDK web12.11.0; copia grpc root1.9.16 e ulteriore copia nel vecchio google-gax | Rimangono advisory high; il solo aggiornamento patch1.9.15→1.9.16 non chiude il gruppo. |
| tar6.2.1 | CLI14.26.0, `lib/archiveDirectory.js` usa `tar.create` durante packaging | Critical ancora segnalato. Non è un endpoint browser; il tool di rilascio rimane sensibile. Correzione tar7 o cambio CLI richiedono perimetro esplicito. |
| PostCSS8.4.31 annidato, next | Next15.5.29; elaborazione CSS durante build | Rilievi residui high/moderate; PostCSS root corretto non sostituisce il pin annidato di Next. Verificare override8.5 o migrazione Next, senza imporre Next16 automaticamente. |
| sharp0.33.5, cookie0.5, firebase-frameworks0.11.8 | Framework SSR; sharp importato dal suo adattatore Angular, cookie usato da firebase-aware; Next ha una copia sharp0.35.5 | Non dedurre un'esposizione Next dalla copia Angular né ignorare il pacchetto SSR. Valutare aggiornamento/rimozione dipendenza e generazione SSR. |
| exceljs, uuid8 | Esportazione browser in `lib/excel.js`, solo creazione workbook | Nessun import di file forniti dall'utente individuato; advisory residua da valutare, niente downgrade ExcelJS3 automatico. |
| CLI e tool transitivi | proxy-agent/get-uri/pac-proxy-agent/basic-ftp; PubSub/google-gax5/opentelemetry; glob/minimatch/rimraf; archiver/archiver-utils/zip-stream; csv-parse/exegesis; gaxios/googleapis-common/gcp-metadata; stream-json, universal-analytics/uuid, zod; express/qs, fast-xml-parser, hono server | Residui build/emulator/deploy; alcuni vincoli della CLI o pin override esistenti impediscono fix automatici. Non equivalgono a codice HTTP dell'app ma non sono accettati implicitamente per CI privilegiata. |
| ESLint/type tooling | typescript-eslint parser/plugin/type-utils/typescript-estree/utils | Uso locale/CI; valutare aggiornamenti compatibili del toolchain, senza includere una migrazione ESLint nel passaggio corrente. |

L'advisory [protobufjs code generation](https://github.com/protobufjs/protobuf.js/security/advisories/GHSA-xq3m-2v4x-88gg)
richiede schemi/descriptor controllati dall'attaccante; l'uso di soli schemi
SDK fidati limita quel vettore, non chiude le altre advisory del gruppo.
Per tar, [l'advisory di ricorsione](https://github.com/isaacs/node-tar/security/advisories/GHSA-r292-9mhp-454m)
riguarda listing/extraction con selezione membri: il percorso packaging osservato
è create. Non viene generalizzata questa osservazione alle altre advisory tar.

Verifiche completate: installazione pulita,50 test frontend,126 riferimenti API/
130 export/0 errori, lint0errori/53warning preesistenti, build fixture Node20,
55 test Python deployment/secret. Smoke standard inizialmente non avviabile
per porta8080 occupata da un processo preesistente, preservato. Riutilizzato
il driver privato su5280/8280/9299/9399 e porte servizio dedicate, con copie
temporanee degli smoke aventi sole sostituzioni porte/import:2test Python e
client Firestore/Auth/Storage/Functions/event HTTP PASS,exit0/shutdown pulito;
file temporanei rimossi. Log `.local/staging/precloud-*`.
Review indipendente unica Sol high conclusa senza rilievi correggibili,
accettata dal coordinatore. Verificati riferimenti native Linux nel lockfile,
non eseguita installazione Linux. RE2 opzionale richiede Node più recente,
ma anche la versione baseline lo richiedeva: su Node20 il fallback RegExp di
Superstatic resta quello preesistente. Nessun pin di rollback aggiunto.
CI remota e ambienti distribuiti non verificati.
Il prerequisito dipendenze rimane **aperto**: nessuna accettazione del rischio
residuo né attivazione cloud autorizzata da questi risultati.
