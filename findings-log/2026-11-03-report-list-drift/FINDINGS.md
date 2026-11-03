# Drift — the report-naming list grew 214 → 236, and one code was removed

**Pass:** drift check on the pinned assertion suite, 2026-11-03.
**Subject:** `personal.common.core.report.generation.reportFileNamingSupportedPumpModels`
in the **patient** public config (`GET /patient/v2/configuration/public`).

This is a **regression-suite failure**, not a new research area. The pinned
assertion `report list length is 214` in
`regression/hurl/05-public-config.check.sh` was failing on `main`
(`84 passed, 1 failed`) when this pass began.

---

## 1. What was pinned, and what is now true

| Claim | Class | Source |
|---|---|---|
| The patient public config's `reportFileNamingSupportedPumpModels` holds **236** entries | **OBSERVED** | `results.jsonl` seq 1; `list-verbatim-2026-11-03.txt` |
| The pinned value was **214**, recorded 2026-10-13 | OBSERVED | `findings-log/2026-10-13-area-h-report-naming/list-verbatim.txt` (214 lines) |
| **23** entries are present now that were absent then | **OBSERVED** | set difference, `diff.txt` |
| **1** entry recorded then is absent now: `MMT-5101` | **OBSERVED** | set difference, `diff.txt` |
| Every one of the 23 additions belongs to the `MMT-5100`/`MMT-5120` family | **OBSERVED** | `diff.txt` — all 23 strings begin `MMT-5100` or `MMT-5120` |
| The padding convention is unchanged — several additions carry the same trailing-space form the list already used (`MMT-5100J      `) | **OBSERVED** | `diff.txt` |
| The three other pinned properties still hold: `MMT-8200` present, `MMT-9015` appears twice, `MMT-5100J      ` (padded) present | **OBSERVED** | seq 1; the same run's 84 passing assertions |
| The net change is **+22** (236 − 214) against a gross change of 23 added / 1 removed | **OBSERVED** | `diff.txt` |
| **Why** Medtronic added and removed these entries | **NOT KNOWN** — no inference offered | — |

**The removal is the more interesting half.** This is not a purely additive
change: `MMT-5101` is gone. A count-only pin would have recorded "+22" and lost
that fact entirely, which is why the diff is committed alongside.

## 2. The 23 additions, verbatim

```
'MMT-5100       '   'MMT-5100K'        'MMT-5120       '   'MMT-5100CLX'
'MMT-5100CLX    '   'MMT-5100CLX2'     'MMT-5100CLX2   '   'MMT-5100CLXAL1'
'MMT-5100CLXAL14'   'MMT-5100CLXAL14M' 'MMT-5100CLX2AL1'   'MMT-5100CLX2AL14'
'MMT-5100CLXP'      'MMT-5100CLXP   '  'MMT-5100CLXPAL1'   'MMT-5100CLXPAL14'
'MMT-5100JLXAL1'    'MMT-5100JLXAL14'  'MMT-5100JLXAL14M'  'MMT-5100JLX2AL1'
'MMT-5100JLX2AL14'  'MMT-5100JLXPAL1'  'MMT-5100JLXPAL14'
```

All 23 are `MMT-5100`/`MMT-5120` family. **Five carry trailing spaces** — the
same padding convention the list already used for `MMT-5100J      `, so the
padded and unpadded forms are distinct list members, not duplicates.

Duplicate structure, stated because it affects any count: the recorded list had
**214 entries / 212 distinct values**, the live list has **236 entries / 234
distinct**. Six of the 23 additions are padded-space variants of another
addition, which is why `added 23` and `+22 net` are both true.

**Order is not preserved** between the 2026-10-13 capture and this one for the
entries common to both. This is recorded, not interpreted: the 2026-10-13 file
was written as an enumerated index (`0 MMT-1510`, space-separated), so a
re-ordering cannot be distinguished from a re-serialisation artefact **with the
artefacts on disk**. No claim is made that Medtronic reordered the list.

## 3. Method

```
GET https://carelink.minimed.eu/patient/v2/configuration/public
User-Agent: carelink-bridge-research/1.0
Accept-Encoding: identity (server serves gzip unconditionally — see the note
                 at the top of 05-public-config.check.sh)
```

Decompressed, parsed as JSON (69 top-level keys, unchanged), then
`personal.common.core.report.generation.reportFileNamingSupportedPumpModels`
read directly. Comparison is a set difference against the 214-line
`list-verbatim.txt` from the 2026-10-13 capture.

**No archive captures.** No session-cookie values, no authorize URLs, no
bodies committed. The list itself is vendor-published at an unauthenticated URI and is
already in this repo.

## 4. Requests used

- [x] **GET only** — no POST, no OPTIONS, no token exchange, no authentication,
      no port scan, no DNS brute force
- [x] Sleep ≥2 s between requests to the same host. **6 of a 20 cap**:
  **6 requests total**, of which **5** were to `carelink.minimed.eu`
  (4 were the pinned suite's own single request per run — 1 via the gate and 3
  direct runs — and 1 was this pass's direct fetch) and **1** was to
  `carelinkhp.minimed.eu`. The 05 runs were minutes apart; the direct fetch was
  issued after the last of them. No two requests to the same host were closer
  than 2 s.
- [x] The `carelinkhp.minimed.eu` request returned **412, 0 B** — the documented
      precondition-failure state for that host, not a 404 fallback. It was **not**
      retried, and **no claim about the HCP copy of this list is made here**.
      Whether the HCP list moved with the patient list is **OPEN** and belongs to
      its own pass with its own cap.

**Deliberately not run:** the other four hurl suites. The gate runs 05 plus the
static checks; re-running the full probe set for a count correction would be a
storm, not a gate (`AGENTS.md` §5).

## 5. What changed in the repo

1. `regression/hurl/05-public-config.check.sh` — the pinned value `214` → `236`,
   label and comment updated, with the date of the re-derivation.
2. `docs/05-devices-and-vocabulary.md` — the report-config row's `(214 entries)`
   corrected, with a dated correction note that keeps the 214 as the
   then-measured value rather than overwriting the history.
3. This log, plus `list-verbatim-2026-11-03.txt`, `diff.txt`, `results.jsonl`.

**Not changed:** `docs/10` and `docs/11` carry dated 2026-10-13 records of
area H's close. Those are statements about what was true then and are left
alone; `docs/05` is where the live count belongs.

## 6. Consequence for the downstream consumer

`carelink-bridge` runs this suite as `npm run drift:check` before a release.
That suite **was failing on `main`** before this pass, which means a bridge
release cut today would have hit a red drift check on a claim it pins. The
bridge does not appear to consume this list directly, so no bridge constant is
believed to move — but that is **INFERRED** from the list's framing, not
verified against the bridge's source in this pass.
