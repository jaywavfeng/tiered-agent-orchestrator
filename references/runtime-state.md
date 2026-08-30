# Runtime State Contract

Read this reference before creating or modifying `.tiered-agent` state.

## Runtime layout

```text
.tiered-agent/
├── STATE.json
├── PLAN.md
├── OWNER_DIRECTIVES.md
├── HANDOFF.md
├── inbox/owner/<event-id>.md
├── workers/<worker-id>/
│   ├── TASK.md
│   ├── STATUS.json
│   └── BLOCKER.md
└── review/
    ├── TASK.md
    ├── STATUS.json
    └── REPORT.md
```

Use `scripts/statectl.py` for deterministic initialization, registration, validation, status changes, and management summaries. It never overwrites an initialized runtime.

## Ownership

PROJECT_LEAD exclusively owns:

- `STATE.json`
- `PLAN.md`
- `OWNER_DIRECTIVES.md`
- `HANDOFF.md`
- Worker `TASK.md` files
- review assignment files

Each WORKER owns:

- code inside its `allowed_scope`
- its own `STATUS.json`
- its own `BLOCKER.md`
- uniquely named events it creates under `inbox/owner`

REVIEWER owns `review/STATUS.json` and `review/REPORT.md`.

Workers must not update `STATE.json`. This single-writer rule prevents concurrent global-state conflicts. The Lead reconciles Worker status into global state when it returns.

## Global state

Keep `STATE.json` small. It contains:

- schema version and project ID;
- phase, status, selected profile, and current milestone;
- a compact Worker registry with task and status paths;
- review requirement, level, and status;
- last update timestamp;
- next actor and next instruction.

It must not contain chat transcripts, chain-of-thought, command logs, secrets, concrete model names, or large summaries.

## Plan and handoff

`PLAN.md` records goal, current state, architecture decisions, constraints, milestones, Worker allocation, validation, and completion criteria. Record decisions and their consequences, not hidden reasoning.

`HANDOFF.md` records only current progress, latest verification, recent material changes, next action, and decisions that cannot be forgotten. Do not copy terminal history or duplicate the plan.

## Worker status

Keep `STATUS.json` operational and concise:

- Worker ID and status;
- one-sentence summary;
- files changed;
- verification commands and results;
- next action;
- last update timestamp.

Valid Worker statuses are `ready`, `active`, `blocked`, `waiting-owner`, `completed`, and `inactive`.

## Owner feedback events

For high-level or ambiguous feedback, store the exact Owner message in a new uniquely named Markdown file. Do not paraphrase it into a decision. The Project Lead later interprets it and writes the resulting constraint to `OWNER_DIRECTIVES.md`.

## Checkpoints

Persist state on recoverable transitions, not after every command:

- assignment ready;
- meaningful milestone reached;
- validation result changes;
- blocker or Owner decision becomes active;
- review begins or ends;
- work completes.
