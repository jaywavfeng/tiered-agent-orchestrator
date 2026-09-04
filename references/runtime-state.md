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
├── OWNER_STATUS.md
├── inbox/owner/<event-id>.md
├── history/completion-<revision>/
│   ├── STATE.json
│   ├── PLAN.md
│   ├── OWNER_DIRECTIVES.md
│   ├── HANDOFF.md
│   ├── OWNER_STATUS.md (when present)
│   ├── REOPEN.json
│   ├── workers/<worker-id>/{TASK.md,STATUS.json,BLOCKER.md}
│   └── review/{TASK.md,STATUS.json,REPORT.md}
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
    ├── REPORT.md
    └── history/review-<revision>/{TASK.md,STATUS.json,REPORT.md}
```

Use `scripts/statectl.py` for deterministic initialization, registration, reopening, reassignment, validation, status changes, Owner-event resolution, and management summaries. `init` publishes a complete runtime without overwriting an initialized one. `reopen-project` archives the complete project before changing global state. Reassignment preserves the completed assignment before replacing current files. Treat the helper's implementation details as internal: do not spend Agent context auditing them unless a concrete error points there.

## Ownership

PROJECT_LEAD exclusively owns:

- `STATE.json`
- `PLAN.md`
- `OWNER_DIRECTIVES.md`
- `HANDOFF.md`
- `OWNER_STATUS.md`
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

Completed project state is frozen. Only `reopen-project` may return it to `planning/active`; routine status setters, Workers, Reviewers, and feedback-event writers cannot mutate it. Read-only Owner requests require no runtime write.

`OWNER_STATUS.md` is Lead-owned presentation, not machine authority. Worker and Reviewer files never update it. Existing schema-v1 runtimes that predate the file remain valid; the Lead creates it at the next meaningful transition instead of running a migration framework.

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

## Canonical responsibilities and cold-start takeover

Keep each fact in one canonical place:

- `STATE.json` owns compact lifecycle and routing facts: phase, status, milestone, role paths, review requirement, timestamp, and next actor.
- `PLAN.md` owns the stable final goal, completion criteria, durable architecture decisions and constraints, milestones, work allocation, and validation strategy.
- `OWNER_DIRECTIVES.md` owns current authoritative Owner direction and unresolved choices. It is not a conversation transcript.
- Worker and Reviewer status/blocker/report files own scoped execution results, evidence, failures, and next actions.
- `HANDOFF.md` is the current Lead cold-start packet. It summarizes the final goal, completed work, current position, active roles, verified results, important decisions/constraints, blockers/risks, next action, and Owner decision requirement. It points to canonical detail rather than duplicating it.
- `OWNER_STATUS.md` is a short, plain-language management report for the Owner: purpose, major completed outcomes, current phase, results, risks/failures, work in progress, next steps, and decisions needed. It contains no command log or low-level file list.

For `$tao continue lead` with no chat history, read in this order:

1. `STATE.json` and `HANDOFF.md`;
2. `OWNER_DIRECTIVES.md` and the relevant stable sections of `PLAN.md`;
3. current Worker/Reviewer status and any active blocker;
4. pending Owner events.

This set must answer the takeover questions without chat history. Read code, diffs, completion history, or old assignment archives only when the current packet identifies a discrepancy or missing decision.

Update the canonical source first, then refresh `HANDOFF.md`. Refresh `OWNER_STATUS.md` only when a milestone, blocker, material result/risk, completion, reopen, next-step change, or Owner decision changes the human-visible picture. Neither summary is an append-only log.

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

`inactive` does not mean successfully completed and never satisfies a Worker dependency. It may be excluded from final work only when PROJECT_LEAD has deliberately abandoned or superseded that assignment.

## Assignment history

`TASK.md`, `STATUS.json`, and `BLOCKER.md` describe the current assignment. Before reuse, `reassign-worker` copies the completed assignment into `history/assignment-NNNN/` and then writes the next assignment in place. This keeps the stable Worker path and conversation while preserving old objectives, scopes, results, verification, and blocker evidence without expanding `STATE.json`.

The Worker always rereads current repository state when continued. Chat memory may help execution, but it never selects the active assignment or overrides the latest `TASK.md`.

## Completion history and reopen

`reopen-project` is PROJECT_LEAD-only and accepts an actionable Owner reason plus a new milestone. It copies global state, plan/directives/handoff, all current Worker task/status/blocker files, and the current review task/status/report into `history/completion-NNNN/`. Only after the snapshot directory is atomically published does it set the live project to `planning/active` and clear the old review requirement. The current completed Worker remains unchanged until the Lead uses `reassign-worker`, preserving both the stable Worker identity and assignment evidence.

If a reopen is interrupted, rerun the same command or inspect the reported files. A project is complete only when every non-inactive Worker is completed and any required review is completed and current. Do not proactively design or audit additional recovery layers without evidence that this failure mode is occurring.

## Review history and invalidation

When execution resumes after a completed review, the global reviewer assignment is detached while the review requirement remains. An unfinished review cannot transition back to execution, and `add-worker` is forbidden while the project is in review. This makes the old approval stale without destroying its files. The next `assign-review` archives that completed evidence under `review/history/review-NNNN/` before publishing the replacement assignment. Completion cannot use the detached review.

`assign-review --level strong` requires `--strong-justification`, which is preserved in `review/TASK.md`. This prevents a routine review from silently consuming the strong tier.

Existing helper releases may contain internal recovery artifacts for interrupted multi-file updates. Agents should neither inspect nor extend them during normal work. A reported validation failure is the trigger for targeted inspection; theoretical crash timing is not.

## Dispatch handoff

When the host supports native subagents, a dispatch is valid only when the caller explicitly supplies the configured model/reasoning, the host returns machine-readable actual/effective values for both, those values match, and the runtime is registered as the intended Worker or Reviewer. Acceptance, echoed arguments, a success flag, or a nickname is not evidence. Missing, rejected, ignored, or contradictory routing fails closed before substantive work. The child does not recursively self-verify a native route; the Lead checks the host receipt.

An Owner-created top-level runtime is different: only a clearly visible model family is checked, and manual reasoning is never validated or gated. If the model indicator is unavailable to the Agent, it continues the existing assignment without a selector check, command resend, new runtime, or recursive proof. A clear model-family mismatch gets one concise correction for the same conversation and leaves the formal Worker/Reviewer intact. Billing attribution remains unproven without host per-model/per-conversation telemetry or a documented manual measurement.

After dispatch, no high-frequency status polling loop is part of the runtime protocol. The Lead may passively wait for an event that advances the Worker, but a timeout is not a milestone and must not trigger a timeout → re-analysis → status-check loop. One unchanged timeout ends that wait. A manual Worker is resumed by returning to its original conversation with `$tao continue worker-N`.

## Owner feedback events

For high-level or ambiguous feedback during active work, store the exact Owner message in a new uniquely named Markdown file. Do not paraphrase it into a decision. The Project Lead later interprets it, writes the resulting constraint to `OWNER_DIRECTIVES.md`, and uses `resolve-owner-feedback`. Only YAML frontmatter determines event status; verbatim Owner text cannot forge a pending event.

For a completed project, PROJECT_LEAD classifies the current Owner request directly: answer read-only requests without mutation, or pass actionable wording to `reopen-project`, where it is preserved in `REOPEN.json`. Do not create a pending Worker-owned event inside frozen completed state.

## Checkpoints

Persist state on recoverable transitions, not after every command:

- assignment ready;
- completed assignment archived and Worker reassigned;
- completed project snapshotted and reopened;
- meaningful milestone reached;
- validation result changes;
- blocker or Owner decision becomes active;
- review begins or ends;
- work completes.

## Sufficient reliability

> **Prefer the simplest mechanism that is sufficiently reliable for the actual failure modes of the project.**

The default is simple files, atomic replacement for individual machine-written state, basic schema/reference/ownership validation, and recovery by rereading the repository.

Do not add checksum trees, content hashes, freshness markers, secondary transaction protocols, periodic audits, or recovery-of-recovery logic without a concrete, high-impact failure and evidence that the added protection is worth its code, tests, context, and token cost. Human summaries are deliberately not parsed or gated by `statectl`; their quality is a Project Lead responsibility at meaningful transitions.
