# Release candidate audit · 0.3.0 · 2026-11-27

Historical record of the v0.3 candidate audit before owner approval. The owner later approved the project name, Apache-2.0 and public visibility; see LAUNCH_CHECKLIST.md for remaining actions.

Scope: author-side review of the standalone MVP, not an independent security certification. Baseline: v0.2 main commit 64559e59c8df2eccf51b59acb61d19be1a182a30; all 29 local baseline files matched the retained source manifest. No other repository was edited.

## Findings and remediation

| Finding | Resolution |
|---|---|
| Permissive ISO parser accepted ambiguous precision/offsets | explicit seconds and offset grammar; reject unknown offset and excessive fraction |
| Publication minute promoted to second-level evidence | MINUTE provider interval; within minute is unverified; BEA fixture now uses MINUTE |
| Missing lineage silently treated as empty | explicit missing-lineage finding; duplicate parents blocked |
| Deep/large graph could exhaust recursion | bounded audit traversal and input sizes; fail with operational error, never PASS |
| Replay malformed identifier could crash; repeated scanning | validated ID index and linear closure |
| Receipt equality conflated bool/int or int/float | compare canonical JSON digests |
| Nonfinite exponent in JSON | reject at input boundary |
| Incomplete split could hide a known violation | continue checking valid fields/rows, known violations dominate |

Policy changed to temporal-evidence-v0.3. All bundled receipts regenerated. Older receipts require the original policy/version. 53 local unit tests passed (including 100 seeded scenarios); BEA remains 24/24 designed cases. Wheel built without network or dependency resolution, installed into a fresh venv, invoked from outside repository. GitHub CI must pass before merge.

## Name, provenance and proposed license

Umbrella working name: Open Decision Core. Use descriptive module labels Temporal Audit, Decision Policy and Research Lab; avoid previously identified collisions with ChronoGuard and DecisionGuard. Distribution `open-decision-core-preview` and import `odc` are provisional; PyPI lookup did not establish availability, no trademark clearance claimed. Do not publish on PyPI yet.

Proposed Apache-2.0 text: [Apache-2.0 text now at repository root](../LICENSE), not yet a license grant. Owner must confirm ownership/right to license and approve moving text to root LICENSE before public release. No runtime third-party dependencies. Build/test tooling has its own licenses. The six BEA numerical facts and metadata are attributed; reuse terms at https://www.bea.gov/help/faq/147. Code was developed separately using architectural ideas; this review is not a full independent provenance or trademark audit.

## Remaining gates

- Independent review/clean install by an external tester; larger external datasets; no claimed broad accuracy, adoption or production security.
- Owner approval of final name, license and repository visibility; verify commit history and collaborators before publication.
- Public-facing README, release tag, feedback channel and external usage. Application requires public profile and repository; project adoption currently unmeasured. Do not claim stars/downloads or grant eligibility that are not demonstrated.
- No real actions or live server; the demo is a finite, offline case selector showing Python-generated receipts. Policy engine and Research Lab remain roadmap items.
