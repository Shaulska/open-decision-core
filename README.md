# Open Decision Core

**Could you have known it then?**

A local-first toolkit for checking whether the evidence behind an AI or ML decision was available at its declared cutoff. Open Decision Core audits exact versions, lineage and historical split manifests, then produces deterministic, reproducible receipts.

**MVP v0.3.0** · Python 3.10+ · No runtime dependencies · No API keys

[Project website (local preview)](site/index.html) · [Interactive BEA demo](examples/bea/index.html) · [Evidence contract](docs/CONTRACT.md) · [Roadmap](docs/ROADMAP.md)

## Why it matters

An event date is not the date its data became available. A revised value may accidentally enter a historical backtest, even when the original event happened earlier. Open Decision Core makes the version and availability assumptions explicit, and rejects known violations rather than silently using the latest data.

| Verdict | Meaning |
|---|---|
| PASS | No finding under the implemented declared-evidence contract |
| BLOCK | A concrete contract violation |
| UNVERIFIED | Missing, unsupported or insufficiently precise evidence |

## Try it in one minute

From a checkout of the repository:

```sh
python -m odc audit examples/timely.json
python -m odc audit examples/future-revision.json
python -m odc audit examples/unknown.json
python -m odc verify examples/demo.json examples/demo.receipt.json
```

The first three commands demonstrate PASS, BLOCK and UNVERIFIED respectively. Exit codes: 0, 2, 3; malformed input or operational errors return 4. An optional local install is `python -m pip install .` (build tools required).

Python SDK:

```python
import json
from pathlib import Path
from odc import audit, verify

bundle = json.loads(Path('examples/timely.json').read_text())
receipt = audit(bundle)
assert verify(bundle, receipt)
print(receipt['status'])
```

Other commands: `python -m odc replay examples/demo.json timely`, `python -m odc report examples/demo.json -o report.html`, and `python -m odc split-check manifest.json`. See the contract for input format. Receipt policy `temporal-evidence-v0.3` is versioned; use the original version to verify older receipts.

## Real-data case study

Six archived U.S. Bureau of Economic Analysis GDP releases (2024 Q1/Q2), manually transcribed with source links. A fixed matrix of 24 designed scenarios exercises version availability and the absence of historical local-receipt evidence. Results: 12 PASS, 6 BLOCK, 6 UNVERIFIED; all 24 matched expected verdicts. These are correlated controlled cases, not an independent estimate of accuracy.

Open `site/index.html` locally to explore the project and replay cases. The interface selects actual Python-generated receipts, exports the bundle and receipt, and makes no network requests except links you choose to open. It does not run arbitrary audits in the browser.

```sh
python -m odc.benchmark examples/bea/releases.json -o examples/bea/results.json
python -m odc.demo examples/bea/releases.json -o examples/bea/index.html
python site/build.py
python -m unittest discover -s tests -v
```

Read the [methodology and limitations](docs/BEA_BENCHMARK.md).

## Ecosystem

| Layer | Status | Purpose |
|---|---|---|
| Temporal Audit | Implemented MVP | Exact-version evidence, cutoff and lineage checks, receipts, split audit |
| Decision Policy | Planned | Empirically evaluate risk, abstention and human review policies |
| Research Lab | Planned | Independent outcome evaluation, calibration and reproducible research |

## Trust boundaries

PASS is not proof of source truth, historical existence, predictive accuracy, security or authorization. Provider publication times are proxies, not actual local receipt. Minute-level proxies have conservative interval semantics; unsupported precision is unverified. Hashes detect differences from retained originals, not malicious replacement of both input and receipt. Split checks only inspect declared manifests. Use trusted local inputs; do not expose the preview as an unauthenticated upload endpoint.

## Contributing and release status

[Contributing](CONTRIBUTING.md) · [Security and limitations](SECURITY.md) · [Release audit](docs/RELEASE_AUDIT.md) · [Launch checklist](docs/LAUNCH_CHECKLIST.md)

The project code and original documentation are licensed under [Apache-2.0](LICENSE). See [NOTICE](NOTICE) for data attribution. This is an experimental MVP, not a production security guarantee. External adoption and independent validation are not established. Package name remains provisional; not published on PyPI. For reproducible feedback, open a [GitHub issue](https://github.com/Shaulska/open-decision-core/issues/new).
