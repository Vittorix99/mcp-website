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


### API abilitate staging — due schermate owner del16novembre2026

La schermata finale indica `1–44 of44`,100righe per pagina. Le due porzioni
fornite coprono44nomi nella dashboard API abilitate; evidenza owner, non
interrogazione indipendente Service Usage. Nessuna attivazione/disattivazione.

| Ambito rilevante | Nomi presenti nell'elenco |
|---|---|
| Dati e Storage | Cloud Firestore API; Cloud Datastore API; Cloud Storage for Firebase API; Cloud Storage; Cloud Storage API; Google Cloud Storage JSON API |
| Identità | Identity Toolkit API; Identity and Access Management (IAM) API; IAM Service Account Credentials API; Token Service API |
| Applicazione Firebase | Firebase Hosting API; Firebase Management API; Firebase Rules API |
| Infrastruttura | Cloud Pub/Sub API; Cloud Logging API; Cloud Monitoring API; Cloud Resource Manager API; Service Management API; Service Usage API |

Altri nomi visualizzati: Analytics Hub API; App Engine Admin API; BigQuery API;
BigQuery Connection API; BigQuery Data Policy API; BigQuery Data Transfer API;
BigQuery Migration API; BigQuery Reservation API; BigQuery Storage API;
Cloud Dataplex API; Cloud Runtime Configuration API; Cloud SQL; Cloud Testing API;
Cloud Trace API; Dataform API; FCM Registration API; Firebase App Distribution API;
Firebase Cloud Messaging API; Firebase Installations API; Firebase Remote Config API;
Firebase Remote Config Realtime API; Gemini for Google Cloud API; Gmail API;
Google Cloud APIs; Telemetry API.

**Non compaiono nell'elenco mostrato:** Cloud Build, Cloud Functions, Cloud Run,
Artifact Registry, Eventarc, Cloud Scheduler, Secret Manager. Cloud Build è
anche confermato dalla precedente pagina Enable. Per gli altri, registrare
assenza nell'elenco; riconciliare gli identificativi di servizio esatti col piano
bootstrap prima delle mutazioni. Presenza di un'API non attesta risorse create,
permessi sufficienti o utilizzo attuale; le metriche del periodo non sono
usate per dedurre servizi inattivi o eliminabili.

`Token Service API` viene trascritto come nome visualizzato: non è una prova
dell'abilitazione di `sts.googleapis.com` (Security Token Service per WIF).
Stato STS e pool/provider WIF ancora da verificare. L'abilitazione di Gmail,
Cloud SQL e BigQuery non dimostra che l'app li usi; nessuna pulizia proposta
sulla sola base dell'inventario API.


### Hosting staging — conferma owner del16novembre2026

L'owner conferma: nello staging non è presente il sito; il progetto è usato
per il database. Registrato come **nessun sito frontend staging distribuito
secondo conferma owner**, non come censimento API indipendente di siti o
canali Hosting provisionati. Nessuna release o URL frontend operativo verificato.

L'espressione owner «solo il db» descrive l'uso del progetto, non annulla le
risorse già osservate: Firestore, due bucket Storage, due account di servizio
e API abilitate. Non si deduce assenza di dati/file nei bucket.

Implicazione: primo bootstrap sia backend sia frontend staging; i target
cloudfunctions.net/web.app del catalogo repository sono configurazioni previste,
non prova di release attive. Build e smoke staging dovranno usare configurazione
staging esplicita e identità dedicate, dopo piano IAM e autorizzazione separata.
Nessuna creazione sito, deploy o aggiornamento dati effettuati.


### Fatturazione staging — schermata owner del16novembre2026

La pagina Account management dell'account **Firebase Payment**, tipo **Direct**,
mostra `mcp-website-dev` / `mcp-website-dev-39539` tra i progetti collegati.
L'account personale dell'owner compare come Billing Account Administrator.
Registrato il collegamento progetto→account sulla base della schermata.
Identificativo billing ed email personale non necessari all'inventario tecnico
non trascritti. Nessuna informazione di pagamento richiesta o usata.

La schermata fornita non espone un campo esplicito Active/billingEnabled:
non certifica autonomamente stato pagamenti, budget, quote o capacità di build.
Eventuale conferma operativa resta nel preflight bootstrap; nessuna modifica
all'account, al collegamento, ai ruoli billing o al piano effettuata.


### WIF staging — riscontro owner del16novembre2026

Dopo apertura della pagina Workload Identity Federation del progetto staging,
l'owner riporta che non esiste nulla. Registrato come **nessun pool WIF
presente secondo il riscontro owner nell'elenco consultato**; non una chiamata
API indipendente né verifica di eventuali pool eliminati/nascosti.
Non si deducono gli stati di tutte le API IAM/STS dalla sola vista vuota.

Pool/provider GitHub previsti dal piano restano da creare nel bootstrap,
con vincoli repository/workflow/ref/Environment e identità deploy espliciti,
soltanto dopo autorizzazione delle risorse e dei binding concreti. Nessun
pool, provider, service account, binding IAM o variabile GitHub creato ora.


### GitHub Environments — schermata owner del16novembre2026

Settings→Environments mostra «There are no environments for this repository»;
l'owner conferma assenza di Environment per `Vittorix99/mcp-website`.
`staging` e `production` restano quindi da predisporre. Questo dato non
censisce variabili/segreti Actions di repository o di organizzazione.
Nessun Environment, secret, variabile o regola creato/modificato.
Disponibilità di required reviewers/protezioni da riconciliare con piano
GitHub e visibilità repository prima di approvare il piano produzione.


### Authentication staging — riscontro owner del16novembre2026

Alla verifica dei metodi di accesso Firebase Authentication, l'owner riporta
**Email/Password** come provider abilitato nello staging. Nessuna schermata
utenti o dato personale richiesto. Configurazione email-link/passwordless,
domini autorizzati, template email e stato degli altri provider non verificati
indipendentemente; non dedurre email-link abilitato dalla sola voce Email/Password.
Nessun provider, account, dominio o template modificato.


### Domini Authentication staging — riscontro owner del16novembre2026

L'owner riporta **nessun dominio autorizzato nello staging** e precisa che
l'unico dominio è in produzione. Il nome di quel dominio e l'elenco produzione
non sono stati forniti; non trasferire automaticamente la configurazione fra
progetti. Riscontro owner, non lettura API indipendente.

L'elenco domini staging resta da riconciliare con URL e flussi Auth effettivi
nel piano bootstrap. Non si deduce che ogni operazione Email/Password sia
impossibile dalla sola assenza di domini riportata. Stato email-link ancora
non verificato. Nessun dominio aggiunto/rimosso o provider modificato.


### Email-link staging — schermata provider owner del16novembre2026

Il dettaglio del provider mostra **Email/Password attivo** ed **Email link
(passwordless sign-in) disattivato**. Questo completa il riscontro precedente:
abilitare Email/Password non attesta l'abilitazione dell'accesso senza password.
La schermata precedente dei template email non era una prova di questo stato.

La configurazione dei flussi login/ritorno email staging va concordata nel
bootstrap insieme ai domini e alle URL effettive. Nessuna opzione del provider,
nessun template e nessun dominio modificati durante l'inventario.


### PayPal sandbox — schermata owner del16novembre2026

La pagina API Credentials mostra esplicitamente modalità sandbox e una REST API
app visibile chiamata **Default Application**. La colonna Date and time riporta
`20/12/24,13:40` (fuso non indicato). Secret mascherato nella schermata; nessun
Client ID o Secret trascritto, richiesto, usato o caricato nel repository.

Questo prova la presenza dell'app visualizzata nella vista sandbox, non che sia
dedicata a MCP, che le credenziali correnti nel codice appartengano a quell'app,
né che autenticazione o pagamenti sandbox siano stati provati. Scelta dell'app
staging e associazione all'account merchant ancora da confermare. Disponibilità
di account sandbox Business/Personal per E2E ancora da verificare. Nessuna app,
credenziale o transazione PayPal creata/modificata durante l'inventario.


### Account PayPal sandbox — schermata owner del16novembre2026

La pagina mostra2account sandbox, entrambi etichettati Default:

| Tipo | Paese | App mostrate | Data creazione visualizzata |
|---|---|---|---|
| Business | IT | 1 | 20/12/24,13:40 |
| Personal | IT | 0 | 20/12/24,13:40 |

Email sandbox non trascritte perché non necessarie all'inventario; nessuna
password o credenziale richiesta. La vista non mostra uno stato esplicito degli
account né attesta login, fondi/currency di test o transazioni riuscite.
L'associazione nominale fra l'unica app Business e Default Application resta
da confermare nel dettaglio app: coincidenza di conteggi/date non è una prova.
Nessun account/app creato o modificato, nessun pagamento eseguito.


## Proposta unica: bootstrap staging e IAM — 16 novembre 2026

**Stato:** piano da approvare; sola preparazione documentale. Nessuna mutazione
cloud eseguita o autorizzata da questo testo. Il piano operativo del13novembre
rimane il riferimento; questa sezione ne concretizza i prerequisiti osservati
e supera le precedenti ipotesi generiche di ruoli per lo staging.

**Obiettivo:** ottenere uno staging autonomo, con codice approvato, identità
separate e prima baseline verificata, prima di attivare il deploy automatico.
**Architettura:** frontend Hosting+SSR Node20 e Functions Python3.11 in
us-central1; Firestore esistente `(default)`/nam5 e Storage già presente.
GitHub OIDC/WIF impersona solo l'identità deploy; runtime e build usano account
Google gestiti senza file chiave. Nessun collegamento nuovo alla produzione.
**Spec:** piano Segreti/deploy in questo documento, inventario owner soprastante,
config/environment_catalog.json e contratti di scripts/deployment/.

### 1. Riepilogo verificato e confini

| Elemento | Stato osservato / conseguenza |
|---|---|
| Progetto | mcp-website-dev-39539,numero1005755179074 |
| Dati | Firestore `(default)`,Native,nam5; backup pianificati disabilitati; contenuto/provenienza e altre copie di recupero non classificati |
| Storage | Firebase apre mcp-website-dev-39539.firebasestorage.app; secondo bucket mcp-website-dev-39539 con uso ignoto |
| Backend/frontend | Nessuna funzione e nessun sito distribuito secondo owner; i target del catalogo non sono una baseline |
| Identità legacy | Due account staging Enabled; chiave osservata Active su firebase-admin-test. Non riusare o revocare durante il bootstrap |
| Build | Cloud Build API da abilitare; identità effettiva di build staging non osservata |
| API |44abilitate; servizi di deploy mancanti nell'elenco; STS da verificare per ID esatto |
| GitHub/WIF | Nessun Environment e nessun pool secondo owner; protezioni produzione e piano GitHub non verificati |
| Auth | Email/Password attivo,email-link spento; domini staging assenti secondo owner |
| PayPal | Default Application sandbox e account Business/Personal presenti; associazione merchant/credenziali ed E2E non provati |

**Confini invariati:** nessuna modifica a mcp-website-2a1ad, nessuna cancellazione
staging, nessun import/copia dati produzione, nessuna revoca/rotazione legacy.
Sender, mail applicativa e Pass2U restano disabilitati; gender/SoundCloud fake,
PayPal sandbox. Invii Auth di prova soltanto a destinatari di test concordati.
La valutazione dei residui high è rinviata per decisione owner, non risolta.

### 2. Risorse proposte, tutte nel progetto staging

Account nuovi, senza chiavi scaricabili:

| ID account | Responsabilità |
|---|---|
| github-deploy | Deploy delle release approvate; nessun accesso diretto ai payload Secret Manager |
| functions-build | Build Python e SSR; nessun accesso a dati/Auth/secret provider |
| app-runtime | Backend Python e identità di consegna Eventarc/Scheduler |
| web-runtime | SSR e operazioni Auth del framework; nessun Firestore amministrativo o secret provider |

Ogni email termina in `@mcp-website-dev-39539.iam.gserviceaccount.com`.
Bucket applicativo proposto: `mcp-website-dev-39539.firebasestorage.app`, già
presente; niente creazione/rinomina/spostamento bucket o database. Prima del
binding verificare che sia il bucket voluto; non toccare il secondo bucket.
Hosting site ID proposto `mcp-website-dev-39539`,da creare solo se non già
provisionato; URL atteso https://mcp-website-dev-39539.web.app. Auth domain del
progetto da verificare rispetto alla Firebase web app effettiva.
Artifact Registry Docker `gcf-artifacts`,us-central1; bucket sorgenti/upload
creati dal servizio Functions v2 inventariati dopo il provisioning. Conservare
immagini/revisioni della baseline per almeno la finestra rollback30giorni;
non accettare una cleanup policy automatica che la invalidi.
Secret unico iniziale: `PAYPAL_CLIENT_SECRET`,valore sandbox inserito dall'owner
fuori chat/Git/log; Client ID pubblico della stessa app in configurazione.
Non creare secret dei provider disabilitati.

### 3. Binding IAM proposti: nessun Owner/Editor ai nuovi account

`P` nella tabella è esclusivamente mcp-website-dev-39539. I ruoli sono una
proposta nominativa da verificare con policy/supported permissions prima
dell'applicazione, non una prova cloud di minimo privilegio.

| Principale | Scope | Ruolo/permessi proposti |
|---|---|---|
| app-runtime | P,Firestore `(default)` | roles/datastore.user; limitarne lo scope al database se supportato dalla policy verificata |
| app-runtime | P | Ruolo custom `stagingAppAuth`: firebaseauth.users.create,get,update,delete,sendEmail (nomi completi firebaseauth.users.* elencati,senza wildcard) |
| app-runtime | Solo bucket applicativo | roles/storage.objectAdmin |
| app-runtime | Solo secret PAYPAL_CLIENT_SECRET | roles/secretmanager.secretAccessor |
| app-runtime | P | roles/eventarc.eventReceiver |
| app-runtime,identità Eventarc/Scheduler | Solo servizi trigger/scheduler del manifest approvato | roles/run.invoker; nessun allUsers sui worker |
| web-runtime | P | Custom `stagingWebAuth`: firebaseauth.users.get e firebaseauth.users.createSession |
| web-runtime | Solo se stesso | Custom `stagingBlobSigner`: iam.serviceAccounts.signBlob,per createCustomToken del framework; non su altri account |
| functions-build | P | roles/logging.logWriter |
| functions-build | Solo repository gcf-artifacts | roles/artifactregistry.writer |
| functions-build | Solo bucket sorgenti/upload inventariati | roles/storage.objectViewer; nessun accesso al bucket applicativo |
| github-deploy | P | roles/cloudfunctions.developer,roles/run.developer,roles/firebasehosting.admin,roles/cloudbuild.builds.editor,roles/eventarc.admin,roles/cloudscheduler.admin,roles/serviceusage.serviceUsageConsumer |
| github-deploy | P | Custom `stagingReleaseMetadata`: resourcemanager.projects.getIamPolicy,per preflight IAM della CLI; nessuna scrittura policy |
| github-deploy | Solo4account nuovi | roles/iam.serviceAccountUser (actAs/get); nessun binding su account produzione/legacy |
| github-deploy | Solo secret PAYPAL_CLIENT_SECRET | roles/secretmanager.viewer (metadati,non payload) |
| github-deploy | Solo repository gcf-artifacts | roles/artifactregistry.reader,per metadati del deploy |
| github-deploy | Solo bucket applicativo | Custom `stagingBucketMetadata`: storage.buckets.get,per cloud_preflight; nessun accesso oggetti |
| Principal WIF vincolato | Solo github-deploy | roles/iam.workloadIdentityUser |

Ruoli custom completi: `projects/P/roles/stagingAppAuth`,stagingWebAuth,
stagingBlobSigner,stagingReleaseMetadata e stagingBucketMetadata. Verificare che le singole permission
siano supportate nei custom role; nessun allargamento automatico in caso di403.
Lo Storage Admin SDK corrente non mostra chiamate generate_signed_url: nessun
signBlob aggiunto al backend per ipotesi. Entrambi i runtime potranno ottenere
le proprie credenziali ADC; nessun GOOGLE_APPLICATION_CREDENTIALS persistente.

**Bootstrap privilegiato:** la CLI14.26.0 richiede functions.setIamPolicy per
creare nuovi HTTP. Quando si aggiungono i primi trigger a un backend prima
solo HTTP,ensureServiceAgentRoles propone anche Token Creator per il service
agent Pub/Sub e Run Invoker/Eventarc Receiver per il default Compute a scope
progetto,anche se i runtime sono custom. La sessione owner potrebbe applicarli:
non è consentito lasciare questa mutazione implicita.

Prima creazione eseguita dall'owner con sessione personale esistente,dopo
autorizzazione puntuale e attraverso un percorso operator OAuth separato.
L'adattatore bootstrap deve sostituire l'automatismo IAM della CLI con sola
validazione dei binding già applicati dall'owner nel manifest approvato:
nessun setIamPolicy di progetto durante il deploy,nessun default Compute o
Token Creator indiscriminato. Registrare/dimostrare con test il passaggio
HTTP-only→primi trigger. Non assegnare Owner/IAM Admin a github-deploy. Per i normali rilasci
si ammette solo topologia già verificata; nuovi endpoint/trigger richiedono
un nuovo bootstrap controllato. Non assumere che Functions Developer basti
per il primo deploy. Deploy di codice fidato può comunque esercitare i diritti
del runtime: assenza di Secret Accessor sul deploy non isola da codice malevolo.

Service agent da censire dopo abilitazione: Functions
`service-1005755179074@gcf-admin-robot.iam.gserviceaccount.com`,Cloud Build
`service-1005755179074@gcp-sa-cloudbuild.iam.gserviceaccount.com`,Eventarc
`service-1005755179074@gcp-sa-eventarc.iam.gserviceaccount.com`,Scheduler
`service-1005755179074@gcp-sa-cloudscheduler.iam.gserviceaccount.com` e Pub/Sub
`service-1005755179074@gcp-sa-pubsub.iam.gserviceaccount.com`,se creati.
Mantenere solo i ruoli di servizio documentati sulle rispettive identità;
non assegnare ruoli serviceAgent agli account applicativi o GitHub. Per eventuali
Token Creator del trasporto verificare il requisito reale e il target prima
del binding; nessuna concessione indiscriminata al progetto.

### 4. WIF e GitHub: target concreto, attivazione differita

Pool global `github-actions`,provider OIDC `main-release`,issuer
https://token.actions.githubusercontent.com,progetto1005755179074.
Provider resource:
`projects/1005755179074/locations/global/workloadIdentityPools/github-actions/providers/main-release`.
Mapping google.subject=assertion.sub e attributi per repository_id,repository,
ref,workflow_ref,job_workflow_ref. Condizione proposta congiunta:
- repository_id == '899139661' e repository == 'Vittorix99/mcp-website';
- ref == 'refs/heads/main';
- workflow_ref == 'Vittorix99/mcp-website/.github/workflows/release.yml@refs/heads/main';
- job_workflow_ref == 'Vittorix99/mcp-website/.github/workflows/deploy-environment.yml@refs/heads/main';
- sub == 'repo:Vittorix99/mcp-website:environment:staging'.

Binding SA per principalSet del pool/attribute.repository_id/899139661,con
restrizione provider sopra. Confermare subject effettivo e customizzazione
OIDC prima del grant; test negativi per fork,PR,altro branch/workflow/Environment.
Non indebolire a solo nome repository o solo branch. Nessun trust production
nel provider staging. Environment GitHub iniziale solo `staging`,main-only.
Variabili Environment:4account (`BUILD_SERVICE_ACCOUNT` nuovo incluso),WIF_PROVIDER,
FIREBASE_API_KEY,FIREBASE_APP_ID,PAYPAL_CLIENT_ID e flag di baseline solo dopo prove.
Flag repository ENABLE_STAGING_DEPLOY/ENABLE_PRODUCTION_DEPLOY restano assenti
o false. Environment production/protezioni verranno trattati nel gate produzione.

**Decisione main preservata:** niente merge aggiuntivi finché l'owner non
approva l'integrazione finale. Nessun trust temporaneo al ramo di sviluppo e
nessuna attivazione push/main per aggirare la decisione. Il primo deploy potrà
partire solo su SHA esplicitamente approvato con canale di rilascio concordato;
questo piano propone di attendere l'integrazione main autorizzata.

### 5. Sequenza con risultati verificabili

- [x] **A — Preparazione repository,senza cloud.** Correggere il solo bucket
  staging nel catalogo e relativi assert. Aggiungere BUILD_SERVICE_ACCOUNT a
  release.py/manifest/workflow e al digest/attestazione di configurazione.
  L'adattatore firebase.cjs dovrà impostare buildConfig.serviceAccount tramite
  il converter Functions v2 della CLI fissata,per Python e SSR,senza patchare
  node_modules,validando progetto/codebase/account. CLI14.26.0 non inoltra oggi
  un build account custom nel converter: creare un account senza questo
  adattamento lascerebbe le build sull'identità di default non verificata.
- [x] **A — Bootstrap esplicito staging-only.** Nuovo percorso controllato in
  scripts/deployment/bootstrap_staging.py e relativo adattatore
  scripts/deployment/firebase-bootstrap.cjs,riusando solo i validator/configuratori
  pubblici di release.py,per prima release senza baseline. Il bootstrap usa
  esclusivamente l'owner OAuth interattivo locale autorizzato,con identità
  operatore/progetto/SHA verificati e gestione delle credenziali confinata ai
  comandi owner: niente JSON service_account/chiavi private,token stampati o
  credenziali negli artifact. Non riusare validateFederation per la sessione
  personale e non indebolirne la validazione external_account dei normali job
  WIF. Input bootstrap nominativi: BOOTSTRAP_APPROVED_SHA e
  BOOTSTRAP_OPERATOR_EMAIL,confrontati con checkout e sessione operatore attiva.
  Separare esplicitamente autenticazione operator-bootstrap e release.
  Rifiuta produzione,inventario inatteso e SHA non approvato;
  non falsifica PAYMENT_ROLLOUT_APPROVED o ROLLBACK_BASELINE_VERIFIED. Se una
  creazione parziale esiste,fermare e inventariare: nessuna cancellazione/retry
  distruttivo automatico. Il normale rilascio continua a richiedere baseline.
- [x] **A — Prove prima dell'approvazione cloud.** Regressioni per bucket,
  build account su Python/SSR,converter realeCLI,wrong-project,WIF non valido,
  prima baseline e rifiuto bootstrap produzione. Test di separazione owner
  OAuth/WIF,identità operatore diversa dal manifest,chiavi private e secret nei
  log/artifact. Test contro il modulo realeCLI del primo deploy con trigger:
  nessuna chiamata setIamPolicy di progetto e nessun grant/default Compute
  implicito; un binding mancante deve bloccare,non essere aggiunto. Regressione
  cloud_preflight con deploy autorizzato al solo storage.buckets.get sul bucket
  applicativo. Test del selettore realeCLI:
  prima tranche solo HTTP Python+SSR,nessun Firestore trigger o scheduler.
  Filtri per funzione `functions:python_codebase:NAME`,confronto insieme esatto
  con manifest SDK; non basta un prefisso. Test e build pertinenti,unica review
  Sol high del blocco codice; preparare manifest risorse/policy redatto.
- [ ] **B — Approvazione cloud separata.** Presentare SHA,API,identità,scope e
  diff IAM reali. Owner abilita solo API mancanti della allowlist:
  cloudfunctions.googleapis.com,run.googleapis.com,cloudbuild.googleapis.com,
  artifactregistry.googleapis.com,eventarc.googleapis.com,cloudscheduler.googleapis.com,
  secretmanager.googleapis.com,sts.googleapis.com,iamcredentials.googleapis.com,
  iam.googleapis.com,serviceusage.googleapis.com,cloudresourcemanager.googleapis.com,
  firebase.googleapis.com,firebasehosting.googleapis.com,firestore.googleapis.com,
  storage.googleapis.com,firebasestorage.googleapis.com,pubsub.googleapis.com,
  identitytoolkit.googleapis.com,logging.googleapis.com. API già abilitate restano.
  BillingEnabled,quote e supported IAM verificati; inventariare service agent e
  sorgenti generate,poi applicare soltanto i binding nominativi approvati.
  Se i bucket sorgente/upload non esistono ancora,provisionarli e rilevarli
  prima di avviare la prima build,senza concedere accesso globale ai bucket:
  la preparazione sorgenti non deve distribuire funzioni né modificare dati
  applicativi e rientra nel manifest di provisioning autorizzato.
- [ ] **B — Configurazioni concordate.** Creare4SA,WIF,Environment staging,
  site/repository mancanti. Sul solo repository gcf-artifacts di us-central1,
  concordare e predisporre opt-out Firebase cleanup
  (`firebase-functions-cleanup-opted-out=true`) e nessuna policy DELETE durante
  il bootstrap: immagini conservate fino alla prova rollback e successiva
  decisione esplicita di retention. Nessun --force o default di un giorno.
  Owner inserisce sandbox secret e Client ID della
  stessa app verificata; abilitazione email-link e domini/return URL della web
  app staging,senza import utenti produzione. Verificare regole Firestore/Storage
  e indici cloud rispetto ai file tracciati: nessuna distribuzione automatica
  di rules/indexes o riuso permissivo senza diff e autorizzazione owner.
- [ ] **C — Prima release controllata.** Prima di esporre nuovi handler:
  classificare dati/file esistenti,verificare dipendenze legacy e avere piano
  di conservazione/ripristino approvato. Deploy iniziale solo HTTP+SSR sullo SHA
  autorizzato; health e configurazione staging,nessun trigger dati/cron ancora.
  Se fallisce la prima release non c'è vecchia baseline da ripristinare:
  fermare la promozione e gestire le sole risorse create secondo manifest owner,
  mantenendo i dati. Mai fallback verso funzioni di produzione.
- [ ] **C — Dati staging,gate dedicato.** Dopo bootstrap iniziale e prima E2E:
  owner autorizza eventuale export/reset/import di soli dati sintetici. Gli
  attuali loader demo/emulator-only non vanno puntati al cloud o privati delle
  guardie. Piano loader cloud con scope,collisioni,AuthUID,pulizia e recupero
  va definito/revisionato separatamente prima di ogni applicazione.
- [ ] **C — Completamento topologia.** Dopo messa in sicurezza dei dati,deploy
  degli8trigger Firestore e3scheduler dal manifest approvato; rispettare
  Eventarc nam5 per database nam5 e destinazione funzioni us-central1. Verificare
  account invocanti e Run Invoker per i soli worker. La prima tranche non è
  una baseline completa e non può abilitare la pipeline ordinaria.
- [ ] **C — Baseline/E2E/rollback.** Verificare manifest completo,provider
  sandbox/disabilitati,login admin/socio e operazioni critiche su dati sintetici.
  Produrre baselineA completa,rilascioB stessa topologia e rollback realeB→A
  con numeri versione secret e health. Solo dopo prove owner valide impostare
  i flag di baseline/rollout e,con separata decisione di integrazione,il flag
  repository staging. Flag produzione resta false;nessuna promozione implicita.

### 6. Criteri di stop e approvazione richiesta

Fermarsi su identità/default build non attesi,permessi non supportati,403,
creazione parziale,configurazione produzione,API fuori allowlist,indice/regola
non revisionati,claim OIDC diverso o dati non classificati. Nessuna correzione
IAM automatica per superare un errore. L'inventario è sufficiente per questa
proposta,non è dichiarato esaustivo: uso del secondo bucket,origine dei dati,
lineage della chiave legacy,billingEnabled,piano GitHub/claim reali e permessi
cloud effettivi restano verifiche esplicite ai gate prima delle azioni pertinenti.

**Prossima approvazione richiesta:** il solo bloccoA di preparazione repository
con review e test; non le operazioniB/C. Niente cloud finché manca il distinto
consenso su manifest concreto dopo A. I gate dati e produzione restano separati.

Fonti primarie controllate il16novembre2026:
[build account e scope](https://docs.cloud.google.com/functions/docs/building),
[IAM Functions](https://docs.cloud.google.com/functions/docs/concepts/iam),
[WIF pipeline](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines),
[Eventarc locations](https://docs.cloud.google.com/eventarc/docs/locations),
[Auth permissions](https://docs.cloud.google.com/identity-platform/docs/audit-logging),
[service-account signing](https://docs.cloud.google.com/iam/docs/service-account-permissions).


**Review del piano:** unica review indipendente Sol high del16novembre2026;
2P1 (separazione auth owner/WIF e IAM implicito della CLI) e1P2 (metadati bucket),
accettati e corretti in questa proposta. Nessun secondo dispatch; nessuna
implementazione o prova cloud dedotta dalla review documentale.

### Blocco A — preparazione repository del 16 novembre 2026

Autorizzato dall'owner il solo lavoro locale. Implementazione e prove locali
non autorizzano il provisioning B o l'esecuzione cloud C.

- Catalogo staging corretto al bucket osservato
  `mcp-website-dev-39539.firebasestorage.app`; produzione invariata.
- Quattro identità distinte nel manifest. `BUILD_SERVICE_ACCOUNT` entra nel
  digest e nel workflow; il converter reale Functions v2 della CLI14.26.0
  riceve l'account build esplicito per Python e SSR, mantenendo i runtime separati.
- Il deploy ordinario conserva autenticazione WIF, vincoli main e baseline.
  L'adattatore legge i binding IAM richiesti e blocca le scritture di progetto;
  modifiche alla policy invoker esistente richiedono provisioning esplicito.
  Solo il bootstrap autorizzato può inizializzare l'invoker pubblico dei nuovi
  servizi HTTP approvati. Non assegna ruoli al Compute account di default.
- `bootstrap_staging.py prepare` prepara un piano pubblico offline. Discovery
  SDK in ambiente demo, con connessioni socket bloccate:130 HTTP,8 Firestore,
  3 scheduler. Il selettore reale CLI include esattamente i130 HTTP.
- `bootstrap_staging.py apply` è un comando cloud futuro, non eseguito nel
  blocco A. Rifiuta produzione,CI,checkout sporco,SHA diverso o non integrato
  in origin/main. Confronta il piano con configurazione e discovery correnti;
  verifica operatore gcloud e OAuth personale, credenziale privata
  `authorized_user`, email verificata e profilo Firebase temporaneo vuoto.
  Non accetta WIF o chiavi service account nel percorso operatore.
- Prima di creare risorse controlla inventario Functions in tutte le regioni,
  Cloud Run managed globale e assenza di release Hosting. Una creazione
  parziale blocca il nuovo tentativo: nessuna cancellazione o rollback automatici.
  Dopo deploy verifica endpoint,account build/runtime,SHA/digest attivi e health.
  L'esito HTTP+SSR non viene dichiarato baseline della topologia completa.

**Input futuri, da predisporre insieme dopo B e approvazione C:** configurazione
pubblica già prevista per staging,`BOOTSTRAP_APPROVED_SHA` (commit main
approvato),`BOOTSTRAP_OPERATOR_EMAIL`,e solo per l'esecuzione
`BOOTSTRAP_OPERATOR_ADC` (percorso assoluto di OAuth ADC personale, mai il suo
contenuto in chat o negli artifact). `BOOTSTRAP_CLOUD_APPROVED=true` e
`BOOTSTRAP_DATA_REVIEWED=true` attestano due consensi distinti dell'owner;
non impostarli come conseguenza dei test locali. Restano necessari checkout
pulito,Node20,Python3.11,CLI14.26.0 e assenza di dotenv ereditati nel checkout
di rilascio. Non aggiungere `PAYMENT_ROLLOUT_APPROVED` o
`ROLLBACK_BASELINE_VERIFIED` per simulare una baseline iniziale.

Sequenza dei comandi, **documentata e non eseguita sul cloud**:

```sh
.venv/bin/python scripts/deployment/bootstrap_staging.py prepare --environment staging
# Solo dopo provisioning, revisione del piano e consensi cloud/dati:
.venv/bin/python scripts/deployment/bootstrap_staging.py apply --environment staging
```

Il piano e il risultato contengono solo metadati pubblici in `.local/release/`.
La credenziale non viene copiata; gli errori dei processi esterni non vengono
stampati perché potrebbero includere dati di autenticazione. In caso di
fallimento dopo l'avvio,`bootstrap-result.json` indica la necessità di inventario
manuale prima di qualsiasi seguito. Un esito positivo lascia separati data gate,
trigger/cron,E2E sandbox e prova baseline completa A→B→rollback A.


**Verifica locale finale A:**1413 unitari backend,522 scenari API,57 Auth,
103 strumenti e68 configurazione/frontend passati. Build e smoke isolato
Firestore/Auth/Storage/Functions/API/8 trigger passati. Lint0 errori e53 warning
preesistenti. Review indipendente unica Sol high:3P1 e1P2 accettati e corretti
con regressioni RED→GREEN (formato OAuth SDK reale,cancellazione/retry del
Fabricator reale,inventario incompleto con exit0,retention prima del deploy).
OAuth accetta esclusivamente true booleano o "true" testuale; false e stringhe
arbitrarie sono rifiutati. Gli inventari globali con stderr non vuoto si fermano
senza stampare diagnostica. In bootstrap la CLI non può eliminare o aggiornare
funzioni,né configurare automaticamente cleanup policy.

Decisione di conservazione iniziale: preflight Python e CLI richiedono opt-out
Firebase e nessuna policy DELETE nel repository esatto. È più restrittiva del
solo minimo30giorni: evita di applicare una retention non ancora concordata
alla prima baseline. La configurazione concreta e gli eventuali costi di
conservazione appartengono al successivo blocco B, da discutere con l'owner.
Nessuna prova OAuth/IAM/deploy reale né CI remota attestata da questi test.
