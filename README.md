# Open Decision Core · MVP preview

**Can the evidence behind a decision be shown to have been available when the decision was made?**

A local-first Python toolkit for auditing declared time-aware evidence, replaying exact versions, and detecting inconsistent historical evaluation manifests. Experimental release 0.1.0; name provisional. No LLM, network access, paid API, or external actions are needed.

## Quick start (Python 3.10+)

```sh
python -m odc audit examples/timely.json
python -m odc audit examples/future-revision.json
python -m odc audit examples/unknown.json
python -m odc replay examples/demo.json timely
python -m odc verify examples/demo.json examples/demo.receipt.json
python -m odc report examples/demo.json -o report.html
python -m unittest discover -s tests -v
```

Open `examples/demo.html` in a browser for an already-generated audit. `BLOCK` and `UNVERIFIED` deliberately return non-zero exit codes. The three examples are **synthetic** and do not prove real-world predictive performance.

| Code | Meaning |
|---|---|
| 0 | PASS: no finding under implemented declared-contract checks |
| 2 | BLOCK: concrete contract violation |
| 3 | UNVERIFIED: missing/unsupported evidence |
| 4 | Malformed input or operational error |

## Architecture

- **Core**: evidence/decision contract, exact-version identifiers, deterministic SHA-256 receipts.
- **Temporal auditor**: current MVP; timestamp order, late source/version, lineage, unknown evidence and split manifest checks.
- **Policy engine**: future selective decisions and risk/coverage evaluation; not implemented.
- **Research Lab**: future model and policy evaluation; currently a static HTML audit report only.

The audit is independent of the upstream predictor. A PASS is not an endorsement, a security guarantee, proof of source truth, or permission to execute an action. Hashes detect changes relative to a retained receipt, not a malicious party able to replace both input and receipt. Explicit timestamps can be false; provider publication time is a proxy, not historical local receipt.

## Contract and limits

See [contract](docs/CONTRACT.md), [roadmap](docs/ROADMAP.md), and [security](SECURITY.md). All inputs are local JSON; no code execution or external network requests. The initial split audit only handles explicit train/test manifests and is not a universal leakage detector. Day-level evidence is UNVERIFIED. This preview is intended for private review before a public release. Licensing and final package naming pending owner review.
