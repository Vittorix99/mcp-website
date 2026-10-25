# Project Documentation

Documentazione first-party del progetto, centralizzata per evitare file sparsi nella codebase.

## Process

- [Development Methodology](./process/DEVELOPMENT_METHODOLOGY.md)
- [Registro incarichi Sol/Luna](./process/MODEL_USAGE_LOG.md)
- [WS1 Environment and Provider Safety Design](./superpowers/specs/2026-10-24-ws1-environment-provider-safety-design.md)
- [Core WS1 Implementation Plan](./superpowers/plans/2026-10-25-core-ws1-environment-provider-safety.md)
- [GitHub Actions: guida operativa](./process/GITHUB_ACTIONS_GUIDE.md)
- [Modello workflow staging inattivo](./operations/workflow-templates/staging.yml)
- [Modello workflow production inattivo](./operations/workflow-templates/production.yml)

## Operations

Core WS1 è implementato e verificato localmente; i tre rilievi della review indipendente sono corretti. Integrazione e attivazione cloud restano soggette ai rispettivi gate.

- [Catalogo ambienti e risorse](./operations/ENVIRONMENT_RESOURCE_CATALOG.md)
- [Transizione credenziali ADC/WIF](./operations/CREDENTIAL_TRANSITION.md)
- [Segreti nella cronologia: decisione aperta](./operations/SECURITY_HISTORY_REMEDIATION.md)

## Backend

- [Backend Docs](./backend/BACKEND_DOCS.md)
- [Doppler Secrets](./backend/DOPPLER_SECRETS.md)
- [GitHub Wiki Sync](./backend/GITHUB_WIKI.md)
- [Template Rendering](./backend/TEMPLATE_RENDERING.md)
- [Backend Use Cases](./backend/BACKEND_USE_CASES.md)
- [Entities](./backend/ENTITIES.md)
- [Database Bug Fix Scripts](./backend/scripts/database_bug_fix/README.md)
- [Event Payment Integration Tests](./backend/tests/integration/event_payment/README.md)

## Features

- [Entrance Scanner](./features/ENTRANCE_SCANNER.md)
- [MailerSend](./features/MailerSend.md)

## Roadmap

- [MCP Website Agile Roadmap v2](./roadmap/MCP%20Website%20Agile%20Roadmap%20v2.docx.md)

## Core WS1 verification

- [Verifica locale e limiti operativi](./reviews/WS1_CORE_VERIFICATION.md)
- [Review indipendente e correzioni](./reviews/WS1_CORE_REVIEW.md)
