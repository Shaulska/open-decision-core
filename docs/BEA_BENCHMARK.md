# BEA vintage replay: controlled real-data case study (v0.2)

## Question
Can a declared decision use a particular version of a previously observed value at the specified cutoff? This demonstration is a temporal audit, not a forecasting backtest. The dates of decisions and their choice of version are constructed test cases; no actual historical decision is alleged.

## Source and rights
Source: U.S. Bureau of Economic Analysis. Six archived 2024 GDP news releases were manually transcribed; each headline value, release number, date and source link is included in `examples/bea/releases.json`. BEA's [reuse policy](https://www.bea.gov/help/faq/147) states its information is public domain unless otherwise noted. Only six numerical estimates and factual metadata are reproduced; no logo or endorsement. Q1 and Q2 2024 are the fixed scope; this is not the full vintage history (including later annual revisions). The selected release headers state 08:30 EDT. We normalize the stated minute to `08:30:00-04:00` for the existing timestamp contract, not as observed second-level availability. Event time is the represented quarter's end, not a claim of an instantaneous economic measurement. All constructed decisions are at noon EDT on the day after the chosen release, avoiding sub-minute ordering claims. The provider publication timestamp is an explicitly declared proxy, never evidence of actual local receipt; `received_at` is null. No retrospective timestamp is claimed as locally captured.

## Design
For each quarter, choose each of the three cutoff releases and test each of the three exact evidence versions (18 provider-proxy cases). Expected result: selected release at or before cutoff stage => PASS; later release => BLOCK. Separately, require historical local receipt for the matching version after each cutoff (six cases): expected UNVERIFIED. Expected labels follow the predetermined stage ordering, not the auditor outputs. A case with equal 3.0 values from Q2 second/third estimates demonstrates that identical values do not make a future version admissible.

## Reproduction
From the repository root with Python 3.10+:

```sh
python -m odc.benchmark examples/bea/releases.json -o examples/bea/results.json
python -m odc.demo examples/bea/releases.json -o examples/bea/index.html
python -m unittest discover -s tests -v
```

Open the generated HTML locally; controls select actual precomputed Python receipts and display exact evidence versions. Export includes the bundle and receipt; preserve Python JSON numeric representation (3.0 versus 3). To verify, load the export using Python and call `odc.verify(export['bundle'], export['receipt'])`. The data is not submitted anywhere. The checked-in artifacts are tested for deterministic reproduction.

## Result and limitations
24/24 expected outcomes matched (12 PASS, 6 BLOCK, 6 UNVERIFIED). Six releases, 24 correlated designed cases, not 24 independent data observations. This does not estimate general sensitivity/specificity, predictive benefit, real-world event timing, or authenticity. There is no fitting, model selection, accuracy comparison or independent holdout. A PASS is consistency with supplied release metadata under the policy only. Independent source authentication and larger external benchmarks remain future work.
