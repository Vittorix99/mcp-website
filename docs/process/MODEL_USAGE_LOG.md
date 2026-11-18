# Registro di utilizzo dei modelli

Data della ripresa: 2026-10-25. Branch di esecuzione:
`core-ws1-environment-safety`, worktree `.worktrees/core-ws1`.

Il coordinatore delle sessioni su ChatGPT/Codex usa **GPT-6.1 Sol**; su Claude
Code si usa lo schema Opus/Sonnet/Haiku di `AGENTS.md`. Le righe sotto sono
tutte di sessioni ChatGPT/Codex; le nuove righe indicano la piattaforma. Questo registro
conta incarichi effettivamente delegati, non token, chiamate interne o costi.
La sessione non espone un contatore affidabile di consumo per singolo agente.

| Modello | Incarico delegato | Effort | Stato ed evidenza |
|---|---|---|---|
| Sol 6.1 | `baseline_review_sol`: review indipendente della base pre-WS1 | high | Conclusa: 85 test passati, nessun rilievo bloccante |
| Luna 6 | `toolchain_bootstrap_luna`: bootstrap e test del toolchain | medium | Concluso e corretto dopo review Sol; 7 test finali passati, installazione reale verificata da Sol |
| Luna 6 | `sender_test_migration_luna`: aggiornamento meccanico dei test Sender | medium | Concluso; Luna non ha eseguito i test per un percorso Python errato; Sol ha corretto un caso e verificato il perimetro, 143 test passati prima dell'ulteriore caso allowlist |
| Luna 6 | `pass2u_fake_luna`: fake e factory Pass2U | medium | Concluso: 8 test passati; Sol ha integrato e verificato il perimetro provider, 82 test passati |
| Luna 6 | `build_fixture_luna`: server locale di risposte fixture | medium | Concluso: 3 test passati, riletti e rieseguiti da Sol insieme agli altri test frontend |
| Luna 6 | `github_guide_luna`: guida operativa GitHub Actions | medium | Conclusa; riletta da Sol, verifica dei link passata |
| Luna 6 | `docs_links_luna`: controllo dei link Markdown e test comportamentali | medium | Concluso; Sol ha riletto codice e rieseguito i 3 test, passati |
| Luna 6 | `operations_docs_luna`: catalogo risorse e transizione credenziali | medium | Concluso; Sol ha confrontato il catalogo con la policy e verificato i link |
| Luna 6 | `newsletter_tests_luna`: migrazione test newsletter ai DTO e repository attuali | medium | Concluso; da 17 falliti a 21 passati, revisione e riesecuzione Sol |
| Luna 6 | `communication_api_tests_luna`: migrazione test API comunicazioni e impostazioni | medium | Concluso; Sol ha revisionato e rieseguito i 29 test, passati |
| Luna 6 | `scanner_tests_luna`: verifica CLI scanner e redazione in repository temporanei | low | Concluso; Sol ha revisionato e rieseguito i 5 test, passati; nessuna modifica allo scanner |
| Luna 6 | `sender_routes_tests_luna`: aggiornamento percorsi mock Sender | low | Concluso; Sol ha revisionato e rieseguito 20 test, passati |
| Luna 6 | `membership_api_tests_luna`: migrazione test API membership ai DTO attuali | medium | Concluso; revisionato da Sol con correzione del nome di un test e rimozione di un mock inutile; suite completa verde |
| Luna 6 | `purchase_contract_tests_luna`: migrazione test acquisti ai DTO attuali | medium | Concluso; revisionato da Sol, corretto il campo nel test del tipo non valido; suite completa verde |
| Luna 6 | `event_fixture_repairs_luna`: fixture eventi, location e ticket | medium | Concluso; 37 test passati, diff revisionato da Sol; suite completa verde |
| Luna 6 | `inactive_workflow_docs_luna`: template futuri inattivi e stato documentazione | low | Concluso; Sol ha corretto i project ID abbreviati, verificato YAML, blocchi di esecuzione e link; nessun deploy implementato o abilitato |
| Sol 6.1 | `ws1_final_review_sol`: unica review indipendente dell'intero branch WS1 | high | Conclusa; 3 Important, nessun Critical/Minor. Sol coordinatore ha corretto tutti e tre con regressioni RED→GREEN; nessuna seconda review |
| Sol 6.1 (Codex) | `local_seed_review_sol`: review circoscritta del seed Auth locale richiesto dal proprietario | high | Conclusa; 1 Important sull'attesa di Auth all'avvio, accettato e corretto dal coordinatore con regressione RED→GREEN. Verifica finale: 685 test backend e 24 frontend passati; lint mirato pulito. Login e accesso admin confermati dal proprietario il 2026-10-27, non verificati indipendentemente nel browser |

Totale registrato: **15 incarichi a Luna e 3 review delegate a Sol**,
oltre al lavoro del coordinatore Sol nella conversazione principale.

Ultima verifica delle suite Sol: **685 test backend e 24 frontend passati, zero fallimenti**;
build ed emulatori passati nella verifica Core precedente al seed. Login locale
confermato dal proprietario il 2026-10-27. Core locale pronto per revisione del proprietario;
CI remota e deploy non eseguiti. Audit Gitleaks storico:
12 segnalazioni classificate nel rapporto separato del worktree. Chiavi private
disabilitata/assente verificate su IAM; MailerLite ritirato e progetto OAuth
legacy non più esistente su conferma del proprietario. Il proprietario ha
rinviato le modifiche alle restrizioni Firebase. Nessun valore segreto riportato.

Sol ha implementato e integrato le parti che richiedono giudizio: matrice
ambienti, sicurezza credenziali, startup Firebase, gateway PayPal, policy mail
e Sender, collegamento degli altri provider e protezioni della build frontend.

Ogni nuova delega sarà annunciata in chat con modello, incarico e motivo;
al ritorno verranno comunicati esito, verifica e correzioni. Nessun importo o
numero di token verrà stimato a partire dal conteggio dei task.

## WS2 — contratti API

Esecuzione nativa coordinatore, senza deleghe di implementazione.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / Sol 6.1 | `ws2_final_review_sol`: unica review indipendente del branch WS2 | high | Conclusa; tre Important accettati e corretti dal coordinatore con tre regressioni RED→GREEN. Suite frontend finale 39 passati, inventario confermato. Una sola review indipendente; prova Firebase reale PASS, exit 0 riportato dal proprietario. |

Conteggio WS2: 0 incarichi Luna, 1 review Sol. Token e costi non disponibili.

## WS2 — ritiro riferimenti API obsoleti

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / Luna 6 | `obsolete_api_cleanup_luna`: rimozione meccanica di quattro riferimenti e due servizi frontend senza consumatori | low | Interrotto dal limite di utilizzo dopo test RED e modifiche ai file. Il coordinatore ha revisionato e completato il diff: 40 test frontend passati, gate 126 riferimenti/128 export/zero eccezioni/zero errori; lint mirato e scanner passati. Build passata. Diff accettato con correzione del commento sulle eccezioni; nessun nuovo tentativo delegato. |

Conteggio di questo intervento: 1 incarico Luna, 0 review delegate Sol; review del diff al coordinatore. Token e costi non disponibili.

## WS3 — osservabilità HTTP

Esecuzione nativa, nessuna delega di implementazione.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / Sol 6.1 | `ws3_observability_review_sol`: unica review finale su privacy, contratti HTTP e autenticazione | high | Conclusa pulita, nessun rilievo. Il revisore ha rieseguito 23 test backend mirati e 9 test del verificatore HTTP. Coordinatore: 709 backend e 42 frontend passati. Proprietario: smoke Firebase PASS, exit 0. Nessuna seconda review. |

Conteggio WS3: 0 incarichi Luna, 1 review Sol. Token e costi non disponibili.

## Staging — matrice dei casi sintetici

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / Luna 6 | `staging_case_index_luna`: inventario in sola lettura dei casi nei test partecipanti e sconti | low | Concluso; nessun file modificato e nessun test eseguito. Coordinatore: riferimenti controllati, risultati accettati e integrati nel piano; interpretazione di pagamenti, autorizzazioni, ingressi e statistiche mantenuta al coordinatore. Verifica documentale finale del 2026-11-07: 105 ID scenario univoci, link locali esistenti e nessun errore di whitespace. |

Conteggio della matrice: 1 incarico Luna, 0 review delegate Sol.
Token e costi non disponibili. I 105 scenari sono definiti, non eseguiti.

## Staging — generatore e importazione locale — 2026-11-07

Implementazione del coordinatore: nessuna delega meccanica, poiché il lavoro
tocca relazioni, importi, stati e limiti delle scritture.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / Sol 6.1 | `synthetic_generator_review_sol`: unica review indipendente di generatore, caricatore emulatori e relativi test | high | Conclusa: 1 P1 (regole fuori dalla directory progetto Firebase), 2 P2 (documenti residui tra seed diversi, token storici fuori cronologia/durata). Tutti accettati e corretti dal coordinatore con regressioni RED→GREEN. Revisore: 23 test mirati passati prima delle correzioni. Coordinatore: 33 test scripts/tests passati dopo correzioni, export completo verificato offline, configurazione verificata con CLI Firebase installata, scanner segreti zero finding. Successiva regressione sui metadati RPC: 34 test strumenti passati. Vittorio ha poi riportato importazione e rilettura di 53684 documenti negli emulatori, codice 0; esito del proprietario, non rieseguito dal coordinatore. Nessun cloud/Auth/mail modificato. |

Conteggio generatore: 0 incarichi Luna, 1 review Sol. Token e costi non
disponibili. Nessuna seconda review. Le verifiche offline non equivalgono
all'esecuzione della matrice API o alla prova reale nell'emulatore.

## Staging — review API interrotta e audit utilizzo — 2026-11-08

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / Sol 6.1 | `synthetic_api_review_sol`: review circoscritta di fixture API/statistiche e runner | high | Interrotta da usage limit, non conclusa. Nota parziale: gli stati parametrizzati vengono dalla funzione di produzione che si vuole verificare; serve un elenco atteso indipendente. Nessuna approvazione della review e nessun nuovo tentativo. Nessuna esecuzione emulatori dal revisore. |

Conteggio batteria API: 0 deleghe Luna, 1 review Sol incompleta. Il
coordinatore ha eseguito 39 test strumenti, 44 unit test collegati e collection
di 23 nuovi scenari; non sono 23 scenari runtime superati. Sviluppo sospeso
durante l'indagine richiesta da Vittorio, senza modifiche cloud.

Per questa indagine sono disponibili contatori nativi Codex: non sono stime
da numero di incarichi. All'ultimo «vai procedi» risultava già usato il 64%
della finestra di 300 minuti. La review iniziò all'89%, arrivò al 99% e fallì
per limite. Nel tratto esaminato: 22 eventi usage distinti del coordinatore
Sol medium e 13 della review Sol high. Contesto coordinatore fino a 287527
token per chiamata nel tratto, in larga parte cached. Questi input ripetuti
non sono nuovi token distinti né unità di quota fatturate.

Configurazione locale osservata: service_tier=priority. Possibile Fast da
verificare nel client; tier effettivamente servito non disponibile nel record
del turno. Nessuna configurazione o policy modificata. Numeri dettagliati e
limiti interpretativi in `.local/staging/usage-audit.json`, escluso da Git.

Indicazioni per la ripresa: passaggio di consegne breve in chat nuova, letture
mirate, un'unica review del blocco completo e verifica del tier Standard.
Caveman comprime le risposte: non limita da solo contesto, ragionamento o
numero di chiamate. Nessuna percentuale di risparmio o costo stimato.

## Staging — ripresa batteria API — 2026-11-09

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / Sol 6.1 | `synthetic_api_completion_review_sol`: review circoscritta della batteria API, fixture, runner e collegamento CI | high | Conclusa senza rilievi; accettata dal coordinatore. Revisore: 5 test del runner passati, sola lettura, nessuna esecuzione emulatori o operazione cloud. Coordinatore: sei stati letterali indipendenti al posto dei casi derivati da `PurchaseStatus.invalid_statuses()`; 39 test strumenti e 35 unitari acquisti/statistiche passati, 23 casi API raccolti, scanner zero segnalazioni, diff check pulito. Esecuzione API negli emulatori ancora da confermare dal proprietario. |

Conteggio ripresa: 0 incarichi Luna, 1 review Sol. Token e costi non disponibili.

Vittorio ha eseguito `scripts/staging/test_emulator.py --api` e riportato
**23 test passati**, un warning HarfBuzz, codice 0 e arresto pulito degli
emulatori. Esito runtime del proprietario, non rieseguito dal coordinatore.
Questo chiude la prima batteria API; non dimostra tutti i 105 scenari,
autenticazione reale, provider reali o staging cloud.

## Pagamenti — errori e retry API — 2026-11-09

Implementazione nativa del coordinatore: test su stati intermedi di pagamento,
nessuna delega meccanica e nessuna modifica applicativa.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / Sol 6.1 | `payment_failure_api_review_sol`: review finale del diff test/fixture PAY-05/07/08/09 | high | Conclusa senza rilievi, accettata dal coordinatore. Revisore: handler, service, repository e statistiche verificati; costruzione ApiException, confini importi e diff check confermati offline. Sola lettura e nessuna esecuzione emulatori. Coordinatore: 29 test unitari collegati passati, 35 casi API raccolti (12 nuovi), scanner zero segnalazioni, diff check pulito. Vittorio ha poi riportato 35 test API passati, un warning HarfBuzz, codice 0 e arresto pulito degli emulatori; esito del proprietario, non rieseguito dal coordinatore. |

Conteggio blocco: 0 incarichi Luna, 1 review Sol. Token e costi non disponibili.

## Sconti — checkout API e utilizzi — 2026-11-09

Implementazione nativa del coordinatore nel perimetro pagamenti, senza
modifiche applicative né deleghe meccaniche.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / Sol 6.1 | `discount_api_review_sol`: review finale dei test DIS-01/03/04/05/07 e relative fixture | high | Conclusa senza rilievi, accettata dal coordinatore. Revisore: flussi reali DTO/handler/service/repository, formule e claim/retry verificati; sintassi Python e diff check puliti. Nessuna esecuzione emulatori dal revisore. Coordinatore: 27 test unitari collegati passati, scanner zero segnalazioni e diff check pulito; corretto un import test non compatibile con import-mode=importlib. Successivamente ispezionato il report locale `.local/staging/api-results.xml` del 2026-11-09T20:18:05+01:00: 51 test, zero failure/error/skipped, inclusi 16 casi sconto. Il coordinatore non ha riavviato gli emulatori; il report non certifica separatamente exit code del runner o arresto degli emulatori. |

Conteggio sconti: 0 incarichi Luna, 1 review Sol. Token e costi non disponibili.

## Sconti — limiti e totale zero — 2026-11-09

Estensione nativa del coordinatore, 13 nuove istanze DIS-02, senza codice
applicativo modificato. Il caso a totale zero è una caratterizzazione fake.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / Sol 6.1 | `discount_boundary_review_sol`: review finale dell'estensione DIS-02 | high | Conclusa senza rilievi, accettata dal coordinatore. Revisore: contratti sconti/capture/persistenza/statistiche, default fee e preservazione del retry dopo claim verificati; sintassi e diff check puliti. Nessuna esecuzione emulatori/cloud dal revisore. Coordinatore: 27 test unitari collegati passati, scanner zero segnalazioni e diff check pulito; successivamente ispezionato il JUnit locale del 2026-11-09T20:47:56+01:00: 64 test, zero failure/error/skipped, con 8 invalidi e il caso totale zero presenti, oltre ai 4 parametri validi aggiunti. Emulatori non riavviati dal coordinatore. Il report non certifica separatamente exit code del runner e arresto degli emulatori. |

Conteggio limiti: 0 incarichi Luna, 1 review Sol. Token e costi non disponibili.

## Concorrenza — PAY-12 / DIS-06 — 2026-11-09

Implementazione nativa, nessuna delega Luna. Proprietario: review Sol medium
fino a nuova indicazione (override di high). Nessuna modifica applicativa.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / Sol 6.1 | `concurrent_checkout_review_sol`: unica review finale di test PAY-12/DIS-06, chiave SDK e regole aggiornate | medium | Conclusa con due rilievi P2 sui test, entrambi corretti e accettati dal coordinatore: ID partecipante generato distinto da membershipId; timeout executor non sufficiente, sostituito da deadline del processo dedicato. Self-check offline con worker bloccati: processo figlio termina con exit 124, senza emulatori/network. Dopo le correzioni: 66 casi API raccolti, 34 unitari collegati passati. Runtime eseguito dal proprietario (exit 1 riportato); JUnit locale 2026-11-09T21:43:48+01:00 ispezionato dal coordinatore: 66 casi, 65 passati, 1 failure PAY-12 su due purchase anziché una; zero error/skipped. DIS-06 passa, incluso perdente catturato senza purchase e retry senza ricattura. Nessun fix applicativo; arresto emulatori non attestato dal JUnit. |

Conteggio dispatch effettivi: 0 incarichi Luna, 1 review Sol. Token e costi non disponibili.

## PAY-12 — claim atomico della capture — 2026-11-09

Implementazione del coordinatore, nessuna delega Luna (stato di pagamento e
concorrenza). Una review delegata a un sotto-agente (effort medium, modello
predefinito dell'host, non `gpt-6.1-sol`): nessun Critical, 2 Important e
2 Minor; corretti test del service sul perdente, codice del retry esaurito e
`Aborted`. Conteggio: 0 incarichi Luna, 1 review delegata. Token e costi non
disponibili.


## DIS-06 — prenotazione sconto prima della capture — 2026-11-11

Implementazione del coordinatore; nessuna delega Luna perché il blocco tratta
stati di pagamento e concorrenza.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6.1-sol | `dis06_reservation_review_sol`: unica review finale su prenotazione, rilascio, scadenza e failure window | medium | Conclusa: un Important sulla riduzione admin del limite sotto le prenotazioni vive, riprodotto RED e corretto con CAS; nessun Minor. Coordinatore: 768 unitari, 39 test script, 72 API, 6 integrazione sconti passati; 20 corse concorrenti da 3 scenari (60/60). Lock timeout runtime risolto dopo la review sostituendo le transazioni con batch condizionati alla versione; verificati retry CAS e aggiornamenti atomici delle ricevute. Runner emulatori exit 0 e arresto pulito. Scanner zero segnalazioni; nessun cloud/provider reale o CI remota. Esito della review accettato e corretto dal coordinatore; nessuna seconda delega. |

Conteggio dispatch effettivi nel blocco: 0 incarichi Luna, 1 review Sol.
Token e costi non disponibili.


## Recupero controllato ordini — 2026-11-11

Implementazione nativa del coordinatore, nessuna delega Luna: stato pagamento,
concorrenza e permessi richiedono Sol. Approvato in chat dal proprietario.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6.1-sol | `order_recovery_review_sol`: unica review finale recupero admin, deduplica condivisa, ricevute sconto, auth e failure window | medium | Conclusa: 4 Important (lookup soci estranei, dati salvati malformati, prezzi locali non finiti, metadati legacy alterati), tutti riprodotti RED e corretti dal coordinatore; nessun Critical/Minor. Esito accettato e corretto, nessuna seconda delega. Verifica finale: 826 unitari, 39 test script, 107 API, 6 integrazione sconti e 20×6 scenari concorrenti (120/120), tutti passati; runner emulatori exit 0 e arresto pulito. Scanner zero segnalazioni, diff check pulito. Nessuna CI remota/cloud/provider reale. |

Conteggio dispatch effettivi: 0 incarichi Luna, 1 review Sol. Token/costi non disponibili.


## PAY-10 — cattura non verificabile — 2026-11-11

Implementazione nativa del coordinatore (pagamenti), nessuna delega Luna.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6.1-sol | `pay10_review_sol`: unica review finale su importi, totale assente, final_capture e conservazione dell'incasso | medium | Conclusa: 1 Important (amount non-oggetto prima della persistenza) e 1 Minor sui limiti Decimal, riclassificato Important dal coordinatore per la violazione della tolleranza monetaria. Entrambi riprodotti RED e corretti; nessun rilievo differito. Review ripresa sullo stesso incarico dopo interruzione, nessuna seconda delega. Esito accettato e corretto dal coordinatore: 849 unitari, 39 test script, 151 API e 6 integrazione sconti passati; emulatori exit 0 e arresto pulito. Scanner zero segnalazioni e diff check pulito. Nessuna CI remota/cloud/provider reale. |

Dispatch effettivi: 0 Luna, 1 review Sol. Token/costi non disponibili.


## DIS-08 — tessera inclusa e sconti — 2026-11-12

Regola confermata dal proprietario; implementazione nativa del coordinatore,
52 nuove prove API, nessuna modifica applicativa o agli importi. Nessuna delega
Luna per la verifica congiunta di pagamenti, rinnovi e contabilità.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6.1-sol | `dis08_review_sol`: unica review finale su formule incluse, dati socio, quote/storico e retry | medium | Conclusa senza Critical/Important/Minor, accettata dal coordinatore. 52 nuovi casi, 203/203 API, 849 unitari e 39 script passati. Verificati lordo richiesto reale, dati/storico socio, soci attivi e retry invariato; anche capture senza impostazione quota per i soci correnti. Primo errore fixture (email .test) corretto prima della review. Runner emulatori exit 0 e arresto pulito; scanner zero segnalazioni e diff check pulito. Nessuna modifica applicativa, cloud/provider reale o prova CI remota. |

Dispatch effettivi: 0 Luna, 1 review Sol. Token/costi non disponibili.


## OPS-07 — pulizia ordini e corsa con capture — 2026-11-12

Implementazione nativa del coordinatore; nessuna delega Luna per logica di
pagamento, cancellazione e concorrenza.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6.1-sol | `ops07_review_sol`: unica review finale su timestamp, eligibility cleanup, marker pre-provider e CAS delete | medium | Conclusa senza Critical/Important/Minor, accettata dal coordinatore. Successivo controllo autore: quattro forme list/map di metadati riprodotte RED e corrette con confronti conservativi; nessuna seconda delega. Verifica finale 885 unitari, 39 script, 224 API e 6 integrazione sconti verdi, exit 0 e arresto pulito. Scanner zero segnalazioni e diff check pulito. Nessun cleanup cloud, deploy o provider reale. |

Dispatch effettivi: 0 Luna, 1 review Sol. Token/costi non disponibili.


## EVT-03 — disponibilità evento nel checkout — 2026-11-12

Implementazione nativa del coordinatore: controlli su pagamenti e recupero,
nessuna delega Luna. Regola sold_out/coming_soon/ended confermata dall'owner.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6.1-sol | `event_availability_review_sol`: unica review finale del gate condiviso, create/capture, recovery e retry completato | high | Conclusa senza rilievi; accettata dal coordinatore. Verifiche eseguite dal coordinatore: 888 unitari, 233 API passati, exit 0 e arresto pulito emulatori, scanner 0 e diff check pulito. Review ha letto l'evidenza senza rieseguire le suite. Nessun deploy/cloud/provider reale/CI remota. |

Dispatch effettivi: 0 Luna, 1 review Sol. Token/costi non disponibili.


## EVT-04 — prenotazione posti e capienza — 2026-11-12

Implementazione nativa coordinatore: pagamenti, concorrenza e recovery; 0 deleghe Luna.
Regole owner: admin libero, hold intero gruppo alla creazione per 10 minuti,
capienza zero/assente blocca online; piano approvato in chat.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6.1-sol | `event_capacity_review_sol`: unica review finale CAS posti, create/capture, provisioning/recovery e cleanup | high | Conclusa con 1 P1 (ricreazione posti da hold consumed dopo delete/rivendita) e 1 P2 (sconto impegnato da capture scaduta). Accettati e corretti dal coordinatore con regressioni RED→GREEN; nessuna seconda delega. Verifica finale coordinatore: 888 unitari, 268 API, 6 integrazioni sconti passati, JUnit zero failure/error/skip, emulatori exit 0 e arresto pulito; scanner 0 e diff check pulito. Nessun deploy/cloud/provider reale/CI remota. |

Dispatch effettivi: 0 Luna, 1 review Sol. Token/costi non disponibili.


## MEM-03/04 — validità membership uniforme — 2026-11-12

Regola anno corrente E flag valido approvata in chat. Implementazione nativa
coordinatore: ammissione, pagamenti e contabilità; nessuna delega Luna.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6.1-sol | `membership_validity_review_sol`: unica review finale della regola condivisa, conteggi e controllo create/capture/rinnovo | high | Conclusa con 1 P1 (target duplicati per stessa email fallivano dopo primo rinnovo) e 1 P2 (preflight validava ID diverso dopo riassegnazione email). Accettati e corretti dal coordinatore con 4 regressioni RED→GREEN; nessuna seconda delega. Finale: 888 unitari, 287 API (19 nuovi), 6 integrazioni sconti passati; JUnit zero failure/error/skip, emulatori exit 0/arresto pulito, scanner 0 e diff check pulito. Nessun deploy/cloud/provider reale/CI remota. |

Dispatch effettivi: 0 Luna, 1 review Sol. Token/costi non disponibili.


## OPS-01 — identità e permessi area personale — 2026-11-12

Piano approvato in chat dopo probe Auth reale emulato. Implementazione nativa
coordinatore: autorizzazione e claim concorrenti; nessuna delega Luna.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6.1-sol | `ops01_identity_review_sol`: unica review finale identità JWT/UID, primo link verificato, preferenze CAS e guardie emulatori | high | Conclusa senza rilievi; accettata dal coordinatore. Evidenze eseguite dal coordinatore:888 unitari,44 script,57 Auth Emulator senza bypass verifier,287 API,36 integrazioni membri,6 integrazioni sconti,2 smoke Python e client smoke HTTP completo passati. JUnit zero failure/error/skip, runner exit0/shutdown pulito, scanner0/diff pulito. Review ha letto le evidenze senza duplicare suite. Nessun deploy/cloud/provider reale/CI remota. |

Dispatch effettivi:0 Luna,1 review Sol. Token/costi non disponibili.


## OPS-02 — metodi HTTP e contratti richiesta — 2026-11-12

Blocco autorizzato dal proprietario in chat. Diagnosi checkout e correzioni
a cura del coordinatore; matrice ripetitiva dei contratti delegata a Luna.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6-luna | `ops02_contract_matrix`: test su metodi errati e body non validi nelle API core elencate nel test | medium | Conclusa:352 test mirati passati; Sol ha corretto l’assunzione del mock su create_membership (validazione nel service prima della repository), letto il diff e accettato il risultato. Nessuna modifica applicativa delegata. |

| Codex / gpt-6.1-sol | `ops02_final_review`: unica review finale dei contratti HTTP/DTO e del preflight checkout | high | Conclusa senza rilievi; accettata dal coordinatore. Verificati1240 unitari (352 nuovi),44 script,329 API (42 nuovi),2 smoke Python e client HTTP emulato PASS; JUnit API zero failure/error/skip, exit0/shutdown pulito. Scanner sorgenti modificati0/diff pulito. Review ha letto le evidenze senza rieseguire suite. Nessun deploy/cloud/provider reale/CI remota. |

Dispatch effettivi:1 Luna,1 review Sol. Token/costi non disponibili.


## OPS-03/05 — invii tessere, ticket e omaggi — 2026-11-12

Proseguimento richiesto dal proprietario in chat; solo prove locali/provider fake.
Diagnosi trigger e policy degli esiti incerti a cura del coordinatore.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6-luna | `ops05_omaggio_tests`: lotto di test emulatori su contatori, skip/reinvio, fallimenti e allegati stub | medium | Conclusa:5 caratterizzazioni verdi e1 regressione RED di sovrascrittura durante invio. Sol ha letto/accettato il test e corretto la persistenza con scritture mirate; nessuna modifica applicativa delegata. |

| Codex / gpt-6.1-sol | `ops03_05_final_review`: unica review finale di trigger, claim invio, retry manuale e scritture mirate | high | Conclusa con1 P2: claim membership interrotto da scrittura concorrente non-trigger. Accettato dal coordinatore, riprodotto con2 RED e corretto con4 riletture/precondizioni prima dei provider; nessuna seconda delega. Finale1243 unitari,348 API (19 nuovi),2 smoke Python e client HTTP emulato PASS; API JUnit zero failure/error/skip, exit0/shutdown pulito. Script44 di OPS-02 riutilizzati invariati. Scanner sorgenti0/diff pulito. Nessun deploy/cloud/provider reale/CI remota. |

Dispatch effettivi:1 Luna,1 review Sol. Token/costi non disponibili.


## OPS-06 — isolamento provider disabilitati e simulati — 2026-11-12

User story autorizzata dal proprietario in chat. Verifiche locali soltanto;
nessun cambio configurazione cloud o provider reale.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6-luna | `ops06_sender_offline_matrix`: test di14 operazioni sync/service con policy Sender disabilitata reale | medium | Conclusa:14 passati, spy trasporto mai raggiunto; diff letto/accettato da Sol. Nessuna modifica applicativa delegata. |
| Codex / gpt-6.1-sol | `ops06_final_review`: unica review finale isolamento provider e override gender disabilitato | high | Conclusa senza rilievi; accettata dal coordinatore. Evidenze1257 unitari,358 API,14 Sender focalizzati e2 smoke Python+client HTTP emulato PASS; API JUnit zero failure/error/skip, exit0/shutdown pulito, scanner sorgenti0/diff pulito. Nessun rerun del reviewer. Script44 invariati riutilizzati; nessun deploy/cloud/provider reale/CI remota. |

Dispatch effettivi:1 Luna,1 review Sol. Token/costi non disponibili.


## OPS-08 — pulizia conservativa token scanner — 2026-11-12

Proseguimento sviluppo richiesto dal proprietario. Verifiche e cancellazioni
solo nell'emulatore dedicato; nessuna pulizia cloud o modifica schedule.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6-luna | `ops08_token_cleanup_tests`: matrice soglia7 giorni e timestamp con client in memoria | medium | Conclusa:10 verdi e6 RED su timestamp malformati. Sol ha corretto il nome campo fixture in is_active e aggiunto il caso campo assente (17 casi finali); diff accettato. Nessuna modifica applicativa delegata. |
| Codex / gpt-6.1-sol | `ops08_final_review`: unica review finale soglia token, cancellazione condizionale e storico scansioni | high | Conclusa senza rilievi, accettata dal coordinatore. Verificati1274 unitari,364 API (6 nuovi),2 smoke Python e client HTTP emulato PASS; API JUnit zero failure/error/skip, runner exit0/shutdown pulito, source scanner0/diff pulito. Nessun rerun reviewer;44 script invariati riutilizzati. Nessuna pulizia cloud/deploy/CI remota. |

Dispatch effettivi:1 Luna,1 review Sol. Token/costi non disponibili.


## OPS-09 — export/import sintetico ripetibile e ripresa — 2026-11-12

Proseguimento sviluppo autorizzato dal proprietario; solo file privati
sintetici ed emulatore dedicato, nessuna scrittura cloud.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6-luna | `ops09_offline_resume_tests`: test byte ripetibili, export interrotto/temp residui e messaggi CLI | medium | Conclusa:3 verdi e3 RED (due temp residui, avviso import parziale). Diff letto e accettato da Sol; correzioni production al coordinatore. Nessuna modifica applicativa delegata. |
| Codex / gpt-6.1-sol | `ops09_final_review`: unica review finale export privato, ripresa import e messaggi redatti | high | Conclusa senza rilievi; accettata dal coordinatore.50 test script e369 scenari emulatore passati, API JUnit zero failure/error/skip, runner exit0/shutdown pulito, scanner sorgenti0/diff pulito. Backend1274 e smoke OPS-08 riutilizzati invariati, nessun rerun reviewer. Nessuna scrittura cloud/provider/account/deploy/CI remota. |

Dispatch effettivi:1 Luna,1 review Sol. Token/costi non disponibili.


## OPS-10 — liste applicative sul dataset completo — 2026-11-12

Proseguimento sviluppo autorizzato; scope annunciato: completezza liste API
e ricerca/filtri/ordinamento/paginazione già disponibili nell'app, solo locale.

| Piattaforma / modello | Incarico | Effort | Stato ed evidenza |
|---|---|---|---|
| Codex / gpt-6-luna | `ops10_bulk_read_contracts`: confronto liste API con export completo4000 soci/50 eventi | medium | Conclusa:1 scenario completo passato (4000 soci,50 eventi,7076 acquisti,21701 partecipanti), identità/conteggi e snapshot invariato; diff/evidenze letti e accettati da Sol. Nessuna modifica applicativa delegata. |

| Codex / gpt-6.1-sol | `ops10_final_review`: review del contratto liste sul corpus completo e limiti evidenze UI | high | Conclusa con1 rilievo sul test: confronto aggregato acquisti/evento non rileva scambi fra ID. Accettato dal coordinatore; sostituito con mappa per singolo acquisto. Suite370 API passata in88.19s; dopo il rilievo, scenario aggiornato passato in41.02s (369 deselected). Entrambi JUnit zero failure/error/skip e runner exit0/shutdown pulito. UI parziale:40 pagine soci/4000 unici A-Z, conteggi2025/2026; restanti filtri e altre liste UI aperti dopo indisponibilità controllo browser. Server locali riavviati su richiesta owner; nessuna modifica applicativa/cloud/provider reale. |

Dispatch effettivi:1 Luna,1 review Sol. Token/costi non disponibili.

Chiusura OPS-10,2026-11-13: nessun ulteriore dispatch. Coordinatore: profilo1985–2008 corretto inline;50 test strumenti e scenario completo aggiornato1PASS/369deselected in40.69s. UI agent:3854ordinari/39pagine e146omaggi/6pagine; limiti proiezioni visibili documentati. Verificati53749documenti+2impostazioni invariati dopo le prove agent. Acquisti chiusi con risposta owner «tutto passa» sul blocco ricerca/evento/status/date/ordinamento; evidenza owner-reported, non verifica indipendente. Scope OPS-10 completato; nessun nuovo difetto frontend dimostrato, nessuna ulteriore review delegata per documentazione, nessun push/cloud/provider/CI remota. Dispatch complessivi invariati:1 Luna,1 Sol high; token/costi non disponibili.
