# REDACTIONS.md — lane l2, applied mechanically before any write-up

`pow.nutrino.cc.broker.service.config` and `pow.nutrino.cc.metadata.service.config` returned a **non-placeholder** `security_headers."x-api-key"` on the `.com` deployments. This is the key material `docs/08` F2 / `findings-log/probe-2026-10-08/SECURITY-FINDINGS.md` §S3 already document and already redact — an already-published vendor value, not a new disclosure. It is still a credential and `SECURITY.md` does not permit it in this repository.

`redact.py` applied the **gate's own pattern list** (`scripts/scrub-patterns.txt`), not a hand-typed subset, and the replacement is the repository's existing token.

| file | substitutions | sha256 of the redacted file (16) |
|---|---:|---|
| `headers/k052-carelink-support-medtronic-com-pow.nutrino.cc.broker.service.config.b` | 1 | `1aa324b1b10c5e53` |
| `headers/k053-carelink-support-medtronic-com-pow.nutrino.cc.metadata.service.config.b` | 1 | `db3584ea2ae9a026` |
| `headers/k029-carelink-medtronic-com-pow.nutrino.cc.metadata.service.config.b` | 1 | `db3584ea2ae9a026` |
| `headers/k028-carelink-medtronic-com-pow.nutrino.cc.broker.service.config.b` | 1 | `1aa324b1b10c5e53` |

**`results.jsonl` is deliberately untouched.** Its `body_bytes` and `body_sha256` are the **as-received** values — 329 / 314 on the two `.com` hosts and 309 / 288 on `carelink.medtronic.eu` — and they are what makes the finding reproducible. The redacted file in `headers/` is therefore *not* byte-identical to the body those two fields describe; the difference is exactly the substitution count above. Comparing the two is a way to confirm the redaction happened, not a way to check a finding.

**What may and may not be said about the value.** Its *shape* — a 40-character base62 string, identical in both services, present on the `.com` deployments and replaced by a 17-character placeholder on `carelink.medtronic.eu` — is recorded, because the shape is the finding. The value itself is not recorded anywhere in this repository, and `SECURITY.md` says so in advance.
