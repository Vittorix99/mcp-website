# Transizione credenziali — Core WS1

**Stato corrente —20 novembre 2026:** PR11/12/13 integrate su main; sorgente
bootstrap preparata su `e5c7ac5349e3dcc2539e8c1bfb90740ffdf529a7`, CI main
completata con successo. Billing staging confermato `billingEnabled=true`
il18novembre; preflight API/identità/bucket/segreti PASS. Nessun bootstrap
eseguito e flag di promozione non abilitati. Owner classifica Firestore staging
come copia storica di produzione e ne autorizza la cancellazione; preservare
Storage e utenti Auth. Controllo20novembre su141funzioni produzione completato:
nessuna dipendenza runtime da staging rilevata nel perimetro verificato.
Piano di recupero/bonifica proposto in4d; risorse aggiuntive e sospensione client
ancora da approvare. Nessun documento cloud cancellato.

**Checkpoint infrastruttura —17 novembre 2026 (storico):** inventario staging raccolto, quattro
identità dedicate create, API abilitate e lotto IAM applicato; repository
`us-central1/gcf-artifacts` predisposto. Profilo E2E e quattro contenitori secret
predisposti (dettagli3h); versioni1 PayPal sandbox, MailerSend e SoundCloud
inserite e abilitate; Gender resta vuoto. Gmail di test collegata.
API Gender non funzionante secondo owner: correzione differita, profilo staging
Gender fake; non serve inserire GENDER_API_KEY per il prossimo gate.
Sender resta sospeso in attesa del chiarimento richiesto all'owner. Environment
GitHub staging main-only con14variabili pubbliche e WIF ristretto configurato;
prova con token GitHub autentico e scambio STS ancora da eseguire. Hosting site
esistente senza release; domini Auth staging presenti, email-link ora abilitato.
Budget15EUR/mese con soli avvisi verificato; bucket upload e sorgenti predisposti
con viewer build dedicato. Riuso sorgenti da parte di Functions e prove
bootstrap/E2E/rollback restano da validare durante il rilascio autorizzato;
billingEnabled non attestato via REST (Cloud Billing API disabilitata).
La valutazione dei residui high è differita su indicazione owner. Nessun deploy,
aggiornamento dati cloud o intervento in produzione; main hold invariato.
I checkpoint precedenti sotto riportati sono storici, non lo stato corrente.

**Checkpoint storico del 2026-11-15:** preparazione repository segreti/deploy integrata nel worktree `.worktrees/core-ws2`, ramo `core-age-data-integrity`; ultimo commit applicativo `9374efb` (Q-05), PR #12 draft dipendente da PR #11. CI #11 passata sul commit `0b85eb7` secondo il checkpoint storico; CI #12 non confermata. Le prove locali Q-05 sono registrate in `docs/process/NEXT_SESSION.md` e non attestano un deploy. Il ramo originario `ci/staging-deployment` resta un riferimento storico. Inventario cloud e identità build, piano IAM concreto e autorizzazione di attivazione restano aperti. Nessuna creazione di identità, modifica IAM, rotazione/revoca o deploy deriva dalla sola presenza di questo documento.

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

**Stato aggiornato:** blocco A repository completato0a17e98;stima costi
b177bbd. Blocco B in corso:4account dedicati creati,8API autorizzate abilitate
(con2dipendenze Google),5ruoli custom e17grant nominativi ora applicati e
verificati. Repository Docker gcf-artifacts us-central1 creato e2grant scoped
verificati. Editor default invariati per decisione owner. Controllo Functions
aggiornato43192d4. Secret,WIF e altre configurazioni ancora aperti;nessun
deploy o aggiornamento dati. Evidenze e avanzamento nelle sezioni3c–3f.

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
| app-runtime | Policy sul progetto P con condizione `resource.name == "projects/mcp-website-dev-39539/databases/(default)"` | roles/datastore.user; condizione documentata da Firebase,da verificare sul binding effettivo prima del grant |
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

### 3a. Manifest B: destinatari nominativi e stato delle assegnazioni

Qui **manifest** significa prospetto delle modifiche desiderate. La tabella
IAM della sezione3 descrive lo stato desiderato;il lotto eseguito ha un
piano JSON privato e snapshot/diff delle policy,riepilogati nella sezione3e. I file
`.local/release/config.json` e `bootstrap-plan.json`,generati dai comandi
locali,sono configurazioni di rilascio e non assegnano permessi IAM. Nessuna
assegnazione elencata qui va dedotta dal solo prospetto:lo stato applicato
è registrato separatamente nella sezione3e.

I quattro destinatari previsti nel progetto staging sono precisamente:

| Nome usato nella tabella3 | Principale IAM completo |
|---|---|
| github-deploy | `serviceAccount:github-deploy@mcp-website-dev-39539.iam.gserviceaccount.com` |
| functions-build | `serviceAccount:functions-build@mcp-website-dev-39539.iam.gserviceaccount.com` |
| app-runtime | `serviceAccount:app-runtime@mcp-website-dev-39539.iam.gserviceaccount.com` |
| web-runtime | `serviceAccount:web-runtime@mcp-website-dev-39539.iam.gserviceaccount.com` |

**Progresso verificato CLI —16novembre2026:**su richiesta esplicita owner,
creati github-deploy,functions-build,app-runtime e web-runtime nel progetto
mcp-website-dev-39539,numero1005755179074,lifecycleACTIVE verificato via API.
Comandi con account owner e --project staging espliciti;progetto predefinito
locale production lasciato invariato. Readback indipendente per tutti e4:
account Enabled,0chiavi gestite dall'utente,0ruoli direttamente assegnati nella
policy di progetto,0binding nella policy di ciascun nuovo service account.
Nessun grant IAM o file chiave creato. Inventario prima della creazione:
soltanto i due SA legacy già riportati dall'owner. La richiesta CLI supera
la preferenza per console manuale in questo passaggio;restano le approvazioni
previste per i binding IAM e le fasi deploy/dati. Non si deduce assenza di ogni
possibile accesso ereditato dal solo conteggio dei ruoli diretti.

Le righe a scope P sono binding nella policy di
`projects/mcp-website-dev-39539`,mai produzione. Le altre risorse esatte sono:

- Database autorizzato dalla condizione:
  `projects/mcp-website-dev-39539/databases/(default)`. datastore.user permette
  lettura e scrittura,inclusa cancellazione,dei documenti del database;
  non è un filtro per singola collezione.
- Bucket applicativo:`gs://mcp-website-dev-39539.firebasestorage.app`.
  objectAdmin concede gestione degli oggetti,inclusa cancellazione;il deploy
  riceve invece soltanto storage.buckets.get sul bucket tramite ruolo custom.
- Secret sandbox:
  `projects/mcp-website-dev-39539/secrets/PAYPAL_CLIENT_SECRET`.
  secretAccessor al backend;secretmanager.viewer al deploy,per i metadati.
- Repository immagini:
  `projects/mcp-website-dev-39539/locations/us-central1/repositories/gcf-artifacts`.
  writer alla build e reader al deploy.
- Firma SSR:policy sul solo service account
  `web-runtime@mcp-website-dev-39539.iam.gserviceaccount.com`,assegnata allo
  stesso web-runtime. Nessun signBlob sul backend o su altri account.
- actAs del deploy:quattro binding separati,uno sulla policy di ciascuno dei
  quattro nuovi account sopra,con membro github-deploy e
  `roles/iam.serviceAccountUser`.

I cinque ruoli custom proposti hanno questi soli permessi. Il16novembre2026
queryTestablePermissions sul progetto ha confermato tutti i9permessi distinti
GA e SUPPORTED (valore di default del campo omesso). I ruoli sono stati poi
creati e verificati nel lotto3e:

| ID ruolo custom nel progetto staging | includedPermissions esatti |
|---|---|
| `stagingAppAuth` | `firebaseauth.users.create`, `firebaseauth.users.get`, `firebaseauth.users.update`, `firebaseauth.users.delete`, `firebaseauth.users.sendEmail` |
| `stagingWebAuth` | `firebaseauth.users.get`, `firebaseauth.users.createSession` |
| `stagingBlobSigner` | `iam.serviceAccounts.signBlob` |
| `stagingReleaseMetadata` | `resourcemanager.projects.getIamPolicy` |
| `stagingBucketMetadata` | `storage.buckets.get` |

Ogni ID completo è `projects/mcp-website-dev-39539/roles/ID`.
I permessi firebaseauth sono presenti sia nel catalogo ufficiale sia nella
query del progetto;questo non equivale a una creazione riuscita del custom role.
I ruoli `roles/...` della tabella3 sono pacchetti predefiniti Google,non
permessi atomici: prima dell'applicazione salvare gli includedPermissions
correnti insieme al diff,senza promettere che un'etichetta contenga un solo
permesso o che il suo contenuto sia immutabile.

**Accesso GitHub WIF proposto:**membro
`principalSet://iam.googleapis.com/projects/1005755179074/locations/global/workloadIdentityPools/github-actions/attribute.repository_id/899139661`,
ruolo `roles/iam.workloadIdentityUser` sulla sola policy di github-deploy.
Le condizioni del provider della sezione4 devono restringere congiuntamente
repository,workflow,main ed Environment staging. Non assegnare questo ruolo
agli account runtime/build né un ruolo Owner all'utente GitHub. Il principalSet
è completo come stringa,ma il binding resta non applicabile finché claim e
provider effettivi non sono verificati.

**Identità Google gestite,distinte dai quattro account applicativi:**

| Principale completo da censire dopo abilitazione API | Ruolo di servizio sul solo progetto staging |
|---|---|
| `serviceAccount:service-1005755179074@gcf-admin-robot.iam.gserviceaccount.com` | `roles/cloudfunctions.standardServiceAgent`;compatibilità locale col ruolo legacy solo se già assegnato |
| `serviceAccount:service-1005755179074@gcp-sa-cloudbuild.iam.gserviceaccount.com` | `roles/cloudbuild.serviceAgent` |
| `serviceAccount:service-1005755179074@gcp-sa-eventarc.iam.gserviceaccount.com` | `roles/eventarc.serviceAgent` |
| `serviceAccount:service-1005755179074@gcp-sa-pubsub.iam.gserviceaccount.com` | `roles/pubsub.serviceAgent` |
| `serviceAccount:service-1005755179074@gcp-sa-cloudscheduler.iam.gserviceaccount.com` | `roles/cloudscheduler.serviceAgent` |

Si verificano i binding già creati dal servizio;non si aggiungono duplicati
né questi ruoli agli account applicativi. Il controllo CLI iniziale richiede
Functions/Build;Eventarc/PubSub e eventarc.eventReceiver servono con i trigger
nella fase C successiva. Scheduler e trigger rimangono esclusi dal primo
deploy HTTP+SSR. Un eventuale Token Creator per il trasporto non è un grant
di progetto approvato:necessità e destinatario specifico vanno verificati.

**Righe ancora incomplete,da completare prima del consenso pertinente:**

1. Nome reale di ogni bucket sorgenti/upload:nessun binding objectViewer a
   wildcard o a tutti i bucket del progetto. Da rilevare nel provisioning
   tecnico concordato,prima della build.
2. Nomi reali dei servizi Cloud Run worker ed esatta identità invocante:
   roles/run.invoker va assegnato sul singolo servizio nella fase trigger C,
   non su tutto il progetto. Non esiste ancora una lista finale di binding
   Run Invoker applicabili per gli8trigger/3scheduler.
3. Policy correnti,condizioni sovrapposte,permessi custom supportati e claim
   GitHub effettivi:finché non osservati,questa è una proposta e non un
   confronto verificato fra situazione attuale e desiderata.

Queste lacune devono apparire nel prospetto di approvazione;non si richiede
un'approvazione generica per colmarle durante un deploy. Il primo operatore
sarà l'owner con sessione personale già esistente:nessuna nuova assegnazione
Owner/Editor alla persona o ai nuovi account,nessuna modifica ai due SA legacy.
Distribuire codice può esercitare i permessi runtime:separare i quattro
account chiarisce le responsabilità,non rende innocuo codice di deploy malevolo.

Riferimenti verificati16novembre2026:
[permessi Auth](https://docs.cloud.google.com/iam/docs/roles-permissions/firebaseauth),
[condizione database](https://firebase.google.com/docs/firestore/manage-databases#configure_database_access_conditions),
[service agent Functions](https://docs.cloud.google.com/functions/docs/concepts/iam).

### 3b. Verifica API e policy effettive —16novembre2026

Richiesta owner:verificare API e policy,senza correzioni. Controlli eseguiti
in sola lettura con identità owner,progetto staging esplicito. Nessuna API
abilitata,nessun grant/revoca,nessuna modifica bucket/database. Inventario API
prima e dopo identico:44servizi. BillingEnabled=true verificato via API,
oltre alla precedente conferma owner.

**Differenza API rispetto alla allowlist B:**

| Servizio richiesto | Stato attuale |
|---|---|
| `cloudfunctions.googleapis.com` | Non abilitato |
| `run.googleapis.com` | Non abilitato |
| `cloudbuild.googleapis.com` | Non abilitato |
| `artifactregistry.googleapis.com` | Non abilitato |
| `eventarc.googleapis.com` | Non abilitato |
| `cloudscheduler.googleapis.com` | Non abilitato |
| `secretmanager.googleapis.com` | Non abilitato |
| `sts.googleapis.com` | Non abilitato |

Le altre12API della allowlist sono già abilitate:iam,iamcredentials,
serviceusage,cloudresourcemanager,firebase,firebasehosting,firestore,storage,
firebasestorage,pubsub,identitytoolkit,logging (tutte con suffisso.googleapis.com).
Non si deduce assenza di risorse dall'API disabilitata:Functions/Run/Build,
Artifact Registry,Eventarc,Scheduler e Secret Manager non sono stati interrogati
per evitare qualsiasi richiesta interattiva di abilitazione. Esistenza e
policy di repository/secret/worker restano da verificare nella fase pertinente.

**IAM attuale e differenza rispetto al prospetto:**

- Policy progetto letta:10binding,tutti relativi all'owner,ai due account
  legacy e ai service agent Firebase/Firestore già esistenti. Nessun binding
  diretto per github-deploy,functions-build,app-runtime o web-runtime.
- Ruoli custom di progetto:0. Tutti e5i ruoli custom proposti sono quindi da
  creare;nessun grant è stato applicato a seguito di questa verifica.
- Tutti i9permessi distinti dei5ruoli custom risultano testabili sul progetto,
  GA,non limitati ai soli ruoli predefiniti e supportati nei custom role.
  IAM omette il campo per lo stato predefinito SUPPORTED e i booleani false:
  la normalizzazione è documentata nel riepilogo locale,non è una prova di
  creazione/applicazione del ruolo.
- Scaricate in sola lettura le definizioni correnti di23ruoli predefiniti
  proposti,compresi i service agent. Per i ruoli proposti al deploy non
  risultano resourcemanager.projects.setIamPolicy,secretmanager.versions.access
  o serviceusage.services.enable/disable. Il binding actAs resta limitato ai
  quattro nuovi account come da prospetto.
- **Rilievo prima del grant:**roles/eventarc.admin contiene88permessi e include
  setIamPolicy sulle risorse Eventarc,ad esempio eventarc.triggers.setIamPolicy.
  Non è amministrazione IAM del progetto,ma è più della sola gestione codice.
  Non serve alla prima tranche HTTP+SSR;prima di assegnarlo decidere se
  rinviare il grant alla fase trigger o definire un ruolo più ristretto.
  Il prospetto originale non è stato applicato né sostituito silenziosamente.
- Pool Workload Identity Federation globali:0. Il pool/provider proposto resta
  da creare;nessun collegamento GitHub è attivo per questi nuovi account.
- Nessun nuovo binding Functions/Build/Eventarc/PubSub/Scheduler serviceAgent
  presente nella policy progetto. Non si deduce da ciò l'assenza di ogni
  identità Google:verificare identità e binding dopo l'abilitazione concordata.

**Risorse dati e policy lette:**

| Risorsa | Evidenza attuale |
|---|---|
| Bucket applicativo firebasestorage.app | US,uniform_bucket_level_access=false,public_access_prevention=inherited;soft delete604800secondi (=7giorni) |
| IAM bucket applicativo | roles/storage.legacyBucketOwner per projectOwner/projectEditor e roles/storage.legacyBucketReader per projectViewer;nessun nuovo account e nessun allUsers/allAuthenticatedUsers nella policy letta |
| Altri bucket | Solo mcp-website-dev-39539 oltre al bucket applicativo;nessun bucket gcf-v2-sources/upload osservato nell'elenco corrente |
| Firestore(default) | Native,nam5;deleteProtectionState=DELETE_PROTECTION_DISABLED e pointInTimeRecoveryEnablement=POINT_IN_TIME_RECOVERY_DISABLED |

Con uniform access disabilitato,gli ACL degli oggetti possono aggiungere
accessi rispetto alla sola policy del bucket. Non sono stati letti contenuti
o ACL di singoli oggetti;non dichiarare privati tutti i file da questa verifica.
PITR e delete protection disattivati sono elementi del gate protezione dati
prima di reset/import:non sono stati cambiati automaticamente. Non è stata
eseguita una nuova query dei backup pianificati;il dato precedente deriva
dalla schermata owner e non diventa verifica API per deduzione.

Evidenza privata di soli metadati in
`.local/staging/cloud-b-verification/` (file0600,directory0700,non versionata):
policy correnti,definizioni ruoli,query permessi e riepilogo. Nessun token,
refresh token,chiave o payload Secret Manager salvato negli artifact.
Il comando generico CLI dei testable permissions è andato in timeout;la query
IAM REST mirata con pagina1000 e TLS verificato ha trovato tutti i9permessi
in14pagine. Gli errori tecnici iniziali di lettura delle definizioni sono
stati risolti;le23definizioni finali risultano tutte lette correttamente.

**Esito:**verifica terminata,staging non ancora pronto al deploy. Il prossimo
lotto concreto da discutere è l'abilitazione delle sole8API mancanti,seguita
dal readback di API e service agent creati dal servizio. Grant custom/runtime,
WIF,repository/secret,configurazione Auth e policy dati restano passaggi distinti.
Questa verifica non autorizza l'applicazione del lotto successivo.

Fonte sul significato dei campi della query:
[queryTestablePermissions](https://docs.cloud.google.com/iam/docs/reference/rest/v1/permissions/queryTestablePermissions).

### 3c. Otto API abilitate e confronto IAM successivo —16novembre2026

Owner autorizza esplicitamente l'abilitazione delle8API elencate nella
sezione3b. Eseguito un solo comando gcloud services enable con quei8ID,
--project=mcp-website-dev-39539 e account owner espliciti. Progetto verificato
ACTIVE/1005755179074 prima del comando. Operazione conclusa con exit0 e tutte
le8API richieste presenti nel readback. Nessun nuovo grant applicativo,
nessun deploy o aggiornamento dati eseguito dall'agente.

**Delta effettivo:**44→54API abilitate. Oltre alle8autorizzate sono comparse
come dipendenze `containerregistry.googleapis.com` (Container Registry API) e
`source.googleapis.com` (Legacy Cloud Source Repositories API),non nominate
esplicitamente nel comando. Nessuna API rimossa o disabilitata. Conservare
questo delta nel manifest;non disabilitare dipendenze per ricondurre il numero
artificialmente a52.

**Assegnazioni ruolo/principale comparse fra i due snapshot,senza comandi
manuali set/add/remove IAM:**

| Principale | Ruolo osservato dopo abilitazione |
|---|---|
| `1005755179074@cloudbuild.gserviceaccount.com` | `roles/cloudbuild.builds.builder` |
| `service-1005755179074@gcp-sa-cloudbuild.iam.gserviceaccount.com` | `roles/cloudbuild.serviceAgent` |
| `service-1005755179074@gcf-admin-robot.iam.gserviceaccount.com` | `roles/cloudfunctions.standardServiceAgent` |
| `service-1005755179074@gcp-sa-cloudscheduler.iam.gserviceaccount.com` | `roles/cloudscheduler.serviceAgent` |
| `service-1005755179074@containerregistry.iam.gserviceaccount.com` | `roles/containerregistry.ServiceAgent` |
| `service-1005755179074@serverless-robot-prod.iam.gserviceaccount.com` | `roles/run.serviceAgent` |
| `1005755179074-compute@developer.gserviceaccount.com` | **`roles/editor`** |
| `mcp-website-dev-39539@appspot.gserviceaccount.com` | **`roles/editor`** |

Il suffisso serverless-robot-prod è il dominio dell'identità di servizio
Google;questo binding è nella policy del progetto staging e non indica un
accesso al progetto applicativo di produzione. Nessun binding preesistente
rimosso. github-deploy,functions-build,app-runtime e web-runtime continuano
ad avere0ruoli direttamente assegnati nella policy del progetto.

**Due effetti da chiudere prima del deploy:**

1. I due account default Compute/AppEngine sono comparsi Enabled con Editor.
   È compatibile con i grant automatici documentati di Google quando non
   impediti dalla policy effettiva;non è stata eseguita una query dei vincoli
   organizzativi né un'analisi completa dei loro utilizzi. Non equipararli
   ai4account dedicati e non iniziare a usarli per runtime/build. Valutare
   rimozione mirata dei2Editor solo dopo verifica delle dipendenze e consenso
   esplicito,con snapshot IAM per ripristino. Nessuna revoca automatica fatta.
   Anche il ruolo builder dell'account CloudBuild legacy va considerato nel
   riesame delle identità default;nessun comando di build è stato eseguito.
2. Il ruolo Functions assegnato oggi è
   roles/cloudfunctions.standardServiceAgent (GA,265permessi),non il vecchio
   roles/cloudfunctions.serviceAgent (titolo Deprecated,278permessi).
   Le definizioni API lette mostrano13permessi Artifact Registry aggiuntivi
   solo nel ruolo vecchio,nessuna aggiunta nel nuovo. La guardia locale in
   scripts/deployment/cli-guards.cjs requiredProjectBindings attende ancora
   il ruolo vecchio e bloccherebbe questo progetto. Prima del deploy serve
   adeguamento con regressione/review al ruolo corrente,non l'assegnazione
   del ruolo deprecato per far passare il controllo. Codice non modificato
   durante questa operazione di abilitazione API.

**Readback runtime:**gcloud functions list --regions=- e Cloud Run managed
globale restituiscono entrambi[] con exit0 e stderr vuoto. Confermata assenza
di funzioni/servizi Run,non assenza di ogni possibile workload Compute/App
Engine o altri utilizzi delle identità default. Nessuna affermazione di
inutilizzo generale derivata dal solo inventario Functions/Run.

Eventarc/PubSub serviceAgent non compaiono come nuovi binding nello snapshot;
la loro eventuale inizializzazione mirata resta un'azione separata prima dei
trigger. PoolWIF,customrole e grant runtime/build/deploy non creati da questo
passaggio. Repository,secret e configurazioni applicative restano da preparare.

Evidenze private metadata-only in.local/staging/cloud-b-verification:
api_enable_result.json,api_enable_readback_summary.json,policy e inventari
prima/dopo,definizioni dei due ruoli Functions. Nessuna credenziale o payload
secret salvati. Operazione API completata;blocco B ancora in corso,nessuna
approvazione di deploy,dati,revoca o modifica produzione implicita.

Riferimenti sui grant automatici:
[default service account e Editor](https://docs.cloud.google.com/iam/docs/troubleshoot-org-policies),
[verifica impatto prima di cambiare ruoli](https://docs.cloud.google.com/compute/docs/instances/change-service-account).

### 3d. Controllo Functions corretto;Editor lasciati invariati —16novembre2026

Owner dispone di non proseguire il riesame/restrizione dei2Editor automatici
e di occuparsi soltanto del controllo locale Functions. I due grant restano
invariati per sua scelta;non sono un blocco imposto da questa sessione.
Nessuna operazione cloud eseguita in questo intervento.

Correzione minima in scripts/deployment/cli-guards.cjs:il binding del service
agent Functions ammette roles/cloudfunctions.standardServiceAgent oppure il
legacy roles/cloudfunctions.serviceAgent,per compatibilità con ambienti già
provisionati. Resta obbligatorio il preciso membro
serviceAccount:service-PROJECT_NUMBER@gcf-admin-robot.iam.gserviceaccount.com,
con binding non condizionato e nel progetto/numero attesi. Editor o Functions
Admin non sostituiscono il binding richiesto. Gli altri ruoli di servizio e i
blocchi sulle scritture IAM rimangono attivi;nessun ruolo deprecato viene
assegnato per superare il controllo.

Prova RED→GREEN:la fixture del primo trigger Firestore con il ruolo corrente
falliva prima della patch per Required project IAM binding missing e passa
dopo. Regressioni confermano compatibilità legacy e rifiuto di membro errato,
numero progetto diverso,binding condizionato,Editor e FunctionsAdmin.

Verifica locale Node20:8test IAM mirati,70configurazione/frontend e103strumenti
PASS;lint mirato PASS. Replay offline della policy staging già acquisita,
per la tranche HTTP:PASS,0scritture IAM. È una prova del controllo su snapshot,
non un deploy o un'attestazione di tutti i prerequisiti cloud. Non rieseguite
build/API/backendunit perché non modificati codice applicativo o build.
Review indipendente unica Solhigh functions_agent_role_review:nessunP1/P2,
8/8mirati verificati anche dal reviewer;accettata dal coordinatore.

Prossimo B:custom role e grant nominativi,WIF,repository/secret/configurazioni,
con le approvazioni e i gate dati/deploy già previsti. Non riproporre la
rimozione degli Editor senza nuova richiesta owner. Nessun cambio alle
identità legacy,alla produzione o ai flag della pipeline.

### 3e. Primo lotto IAM applicato e verificato —16novembre2026

Owner autorizza di proseguire dopo la correzione del controllo Functions.
Applicato il sottoinsieme nominativo del prospetto su risorse già esistenti:
5creazioni custom role e17assegnazioni ruolo/principale (22operazioni).
Repository e secret risultavano assenti nella verifica metadata,quindi quei
grant sono rinviati. Eventarc/Scheduler rinviati alla fase trigger,senza
applicare EventarcAdmin nel frattempo. Nessun WIF,deploy o aggiornamento dati.

Piano concreto e22comandi verificati prima dell'esecuzione da Solhigh
staging_iam_lot_review:nessunP1/P2,accettato. Hash piano
`c3eef5a6fe4540f80e0de53f4b916d3ec712c95759bdd020864c25272d2a9cdc`.
Prima della prima scrittura ricontrollati ID/numero progetto,assenza ruoli
custom e uguaglianza delle6policy ai rispettivi snapshot. Solo aggiunte
incrementali con gcloud,progetto/account espliciti;nessun reset di policy,
revoca o retry/rollback automatico. Tutte le22operazioni concluse con successo.

**Cinque ruoli custom creati GA**,tutti nel namespace
`projects/mcp-website-dev-39539/roles/`:stagingAppAuth,stagingWebAuth,
stagingBlobSigner,stagingReleaseMetadata,stagingBucketMetadata. Readback delle
5definizioni conferma esattamente gli includedPermissions della tabella3a,
nessuna permission aggiuntiva e nessun ruolo cancellato/disabilitato.

**Diciassette assegnazioni effettive:**

| Principale (suffisso @mcp-website-dev-39539.iam.gserviceaccount.com) | Risorsa | Ruolo applicato |
|---|---|---|
| app-runtime | Progetto staging | Custom stagingAppAuth |
| app-runtime | Policy progetto,condizione solo DB(default) | roles/datastore.user |
| web-runtime | Progetto staging | Custom stagingWebAuth |
| functions-build | Progetto staging | roles/logging.logWriter |
| github-deploy | Progetto staging | roles/cloudfunctions.developer |
| github-deploy | Progetto staging | roles/run.developer |
| github-deploy | Progetto staging | roles/firebasehosting.admin |
| github-deploy | Progetto staging | roles/cloudbuild.builds.editor |
| github-deploy | Progetto staging | roles/serviceusage.serviceUsageConsumer |
| github-deploy | Progetto staging | Custom stagingReleaseMetadata |
| github-deploy | Solo account github-deploy | roles/iam.serviceAccountUser |
| github-deploy | Solo account functions-build | roles/iam.serviceAccountUser |
| github-deploy | Solo account app-runtime | roles/iam.serviceAccountUser |
| github-deploy | Solo account web-runtime | roles/iam.serviceAccountUser |
| web-runtime | Solo proprio account web-runtime | Custom stagingBlobSigner |
| app-runtime | Solo bucket applicativo firebasestorage.app | roles/storage.objectAdmin |
| github-deploy | Solo bucket applicativo firebasestorage.app | Custom stagingBucketMetadata |

La condizione Firestore ha titolo staging-default-firestore-only ed espressione
`resource.name == "projects/mcp-website-dev-39539/databases/(default)"`.
Gli altri16grant sono non condizionati sulla risorsa nominata;
non è stato assegnato actAs a livello progetto né signBlob su altri account.

**Verifica API successiva con letture separate:**rilette le6policy e le5definizioni
custom role. Differenza esatta:10aggiunte progetto,5sulle policy dei4account,
2sul bucket;0rimozioni e0aggiunte inattese. Tutti i binding preesistenti
conservati,inclusi i2Editor lasciati invariati per scelta owner. Readback
all_pass=true con17grant attesi e5definizioni corrispondenti. È verifica delle
policy,non un test di accesso runtime impersonato o un deploy applicativo.

Evidenze private metadata-only in.local/staging/cloud-b-verification:
iam_lot_plan.json,iam_lot_commands.json,6snapshot before/after,
iam_lot_apply_result.json(status applied-and-verified),iam_lot_verified_summary.json
più definizioni ruoli. Nessuna chiave o valore secret salvato. Nessun codice
applicativo modificato né suite applicative rieseguite per questo lotto cloud.

**Ancora aperti nel B:**repository gcf-artifacts us-central1 e relativo opt-out
cleanup/permessi writer-reader;secret sandbox e valore inserito dall'owner,
poi secretAccessor backend/viewer deploy;bucket sorgenti reali e objectViewer
build;WIF/Environment GitHub,Hosting/Auth,monitoraggio budget. Eventarc,
Scheduler e invocazioni worker prima della loro fase. Staging non dichiarato
pronto al deploy finché mancano questi prerequisiti e il consenso sullo SHA.

### 3f. Repository immagini creato e verificato —16novembre2026

Owner autorizza di proseguire con il repository dopo la spiegazione delle
immagini container. Preflight via API conferma progetto staging ACTIVE,
numero1005755179074 e nessun repository presente in us-central1.

Creato il solo repository
`projects/mcp-website-dev-39539/locations/us-central1/repositories/gcf-artifacts`,
formato DOCKER,mode STANDARD_REPOSITORY,con descrizione staging rollback.
Label `firebase-functions-cleanup-opted-out=true`,nessuna cleanup policy.
Scansione vulnerabilità esplicitamente DISABLED alla creazione,coerente con
il piano costi che non attiva scansioni opzionali a pagamento. Non modificati
controlli di scansione di repository esistenti;eventuali requisiti futuri di
scansione restano una decisione distinta.

Policy iniziale del repository letta e verificata senza binding diretti.
Applicate due sole assegnazioni,entrambe sul repository esatto:

| Principale | Ruolo |
|---|---|
| `functions-build@mcp-website-dev-39539.iam.gserviceaccount.com` | `roles/artifactregistry.writer` |
| `github-deploy@mcp-website-dev-39539.iam.gserviceaccount.com` | `roles/artifactregistry.reader` |

Readback con richieste separate conferma nome/regione/formato/mode,label
opt-out,0cleanup policy,scanningDISABLED e differenza IAM esattamente uguale
ai2grant previsti,non condizionati. Elenco immagini restituisce[]:repository
vuoto. Nessun comando di build o deploy eseguito in questo passaggio. I grant di progetto e gli
accessi ereditati non sono esclusi dalla presenza dei soli2binding diretti.

Nella rilettura della policy progetto è comparsa la sola assegnazione
`roles/artifactregistry.serviceAgent` a
`service-1005755179074@gcp-sa-artifactregistry.iam.gserviceaccount.com`,
identità gestita Google creata durante il provisioning. Nessun grant di
progetto manuale aggiunto;0rimozioni rispetto allo snapshot successivo al
lotto IAM3e. Grant preesistenti,compresi gli Editor accettati,conservati.

Evidenze private metadata-only in.local/staging/cloud-b-verification:
registry_create_result.json,registry_metadata_before_grants.json,
registry_iam_before_grants.json,registry_grants_result.json,readback metadata/
IAM/immagini,registry_verified_summary.json(all_pass=true) e delta policy
progetto. Comandi con --project staging e account owner espliciti,nessun
cambio di default locale. Nessuna API aggiuntiva abilitata dall'agente,
secret,chiave,contenuto applicativo o dati manipolati. Documentazione e
checkpoint aggiornati;nessuna modifica al codice applicativo.

Opt-out e assenza DELETE restano iniziali per proteggere bootstrap/rollback,
non una retention indefinita definitiva. La pulizia successiva dovrà
preservare immagini attive e baseline nella finestra30giorni concordata.
Questo passaggio prepara lo spazio;non dimostra un deploy o il rollback.

Prossimo B:secret PayPal sandbox con valore inserito dall'owner fuori chat,
poi2grant su quel solo secret;bucket sorgenti reali e objectViewer build;
WIF/GitHub,Hosting/Auth e monitoraggio budget. Gate deploy,dati e main hold
invariati;B non ancora dichiarato completo.

### 3g. Prova reale MailerSend da includere nello staging —16novembre2026

Owner chiarisce che lo staging deve permettere anche la consegna reale delle
email di test. MAIL_MODE=disabled è lo stato iniziale attuale,non il risultato
finale sufficiente per l'E2E mail. Correggere il piano che limitava i secret
iniziali al solo PayPal:per il profilo con invii reali serve anche
`projects/mcp-website-dev-39539/secrets/MAILERSEND_API_KEY`.

RuntimeSettings e MailerSendMailService supportano già MAIL_MODE=staging con
MAIL_ALLOWED_RECIPIENTS obbligatorio e blocco dei destinatari non consentiti.
I binding SecretParam per le funzioni mail esistono già. Prima dell'attivazione
occorre adeguare la configurazione di release:oggi legge il default disabled
dal catalogo,non inoltra l'allowlist e include il mittente solo in produzione;
il preflight staging richiede ancora soltanto il secret PayPal.

Lotto da preparare:secret MailerSend (valore inserito dall'owner fuori chat),
secretAccessor app-runtime e viewer metadata github-deploy sul solo secret;
MAIL_MODE=staging,mittente verificato e destinatari test espliciti fuori Git;
aggiornamento manifest/digest/workflow/preflight e regressioni. Destinatari e
mittente richiesti all'owner,senza chiedere API key. Invii massivi del dataset
restano esclusi;la prova finale deve verificare richiesta al provider e
ricezione effettiva,non soltanto un HTTP200 locale. Nessuna modifica cloud,
configurazione runtime o invio eseguito da questo chiarimento. Altri provider
conservano i modi attuali finché non richiesto diversamente.

### 3h. Profilo E2E staging e contenitori dei secret —16 novembre 2026

Owner richiede servizi reali nello staging, salvo Pass2U per evitare consumo
crediti; PayPal resta sandbox. Mittente MailerSend comunicato dall'owner,
destinatari esatti recuperati da `.local/staging/recipients.json` (fuori Git).
Connettore Gmail Dev verificato tramite get_profile sulla casella corrispondente:
nessun messaggio letto o inviato. Autorizzata futura lettura limitata ai test
staging, inclusa verifica contenuti/allegati e resa grafica quando disponibile.
Credenziali SMTP della schermata non equivalgono al token API usato dal codice.

Piano del lotto autorizzato: configurazione release esplicita mail, gender e
SoundCloud in modo staging, Pass2U fake, allowlist email di soli indirizzi esatti
obbligatoria e inclusa nel digest. Default del catalogo per avvio senza release
rimangono prudenti. Preflight legge soltanto metadati/versioni/IAM di tutti i
provider attivi; mai payload. Runtime rifiuta Pass2U reale in staging anche con
chiave presente e richiede chiave per gender reale. Produzione invariata.

Sender.net è un'eccezione ancora da chiarire: la precedente sospensione è
imposta dal runtime, manca la mappatura SecretParam e il webhook accetta
richieste senza autenticazione se manca il suo secret. Non riattivarlo con un
semplice flag. Chiesto all'owner se la nuova decisione include anche Sender;
nessuna riattivazione in questo lotto. Eventuale lotto dedicato richiede
binding, autenticazione webhook obbligatoria e isolamento contatti/campagne.

Risorse concrete da predisporre in `mcp-website-dev-39539`:
PAYPAL_CLIENT_SECRET (sandbox), MAILERSEND_API_KEY, SOUNDCLOUD_CLIENT_SECRET,
GENDER_API_KEY. Quattro contenitori vuoti con replica automatica; zero versioni.
Su ciascuno soltanto due grant diretti e senza condizioni:
- `roles/secretmanager.secretAccessor` a
  `app-runtime@mcp-website-dev-39539.iam.gserviceaccount.com`;
- `roles/secretmanager.viewer` a
  `github-deploy@mcp-website-dev-39539.iam.gserviceaccount.com` (metadati, non valori).
Nessun grant al build/web, nessun grant SM a livello progetto; nessuna chiave
Pass2U o Sender. Piano/script/evidenze private `provider_secret_*` in
`.local/staging/cloud-b-verification`. Review Sol high prima delle mutazioni;
readback di replica, zero versioni e8grant, confronto IAM progetto invariato.
I valori verranno inseriti dall'owner direttamente in SM, senza chat/log/Git.

Costi: la precedente stima includeva una sola versione secret; a4versioni
attive la componente lorda versioni diventa0,24USD/mese invece di0,06, prima
delle quote e degli accessi. Costi/quote MailerSend, SoundCloud e Gender da
verificare sugli account prima delle prove reali; non inclusi nel vecchio totale.
Nessun deploy, import dati o invio massivo autorizzato da questo lotto; gate
main, baseline rollback e rilascio restano invariati.

Esito del lotto3h: review indipendente Sol high con un P2 sul confronto IAM;
corretto con regressione RED→GREEN (policy iniziale vuota, policy finale esatta).
Verifica locale:1415unit backend,112tooling,70frontend/config e5test privati di
provisioning PASS. Verifica contratto release→runtime→SecretParam conferma
assenza di binding Pass2U e secret necessari per ciascuna funzione.

Provisioning eseguito:4contenitori,8grant diretti,0versioni. Primo tentativo
fermato dopo la sola creazione PayPal perché il CLI proietta una policy vuota
come null; confermati inventario, replica, zero versioni e assenza grant prima
della ripresa esplicita. Adeguamento coperto da test, nessun retry alla cieca.
Seconda lettura indipendente: esattamente2grant per secret,0versioni e IAM
di progetto identico al checkpoint registry precedente al primo tentativo.
Evidenze `provider_secret_result.json` e
`provider_secret_independent_readback.json` nella cartella privata.
I campi email approvati sono in `.local/staging/mail-public-config.json`0600;
nessun indirizzo personale aggiunto ai documenti versionati.

Passo owner MailerSend:Developer Tools→API tokens→Create new token; token
dedicato staging con Sending access e dominio del mittente approvato; verificare
la scadenza scelta. Inserire il valore direttamente come nuova versione nel
secret MAILERSEND_API_KEY dello staging,mai in chat/Git. Fonte ufficiale:
https://www.mailersend.com/help/managing-api-tokens.
PayPal sandbox e SoundCloud richiedono i rispettivi valori; Gender è differito
(aggiornamento sotto). Nessun riuso automatico dei segreti produzione. Preflight resta bloccante finché le
versioni non sono abilitate. Ricezione/contenuto/grafica email ancora da provare.

**Aggiornamento owner —16 novembre 2026, successivo al lotto3h:** API Gender
non funzionante, correzione rinviata. Release staging usa ora GENDER_MODE=fake:
nessuna richiesta HTTP Gender, nessun binding GENDER_API_KEY alle funzioni e
nessun requisito di versione secret Gender nel preflight. Il contenitore vuoto
e i due grant già creati restano invariati; non è stata eseguita una revoca.
Il simulatore produce risultati sintetici: la qualità del servizio Gender reale
non è validata e resta un punto rinviato. Nessun fix dell'API dichiarato.
Tre versioni provider da inserire ora (PayPal sandbox, MailerSend, SoundCloud),
non quattro; nel precedente modello di costo la voce versioni diventerebbe
0,18USD/mese prima di quote/accessi. Verifica mirata release/bootstrap PASS.

**Inserimento diretto dei secret autorizzato dall'owner —16 novembre 2026:**
l'owner chiede di provvedere tramite CLI. Questa istruzione supera, per i soli
tre valori seguenti, il precedente passaggio di inserimento manuale owner.
Lettura locale in memoria dei soli campi provider necessari dalle configurazioni
backend esistenti `.env` e `.env.integration` nel checkout principale; valori
coincidenti per PayPal, MailerSend e SoundCloud. Nessun export completo, nessuna
lettura delle chiavi Firebase/Gmail e nessun download da Doppler.

La modalità legacy dei file è production: non è stata usata per scegliere le
credenziali. La coppia PAYPAL_CLIENT_ID/SECRET è distinta da PAYPAL_LIVE_* e
l'autenticazione sull'endpoint `api-m.sandbox.paypal.com/v1/oauth2/token` ha
restituito200 con access token valido, mantenuto soltanto in memoria. Nessuna
creazione ordine/capture/pagamento. MAILERSEND_API_KEY è presente e distinta
dalla password SMTP; riusato il token API esistente, senza creare o ruotare token.
SoundCloud riusa la coppia esistente. Validità operativa MailerSend/SoundCloud
ancora da provare; stato ENABLED in SM non equivale a successo del provider.

Creati tramite `gcloud secrets versions add --data-file=-` (payload su stdin,
mai negli argomenti/log/file intermedi) soltanto:
- PAYPAL_CLIENT_SECRET versione1, ENABLED;
- MAILERSEND_API_KEY versione1, ENABLED;
- SOUNDCLOUD_CLIENT_SECRET versione1, ENABLED.
Readback delle versioni tramite soli metadati, senza leggere i payload da SM.
GENDER_API_KEY conserva0versioni; nessun secret Pass2U inserito. Produzione,
file sorgenti, IAM, deploy e dati applicativi invariati. Client ID pubblici
salvati in `.local/staging/provider-public-config.json`0600 per la futura
configurazione release; valori dei secret non salvati in nuovi file locali.
Evidenze private `provider_local_source_check.json` e
`provider_secret_upload_result.json`. Restano prove di invio/ricezione mail,
SoundCloud, preflight completo e gate bootstrap/E2E/rollback.

### 4. WIF e GitHub: configurazione applicata, prova OIDC reale pendente

**Aggiornamento corrente —17 novembre 2026:** creati pool global
`github-actions` e provider `main-release` nel solo progetto staging. Entrambi
ACTIVE, non disabilitati. Readback esatto di issuer, mapping, sei condizioni e
assenza di audience aggiuntive: nessun allargamento dei vincoli elencati sotto.
Concesso `roles/iam.workloadIdentityUser` solo su
`github-deploy@mcp-website-dev-39539.iam.gserviceaccount.com` al principalSet
repository ID899139661 del pool. Nessun altro grant aggiunto o rimosso; IAM di
progetto invariato. Nessuna chiave SA creata e nessun intervento produzione.

GitHub OIDC customization conferma use_default=true, use_immutable_subject=false
e sub_claim_prefix repo:Vittorix99/mcp-website. Nessuna personalizzazione
applicata. Condizione vincola il subject standard all'Environment staging,
ref main, caller release.yml e reusable deploy-environment.yml. Audience default
verificata sul sorgente della action fissata a7c6bc770dae815cd3e89ee6cdf493a5fab2cc093:
https://iam.googleapis.com/ seguito dalla risorsa provider concordata. Non
aggiunta audience generica GitHub.

Individuata tramite Firebase Management API l'app web esistente ACTIVE
`MCP WEB TEST`, appID `1:1005755179074:web:773eff0b586742e443cddb`; non creata una
nuova app. SDK config conferma progetto staging, authDomain firebaseapp staging
e bucket firebasestorage osservato. Richieste REST con x-goog-user-project
esplicito sullo staging. I due valori browser pubblici FIREBASE_API_KEY e
FIREBASE_APP_ID inseriti nell'Environment: totale14variabili, valori riletti.
Nessun segreto privato aggiunto a GitHub. Identificativi e chiave web non
provengono dalla configurazione produzione.

Review indipendente Sol high: un P2 corretto (Python ottimizzato rimuoveva
assert; ora guardia esplicita non-assert all'ingresso, regressione RED→GREEN
con -O e zero chiamate esterne). Offline:1caso ammesso/14rifiutati sulla
condizione effettiva; reviewer verifica cinque mutazioni previste e stop prima
del grant se il provider live fosse più ampio. Validatori configurazione
pubblica e runtime policy PASS su14variabili e SHA sintetico zero, senza
creare attestazioni o release. Non è una prova JWT firmato/scambio STS.

Prima esecuzione fermata dopo creazione pool/provider, prima di qualsiasi grant:
il primo readback non completato, diagnostica iniziale non conservata e causa
non attestata. Rilettura indipendente successiva conferma tutte le condizioni
esatte e IAM invariato; ripresi esplicitamente soltanto grant e due variabili,
senza ripetere le creazioni o ridurre i vincoli. Secondo readback completo
PASS: un solo provider ristretto, un solo grant atteso sul SA,14variabili,
main-only, IAM progetto invariato. Flag repository deploy ancora assenti,
PAYMENT_ROLLOUT_APPROVED/ROLLBACK_BASELINE_VERIFIED false.

Evidenze private in `.local/staging/cloud-b-verification`: wif_activation_plan,
wif_activation_result, wif_activation_independent_readback,
wif_firebase_public_config_validation, firebase_web_app_config_check e snapshot
IAM. Valori pubblici SDK in `.local/staging/firebase-web-public-config.json`0600;
nessun token OAuth/OIDC persistito. Nessun workflow/build/deploy, invio mail o
import dati eseguito. Prova con token GitHub autentico e STS da fare soltanto
nel canale main/SHA autorizzato, prima di dichiarare WIF funzionante end-to-end.
Riferimenti: https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines,
https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-with-reusable-workflows,
https://github.com/google-github-actions/auth/blob/7c6bc770dae815cd3e89ee6cdf493a5fab2cc093/src/main.ts.

**Checkpoint precedente della sola creazione Environment:**

**Eseguito il17 novembre 2026 su richiesta owner:** tramite `gh api` con
identità Vittorix99 e permesso admin, verificato repository ID899139661,
creato Environment `staging` (ID27524025438). Policy
`protected_branches=false, custom_branch_policies=true`; unica regola esplicita
`name=main,type=branch` (nessuna regola tag). Nessun reviewer o attesa aggiuntiva
per staging; protezioni produzione restano un gate separato.

Inserite e rilette esattamente12variabili pubbliche: DEPLOY_SERVICE_ACCOUNT,
BUILD_SERVICE_ACCOUNT,RUNTIME_SERVICE_ACCOUNT,WEB_RUNTIME_SERVICE_ACCOUNT,
WIF_PROVIDER,PAYPAL_CLIENT_ID,SOUNDCLOUD_CLIENT_ID,MAILERSEND_FROM_EMAIL,
MAILERSEND_FROM_NAME,MAIL_ALLOWED_RECIPIENTS,PAYMENT_ROLLOUT_APPROVED,
ROLLBACK_BASELINE_VERIFIED. I due flag di approvazione sono false. Nome mittente
`MCP Staging`; indirizzi e client ID recuperati dai file privati già approvati,
non trascritti qui.0Environment secrets: i valori provider restano in SM.
Mancano FIREBASE_API_KEY e FIREBASE_APP_ID dell'app staging: non copiare quelli
produzione. WIF_PROVIDER è per ora il riferimento concordato, non una prova
che il pool/provider siano stati creati o funzionino.

Readback completo REST e validatore release.validate_environment PASS:
regola main-only,12nomi/valori esatti,0secret,unico Environment staging.
La prima lettura delle variabili restituiva10di12elementi: riletti tutti con
per_page=100 e controllo total_count, senza ripetere mutazioni. Flag repository
ENABLE_STAGING_DEPLOY/ENABLE_PRODUCTION_DEPLOY assenti prima e dopo; nessun
workflow/build/deploy avviato. Nessun Environment production creato o modifica
Google Cloud in questo lotto. Evidenza privata:
`.local/staging/cloud-b-verification/github_staging_environment_result.json`.
Documentazione API di riferimento:
https://docs.github.com/en/rest/deployments/environments e
https://docs.github.com/en/rest/deployments/branch-policies.

**Piano WIF concordato e ora applicato come descritto sopra:**

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

### 4a. Inventario Hosting/Auth e prerequisiti residui —17 novembre 2026

Letture GET con account operatore esplicito e progetto/quota project soltanto
`mcp-website-dev-39539`; nessuna mutazione cloud o accesso ai dati applicativi.
Gli elenchi hanno nextPageToken assente: risultati completi per queste query.

- Hosting: sito `mcp-website-dev-39539` già esistente, zero release e un canale.
  Non ricreare il sito. Questo aggiorna il riscontro owner storico del16novembre:
  assenza di frontend distribuito confermata, assenza del sito smentita dall'API.
- Auth: domini autorizzati `localhost`, `mcp-website-dev-39539.firebaseapp.com`,
  `mcp-website-dev-39539.web.app`. Nessuna aggiunta necessaria per questi host.
  Email enabled=true e passwordRequired=true: email-link ancora disabilitato.
  Il login in `mcp-website/app/login/page.jsx` richiede email-link e costruisce
  il ritorno `/login/verify` sull'origine corrente; nessun invio effettuato.
- Bucket: presenti soltanto `mcp-website-dev-39539` e
  `mcp-website-dev-39539.firebasestorage.app`, entrambi US. Nessun bucket
  sorgenti/upload elencato; nessuna creazione o assegnazione objectViewer.
- Scheduler: zero job nella sola regione interrogata `us-central1`;
  non costituisce censimento di altre regioni.
- Billing: GET billingInfo HTTP403. Causa non diagnosticata; non dedurre billing
  disattivo o account scollegato. Nessun tentativo di grant/abilitazione API.
  Richiesta all'owner verifica console dello stato e del budget filtrato staging,
  con importo/valuta/soglie, senza dati di pagamento o segreti. Esito pendente.

**Verifica budget successiva,17novembre2026:** su richiesta esplicita owner,
controllata direttamente la console Chrome autenticata, in sola lettura.
Budget esistente `Firebase Project mcp-website-dev-39539`, importo salvato15EUR
mensili (aggiornato dall'owner, prima25EUR). Il selettore Projects mostra come
unica voce selezionata `mcp-website-dev / mcp-website-dev-39539`; elenco budget
Applies to: Project mcp-website-dev. Tutti i servizi inclusi; savings programs
e other savings inclusi nel calcolo. Avvisi su spesa Actual50/90/100%, ossia
7,50/13,50/15EUR; email a billing admins and users attiva, nessun canale
Monitoring o Pub/Sub collegato. Alerts only selezionato; Spend cap enforcement
non selezionato e controllo disabilitato; elenco riporta Not applicable.
Quindi15EUR è un budget di avviso, non un tetto che arresta questa spesa.
Spesa visualizzata0EUR, non prova di assenza di costi ancora da contabilizzare.
Nessuna modifica o salvataggio da parte dell'agente; chiusi selettore e editor
con Cancel. Il riscontro console chiude l'incertezza sul budget, non certifica
da solo billingEnabled/capacità build; il precedente403 REST resta documentato.

Evidenze private0600 nella cartella cloud-b-verification:
`hosting_sites_current.json`, `hosting_releases_current.json`,
`hosting_channels_current.json`, `auth_config_current.json`,
`source_buckets_current.json`, `scheduler_current.json`, `billing_current.json`.

**Diff Auth pronto da autorizzare:** soltanto
`signIn.email.passwordRequired: true -> false`, lasciando enabled=true,
domini e altre impostazioni invariati. La semantica ufficiale mantiene accesso
con password e permette anche email-link:
https://docs.cloud.google.com/identity-platform/docs/reference/rest/v2/Config.
Prima dell'applicazione rileggere il valore e confrontare il resto della
configurazione; dopo, readback esatto e verifica di nessun'altra modifica.
Nessun invio email, creazione utente o deploy è incluso in questa proposta.
L'applicazione rimane soggetta al gate di configurazione cloud concreto;
bootstrap, prova WIF reale, main hold e flag deploy restano separati.

### 4b. Prerequisiti Auth e bucket upload —17 novembre 2026

Owner approva l'avvio del punto1 del percorso staging (Auth, bucket sorgenti
e permessi build); nessuna autorizzazione main/deploy/dati/produzione derivata.
La proposta anticipata di runner cloud non è stata approvata né implementata:
resta un requisito successivo alle risorse/bootstrap, con limiti da definire.

Preflight nuovo: progetto ACTIVE e numero1005755179074, functions-build attivo,
Auth Email/Password e soli tre domini attesi. Cloud Billing GET403 ha reason
SERVICE_DISABLED: API disabilitata, non prova di billing inattivo. Nessuna
abilitazione API o variazione billing proposta/applicata in questo lotto.

Una sola chiamata Functions v2 generateUploadUrl, environment GEN_2 e regione
us-central1, ha creato il bucket restituito dal servizio:
`gcf-v2-uploads-1005755179074.us-central1.cloudfunctions.appspot.com`.
Metadati confermano progetto1005755179074, US-CENTRAL1; bucket inizialmente vuoto.
URL firmato ricevuto e scartato in memoria, mai salvato/stampato né utilizzato.
Nessun archivio caricato, build o funzione distribuita. IAM progetto invariato.

Review indipendente Sol high del solo lotto Auth/grant:1P2 sulle evidenze IAM
dei bucket originali, corretto prima del grant catturando entrambe le policy.
Applicato un solo grant roles/storage.objectViewer a
`functions-build@mcp-website-dev-39539.iam.gserviceaccount.com`, esclusivamente
sul bucket upload osservato. Delta verificato:1aggiunta,0rimozioni/altre
aggiunte. Policy progetto e dei due bucket originali identiche agli snapshot;
ruoli Editor/Owner e account legacy lasciati invariati.

Applicata una sola PATCH Auth con updateMask=signIn.email.passwordRequired,
valore false. Enabled resta true, domini e ogni altro campo invariati.
Il primo confronto letterale ha fermato il flusso: l'API ometteva il solo
booleano false secondo ProtoJSON, invece di restituirlo esplicitamente.
Rilettura indipendente dimostra un'unica differenza di percorso, proprio il
campo previsto. Corretto il verificatore normalizzando soltanto quel campo
assente a false; null o altre differenze restano rifiutate. Regressione
RED/GREEN,7test offline PASS normali e con python -O; seguito mirato della
stessa review accetta la correzione senza altri P1/P2. Nessuna seconda PATCH,
retry o rollback. Nessun utente creato, login reale o invio email effettuato.

**Residuo di questo checkpoint, predisposto nella sezione4c:** generateUploadUrl non ha creato il bucket
`gcf-v2-sources`; nessuna policy assegnata a risorse inesistenti/nomi presunti,
nessun viewer globale di progetto. La documentazione descrive la copia nel
bucket sorgenti durante il deployment; risolvere il provisioning/accesso
prima della prima build senza aggirare il gate deploy. Non dichiarare il
bootstrap pronto o il punto1 completamente chiuso. Prima di ogni ripresa,
leggere inventario/stato attuale; non rieseguire i comandi già applicati.

Evidenze private0600 in cloud-b-verification: prerequisites_preflight,
source_upload_provision_before/after/result/response_metadata,
upload_bucket_before_grant, original_buckets_iam_before_grant,
upload_bucket_grant_after/result, auth_prerequisite_first_attempt/result,
auth_prerequisite_delta_paths/after/independent_readback e
auth_upload_final_independent_readback. Gli snapshot Auth contengono campi
sensibili: confrontare in memoria, stampare solo percorsi/booleani/contatori.
Non trascrivere configurazioni complete nei log o nei documenti tracciati.

Riferimenti: [updateConfig](https://docs.cloud.google.com/identity-platform/docs/reference/rest/v2/projects/updateConfig),
[generateUploadUrl](https://docs.cloud.google.com/functions/docs/reference/rest/v2/projects.locations.functions/generateUploadUrl),
[build process](https://docs.cloud.google.com/functions/docs/building),
[ProtoJSON](https://protobuf.dev/programming-guides/json/).

### 4c. Bucket sorgenti precreato e grant build —17 novembre 2026

Su richiesta owner «risolviamo», predisposto prima della build il bucket
Cloud Storage ordinario `gcf-v2-sources-1005755179074-us-central1`, usando il
nome documentato da Functions per sorgenti senza CMEK. Preflight indipendente
conferma assenza del bucket (GET404 e inventario completo di3bucket), progetto
ACTIVE1005755179074 e identità build attiva. Il service agent Functions ha già
roles/cloudfunctions.standardServiceAgent e i permessi Storage necessari:
nessun nuovo grant di progetto o ruolo legacy aggiunto per farlo funzionare.

Creazione esplicita nel solo staging: US-CENTRAL1, STANDARD, accesso uniforme
e publicAccessPrevention=enforced. Nessun lifecycle/retention lock/versioning
o KMS richiesto. Readback soft delete predefinito604800secondi (7giorni),
distinto da un retention lock; nessun oggetto presente o caricato.

Review indipendente Sol high preventiva: nessun P1/P2, accettata la sola
preparazione della risorsa e del grant. Primo tentativo crea il bucket e si
ferma PRIMA del PUT IAM: la guardia ammetteva solo i default legacyBucketOwner/
legacyBucketReader; Google assegna anche legacyObjectOwner/legacyObjectReader
agli stessi gruppi projectOwner/projectEditor/projectViewer. Sono i medesimi
default già osservati sul bucket upload, non destinatari nuovi. Snapshot
indipendente conferma esattamente4binding/6archi default e nessuna condizione.
Corretta solo la whitelist dei default, con regressione RED/GREEN e test di
rifiuto allUsers;10test offline PASS normali e con python -O. Seguito mirato
della stessa review accetta helper/protocollo di ripresa, senza nuovi P1/P2.

Nessuna ripetizione di --apply o della creazione. Ripreso soltanto il grant,
dopo confronto fresco del fingerprint di creazione, configurazione e policy
osservate, bucket vuoto e snapshot di progetto/tre bucket preesistenti.
Marker separato prima del PUT; policy iniziale e suo etag preservati.
Applicata una sola aggiunta roles/storage.objectViewer a
`functions-build@mcp-website-dev-39539.iam.gserviceaccount.com` sul solo nuovo
bucket,0rimozioni/altre aggiunte. IAM progetto e policy dei3bucket precedenti
invariati. Editor/Owner/default/legacy preservati come richiesto dall'owner.

Readback finale indipendente12controlli PASS: identità/protezioni source,
assenza lifecycle/retention lock, delta IAM esatto, policy progetto e3bucket
immutate, inventario completo4bucket, sorgenti vuote, zero Functions/release
Hosting/build regionali e globali. Nessun deploy, codice caricato, login o
invio email, dato applicativo o intervento produzione/main.

**Limite esplicito:** precreare il nome documentato prepara risorsa e permessi,
non dimostra che Functions la riusi senza adeguamenti. Il riuso reale, eventuali
configurazioni richieste dal servizio e build riuscita si verificano solo nel
bootstrap sullo SHA/main autorizzato. Fermarsi se il servizio rifiuta il bucket
o richiede modifiche fuori manifest; nessun ampliamento IAM o retry implicito.
Questa fase chiude la preparazione del bucket sorgenti, non tutti i gate B/C.

Evidenze private0600: source_bucket_preflight/plan/created,
source_bucket_initial_policy_inspection, source_bucket_creation_first_attempt,
source_bucket_grant_resume_result, source_bucket_result,
source_bucket_policy_after, source_bucket_final_metadata e
source_bucket_independent_readback nella cartella cloud-b-verification.
Il marker risultato vieta il replay; conservare le evidenze della creazione
parziale e della ripresa esplicita. Helper/test locali ignorati da Git.
Riferimenti: [nome e processo sorgenti](https://docs.cloud.google.com/functions/docs/building),
[creazione bucket](https://docs.cloud.google.com/storage/docs/creating-buckets).

### 4d. Recupero e bonifica Firestore staging —20 novembre 2026

**Stato:** piano preparato, non applicato. L'autorizzazione owner riguarda i
soli documenti di `mcp-website-dev-39539`, database `(default)`, incluse le
sottocollezioni. Conservare database, indici, policy originali, utenti Auth,
entrambi i bucket applicativi e relativi oggetti, bucket upload/source. Nessuna
modifica a produzione o ai flag deploy. Nessun seed/import sintetico implicito.

**Prova dipendenze:** inventario completo141funzioni produzione, snapshot runtime
riletto20novembre,141metadati oggetti sorgenti con generazione fissata. I139backend
Python hanno impronta MD5/dimensione identica e inizializzazione Firestore uguale
al campione distribuito verificato: `GCLOUD_PROJECT=mcp-website-2a1ad`, fallback
ADC, nessun file credenziali configurato nel pacchetto, nessun dotenv caricato
in cloud. Altri2pacchetti: `app` e `ssrmcpwebsite2a1ad`; analizzati codice web,
bundle, dotenv e configurazioni JSON. I soli riferimenti staging sono uno script
seed non tra gli import di main e `.env.development` SSR. Il gestore Next usa
`dev:false`; tutte le versioni compatibili firebase-frameworks0.11.0–0.11.8
pubblicate al momento del controllo confermano la scelta; bundle compilati senza
identificatori staging. Inventario/sorgenti invariati al readback finale.
Questa prova riguarda le funzioni censite, non client esterni o altri workload.
Evidenze locali filtrate in `.local/staging/cloud-b-verification/`, inclusi
`production_dependency_check_summary_2026-11-20.json` e i file richiamati.
Nessun archivio sorgente o valore di credenziale salvato su disco.

**Preflight bonifica:**20novembre zero Functions in tutte le regioni e zero
servizi Cloud Run managed globali staging e zero operazioni Firestore in corso.
Firestore Native nam5, PITR disabilitato. Il service agent Firestore ha già
`roles/firestore.serviceAgent`; il bucket di recupero proposto risponde404
al preflight, quindi non è una risorsa esistente da riusare.
Prima di applicare, riconfermare inventario vuoto, progetto/account espliciti,
assenza di operazioni Firestore concorrenti e risorsa destinazione. L'owner deve
sospendere eventuali script/operatori con accesso IAM durante export e pulizia:
il blocco Rules descritto sotto non blocca gli SDK amministrativi.

**Delta proposto da approvare (non applicato):**

1. Creare solo `gs://mcp-website-dev-39539-firestore-recovery-20261120` nel progetto
   staging, STANDARD, multi-regione US, Uniform Bucket-Level Access e Public
   Access Prevention enforced. Nessuna Firebase Storage rule sul nuovo bucket,
   nessun grant runtime/deploy/build, nessun grant di progetto, nessun pubblico.
   Conservare i normali accessi amministrativi ereditati; nessuna revoca dei ruoli
   esistenti. Nessun lifecycle di cancellazione o retention lock; soft-delete
  7giorni esplicito. Il bucket e l'export restano finché l'owner decide la retention.
   Se esiste già o presenta impostazioni inattese, fermarsi: non riusarlo o
   modificarlo alla cieca. Usare i permessi del service agent Firestore già
   presenti nel medesimo progetto; su403 fermarsi, nessun grant aggiuntivo implicito.
2. Salvare il riferimento esatto del ruleset Firestore corrente e i metadati di
   indici/database. Pubblicare temporaneamente solo su Firestore staging un
   ruleset deny-all per accessi client, con ripristino dell'esatto riferimento
   precedente. Non modificare Storage Rules. Il blocco impedisce anche le letture
   client durante la finestra; account IAM privilegiati continuano ad avere accesso.
   Prima del blocco individuare un percorso inesistente sotto una collection con
   lettura pubblica nelle Rules correnti (per esempio events), verificando un404
   con API key web staging e senza OAuth/ADC: è il controllo positivo del canale
   client, senza leggere dati reali. Dopo la pubblicazione rileggere il riferimento
   release, attendere almeno10minuti dalla modifica e ripetere la lettura non
   mutante sul medesimo percorso: deve essere negata dalle Rules. Errori di API key,
   trasporto o App Check non valgono come prova. Se il controllo non è possibile
   o non conferma il blocco, fermarsi prima dell'export. La sospensione degli
   scrittori IAM deve durare fino alla fine di verifica/ripristino Rules.
   [Propagazione Firestore Rules](https://firebase.google.com/docs/firestore/security/get-started).
3. Export gestito completo di tutti i gruppi/sottocollezioni nel prefisso nuovo
   `gs://mcp-website-dev-39539-firestore-recovery-20261120/pre-cleanup-20261120`.
   Una sola richiesta con ID operazione registrato, nessun retry automatico.
   Prima di cancellare: operazione done/success senza errori, prefisso corrispondente,
   presenza dei file metadata di export e inventario oggetti con generazioni.
   Non mostrare né scaricare i documenti reali nei log. Nessun restore dichiarato
   collaudato: il percorso di recupero è definito, non provato mediante import.
4. Solo dopo export verificato, eseguire una sola richiesta
   `projects/mcp-website-dev-39539/databases/(default):bulkDeleteDocuments`,
   corpo vuoto: tutti i collection group, comprese sottocollezioni. Non eliminare
   il database, non usare loader demo e non indirizzare mai produzione.
   Registrare ID/progresso/esito; su esito parziale non ripetere automaticamente.
5. Verificare fine operazione senza errori e assenza di documenti, comprese
   sottocollezioni residue; riconfermare database/indici e metadati/IAM degli
   altri bucket invariati. Ripristinare il ruleset Firestore originale per ID
   e verificarlo. Nessun bootstrap/deploy segue implicitamente questa bonifica.

**Guasti e recupero:** export fallito significa nessuna cancellazione; dopo
verifica che il dataset sia intatto, ripristinare le Rules originali e fermarsi.
Se la creazione bucket o il blocco Rules è parziale, inventariare prima di
qualsiasi ripresa. Se la cancellazione è parziale, mantenere il blocco client e
l'export, fermarsi e riportare lo stato: nessun retry/import automatico.
Prima di un eventuale import, la cancellazione deve essere in stato terminale
verificato: mai sovrapporre bulk delete ancora attivo e ripristino.
L'eventuale ripristino è un import completo dallo stesso prefisso nel solo
Firestore staging, dopo decisione owner; non legge né scrive la produzione.

**Costi:** export con una lettura per documento e storage del backup; bulk delete
con cancellazioni e letture fatturate. Volume totale e importo non ancora misurati;
il budget15EUR è un avviso, non un limite rigido. Nessuna garanzia di costo totale
viene dedotta dal numero20di raccolte root. Le operazioni gestite restano attive
anche se si chiude il terminale: riprendere dal loro ID, non reinviarle.
Fonti: [export/import](https://firebase.google.com/docs/firestore/manage-data/export-import),
[bulk delete API](https://firebase.google.com/docs/firestore/reference/rest/v1/projects.databases/bulkDeleteDocuments),
[caricamento env Next](https://nextjs.org/docs/pages/guides/environment-variables).

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

**Prossima approvazione cloud:** solo dopo completamento del prospetto B con
risorse nominate,policy correnti e differenze da applicare. A è già completato.
Il prospetto sotto è lo stato desiderato proposto,non un diff IAM verificato
sul cloud né un file eseguibile. I gate deploy,dati e produzione restano separati.

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

### Stima economica staging e proposta costi — 16 novembre 2026

**Richiesta owner:** mantenere staging completo e contenere la spesa; frequenza
indicata: **4 deploy completi al mese**. Billing dichiarato a posto dall'owner
nella conversazione; non verificato indipendentemente via API. Questa sezione
è una stima e una proposta: non autorizza provisioning,modifiche runtime,
cleanup,nuove restrizioni di accesso o attivazione della pipeline.

**Perimetro e ipotesi:** staging us-central1,Firestore esistente nam5,bucket
applicativo US;141 endpoint Python (130 HTTP,8 trigger,3 scheduler) e1 SSR.
Tutte le funzioni e i flussi restano presenti. Istanze minime0 proposte per
backend e SSR; limiti massimi da validare con concorrenza e worker. Nessuna
riduzione arbitraria della memoria per risparmiare: nel codice attuale non ci
sono limiti memoria/min/max espliciti. Il frontend è Firebase Hosting con SSR,
non Firebase App Hosting: usare il listino Hosting corretto.

Il dataset sintetico locale già generato contiene53684 documenti; l'export
occupa33,14MiB. È una misura dei file locali,non dei byte Firestore cloud:
indici,metadati e copie hanno dimensioni diverse. **Aggiornamento owner del
17 novembre 2026:** il dataset4000 soci/50 eventi e le prove massive restano
negli emulatori. Non importare quel dataset nello staging cloud per il gate.
Sul cloud usare pochi record sintetici isolati e scenari rappresentativi per
provare infrastruttura e integrazioni reali. Nessun test di carico o import
massivo cloud fa parte dell'autorizzazione corrente.

Prima di ogni sessione cloud fissare il numero massimo di scenari, chiamate,
record coinvolti ed email effettive; contare anche richieste SDK, trigger,
letture/scritture, scheduler e fan-out indiretto. Preparare il runner con limiti
di operazioni e invii verificabili prima di eseguire i test. Al raggiungimento
del limite fermare nuove operazioni, senza replay o retry automatici delle
azioni con effetti esterni. Eseguire soltanto le prove necessarie e le
regressioni invalidate da modifiche; niente ripetizioni dell'intera suite
locale sul cloud. Email vere soltanto ai destinatari autorizzati e in numero
minimo per verificare consegna, contenuto e resa; non inviare a tutti gli alias
per ciascuno scenario né abilitare invii dal caricamento dati.

I due scheduler giornalieri (cleanup03:00 e rebuild05:15 Europe/Rome) e quello
annuale restano nel modello. Le letture dei job e i trigger vanno conteggiati,
anche quando nessuno apre il sito. Questi limiti operativi non sono un tetto
monetario garantito del provider; gli alert budget non arrestano la spesa.
Runner e limiti della futura sessione cloud ancora da predisporre/verificare;
questa nota non attesta un controllo tecnico già installato.

**Nessuna telemetria cloud disponibile:** durata e tipo macchina delle build,
riuso effettivo,dimensione media delle immagini,CPU/memoria/tempo fatturati,
traffico,spesa legacy e quote gratuite residue sono ancora da misurare. La
CLI14.26.0 installata ha functionsv2deployoptimizations=true di default e
prevede riuso immagini attraverso sourceToken; non equiparare141 funzioni a
141 build distinte misurate. Il riuso è una possibilità,non un risparmio
attestato. Non attivare Artifact Analysis/scansioni a pagamento per ipotesi;
eventuali obblighi di scansione vanno verificati e quantificati separatamente.

**Modello mensile di riferimento,in USD senza IVA/cambio,sconti o crediti:**

| Voce | Ipotesi di calcolo (non misura) | Importo USD |
|---|---|---:|
| Cloud Build |4 rilasci ×10 build effettive ipotizzate ×5 minuti ×0,0156/min,e2-highcpu-8 come tariffa di scenario,non macchina effettiva verificata |3,12|
| Artifact Registry |20GiB medi fatturabili ×circa0,10/GiB-mese; nessuna deduzione quota gratuita |2,00|
| Esecuzione backend/SSR/worker |100000 richieste complessive;100000 vCPU-secondi e50000 GiB-secondi,comprendendo startup:0,000024/vCPU-s +0,0000025/GiB-s +0,40/milione richieste |2,565|
| Firestore,Hosting,file,backup piccoli e trasferimenti |Accantonamento3,50USD per uso funzionale e dati sintetici contenuti; non derivato da una fattura o da una tariffa nam5 misurata |3,50|
| Scheduler |3 job ×0,10/mese,quota gratuita non dedotta |0,30|
| Secret Manager |1 versione automatica e10000 accessi:0,06 +0,03,quote gratuite non dedotte |0,09|
| GitHub Actions |240 minuti Linux2core ×0,006/min; minuti inclusi/pubblico non dedotti; ulteriore CI PR non compresa |1,44|
| **Totale di scenario** |Cloud11,575 +GitHub1,44 |**13,015**|

I20GiB sono uno spazio medio ipotizzato,non una retention applicata né un
limite automatico. Il tempo runtime è tempo fatturato ipotizzato,non una
promessa che ogni richiesta duri1secondo;cold start,funzioni pesanti e durata
reale dei rebuild possono cambiare il risultato. Il prezzo orario Registry
pubblicato è0,000136986USD/GiB-ora,dunque circa0,10 con730ore. Al totale
possono aggiungersi altri dati/risorse legacy,retention backup maggiore,
scansioni opzionali,traffico extra e un eventuale abbonamento GitHub necessario
alle protezioni; questi elementi non sono ancora inventariati. La stima
riguarda l'assetto target staging: non è una differenza riconciliata rispetto
alla fattura attuale e non comprende produzione,domini personalizzati o
servizi provider live.

**Intervallo di pianificazione:**circa5–15USD/mese per4 rilasci e uso leggero,
se il riuso è efficace e i volumi restano nelle ipotesi. È una stima
condizionata,non un preventivo garantito o un tetto. Le quote gratuite possono
ridurre l'addebito ma non sono assunte disponibili: per Cloud Build la quota
2500minuti è promozionale e limitata a e2-standard-2 nel default pool,quindi
non è applicata alla tariffa e2-highcpu-8 del modello. Altre quote sono
condivise fra progetti dello stesso billing account; Logging ha quota50GiB
per progetto/mese,ipotesi uso inferiore con retention ordinaria30giorni.

**Sensibilità senza riuso:**4 rilasci ×142 build ×4minuti ×0,0156 =35,4432USD
solo build. Con50GiB medi Registry (=5USD) e le altre ipotesi uguali,il totale
è48,3382USD/mese. Anche questo è un caso ipotetico,non il massimo possibile:
più minuti,memoria,traffico o dati possono superarlo. Il primo mese contiene
bootstrap e prove baseline/rollback aggiuntive,che vanno conteggiate oltre ai
4 rilasci se non ricadono in quei4.

**Proposta operativa da concordare prima dell'attivazione:**

- Obiettivo di pianificazione5–15USD/mese,budget iniziale di monitoraggio15USD
  equivalente nella valuta di fatturazione,con avvisi50/80/100%. Un budget di
  soli avvisi non interrompe la spesa. Nessun automatismo che disabiliti
  billing,cancelli risorse o tagli un rilascio in corso.
- Staging completo disponibile con minInstances0,accettando cold start;
  scalabilità massima per funzione/SSR misurata e validata. Un limite per
  funzione non è un limite globale di spesa su142 servizi.
- Raggruppare modifiche in4 rilasci mensili e separare test/CI da pubblicazione.
  **La pipeline attuale,pur disattivata dai flag,prevede deploy a ogni push
  main dopo attivazione:** il comportamento di attivazione va concordato e
  adattato prima di accendere i flag; non è già manual-only.
- Repository senza DELETE durante bootstrap/prova rollback come da blocco A.
  Dopo la prova concordare cleanup che protegga immagini attive e baseline
  per tutta la finestra30giorni. Non applicare ora una semplice cancellazione
  per età o per numero di versioni. Verificare crescita settimanalmente
  durante bootstrap; nessuna conservazione illimitata adottata come politica
  definitiva e nessuna cancellazione automatica implementata da questa stima.
- Dopo il primo deploy autorizzato raccogliere soltanto metadati costi:
  buildId/macchina/minuti,byte unici Registry,tempo fatturato e min/max istanze,
  letture/scritture e trasferimenti. Ricalcolare la stima prima del successivo
  deploy se il riuso non funziona o i volumi superano le ipotesi. Confermare
  piano GitHub,visibilità repo,minuti residui e spesa preesistente prima di
  dichiarare un costo complessivo effettivo.

Fonti primarie consultate16novembre2026:
[Cloud Build](https://cloud.google.com/build/pricing),
[Cloud Run](https://cloud.google.com/run/pricing),
[Artifact Registry](https://cloud.google.com/artifact-registry/pricing),
[Firestore](https://cloud.google.com/firestore/pricing),
[Cloud Storage](https://cloud.google.com/storage/pricing),
[Firebase Hosting](https://firebase.google.com/pricing),
[Secret Manager](https://cloud.google.com/secret-manager/pricing),
[Scheduler](https://cloud.google.com/scheduler/pricing),
[Eventarc](https://cloud.google.com/eventarc/pricing),
[Logging](https://cloud.google.com/products/observability/pricing),
[GitHub runner](https://docs.github.com/en/billing/reference/actions-runner-pricing),
[GitHub Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions),
[budget](https://docs.cloud.google.com/billing/docs/how-to/budgets).

**Stato:**stima pronta per discussione; nessuna risorsa creata o modifica
cloud/codice di esecuzione applicata. Procedere dopo scelta del budget e
manifest B nominativo approvato,non come conseguenza automatica della stima.
