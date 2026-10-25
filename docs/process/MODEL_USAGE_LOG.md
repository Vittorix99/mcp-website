# Registro di utilizzo dei modelli

Data della ripresa: 2026-10-25. Branch di esecuzione:
`core-ws1-environment-safety`, worktree `.worktrees/core-ws1`.

Il coordinatore della conversazione usa **GPT-6.1 Sol**. Questo registro
conta incarichi effettivamente delegati, non token, chiamate interne o costi.
La sessione non espone un contatore affidabile di consumo per singolo agente.

| Modello | Incarico delegato | Effort | Stato ed evidenza |
|---|---|---|---|
| Sol 6.1 | `baseline_review_sol`: review indipendente della base pre-WS1 | high | Conclusa: 85 test passati, nessun rilievo bloccante |
| Luna 6 | `toolchain_bootstrap_luna`: bootstrap e test del toolchain | medium | Concluso e corretto dopo review Sol; 7 test finali passati, installazione reale verificata da Sol |
| Luna 6 | `sender_test_migration_luna`: aggiornamento meccanico dei test Sender | medium | Concluso; Luna non ha eseguito i test per un percorso Python errato; Sol ha corretto un caso e verificato il perimetro, 143 test passati prima dell'ulteriore caso allowlist |
| Luna 6 | `pass2u_fake_luna`: fake e factory Pass2U | medium | Concluso: 8 test passati; Sol ha integrato e verificato il perimetro provider, 82 test passati |
| Luna 6 | `build_fixture_luna`: server locale di risposte fixture | medium | Concluso: 3 test passati, riletti e rieseguiti da Sol insieme agli altri test frontend |

Totale di questa ripresa: **4 incarichi a Luna e 1 review delegata a Sol**,
oltre al lavoro del coordinatore Sol nella conversazione principale.

Sol ha implementato e integrato le parti che richiedono giudizio: matrice
ambienti, sicurezza credenziali, startup Firebase, gateway PayPal, policy mail
e Sender, collegamento degli altri provider e protezioni della build frontend.

Ogni nuova delega sarà annunciata in chat con modello, incarico e motivo;
al ritorno verranno comunicati esito, verifica e correzioni. Nessun importo o
numero di token verrà stimato a partire dal conteggio dei task.
