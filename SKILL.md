---
name: tao
description: Orchestrate large, multi-stage, or long-running engineering work with a persistent strong Project Lead, reusable economy Workers, optional review, and repository-backed handoffs. Activate only for an explicit $tao command; existing state or work on TAO itself never activates it implicitly. Do not start the full workflow for simple, local, low-risk edits that one agent can finish directly.
license: Apache-2.0
metadata:
  author: "jaywavfeng"
  version: "0.4.0"
---

# Tiered Agent Orchestrator

> **Use the cheapest model that is likely to complete the task correctly without costly rework.**

Use expensive intelligence only where expensive intelligence is needed. Optimize for completion-value efficiency: correct completion first, then lower strong-model/Sol usage, then lower credits/cost, then less unnecessary context and model switching, and only lastly fewer total tokens. A run is successful when strong-model usage falls without trading away correctness; spending more economy-model tokens is appropriate when it prevents rework.

- PROJECT_LEAD makes decisions and distills intent.
- WORKER is a reusable, long-lived execution conversation that performs successive bounded assignments.
- REVIEWER checks completed work when the expected quality gain justifies another model switch.
- The repository carries operational state; chat history is never a handoff dependency.

The model tier is a hard constraint. PROJECT_LEAD uses the configured strong model only for ambiguity, architecture, major decisions, difficult blockers, and final acceptance. WORKER uses the configured economy model with the profile's highest practical reasoning effort for nearly all execution; do not under-reason ordinary work merely to lower one run's cost. See the OpenAI profile for exact model and reasoning labels.

## Route the request

Apply this activation gate before reading runtime state: the current Owner request must explicitly invoke `$tao`. The existence of `.tiered-agent`, a previous invocation, the repository name, or a request to develop/test/release TAO itself is never implicit activation. Without an explicit `$tao`, handle the request normally and do not enter any TAO role.

After explicit activation, locate the repository root and check for `.tiered-agent/STATE.json`.

1. If state exists, treat the request as a continuation. Do not run the new-project complexity gate. If it is `complete/complete`, first classify the current request using the completed-project gate below.
2. If the user names `continue worker-N`, use the Worker workflow.
3. If the user names `continue reviewer-N`, use the Reviewer workflow.
4. If the user asks for status, mentions a blocker, says `continue lead`, naturally says `continue` in the original Lead conversation, or returns with high-level feedback, use the Project Lead resynchronization workflow.
5. Otherwise apply the complexity gate.

### Completed-project gate

Completed state is frozen, not terminal forever.

- For a question, status request, summary, explanation, retrospective, or other request that requires no repository change, answer from existing evidence and leave the project complete. Do not create an Owner event merely for a read-only request.
- For an actionable correction, modification, added requirement, or optimization, PROJECT_LEAD runs `statectl.py reopen-project` with the Owner's reason and a new milestone. The command archives the complete project snapshot before returning it to `planning/active`. Then reuse a suitable completed Worker with `reassign-worker`; do not initialize a new project or add a Worker merely because the project reopened.
- If intent is genuinely ambiguous, ask one concise question while leaving the project complete. Reopen only after actionable work is clear.

## Complexity gate

Handle the task directly without creating orchestration state when it is bounded, low-risk, locally clear, and likely to finish in one focused session without a durable handoff. Examples include a typo, a small configuration edit, or a straightforward isolated fix.

Initialize the full workflow when at least one is true:

- the task combines architecture, implementation, environment work, and validation;
- it is long-running, multi-stage, cross-module, or likely to need checkpoints;
- separating decisions from mechanical execution will materially reduce strong-model work;
- the user explicitly requests tiered orchestration.

If the gate rejects orchestration, state that briefly and complete the task normally. Do not create `.tiered-agent`.

## Project Lead workflow

Read [the orchestration protocol](references/orchestration-protocol.md) and [runtime state contract](references/runtime-state.md). Read [escalation and review](references/escalation-and-review.md) only when handling feedback, a blocker, or review.

For a new project:

1. Inspect only the repository entrypoints, instructions, and validation evidence needed for a decision. Do not broadly scan the repository.
2. Resolve only uncertainties that materially change the goal or architecture.
3. Initialize runtime state with `python scripts/statectl.py init --project-root <repo> --project-id <slug>`. If executing from an installed copy, use the absolute path to this skill's script.
4. Write the distilled goal, current state, decisions, constraints, milestones, validation, and completion criteria to `PLAN.md`. Never record private chain-of-thought.
5. Analyze the dependency graph. Default to one reusable Worker conversation for sequential milestones.
6. Register the first Worker with `statectl.py add-worker`. Add another only when work is genuinely parallel, responsibilities or context differ materially, reuse would cause clear context pollution, or the existing Worker is inactive—and only when the benefit exceeds the extra conversation and token cost. Never add a Worker merely because the milestone changed.
7. Before dispatch, apply the model-routing and host-capability rules below. Update global state only at meaningful transitions.

### Hard model-routing and dispatch rules

- If the host can natively spawn a TAO Worker with an explicit model, PROJECT_LEAD **MUST** pass the configured economy model and `xhigh` reasoning. The `model` parameter **MUST NOT** be omitted, and the spawned agent **MUST** map to one formal `worker-N` assignment.
- After native dispatch, PROJECT_LEAD **MUST** verify the actual/effective route from the structured host receipt or stronger effective-model metadata. Successful acceptance of explicit `model` and reasoning fields by a host whose tool contract guarantees those overrides is evidence; if the host rejects/ignores the fields or returns contradictory effective metadata, stop the Worker and fail closed. A free-form nickname is not evidence. The Worker must not recursively self-verify a route already guaranteed by the host receipt.
- If the host cannot reliably set an economy model explicitly, PROJECT_LEAD **MUST NOT** spawn a Worker. Stop the turn and tell the Owner to create a top-level economy Worker manually using the profile's model/reasoning and `$tao continue worker-N`. In that manual conversation, the host's current-conversation model/reasoning selector is the evidence. Never demand another manual Worker as a second proof. If the selector shows the correct model but lower reasoning, ask the Owner to change the same conversation to the required setting and continue it.
- A native subagent is only a Worker runtime; it remains bound by `TASK.md`, scope, status, dependencies, ownership, and the single-writer protocol. The host's multi-agent capability never justifies fan-out.
- After dispatching a Worker, **MUST NOT** continuously poll `STATUS.json`, repeatedly timeout and re-analyze, duplicate the assignment, or perform the Worker's execution. A timeout is not a milestone. The Lead may use passive/event wait for automatic progress, then resume on a completion, blocker, milestone, or Owner event. For a manually opened Worker, end the Lead turn and wait for the Owner to return with `continue`.

Before every action, ask whether it needs strong reasoning. If not, delegate it to the current Worker. PROJECT_LEAD **MUST NOT** perform routine repository scans, SSH/GPU/disk/environment checks (including `nvidia-smi`), dependency installation, training, tests, implementation, debugging, video/data processing, chart generation, deployment, or repeated shell commands. Only the smallest read-only check required for an architecture decision is allowed.

For resynchronization:

1. Read `STATE.json`, active Worker status summaries, pending Owner inbox events, relevant blockers, and `HANDOFF.md`.
2. Inspect diffs or code only where status and evidence require it.
3. Interpret new Owner intent and update `OWNER_DIRECTIVES.md` and `PLAN.md` when decisions changed. For actionable feedback on a completed project, use the PROJECT_LEAD-only `reopen-project` first. When a completed Worker is suitable for the next assignment, use `reassign-worker` to archive its prior assignment, rewrite its task contract, and return it to `ready` instead of creating a new Worker ID.
4. Report progress concisely. The Owner must not summarize Worker history. Do not poll for progress after dispatch; resume only on an event or Owner return.

## Worker workflow

Read only [the runtime state contract](references/runtime-state.md), the named Worker's `TASK.md` and `STATUS.json`, relevant Owner directives, explicitly referenced plan sections, and the code dependencies named in the task.

A Worker ID identifies a long-lived role and conversation, not a single task. Always reread the current `TASK.md`; the Lead may have safely reassigned the same Worker after an earlier assignment completed. Repository state, not remembered chat, defines the current assignment.

Before editing, verify:

- the Worker ID exists and the task status is ready, active, blocked, or waiting-owner;
- the requested changes fit `allowed_scope` and avoid `do_not_modify`;
- dependency Workers are complete when required.

For a manually opened Worker, use the host's exact current-conversation indicator. In the OpenAI profile, `极高` maps to `xhigh` and `高` maps to `high`; never infer or downgrade an unread value. A verified `Luna / 极高` manual Worker passes. If the value is unavailable, report it as unknown rather than inventing `high`, and ask the Owner to check the same conversation's selector—never recursively request another Worker.

Then work independently through implementation and validation. Update only the Worker's status, its allowed code scope, its blocker file, and uniquely named Owner inbox events. Do not edit global state, the plan, other assignments, or other Worker status files.

When the assignment is done, set the status to `completed` and return control to the Lead. Do not create or request a new Worker for the next milestone. The Lead may archive this assignment and reset the same Worker to `ready`; the Owner then continues the original Worker conversation with `$tao continue worker-N`.

If a native runtime exits or the process crashes, repository status remains authoritative. Resume the same formal Worker and current assignment from `ready`, `active`, `blocked`, or `waiting-owner`; do not add a Worker or let PROJECT_LEAD duplicate its execution. `statectl.py` automatically resumes interrupted reassignment and review-assignment transactions and refuses to overwrite newer conflicting files.

Apply clear local Owner corrections directly when scope and intent are unambiguous. For ambiguous, directional, or architecture-changing feedback, preserve the Owner's exact words with `statectl.py record-owner-feedback`, pause conflicting work, and direct the Owner back to the original Project Lead conversation.

When blocked, follow [escalation and review](references/escalation-and-review.md). Stop the same failure path when it repeats instead of retrying it with Luna without new evidence; escalate the capability gap to the first lower-cost escalation tier before considering the strong tier.

## Reviewer workflow

Proceed only when `STATE.json` requests review and `review/TASK.md` names the reviewer. Read the review task, relevant diff, completion criteria, and validation evidence. Do not broaden implementation scope.

Write findings and evidence to `review/REPORT.md` and update `review/STATUS.json`. Approve, request bounded fixes, or escalate a decision to PROJECT_LEAD. Never invent release approval when validation is incomplete.

## Status workflow

Run `python scripts/statectl.py status --project-root <repo>` or read the same minimal files manually. Report:

- each Worker state and current result;
- review state;
- active blockers and pending Owner feedback;
- current risk and next actor;
- whether an Owner decision is required.

Do not scan the whole repository for a routine status request unless the persisted evidence conflicts.

## Profiles

The protocol uses only `strong`, `balanced`, and `economy`. Read exactly one profile when recommending a conversation model:

- [OpenAI Codex profile](profiles/openai-codex.md)
- [Generic profile](profiles/generic.md)

Profiles are recommendations, not authorization to switch models or create conversations automatically. If the current model differs from a recommendation, give one short correction and preserve state.

## Safety

Never let orchestration bypass host approvals or user control. Do not automatically push Git, force-push, delete important data, expose secrets, change global agent configuration, or deploy production systems. A task assignment grants write scope, not new external authority.
