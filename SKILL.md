---
name: tao
description: Orchestrate large, multi-stage engineering work with a decision-focused Lead, reusable economy Workers, repository-backed handoffs, and optional host task messaging. Activate only for an explicit $tao command. Do not orchestrate simple local edits or activate merely because this skill is being maintained.
license: Apache-2.0
metadata:
  author: "jaywavfeng"
  version: "0.6.0"
---

# Tiered Agent Orchestrator

> **Use the cheapest model that is likely to complete the task correctly without costly rework.**

Correct completion first, then maximize useful work per token/credit. PROJECT_LEAD uses the strong tier for intent, architecture, difficult decisions and acceptance. A reusable WORKER uses the economy tier for implementation and validation. REVIEWER is optional and normally balanced. The repository carries operational state; chat history is never a handoff dependency.

## Activate and choose a role

The current Owner request must explicitly invoke `$tao`. Existing `.tiered-agent` state, pasted examples, or a request to develop/test/release TAO itself never activates orchestration. Without activation, work normally.

For new work, handle a bounded, low-risk task directly when a durable handoff would cost more than it helps. Otherwise initialize once. With existing state, continue the named `worker-N` or `reviewer-N`; `$tao continue lead`, high-level feedback, or status returns to the Lead. Do not rerun the complexity gate for an existing assignment.

Completed projects remain frozen for read-only questions. For actionable changes, only the Lead uses the `reopen-project` subcommand, which archives completion before resuming planning. Then reuse a completed Worker via `reassign-worker`.

## Run the helper, do not open it

`scripts/statectl.py` is a command-line tool. Invoke it through a verified Python 3.9+ interpreter in the terminal. Resolve this skill's script location once; from an installed skill use its absolute path, not a same-named file in the target project.

```powershell
& "<absolute path to python.exe>" "<absolute skill directory>\scripts\statectl.py" context --project-root "<project directory>" --role worker-1
```

On other shells use `python "/absolute/skill/scripts/statectl.py" ...`. Replace placeholders with real paths. Never launch a bare `.py` path, `code`, `Invoke-Item`, `Start-Process` on the script, or a file-opening tool to perform a state operation. Do not automatically show this helper in VS Code or the app's file panel. Opening is appropriate only when the Owner requests viewing/editing it. Do not change OS associations.

Use the needed subcommand directly; if its arguments are unclear, run that subcommand with `--help`. Read source only to investigate a concrete error. Success requires the process exit code, CLI output and expected state, not an editor window. `context` also returns the executable/script argument array for subsequent calls.

## Lead

Read [Lead coordination](references/orchestration-protocol.md) for first planning or a directional change. Read [state ownership](references/runtime-state.md) once before modifying runtime state. Read exactly one [OpenAI](profiles/openai-codex.md) or [generic](profiles/generic.md) profile when selecting models.

For a fresh project, use `init`, write stable goals/constraints/acceptance in `PLAN.md`, and register one Worker with `add-worker`. Group related execution steps into one bounded assignment. Add Workers only for useful independent work whose benefit exceeds coordination cost; never because the milestone changed.

For `$tao continue lead`, use `context --role lead`. Its current status and `HANDOFF.md`, relevant `OWNER_DIRECTIVES.md`/`PLAN.md` sections, active blockers and pending events must recover the final goal, completed work, current position, verified results, constraints, blockers, next action and Owner decision without chat history. Read historical assignments or code only for a concrete discrepancy or decision.

Before messaging or creating a runtime, read [host dispatch](references/host-dispatch.md). Reuse a bound Worker, persist the assignment first, prepare the short message, reserve delivery, send through the host, and record the outcome. Missing tools or a missing binding retains the manual `$tao continue worker-N` path. Automatic creation requires explicit Owner authority and actual/effective route evidence; capability to accept a model parameter is insufficient.

The Lead MUST NOT substitute for a Worker on routine implementation, SSH/environment checks, `nvidia-smi`, training, tests or data processing. Use strong reasoning for decisions; a minimal read needed to decide architecture is appropriate. Task authorization also permits the small state/relay operations needed to manage that task.

## Worker and Reviewer

A Worker is a long-lived role and conversation, not a single task. Start with `context --role worker-N`; for a relay message also pass its `--assignment-revision`. Read the returned current task and status, relevant directives and named dependencies. Do not preload Lead references, the whole plan or archives.

Confirm status, dependencies, `allowed_scope` and exclusions before acting. Execute and validate independently, using `set-worker-status` at meaningful transitions; relay-driven writes include `--assignment-revision`. Workers own their code scope, status, blocker and uniquely named Owner events, never the Lead's global files or transport bindings. Scope is not authority for unrelated external actions.

Owner-created Workers check only a clearly exposed model family; if unavailable, continue without asking for selector proof. Never validate or gate reasoning in a manual conversation. A visible wrong model gets one correction for the same conversation. Native runtime proof is the Lead's responsibility, never recursive Worker self-inspection.

On completion, set `completed`. With an authorized binding, use `notification-context` and send its message once to the Lead; otherwise return the manual continuation instruction. Do not request a new Worker for the next milestone. For a blocker, ambiguous Owner feedback or the same failure without new evidence, read [escalation](references/escalation-and-review.md). Clear in-scope corrections remain local; directional feedback is preserved verbatim for the Lead.

A Reviewer starts only when assigned. Use `context --role reviewer-N`, inspect the task, relevant diff and actual validation evidence, then write the report and review status. Do not broaden implementation. Strong review needs an explicit risk justification; route rules are shared with Workers.

## Keep coordination below the task

Target **coordination tokens / actual-task tokens <= 10%** over a completed task. Architecture, implementation and substantive acceptance are actual work regardless of model tier. Protocol loading, bookkeeping, dispatch and redundant status checks are coordination. Attribute only from documented purpose-level evidence; incomplete attribution is unmeasured. No daily token ledger. Read [benchmark measurement](benchmarks/README.md) only when evaluating usage.

Use one Worker by default, short messages and event-driven progress. A timeout is not a milestone: one unchanged passive wait ends without another polling/reanalysis loop. Completion/blocker messages can wake an idle bound Lead; no periodic automation is required. Status requests read current state only.

Write at assignment, completion, blocker, material validation or direction changes, not after commands. Keep facts in their canonical file; refresh `HANDOFF.md` for a changed handoff and `OWNER_STATUS.md` only for changed human-visible outcomes/risks. The human summary is never used to override machine state. If measured overhead exceeds 10%, batch assignments and remove repeated context/reporting without weakening acceptance.

> **Prefer the simplest mechanism that is sufficiently reliable for the actual failure modes of the project.**

Do not add hashes, checksum trees, audit layers or new recovery protocols for hypothetical failures. Ordinary commands validate current state; explicit `validate` checks history. Read-only commands never repair files. Use `recover` through Python only after a reported interrupted update. Once the mechanism is sufficiently reliable, advance the Owner's task.

Never bypass host approvals. Git publication, production deployment, destructive changes and global configuration changes require existing Owner authority; an assignment alone does not grant it. Route evidence does not prove billing or savings.
