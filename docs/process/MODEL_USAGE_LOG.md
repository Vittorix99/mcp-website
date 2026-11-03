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
