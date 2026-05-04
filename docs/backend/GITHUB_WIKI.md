# GitHub Wiki Sync

La documentazione resta in `docs/` come fonte di verita.

Per pubblicarla nella GitHub Wiki usiamo:

```bash
scripts/wiki/sync_docs_to_wiki.sh
```

Questo clona o aggiorna la wiki locale in:

```text
runtime-data/github-wiki
```

e genera pagine Markdown a partire da `docs/`.

## Pubblicazione

Prima genera localmente:

```bash
scripts/wiki/sync_docs_to_wiki.sh
```

Poi, se il risultato va bene:

```bash
scripts/wiki/sync_docs_to_wiki.sh --push=true
```

## Repository Wiki

GitHub Wiki usa un repository separato:

```text
https://github.com/Vittorix99/mcp-website.wiki.git
```

Lo script lo deriva automaticamente da `origin`.

Per override manuale:

```bash
scripts/wiki/sync_docs_to_wiki.sh --wiki-repo=https://github.com/OWNER/REPO.wiki.git
```

## Sicurezza

Lo script elimina solo pagine che contengono il marker:

```text
AUTO-GENERATED-FROM-DOCS
```

Quindi eventuali pagine manuali nella wiki non vengono cancellate.
