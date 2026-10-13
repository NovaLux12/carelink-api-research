# Research area P — recover the request schema from the vendor's own app, statically

**Pass date:** 2026-10-13
**Claim:** area P (`docs/11-suggested-research-areas.md` §"P. Recover the request schema from the vendor's own app, statically")
**Verdict:** **Negative on recoverability.** No reproducible mobile-app binary is in the repository or anywhere cited by it. The two vendor web bundles that *are* reproducible by digest expose route strings and one client-side matching enum, but not the authenticated request-body field names (`markers[]` per-entry fields, NGP alarm vocabulary). The request-shape half of the token-blocked rows in `docs/10-open-questions.md` (lines 38-39, 46, 77) remains unverified by this pass. A documented negative is the stated legitimate close.
**Tooling (read-only):** `grep` 3.12, `python3` 3.14.8, `sha256sum` 0.10.0, `git` 2.53.0. **Zero vendor health-surface requests. Zero POST anywhere.**
**Requests:** 0 of a 0 cap; no vendor GET performed; ≥2s spacing rule stated in applicable terms (vacuous for this static pass).

## 1. What I looked for

Per `docs/11` area P, the target is the CareLink mobile client's compiled request shape: the `markers[]` per-entry field names (`removalType`, `removalReason`, `sensorInsertionLocation`, `timecapUnscrewed`), the `deviceFamily` casing the client matches on, and the NGP alarm vocabulary. The area's blocker is stated verbatim: "the artefact is not in the repo and no static-analysis tooling has been run against it".

## 2. Whether a reproducible binary exists

- No application binary is committed: no `.apk`, `.ipa`, `.aab`, `.dex`, or `.wasm`, and no vendor bundle larger than ~1 MB in the repo tree.
- The only mobile-artifact document is store *metadata* — `findings-log/medtronic-carelink-2026-07-21/09-mobile-artifacts.md` — whose Methods section states verbatim: "No APK was downloaded, installed, decompiled, or reverse-engineered." Its Unknowns lists "static endpoint/resource strings inside the app". OBSERVED: no mobile app binary or decompiled output is cited anywhere in the repo.
- `docs/09` records the standing reason a public web path cannot supply it: `carelink.minimed.eu` serves gzip unconditionally and `carelinkhp.*` returns a 200 + text/html 5518 B catch-all, i.e. no source maps. INFERRED (from those, not newly demonstrated): the public web path cannot yield a request-body schema by grep alone.

## 3. What the reproducible bundles do contain (offline grep only)

Two vendor web bundles match committed digests exactly and so are the same artefacts prior passes analysed:

- clinic (`pow`) bundle — 3,397,615 B, sha256 `2a7fa8e7af519c2b...` (`docs/01-hosts-and-estate.md`, `docs/08-security-findings.md`, areas A/G).
- patient bundle — 3,417,255 B, sha256 `0fb4fbd4...` (`docs/11` area V, area-v-pde-clients FINDINGS seq 3/7).

A literal census (quoted + raw substring, GNU grep 3.12) returned:

| Token | clinic | patient | Reading |
|---|---|---|---|
| deviceFamily | 2 | 5 | Client reads `deviceFamily` and stores `deviceFamilyMapping`; patient call sites use `startsWith` over `BLE`/`SIMPLERA`/`GUARDIAN`. This is the single request-shape fact the bundles genuinely give. OBSERVED, confirming `docs/05` and area G. |
| deviceModel / sensorModel | 39 / 3 | 27 / 5 | Emitted fields, UI/resolver tokens only; no per-entry schema. |
| logbook route literals | yes | no | Clinic names `hcp/patients/{patientId}/logbook/entries`, `.../filled`, `.../last`, plus `hcp/configuration/public/logbook.supported.entry.types` and `hcp/configuration/public/system.logbook.entry.validation.config`. OBSERVED endpoints only. |
| markers | 3 | 0 | The 3 hits are substrings in a minified token stream (`...markers,reconciliation,...`), not a property name. OBSERVED negative. |
| removalType / removalReason / sensorInsertionLocation / timecapUnscrewed | 0 | 0 | OBSERVED negative — none of the `docs/10` call-site field names appear as literals. |
| alarm / alarmCode / therapyAlgorithmState / reservoirLevel / reservoirLevelPercent | 7 / 0 / 0 / 0 / 0 (clinic, log/translation labels) | 49 / 0 / 0 / 0 / 0 | OBSERVED negative on wire form: no alarm-code identifier, no therapyAlgorithmState, no reservoirLevel*, alarmCode 0 in both. |

The reproducible bundles expose surface endpoints and one client-side matching enum, but not authenticated request-body field names. Consistent with the existing reading that those names are "call-site fields, not config" (`docs/10:46`).

## 4. Consequence for the token-blocked rows

| docs/10 row | This pass |
|---|---|
| NGP alarm-code vocabulary (#84, "not published on any unauthenticated surface", docs/10:38) | Unchanged: 28 key names already 404 under controls; `alarmCode` = 0 in both bundles. Still needs an authenticated `POST hcp/configuration/application` or a real pump report — token-gated, out of automation scope. |
| Whether alarm wire form is numeric or string (`lastAlarm.code`) (docs/10:39) | Unchanged: no `lastAlarm`/alarm code token anywhere; stays INFERRED from a 2015 gist. |
| markers[] per-entry payload schema (#76, docs/10:46) | Unchanged: 12 entry-type vocabulary settled and double-sourced; per-entry field names unobserved in both bundles; the only config surface that could carry them, `system.logbook.entry.validation.config`, returns null/404 unauthenticated (HCP-CONFIG-SCHEMA). Still requires a clinician token on `logbook/entries`, explicitly not requested. |

This is exactly the negative outcome area P counts as first-class.

## 5. Request accounting

- Vendor health-surface requests: **0** (no GET, OPTIONS, POST, DNS, or probe to any host, including Common Crawl).
- Local read-only: bundle reads plus literal census; digests reproduced as above.

## 6. Close position

Area P closes on the documented negative leg: the reproducible bundles corroborate `deviceFamily` client-side matching on `BLE`/`SIMPLERA`/`GUARDIAN` and the HCP logbook/validation-config endpoint strings, and tighten the negative on three tokens, but the token-blocked rows remain token-blocked. Full closure needs (a) a reproducible mobile-app binary committed with a named static tool, or (b) an authenticated clinician session on `hcp/patients/{patientId}/logbook/entries` and `hcp/configuration/application` — both outside `AGENTS.md` §11 for an automated run. No new area letter is minted (`docs/11` "Why there is no area AA"); remaining work stays as the unchanged `docs/10` rows for #76/#84. No docs or regression changes were made beyond recording this log.
