# OpenAI Codex Profile

This profile maps abstract orchestration roles to the current OpenAI Codex model family. For v0.3.0, model routing is a hard cost-control constraint: these are the required defaults when the host exposes the corresponding models.

| Role | Model | Reasoning | Use |
|---|---|---|---|
| PROJECT_LEAD | `gpt-5.6-sol` | High / Extra High (`xhigh`) | Ambiguous goals, architecture, task design, major blockers, final acceptance |
| WORKER | `gpt-5.6-luna` | High | Clear implementation, commands, environment checks, tests, routine debugging |
| WORKER, harder local reasoning | `gpt-5.6-luna` | High (raise only when needed) | Bounded but locally difficult work that does not need a new decision |
| REVIEWER | `gpt-5.6-terra` | High | Independent review for medium or large changes |
| REVIEWER, critical | `gpt-5.6-sol` | High | Only high-risk, architectural, algorithmic, security, or integration review |

## Native Worker dispatch

PROJECT_LEAD **MUST** explicitly pass `model: "gpt-5.6-luna"` and High reasoning when using a Codex native `spawn_agent` (or equivalent). The `model` argument MUST NOT be omitted: an omitted model can inherit Sol and defeats tiering. The subagent must be registered as one formal `worker-N` and obey the TAO task, scope, status, dependencies, ownership, and event-handoff protocol. Host multi-agent support does not authorize fan-out or automatic Worker creation.

If the host cannot reliably set that explicit model, PROJECT_LEAD MUST NOT spawn a subagent. It must stop and tell the Owner:

```text
Open gpt-5.6-luna / High
$tao continue worker-1
```

The Owner manually creates or selects that top-level Worker conversation. This fallback is intentional: TAO must not create a Worker that silently inherits the strong Project Lead model merely to appear automated.

The Owner manually creates or selects top-level conversations when native explicit model dispatch is unavailable. The Skill must not assume it can switch a conversation model. PROJECT_LEAD remains on Sol; Workers remain on Luna; ordinary Reviewers remain on Terra or another lower-cost balanced model.

Prefer one long-lived Project Lead conversation and one conversation per active Worker. Reuse those conversations through repository state rather than repeatedly switching models in one chat. A completed assignment is reassigned to the same Worker where suitable; a milestone change never implies `worker-2`.

These mappings were checked against [official OpenAI model guidance](https://learn.chatgpt.com/docs/models). If availability changes, update this profile without changing the orchestration protocol.
