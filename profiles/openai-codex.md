# OpenAI Codex Profile

This profile maps abstract orchestration roles to the current OpenAI Codex model family. For v0.5.0, model routing is a hard completion-value constraint: use the cheapest model likely to finish correctly without costly rework. These are the required defaults when the host exposes the corresponding models.

> **Use the cheapest model that is likely to complete the task correctly without costly rework.**

| Role | Model | Reasoning | Use |
|---|---|---|---|
| PROJECT_LEAD | `gpt-5.6-sol` | Extra High (`xhigh`) | Ambiguous goals, architecture, major decisions, high-risk blockers, final acceptance |
| WORKER | `gpt-5.6-luna` | Extra High (`xhigh`) | Default for clear implementation, commands, environment checks, tests, and routine debugging; avoid under-reasoning that causes rework |
| ESCALATED WORKER / REVIEWER | `gpt-5.6-terra` | High or Extra High (`high` / `xhigh`) | First escalation for a Luna capability gap and ordinary independent review |
| SOL escalation | `gpt-5.6-sol` | Extra High (`xhigh`) | Architecture, major decisions, high-risk blockers, or Terra remains insufficient |

## Native Worker dispatch

PROJECT_LEAD **MUST** explicitly pass `model: "gpt-5.6-luna"` and `reasoning_effort: "xhigh"` (or the host's equivalent xhigh field) when using a Codex native `spawn_agent` (or equivalent). The `model` argument MUST NOT be omitted: an omitted model can inherit Sol and defeats tiering. The subagent must be registered as one formal `worker-N` and obey the TAO task, scope, status, dependencies, ownership, and event-handoff protocol. Host multi-agent support does not authorize fan-out or automatic Worker creation.

Before using native dispatch, confirm that the host returns machine-readable actual/effective model **and** reasoning metadata for the created runtime. After dispatch, both returned values must match `gpt-5.6-luna / xhigh`. Successful acceptance, echoed request arguments, a success flag, or a free-form nickname is not evidence. If the host contract exposes only requested overrides, if the result omits effective metadata, or if any returned value contradicts the request, stop before substantive work and use the manual fallback. The Worker must not recursively introspect or self-prove its model; native proof belongs to the Lead and the host receipt.

If the host cannot reliably set that explicit model, PROJECT_LEAD MUST NOT spawn a subagent. It must stop and tell the Owner:

```text
Open gpt-5.6-luna (xhigh recommended)
$tao continue worker-1
```

## Owner-created top-level Worker or Reviewer

The manual path is not a weaker form of native attestation; it is an Owner-controlled trust boundary. Check only the model family, and only when the host clearly exposes it to the Agent. If the indicator clearly shows Luna for an ordinary Worker (or Terra for a manual escalated Worker/Reviewer), continue the existing assignment. If it is unavailable, continue without asking the Owner to inspect the selector, resend `$tao continue worker-N`, create another conversation, or provide independent proof. A clearly visible wrong model gets one brief instruction to switch the same conversation; preserve the formal assignment and never recurse into verification.

Never inspect, validate, correct, or gate the reasoning level of an Owner-created conversation. `5.6 Luna / high`, `5.6 Luna / 极高`, and Luna with any other reasoning setting all continue. For display terminology only, `极高` = `xhigh` and `高` = `high`; this mapping is not a manual routing requirement. The recommended creation setting remains xhigh because it usually avoids rework, but the Owner's manual selection is authoritative.

Routing and billing are different claims. Native effective metadata proves a native route; an Owner controls a manual route, optionally supported by a visible model indicator. Neither certifies how the account was charged. Attribute tokens or credits to Luna only when the host exposes per-model/per-conversation usage telemetry or the Owner records a documented manual measurement; otherwise record attribution as unknown. In particular, a native subagent result without effective route metadata or separately attributable usage is not valid evidence for a Luna savings claim.

This fallback is intentional: TAO must not create a Worker that silently inherits the strong Project Lead model merely to appear automated, and it must not trap a manual Worker in a selector-inspection, command-resend, or “open another verified Worker” loop.

The Owner manually creates or selects top-level conversations when native explicit model dispatch or runtime confirmation is unavailable. The Skill must not assume it can switch a conversation model. PROJECT_LEAD remains on Sol; Luna/xhigh is the recommended ordinary Worker configuration; Terra/high or xhigh is recommended for escalated Workers and ordinary Reviewers; Sol is reserved for the listed high-value escalations. Native Terra Workers and Reviewers must pass the same effective-model/reasoning attestation gate. Owner-created Terra conversations use the manual model-only, reasoning-agnostic rule above.

Prefer one long-lived Project Lead conversation and one conversation per active Worker. Reuse those conversations through repository state rather than repeatedly switching models in one chat. A completed assignment is reassigned to the same Worker where suitable; a milestone change never implies `worker-2`. Do not retry an identical Luna failure path without new evidence; escalate to Terra first.

These mappings were checked against [official OpenAI model guidance](https://learn.chatgpt.com/docs/models). If availability changes, update this profile without changing the orchestration protocol.
