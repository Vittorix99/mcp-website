# Transizione credenziali — Core WS1

**Stato aggiornato al 2026-11-13:** CI della PR #11 passata sul commit `0b85eb7`; verifica offline/emulatori e build fixture, non deploy cloud. La transizione Secret Manager/WIF e il deploy automatico non sono implementati. Il piano operativo sotto prepara il blocco successivo; nessuna creazione di identità, modifica IAM, rotazione/revoca o deploy deriva dalla sola presenza di questo documento.

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
attività da fare. Implementazione non avviata su richiesta owner; quando
ripreso, il medesimo perimetro non richiede una nuova approvazione del piano.
Restano distinti i gate concreti di accesso cloud e rilascio descritti sotto.

### Riscontri di sola lettura

- GitHub `Vittorix99/mcp-website`:0 Environment,0 variabili Actions repository,
  0 secret Actions repository. Controllati i soli metadati; nessun valore
  segreto letto, caricato o modificato.
- Google Cloud `mcp-website-dev-39539`:0 workload identity pool globali.
  Non sono state create identità né abilitate API o policy.
- Unico workflow attivo: `.github/workflows/pr.yml`, eventi pull_request e
  workflow_dispatch. Nessun trigger push/main né deploy.
- I file `workflow-templates/staging.yml` e `production.yml` sono esempi
  inattivi fuori da `.github/workflows/`; non implementano deploy o rollback.
- Il runtime legge e valida configurazione/provider durante l'import
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

Oggi sono completati ricognizione e approvazione del piano; implementazione
in backlog. Workflow attivi, binding
runtime, accessi cloud, test post-deploy e rollback devono essere implementati
nel blocco approvato; i template inattivi non vanno semplicemente spostati o
sbloccati. Le prove della PR #11 restano valide per il codice già concluso.

Riferimenti primari: [Firebase environment e secret parameters](https://firebase.google.com/docs/functions/config-env),
[WIF per pipeline](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines).
