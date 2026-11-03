# WS2 — Verifica del primo blocco

Stato: primo blocco WS2 integrato in `main`; CI remota verificata. Base: `d8ac90e8`.
Design e piano approvati dal proprietario in chat il 2026-11-03.

## Perimetro

- Inventario di tutta la mappa API: 130 riferimenti contro 128 export HTTP.
- Quattro eccezioni legacy esplicite, documentate nell'[audit](WS2_API_REFERENCE_AUDIT.md).
- Contratto di lettura degli eventi: liste pubbliche e card, dettaglio,
  errori 400/404/405, liste e dettaglio admin, rifiuti 401 per assenza di
  token, token membro e token invalido. Nessun bypass nell'HTTP remoto.
- Gate aggiunto al workflow PR esistente; nessun nuovo provider o deploy.

## Evidenze locali

- Baseline backend: 686 passati, warning WeasyPrint/HarfBuzz preesistente.
- Task 1: sei regressioni RED prima dell'implementazione, poi GREEN.
  Suite frontend completa: 30 passati, lint mirato senza errori.
- Task 2: sei regressioni RED prima dell'implementazione, poi GREEN.
  Suite frontend completa: 36 passati, lint mirato senza errori.
- Prova reale eseguita dal proprietario: `nvm use && ./scripts/test-emulators.sh`.
  Log riportato: `Emulator client smoke: PASS (Firestore/Auth/Storage/Functions/event HTTP contracts)`
  e `Script exited successfully (code 0)`. Risultato owner-reported, non
  presentato come esecuzione indipendente dell’agente. Emulatori arrestati dal comando.
- Build fixture passata; lint globale: 0 errori e 53 warning preesistenti.
- Backend rieseguito: 686 passati. Scanner repository: 0 segnalazioni;
  configurazione Firebase valida; link Markdown modificati validi.
- Review indipendente finale Sol high: tre Important riprodotti e corretti
  con regressioni RED→GREEN. Suite frontend finale: 39 passati; inventario
  confermato. Vedere [rapporto di review](WS2_CORE_REVIEW.md).
- CI remota WS2: [run 5](https://github.com/Vittorix99/mcp-website/actions/runs/41730948217)
  passata: 686 test backend, 39 frontend, 2 smoke Python e client/HTTP emulatori.
  [PR #2](https://github.com/Vittorix99/mcp-website/pull/2) unita dal proprietario
  in `main` (`f1d70ffe`). Albero del merge confrontato col branch: identico.
  Nessun deploy o merge eseguito dall’agente.

## Decisioni e limiti

Esecuzione nativa, una sola review indipendente finale con tre rilievi corretti. Riutilizzate le
dipendenze già installate di WS1 perché i lockfile non cambiano; symlink
locali ignorati da Git. `.gitignore` ora ignora anche symlink con i nomi
`node_modules` e `.venv`, coerentemente con le directory già escluse.

I test del verificatore HTTP usano un server loopback temporaneo: intercettano
fetch soltanto nel processo di test e mantengono intatto il controllo della
destinazione nel codice. Questi test verificano gli assert, non sostituiscono
la prova contro Firebase. Nessun token viene incluso nei messaggi di errore.

L'inventario statico non certifica body, metodi, risposte e permessi di tutte
le API, né gli accessi dinamici a proprietà non dichiarate nella mappa.
I servizi legacy signup/domande non vengono ripristinati o rimossi.
Nessuna prova browser generale o modifica ai pagamenti nel presente blocco.
