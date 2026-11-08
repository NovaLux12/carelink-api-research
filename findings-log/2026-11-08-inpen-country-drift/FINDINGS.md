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
| The `enabledPerCountry` value is a JSON **object** keyed by country, not an array | **OBSERVED** | measured on the live response; re-derive with the §7 command (`jq type` → object). NOT re-derivable from `results.jsonl`, which holds aggregates only |
| Every key currently carries `true`; there is no false-valued entry | **OBSERVED** | measured on the live response; re-derive with the §7 command. NOT re-derivable from `results.jsonl` |
| The InPen list remains a **strict subset** of `personal.common.core.reporting.enabled.countries` (115) | **OBSERVED** | measured on the live response; re-derive with the §7 subset command. NOT re-derivable from `results.jsonl` |
| Both additions (FR, PT) are already in the reporting list | **OBSERVED** | measured on the live response; re-derive with the §7 command. NOT re-derivable from `results.jsonl` |
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

Measured against this pass's own capture, the credential-shaped values present
were: a reCAPTCHA site key (`6L…buor…`), an `auth0ClientId`, a Mixpanel `token`
under `personal.mixpanel.analytics.settings`, and **two `x-api-key` values** under
`nutrino.cc.{broker,metadata}.service.config` — the last two being what the
precedent above names explicitly. **Every one is served unauthenticated by the
vendor and none is a secret** — but that is not the
test the repo applies. The test is that the committable artefact is the
**redaction**, not the capture, because a second copy of a credential shape in git
history is a second thing to rotate if the vendor ever changes what it serves.

Both raw files are removed and `.gitignore`d in the shape of the precedent. What
remains is sufficient to audit **part** of §1–§3 — and which part is stated
precisely below rather than claimed wholesale, because "sufficient" turns out to be
true of four rows and false of three:

| Artefact | What it supports |
|---|---|
| `inpen-list-verbatim-2026-11-08.txt` | the 31 countries, verbatim and sortable |
| `diff-vs-recorded-29.txt` | the exact delta against the 2026-10-11 record |
| `results.jsonl` | the three requests, with counts, timings, and the **31 / 115** figures |
| §7 below | the commands to re-derive everything else from a fresh GET |

**Auditable from what is committed:** the count (31), the reporting count (115), the
verbatim list, and the delta against the recorded 29 — four of §1's rows in full.

**NOT auditable from what is committed:** the object-vs-array type, the
all-values-`true` check, and the subset comparison against the reporting list. No
committed file contains the response body, so those three require a re-fetch. §7
gives the exact command for each.

**What this costs:** a reader cannot re-run the §3 subset comparison from a
committed file; they must re-fetch the config. That is the intended trade — the
precedent makes it explicitly, and re-fetching is one unauthenticated GET.

**Nothing in §1 was retracted.** Every figure was derived from the response before
it was removed. The count and the delta are re-derivable from the committed files;
the type, all-`true` and subset checks are not — they need the fresh GET in §7,
which contains a separate command for each. The distinction is stated rather than
smoothed over, because "re-derivable from the committed evidence" and
"re-derivable by re-fetching" are different guarantees and only the first one
survives the vendor changing what it serves.

### ⚠ The remedy does not remove the bytes from history, and that is stated here

Removing the files from the tree does **not** remove them from the branch's
history: `20fa875` is an ancestor of this branch's head, so the capture blob is
still reachable and **would land in `main` if this PR is merged with a merge
commit**. §6's own rationale — that a second copy in history is a second thing to
rotate — is therefore only satisfied by removing it from history, not from the tip.

**What actually removes it, in preference order:**

1. **Squash-merge this PR.** The squashed commit carries the final tree only; no
   intermediate blob reaches `main`. This is the cheap correct answer and is what
   this pass recommends.
2. **Rewrite the branch** (`git rebase -i` / `filter-repo`) before merge, if a
   merge commit is wanted for another reason. Not done here: `AGENTS.md` forbids
   force-pushing to a pushed branch without exception, and a force-push of a
   public branch is a worse process breach than the one this section records.

**So the state is: the capture is out of the tree, out of the merge result under a
squash, and still in this branch's history until the branch is deleted.** The
branch should be deleted on merge, which the repo does for every lane.

**A related gate defect found while checking this, and it is not this pass's to
fix:** `scripts/research-gate.sh` scans only `*.md *.yml *.yaml *.sh *.hurl`, so a
`.json` capture is never scanned at all; and the reCAPTCHA pattern in
`scripts/scrub-patterns.txt` is line-anchored (`^6L…$`), so it matches a bare key
line but **not** the key embedded in a JSON value. Measured on the live capture:
anchored 0 hits, unanchored 1. The gate reporting "leak scan clean" on this PR was
therefore true of the patterns it ran and vacuous for the file it most needed to
check. Filed as a separate correction rather than silently widened here — widening
a scrub pattern in a drift-repair PR is the kind of quiet change that should not
ride along.

## 7. Re-deriving this pass

One GET, then four commands — one per claim that is not auditable from the
committed files. Each produces exactly one row of §1.

```bash
curl -s --compressed -A 'carelink-bridge-research/1.0' \
  'https://carelink.minimed.eu/patient/v2/configuration/public' -o cfg.json
```

```bash
# 31 (and the verbatim list)
jq -r '.["personal.inpen.supported.countries"].enabledPerCountry | keys | .[]' cfg.json | sort
# -> 31 lines; diff against the 29 recorded at docs/00-summary-the-map.md:375

# object, not array
jq -r '.["personal.inpen.supported.countries"].enabledPerCountry | type' cfg.json
# -> object

# every key true, none false
jq -r '.["personal.inpen.supported.countries"].enabledPerCountry
       | [to_entries[] | select(.value != true)] | length' cfg.json
# -> 0  (zero keys that are not true)

# subset of the reporting list, and 115
jq -r '(.["personal.inpen.supported.countries"].enabledPerCountry | keys | sort) as $i
       | (.["personal.common.core.reporting.enabled.countries"]) as $r
       | "\($i | length) inpen, \($r | length) reporting, missing: \([$i[] | select(. as $c | $r | index($c) | not)])"' cfg.json
# -> 31 inpen, 115 reporting, missing: []
```

**Note the shape of the last one:** it prints the *missing* members rather than a
boolean, so an empty list is the evidence. A `true`/`false` summary cannot
distinguish "subset holds" from "the lookup returned null" — the failure mode
`docs/09` records.
