# Transizione credenziali — Core WS1

**Stato aggiornato al 2026-11-15:** preparazione repository segreti/deploy integrata nel worktree `.worktrees/core-ws2`, ramo `core-age-data-integrity`; ultimo commit applicativo `9374efb` (Q-05), PR #12 draft dipendente da PR #11. CI #11 passata sul commit `0b85eb7` secondo il checkpoint storico; CI #12 non confermata. Le prove locali Q-05 sono registrate in `docs/process/NEXT_SESSION.md` e non attestano un deploy. Il ramo originario `ci/staging-deployment` resta un riferimento storico. Inventario cloud e identità build, piano IAM concreto e autorizzazione di attivazione restano aperti. Nessuna creazione di identità, modifica IAM, rotazione/revoca o deploy deriva dalla sola presenza di questo documento.

Prima del rilascio restano da chiudere in sequenza: valutazione aggiornata delle dipendenze, eventuale riuso di vecchie build distribuite e risultato CI sullo SHA da rilasciare. Inventario/IAM precedono una separata autorizzazione cloud; bootstrap, traffico pagamenti compatibile, E2E sandbox e rollback richiedono evidenze reali. Checklist corrente: [NEXT_SESSION.md](../process/NEXT_SESSION.md#q-05-concluso-e-prerequisiti-cloud--15-novembre-2026).

L'inventario del manifest è basato su riferimenti di file e codice tracciati. I nomi riportati non attestano che i file esistano nel checkout o che siano correnti. Per i due file storici segnalati dall'audit sono stati estratti soltanto metadati non segreti (tipo e progetto); nessun valore di credenziale viene riportato. Non sono stati aperti `.env` o JSON locali ignorati per questo inventario.

**Referente confermato:** Vittorio Di Giorgio, unico sviluppatore con accesso a tutti i servizi (conferma in chat del 25 ottobre 2026). Le indicazioni di owner da assegnare nelle righe del manifest sono quindi risolte a livello di referente; rimangono da verificare le associazioni alle singole identità e i loro utilizzi. Le due chiavi private storiche, distinte, risultano associate a `mcp-website-2a1ad`: vedere la [decisione di gestione](SECURITY_HISTORY_REMEDIATION.md). Nessuna revoca o rotazione è autorizzata dalla sola conferma del referente.

## Identità legacy indicate da riferimenti tracciati

Il manifest `scripts/doppler/secrets_manifest.conf` elenca i seguenti percorsi JSON come sorgenti per il secret `FIREBASE_SERVICE_ACCOUNT_JSON` o `GMAIL_SERVICE_ACCOUNT_JSON`:

| Percorso indicato nel manifest | Ambito/config manifest | Scopo osservato | Progetto associato | Sostituzione proposta | Responsabile / stato |
|---|---|---|---|---|---|
| `mcp-backend/functions/service_account_test.json` | backend / dev | Iniezione `FIREBASE_SERVICE_ACCOUNT_JSON`; l'uso concreto e il progetto non sono verificati | Non verificato | ADC per identità cloud gestita; GitHub Actions con WIF per CI | Referente: Vittorio Di Giorgio; **blocked before staging activation** |
| `mcp-backend/functions/service_account.json` | backend / prod | Iniezione `FIREBASE_SERVICE_ACCOUNT_JSON`; l'uso concreto e il progetto non sono verificati | Non verificato | ADC per identità cloud gestita; GitHub Actions con WIF per CI | Referente: Vittorio Di Giorgio; **blocked before staging activation** |
| `mcp-backend/functions/service_account_gmail_test.json` | backend / dev | Iniezione `GMAIL_SERVICE_ACCOUNT_JSON`; il codice d'uso e il progetto non sono verificati | Non verificato | ADC per runtime cloud solo se compatibile con l'uso confermato; WIF per CI | Referente: Vittorio Di Giorgio; **blocked before staging activation** |
| `mcp-backend/functions/service_account_gmail_prod.json` | backend / prod | Iniezione `GMAIL_SERVICE_ACCOUNT_JSON`; il codice d'uso e il progetto non sono verificati | Non verificato | ADC per runtime cloud solo se compatibile con l'uso confermato; WIF per CI | Referente: Vittorio Di Giorgio; **blocked before staging activation** |

`mcp-backend/functions/mock_data.py` contiene un riferimento storico a `credentials.Certificate("service_account.json")`; il commento lo descrive come percorso da sostituire, ma non prova progetto, identità o uso corrente. La configurazione Firebase runtime corrente, `mcp-backend/functions/config/firebase_config.py`, usa credenziali anonime per emulatori e Application Default Credentials (ADC) in cloud. `runtime_settings.py` rifiuta `GOOGLE_APPLICATION_CREDENTIALS` in local/test e rifiuta le variabili JSON di service account.

Il manifest Doppler nomina anche `.env.integration`, `.env`, `.env.development`, `.env.production` e `.env` frontend. Sono fonti/target dichiarati dal manifest; contenuti e appartenenza a progetti non sono verificati qui. Doppler resta il meccanismo transitorio durante WS1: non sono autorizzati rimozione, sostituzione, upload o download di segreti.

## Percorso di transizione e gate

**Verifica storica autorizzata del 25 ottobre 2026:** tramite la sessione utente
`gcloud`, una delle due chiavi esposte risulta disabilitata per esposizione e
l'altra assente dall'elenco chiavi del rispettivo account. Gli account risultano
non disabilitati; non sono state modificate chiavi o policy. L'esito riguarda
esclusivamente le due chiavi storiche identificate, non certifica lo stato dei
file nominati nel manifest Doppler né delle altre segnalazioni.

1. Prima di ogni rotazione, verificare con il responsabile designato l'esistenza e l'uso di ciascuna identità, il progetto associato, gli ambiti IAM, i carichi e le dipendenze; assegnare un owner accountable. Finché questi dati mancano: **blocked before staging activation**.
2. Verificare che local/test operino solo con emulatori senza credenziali cloud e che l'applicazione cloud supporti ADC. Per workflow GitHub Actions, predisporre WIF con ambiente protetto e permessi minimi, senza chiavi persistenti.
3. Validare l'identità sostitutiva, i permessi minimi, i log senza segreti e il rollback in un gate separato autorizzato. Nessuna prova staging o produzione fa parte del presente passaggio.
4. Solo dopo una transizione verificata e un'autorizzazione separata, il responsabile credenziali può pianificare rotazione/revoca; conservare evidenza dell'esito e confermare che non restino dipendenze. Non eliminare file né revocare credenziali come parte di Core WS1.

| Gate | Stato |
|---|---|
| Identificazione di account, progetto, utilizzo e owner accountable | **blocked before staging activation** |
| Inventario Doppler, accessi, audit e integrazione GitHub Actions | Da completare prima dell'abilitazione di workflow cloud |
| Verifica ADC runtime e WIF CI | Boundary ADC verificato offline; prova cloud ADC/WIF e permessi reali ancora necessaria |
| Rotazione e revoca | Due token MailerLite eliminati dal proprietario; ulteriori interventi richiedono decisioni separate |
| Deployment cloud | Nessun deployment attivo o autorizzato da Core WS1 |

## Fonti tracciate

- `scripts/doppler/secrets_manifest.conf` per i nomi dei percorsi JSON e i secret name associati.
- `mcp-backend/functions/mock_data.py` per il riferimento storico a `service_account.json`.
- `mcp-backend/functions/config/firebase_config.py` e `mcp-backend/functions/config/runtime_settings.py` per ADC, modalità emulatori e rifiuto delle credenziali locali.
- `docs/superpowers/plans/2026-10-25-core-ws1-environment-provider-safety.md`, vincoli globali e Task 12; `docs/superpowers/specs/2026-10-24-ws1-environment-provider-safety-design.md`, sezioni 7.3, 14 e 22.


## Piano operativo: segreti e deploy automatici — 2026-11-13

Richiesta owner: branch/PR con controlli, merge su main, deploy automatico
staging con test post-deploy, produzione inizialmente con approvazione manuale.
Il ramo di preparazione è `ci/staging-deployment`, base `0b85eb7` della PR #11;
resta dipendente dall'integrazione #9 → #11. Piano approvato dal proprietario in chat il 2026-11-13 e inserito nelle
attività da fare. Implementazione ripresa su richiesta owner; il medesimo perimetro non
richiede una nuova approvazione del piano.
Restano distinti i gate concreti di accesso cloud e rilascio descritti sotto.

### Riscontri di sola lettura

- GitHub `Vittorix99/mcp-website`:0 Environment,0 variabili Actions repository,
  0 secret Actions repository. Controllati i soli metadati; nessun valore
  segreto letto, caricato o modificato.
- Google Cloud `mcp-website-dev-39539`:0 workload identity pool globali.
  Non sono state create identità né abilitate API o policy.
- All'inizio della ricognizione, unico workflow: `.github/workflows/pr.yml`, eventi pull_request e
  workflow_dispatch. Nessun trigger push/main né deploy.
- I file `workflow-templates/staging.yml` e `production.yml` sono esempi
  inattivi fuori da `.github/workflows/`; non implementano deploy o rollback.
- Il runtime iniziale leggeva e validava configurazione/provider durante l'import
  (`main.py`, `firebase_config.py`, service singleton). Non dichiara binding
  SecretParam. Aggiungere solo un workflow o rinominare gli env non basta:
  l'accesso ai segreti va rinviato all'inizializzazione runtime, preservando
  il rifiuto di credenziali mancanti quando il provider viene avviato.

### Fonte dei valori

| Ambito | Configurazione pubblica | Segreti e identità |
|---|---|---|
| PR/local/test | Catalogo tracciato, emulatori, fixture | Nessuna credenziale cloud/provider reale |
| Job deploy staging | Environment GitHub staging: progetto, regione, URL, Firebase web config, client ID PayPal sandbox, riferimenti WIF/account | OIDC/WIF limitato a repository/workflow/main; nessuna chiave JSON o FIREBASE_TOKEN persistente |
| Backend staging | Configurazione runtime staging esplicita; mail/Pass2U/Sender disabilitati, gender/SoundCloud fake | Secret Manager del progetto staging; inizialmente solo credenziali sandbox PayPal necessarie |
| Produzione | Environment GitHub production separato, protetto da approvazione owner e branch main | Identità deploy/runtime e secret separati; soli binding necessari per funzione |

Non esportare l'intero `.env` o archivio Doppler negli artifact/log/GitHub.
Gli env pubblici vanno passati esplicitamente; `NEXT_PUBLIC_*` è materiale
pubblicato nel browser. Doppler resta transitorio fino alla sostituzione
verificata: una sola fonte autorevole per ogni segreto, nessuna doppia
manutenzione manuale. Nessuna rimozione degli env locali o rotazione automatica.

### Implementazione proposta in un blocco coerente

1. Inventariare nomi/consumatori/ambienti delle variabili necessarie; separare
   configurazione pubblica, segreti e riferimenti di identità. Fornire esempi
   senza valori reali e validazione che rifiuti credenziali/ambienti errati.
2. Integrare SecretParam e binding per funzione. Separare discovery/deploy da
   inizializzazione runtime dei provider; non usare chiavi dummy per aggirare
   la validazione cloud. Conservare comportamento local/test e provider
   disabilitati. Verificare discovery senza segreti e rifiuto runtime se mancanti.
3. Riutilizzare il job di verifica esistente, rendendolo richiamabile dalla
   pipeline push/main. Dopo tutti i controlli verdi, checkout dello stesso SHA
   e deploy staging; niente artifact o codice proveniente da PR non fidate in
   un job privilegiato. Pin delle Actions e dipendenze, concurrency per ambiente.
4. Build frontend per ambiente: i valori NEXT_PUBLIC sono fissati nella build,
   quindi non promuovere una build frontend staging contenente configurazione
   staging in produzione. Release identificata da SHA e manifest di digest e
   configurazioni/versioni, senza valori segreti; nessuna promessa di un unico
   binario frontend identico fra ambienti diversi.
5. Test post-deploy staging: prima health/read-only e identità della release;
   poi E2E sandbox con dati sintetici isolati e pulizia mirata. I dati esistenti
   restano protetti. Email solo al destinatario di prova autorizzato, quando
   viene abilitato il relativo blocco; Sender resta disabilitato.
6. Produzione dopo staging verde e approvazione GitHub Environment. Definire e
   verificare rollback sul precedente SHA/configurazione/versioni segreti;
   niente rollback dei dati. Il rollout pagamenti deve evitare worker misti
   che ignorano le reservation: risolvere questo gate prima del primo deploy.
7. Unica review finale Sol high del blocco, prove offline/emulatori e discovery,
   successivamente prova staging controllata. Attivare l'automatismo soltanto
   dopo verifica dei metadati/permessi e autorizzazione cloud concreta.

### Dati/configurazioni necessari per l'attivazione

- Confermare progetto/bucket/origini effettivi e inventario account provider;
  gli identificativi del catalogo sono riferimenti, non conferme operative.
- Preparare un piano IAM minimo con account deploy/runtime separati per
  ambiente, WIF vincolato a repository ID899139661, workflow/ref main e
  ambiente. Non assegnare Owner/Editor o creare chiavi persistenti.
- Presentare nomi delle identità, risorse e permessi esatti prima di creare
  accessi. Configurare Environment GitHub staging/production e approvazione
  produzione; verificare che il piano GitHub supporti le protezioni richieste.
- Popolare Secret Manager fuori da chat/Git/artifact, tramite accesso owner,
  solo dopo aver completato il binding e verificato l'utilizzo attuale.

### Accettazione e limite della preparazione corrente

Il blocco sarà completato quando un commit main verificato viene distribuito
su staging senza env del computer dello sviluppatore, i test staging passano,
produzione resta in attesa di approvazione e il rollback è dimostrato.
Nessun secret deve comparire in repository, artifact, bundle frontend o log;
PR e fork non devono ottenere l'identità deploy. Valori/riferimenti mancanti
bloccano l'attivazione senza fallback su produzione.

L'implementazione repository è in corso nel blocco approvato. Il codice dei
workflow non equivale ad attivazione: i flag repository sono assenti e quindi
i job cloud restano saltati. Accessi, bootstrap della prima baseline, E2E
sandbox e prova reale del rollback restano gate distinti. I template inattivi
rimangono esempi storici. Le prove della PR #11 restano valide per il codice
già concluso, non certificano il nuovo ramo né un rilascio cloud.

Riferimenti primari: [Firebase environment e secret parameters](https://firebase.google.com/docs/functions/config-env),
[WIF per pipeline](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines).


### Esecuzione del blocco approvato

Vincoli: Python3.11/Node20 e dipendenze bloccate esistenti; nessun valore
segreto o credenziale persistente nel repository; nessuna mutazione cloud
prima della revisione di identità/permessi concreti. Una review finale Sol high.

- [x] Runtime/discovery: `config/runtime_settings.py` separa policy strutturale
  e validazione credenziali del singolo provider. Il caricatore rigoroso
  esistente resta disponibile e invariato nel contratto predefinito. Factory
  provider usano validazione mirata; Firebase/main e costanti leggono policy.
  Tre servizi con provider eager diventano lazy preservando l'iniezione test.
  RED/GREEN in `tests/unit/config/test_deployment_secrets.py`: nessuna chiave
  necessaria per discovery, provider attivo senza chiave rifiutato, progetti
  errati sempre rifiutati, nessun provider inizializzato per liste pubbliche.
- [x] Binding: `config/function_secrets.py` descrive i provider utilizzabili
  dalle funzioni; SecretParam soltanto per segreti dei provider attivi.
  Decoratori HTTP e trigger dichiarano e verificano gli stessi binding prima
  degli effetti del relativo handler. Prova manifest reale e casi negative:
  route pubblica senza segreti, PayPal sandbox distinto da produzione, mail
  disabilitata senza binding, auth/metodo rifiutati prima dei provider.
- [x] Release (preparazione repository): workflow riutilizzabile di verifica e pipeline staging per
  push/main; script sotto `scripts/deployment/` validano input, generano solo
  configurazioni non segrete, verificano SHA/ambiente e testano la release.
  Nessuna autenticazione privilegiata da PR/fork. Produzione protetta e
  rollback sullo SHA verificato, con build frontend per ambiente.
- [x] Verifica finale repository: unitari backend, strumenti, frontend, discovery,
  emulatori API/Auth/smoke pertinenti; review Sol high unica. Documentare i
  risultati realmente osservati e i prerequisiti cloud ancora mancanti.
- [ ] Attivazione: proporre identità e ruoli concreti, verificare risorse e
  protezioni, collegare segreti tramite owner, poi prova staging e rollback.
  Questa casella richiede risultati cloud, non si chiude con mock o template.

### Preparazione repository: comportamento effettivo

`release.yml` richiama i controlli PR su push/main. I flag **repository**
`ENABLE_STAGING_DEPLOY` e `ENABLE_PRODUCTION_DEPLOY` devono valere `true`;
assenti significano nessun job cloud. Non usare variabili Environment per
questi due flag: non sono disponibili quando GitHub decide se creare il job.
Nessun `workflow_run`, artifact PR o chiave JSON alimenta un job privilegiato.

`deploy-environment.yml` usa checkout dello stesso SHA, Environment separati
e OIDC. Prima dell'autenticazione verifica repository ID899139661, workflow
release, ref main e regola Environment main-only. Produzione richiede reviewer
obbligatori e bypass amministratori disattivato; metadati mancanti bloccano.
Actions e CLI Firebase14.26.0 sono fissati. Gli adattatori di discovery/build
richiedono revisione a ogni upgrade CLI.

`scripts/deployment/release.py` genera solo configurazione pubblica e rifiuta
dotenv esistenti. Non copia env locali né legge payload Secret Manager.
SHA/digest sono specifici per ambiente; il digest non descrive i valori
segreti. Health backend/frontend e metadati di tutte le funzioni backend
verificano l'identità della release; smoke post-deploy solo di lettura.
La build frontend usa lo script release anche attraverso Firebase, che
altrimenti ignora il comando build personalizzato in package.json.

SecretParam dichiara i soli provider attivi per funzione. PayPal usa il nome
canonico `PAYPAL_CLIENT_SECRET` in progetti distinti. Gli alias legacy live
restano compatibili nel runtime ma non vengono generati. Sender non riceve
binding. L'account backend è condiviso: i binding limitano l'iniezione env,
non separano IAM fra singole funzioni dello stesso backend.

### Rollback e prima baseline

Prima delle mutazioni, artifact `rollback-staging`/`rollback-production`
conserva per30 giorni revisioni Cloud Run Python e SSR, percentuali traffico,
versione Hosting, SHA/digest e riferimenti alle versioni numeriche dei secret.
Nessun payload, env completo, dataset o credenziale WIF viene caricato.
Il ripristino riusa revisioni immutabili e versione Hosting; non ricompila
il vecchio SHA contro secret latest. Rifiuta versioni secret disabilitate o
alias non numerici, poi verifica traffico e health. Deploy/smoke fallito tenta
rollback e lascia il job fallito. Cancellazione del runner, artifact scaduto
o revisioni eliminate richiedono intervento owner. Nessuna atomicità fra
servizi e nessun rollback dei dati.

Actions `rollback` richiede l'ID del run che catturò la baseline desiderata.
Accetta artifact solo da `release.yml` main nel medesimo repository, run
completato e primo tentativo. Anche rollback produzione richiede approvazione.
Il traffico non ripristina Scheduler/Eventarc: l'automatismo richiede inventario
funzioni invariato e rifiuta modifiche a trigger, decoratori, binding o
firebase.json rispetto alla baseline. Nuovi endpoint o topologie richiedono
upgrade controllato e nuova prova rollback. Rules, indexes, account, API e
IAM non sono distribuiti automaticamente da questi workflow.

Gli attuali endpoint legacy non hanno gli stamp: serve un bootstrap cloud
controllato e un piano sul traffico pagamenti. I flag Environment
`PAYMENT_ROLLOUT_APPROVED` e `ROLLBACK_BASELINE_VERIFIED` attestano gate owner
conclusi, non sostituiscono prove. Il secondo richiede prova reale in staging
e resta assente finché non registrata. Anche E2E sandbox e verifica dei secret
reali restano aperti: gli smoke e gli emulatori non provano un checkout PayPal
reale. Produzione resta spenta.

### Risorse da definire al gate cloud

Proposta nominativa per ciascun progetto del catalogo, nessuna risorsa creata:

| Identità proposta | Ambito |
|---|---|
| `github-deploy@PROJECT_ID.iam.gserviceaccount.com` | Deploy Functions/Hosting, metadati, rollback Cloud Run; nessun payload provider |
| `app-runtime@PROJECT_ID.iam.gserviceaccount.com` | Firestore/Auth/Storage applicativi; Secret Accessor sui singoli secret attivi |
| `web-runtime@PROJECT_ID.iam.gserviceaccount.com` | SSR pubblico; nessun secret provider o accesso amministrativo ai dati |
| Pool `github-actions`, provider `main-release` | GitHub OIDC vincolato a repository ID899139661, main, workflow release/reusable e subject Environment |

Prima di richiedere modifiche IAM occorre inventariare numeri progetto,
bucket effettivi, account provider, identità Cloud Build e service agent.
La proposta ruoli deploy comprende Cloud Functions Developer, Firebase
Hosting Admin, Cloud Build Builds Editor, Artifact Registry Writer, Cloud Run
Admin, Eventarc Admin, Cloud Scheduler Admin, Service Usage Consumer e Secret
Manager Viewer; Service Account User solo su runtime/build confermati. Sono
ruoli **da ridurre/verificare** sulle risorse reali, non concessioni approvate
o prova di minimo privilegio. Nessun Owner/Editor o Secret Accessor al deploy.
Il runtime deve ricevere accesso ai soli dati/secret necessari. La pipeline
controlla API già abilitate e binding Secret Accessor per secret, senza
abilitare API o assegnare automaticamente quest'ultimo ruolo.

Variabili pubbliche Environment: `WIF_PROVIDER`, `DEPLOY_SERVICE_ACCOUNT`,
`RUNTIME_SERVICE_ACCOUNT`, `WEB_RUNTIME_SERVICE_ACCOUNT`, `FIREBASE_API_KEY`,
`FIREBASE_APP_ID`, `PAYPAL_CLIENT_ID`; produzione aggiunge
`MAILERSEND_FROM_EMAIL`, `MAILERSEND_FROM_NAME`, `SOUNDCLOUD_CLIENT_ID`.
Analytics opzionale resta fuori dal primo blocco. Secret staging:
`PAYPAL_CLIENT_SECRET`; produzione aggiunge `MAILERSEND_API_KEY`,
`PASS2U_API_KEY`, `SOUNDCLOUD_CLIENT_SECRET`. Inserimento valori tramite owner
in Secret Manager, fuori da chat/Git/artifact. Non creare secret disabilitati.

### Evidenze locali del checkpoint

- Backend1297 unitari, strumenti87, frontend48, lint e build fixture passati.
  Discovery SDK Firebase reale in staging/produzione senza payload provider;
  binding PayPal recovery e MailerSend capture/rinnovo coperti da regressioni.
- API370 in85.98s e Auth57 in1.02s su emulatori dedicati passati; runner exit0
  e shutdown pulito. Queste prove precedono le ultime correzioni dei binding
  cloud, che non cambiano i profili fake e sono coperte dagli unitari finali.
- Smoke completo:2 test Python e client Firestore/Auth/Storage/Functions con
  contratti HTTP eventi PASS, runner exit0/shutdown pulito. Driver privato usa
  porte dedicate e copie temporanee degli smoke con sole sostituzioni porte:
  i test originali fissano5001/8080/9199. Copie eliminate dopo la prova;
  nessuna modifica applicativa per aggirare le asserzioni. I primi tentativi
  hanno rilevato errori del driver, non difetti runtime.
- Actionlint1.7.12 PASS sui tre workflow; configurazione Firebase valida;
  API126 riferimenti/130 export/0 errori; scanner sorgenti0 e diff check pulito.
  `.local/**` è escluso come scratch privato ignorato, non come codice app.
- Unica review Sol high conclusa con4 rilievi accettati e corretti: template
  env tracciati, binding recovery PayPal, binding mail rinnovo e snapshot da
  revisioni attive. Le regressioni coprono anche rilascio dopo rollback e
  versioni secret riferite dalle revisioni salvate, non dai metadati latest.
- Log privati `.local/staging/deploy-*.log`. Nessuna CI del nuovo ramo o prova
  cloud è attestata da questi risultati. WIF/IAM, bootstrap, E2E sandbox e
  rollback reale restano aperti; flag deploy assenti, nessuna mutazione cloud.

### Decisione owner: integrazione finale differita — 2026-11-13

La PR #9 è stata unita dall'owner in main (`8cfc8c68`); contiene prove sconti.
Su richiesta owner, la PR #11 è nuovamente **draft**, aperta e senza
auto-merge: il resto della ristrutturazione prosegue sui branch di sviluppo.
Non unire altre PR in main fino alla decisione finale d'integrazione owner.

Protezione main configurata su richiesta owner e riletta via API: PR e
check GitHub Actions `verify` obbligatori, strict/up-to-date, applicazione
anche agli admin, conversazioni risolte, force push e cancellazione vietati.
App attesa15368; approvazioni aggiuntive richieste0 per l'owner unico.
Nessun deploy o workflow cloud attivato. Il disegno di attivazione staging
andrà riconciliato con questa decisione prima del gate cloud, senza cambiare
ora i trigger o le condizioni WIF della pipeline preparata.


## Inventario cloud staging — 16 novembre 2026

Inventario di sola lettura avviato su richiesta dell'owner. Nessuna modifica
a risorse, dati, IAM o credenziali autorizzata da questa ricognizione.

| Elemento | Riscontro | Provenienza |
|---|---|---|
| Nome progetto | `mcp-website-dev` | Schermata impostazioni Firebase fornita dall'owner |
| ID progetto | `mcp-website-dev-39539` | Stessa schermata; corrisponde al catalogo repository staging |
| Numero progetto | `1005755179074` | Stessa schermata |

La schermata conferma i metadati visualizzati, non l'inventario delle risorse
né i permessi effettivi. Bucket, database, release distribuite, identità
runtime/build, service agent e policy IAM restano da verificare.
La decisione d'integrazione main riportata sopra rimane in vigore; questa
ricognizione non modifica workflow o condizioni WIF.


### Bucket staging — riscontro owner del16novembre2026

| Bucket | Località riportata | Provenienza |
|---|---|---|
| `mcp-website-dev-39539.firebasestorage.app` | Multi-region `us` | Elenco Cloud Storage fornito dall'owner |
| `mcp-website-dev-39539` | Multi-region `us` | Stesso elenco |

**Discrepanza aperta:** il catalogo repository staging indica
`mcp-website-dev-39539.appspot.com`, assente dall'elenco fornito. Non si deduce
quale dei due bucket sia il default Firebase o quello usato da backend/frontend,
né lo scopo del secondo bucket. Verificare queste associazioni e gli eventuali
bucket di build prima di proporre modifiche al catalogo o ai permessi.
Nessun contenuto, regola o policy del bucket letto/modificato dall'agente.


L'owner conferma che Firebase Storage seleziona all'apertura
`gs://mcp-website-dev-39539.firebasestorage.app` (16novembre2026). È il bucket
presentato dalla console Firebase; uso effettivo di backend/frontend distribuiti
e finalità del bucket `mcp-website-dev-39539` ancora da verificare. Il nome
`.appspot.com` del catalogo resta una discrepanza aperta: nessuna configurazione
applicativa o IAM modificata in questa fase d'inventario.


### Firestore staging — schermata owner del16novembre2026

| Elemento | Riscontro visualizzato |
|---|---|
| Database ID | `(default)` |
| Stato | Indicatore verde di stato |
| Edizione | Standard |
| Modalità | Firestore Native |
| Località | `nam5` (United States) |
| Creazione | 15gennaio2026,21:02:52 (UTC+1, come mostrato dalla console) |
| Backup pianificati | Disabled |
| Cifratura | Google-managed |

Provenienza: schermata dell'elenco database fornita dall'owner, non lettura
API indipendente. Nessun documento del database aperto o modificato. La voce
backup pianificati disabilitati non dimostra l'assenza di export, backup manuali
o altre forme di recupero; queste restano da verificare prima di eventuali
sostituzioni dei dati staging. Nessuna attivazione backup effettuata.


### Funzioni e topologia storica — riscontro owner del16novembre2026

- L'owner riporta **zero funzioni** nell'elenco Firebase Functions del progetto
  staging `mcp-website-dev-39539`; nessuna lettura API indipendente effettuata.
- L'owner spiega che in passato usava funzioni distribuite sul progetto di
  produzione, collegandole al database staging MCP Dev. Non era un backend
  staging distribuito separatamente nel progetto dev.
- La spiegazione è un riscontro storico: stato attuale di routing, progetti
  selezionati dai client Firebase, account runtime e accessi cross-project non
  ancora verificati. Non si deduce che tutte le funzioni di produzione usino
  oggi il database staging o che il collegamento sia selezionato dal frontend.

Implicazioni per il piano: il backend URL staging del catalogo è un target
previsto, non una release operativa dimostrata. Occorre inventariare gli
account runtime delle funzioni esistenti, i loro accessi a MCP Dev e il routing
prima del bootstrap separato. Non modificare/reimpiegare le funzioni di
produzione né revocare accessi durante l'inventario. Nessun deploy eseguito.


### Esempio funzione produzione — YAML fornito dall'owner,16novembre2026

L'owner riporta regione `us-central1` e fornisce un export Cloud Run Service
(`serving.knative.dev/v1`) relativo a `admin-create-event`, non `get_all_events`.
L'export contiene anche configurazione sensibile: nessun payload sensibile è
riportato, copiato nel repository o usato per autenticarsi.

| Metadato | Riscontro nell'export |
|---|---|
| Funzione/target | `admin_create_event` |
| Service Cloud Run | `admin-create-event`, gestito da Cloud Functions |
| Progetto indicato | `mcp-website-2a1ad`; namespace/numero `407185703168` |
| Regione | `us-central1` |
| Runtime | `python310`, base image Google22 full |
| Account runtime | `407185703168-compute@developer.gserviceaccount.com` |
| Account dichiarato per build | `projects/mcp-website-2a1ad/serviceAccounts/407185703168-compute@developer.gserviceaccount.com` |
| Build indicata | `projects/407185703168/locations/us-central1/builds/0492faeb-deeb-4d5f-bb62-f415bf235d4e` |
| Revisione ready | `admin-create-event-00029-hip`,100% traffico nell'export |
| Ready | True nell'export |
| Configurazione pubblica progetto | `GCLOUD_PROJECT` e `FIREBASE_CONFIG.projectId`: `mcp-website-2a1ad` |
| Configurazione pubblica bucket | `STORAGE_BUCKET` e `FIREBASE_CONFIG.storageBucket`: `mcp-website-2a1ad.firebasestorage.app` |
| Bucket sorgenti build referenziato | `gcf-v2-sources-407185703168-us-central1` (progetto produzione) |
| Repository immagine referenziato | Artifact Registry `gcf-artifacts` in `us-central1`, progetto produzione |

Limiti: metadati di un export fornito dall'owner, non verifica API corrente
né inventario di tutte le funzioni. L'account dichiarato per build coincide
con quello runtime in questo export; ruoli e utilizzo nell'esecuzione build
restano da verificare. Non dedurre minimo privilegio dal solo nome account.

Questo export **non conferma accesso al database MCP Dev**. Le configurazioni
pubbliche indicano produzione, ma è presente `GOOGLE_APPLICATION_CREDENTIALS`:
progetto/identità effettivi del client Firestore dipendono anche dal codice e
dalle credenziali selezionate, non solo da `GCLOUD_PROJECT` o dal service account
runtime. Verificare binding IAM cross-project e configurazione effettiva senza
richiedere file credenziali o payload. Sono presenti variabili provider sensibili
con `value` inline; ciò non prova che i rispettivi provider siano attivi o che i
valori siano validi. La futura migrazione a Secret Manager resta distinta.
Nessuna invocazione della funzione, modifica IAM, revoca o deploy eseguiti.


### IAM staging — schermata owner del16novembre2026

Ruoli visualizzati nella schermata IAM fornita dall'owner:

| Principale | Ruoli mostrati |
|---|---|
| `firebase-admin-test@mcp-website-dev-39539.iam.gserviceaccount.com` | Firebase Admin |
| `firebase-adminsdk-fbsvc@mcp-website-dev-39539.iam.gserviceaccount.com` | Firebase Admin SDK Administrator Service Agent; Firebase Authentication Admin; Service Account Token Creator; Storage Admin |
| Account personale del proprietario | Owner (Legacy) |

`407185703168-compute@developer.gserviceaccount.com` non compare nell'elenco
visibile. Non è una verifica esaustiva dell'IAM effettivo: non esclude altri
binding, ereditarietà o un'identità applicativa diversa dal runtime.
L'elenco IAM non coincide necessariamente con l'elenco di tutti gli account
di servizio esistenti e non attesta chiavi, utilizzi o stato degli account.

Dal solo campo pubblico di percorso nello YAML già fornito:
`GOOGLE_APPLICATION_CREDENTIALS=./service_account.json`. Nessun file credenziali
aperto o richiesto. Il nome del file non identifica il suo progetto o client_email:
non associare automaticamente questa credenziale a `firebase-admin-test`.
Il collegamento storico produzione→MCP Dev resta da ricostruire.
Nessuna modifica IAM, chiave o configurazione effettuata.


### Account di servizio staging — elenco owner del16novembre2026

| Account visualizzato | Stato account | Descrizione visualizzata | Colonna chiavi |
|---|---|---|---|
| `firebase-admin-test@mcp-website-dev-39539.iam.gserviceaccount.com` | Enabled | Firebase Admin SDK for test environment | Un identificativo chiave visualizzato; identificativo non trascritto |
| `firebase-adminsdk-fbsvc@mcp-website-dev-39539.iam.gserviceaccount.com` | Enabled | Firebase Admin SDK Service Agent | No keys |

Provenienza: schermata dell'elenco account fornita dall'owner. La schermata
non stabilisce tipo, stato attivo/disabilitato, date o utilizzo della chiave
elencata per firebase-admin-test; Enabled è lo stato dell'account. No keys è
il riscontro della colonna per il secondo account, non prova dell'assenza di
ogni meccanismo di autenticazione. Non dimostrata l'associazione fra la chiave
elencata e il file ./service_account.json referenziato dal backend produzione.
Nessun payload/ID chiave registrato, nessuna chiave creata, usata o modificata.


La successiva schermata Chiavi di firebase-admin-test fornita dall'owner
(16novembre2026) mostra stato **Active** per la riga visibile. Il ritaglio non
mostra un tipo testuale né date di creazione/scadenza: non dedurli dall'icona.
Questo aggiorna il solo stato della chiave osservata, senza attestare utilizzo
corrente, contenuto del file credenziali del backend o assenza di altre chiavi
fuori dalla porzione visibile. Nessuna modifica o revoca eseguita.


### Cloud Build staging — schermata owner del16novembre2026

Aprendo la cronologia Cloud Build dello staging, l'owner viene indirizzato alla
pagina Cloud Build API (`cloudbuild.googleapis.com`) con pulsante **Enable**,
progetto selezionato `mcp-website-dev`. Registrato come API da abilitare nello
staging, sulla base della schermata owner; nessuna attivazione effettuata.

La cronologia non è stata consultata: non si deducono zero build storiche,
assenza di service agent o identità di build predefinita dal solo invito
all'abilitazione. Abilitazione API, verifica dell'identità build effettiva e
relativi permessi entreranno nel piano bootstrap autorizzato separatamente.
