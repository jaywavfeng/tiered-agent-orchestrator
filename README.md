# tiered-agent-orchestrator

[English](README.md) | [简体中文](README.zh-CN.md)

**Correct completion first, then maximize useful work per token/credit. Use the cheapest model likely to finish correctly without costly rework, and keep the project recoverable without chat history.**

One project. One long-lived manager. Reusable long-lived workers. Shared repository state.

> Project status: v0.5.0 · Apache-2.0 · Benchmark pending

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

The Lead distills expensive reasoning into a compact plan and bounded assignments. Workers do most of the implementation. Operational state lives in `.tiered-agent/`, so a new account or completely fresh Lead can continue without chat history. `HANDOFF.md` is the Lead's cold-start packet; `OWNER_STATUS.md` is the separate human project-manager report.

**You never need to copy the previous conversation.**

### Completion-value execution

> **Use the cheapest model that is likely to complete the task correctly without costly rework.**

TAO optimizes for correct completion first, then lower strong-model/Sol usage, then lower credits/cost, then less unnecessary context and model switching, and only lastly fewer total tokens. The goal is value per completed task—not the lowest single-run cost. Sol is reserved for ambiguity, architecture, major decisions, high-risk blockers, and final acceptance. Luna/xhigh Workers perform ordinary searches, environment checks, implementation, experiments, tests, debugging, data/video processing, remote operations, and result packaging; spending more Luna reasoning tokens is acceptable when it avoids rework.

This routing is a hard constraint. Ordinary execution defaults directly to `gpt-5.6-luna / xhigh`; do not lower native reasoning merely to save a small one-off cost. Native dispatch is allowed only when the host accepts explicit `model: "gpt-5.6-luna"` and `reasoning_effort: "xhigh"` **and returns machine-readable actual/effective values for both**. Acceptance, echoed request fields, a success flag, or a nickname is not proof. Missing or contradictory metadata fails closed before substantive native work, and Sol must not absorb the assignment. Owner-created top-level conversations are different: TAO checks only a clearly visible model family and never validates or gates reasoning. Luna/high, Luna/极高, and any other Luna reasoning setting continue; an unavailable model indicator also continues without a selector check or command resend. Route proof is not billing proof: Luna token/credit attribution requires host per-model/per-conversation telemetry or a documented manual measurement. Native Terra escalations and Reviewers keep the strict gate; manual ones use the lighter rule.

## What it does

- Keeps one Project Lead conversation for the project lifecycle.
- Defaults to one long-lived Worker conversation and reuses it across sequential milestones.
- Adds another Worker only for genuine parallelism, distinct responsibilities or context, material context-isolation value, or an explicitly inactive Worker—and only when the benefit exceeds coordination and token cost.
- Gives every Worker an objective, write scope, dependencies, exclusions, and completion criteria.
- Archives completed assignments before reusing the stable Worker ID, so old task evidence is never silently overwritten.
- Reopens a completed project only for actionable Owner work, after archiving an immutable completion snapshot.
- Separates global Lead-owned state from Worker-owned status to avoid concurrent write conflicts.
- Treats review as a synchronization barrier and invalidates completed review evidence whenever execution resumes.
- Requires an explicit high-risk justification before assigning a strong-tier review.
- Escalates decisions and ambiguous intent instead of turning the Owner into a message bus.
- Loads context progressively so Workers do not pay to read the Lead's entire exploration.
- Supports `$tao continue lead` from zero chat context through one bounded repository-state read sequence.
- Keeps a concise `OWNER_STATUS.md` for the Owner without mixing presentation into machine state.
- Prefers the simplest mechanism sufficient for real failure modes and rejects speculative defensive layers.
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

The Skill is explicit-only and does not activate from ordinary language. Start every orchestration request with `$tao`. Existing `.tiered-agent` state, a previous invocation, or a request to modify TAO itself never activates the Skill implicitly.

### 2. Open the Project Lead

Choose a strong model and describe the final goal naturally:

```text
$tao Build the import pipeline, migrate existing callers, and run the full integration suite.
```

The Lead reads only enough of the repository to decide architecture, creates `.tiered-agent` state, and determines whether Worker delegation will reduce strong-model work. It must delegate routine mechanics to the economy Worker. After dispatch it may passively wait for an event that advances the Worker; it does not poll `STATUS.json` or repeat checks. A timeout is not a milestone: do not loop through timeout → Sol re-analysis → STATUS check → wait.

### 3. Start the default Worker once, then reuse it

A typical instruction is:

```text
Create one economy Worker conversation and send:
$tao continue worker-1
```

For the next sequential milestone, the Lead reassigns `worker-1` and the Owner returns to this same Worker conversation. A milestone boundary alone never creates `worker-2`.

If a completed project later receives actionable feedback, invoke `$tao` in the original Lead conversation. The Lead archives the completed project with `reopen-project`, returns it to planning, and reassigns the same completed Worker. A question, summary, explanation, status request, or ambiguous remark leaves the project complete; ambiguity is clarified before reopening.

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

### Zero-context Lead takeover

Open the same repository in a new account or a completely fresh strong-model conversation and send:

```text
$tao continue lead
```

The new Lead does not need a recap. It reads `STATE.json` and `HANDOFF.md` first, then current `OWNER_DIRECTIVES.md`, only the relevant stable sections of `PLAN.md`, and active Worker/Reviewer status or blockers. That bounded set identifies the final goal, completed work, current position, role states, decisions and constraints, verified results, blockers, next action, and whether the Owner must decide anything. Code, diffs, and historical archives are loaded only when this evidence identifies a specific discrepancy.

For the Owner's plain-language overview, open `.tiered-agent/OWNER_STATUS.md`. It is updated only at milestones, blockers, material result/risk changes, completion, reopen, or a changed Owner decision—not after each command.

### Dispatch lifecycle

Ideal native-dispatch mode, available only when the returned receipt attests actual/effective model and reasoning:

```text
Owner
  ↓
Sol Project Lead
  ↓
explicit spawn of gpt-5.6-luna / xhigh worker-1
  ↓
Lead passively waits for an event (timeout is not a milestone)
  ↓
Luna performs checks / implementation / training
  ↓
milestone event
  ↓
Sol reads the summary and chooses the next stage
  ↓
Lead reassigns the same worker-1
```

When effective model/reasoning metadata is missing, unsupported, rejected, or contradictory:

```text
Sol Project Lead prepares worker-1 and stops any unverified native Worker
  ↓
Sol stops
  ↓
Owner opens gpt-5.6-luna (xhigh recommended) and sends:
$tao continue worker-1
```

For this Owner-created conversation, only a clearly visible model family is checked. Reasoning is never inspected or gated: Luna/high, Luna/极高, and any other Luna reasoning setting continue. If the Agent cannot see the model indicator, it continues the existing Worker without asking for a selector check, a repeated command, proof, or another Worker. A clearly wrong model gets one concise correction for the same conversation. Billing attribution still requires host telemetry or documented manual measurement. TAO does not continuously poll or duplicate Worker work after dispatch; one unchanged passive-wait timeout ends the wait without another Sol analysis loop. Repeated identical Luna failures stop and escalate to Terra instead of retrying the same plan.

## Commands

| Invocation | Behavior |
|---|---|
| `$tao <goal>` | Apply the complexity gate and initialize a Project Lead only for suitable work |
| `$tao continue worker-1` | Continue a bounded Worker from repository state |
| `$tao continue reviewer-1` | Continue an explicitly assigned review |
| `$tao status` | Summarize machine/role state and point to the Owner report |
| `$tao continue lead` | Cold-start or resynchronize any Lead from repository state alone |

Simple, local, low-risk edits are completed directly without creating orchestration state.

## Runtime state

```text
.tiered-agent/
├── STATE.json
├── PLAN.md
├── OWNER_DIRECTIVES.md
├── HANDOFF.md
├── OWNER_STATUS.md
├── inbox/owner/<event-id>.md
├── history/completion-<revision>/
│   └── complete global, Worker, and Review snapshot
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
    └── history/review-<revision>/
```

`STATE.json` is deliberately small and never stores chat transcripts, hidden reasoning, secrets, command logs, or model names. `PLAN.md` is the stable source for the final goal, completion criteria, decisions, constraints, milestones, allocation, and validation strategy. `OWNER_DIRECTIVES.md` contains current authoritative Owner direction. Worker/Reviewer files contain scoped technical evidence. `HANDOFF.md` is the compact Lead cold-start packet. `OWNER_STATUS.md` is a derived, plain-language Owner report and never overrides canonical state.

Record each fact once in its canonical file. Summaries compress and point to detail instead of copying it. Update them only at meaningful transitions.

Global state, the plan, directives, assignments, and assignment archives have one writer: PROJECT_LEAD. Each Worker owns only its declared code scope, current status, blocker, and uniquely named Owner-feedback events. After completion, only the Lead's reassignment transaction may archive those files and reset the Worker to `ready`.

## State helper

Python 3.9+ is the only runtime dependency. The helper uses the standard library. Initialization never overwrites existing state; reopen snapshots completed projects; reassignment and review assignment preserve prior evidence. Existing recovery behavior remains an internal compatibility detail rather than something Agents should inspect during ordinary work.

```console
python scripts/statectl.py init --project-root /path/to/project --project-id my-project --profile generic
python scripts/statectl.py add-worker --project-root /path/to/project --worker-id worker-1 --objective "Implement the parser" --allowed-scope "src/parser/**" --completion-criterion "Parser tests pass"
python scripts/statectl.py reopen-project --project-root /path/to/project --reason "Owner requested a correction" --milestone "M2 correction"
python scripts/statectl.py reassign-worker --project-root /path/to/project --worker-id worker-1 --milestone "M2" --objective "Integrate the parser" --allowed-scope "src/integration/**" --completion-criterion "Integration tests pass"
python scripts/statectl.py resolve-owner-feedback --project-root /path/to/project --event-id <event-id> --resolution "Integrated into M2"
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

Completed state is frozen but reopenable. The Lead answers read-only follow-ups without mutation. For actionable work it snapshots the prior completion, reopens explicitly, and reuses the original Worker. Owner-event status is parsed only from frontmatter, so verbatim text cannot forge a pending event.

Escalation is evidence-based, not “three failures means stop.” A Worker continues while each attempt tests a distinct hypothesis and stops when it is repeating the same failure class without new evidence.

## Sufficient reliability, not defensive theater

> **Prefer the simplest mechanism that is sufficiently reliable for the actual failure modes of the project.**

TAO defaults to simple repository files, atomic replacement for machine-written state, basic schema/reference/ownership checks, and targeted rereading after a real error. It does not ask Agents to add hashes, checksum trees, freshness markers, nested gates, periodic audits, or recovery-of-recovery logic for theoretical edge cases. Extra protection is justified only by a concrete, materially harmful failure whose expected benefit clearly exceeds code complexity, maintenance, context, and token cost.

The Lead does not proactively run repository-wide audits, security sweeps, or consistency scans. Without evidence of a problem, it spends the budget advancing the Owner's actual deliverable.

## Review policy

Low-risk, well-validated work can finish without a separate review. Medium or large changes normally use a balanced Reviewer. A strong Reviewer is reserved for high-risk, core algorithm, architecture, security, or multi-Worker integration work.

Changing reviewed code invalidates the old approval. TAO retains the evidence, requires a replacement review, and archives the old review when the new assignment is published.

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

The test suite covers initialization, completed-project reopen/history, schema and path safety, reusable Workers, dependency and write-scope conflicts, stale-review prevention, verbatim Owner feedback, zero-chat Lead takeover, Owner-status lifecycle, simplest-sufficient reliability, explicit activation/model-routing contracts, all behavior contracts, and benchmark attribution/aggregation.

## Compatibility and current limitations

- Requires conversations to share a writable repository.
- The Owner manually opens model-specific top-level conversations in v1.
- Repository state can resume a formal Worker after a lost host conversation, but TAO cannot resurrect the host conversation object itself.
- Existing schema-v1 runtimes remain valid without `OWNER_STATUS.md`; the Lead creates it at the next meaningful transition. No migration framework or status hash is required.
- Existing internal crash-recovery behavior remains supported, but normal Agents neither inspect it nor add more recovery layers unless a concrete validation error points there.
- Model and reasoning labels vary across hosts; use the generic profile when needed. Owner-created conversations never gate continuation on reasoning labels.
- Native effective metadata proves native routing, not billing. Manual routing is Owner-controlled. Token and credit attribution must come from host per-model/per-conversation telemetry or documented manual measurements; otherwise it remains unknown.
- SkillsMP independently scans public GitHub repositories on its own schedule; repository publication cannot guarantee immediate indexing.

This structure follows the [Agent Skills specification](https://agentskills.io/specification) and [official OpenAI documentation for building skills](https://learn.chatgpt.com/docs/build-skills). The current OpenAI mapping follows [official model guidance](https://learn.chatgpt.com/docs/models).

## Uninstall

Remove the installed Skill directory from the agent's skill location. Project runtime state is separate; delete `.tiered-agent/` from an individual project only when you intentionally want to discard its orchestration history.

## License

Apache-2.0. See [LICENSE](LICENSE).
