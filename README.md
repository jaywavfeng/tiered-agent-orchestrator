# tiered-agent-orchestrator

[English](README.md) | [简体中文](README.zh-CN.md)

**Correct completion first. A decision-focused Lead, reusable economy Workers, and repository-backed handoffs.**

Project status: **v0.6.0 · Apache-2.0 · Benchmark pending**

> Use the cheapest model that is likely to complete the task correctly without costly rework.

TAO is a Codex skill invoked as `$tao`. It keeps intent, architecture and acceptance with a strong Project Lead while a long-lived economy Worker implements and validates bounded assignments. One Worker is the default; it is reused across milestones. The project carries the state. **You never need to copy the previous conversation.**

## What changed in v0.6.0

- Optional host-task bindings, short dispatch packets, delivery receipts and completion/blocker callbacks let existing Worker tasks relay automatically.
- Automatic new-task creation remains conditional on explicit Owner authority and actual/effective model **and** reasoning evidence before substantive execution. Current desktop task contracts do not promise that evidence; creating a task successfully is not an attested route.
- Coordination has a **10% target relative to actual-task tokens**, with optional purpose-based benchmark reporting. Missing attribution is unmeasured; there is no daily token ledger.
- Role-specific context and current-state validation avoid repeatedly reading archives. Read-only commands no longer trigger recovery; `recover` explicitly handles a reported interrupted update.
- Helper invocations explicitly use Python. Normal TAO operations must not open the script in VS Code or an app file panel. The script has no editor-launch implementation; ambiguous bare-script instructions were removed. The historical GUI trigger has not been reproduced from an original tool trace.

## Install and activate

Use Codex's skill installer with repository `jaywavfeng/tiered-agent-orchestrator`, repository path `.`, and installation name `tiered-agent-orchestrator`. The skill's invocation name remains `tao`; it uses only Python 3.9+ and the standard library. An existing installation is not automatically updated by a GitHub release.

For a new complex project, select the Lead model and describe the outcome:

```text
$tao Plan and complete this project. Use one reusable Worker and repository-backed handoffs.
```

To authorize the optional automatic relay and conditional new tasks explicitly:

```text
$tao Automatically send assignments to my selected Worker tasks and completion/blocker messages back to the Lead. Reuse existing Workers. If none is suitable and the host can prove the effective model and reasoning before execution, create a new gpt-5.6-luna task with xhigh in this current saved project directory. Do not create an isolated worktree. Keep the Lead on gpt-5.6-sol; use gpt-5.6-terra first for escalation.
```

The Lead records existing authority once and binds actual task IDs, not guessed titles. Host restrictions still apply. If effective metadata is unavailable, manually create/select the economy task once, continue it with `$tao continue worker-1`, then let the authorized relay reuse it. Model reasoning is never gated in an Owner-created task: Luna/high, Luna/极高 and unavailable selectors do not require repeated proof. A visible wrong model gets one correction on the same task.

| Operation | Request |
|---|---|
| Cold-start Lead | `$tao continue lead` |
| Existing Worker | `$tao continue worker-1` |
| A genuinely independent registered Worker | `$tao continue worker-2` |
| Status | `$tao status` |

A maintenance request about TAO or the mere existence of `.tiered-agent` never implicitly starts orchestration. Small local tasks are completed directly.

## State and automatic handoff

The Lead owns goals/directives, global state, assignments and optional `TRANSPORT.json`. Workers own their assigned code scope, status and blockers. `HANDOFF.md` is the compact takeover packet; `OWNER_STATUS.md` is a human report, not a machine database. Each fact has one canonical source.

After persisting a ready assignment, the Lead verifies the bound task's directory and availability, generates a short packet, records `pending`, sends through `send_message_to_thread`, then records `sent`, definite `not-sent`, or `unknown`. Pending/uncertain delivery blocks a blind resend. The Worker validates the assignment revision, executes, records its result, and sends one notification to the Lead. Chat delivery never establishes task acceptance.

Use bounded `wait_threads` calls with cursors. One unchanged timeout ends the wait; callbacks can wake an idle Lead. Do not poll or regenerate summaries on a timer. `reassign-worker` archives the completed assignment and reuses the same Worker; `reopen-project` archives completed project state before an actionable correction. Old projects without transport still work manually.

Full host procedure and normalized observation/receipt formats: [host dispatch](references/host-dispatch.md). A working two-assignment example is in [one Worker flow](examples/one-worker-flow.md). Internal subagents remain conditional on the same native route proof; they are not automatically equivalent to Owner-created sidebar tasks.

## Execute the CLI through Python

From this repository, these are runnable command interfaces:

```console
python scripts/statectl.py --help
python scripts/statectl.py init --project-root /path/to/project --project-id my-project
python scripts/statectl.py add-worker --project-root /path/to/project --worker-id worker-1 --objective "Implement parser" --allowed-scope "src/**" --completion-criterion "Parser tests pass"
python scripts/statectl.py context --project-root /path/to/project --role worker-1
python scripts/statectl.py status --project-root /path/to/project
python scripts/statectl.py validate --project-root /path/to/project
```

From an installed skill on Windows, use actual absolute paths:

```powershell
& "<absolute path to python.exe>" "<absolute skill directory>\scripts\statectl.py" context --project-root "<project directory>" --role worker-1
```

Replace placeholders; quote paths with spaces or Chinese characters. Use the interpreter already verified for the environment. Do not invoke a bare `.py` path, launch it with `code`/`Invoke-Item`, or treat an opened editor as a successful command. For arguments, request the subcommand's `--help`; inspect source only for a concrete diagnostic need. Do not change file associations or editor settings.

New CLI subcommands are `bind-thread`, `context`, `dispatch-context`, `record-dispatch`, `notification-context`, and `recover`. Relay status updates use `--assignment-revision`. `status` no longer returns the history count because normal status does not scan archives. Explicit `validate` retains full historical checking. Existing ownership, dependency, scope, completion and review rules remain enforced.

## Coordination budget and validation

The target is **coordination tokens / actual-task tokens <= 0.10** for one completed task. Architecture and substantive acceptance are actual task work, including when performed by the Lead. Protocol reading, dispatch, bookkeeping and redundant status checks are coordination. Per-model usage alone cannot classify purpose; never substitute account-wide limits or guessed token counts.

The existing benchmark schema accepts an optional `purpose_usage` object. See [measurement rules](benchmarks/README.md) for source evidence, incomplete attribution and synthetic fixtures. A ratio is reported only for complete, successfully finished, nonsynthetic attributed runs. Exceeding 10% calls for batching assignments and cutting repeated context/reporting, not weakening actual validation.

> **Prefer the simplest mechanism that is sufficiently reliable for the actual failure modes of the project.**

No permanent token ledger, periodic audit, checksum tree or extra recovery system is required. Report measured document/read/action reductions as proxies, not claimed token/credit savings. Public savings remain **Benchmark pending**.

Run tests and measurement interfaces:

```console
python -m unittest discover -s tests -v
python scripts/benchmark.py --help
python scripts/benchmark.py overhead benchmarks/runs.jsonl
```

`runs.jsonl` is supplied measurement data, not bundled real evidence. Tests use isolated temporary projects and synthetic host receipts. CI covers Windows/Ubuntu and Python 3.9/3.13. Scenario definitions under `evals/` are separate from actual Agent execution evidence; mock relay tests do not establish live desktop creation or GUI behavior.

See [v0.6.0 validation notes](benchmarks/v0.6.0-validation.md) for release evidence and explicit measurement limits. Git publication, deployment and global configuration changes still require Owner authority.
