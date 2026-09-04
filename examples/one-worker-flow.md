# One-Worker Handoff

This example shows the user-facing flow, not a transcript that agents must copy.

1. The Owner opens a strong Project Lead conversation and says:

   > `$tao Build the repository's new import pipeline, migrate current callers, and run the integration suite.`

2. The Lead inspects the project, initializes `.tiered-agent`, writes the plan, and assigns `worker-1`.

3. Native dispatch is used only if the host accepts explicit routing and returns machine-readable actual/effective model and reasoning metadata. The Lead requests `model: gpt-5.6-luna` and `reasoning_effort: xhigh`, then requires both returned values to match. Acceptance or echoed arguments alone are insufficient; missing or contradictory evidence fails closed before substantive work. The Worker never recursively self-verifies a native route. When manual fallback is required, the Lead tells the Owner:

   > Open `gpt-5.6-luna` (xhigh recommended), create one economy Worker conversation, and send:
   >
   > `$tao continue worker-1`

   In this Owner-created conversation, only a clearly visible model family is checked. Reasoning is never validated or gated: Luna/high, Luna/极高, and any other Luna reasoning setting continue. If the Agent cannot see the model indicator, it continues `worker-1` without asking the Owner to inspect a selector, resend the command, or open another Worker. A clearly wrong model gets one concise correction for the same conversation. Token or credit attribution remains unknown without host per-model/per-conversation telemetry or a documented manual measurement.

4. The Worker reads its repository assignment, implements and validates milestone M1, and marks its assignment `completed`.

5. The Owner returns to the original Lead conversation and says `continue`.

6. The Lead archives M1 and reassigns milestone M2 to the same `worker-1`. No new Worker ID or conversation is created.

7. The Owner returns to the original Worker conversation and sends:

   > `$tao continue worker-1`

8. For management status, the Owner returns to the original Lead conversation and sends:

   > `$tao status`

   The concise human report is `.tiered-agent/OWNER_STATUS.md`; it changes only when the Owner-visible project picture changes.

9. If that Lead conversation or even the Codex account disappears, the Owner opens the repository in a new Lead conversation and sends:

   > `$tao continue lead`

   The Lead reads `STATE.json` and `HANDOFF.md` first, then only current directives, relevant stable plan sections, active role status, blockers, and pending Owner events. It never asks the Owner to reconstruct the chat.

10. After final completion, a read-only `$tao` question leaves the project complete. New actionable `$tao` feedback makes the Lead run `reopen-project`, archive the completion snapshot, and reassign the same `worker-1`; it never initializes a second project merely because the Owner requested a revision.

The Owner never copies the previous conversation. Without an explicit `$tao`, no orchestration state is read or changed—even if `.tiered-agent` already exists. After dispatch, the Lead may passively wait for an event but does not poll `STATUS.json` or duplicate the assignment; a timeout is not a milestone. `worker-2` is created only when a genuinely independent parallel task, distinct responsibility, or materially isolated context makes the extra conversation worth its cost. If the Worker blocks or repeats an identical Luna failure path, it records the evidence, stops, and escalates to Terra first before considering Sol. TAO prefers the simplest mechanism sufficiently reliable for a real failure mode and does not spend the project budget inventing defensive layers.
