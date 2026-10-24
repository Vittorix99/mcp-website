# MCP-WEB-PROJECT Structural Refactoring Intent

**Status:** accepted — Design authorized
**Date:** 2026-10-24
**Accepted:** 2026-10-24, explicit project-owner approval recorded in the working session

## Problem

The current Firebase/Next.js system is difficult to understand, reproduce, test, measure, and change safely. Relational and analytical workloads are increasingly awkward in Firestore, but there is not yet enough project-specific evidence to justify staying on Firebase, introducing a hybrid, or migrating to Supabase/PostgreSQL.

## Intended outcome

Create an evidence-based, staged restructuring program that first makes the current Firebase system safe and measurable, then compares the three platform alternatives neutrally, and only executes the explicitly approved architecture.

## Affected users and systems

- Customers purchasing event access or memberships.
- Members using passwordless login, tickets, event guides, and locations.
- Administrators managing events, participants, memberships, purchases, communications, analytics, entrance, and radio.
- Developers and operators working across local, staging, and production.
- Next.js, Firebase Functions, Firestore, Auth, Storage, scheduled/triggers, PayPal, MailerSend, Sender.net, Pass2U, SoundCloud, and Genderize.io.

## Goals

1. Establish a verified current-state architecture, resource, API, data, dependency, and risk inventory.
2. Make environments, credentials, providers, tests, CI/CD, and rollback safe and reproducible.
3. Freeze and test critical contracts before refactoring internal structure.
4. Measure latency, database operations, errors, image traffic, and cost before optimization.
5. Separate transport, validation, authorization, use cases, domain rules, repositories, and provider adapters.
6. Replace production-derived staging data with persistent synthetic scenarios and deterministic volumetric datasets.
7. Produce a neutral ADR comparing restructured Firebase, an explicit-boundary hybrid, and progressive Supabase/PostgreSQL.

## Non-goals

- No unrelated product features.
- No visual redesign.
- No big-bang rewrite.
- No production deployment, data deletion, or migration without explicit approval.
- No assumption that Supabase or Cloudflare is the destination.
- No production migration code before the architecture ADR is approved.

## Constraints

- Firebase remains operational through stabilization and assessment.
- Existing documentation is evidence input, not authoritative truth.
- Findings distinguish verified facts, inferences, assumptions, and recommendations.
- Secrets, tokens, payment data, and unnecessary personal data must never appear in artifacts or logs.
- Every major phase ends at a human approval gate.

## Initial evidence artifact

See `docs/architecture/CURRENT_STATE_ASSESSMENT_2026-10-24.md` and `docs/architecture/API_CONTRACT_INVENTORY_2026-10-24.md`.

## Gate decision

The product owner accepted this intent and explicitly authorized WS1 Design on 2026-10-24. This approval authorizes design work only; implementation still requires an approved WS1 specification and implementation plan.

The prioritized questions in the current-state assessment remain tracked as design inputs. Where an answer is not required to define a safe, non-destructive design, it may remain open until the relevant implementation or architecture gate.
