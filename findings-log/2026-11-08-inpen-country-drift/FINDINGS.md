# Drift — the InPen country list grew 29 → 31, and the additions are FR and PT

**Pass:** drift check on the pinned assertion suite, 2026-11-08.
**Subject:** `personal.inpen.supported.countries.enabledPerCountry`
in the **patient** public config (`GET /patient/v2/configuration/public`).

This is a **regression-suite failure**, not a new research area. The pinned
assertion `inpen countries moved in lockstep` in
`regression/hurl/05-public-config.check.sh:174` was failing on `main`
(`84 passed, 1 failed`) when this pass began.

---

## 1. What was pinned, and what is now true

| Claim | Class | Source |
|---|---|---|
| The patient public config's `enabledPerCountry` holds **31** countries | **OBSERVED** | `results.jsonl` seq 1; `inpen-list-verbatim-2026-11-08.txt` |
| The pinned value was **29**, recorded 2026-10-11 by live read | OBSERVED | `docs/00-summary-the-map.md:375` |
| Exactly **two** countries are present now that were absent then: **FR** and **PT** | **OBSERVED** | `diff-vs-recorded-29.txt` |
| **Nothing was removed** — the change is purely additive | **OBSERVED** | `diff-vs-recorded-29.txt` (only `>` lines) |
| The 29-list recorded on 2026-10-11 is exactly reproducible from this capture minus FR/PT | **OBSERVED** | `diff-vs-recorded-29.txt` — no `-` lines, no other `+` lines |
| The `enabledPerCountry` value is a JSON **object** keyed by country, not an array | **OBSERVED** | seq 1; `jq type` → object |
| Every key currently carries `true`; there is no false-valued entry | **OBSERVED** | seq 1; `jq 'to_entries\|map(select(.value==true))\|length'` → 31 |
| The InPen list remains a **strict subset** of `personal.common.core.reporting.enabled.countries` (115) | **OBSERVED** | set comparison in §3 |
| Both additions (FR, PT) are already in the reporting list | **OBSERVED** | seq 1; set comparison in §3 |
| The reporting list is still **115**, unchanged from its 2026-11-03 value | **OBSERVED** | seq 1; the passing `reporting countries drifted 17 -> 29` guard |
| **Why** Medtronic added FR and PT | **NOT KNOWN** — no inference offered | — |

**The lockstep relationship held through this change**, which is why the assertion
is worth keeping rather than relaxing: the InPen list grew by exactly the two
countries the reporting list already carried, so the subset invariant survived a
vendor mutation. A count-only pin would have recorded "+2" and told nobody which
two — which is why the verbatim list and the diff are committed alongside.

## 2. The delta, verbatim

```
$ diff <recorded-29, sorted> <captured-31, sorted>
12a13
> FR
23a25
> PT
```

| Set | n |
|---|---|
| Recorded 2026-10-11 (`docs/00:375`) | 29 |
| Captured 2026-11-08 | 31 |
| Added | 2 (FR, PT) |
| Removed | 0 |

Current list, verbatim:

```
AE AT AU BE CH CL CZ DE DK EG ES FI FR GB GE HR IE IL IS IT LU NL NO PL PT RO RS SE SI SK ZA
```

Recorded list, verbatim, for comparison:

```
AE AT AU CH BE NL LU IT ZA CL IE HR CZ EG GE IL PL RO RS SK SI SE DK FI DE IS NO ES GB
```

## 3. The invariant the assertion is actually protecting

The pinned check is not "the count is 29". It is **"the InPen list and the
reporting list move together"** — the 2026-10-10 finding was that a client which
cached "these countries have reporting" was silently wrong for 12 countries
after a one-day rollout.

Re-derived from the same response:

| Check | Result |
|---|---|
| `inpen ⊄ reporting` (countries in InPen but not reporting) | **none** |
| `inpen ⊆ reporting` | **true** (31 ⊂ 115) |
| Both new members present in reporting | **true** |
| Reporting list itself changed | **no** — 115, as at 2026-11-03 |

So the relationship the guard exists to detect is **intact**. The failure is a
stale expected count, not a broken invariant.

## 4. Requests used

- [x] **GET only** — no POST, no OPTIONS, no token exchange, no authentication,
      no port scan, no DNS brute force
- [x] Sleep ≥2 s between requests to the same host. **3 of a 10 cap**:
  **3 requests total**, all to `carelink.minimed.eu` and all the same path:
  seq 1 this pass's direct fetch; seq 2 the gate's own single 05 request;
  seq 3 a direct 05 run to identify which assertion failed. The gate run and the
  direct run were minutes apart; the direct fetch was issued before both.
  No two requests to the same host were closer than 2 s.
- [x] No other host was contacted. Only `05-public-config.check.sh` was run.

**Deliberately not run:** the other four hurl suites. The gate runs 05 plus the
static checks; re-running the full probe set for a count correction would be a
storm, not a gate (`AGENTS.md` §5).

## 5. What this pass changes

1. `regression/hurl/05-public-config.check.sh:174` — expected `29` → `31`.
2. The verbatim list and diff committed here, so the next reader can tell a
   two-country addition from a reshaping without re-probing.
3. No `docs/` page is edited. The 2026-10-11 live-read record in
   `docs/00:375` is a dated observation and stays true **at its date**; this
   pass's dated record is the correction, per `AGENTS.md` §3.

**Successor area:** none minted. This is a regression-suite repair with a
complete answer — the delta is enumerated, not sampled. Whether Medtronic intends
further expansion is **NOT KNOWABLE** from one capture and does not clear the
minting bar (Derived · Bounded · Non-duplicate · Labelled).

**Evidence path:** `findings-log/2026-11-08-inpen-country-drift/`

---

## 6. Withdrawal — raw captures were committed, then removed

**Recorded because the repo's own precedent forbids what this pass first did, and
the pass should carry its own correction rather than leave it in a PR thread.**

The first version of this directory committed `config-2026-11-08.json` and
`config-gzip-2026-11-08.bin` — the raw unauthenticated response. An independent
verifier flagged the shape without calling it a leak, and checking the precedent
showed the rule was already settled:

> **⚠ Raw captures are deliberately NOT committed.** The 69-key public config is
> unauthenticated and carries credential-shaped values: a reCAPTCHA site key, and
> an `x-api-key` under each of the two `nutrino.cc.*` service keys. Committing
> `docs/*.json` would put credentials in the diff.
> — `findings-log/2026-10-12-published-pointers/FINDINGS.md`

Measured against this pass's own capture, the values present were: a reCAPTCHA
site key (`6L…buor…`), an `auth0ClientId`, and a Mixpanel `token`. **Every one is
served unauthenticated by the vendor and none is a secret** — but that is not the
test the repo applies. The test is that the committable artefact is the
**redaction**, not the capture, because a second copy of a credential shape in git
history is a second thing to rotate if the vendor ever changes what it serves.

Both raw files are removed and `.gitignore`d in the shape of the precedent. What
remains is sufficient to audit every claim in §1–§3 without the vendor's site key:

| Artefact | What it supports |
|---|---|
| `inpen-list-verbatim-2026-11-08.txt` | the 31 countries, verbatim and sortable |
| `diff-vs-recorded-29.txt` | the exact delta against the 2026-10-11 record |
| `results.jsonl` | the three requests, with counts and timings |
| §5 below | the command to re-derive the list in one line |

**What this costs:** a reader cannot re-run the §3 subset comparison from a
committed file; they must re-fetch the config. That is the intended trade — the
precedent makes it explicitly, and re-fetching is one unauthenticated GET.

**Nothing in §1 was retracted.** Every figure was derived from the response before
it was removed, and each is independently re-derivable by the command in §5.

## 7. Re-deriving this pass

```bash
curl -s --compressed -A 'carelink-bridge-research/1.0' \
  'https://carelink.minimed.eu/patient/v2/configuration/public' \
| jq -r '.["personal.inpen.supported.countries"].enabledPerCountry | keys | .[]' | sort
# -> 31 lines; diff against the 29 recorded at docs/00-summary-the-map.md:375
```
