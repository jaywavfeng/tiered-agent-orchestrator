# tiered-agent-orchestrator

[English](README.md) | [简体中文](README.zh-CN.md)

**Use expensive models for decisions. Use cheaper models for execution. Keep project state across agent conversations.**

One project. One long-lived manager. Reusable long-lived workers. Shared repository state.

> Project status: v0.3.0 · Apache-2.0 · Benchmark pending

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

### Cost-first execution

TAO optimizes for correct completion first, then lower strong-model/Sol usage, then lower credits/cost, then less unnecessary context and model switching, and only lastly fewer total tokens. Sol is reserved for ambiguity, architecture, major decisions, difficult blockers, and final acceptance. Luna Workers perform searches, environment checks, implementation, experiments, tests, debugging, data/video processing, remote operations, and result packaging. Total tokens may rise slightly when expensive-model usage and credits fall substantially.

This routing is a hard constraint. When Codex native subagent dispatch supports an explicit model, the Lead must pass `gpt-5.6-luna` with High reasoning. If the host cannot reliably set the model, the Lead must not spawn: it stops and asks the Owner to open `gpt-5.6-luna / High` and send `$tao continue worker-1`. TAO must never create a Worker that silently inherits Sol to simulate low-cost delegation.

## What it does

- Keeps one Project Lead conversation for the project lifecycle.
- Defaults to one long-lived Worker conversation and reuses it across sequential milestones.
- Adds another Worker only for genuine parallelism, distinct responsibilities or context, material context-isolation value, or an explicitly inactive Worker—and only when the benefit exceeds coordination and token cost.
- Gives every Worker an objective, write scope, dependencies, exclusions, and completion criteria.
- Archives completed assignments before reusing the stable Worker ID, so old task evidence is never silently overwritten.
- Separates global Lead-owned state from Worker-owned status to avoid concurrent write conflicts.
- Escalates decisions and ambiguous intent instead of turning the Owner into a message bus.
- Loads context progressively so Workers do not pay to read the Lead's entire exploration.
- Adds deterministic, dependency-free state validation and management summaries.
- Provides paired benchmark tooling without publishing invented savings claims.

It does **not** automatically switch top-level models, create model-specific conversations when the host cannot guarantee an economy model, push Git, deploy production, or bypass the host's approval model.

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

The Skill is explicit-only and does not activate from ordinary language. Start an orchestration request with `$tao`.

### 2. Open the Project Lead

Choose a strong model and describe the final goal naturally:

```text
$tao Build the import pipeline, migrate existing callers, and run the full integration suite.
```

The Lead reads only enough of the repository to decide architecture, creates `.tiered-agent` state, and determines whether Worker delegation will reduce strong-model work. It must delegate routine mechanics to the economy Worker. After dispatch it yields for a completion, blocker, milestone, or Owner event; it does not poll `STATUS.json` or repeat checks.

### 3. Start the default Worker once, then reuse it

A typical instruction is:

```text
Create one economy Worker conversation and send:
$tao continue worker-1
```

For the next sequential milestone, the Lead reassigns `worker-1` and the Owner returns to this same Worker conversation. A milestone boundary alone never creates `worker-2`.

Work normally in the Worker conversation. Return to the original Project Lead conversation for a blocker, ambiguous direction change, architecture decision, or management status:

```text
$tao status
```

### Reuse across milestones

```text
Lead:
$tao Complete this project

Worker conversation:
$tao continue worker-1

M1 complete
↓
Return to Lead: continue
↓
Lead reassigns M2 to worker-1
↓
Return to the same Worker conversation:
$tao continue worker-1
```

Only when a separate task is genuinely independent and parallel—or requires materially different responsibility or isolated context—should the Lead ask the Owner to create another conversation:

```text
$tao continue worker-2
```

### Dispatch lifecycle

Ideal native-dispatch mode:

```text
Owner
  ↓
Sol Project Lead
  ↓
explicit spawn of gpt-5.6-luna / High worker-1
  ↓
Sol stops and waits for an event
  ↓
Luna performs checks / implementation / training
  ↓
milestone event
  ↓
Sol reads the summary and chooses the next stage
  ↓
Lead reassigns the same worker-1
```

When explicit economy routing is unavailable:

```text
Sol Project Lead prepares worker-1
  ↓
Sol stops
  ↓
Owner opens gpt-5.6-luna / High and sends:
$tao continue worker-1
```

TAO does not continuously poll or duplicate Worker work after dispatch.

## Commands

| Invocation | Behavior |
|---|---|
| `$tao <goal>` | Apply the complexity gate and initialize a Project Lead only for suitable work |
| `$tao continue worker-1` | Continue a bounded Worker from repository state |
| `$tao continue reviewer-1` | Continue an explicitly assigned review |
| `$tao status` | Summarize Workers, review, blockers, risks, and next actor |
| `$tao continue lead` | Resynchronize the original Lead with current repository state |

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
│   ├── BLOCKER.md
│   └── history/assignment-<revision>/
│       ├── TASK.md
│       ├── STATUS.json
│       └── BLOCKER.md
└── review/
    ├── TASK.md
    ├── STATUS.json
    └── REPORT.md
```

`STATE.json` is deliberately small and never stores chat transcripts, hidden reasoning, secrets, command logs, or model names. `PLAN.md` stores decisions rather than chain-of-thought. `HANDOFF.md` stores only the next role's essential facts.

Global state, the plan, directives, assignments, and assignment archives have one writer: PROJECT_LEAD. Each Worker owns only its declared code scope, current status, blocker, and uniquely named Owner-feedback events. After completion, only the Lead's reassignment transaction may archive those files and reset the Worker to `ready`.

## State helper

Python 3.9+ is the only runtime dependency. The helper uses the standard library. Initialization never overwrites existing state, and reassignment archives the completed task, status, and blocker before replacing the current assignment.

```console
python scripts/statectl.py init --project-root /path/to/project --project-id my-project --profile generic
python scripts/statectl.py add-worker --project-root /path/to/project --worker-id worker-1 --objective "Implement the parser" --allowed-scope "src/parser/**" --completion-criterion "Parser tests pass"
python scripts/statectl.py reassign-worker --project-root /path/to/project --worker-id worker-1 --milestone "M2" --objective "Integrate the parser" --allowed-scope "src/integration/**" --completion-criterion "Integration tests pass"
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

The test suite covers initialization without overwrite, schema and path safety, reusable Worker reassignment and immutable assignment history, parallel-Worker justification, write-scope conflicts, blocker recovery, review, verbatim Owner feedback, management status, all A–J behavior contracts, and benchmark aggregation.

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
