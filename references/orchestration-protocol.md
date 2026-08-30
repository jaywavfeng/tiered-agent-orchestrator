# Orchestration Protocol

Read this reference when acting as PROJECT_LEAD or when deciding Worker count and ownership.

## Cost-first model policy

Correct completion is the first priority. The next priorities are reducing strong-model/Sol usage, reducing credits and cost, avoiding unnecessary context loading and model switches, and only then reducing total token count. It is acceptable for Luna/economy execution to use more tokens when that materially reduces Sol usage and credits.

Model tiers are hard routing constraints, not suggestions. PROJECT_LEAD reserves the strong tier for ambiguous intent, architecture, decomposition, major decisions, difficult blockers, and final acceptance. WORKER handles routine execution on the economy tier. REVIEWER defaults to balanced or another tier below strong; strong review is reserved for genuine high-risk architecture, algorithm, security, or integration decisions. Exact host mappings live in the selected profile.

## Roles

### OWNER

The Owner expresses goals, gives feedback, makes product decisions, and authorizes consequential external actions. The Owner speaks naturally and is never the message bus between agents.

### PROJECT_LEAD

The Project Lead is the long-lived management conversation. It interprets ambiguous intent, makes architecture decisions, distills a plan, assigns work, handles blockers, coordinates ownership, and decides whether review is worth its cost. It **MUST** ask whether an action needs strong reasoning before doing it and delegate routine work to the current Worker.

PROJECT_LEAD **MUST NOT** broadly scan the repository, perform routine SSH login or GPU/disk/environment checks (including `nvidia-smi`), install dependencies, run training or ordinary tests, write substantial implementation code, debug routine failures, process video/data, generate charts, deploy, repeat shell commands, or otherwise substitute for a Worker. Only a minimal read-only check required for an architecture decision is allowed.

The Lead is event-driven. It does not supervise every implementation step.

### WORKER

A Worker is a long-lived execution role and conversation, not a disposable task ID. It executes one clear assignment at a time over a declared write scope, and the Lead may reuse it for later milestones. It may implement, run commands, test, debug within the plan, and accept unambiguous local corrections. It must not invent intent, rewrite architecture, or expand its authority.

### REVIEWER

A Reviewer evaluates a bounded change against explicit criteria and evidence. Balanced review is the default for medium or large work. Strong review is reserved for high-risk, architecture-heavy, algorithmic, or multi-Worker integration changes.

## Worker dispatch and event handoff

Codex native subagents may host TAO Workers, but only under all of these conditions:

- the host reliably supports an explicit model parameter;
- the dispatch **MUST** explicitly select the configured economy model with High reasoning; omitting `model` is forbidden;
- the subagent is registered as one formal `worker-N` and follows its `TASK.md`, scope, status, dependencies, and ownership rules;
- fan-out remains subject to the parallelization gate and is never automatic merely because the host supports multi-agent execution.

If the host cannot reliably select the economy model, PROJECT_LEAD **MUST NOT** spawn a subagent. It stops and instructs the Owner to manually open the economy model at High reasoning and send `$tao continue worker-N`.

After dispatching, PROJECT_LEAD **MUST NOT** continuously poll `STATUS.json`, repeatedly wait/check or prompt the Worker, duplicate its task, or implement its assignment in parallel. It yields for a completion, blocker, milestone event, or Owner event. With a manually opened Worker conversation, the Lead ends its turn and waits for the Owner to return with `continue`.

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

Use these project statuses:

- `active`: the current actor can make meaningful progress.
- `blocked`: progress requires a Lead decision or external change.
- `waiting-owner`: an explicit Owner decision or authorization is required.
- `complete`: no required work remains.

Wake the Project Lead only for a milestone, blocker, high-level Owner feedback, invalidated plan, ownership conflict, justified review, or final completion.
