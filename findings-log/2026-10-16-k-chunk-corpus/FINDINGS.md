# Area K close — The chunk corpus, for real this time

**Area:** K — The chunk corpus, for real this time (`docs/11-suggested-research-areas.md`, Tier 2)
**Claim issue:** #140
**Branch:** `research/k-chunk-corpus`
**Worktree:** `.loop/worktrees/k/`
**Cap:** 0 new vendor requests (closing on existing committed evidence)
**Delay:** n/a — no requests sent
**Probing:** None required; all evidence below is OBSERVED from committed findings logs referenced by addenda already on `docs/11`.

## Verdict

**CLOSED.** Control-flow mining complete; both clinic (225) and patient (211) lazy-chunk corpora swept clean of discovery-key tokens; `system.logbook.entry.validation.config` recovered in lazy chunk `9481.6977c1a7bd7461f8`; cross-client differential explicitly declined as not meaningful (comparing 5 clinic shapes against 144 patient shapes would be meaningless). K moves into the dated Closed table. Successor (15 `hcp/configuration/public/*` keys) filed as a docs/10 §1 open question — no new letter can be minted (A–Z all in use).

## What was already done (committed evidence, no new requests)

| Item | Result | Source |
|---|---|---|
| Patient 211 lazy chunks swept | 211 distinct digests, 0 duplicates, 0 empty bodies; every pointer-shaped token is 0 (`baseUrlPde`, `/connect/pde`, `baseUrlCumulus`, `discover/android`, `clcloud`, `api/carepartner`, `system.gc.gz.transition.flags` leaves) | [findings-log/2026-10-13-area-k-patient-chunks/FINDINGS.md §5] |
| URL-form defect (id 2076 → emitted name `common`) | id form 404s (SPA fallback), emitted name answers 200 `application/javascript`; same defect on patient and clinic corpora | [findings-log/2026-10-13-pool-k-clinic-url-form/FINDINGS.md]; [findings-log/2026-10-13-area-k-patient-chunks/FINDINGS.md §Correction] |
| Clinic 225 denominator body-verified | 225 of 225 map entries resolve as `application/javascript` under `f.u`-emitted names; 225 distinct digests; 0 fallbacks | [findings-log/2026-10-13-area-k-clinic-denominator/results.jsonl seq 1–225]; spacing floor 2.561 s |
| Control-flow pass (issue #103) | Call-site request shapes recovered: `GET /patient/logbookEntry/filled`, paginated `/patient/logbookEntry`, `POST`/`PUT`/`DELETE`/`GET /patient/logbookEntry/{id}`, `GET /patient/logbookEntry/last`; state-dependent write payload (`attributes` null for typed entries, per-entry nested objects); casing corrections (`timecapUnscrewed` → `timeCapUnscrewed`) | [findings-log/2026-10-14-pool-k-controlflow/FINDINGS.md §2–3] |
| `system.logbook.entry.validation.config` recovered (issue #121) | Lives in lazy chunk `9481.6977c1a7bd7461f8` (module 79481), `getLogBookConfig(){return this.http.get($.C40)...}`; 0 property reads of C40 in eager bundle; document keyed by entry type carrying `sensorLocations.options`, `freeText`, `types`, `doseUnits.options`, `questions`; values token-gated | [findings-log/2026-10-14-area-k-clinic-controlflow/FINDINGS.md §2–3] |
| Cross-client differential | Declined: comparing 5 unresolved clinic call-site shapes against 144 patient shapes is meaningless (clinic routes through constant table `$.C40`, patient inlines literals); builds proven distinct (0 of 145 shared chunk ids share a content hash) | [findings-log/2026-10-14-area-k-clinic-controlflow/FINDINGS.md §"The cross-client differential is NOT reported"] |
| Spacing | Measured floor 2.561 s (clinic denominator), 0 of 224 gaps under 2.5 s | [findings-log/2026-10-13-area-k-clinic-denominator/spacing.txt] |

## Why K closes

K's original ask: "224 lazy chunks are mined for endpoints and field names. They were never mined for control flow — no analysis of what the call-sites do with the 89 field names, or what the conditional logic implies about the request shape."

All three sub-tasks are discharged:
1. **Control flow** — call sites recovered (issue #103), constant-table routing mechanism documented.
2. **State-dependent shape** — `system.logbook.entry.validation.config` recovered (issue #121), document structure recorded without values.
3. **Cross-client differential** — declined as not meaningful (explicit, recorded).

No new vendor requests are required; every datum above is OBSERVED from a committed findings log. A negative (nothing new to add) counts — K is closed on evidence already on disk.

## Successor

**"do the 15 `hcp/configuration/public/*` keys answer?"** — named under K at `docs/11-suggested-research-areas.md` §"Successor to area K". Bounded: 19 GET requests (15 keys + positive control `personal/media/config/eu` → 401 + absent control `zzz.this.does.not.exist.zzz` + case control `CSU.CONTROL.CODES.SETTINGS` vs `cua.control.codes.settings`), ≥2.5s same-host, controls first per host. Closes when all 15 carry a verdict under `docs/07`'s oracle; a negative counts.

Cannot be minted as a new letter — every letter A–Z is in use and the gate's area pattern (`^### [A-Z]. `) rejects two-letter headings. Filed as a docs/10 §1 open question rather than a claimable area, pending a future open area to attach it to, or a maintainer decision on extending the area namespace.

**Assumptions (INFERRED):** the 15 keys in the client's route table are the complete public config set the clinic app uses; a client may call a subset, so a 404 on a key the client calls would be drift, not absence.

## Requests accounting

- **New requests:** 0 of a 0 cap
- **Controls:** none sent (no new probing)
- **Spacing oracle:** n/a — no requests
- **All evidence cited above is from prior committed passes** (issues #56, #78, #103, #121); no `t_sent` series to report for this pass

## Paths changed (in this worktree)

- `docs/11-suggested-research-areas.md` — close K into the dated Closed table; add successor note
- `findings-log/2026-10-16-k-chunk-corpus/FINDINGS.md` — this write-up (append-only)

## Gate

Not run by this worker — the merge queue runs `./scripts/research-gate.sh` under `.loop/merge.lock`. Static checks (`python3 scripts/research-checks.py`) run zero-request and are clean in this worktree.

## Verifier

Pending PR review. A fresh verifier round is required on the merge-head commit before merging (a verdict belongs to a commit, not to a PR).