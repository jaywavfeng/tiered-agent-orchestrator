# One reusable Worker, two assignments

This example assumes an Owner-authorized Lead and Worker bound to the same directory. It uses host messaging, not a background Python service. The actual executable/script path comes from the installed skill; run all subcommands through Python.

1. Lead initializes state, writes the plan, registers `worker-1`, and sets active execution. Bind `lead` and `worker-1` using final host task IDs and Owner selection evidence. Keep the Owner's manual model/reasoning settings.
2. Read the idle Worker's host metadata once and save the normalized observation. Generate `dispatch-context`, reserve `pending` with `record-dispatch`, send the returned prompt via `send_message_to_thread`, then record confirmed `sent` or an accurate failure/unknown result.
3. Worker starts with the explicit CLI invocation below (replace paths), validates the current revision and scope, implements and validates M1, then records completed status with that revision. Generate `notification-context` and send one callback to the bound Lead.
4. Lead checks actual results and acceptance, then uses `reassign-worker` to archive M1 and publish M2 as revision 2. Repeat dispatch to the same host task. A late revision-1 message fails the context/status guard and does not execute M2 accidentally.
5. After M2, Lead performs substantive acceptance and any required review, marks the project complete, and updates handoff/human report once. A completed project answers status without mutation; actionable later work uses `reopen-project` then the same Worker.

```powershell
& "<absolute python.exe>" "<absolute skill directory>\scripts\statectl.py" context --project-root "<project directory>" --role worker-1 --assignment-revision 1
```

For a missing binding/tool, manually continue `$tao continue worker-1`, then `$tao continue lead`. For missing native actual/effective metadata, do not create a speculative Worker. For uncertain message delivery, reconcile once; lack of a message in a bounded history page does not prove failure. A timeout is not a milestone; end an unchanged wait without polling.

Scope/acceptance files, not chat replies, determine the result. See [host dispatch](../references/host-dispatch.md) for argument and normalized receipt details. The synthetic two-assignment acceptance test is `tests/test_relay.py`; it is not a live host run.
