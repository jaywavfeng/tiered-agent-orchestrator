# Orchestration Protocol

Read this reference when acting as PROJECT_LEAD or when deciding Worker count and ownership.

## Explicit activation

TAO runs only when the current Owner request explicitly invokes `$tao`. Existing `.tiered-agent` state, a prior TAO run, repository naming, or maintenance of TAO's own source does not activate the protocol. Without an explicit invocation, do not inspect or mutate orchestration state.

## Cost-first model policy

> **Use the cheapest model that is likely to complete the task correctly without costly rework.**

Optimize for completion-value efficiency, not the lowest single-run cost. Correct completion is the first priority. The next priorities are reducing strong-model usage, reducing credits and cost, avoiding unnecessary context loading and model switches, and only then reducing total token count. Economy execution may use more reasoning tokens when that materially reduces rework, escalations, or credits.

Model tiers are hard routing constraints, not suggestions. PROJECT_LEAD reserves the strong tier for ambiguous intent, architecture, decomposition, major decisions, difficult blockers, and final acceptance. WORKER handles routine execution on the economy tier at the configured highest practical reasoning effort; do not reduce reasoning merely to shave a small per-run cost. REVIEWER defaults to balanced or another tier below strong; strong review is reserved for genuine high-risk architecture, algorithm, security, or integration decisions. Exact host mappings live in the selected profile.

## Roles

### OWNER

The Owner expresses goals, gives feedback, makes product decisions, and authorizes consequential external actions. The Owner speaks naturally and is never the message bus between agents.

### PROJECT_LEAD

The Project Lead is the long-lived management conversation. It interprets ambiguous intent, makes architecture decisions, distills a plan, assigns work, handles blockers, coordinates ownership, and decides whether review is worth its cost. It **MUST** ask whether an action needs strong reasoning before doing it and delegate routine work to the current Worker.

PROJECT_LEAD **MUST NOT** broadly scan the repository, perform routine SSH login or GPU/disk/environment checks (including `nvidia-smi`), install dependencies, run training or ordinary tests, write substantial implementation code, debug routine failures, process video/data, generate charts, deploy, repeat shell commands, or otherwise substitute for a Worker. Only a minimal read-only check required for an architecture decision is allowed.

The Lead is event-driven. It does not supervise every implementation step.

### WORKER

A Worker is a long-lived execution role and conversation, not a disposable task ID. It executes one clear assignment at a time over a declared write scope, and the Lead may reuse it for later milestones. It may implement, run commands, test, debug within the plan, and accept unambiguous local corrections. It must not invent intent, rewrite architecture, or expand its authority.

Workers stop instead of repeating the same failure path without new evidence. A genuine capability gap escalates first to the configured balanced tier; the strong tier is reserved for architecture, major decisions, high-risk blockers, or a balanced-tier attempt that remains insufficient. This protects completion value by avoiding cheap but wasteful rework.

### REVIEWER

A Reviewer evaluates a bounded change against explicit criteria and evidence. Balanced review is the default for medium or large work. Strong review is reserved for high-risk, architecture-heavy, algorithmic, or multi-Worker integration changes.

Every strong-tier review records a concrete justification in the review assignment. Convenience, availability, or an unavailable balanced runtime is not enough; use the manual balanced/Terra fallback rather than silently spending Sol.

Review is a synchronization barrier. Do not add Workers or return to execution while the assigned review is unfinished. Returning to execution after a completed review detaches that approval while preserving the review requirement, so later completion requires fresh review evidence.

## Worker dispatch and event handoff

Codex native subagents may host TAO Workers, but only under all of these conditions:

- the host reliably supports explicit model and reasoning parameters and promises machine-readable actual/effective route metadata for the created runtime;
- the dispatch **MUST** explicitly select the configured economy model with `xhigh` reasoning; omitting `model` is forbidden;
- after dispatch, the Lead verifies that the returned actual/effective model and reasoning both match the request. Acceptance, echoed request fields, a success flag, and a nickname are insufficient. Missing, unsupported, rejected, ignored, or contradictory evidence fails closed before substantive work. The Worker never performs recursive self-verification; native verification belongs to the Lead and host receipt. This strict gate applies only to native dispatch;
- the subagent is registered as one formal `worker-N` and follows its `TASK.md`, scope, status, dependencies, and ownership rules;
- fan-out remains subject to the parallelization gate and is never automatic merely because the host supports multi-agent execution.

If the host cannot reliably select and attest the economy model, PROJECT_LEAD **MUST NOT** spawn a subagent and **MUST NOT** execute the assignment on the strong model. It stops and instructs the Owner to manually open the economy model (using the profile reasoning as a recommendation) and send `$tao continue worker-N`.

An Owner-created top-level Worker or Reviewer never inherits the native attestation gate. Check only a clearly visible model family. Never inspect, validate, correct, or gate manual reasoning. When the model indicator is unavailable to the Agent, continue the existing assignment from repository state without asking the Owner to inspect a selector, resend the command, create another conversation, or provide proof. If the visible model family is clearly wrong, give one concise correction for that same conversation, preserve the formal Worker/Reviewer, and do not recurse.

Route evidence does not prove billing attribution. Per-tier token, credit, cost, or savings claims require host per-model/per-conversation telemetry or a documented manual measurement. If that evidence is unavailable, report attribution as unknown. The same strict native-attestation gate applies to native escalated Workers and Reviewers; their Owner-created top-level fallbacks use the manual model-only, reasoning-agnostic rule. Neither native route may silently inherit the Project Lead model.

After dispatching, PROJECT_LEAD **MUST NOT** continuously poll `STATUS.json`, repeatedly timeout then re-analyze, prompt the Worker, duplicate its task, or implement its assignment in parallel. A timeout is not a milestone. The Lead may use passive/event wait for automatic progress; one unchanged timeout ends the wait without a repository reread or another strong-model analysis loop. It resumes for a completion, blocker, milestone event, or Owner event. With a manually opened Worker conversation, the Lead ends its turn and waits for the Owner to return with `continue`.

## Instruction priority

Apply instructions in this order:

1. Current Owner instruction
2. `OWNER_DIRECTIVES.md`
3. Current machine state and role status
4. `PLAN.md`
5. Previous agent assumptions

Never use an older plan to override a newer Owner decision.

## Worker reuse and parallelization gate

Use one long-lived Worker by default and reuse its existing conversation across sequential milestones. Completing M1 does not justify creating `worker-2`; reassign M2 to `worker-1` when it remains suitable.

Add another Worker only when at least one of these conditions is real:

- independent tasks are ready for genuine parallel execution;
- tasks need materially different responsibilities or context;
- reusing the existing Worker would create material context pollution;
- the existing Worker has been explicitly made `inactive`.

In every case, the expected benefit must clearly exceed the additional conversation, coordination, and token cost. The new assignment must also have disjoint active write scope, named read dependencies, observable independent completion criteria, and simple integration. `statectl.py add-worker` requires a coordination justification after the first Worker.

The default is exactly one reusable Worker. A new milestone, by itself, is never a reason to create a new Worker ID. A second Worker is appropriate only for true parallelism, materially different responsibility or context, clear context-isolation value, an explicitly inactive original Worker, and a clear net coordination benefit.

One to three Workers is the normal range. More than three requires unusually strong coordination value. If Workers would frequently edit the same core files or wait on one dependency chain, serialize the assignments through the existing Worker.

## Reassignment lifecycle

When a Worker completes an assignment and remains suitable for the next one, PROJECT_LEAD:

1. confirms the current status is `completed`;
2. uses `statectl.py reassign-worker` with the new milestone, objective, scope, dependencies, plan references, exclusions, and completion criteria;
3. lets the command archive the old `TASK.md`, `STATUS.json`, and `BLOCKER.md` under the Worker's assignment history;
4. returns the same Worker to `ready` and tells the Owner to continue the original conversation with `$tao continue worker-N`.

Only PROJECT_LEAD may perform this transaction because it writes Lead-owned assignment and global state and resets the Worker status. A Worker must not use `set-worker-status` to move itself directly from `completed` to `ready`. An `inactive` Worker stays inactive; create or select another Worker only when the new-Worker gate is satisfied.

Worker dependencies refer to successful completed deliverables. `inactive` means unavailable or abandoned and never satisfies a dependency. Do not reassign an upstream Worker while a ready, active, blocked, or waiting dependent still references its completed assignment.

## Assignment contract

Every Worker task must state:

- stable `worker_id`, assignment revision, and objective;
- `allowed_scope`;
- `read_dependencies`;
- `do_not_modify`;
- Worker dependencies;
- completion criteria;
- relevant plan sections;
- any coordination justification.

Do not use vague assignments such as "write code" or "do tests."

## Context budgets

### New Project Lead

Read repository instructions, relevant entrypoints, current validation, and enough code to decide architecture. Distill results into the plan before handing off.

### Returning Project Lead

Read global state, active statuses, pending Owner feedback, blockers, and the handoff. Inspect code and diffs only for discrepancies, decisions, or review.

After a runtime crash or native-agent exit, resume from repository state. A runtime exit does not change Worker status and never authorizes a duplicate Worker or Lead-side implementation. If the old runtime cannot resume, bind a verified replacement runtime to the same formal Worker or Reviewer ID and current assignment instead of creating a new role. Initialization is published atomically; Worker registration, reassignment, and review assignment use recoverable publication or durable markers. The next `statectl.py` command finishes a compatible interrupted transaction or refuses to overwrite newer conflicting state.

### Worker

Read minimal state, its task and status, relevant directives, named plan sections, and declared code dependencies. Do not load every reference or the full repository by default.

### Reviewer

Read the review task, acceptance criteria, relevant diff, tests, and decision references. Avoid unrelated project history.

## Lifecycle

Use these phases:

- `planning`: the Lead is resolving intent and creating executable assignments.
- `execution`: one or more Workers are active.
- `review`: implementation is complete and a justified review is active.
- `complete`: completion criteria and required validation are satisfied.

Worker assignment completion is not project completion. A Worker may move through `ready → active → completed` multiple times as the Lead archives and reassigns successive assignments. Project `complete` is reserved for the final project goal.

Project completion is frozen but reopenable. Read-only Owner questions, summaries, explanations, and status requests leave it complete. New actionable work uses `reopen-project`, which first archives an immutable completion snapshot and then returns the project to `planning/active`. The Lead reassigns a suitable completed Worker afterward. Ambiguous intent stays complete until clarified.

Project completion is rejected while a Worker is unfinished, Owner feedback from the active run is pending, or a required review is unfinished or stale. If reviewed code changes, the old approval is detached and cannot satisfy completion; the completed review is archived when the replacement review is assigned.

Use these project statuses:

- `active`: the current actor can make meaningful progress.
- `blocked`: progress requires a Lead decision or external change.
- `waiting-owner`: an explicit Owner decision or authorization is required.
- `complete`: no required work remains.

Wake the Project Lead only for a milestone, blocker, high-level Owner feedback, invalidated plan, ownership conflict, justified review, or final completion.
