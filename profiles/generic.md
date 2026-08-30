# Generic Model Profile

Map the host's available models by capability and cost rather than by vendor name.

| Abstract tier | Selection criteria | Default role |
|---|---|---|
| `strong` | Best available ambiguity handling, architecture judgment, and correction ability | PROJECT_LEAD |
| `balanced` | Strong tool use and review quality at materially lower cost than the frontier model | REVIEWER |
| `economy` | Lowest-cost model that reliably follows a bounded task and validates its work | WORKER |

Choose the lowest reasoning effort that reliably completes the role:

- Lead: high enough for ambiguous, cross-module decisions.
- Worker: moderate or high for clear execution; increase only for bounded local difficulty.
- Reviewer: high enough to inspect evidence and detect integration risks.

Record the selected profile name in `STATE.json`, but do not store provider credentials or concrete model names there. Keep concrete mappings in a local profile document so model changes do not alter the protocol.
