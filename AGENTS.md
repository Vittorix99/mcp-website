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

## Scope

This is an agent workflow policy, not an application runtime router. Model
selection for the primary conversation is controlled by the host application;
an agent must not claim that this file switches the active conversation model.
The project approval gates and authorized work remain in effect.
