# Guida operativa a GitHub Actions

Questa guida spiega come leggere i controlli automatici del repository. La suite unit offline completa è verde: **667 test superati**. Il workflow `.github/workflows/pr.yml` è stato preparato, ma non pubblicato né eseguito; la verifica finale e la review di WS1 restano in sospeso.

## Workflow, job e step

Un **workflow** è un’automazione definita da un file YAML in `.github/workflows/`. Un **job** è un gruppo di attività che GitHub esegue in un ambiente dedicato. Ogni job contiene uno o più **step**: singoli comandi o azioni, per esempio installare dipendenze o lanciare un controllo. Se uno step termina con errore, il job normalmente si interrompe e il workflow segnala il fallimento.

## Controlli della pull request

Il workflow PR previsto parte quando si apre o aggiorna una pull request e può anche essere avviato manualmente. Esegue verifiche in sola lettura: installazione riproducibile con dipendenze Python hashate, Node.js 20 e Python 3.11; controlli di policy e suite unit con rete disabilitata; configurazione frontend, lint e fixture build; smoke test con emulatori; scansione redatta del repository. Non sono previsti job di deploy.

La scansione è progettata per non stampare valori segreti. Evita comunque di copiare log in spazi pubblici o includerli in screenshot senza averli controllati. Il workflow non prevede al momento il caricamento di artefatti: i log sono la fonte principale per diagnosticare un errore. Eventuali artefatti aggiunti in futuro dovranno essere ripuliti da dati sensibili prima della pubblicazione.

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

## Deploy futuri e blocchi attuali

In futuro, **Workload Identity Federation (WIF)** potrà dare a GitHub un’identità temporanea, limitata all’ambiente staging o production. Evita così chiavi JSON di lunga durata salvate come segreti. I modelli inattivi in `docs/operations/workflow-templates/` sono scheletri illustrativi non testati, non un’implementazione di deploy. Restano deliberatamente disabilitati e bloccati; non scaricano né estraggono l’archivio e non eseguono codice dell’artefatto. L’attivazione richiede un gate separato del proprietario e la verifica di provenienza dell’artefatto, commit sorgente, IAM e revisori dell’ambiente. I deploy, la verifica della provenienza e il rollback non sono implementati; non sono configurati i revisori e le protezioni degli ambienti GitHub.

L’inventario di proprietà e risorse Doppler è ancora necessario e blocca la preparazione dello staging. Fino al completamento di tale inventario e delle approvazioni richieste, questi modelli non autorizzano deploy. Nessun deploy è attivo.
