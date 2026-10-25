# Metodologia di sviluppo

**Progetto:** MCP-WEB-PROJECT

**Stato:** metodologia di lavoro adottata

**Ultimo aggiornamento:** 24 ottobre 2026

## 1. Scopo

Questa metodologia definisce come il progetto trasforma una richiesta in software verificato, revisionato, rilasciato e mantenuto.

Il modello combina:

- **AI-Native SDLC**, che governa il ciclo di vita, gli artefatti e i gate umani;
- **skill specializzate**, usate solo nella fase in cui sono necessarie;
- **Git e CI**, che conservano le decisioni e producono evidenze ripetibili;
- **approvazioni umane**, necessarie per le decisioni di prodotto, architettura e produzione.

Le skill non costituiscono processi indipendenti. Sono strumenti coordinati all'interno di un unico processo di sviluppo.

## 2. Principi operativi

1. **Comprendere prima di modificare.** Il comportamento corrente viene ricostruito dal codice, dai test, dalla configurazione e dal runtime.
2. **Lavorare per workstream piccoli.** Ogni workstream ha un obiettivo, un perimetro e criteri di successo espliciti.
3. **Separare fatti e proposte.** Gli artefatti distinguono evidenze, inferenze, assunzioni e raccomandazioni.
4. **Progettare prima di implementare.** Il codice applicativo non cambia prima dell'approvazione del design e del piano.
5. **Proteggere i contratti.** Prima di un refactoring si documentano e testano i comportamenti osservabili da preservare.
6. **Scrivere test prima del codice quando applicabile.** La modifica parte da una prova fallibile del comportamento desiderato.
7. **Correggere la causa, non il sintomo.** I comportamenti inattesi seguono un processo di debugging sistematico.
8. **Usare evidenze fresche.** Nessun lavoro viene dichiarato completo senza verifiche eseguite sullo stato corrente.
9. **Mantenere i cambiamenti reversibili.** Le modifiche sono piccole, isolate e accompagnate da una strategia di rollback proporzionata al rischio.
10. **Tenere la produzione sotto controllo umano.** Deploy, migrazioni, rotazioni di credenziali e operazioni distruttive richiedono autorizzazione esplicita.

## 3. Struttura del processo

```text
DIREZIONE
Discovery → Intent
       │
       └── Gate 1: approvazione dell'intent

SOLUZIONE
Design tecnico → Specifica
       │
       └── Gate 2: approvazione del design

ESECUZIONE
Piano → Build → Test → Review
       │
       └── Gate 3: approvazione del piano e del merge

RILASCIO
Staging → Verifica
       │
       └── Gate 4: autorizzazione alla produzione

OPERAZIONI
Produzione → Monitoraggio → Manutenzione → Nuovo intent, se necessario
```

## 4. Fasi, skill e risultati

| Fase | Obiettivo | Skill principali | Artefatto o risultato |
|---|---|---|---|
| Skill routing | Selezionare solo le skill necessarie al lavoro corrente. | `using-superpowers` | Sequenza di lavoro coerente. |
| Discovery | Capire il sistema esistente, i vincoli, i rischi e il comportamento reale. | `brainstorming` | Assessment, inventari, assunzioni e domande aperte. |
| Intent | Definire problema, risultato atteso, non-obiettivi e criteri di successo. | `ai-native-sdlc` | `intent/intent.md`. |
| Design | Definire comportamento, confini, contratti, alternative e conseguenze. | `brainstorming`, `ai-native-sdlc` | Specifica di design ed eventuali ADR. |
| Planning | Trasformare il design approvato in passi implementativi verificabili. | `writing-plans` | `plan.md` con ordine, file, test, rischi e rollback. |
| Isolamento | Evitare interferenze con modifiche non correlate. | `using-git-worktrees`, quando necessario | Branch o worktree isolato. |
| Build | Implementare una piccola unità alla volta partendo dai test. | `test-driven-development`, `executing-plans` | Codice e test coerenti con il piano. |
| Debug | Identificare la causa di test falliti o comportamenti inattesi. | `systematic-debugging` | Diagnosi dimostrata e correzione mirata. |
| Verification | Eseguire controlli completi sullo stato corrente. | `verification-before-completion` | Evidenze di test, build, lint, contratti e sicurezza. |
| Review | Valutare correttezza, regressioni, sicurezza e conformità al design. | `requesting-code-review`, `receiving-code-review` | Review risolta con evidenze. |
| Integration | Preparare il cambiamento per PR, merge o conservazione del branch. | `finishing-a-development-branch` | Handoff pulito e verificato. |
| Deploy | Rilasciare prima in staging e poi, se autorizzato, in produzione. | `ai-native-sdlc` | Release verificata e rollback disponibile. |
| Maintain | Monitorare il sistema, gestire incidenti e alimentare il ciclo successivo. | `systematic-debugging`, `ai-native-sdlc` | Diagnosi, fix o nuovo intent. |

## 5. Gate umani

### Gate 1 — Intent

Viene approvato:

- il problema da risolvere;
- chi o cosa è coinvolto;
- il risultato atteso;
- il perimetro e i non-obiettivi;
- i criteri misurabili di successo.

L'approvazione autorizza la fase di Design, non l'implementazione.

### Gate 2 — Design

Vengono approvati:

- il comportamento desiderato;
- i confini tra componenti;
- i contratti e le responsabilità;
- l'alternativa tecnica scelta;
- i principali rischi e compromessi.

L'approvazione autorizza la creazione del piano, non ancora le modifiche al codice.

### Gate 3 — Piano e integrazione

Prima della Build viene approvato il piano di implementazione. Prima dell'integrazione vengono verificate le evidenze prodotte dalla Build e dalla Review.

Il piano deve specificare almeno:

- ordine delle modifiche;
- file e componenti coinvolti;
- test da scrivere ed eseguire;
- compatibilità da preservare;
- rischi e rollback;
- comandi di verifica.

### Gate 4 — Produzione

La produzione richiede un'autorizzazione umana esplicita. Il gate comprende:

- risultato dei test di staging;
- smoke test post-deploy previsti;
- piano di rollback;
- eventuali migrazioni e riconciliazioni;
- responsabile della decisione;
- finestra e condizioni operative del rilascio.

## 6. Dimensione e rischio del cambiamento

Il processo resta lo stesso, ma la profondità degli artefatti cresce con il rischio.

| Classe | Esempi | Requisiti minimi |
|---|---|---|
| Basso rischio | Documentazione, correzioni interne senza cambio di comportamento. | Perimetro chiaro, verifica mirata, review del diff. |
| Rischio ordinario | Feature, refactoring, API, query, componenti applicativi. | Design versionato, piano, test, CI, review e staging. |
| Alto rischio | Pagamenti, autenticazione, autorizzazione, credenziali, dati, infrastruttura, migrazioni. | Design completo, ADR se necessario, test di errore e recupero, rollback, riconciliazione, staging e approvazione esplicita. |

La classe di rischio può aumentare durante il lavoro. In quel caso il processo si ferma e vengono aggiornati design e piano prima di proseguire.

## 7. Artefatti versionati

| Artefatto | Funzione |
|---|---|
| `intent/intent.md` | Descrive perché il lavoro esiste e cosa significa avere successo. |
| Assessment e inventari | Registrano lo stato osservato e le lacune di evidenza. |
| `spec.md` o design equivalente | Descrive il comportamento e la soluzione approvata. |
| ADR | Registra una decisione architetturale, le alternative e le conseguenze. |
| `plan.md` | Specifica l'esecuzione concreta e le verifiche. |
| Test | Rendono eseguibili i requisiti e proteggono i contratti. |
| Review record | Registra problemi trovati, decisioni e risoluzioni. |
| Release evidence | Contiene esiti di staging, autorizzazione, deploy e rollback. |
| Incident record | Ricostruisce causa, impatto, correzione e prevenzione. |

Ogni artefatto deve indicare stato, data, ambito e decisioni ancora aperte. Un documento proposto non viene trattato come approvato.

## 8. Ciclo di implementazione

Ogni unità di lavoro segue questo ciclo:

1. Selezionare un comportamento piccolo dal piano approvato.
2. Scrivere o identificare il test che dimostra il requisito.
3. Verificare che il test fallisca per la ragione prevista, quando si applica TDD.
4. Implementare il cambiamento minimo necessario.
5. Eseguire i test mirati.
6. Eseguire la suite di regressione proporzionata al rischio.
7. Aggiornare documentazione e contratti interessati.
8. Controllare il diff rispetto al piano.
9. Ripetere per l'unità successiva.

Se emerge un comportamento inatteso, l'implementazione si interrompe e si applica `systematic-debugging` prima di proporre una correzione.

## 9. Strategia di verifica

La verifica deve essere fresca, ripetibile e proporzionata al rischio. Può includere:

- test unitari delle regole di business;
- test di integrazione di API, repository, Firebase e provider;
- test contrattuali tra frontend e backend;
- test end-to-end dei flussi critici;
- lint, type checking e build;
- test di sicurezza e secret scanning;
- benchmark di latenza, operazioni e costo;
- smoke test in staging;
- verifica del rollback per i cambiamenti ad alto rischio.

Un test precedente, una valutazione visiva del codice o la sola assenza di errori di compilazione non dimostrano che il lavoro è completo.

## 10. Review e integrazione

La review verifica, in ordine:

1. rischi critici e problemi di sicurezza;
2. correttezza funzionale e invarianti;
3. regressioni e compatibilità dei contratti;
4. affidabilità dei test;
5. aderenza a design e piano;
6. prestazioni e costi, quando rilevanti;
7. chiarezza e manutenibilità.

Il feedback non viene applicato automaticamente: viene verificato tecnicamente con `receiving-code-review`. Dopo le correzioni, tutte le verifiche rilevanti vengono rieseguite.

## 11. Deploy e manutenzione

Il flusso ordinario di rilascio è:

```text
PR verificata
→ merge autorizzato
→ deploy staging
→ smoke test e accettazione
→ autorizzazione produzione
→ deploy produzione
→ verifica post-deploy
→ monitoraggio
```

Un incidente o una deviazione significativa riapre il ciclo:

- un difetto circoscritto entra in debugging e produce un test di regressione;
- un cambiamento di comportamento richiede un nuovo intent;
- una decisione architetturale richiede un ADR;
- una deviazione dal piano richiede l'aggiornamento del piano prima di continuare.

## 12. Responsabilità

### Responsabilità umane

- priorità e obiettivi di prodotto;
- accettazione dell'intent;
- approvazione del design e delle decisioni architetturali;
- approvazione del piano;
- accettazione di rischi residui;
- autorizzazione di merge, produzione, migrazioni e operazioni distruttive.

### Responsabilità dell'agente

- analisi del repository e raccolta delle evidenze;
- redazione degli artefatti;
- implementazione conforme al piano approvato;
- scrittura ed esecuzione dei test;
- debugging sistematico;
- verifica e review tecnica;
- documentazione dei risultati e dei limiti delle evidenze.

### Responsabilità dell'automazione

- eseguire controlli ripetibili;
- impedire merge o release quando i gate tecnici falliscono;
- isolare configurazioni e segreti per ambiente;
- conservare log e artefatti di verifica;
- segnalare regressioni, anomalie e deviazioni dai limiti operativi.

## 13. Definition of Done

Un workstream è completo soltanto quando:

- il comportamento implementato corrisponde al design approvato;
- il piano riflette l'implementazione effettiva;
- i test richiesti sono presenti e passano;
- build, lint, contratti e controlli di sicurezza applicabili passano;
- non rimangono problemi critici o alti non accettati esplicitamente;
- il diff è stato revisionato;
- documentazione e ADR sono aggiornati;
- staging è stato verificato quando richiesto;
- rollback e monitoraggio sono definiti quando richiesti;
- le evidenze vengono riportate con i comandi e i risultati effettivi;
- il gate umano successivo è stato registrato.

## 14. Regole specifiche per MCP-WEB-PROJECT

- Firebase resta operativo durante stabilizzazione e assessment.
- Firebase, hybrid e Supabase vengono confrontati con gli stessi benchmark e senza una conclusione predeterminata.
- Nessuna migrazione di produzione inizia prima dell'approvazione dell'ADR architetturale.
- Local, test e staging non devono poter accedere accidentalmente a risorse o provider di produzione.
- Pagamenti, autenticazione, autorizzazione, dati personali e credenziali sono sempre ad alto rischio.
- I contratti frontend/backend vengono protetti prima di ristrutturare i confini interni.
- Le ottimizzazioni vengono decise dopo avere raccolto misure di latenza, operazioni, errori e costo.
- I dati di staging devono essere sintetici, deterministici o esplicitamente anonimizzati e minimizzati.

## 15. Stato corrente

La discovery iniziale è documentata nei seguenti artefatti:

- `intent/intent.md`;
- `docs/architecture/CURRENT_STATE_ASSESSMENT_2026-10-24.md`;
- `docs/architecture/API_CONTRACT_INVENTORY_2026-10-24.md`.

L'intent è stato approvato il 24 ottobre 2026 e il design di **WS1 — sicurezza di ambienti, credenziali e provider** è stato approvato il 25 ottobre 2026. Il prossimo artefatto è il piano di implementazione Core WS1; il codice resta bloccato fino all'approvazione del piano.
