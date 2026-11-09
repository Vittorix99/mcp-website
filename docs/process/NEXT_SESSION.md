# Passaggio di consegne — 9 novembre 2026

- Worktree: `/Users/vittoriodigiorgio/Desktop/Projects/MCP-WEB-PROJECT/.worktrees/core-ws2`.
- Branch corrente: `chore/reduce-agent-overhead`, basato su `19ff14a`.
  Contiene le regole di risparmio e questo handoff; commit locale, non pubblicato.
- Main verificato: `2a4fb1d`, merge PR #8. PR #9 (`d3c7dc7`, sconti) e
  PR #10 (`19ff14a`, limiti sconti) risultavano aperte all'ultima verifica.
  #10 ha base `core-discount-api-scenarios`: integrare prima #9, poi
  verificare/aggiornare la base di #10 a main. Nessun merge autorizzato all'agente.
- Ultima prova: 64 casi API Firestore emulator passati nel JUnit locale,
  inclusi 13 nuovi limiti; 27 unit test collegati passati; review Sol high
  senza rilievi. CI #10 verde:
  https://github.com/Vittorix99/mcp-website/actions/runs/42693126184
- Nessuna modifica applicativa nei blocchi recenti. PayPal e admin simulati;
  zero totale è una caratterizzazione fake, non una garanzia del provider reale.
- Prossimo perimetro proposto, da discutere prima di implementare:
  PAY-12 capture concorrenti dello stesso ordine e DIS-06 ultimo utilizzo
  sconto concorrente. Verificare duplicati e stati parziali con prove
  controllate; riportare eventuali bug prima di correggere il codice applicativo.
- Evidenze e matrice: `docs/superpowers/plans/2026-11-04-staging-synthetic-data.md`;
  leggere solo le sezioni necessarie. Deleghe: `docs/process/MODEL_USAGE_LOG.md`.
- Leggere `AGENTS.md`: blocchi coerenti, una review finale per blocco,
  CI ordinaria monitorata dal proprietario, comandi del walkthrough uno alla volta.
- Rimossa la preferenza globale `service_tier = "priority"`; backup locale
  `~/.codex/config.toml.before-standard-20261109.bak`. Controllare Standard
  nel selettore della nuova chat: nessuna prova della velocità effettiva corrente.
- Nessun deploy, reset/seed cloud o operazione su credenziali autorizzato.
