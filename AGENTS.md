# Project model routing

## Models and responsibilities

- Use `gpt-6.1-sol` as the primary coordinator for reasoning, architecture,
  planning, root-cause analysis, ambiguous implementation, and code review.
- Delegate small, bounded, mechanical implementation tasks to `gpt-6-luna`.
  Examples include repetitive edits, straightforward mappings, boilerplate,
  and implementing a fully specified helper or test fixture.
- Writing code alone does not make a task simple. Payment state changes,
  authentication, authorization, secrets, concurrency, migrations, and
  unclear contracts belong to Sol even when the diff is small.
- Do not select other models without an explicit user request.

## Delegation contract

- Before every delegation, announce `[Luna]` or `[Sol]`, the bounded task,
  selected reasoning effort, and why that model fits. When it returns, announce
  the result and whether Sol accepted, corrected, or escalated the work.
- Keep `docs/process/MODEL_USAGE_LOG.md` updated with actual dispatches,
  status, and verification. Report task counts as task counts, never as token
  or cost measurements. Token/cost fields stay unavailable unless supplied by
  the host's actual usage telemetry.

- The user authorizes this routing and small-task delegation for project work.
- Give Luna a fresh context (`fork_turns: "none"`), explicit file ownership,
  the required behavior, constraints, and an appropriate verification command.
- Set `model: "gpt-6-luna"` and `reasoning_effort: "low"` for mechanical work;
  use `medium` when bounded implementation requires modest reasoning.
- Sol reviews the resulting diff and verification evidence before accepting it.
- If a Luna task reveals ambiguity, unexpected failures, or wider changes,
  return it to Sol. Do not repeatedly retry an unsuitable task on Luna.
- Batch related small edits when delegation overhead would exceed the work.
  Keep dependent steps sequential and avoid concurrent edits to the same files.
- Use `gpt-6.1-sol` with `reasoning_effort: "high"` for independent review.
  This explicit project choice takes precedence over skill defaults that
  recommend a different or more expensive reviewer model.

## Owner-operated external checks

- Owner update 2026-11-11: the agent runs local verification commands, including
  emulator tests, directly from now on. This supersedes the initial walkthrough
  rule below for local commands; cloud and real-provider gates remain in effect.

- During initial learning walkthroughs, let the owner run development, test,
  and build commands manually, one activity at a time. Explain the purpose and
  expected result, then wait for their reported outcome before the next step.
- Before starting any workstream after WS1, stop and notify the owner so they
  can discuss their considerations. Do not automatically begin the next WS.

- To reduce model usage, hand straightforward dashboard checks and account
  administration to the owner instead of navigating external UIs by default.
- Give concise instructions, the exact resource to inspect, and the non-secret
  result needed. Never ask the owner to paste tokens, private keys, or secrets.
- Continue independent code work while awaiting results when approval gates
  allow it. Record owner-reported results as such, not independently verified.
- Retain Sol for security analysis and Luna for bounded implementation. This
  preference does not authorize credential revocation or other cloud mutations.

## Scope

This is an agent workflow policy, not an application runtime router. Model
selection for the primary conversation is controlled by the host application;
an agent must not claim that this file switches the active conversation model.
The project approval gates and authorized work remain in effect.

## Lean development workflow

Owner-approved rules. These override conflicting process-document and skill
workflow defaults; explicit user permissions and production gates still apply.

- Small, bounded, reversible tasks: implement directly, run focused checks,
  and commit. No separate design, plan, report, or repeated approval.
- Large workstreams: one concise plan, one approval, one final review.
- Delegate to Luna for substantial bounded batches; handle tiny edits inline.
- Run relevant tests locally and the full suite in CI. Risky or cross-cutting
  changes require broader local verification before delivery.
- Read only necessary file ranges and log summaries. Reuse still-valid evidence;
  reread or retest when changes invalidate it.
- Update existing documentation rather than creating duplicate reports.
- Keep replies and progress updates concise; avoid repeated recaps.
- Security, authentication, payments, credentials, and migrations retain
  rigorous validation, error handling, review, and applicable approval gates.

## Usage-conscious execution

Owner-approved on 2026-11-09. These rules refine the lean workflow above.

- Group related scenarios into one coherent approved block. Use one final Sol
  high review for that block, rather than separate reviews for small case batches.
  Tiny documentation or mechanical edits do not need a delegated review.
- Default CI monitoring belongs to the owner: provide the run/PR link and ask
  only for the final result or failed step. Do not poll CI repeatedly unless
  the owner explicitly asks for live monitoring. Never report pending CI as passed.
- At a completed checkpoint, prefer a fresh chat with a handoff of at most
  300 words: worktree/branch, commits/PR dependencies, evidence and next scope.
  Do not copy the conversation or reread the complete repository/history.
- Read relevant file ranges and concise tool results. Reuse valid evidence and
  previously read skill instructions; avoid repeated broad scans and recaps.
- Prefer Standard speed; Fast requires an explicit owner choice. A project
  policy cannot switch the host's active model, speed or reasoning setting.
- Keep all existing payment, security, review, test and approval safeguards.
  Report savings only from measured telemetry, never from task counts.
