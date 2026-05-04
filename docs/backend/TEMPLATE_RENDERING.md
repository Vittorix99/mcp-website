# Template Rendering

I template HTML non devono stare nei service o dentro stringhe Python lunghe.

Flusso runtime:

```text
Service -> Payload DTO Pydantic -> TemplateRenderer -> Jinja2 HTML -> Mail/PDF client
```

Flusso preview:

```text
Fixture JSON -> Payload DTO Pydantic -> TemplateRenderer -> HTML locale
```

Il renderer e unico: la preview usa lo stesso `TemplateRenderer` usato dal backend.

## Struttura

```text
mcp-backend/functions/templates/
  emails/
  pdf/
  fixtures/

mcp-backend/functions/dto/templates/
mcp-backend/functions/services/templates/
```

## Preview

Renderizza tutti i template:

```bash
mcp-backend/functions/venv/bin/python scripts/preview_templates.py
```

Renderizza un solo template:

```bash
mcp-backend/functions/venv/bin/python scripts/preview_templates.py --template membership_email
```

Lista template disponibili:

```bash
mcp-backend/functions/venv/bin/python scripts/preview_templates.py --list
```

Output:

```text
runtime-data/template-previews/
```

`runtime-data/` e ignorata da Git, quindi le preview non finiscono nel repository.

## Regola

Quando aggiungi un template:

- crea il DTO Pydantic in `dto/templates/`;
- crea il file Jinja in `templates/emails/` o `templates/pdf/`;
- aggiungi una fixture senza dati sensibili in `templates/fixtures/`;
- registra il template in `scripts/preview_templates.py`.
