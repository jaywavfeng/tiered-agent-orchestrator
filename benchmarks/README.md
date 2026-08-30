# Benchmark Protocol

Status: **Benchmark pending.**

No savings claim belongs in the project README until paired runs exist.

Compare the same task under two strategies:

- `strong-only`: one strong model performs the whole task.
- `tiered`: strong Project Lead, economy Worker or Workers, and optional balanced or strong review.

Record one JSON object per line using `schemas/benchmark-run.schema.json`. Capture values from host telemetry or a documented manual measurement; never estimate missing token counts by intuition.

Required measures are task success, test pass rate, total and per-tier tokens, optional estimated cost or credits, completion time, model switches, Worker conversations, escalations, and Owner interventions.

Validate and aggregate:

```console
python scripts/benchmark.py validate benchmarks/runs.jsonl
python scripts/benchmark.py aggregate benchmarks/runs.jsonl --output benchmarks/summary.json
```

Only compare task IDs that have both strategies. Publish raw records and measurement notes with any future aggregate result.
