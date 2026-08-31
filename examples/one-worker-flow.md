# One-Worker Handoff

This example shows the user-facing flow, not a transcript that agents must copy.

1. The Owner opens a strong Project Lead conversation and says:

   > `$tao Build the repository's new import pipeline, migrate current callers, and run the integration suite.`

2. The Lead inspects the project, initializes `.tiered-agent`, writes the plan, and assigns `worker-1`.

3. If native dispatch can explicitly select a model, the Lead dispatches the formal Worker with `model: gpt-5.6-luna` and `reasoning_effort: xhigh`. Successful acceptance by a structured host API whose contract guarantees those overrides is routing evidence; stronger actual/effective metadata must agree. Unsupported or contradictory routing fails closed. The Worker never recursively self-verifies a host-confirmed route. When manual fallback is required, the Lead tells the Owner:

   > Open `gpt-5.6-luna / xhigh`, create one economy Worker conversation, and send:
   >
   > `$tao continue worker-1`

   In the manual conversation, the host's current model selector is evidence. `5.6 Luna / 极高` means Luna/xhigh and passes; `极高` must never be guessed or reported as `high`. If the same conversation is Luna/high, switch that conversation to xhigh and continue it instead of opening another Worker.

4. The Worker reads its repository assignment, implements and validates milestone M1, and marks its assignment `completed`.

5. The Owner returns to the original Lead conversation and says `continue`.

6. The Lead archives M1 and reassigns milestone M2 to the same `worker-1`. No new Worker ID or conversation is created.

7. The Owner returns to the original Worker conversation and sends:

   > `$tao continue worker-1`

8. For management status, the Owner returns to the original Lead conversation and sends:

   > `$tao status`

9. After final completion, a read-only `$tao` question leaves the project complete. New actionable `$tao` feedback makes the Lead run `reopen-project`, archive the completion snapshot, and reassign the same `worker-1`; it never initializes a second project merely because the Owner requested a revision.

The Owner never copies the previous conversation. Without an explicit `$tao`, no orchestration state is read or changed—even if `.tiered-agent` already exists. After dispatch, the Lead may passively wait for an event but does not poll `STATUS.json` or duplicate the assignment; a timeout is not a milestone. `worker-2` is created only when a genuinely independent parallel task, distinct responsibility, or materially isolated context makes the extra conversation worth its cost. If the Worker blocks or repeats an identical Luna failure path, it records the evidence, stops, and escalates to Terra first before considering Sol.
