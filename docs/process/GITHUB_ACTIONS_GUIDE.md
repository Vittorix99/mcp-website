# Guida operativa a GitHub Actions

Questa guida spiega come leggere i controlli automatici del repository.
WS1 è integrato in `main`; la quarta esecuzione del workflow è passata su GitHub.
WS2 aggiunge il controllo globale dei riferimenti API e approfondisce i contratti
HTTP degli eventi. Per risultati e limiti aggiornati vedere
[verifica WS2](../reviews/WS2_CORE_VERIFICATION.md).

## Workflow, job e step

Un **workflow** è un’automazione definita da un file YAML in `.github/workflows/`. Un **job** è un gruppo di attività che GitHub esegue in un ambiente dedicato. Ogni job contiene uno o più **step**: singoli comandi o azioni, per esempio installare dipendenze o lanciare un controllo. Se uno step termina con errore, il job normalmente si interrompe e il workflow segnala il fallimento.

## Controlli della pull request

Il workflow PR previsto parte quando si apre o aggiorna una pull request e può anche essere avviato manualmente. Esegue verifiche in sola lettura: installazione riproducibile con dipendenze Python hashate, Node.js 22 e Python 3.11; controlli di policy e suite unit con rete disabilitata; configurazione frontend, lint e fixture build; smoke test con emulatori; scansione redatta del repository. Non sono previsti job di deploy.

La scansione è progettata per non stampare valori segreti. Evita comunque di copiare log in spazi pubblici o includerli in screenshot senza averli controllati. Il workflow non prevede al momento il caricamento di artefatti: i log sono la fonte principale per diagnosticare un errore. Eventuali artefatti aggiunti in futuro dovranno essere ripuliti da dati sensibili prima della pubblicazione.

Lo step **API reference contracts** confronta tutta la mappa frontend con gli
handler HTTP esportati. Non ci sono eccezioni legacy: ogni riferimento senza
handler fa fallire il controllo.
Lo step **Full emulator smoke** verifica anche lettura eventi, risposte
pubbliche e permessi admin tramite HTTP, con token emessi dall'emulatore Auth.

## Trovare e leggere un’esecuzione

Nel repository su GitHub, apri **Actions**, seleziona il workflow interessato e poi l’esecuzione. La pagina mostra lo stato e i job; apri il job fallito, quindi lo step rosso. Leggi l’output dall’inizio dell’errore: cerca il comando eseguito, il messaggio e il codice di uscita (exit code). Il codice `0` indica successo; un valore diverso da zero indica che il comando è terminato con errore. GitHub documenta la cronologia e la navigazione dei log nella [guida alla cronologia delle esecuzioni](https://docs.github.com/en/actions/how-tos/monitor-workflows/view-workflow-run-history).

Puoi consultare le stesse informazioni da terminale, dalla cartella del repository:

```sh
gh run list
gh run view RUN_ID --log
```

Sostituisci `RUN_ID` con l’identificativo mostrato da `gh run list`. Non abilitare il debug logging come prima risposta: può esporre variabili d’ambiente e altri dettagli operativi. Non includere valori di segreti in screenshot o messaggi di supporto.

## Ripetere un’esecuzione

Prima di riprovare, leggi il log e individua la causa. Una ripetizione è appropriata solo per un problema temporaneo di infrastruttura o download, dopo aver verificato che l’errore sia transitorio. Puoi ripetere solo i job falliti dall’interfaccia GitHub oppure con:

```sh
gh run rerun RUN_ID --failed
```

La ripetizione usa lo stesso commit. Se serve una modifica al codice o alla configurazione, crea un nuovo commit: questo produrrà una nuova esecuzione. Consulta la [guida ufficiale alle ripetizioni](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs) per i dettagli.

## Environment: configurazione e regole per una destinazione di deploy

Un GitHub Environment è una configurazione nominata del repository, per esempio
`staging` o `production`, che un job Actions seleziona con `environment:`.
Può contenere variabili non segrete, secret e regole di protezione: branch/tag
ammessi, approvazioni richieste e altre condizioni. L'Environment non crea
progetti Google Cloud, database, server o siti e non carica automaticamente
un file .env nell'applicazione. I valori devono essere usati dal workflow e
dalla configurazione di build/runtime previsti.

Il branch identifica il codice; il workflow definisce le operazioni; un job
viene eseguito su un runner; l'Environment ne applica configurazione e regole
per il deploy; Google Cloud ospita le risorse su cui quel job interviene.
Le regole PR proteggono l'integrazione del codice, quelle dell'Environment
proteggono il job di rilascio: sono passaggi distinti.

Le variabili vengono lette tramite `vars.NOME`, i secret tramite
`secrets.NOME`. Per esempio `DEPLOY_SERVICE_ACCOUNT` ha un valore diverso nei
due Environment: il job selezionato riceve il riferimento dell'ambiente
corrispondente. Le variabili non sono un deposito per credenziali. I secret
sono supportati da GitHub, ma nel piano del progetto i payload dei provider
risiedono in Secret Manager, con accesso delle identità runtime appropriate.
GitHub Actions si autenticherà al cloud tramite OIDC/WIF e credenziali temporanee,
senza chiavi service-account persistenti caricate in GitHub.

La disponibilità delle protezioni dipende dal piano GitHub e dalla visibilità
del repository; non basta poter creare un Environment per dedurre il supporto
ai required reviewers. Fonti ufficiali:
[gestione Environment](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments),
[protezioni, variabili e secret](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments),
[OIDC](https://docs.github.com/en/actions/reference/security/oidc).

## Preparazione deploy e stato corrente — 16 novembre 2026

Nel ramo di sviluppo sono preparati `.github/workflows/release.yml` e
`deploy-environment.yml`: verifica dello SHA main, job staging e successiva
produzione protetta, build per ambiente, snapshot e rollback. Gli esempi in
`docs/operations/workflow-templates/` restano template inattivi, distinti dalla
pipeline preparata. La presenza del codice non certifica l'attivazione cloud.

I flag repository `ENABLE_STAGING_DEPLOY` e `ENABLE_PRODUCTION_DEPLOY` governano
la creazione dei job; le variabili Environment includono riferimenti WIF,
account e configurazioni pubbliche usate nel job. I due tipi di variabili hanno
scope diversi: i flag repository non vanno spostati dentro gli Environment.
Il piano produzione richiede approvazione tramite Environment; supporto e
configurazione reali sono ancora da verificare.

L'inventario owner conferma zero Environment GitHub e nessun pool WIF staging;
Cloud Build API staging è da abilitare e frontend/backend staging non sono
distribuiti. La creazione degli Environment non sostituisce il bootstrap
cloud né la verifica IAM. Nessun deploy attivo dichiarato da questa guida.
Resta valida la decisione owner di rinviare l'integrazione finale in main:
attivazione, trigger pipeline e condizioni WIF devono essere riconciliati con
quella decisione prima di qualunque modifica. Inventario e gate aggiornati in
[CREDENTIAL_TRANSITION.md](../operations/CREDENTIAL_TRANSITION.md).
