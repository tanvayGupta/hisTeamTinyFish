# Agent Instructions

## Before Working

1. Read `CURRENT_STATE.md`.
2. Read `implementation_plan.md` only for the current task's requirements.
3. Inspect relevant files and Git status; do not scan the entire repository without a reason.

## Development

- Execute only the requested phase or milestone.
- Follow existing architecture and shared contracts.
- Prefer the simplest working implementation.
- Avoid unnecessary dependencies, abstractions, LLM calls, and unrelated refactoring.
- Verify actual TinyFish API behavior; never fabricate results.
- Never expose credentials or overwrite unrelated work.
- Do not duplicate work already completed and verified.

## Git

- Work only on the assigned branch/worktree.
- Make focused commits at milestone boundaries.
- Never push unless explicitly requested.
- Do not discard existing changes.

## Handoff

At the end of each milestone:

1. Update `CURRENT_STATE.md` with verified progress, tests, blockers, and the next action.
2. Keep it concise and factual.
3. Report changed files, test results, and commit hash.
4. Do not claim success without verification.

Do not create `TASK_LOG.md` unless explicitly requested.
