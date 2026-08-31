# Escalation and Review

Read this reference when a Worker encounters a blocker, receives Owner feedback, or when the Project Lead decides whether review is justified.

## Local correction or Lead decision

A Worker may apply Owner feedback directly only when all are true:

1. the requested change is unambiguous;
2. the scope is bounded;
3. it preserves the final goal;
4. it does not revise a core architecture decision;
5. it requires no hidden-intent inference;
6. the Worker can validate it safely inside its assignment.

Otherwise preserve the Owner's exact words in the inbox, stop conflicting work, update the Worker status, and ask the Owner to return to the original Project Lead conversation.

Completed projects use a different gate: read-only questions are answered without mutation, while actionable work is preserved by `reopen-project` and its completion snapshot. A completed Worker must not create an inbox event inside frozen completed state.

## Escalation signals

Escalate when one or more are true:

- the same failure class is repeating without new evidence;
- the Worker lacks a root-cause model and is guessing;
- the proposed fix crosses `allowed_scope` or contradicts the plan;
- progress requires a new architecture or cross-module decision;
- active Workers have conflicting ownership;
- risk is expanding or a destructive/external action needs authority;
- the Owner feedback is directional, aesthetic, strategic, or otherwise ambiguous.

There is no fixed retry count. Continue while each attempt tests a distinct evidence-based hypothesis; stop when attempts become repetitive.

## Blocker record

`BLOCKER.md` must contain:

- concise blocker summary;
- observable evidence and reproduction steps;
- distinct approaches already attempted and what each taught;
- current safe repository state;
- exact decision or missing input required;
- work that can continue independently, if any.

Do not paste full terminal history. Include only the smallest log excerpt needed to reproduce or decide.

After writing it, set the Worker's status to `blocked` and tell the Owner:

> Return to the original Project Lead conversation and send: continue handling the current blocker. You do not need to copy any context.

## Review gate

Skip a separate review when a bounded Worker change has strong automated validation and low impact.

Use balanced review for medium or large changes whose correctness benefits from an independent pass. Use strong review only for:

- high-risk or security-sensitive changes;
- core algorithms or difficult architecture;
- multi-Worker integration;
- evidence that the plan itself may be wrong.

Review findings need file or test evidence. The Reviewer may approve, request bounded corrections, or escalate a decision. It must not silently redesign the project.

Any implementation change after a completed review makes that approval stale. Reassignment detaches the old reviewer while retaining the review requirement. The next review assignment archives the completed evidence, and project completion remains blocked until the replacement review finishes.
