# Lead Coordination

Read for first planning or changes to project direction, not on every Worker continuation.

> **Use the cheapest model that is likely to complete the task correctly without costly rework.**

## Decide, assign, accept

The Lead distills intent and stable acceptance criteria into `PLAN.md`. Inspect only entrypoints or evidence needed for that decision. Resolve material unknowns, then delegate bounded execution. PROJECT_LEAD MUST NOT perform routine implementation, tests, SSH checks or `nvidia-smi`; small orchestration commands are permitted. Ask whether an action needs strong reasoning, not whether the Lead could execute it.

Default to one reusable Worker. A new Worker needs independent useful work, disjoint active write scope, named read dependencies and an integration path. Its benefit must exceed model/context/coordination costs. Completing M1 does not justify creating `worker-2`. Combine sequential small steps with the same context into one assignment.

Use the helper through the explicit Python invocation in [SKILL.md](../SKILL.md). The `add-worker` and `reassign-worker` subcommands accept objectives, scopes, dependencies and completion criteria; use their `--help` when needed. Avoid task descriptions such as "do tests" without observable acceptance. Only PROJECT_LEAD reassigns a completed Worker, archiving its old task/status/blocker and resetting the same identity to ready.

Persist the assignment before applying [host dispatch](host-dispatch.md). That is the single source for actual/effective model attestation, Owner-created routes, messaging and passive waits. No route or billing proof is inferred from successful request acceptance. The economy model must not silently inherit the Lead's model.

Completion is an evidence decision: inspect the relevant result and validation against criteria. A sent message, finished host task, screenshot or passing build alone is not completion. Balanced review is optional where it materially improves confidence; use [escalation and review](escalation-and-review.md) only when needed. Do not retry the same failure without new evidence; escalate the capability gap first to the configured lower-cost tier.

## Resume with no chat history

`$tao continue lead` uses the role context packet, then relevant directives/plan sections and active blockers/events. It must recover final goal, completed work, current position, verified results, durable constraints, blockers, next action and Owner decision. Repair a missing canonical fact at the relevant transition. Historical evidence and source code are read only for a specific discrepancy or decision.

Interpret ambiguous Owner events, write resulting durable direction, then resolve the event. A message does not override repository authority. A repeated or older Worker notification cannot reopen, reassign or accept a task a second time; compare its revision and current status/next action first.

Completed state is frozen for read-only requests. For actionable changes use `reopen-project` with the Owner's reason and a milestone; then `reassign-worker` for a suitable completed Worker. Neither the existence of `.tiered-agent` nor maintenance of TAO activates this protocol without explicit `$tao` invocation.

## Transition-sized reporting

Update a fact once in its canonical location. `HANDOFF.md` compresses the current takeover picture; `OWNER_STATUS.md` is optional human presentation. Neither is a running command log. Update summaries only when their audience's next action, outcome, risk or decision changes.

> **Prefer the simplest mechanism that is sufficiently reliable for the actual failure modes of the project.**

The coordination target is <= 10% of actual-task tokens, using attributable purpose measurements, not Lead-vs-Worker guesses. Without measurements report proxy changes, not savings. Remove repetitive reads, polling and updates before adding infrastructure. No speculative audit/recovery machinery while useful task work is ready.
