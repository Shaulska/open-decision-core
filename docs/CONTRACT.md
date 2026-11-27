# Preview contract v1

Input object: `schema_version: 1`, `evidence: []`, `decisions: []`.

Evidence fields: `id` unique, `source`, `entity`, `feature`, `version` nonempty strings, `value` JSON value, `event_time`, `published_at`, `received_at`, `available_at` timezone-aware timestamps (missing values are allowed but may be UNVERIFIED), `precision` SECOND (other precision is unsupported), `availability_kind` OBSERVED or PROVIDER_PUBLISHED, `usage` OBSERVATION/SCHEDULED/FORECAST, `source_ref`, `parents` list of evidence IDs. Same version tuple must not have two IDs. OBSERVED requires local received/available timestamps. PROVIDER_PUBLISHED requires published_at and equal available_at, and is admitted only in PROVIDER_ASOF mode; it is a declared publication proxy, not local receipt. An observed event cannot be in the future; a scheduled future event can be known in advance.

Decision fields: unique `id`, `decision_at`, `evidence_ids` exact references, `mode` OBSERVED_REPLAY or PROVIDER_ASOF. Other modes are UNVERIFIED. Audit checks only referenced lineage plus bundle-level ID conflicts. Parents must not become available later than their derived child. No silent selection of latest version. Corrections use a new version/ID. `replay` returns the exact evidence closure **with** the receipt; it may include blocked evidence for diagnosis, not a sanitized feature set.

Receipt: deterministic JSON digest of input and versioned findings, status, counts, receipt digest. `verify` recomputes the full receipt from original input. Counts are findings, not unique incidents. No external authentication or signature.

`split-check`: manifest with `fit_at`, `test_start`, optional nonnegative `embargo_seconds`, train/test arrays. Each row has `id`, `group`, `sample_at`; train rows also `label_available_at`. Checks chronology, overlapping IDs/groups, embargo. Does not prove preprocessing scope or unseen fit data.
