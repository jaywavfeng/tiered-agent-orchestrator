# Benchmark Protocol

Status: **Benchmark pending.**

No savings claim belongs in the project README until paired runs exist.

Compare the same task under two strategies:

- `strong-only`: one strong model performs the whole task.
- `tiered`: strong Project Lead, economy Worker or Workers, and optional balanced or strong review.

Record one JSON object per line using `schemas/benchmark-run.schema.json`. Schema v2 requires an attributable `measurement_source` and non-empty `measurement_evidence`. Use host per-model telemetry or a documented per-conversation manual measurement; aggregate account usage, a requested model, a selector screenshot without usage, or intuition cannot establish per-tier token/credit attribution.

Schema v2 also records `credits_used` separately from optional monetary `estimated_cost`; use `null` when the host does not expose either value rather than estimating it.

Required measures are task success, test pass rate, total and per-tier tokens, optional estimated cost or credits, completion time, model switches, Worker conversations, escalations, and Owner interventions.

Validate and aggregate:

```console
python scripts/benchmark.py validate benchmarks/runs.jsonl
python scripts/benchmark.py aggregate benchmarks/runs.jsonl --output benchmarks/summary.json
```

Only compare task IDs that have both strategies. Publish raw records and measurement notes with any future aggregate result.
