# OpenAI Codex Profile

This profile maps abstract orchestration roles to the current OpenAI Codex model family. It is a recommendation, not a core protocol dependency.

| Role | Model | Reasoning | Use |
|---|---|---|---|
| PROJECT_LEAD | `gpt-5.6-sol` | Extra High / `xhigh` | Ambiguous goals, architecture, task design, major blockers |
| WORKER | `gpt-5.6-luna` | High | Clear implementation, commands, tests, routine debugging |
| WORKER, harder local reasoning | `gpt-5.6-luna` | Extra High / `xhigh` | Bounded but locally difficult work that does not need a new decision |
| REVIEWER | `gpt-5.6-terra` | High | Independent review for medium or large changes |
| REVIEWER, critical | `gpt-5.6-sol` | High | High-risk, architectural, algorithmic, or multi-Worker integration review |

The Owner manually creates or selects top-level conversations. The Skill must not assume it can switch the conversation model or create model-specific conversations automatically.

Prefer one long-lived Project Lead conversation and one conversation per active Worker. Reuse those conversations through repository state rather than repeatedly switching models in one chat.

These mappings were checked against [official OpenAI model guidance](https://learn.chatgpt.com/docs/models). If availability changes, update this profile without changing the orchestration protocol.
