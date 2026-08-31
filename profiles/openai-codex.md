# OpenAI Codex Profile

This profile maps abstract orchestration roles to the current OpenAI Codex model family. For v0.4.0, model routing is a hard completion-value constraint: use the cheapest model likely to finish correctly without costly rework. These are the required defaults when the host exposes the corresponding models.

> **Use the cheapest model that is likely to complete the task correctly without costly rework.**

| Role | Model | Reasoning | Use |
|---|---|---|---|
| PROJECT_LEAD | `gpt-5.6-sol` | Extra High (`xhigh`) | Ambiguous goals, architecture, major decisions, high-risk blockers, final acceptance |
| WORKER | `gpt-5.6-luna` | Extra High (`xhigh`) | Default for clear implementation, commands, environment checks, tests, and routine debugging; avoid under-reasoning that causes rework |
| ESCALATED WORKER / REVIEWER | `gpt-5.6-terra` | High or Extra High (`high` / `xhigh`) | First escalation for a Luna capability gap and ordinary independent review |
| SOL escalation | `gpt-5.6-sol` | Extra High (`xhigh`) | Architecture, major decisions, high-risk blockers, or Terra remains insufficient |

## Native Worker dispatch

PROJECT_LEAD **MUST** explicitly pass `model: "gpt-5.6-luna"` and `reasoning_effort: "xhigh"` (or the host's equivalent xhigh field) when using a Codex native `spawn_agent` (or equivalent). The `model` argument MUST NOT be omitted: an omitted model can inherit Sol and defeats tiering. The subagent must be registered as one formal `worker-N` and obey the TAO task, scope, status, dependencies, ownership, and event-handoff protocol. Host multi-agent support does not authorize fan-out or automatic Worker creation.

After dispatch, verify the actual/effective route from the structured host receipt or stronger effective-model metadata. Successful acceptance is sufficient when the structured host tool contract guarantees the explicit `model` and `reasoning_effort` overrides. If the host rejects or cannot honor those fields, or returned effective metadata contradicts them, stop the Worker before more work and ask the Owner to open a manual `gpt-5.6-luna / xhigh` Worker with `$tao continue worker-N`. A free-form nickname is not evidence, but the Worker must not recursively introspect or re-prove a route already guaranteed by the host receipt.

If the host cannot reliably set that explicit model, PROJECT_LEAD MUST NOT spawn a subagent. It must stop and tell the Owner:

```text
Open gpt-5.6-luna / xhigh
$tao continue worker-1
```

The Owner manually creates or selects that top-level Worker conversation. Its host-owned current-conversation selector is the routing evidence; no second manual Worker or independent self-proof is required. The localized reasoning labels map exactly: `极高` = `xhigh`, while `高` = `high`. A selector showing `5.6 Luna / 极高` passes. Never report `极高` as `high`, and never guess an unread value. If the same conversation is on Luna/high, ask the Owner to switch that conversation to `极高`/xhigh and continue there.

This fallback is intentional: TAO must not create a Worker that silently inherits the strong Project Lead model merely to appear automated, and it must not trap a correctly configured manual Worker in an infinite “open another verified Worker” loop.

The Owner manually creates or selects top-level conversations when native explicit model dispatch or runtime confirmation is unavailable. The Skill must not assume it can switch a conversation model. PROJECT_LEAD remains on Sol; ordinary Workers remain on Luna/xhigh; escalated Workers and ordinary Reviewers use Terra/high or xhigh; Sol is reserved for the listed high-value escalations.

Prefer one long-lived Project Lead conversation and one conversation per active Worker. Reuse those conversations through repository state rather than repeatedly switching models in one chat. A completed assignment is reassigned to the same Worker where suitable; a milestone change never implies `worker-2`. Do not retry an identical Luna failure path without new evidence; escalate to Terra first.

These mappings were checked against [official OpenAI model guidance](https://learn.chatgpt.com/docs/models). If availability changes, update this profile without changing the orchestration protocol.
