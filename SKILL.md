---
name: tiered-agent-orchestrator
description: Orchestrate large, multi-stage, or long-running engineering work with a persistent strong Project Lead, economy Workers, optional review, and repository-backed handoffs. Use for model-cost-aware execution, explicit tiered-agent commands, or continuation when .tiered-agent state exists. Do not start the full workflow for simple, local, low-risk edits that one agent can finish directly.
license: Apache-2.0
metadata:
  author: "jaywavfeng"
  version: "0.1.0"
---

# Tiered Agent Orchestrator

Use expensive intelligence only where expensive intelligence is needed:

- PROJECT_LEAD makes decisions and distills intent.
- WORKER performs clear, bounded implementation.
- REVIEWER checks completed work when the expected quality gain justifies another model switch.
- The repository carries operational state; chat history is never a handoff dependency.

## Route the request

First locate the repository root and check for `.tiered-agent/STATE.json`.

1. If state exists, treat the request as a continuation. Do not run the new-project complexity gate.
2. If the user names `continue worker-N`, use the Worker workflow.
3. If the user names `continue reviewer-N`, use the Reviewer workflow.
4. If the user asks for status, mentions a blocker, says `continue lead`, or returns with high-level feedback, use the Project Lead resynchronization workflow.
5. Otherwise apply the complexity gate.

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

1. Inspect repository instructions, code, and current validation state.
2. Resolve only uncertainties that materially change the goal or architecture.
3. Initialize runtime state with `python scripts/statectl.py init --project-root <repo> --project-id <slug>`. If executing from an installed copy, use the absolute path to this skill's script.
4. Write the distilled goal, current state, decisions, constraints, milestones, validation, and completion criteria to `PLAN.md`. Never record private chain-of-thought.
5. Analyze the dependency graph. Default to one Worker; add Workers only for ready, independently testable tasks with disjoint write ownership.
6. Register each Worker with `statectl.py add-worker` and give the Owner the shortest possible creation instructions: recommended role profile plus one `continue worker-N` line.
7. Update global state only at meaningful transitions.

For resynchronization:

1. Read `STATE.json`, active Worker status files, pending Owner inbox events, relevant blockers, and `HANDOFF.md`.
2. Inspect diffs or code only where status and evidence require it.
3. Interpret new Owner intent, update `OWNER_DIRECTIVES.md` and `PLAN.md` when decisions changed, then update assignments and global state.
4. Report progress concisely. The Owner must not summarize Worker history.

## Worker workflow

Read only [the runtime state contract](references/runtime-state.md), the named Worker's `TASK.md` and `STATUS.json`, relevant Owner directives, explicitly referenced plan sections, and the code dependencies named in the task.

Before editing, verify:

- the Worker ID exists and the task status is ready, active, blocked, or waiting-owner;
- the requested changes fit `allowed_scope` and avoid `do_not_modify`;
- dependency Workers are complete when required.

Then work independently through implementation and validation. Update only the Worker's status, its allowed code scope, its blocker file, and uniquely named Owner inbox events. Do not edit global state, the plan, other assignments, or other Worker status files.

Apply clear local Owner corrections directly when scope and intent are unambiguous. For ambiguous, directional, or architecture-changing feedback, preserve the Owner's exact words with `statectl.py record-owner-feedback`, pause conflicting work, and direct the Owner back to the original Project Lead conversation.

When blocked, follow [escalation and review](references/escalation-and-review.md). Stop repetitive attempts before cheap tokens become waste.

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
