# OpenAI Codex Profile

TAO v0.6.0 preserves the existing model mapping. Availability and routing support must be checked against the current host.

> **Use the cheapest model that is likely to complete the task correctly without costly rework.**

| Role | Model | Reasoning | Use |
|---|---|---|---|
| PROJECT_LEAD | `gpt-5.6-sol` | Extra High (`xhigh`) | Intent, architecture, major decisions, acceptance |
| WORKER | `gpt-5.6-luna` | Extra High (`xhigh`) | Bounded execution and validation |
| First escalation / REVIEWER | `gpt-5.6-terra` | `high` or `xhigh` | Luna capability gaps and ordinary independent review |
| SOL escalation | `gpt-5.6-sol` | `xhigh` | High-risk decisions or Terra remains insufficient |

[Host dispatch](../references/host-dispatch.md) is the single source for route and messaging rules. Native dispatch explicitly requests the profile's model and reasoning. For Codex task tools these fields are `model` and `thinking`; for subagent hosts they may be `model` and `reasoning_effort`. Effective metadata must establish both requested values before substantive work. Do not infer support from field names or success alone. Current desktop task tool contracts do not supply that attestation, so reuse Owner-created tasks.

Owner-created top-level Workers and Reviewers preserve their settings. Check only a clearly exposed model family; if unavailable, continue. Never gate manual reasoning: `5.6 Luna / high`, `5.6 Luna / 极高`, and other Luna reasoning settings all continue. For display only, `极高` = `xhigh` and `高` = `high`. Neither a selector nor an effective-route receipt proves billed credits or token savings.

Select one profile and reuse one long-lived Worker where suitable. Model recommendations do not themselves authorize new sidebar tasks or overrides of Owner-created conversations. This release does not change the Lead tier to a newer model merely because one is available.
