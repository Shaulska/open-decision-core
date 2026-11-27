# Launch checklist · 0.3.0

This is release preparation, not a public release or independent certification. The website is static and local-first; its interactive replay selects actual precomputed Python receipts. There is no server, account signup, tracking, API key or live execution.

## Verified by the development-side review

- Baseline main: `811a980700643985ce7ed695eb069ee649b5b3ba`. Retained 0.1, 0.2 and 0.3 snapshots contain 22, 29 and 34 files. Blob hashes and Git tree hashes agree with the corresponding imported Git trees. Targeted scans for common credential patterns, private keys, emails and references to unrelated private repositories found no matches in these source snapshots. This is not exhaustive secret scanning or proof of rights.
- GitHub main history and known MVP branches inspected; no discussion comments on PRs 1–3. Two historical PR descriptions used an unrelated private project name; current descriptions were generalized. Edit history, merge metadata and previous versions can remain visible after a visibility change. The former repository owner retains write access; owner should confirm this is intended. Review the full access list and Git metadata in GitHub before changing visibility. No unrelated repository changed.
- Site is generated from `examples/bea/index.html`, preserving the evidence JSON and receipts byte-for-byte. Unit tests check determinism and unchanged receipt payloads. Chromium smoke checks cover desktop and mobile, all three statuses and Python verification of exported receipt. These are author-side checks.
- Application draft is nonconfidential and unsubmitted; a private copy is retained separately. The draft is removed from the current public-facing tree, but remains in prior commits. Do not treat file deletion as history erasure.

## Owner decision required before release

1. Confirm ownership/right to license the code and approve the proposed Apache-2.0 license. Move candidate text to root `LICENSE`, update packaging and documentation, and confirm scope (code and original docs; third-party data separately attributed).
2. Confirm working name Open Decision Core; full trademark and package-name clearance has not been performed. Do not publish on PyPI yet.
3. Review Settings → Collaborators, historical PR text, commit metadata and Actions logs. Public visibility exposes repository history. If zero association with any prior work is essential, create a separate sanitized publication snapshot instead of flipping the existing history. Do not rewrite history without approval.
4. Independently test the checkout if possible. Development-side review and the small curated benchmark are not external validation. Confirm the release commit CI is green.
5. Change **only** this repository to Public; do not alter any other project.
6. In this repository choose Settings → Pages → Build and deployment → Source: GitHub Actions. Run the workflow **Publish project website (manual)** from main using Actions → Run workflow. The workflow only uploads `site/index.html`; publication is never triggered by push or PR. Verify the actual Pages URL and replay/export before announcing it. On GitHub Free, Pages is available for public repositories. No paid service needed.
7. Create a release tag and feedback channel. Publish a transparent introduction requesting reproducible feedback. Do not invent users, stars, downloads or research results. Submit the application using real account details only after checking current program criteria and the actual public repository. Approval is not guaranteed.

References: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site ; https://developers.openai.com/community/codex-for-oss
