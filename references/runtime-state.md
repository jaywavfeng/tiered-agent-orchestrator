# Runtime State Contract

Read once before modifying runtime state. Workers normally use their role's `context` output instead of loading this entire reference on every continuation. All helper invocations use an explicit Python interpreter as shown in [SKILL.md](../SKILL.md).

## Ownership and canonical facts

| File | Writer | Purpose |
|---|---|---|
| `STATE.json` | Lead | Schema-v1 lifecycle, profile, role registry, scope/dependencies, next actor |
| `PLAN.md` | Lead | Stable goal, criteria, constraints, milestones and validation strategy |
| `OWNER_DIRECTIVES.md` | Lead | Authoritative Owner decisions and unresolved choices, no transcript |
| `HANDOFF.md` | Lead | Compact current cold-start packet with links to evidence |
| `OWNER_STATUS.md` | Lead | Human report, never machine authority |
| `TRANSPORT.json` (optional) | Lead | Host task bindings and current dispatch receipt; no lifecycle authority |
| `workers/worker-N/TASK.md` | Lead | Current bounded assignment with revision |
| `workers/worker-N/STATUS.json`, `BLOCKER.md` | That Worker | Result, validation, blocker and next action |
| `inbox/owner/<event-id>.md` | Originating Worker; Lead resolves | Verbatim directional/ambiguous feedback |
| `review/TASK.md` | Lead | Review criteria and justified level |
| `review/STATUS.json`, `REPORT.md` | Assigned Reviewer | Scoped review decision and evidence |

Workers own only their assigned code scope and listed files. No Worker writes global state, another Worker's files or transport configuration. The Lead's sole normal write to Worker status is `reassign-worker` after completion. It archives the old assignment then resets status. Scopes and dependencies remain enforced; `inactive` does not satisfy a dependency.

Machine state excludes logs, secrets, concrete model names and large summaries. Routing/receipt details belong in optional transport, whose records do not prove billed usage. Old schema-v1 projects without transport or an Owner report remain usable; no migration is needed.

## Transitions and history

Worker states: `ready`, `active`, `blocked`, `waiting-owner`, `completed`, `inactive`. `completed → ready` is only a Lead reassignment. Relay-driven status writes pass the current `--assignment-revision` to reject stale messages. A blocked Worker resumes only after a real resolution; do not resend a blocked task merely to see if it now works.

`reassign-worker` archives task, status and blocker under `workers/worker-N/history/assignment-NNNN/`. Current assignment files alone select the work; a milestone never creates a new role. Existing tasks without a revision heading are revision 1.

`reopen-project` archives completed global and role state in `history/completion-NNNN/` before returning to `planning/active`. Read-only questions leave completed state frozen. A completed Worker remains intact until reassigned.

Review assignment archives completed review evidence in `review/history/review-NNNN/`. Resuming implementation detaches an old review while preserving the review requirement; stale approval cannot satisfy completion. Strong review requires `--strong-justification`. Completion rejects unfinished non-inactive Workers, pending Owner feedback or unfinished/stale required review.

## Read and update cheaply

For `$tao continue lead`, `context --role lead` returns current status, handoff and pointers to directives/plan/events. These identify final goal, completed work, current position, verified results, constraints, blockers, next action and Owner decision without chat history. Read only relevant plan sections and active blocker files; do not scan archives by default.

`context --role worker-N` returns current task/status, direct dependency statuses and an active blocker. `context --role reviewer-N` requires a current review assignment. All packets include absolute executable/script arguments. They are transient output, not another stored summary database.

`status` and ordinary updates validate current schema, paths, scope/dependencies and lifecycle invariants without inspecting historical contents. `validate` explicitly checks full history and transport bindings. Archiving operations check their affected history. `status`, `context`, dispatch/notification context and `validate` never mutate or recover files. If an interrupted update marker exists, they report it; explicitly run the `recover` subcommand through Python to invoke existing recovery. Conflicting newer content remains protected.

Persist meaningful assignment, validation, blocker, review, completion or direction transitions, never each command. `HANDOFF.md` compresses current facts; the plain-language management report in `OWNER_STATUS.md` changes only when the human-visible picture changes. Neither summary duplicates logs or overrides state.

## Messages and evidence

[Host dispatch](host-dispatch.md) owns the transport workflow and receipt format. Messages only wake a role to read canonical state. Owner-created threads use the model-only gate when visible and continue when unavailable; manual reasoning is not gated. Native automation needs machine-readable actual/effective values for model and reasoning. Acceptance is not attestation, contradictory metadata blocks execution, and children never recursively self-prove their route. Neither route establishes billing without telemetry.

Owner-event frontmatter controls pending/resolved status; verbatim message text cannot forge an event state. For ambiguous feedback, store exact words, pause conflicting work, and notify the Lead once. Read-only requests on completed projects do not create events.

> **Prefer the simplest mechanism that is sufficiently reliable for the actual failure modes of the project.**

The <= 10% coordination token target does not justify another audit system. Use simple state, existing atomic replacement and targeted recovery after a concrete error. A timeout is not a milestone; use passive event waits without repeated analysis.
