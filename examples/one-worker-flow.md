# One-Worker Handoff

This example shows the user-facing flow, not a transcript that agents must copy.

1. The Owner opens a strong Project Lead conversation and says:

   > Build the repository's new import pipeline, migrate current callers, and run the integration suite.

2. The Lead inspects the project, initializes `.tiered-agent`, writes the plan, and assigns `worker-1`.

3. If native dispatch can explicitly select a model, the Lead dispatches the formal Worker with `model: gpt-5.6-luna` and High reasoning. Otherwise the Lead stops and tells the Owner:

   > Open `gpt-5.6-luna / High`, create one economy Worker conversation, and send:
   >
   > `$tao continue worker-1`

4. The Worker reads its repository assignment, implements and validates milestone M1, and marks its assignment `completed`.

5. The Owner returns to the original Lead conversation and says `continue`.

6. The Lead archives M1 and reassigns milestone M2 to the same `worker-1`. No new Worker ID or conversation is created.

7. The Owner returns to the original Worker conversation and sends:

   > `$tao continue worker-1`

8. For management status, the Owner returns to the original Lead conversation and sends:

   > `$tao status`

The Owner never copies the previous conversation. After dispatch, the Lead does not poll `STATUS.json` or duplicate the assignment; it waits for an event or Owner return. `worker-2` is created only when a genuinely independent parallel task, distinct responsibility, or materially isolated context makes the extra conversation worth its cost. If the Worker blocks, it records the evidence in its own blocker file and sends the Owner back to the same Lead conversation.
