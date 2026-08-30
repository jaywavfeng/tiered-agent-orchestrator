# One-Worker Handoff

This example shows the user-facing flow, not a transcript that agents must copy.

1. The Owner opens a strong Project Lead conversation and says:

   > Build the repository's new import pipeline, migrate current callers, and run the integration suite.

2. The Lead inspects the project, initializes `.tiered-agent`, writes the plan, and assigns `worker-1`.

3. The Lead tells the Owner:

   > Create one economy Worker conversation and send:
   >
   > `$tiered-agent-orchestrator continue worker-1`

4. The Worker reads its repository assignment, implements and validates it, and updates its own status.

5. The Owner returns to the original Lead conversation and sends:

   > `$tiered-agent-orchestrator status`

The Owner never copies the previous conversation. If the Worker blocks, it records the evidence in its own blocker file and sends the Owner back to the same Lead conversation.
