# tiered-agent-orchestrator

[English](README.md) | [简体中文](README.zh-CN.md)

**Use expensive models for decisions. Use cheaper models for execution. Keep project state across agent conversations.**

One project. One long-lived manager. The right number of workers. Shared repository state.

> Project status: v0.1.0 · Apache-2.0 · Benchmark pending

## Why this exists

Strong models are valuable for ambiguous intent, architecture, decomposition, major corrections, and difficult review. They are usually an expensive way to search files, edit routine code, run commands, or repeat tests.

`tiered-agent-orchestrator` turns a large engineering task into a small software-team workflow:

```text
OWNER
  └── PROJECT_LEAD (strong)
        ├── WORKER 1 (economy)
        ├── WORKER 2 (economy, only when truly parallel)
        └── REVIEWER (balanced or strong, only when justified)
```

The Lead distills expensive reasoning into a compact plan and bounded assignments. Workers do most of the implementation. Operational state lives in `.tiered-agent/`, so a new conversation can continue without chat history.

**You never need to copy the previous conversation.**

## What it does

- Keeps one Project Lead conversation for the project lifecycle.
- Defaults to one Worker and permits parallel Workers only for independent, disjoint work.
- Gives every Worker an objective, write scope, dependencies, exclusions, and completion criteria.
- Separates global Lead-owned state from Worker-owned status to avoid concurrent write conflicts.
- Escalates decisions and ambiguous intent instead of turning the Owner into a message bus.
- Loads context progressively so Workers do not pay to read the Lead's entire exploration.
- Adds deterministic, dependency-free state validation and management summaries.
- Provides paired benchmark tooling without publishing invented savings claims.

It does **not** automatically switch top-level models, create model-specific conversations, push Git, deploy production, or bypass the host's approval model.

## Quick start

### 1. Install the Skill

For a single Codex repository, clone it into the repository skill location:

```console
git clone https://github.com/jaywavfeng/tiered-agent-orchestrator.git .agents/skills/tiered-agent-orchestrator
```

For user-wide Codex discovery, place the repository at:

```text
$HOME/.agents/skills/tiered-agent-orchestrator
```

Other Agent Skills-compatible coding agents can install the same directory in their supported skill location. The portable contract is the root `SKILL.md`; `agents/openai.yaml` is optional OpenAI-specific metadata.

### 2. Open the Project Lead

Choose a strong model and describe the final goal naturally:

```text
$tiered-agent-orchestrator Build the import pipeline, migrate existing callers, and run the full integration suite.
```

The Lead inspects the repository, creates `.tiered-agent` state, decides the architecture, and determines whether Worker delegation will actually save strong-model work.

### 3. Start only the Workers the Lead requests

A typical instruction is:

```text
Create one economy Worker conversation and send:
$tiered-agent-orchestrator continue worker-1
```

If three tasks are genuinely independent, the Lead may provide three separate continuation lines. If the tasks are coupled, it stays with one Worker.

Work normally in the Worker conversation. Return to the original Project Lead conversation for a blocker, ambiguous direction change, architecture decision, or management status:

```text
$tiered-agent-orchestrator status
```

## Commands

| Invocation | Behavior |
|---|---|
| `$tiered-agent-orchestrator <goal>` | Apply the complexity gate and initialize a Project Lead only for suitable work |
| `$tiered-agent-orchestrator continue worker-1` | Continue a bounded Worker from repository state |
| `$tiered-agent-orchestrator continue reviewer-1` | Continue an explicitly assigned review |
| `$tiered-agent-orchestrator status` | Summarize Workers, review, blockers, risks, and next actor |
| `$tiered-agent-orchestrator continue lead` | Resynchronize the original Lead with current repository state |

Simple, local, low-risk edits are completed directly without creating orchestration state.

## Runtime state

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
│   └── BLOCKER.md
└── review/
    ├── TASK.md
    ├── STATUS.json
    └── REPORT.md
```

`STATE.json` is deliberately small and never stores chat transcripts, hidden reasoning, secrets, command logs, or model names. `PLAN.md` stores decisions rather than chain-of-thought. `HANDOFF.md` stores only the next role's essential facts.

Global state, the plan, directives, and assignments have one writer: PROJECT_LEAD. Each Worker owns only its declared code scope, its status, blocker, and uniquely named Owner-feedback events.

## State helper

Python 3.9+ is the only runtime dependency. The helper uses the standard library and never overwrites initialized state.

```console
python scripts/statectl.py init --project-root /path/to/project --project-id my-project --profile generic
python scripts/statectl.py add-worker --project-root /path/to/project --worker-id worker-1 --objective "Implement the parser" --allowed-scope "src/parser/**" --completion-criterion "Parser tests pass"
python scripts/statectl.py validate --project-root /path/to/project
python scripts/statectl.py status --project-root /path/to/project
```

Agents may maintain the documented files manually when Python is unavailable, but they must preserve the schemas and ownership rules.

## Model profiles

The core protocol knows only `strong`, `balanced`, and `economy`.

- [OpenAI Codex profile](profiles/openai-codex.md) maps the current Sol/Terra/Luna family.
- [Generic profile](profiles/generic.md) explains how to map another host or provider.

Profiles are editable recommendations. Changing a model mapping never changes persisted project state.

## Owner feedback and blockers

A Worker applies a clear local correction directly when it remains inside the assignment. It does not reinterpret feedback such as “this feels too engineered” into an architecture change. Instead it records the exact Owner message, pauses conflicting work, and returns the decision to the original Lead.

Escalation is evidence-based, not “three failures means stop.” A Worker continues while each attempt tests a distinct hypothesis and stops when it is repeating the same failure class without new evidence.

## Review policy

Low-risk, well-validated work can finish without a separate review. Medium or large changes normally use a balanced Reviewer. A strong Reviewer is reserved for high-risk, core algorithm, architecture, security, or multi-Worker integration work.

## Benchmarking

Benchmark pending.

The repository includes a paired JSONL schema and aggregator for comparing:

- strong-model-only execution;
- tiered execution with a strong Lead, economy Workers, and optional review.

It records success, test pass rate, total and per-tier tokens, optional cost or credits, time, model switches, Worker conversations, escalations, and Owner interventions. See [the benchmark protocol](benchmarks/README.md). Do not claim a savings percentage until comparable real runs are published.

## Validation

```console
python -m unittest discover -s tests -v
python scripts/statectl.py --help
python scripts/benchmark.py --help
```

The test suite covers initialization without overwrite, schema and path safety, Worker registration and transitions, parallel write-scope conflicts, blocker recovery, review, verbatim Owner feedback, management status, all A–J behavior contracts, and benchmark aggregation.

## Compatibility and current limitations

- Requires conversations to share a writable repository.
- The Owner manually opens model-specific top-level conversations in v1.
- Model and reasoning labels vary across hosts; use the generic profile when needed.
- Token and credit telemetry must come from the host or documented manual measurements.
- SkillsMP independently scans public GitHub repositories on its own schedule; repository publication cannot guarantee immediate indexing.

This structure follows the [Agent Skills specification](https://agentskills.io/specification) and [official OpenAI documentation for building skills](https://learn.chatgpt.com/docs/build-skills). The current OpenAI mapping follows [official model guidance](https://learn.chatgpt.com/docs/models).

## Uninstall

Remove the installed Skill directory from the agent's skill location. Project runtime state is separate; delete `.tiered-agent/` from an individual project only when you intentionally want to discard its orchestration history.

## License

Apache-2.0. See [LICENSE](LICENSE).
