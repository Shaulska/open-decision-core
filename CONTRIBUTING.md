# Contributing

Start with a reproducible issue: describe evidence, expected verdict, actual verdict and policy version. Use synthetic or legally reusable examples; never attach credentials, confidential data or private datasets.

Run `python -m unittest discover -s tests -v` from the repository root. If changing temporal semantics, add a regression test, update the contract, explicitly version policy changes and regenerate bundled receipts and demo. Explain limitations, avoid claiming source authentication from hashes, and keep BLOCK/UNVERIFIED semantics fail-closed. A new model or policy must not be described as validated without independent evidence.

By submitting a contribution, you agree to license it under Apache-2.0 as described in LICENSE. Only submit material you have the right to license. Report security issues privately; see SECURITY.md.
