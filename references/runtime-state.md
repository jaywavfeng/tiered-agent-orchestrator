# Runtime State Contract

Read this reference before creating or modifying `.tiered-agent` state.

Runtime state records assignments and evidence; it does not select models or replace host-level model routing. Model selection is a hard dispatch concern described by the orchestration protocol and the active profile.

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
│   ├── BLOCKER.md
│   └── history/assignment-<revision>/
│       ├── TASK.md
│       ├── STATUS.json
│       └── BLOCKER.md
└── review/
    ├── TASK.md
    ├── STATUS.json
    └── REPORT.md
```

Use `scripts/statectl.py` for deterministic initialization, registration, reassignment, validation, status changes, and management summaries. `init` never overwrites an initialized runtime; reassignment archives the completed assignment before replacing the current files.

## Ownership

PROJECT_LEAD exclusively owns:

- `STATE.json`
- `PLAN.md`
- `OWNER_DIRECTIVES.md`
- `HANDOFF.md`
- Worker `TASK.md` files
- Worker assignment-history archives
- review assignment files

Each WORKER owns:

- code inside its `allowed_scope`
- its own `STATUS.json`
- its own `BLOCKER.md`
- uniquely named events it creates under `inbox/owner`

REVIEWER owns `review/STATUS.json` and `review/REPORT.md`.

The Lead must keep mechanical execution out of its own turn. A Worker may perform searches, environment checks, commands, experiments, tests, routine fixes, remote operations, data processing, and result packaging within its declared scope.

Workers must not update `STATE.json`. This single-writer rule prevents concurrent global-state conflicts. The Lead reconciles Worker status into global state when it returns.

The only Lead write to current Worker-owned files is the `reassign-worker` transaction after that assignment is `completed`: it archives the old task, status, and blocker, writes the new task, clears the blocker, and resets status to `ready`. Workers cannot perform this transition themselves.

## Global state

Keep `STATE.json` small. It contains:

- schema version and project ID;
- phase, status, selected profile, and current milestone;
- a compact Worker registry with task and status paths;
- review requirement, level, and status;
- last update timestamp;
- next actor and next instruction.

It must not contain chat transcripts, chain-of-thought, command logs, secrets, concrete model names, or large summaries.

Worker registry IDs and paths remain stable across assignments. The Lead updates only the reused Worker's active write scope and Worker dependencies during reassignment; a milestone change does not append a new registry entry.

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

`completed → ready` is valid only through PROJECT_LEAD's `reassign-worker` transaction. Direct Worker status updates cannot perform it. `inactive` is terminal for that Worker identity unless a later protocol version defines an explicit Lead-owned reactivation operation.

## Assignment history

`TASK.md`, `STATUS.json`, and `BLOCKER.md` describe the current assignment. Before reuse, `reassign-worker` copies the completed assignment into `history/assignment-NNNN/` and then writes the next assignment in place. This keeps the stable Worker path and conversation while preserving old objectives, scopes, results, verification, and blocker evidence without expanding `STATE.json`.

The Worker always rereads current repository state when continued. Chat memory may help execution, but it never selects the active assignment or overrides the latest `TASK.md`.

## Dispatch handoff

When the host supports native subagents, a dispatch is valid only when the caller explicitly supplies the configured economy model and `xhigh` reasoning and registers the subagent as a formal Worker. The caller must verify the actual/effective runtime model from host evidence; a nickname or UI label is not proof. If the effective model is unconfirmed, omitted, unreliable, or contradictory, it is unsafe because it may inherit the Lead's strong model; in that case the Lead must stop the Worker and ask the Owner to create the economy Worker conversation manually. Native subagents remain subject to this state contract.

After dispatch, no high-frequency status polling loop is part of the runtime protocol. The Lead may passively wait for an event that advances the Worker, but a timeout is not a milestone and must not trigger a timeout → re-analysis → status-check loop. A manual Worker is resumed by returning to its original conversation with `$tao continue worker-N`.

## Owner feedback events

For high-level or ambiguous feedback, store the exact Owner message in a new uniquely named Markdown file. Do not paraphrase it into a decision. The Project Lead later interprets it and writes the resulting constraint to `OWNER_DIRECTIVES.md`.

## Checkpoints

Persist state on recoverable transitions, not after every command:

- assignment ready;
- completed assignment archived and Worker reassigned;
- meaningful milestone reached;
- validation result changes;
- blocker or Owner decision becomes active;
- review begins or ends;
- work completes.
