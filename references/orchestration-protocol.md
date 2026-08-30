# Orchestration Protocol

Read this reference when acting as PROJECT_LEAD or when deciding Worker count and ownership.

## Roles

### OWNER

The Owner expresses goals, gives feedback, makes product decisions, and authorizes consequential external actions. The Owner speaks naturally and is never the message bus between agents.

### PROJECT_LEAD

The Project Lead is the long-lived management conversation. It interprets ambiguous intent, makes architecture decisions, distills a plan, assigns work, handles blockers, coordinates ownership, and decides whether review is worth its cost.

The Lead is event-driven. It does not supervise every implementation step.

### WORKER

A Worker executes a clear assignment over a declared write scope. It may implement, run commands, test, debug within the plan, and accept unambiguous local corrections. It must not invent intent, rewrite architecture, or expand its authority.

### REVIEWER

A Reviewer evaluates a bounded change against explicit criteria and evidence. Balanced review is the default for medium or large work. Strong review is reserved for high-risk, architecture-heavy, algorithmic, or multi-Worker integration changes.

## Instruction priority

Apply instructions in this order:

1. Current Owner instruction
2. `OWNER_DIRECTIVES.md`
3. Current machine state and role status
4. `PLAN.md`
5. Previous agent assumptions

Never use an older plan to override a newer Owner decision.

## Parallelization gate

Use one Worker by default. Add another only when every condition is satisfied:

- its task is ready now rather than waiting on another Worker;
- its write scope is disjoint from every active Worker;
- its read dependencies are named;
- it has observable, independent completion criteria;
- integration is simple and the time saved exceeds coordination cost.

One to three Workers is the normal range. More than three requires an explicit coordination justification in the assignment. If Workers would frequently edit the same core files, serialize the work.

## Assignment contract

Every Worker task must state:

- `worker_id` and objective;
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

Use these project statuses:

- `active`: the current actor can make meaningful progress.
- `blocked`: progress requires a Lead decision or external change.
- `waiting-owner`: an explicit Owner decision or authorization is required.
- `complete`: no required work remains.

Wake the Project Lead only for a milestone, blocker, high-level Owner feedback, invalidated plan, ownership conflict, justified review, or final completion.
