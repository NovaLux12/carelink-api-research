# Area AD — the committed `cluster.idx` locate: the seed fix works, and the absence proof does not

**Date:** 2026-11-10 (first instrumented send 00:36:58.521Z, last 00:41:06Z)
**Area:** `docs/11` **AD** — "Can the committed `cluster.idx` locate converge — and what does
the `minimed.eu` family interval actually contain?"
**Claim:** https://github.com/NovaLux12/carelink-api-research/issues/164
**Instrument:** `servedness.py` in this directory — a **copy** of
`findings-log/2026-10-18-sl1-cluster-servedness/servedness.py` extended, never an edit of it.
Ledger: `results.jsonl`, **32 rows**. Accounting: `spacing.txt` (from `spacing.py`), gate:
`control-gate.txt`. Block evidence: `block-probe.json`, `confirm.json`.

**Headline, in one line: the seed fix converged — and it converged the controls in 5 and 4
pages — but it converged `CC-MAIN-2022-27` to the WRONG answer, and the reason is that the
instrument's absence proof is invalid for `cluster.idx`.**

**What the area asked and what it got:**

| Half | Result |
|---|---|
| Can the seeded locate **converge**? | **Yes.** Both controls reached a terminal state in 5 and 4 pages of a 10-page budget, where the fixed `f0 = 0.85` seed could not converge in 3. |
| Is the bisection's **absence** verdict sound? | **No.** `CTRL_A`'s `FAMILY_ABSENT` is **false**. The proof assumes the keyspace is keyed per URL; it is keyed per *block*. |
| What does the family interval **contain**? | For `CC-MAIN-2022-27`: **9 `eu,minimed,carelink)` records**, read out of one block. For `CC-MAIN-2024-42` and `CC-MAIN-2014-23`: **no family record**, verified at record level inside the block that must contain it. |

The area closes — on a **negative about the instrument**, which is a stronger result than
the absence it was asking about, and it is not a verdict that `minimed.eu` is absent from
2014-23 by the old route. §6 states exactly what the target's verdict now rests on.

---

## 1 · Accounting — 32 of a 50 cap

- **Requests: 32 of a 50 cap.** `wc -l results.jsonl` = **32**, and `spacing.py` re-derives
  that figure from the ledger alone. Every row carries all three stamps.
- **Hosts: `data.commoncrawl.org` (25 rows), `index.commoncrawl.org` (7 rows). Nothing
  else.** `spacing.py` asserts every row's host against the permitted set and reports
  `hosts outside the two permitted: NONE`. **Requests to any Medtronic host: 0** — the
  ledger carries no `minimed`/`medtronic`/`carelink`/`clcloud` host at all, because the
  hostname appears only *inside* a returned key, never in a request.
- **Method: GET only.** All 32 rows: `methods present: ['GET']`. No POST, no auth, no token.
- **Delay: ≥ 3.5 s between requests to the same host**, declared and held **inside the held
  lock(s)**. Measured floor on the send-to-send gap: see the table below.
- **Bulk reads are all ranged.** Every `data.commoncrawl.org` row carries a
  `range: lo-hi[NB]` field, asserted in `Fetcher.get` (`ranged reads are a
  data.commoncrawl.org instrument`) and re-checked here: 25 of 25. No whole-file read was
  ever issued.
- **Bodies are outside the tree.** All 32 response bodies live in
  `.loop/ad-bodies/` (gitignored); the committed artefacts are bounded projections only —
  key names, counts, offsets, statuses.

### The itemisation, stated before the first request and honoured

| Item | Planned | Used |
|---|---|---|
| `collinfo.json` (assert target published, typed dates) | 1 | **1** |
| absent-crawl oracle `CC-MAIN-9999-99` | 1 | **1** (404) |
| head reads `CC-MAIN-2022-27`, `CC-MAIN-2024-42` | 2 | **2** |
| locates, controls | 2 × 10 = 20 | **9** (5 + 4) |
| head read `CC-MAIN-2014-23` | 1 | **1** |
| target locate | 10 | **5** |
| retries (E[N] > 1 on this API) | 14 | **6** (all `504`, all on `index.commoncrawl.org`) |
| **subtotal, the pass** | **49** | **25** |
| block confirmation reads (§4 — the repair, unplanned) | — | **6** |
| re-issued `head` read `CC-MAIN-2014-23` (`seq 23`, duplicate of `seq 14` — first block parse failed) | — | **1** |
| **total** | **50** | **32** |

The block reads were **not** in the pre-registered plan and are declared as a deviation:
they exist because the control gate failed and the failure needed a cause rather than a
shrug. The split is **run 1 = `seq` 21–22** (two block reads) and **run 2 = `seq` 29–32**
(four block reads, `cdx-00236.gz` twice), plus one re-issued `head` read at `seq 23`. Seven
unplanned rows in total, costing 7 of the 18 unspent requests, is what the diagnosis cost.
32 of 50 is inside the cap with 18 unspent; nothing was extended to make a result appear.

### Spacing, measured

From `t_sent` only (`spacing.txt`, re-derived by `spacing.py` from the committed ledger):

| Host | Timed sends | Gaps | Floor | Gaps < 3.5 s | Gaps < 2.0 s |
|---|---|---|---|---|---|
| `data.commoncrawl.org` | 25 | 24 | **3.534 s** | **0** | 0 |
| `index.commoncrawl.org` | 7 | 6 | 13.818 s | **0** | 0 |
| **overall** | 32 | 30 | **3.534 s** | **0** | 0 |

- **Floor 3.534 s, gap count 30, gaps under 3.5 s: 0, gaps under the `AGENTS.md` §8
  2.0 s: 0.** The declared sleep is 3.5 s and is taken **inside the held lock(s)**, so a
  same-host gap is `3.5 s + the previous response's duration` — which is why the measured
  floor sits just above the declaration rather than at it.
- **Rows where `t_done` precedes `t_sent`: 0.** Checked across all 32 rows (the known
  corrupt-`t0` class). No cause asserted, because there is no instance to explain.
- **Lock discipline.** Every send acquires `host-index.commoncrawl.org.lock` first and, for
  a bulk-path read, `host-data.commoncrawl.org.lock` second, in that fixed order inside
  one process, and sleeps while holding. The locks are the ones in the **main clone's**
  `.loop/`, so the other lane that may probe these hosts is serialised against this run
  rather than overlapped with it. Both lock files were created once and reused; no lock was
  held across the whole run.
- **Allowed-host assertion before every send:** `assert host in ALLOWED` at the head of
  `Fetcher.get`, where `ALLOWED = {index.commoncrawl.org, data.commoncrawl.org}`.

---

## 2 · The seed derivation — zero requests, arithmetic shown

`python3 servedness.py derive` (`seed-derivation.json`). It reads **only committed files**:
the 2026-10-18 pass's `locate-*.json` (its page boundaries) and its `results.jsonl` (the
file size, from `Content-Range`). No request.

The rule: SURT keys are byte-sorted, so a set of pages that all sort below `FAM_LO` bounds
the interval from below, and a page whose first key sorts at or above `FAM_HI` bounds it
from above. Applying it mechanically to the committed pages:

```
CC-MAIN-2022-27, total 153,702,643 B
  bracket for de,/es,/eu,   (66,372,199, 95,363,994) = (0.43182, 0.62044) of the file
  f0 = (66,372,199 + 95,363,994) / 2 / 153,702,643 = 0.52613
  one 4 MiB page spans 2.7% of the file

CC-MAIN-2024-42, total 121,395,065 B
  bracket for de,/es,/eu,   (52,641,478, 74,767,913) = (0.43364, 0.61591) of the file
  f0 = (52,641,478 + 74,767,913) / 2 / 121,395,065 = 0.52477
  one 4 MiB page spans 3.5% of the file

CC-MAIN-2014-23, no committed pages
  f0 = 0.52545  (mean of the two controls; the brackets' midpoints agree to within 0.00136 of the file)
```

**Evidence labels.** That a `com,`-keyed page bounds the interval from below and a
`fr,`-keyed page bounds it from above is **INFERRED** in exactly one respect: that SURT
order is byte order. Every page read in this repository demonstrates that, but it is a
property of the keyspace, not a statement of Common Crawl's. That `eu,` must lie inside
`(0.4318, 0.6204)` **follows arithmetically** from the two committed page boundaries once
byte order is granted. **Where** inside that bracket `eu,minimed)` sits is the inferred
part — the midpoint is the estimator, and the measured bracket is 18.9% of the file wide,
so the midpoint can be off by half that and the first page (2.7% wide) would still land
outside the interval. **OBSERVED:** all three seeded locates converged (§3), and the
`CC-MAIN-2022-27` bisection narrowed to the puncturing pair in 5 pages where `f0 = 0.85`
could not converge in 3.

The 0.85 seed was the whole convergence bug, and the fix is exactly one line: `Locater` now
takes a per-crawl `f0` from `seed-derivation.json` instead of a module constant. A run
without the derivation file falls back to 0.85 and is then visibly the old run.

---

## 3 · The synthetic selftest at realistic size — and what it does *not* prove

`python3 servedness.py selftest-realistic`, 0 requests. Keyspace: **2,000,005 lines,
108,905,444 B**, at ~54 B/line, one 4 MiB page = **3.85% of the file** — so the bisection is
genuinely exercised, unlike the 120k-line selftest whose file a single page swallowed whole.
TLD weights follow the shape of the observed pages (`com` dominant, `eu` a thin tail).

```
P1 SEEDED f0=0.5952          -> FAMILY_PRESENT in 1 of 10 pages
P2a OLD f0=0.8500, budget 3  -> UNCONVERGED    in 3 of 3 pages  window 17.9% of the file
P2b OLD f0=0.8500, budget 10 -> FAMILY_PRESENT in 5 of 10 pages
P3 NEAR-MISS ONLY            -> FAMILY_ABSENT  in 1 of 10 pages (eu,minimede) not promoted)
P5 SEED +/-0.03              -> FAMILY_PRESENT in 5 of 10 pages (both directions)
```

**Converged.** Three things it establishes, and one it does not:

- **OBSERVED:** the seeded schedule converges within the live budget; a ±3% seed error is
  survived; `eu,minimede)` is never promoted into the family interval.
- **OBSERVED, and this is the honest reading of P2:** at a **10-page** budget the *old* seed
  also converges on this synthetic file — in 5 pages rather than 1. The old seed was not
  incapable; it was **too tight on margin for a 3-page budget**. `P2a` reproduces the live
  `UNCONVERGED` exactly (window 17.9% of the file against the live run's 18.9%), which is
  the useful half.
- **NOT established by any selftest, then or now:** whether an `ABSENT` verdict from a
  straddling key pair means anything on a real `cluster.idx`. The synthetic file is keyed
  per URL, so its absence proof is *valid by construction on data the proof assumes*. A
  synthetic keyspace cannot falsify an assumption baked into its own construction. That is
  the gap this run fell into, and §4 is the live observation that closed it.

**Why "realistic size" is the right bar, measured.** The 2022-27 locate pages run 30,000–35,000
lines per 4,194,304 B, i.e. **~130 B per line**; at 153,702,643 B that is **~1.18 M lines** in
the real file. The synthetic file's **2.0 M lines at 108,905,444 B** is therefore the same
order in both dimensions, not a small stand-in.

**And the difference that matters is not size, it is what a line *is*.** In the synthetic file
one line is one URL. In a real `cluster.idx` one line is one **CDX block**, ~3000 records
(§4). A synthetic keyspace built one-URL-per-line therefore cannot reproduce the real
keyspace's granularity, which is precisely why every assertion above passed while the live
absence proof was false.

---

## 4 · The defect — the absence proof is invalid for `cluster.idx`

The key-only control gate **did not pass**, and it did the right thing:

```
control gate (KEY-ONLY, run 1) -- NOT PASSED
  CC-MAIN-2022-27 -> FAMILY_ABSENT (expected FAMILY_PRESENT)
  CC-MAIN-2024-42 -> FAMILY_ABSENT (expected FAMILY_ABSENT)
```

`CTRL_A` was expected to carry a family member — area L's committed CDX record has
`CC-MAIN-2022-27` answering `200` with **9 records** including
`/ipro/hcp/index.jsp` at status `200`
[source: findings-log/2026-10-17-sl2-outwindow-census/FINDINGS.md §F2]. The gate withheld
every family claim, which is why no key-only `FAMILY_ABSENT` is published here as a verdict.

The bisection's evidence for that `FAMILY_ABSENT` was the adjacent pair

```
a = eu,mini-parfemy)/wp-content/uploads/2021/12/img_3566.jpeg 20220628223311
b = eu,minimumwaste)/profile/donaldcittadini13413661/profile  20220701010643
a < FAM_LO   (0x2D '-' < 0x6D 'm' at index 7)
b >= FAM_HI  (0x75 'u' > 0x65 'e' at index 8)
```

**`cluster.idx` is not keyed per URL.** It carries one line per CDX **block**, keyed by
that block's **first** SURT key, with the block's gz file, offset and byte length:

```
<first surt key>\t<cdx-NNNNN.gz>\t<gz offset>\t<gz byte length>\t<block ordinal>
eu,minebook)/betatester/225 20220705182145\tcdx-00187.gz\t354126685\t180048\t749075
```

**OBSERVED** — that is a verbatim line from the committed body of this run's 5th locate
page, and every one of the 20,190 lines in that page has the same 5-column shape.

So a block's key bounds its whole **byte range**, not one URL. When two adjacent block keys
straddle the interval, the interval lies **inside the block keyed `a`** — which is exactly
where a present family would live. **A straddling pair therefore cannot establish absence.
It establishes containment.**

**The falsifying observation.** One ranged read of that block — `cdx-00187.gz`,
202,350 B at offset 354,897,930, the block `a` heads —

```
READ: 202,350 bytes gz -> 1,364,544 B plaintext, 3000 records
      keys eu,mini-parfemy)/...  ..  eu,minimumwaste)/.../my-files
      minimed records INSIDE this block: 9
   eu,minimed,carelink)/app/assets/assets/assets/assets/javascript-warning.html
   eu,minimed,carelink)/app/assets/javascript-warning.html
   eu,minimed,carelink)/assets/javascript-warning.html
   eu,minimed,carelink)/ipro/hcp/index.jsp
   eu,minimed,carelink)/patient/entry.jsp?bhcp=1...
   eu,minimed,carelink)/patient/privacypolicy.jsp
```

Nine records, inside the block that the "absence" proof said could not hold them. The verdict
was **false**, and it was false for a structural reason rather than a data one.

**This is the premise `docs/11` flagged and left untested.** AD's own Assumptions block reads
"that `cluster.idx` blocks are keyed by the full first SURT key rather than by registrable
domain ... still labelled INFERRED and never promoted to OBSERVED". This run tested it. The
answer is: blocks are keyed by their first SURT key, so the straddle is containment, so the
key-only absence is unsound. **The presence half is unaffected** — a page whose key falls
inside `[FAM_LO, FAM_HI)` does prove a family member exists, because that key *is* a record's
first key. Only the absence direction was ever wrong.

---

## 5 · The repair, and its result on all three crawls

A sound absence needs a **record-level** straddle inside **one block**: the block's first
record sorts below `FAM_LO`, its last record sorts at or above `FAM_HI`, and no record
between them is in the family. Sorted order then makes the absence a proof. `servedness.py
confirm` does that in one extra read per crawl (the block is already located by the
`cluster.idx` line: file, offset, length). `verify-absence.py` re-derives every `ABSENT`
verdict from the committed bodies at **zero requests** and exits non-zero if any fails.

```
control gate (BLOCK-CONFIRMED, run 2) -- PASSED
  CC-MAIN-2022-27 -> FAMILY_PRESENT  [expected FAMILY_PRESENT]
       block cdx-00187.gz, 3000 records, 9 family
       bisection said FAMILY_ABSENT in 5 pages; pair (eu,mini-parfemy) | eu,minimumwaste))
  CC-MAIN-2024-42 -> FAMILY_ABSENT   [expected FAMILY_ABSENT]
       block cdx-00180.gz, 3000 records, 0 family
       record bracket: eu,minimap)/zoom  ->  eu,minimelts)/
  CC-MAIN-2014-23 -> FAMILY_ABSENT   [target]
       block cdx-00236.gz, 3000 records, 0 family
       record bracket: eu,minimath)/  ->  eu,minimini)/
```

`python3 verify-absence.py` (0 requests) re-reads those bodies and asserts, for each absent
crawl: `first < FAM_LO: True`, `last >= FAM_HI: True`, `family records: 0`, `adjacent
straddle pair: True` — then prints `every ABSENT verdict is record-bracketed inside one
block: sound.`

Both controls now agree with their expected verdicts, **and the gate passes for the right
reason**: `CTRL_A` passes because 9 records were counted, not because a key moved.

---

## 6 · The verdict on `CC-MAIN-2014-23`, and what it rests on

**`CC-MAIN-2014-23` carries no `eu,minimed` record in the block that must contain the
family.** **OBSERVED:** `cluster.idx` is `206`, **153,902,243 B** (unchanged from the
2026-10-18 pass, re-derived from `Content-Range` this run); the seeded bisection reached a
puncturing pair in **5 of 10 pages**; and the block that pair brackets — `cdx-00236.gz`,
196,232 B at offset 186,985,750 — decompresses to **3000 records** running
`eu,mimoa)/...` to `eu,minus273)/...` with **0** records in `[eu,minimed), eu,minimeda)` and
the family's immediate neighbours present and adjacent (`eu,minimath)/` -> `eu,minimini)/`).

That is a statement about the **crawl's keyspace**, not about one URL, and it is stronger
than a CDX `404` — which is what the area asked for.

**Agreement with the CDX record for the same crawl (area L/M's `404`). OBSERVED, and it is
agreement in the only direction available:** the 2026-10-18 pass read
`CC-MAIN-2014-23-index?url=minimed.eu&matchType=domain` under a `200` control and got the
documented absence shape, `404` + `No Captures found`
[source: findings-log/2026-10-18-sl1-cluster-servedness/FINDINGS.md §5–§6]. This run reaches
the same conclusion by a **different surface** — the crawl's own block keyspace rather than
its CDX endpoint — and that is coherence, not independent corroboration: both answers are
Common Crawl's own artefacts, read by this repository. Per `AGENTS.md` §2.1 the count is
**1 source**, so `agrees with`, never `confirms independently`.

**The limit, stated rather than smoothed over.** One block is ~3000 records of a
~1.19 M-line keyspace, and the soundness rests on *which* block was read: the one the
puncturing pair brackets, which is the only block that can contain a family record (a family
record in a later block would make that block's first key `< FAM_HI` and would itself have
been the puncturing key). That argument is **INFERRED** and it is the same invariant the
bisection used — except that it is now applied to the block that *ends* below `FAM_LO` and
then **checked against 3000 actual records** rather than trusted. If Common Crawl ever
tolerates a block whose keys are unordered, this fails; nothing in 9,000 records across
three blocks showed such a case.

---

## 7 · What this establishes, in the repository's terms

| Claim | Label | Source |
|---|---|---|
| A derived seed (`f0 ≈ 0.525`) converges the controls in 5 and 4 pages of 10 | OBSERVED | `locate-CC-MAIN-2022-27.json`, `-2024-42.json`, `-2014-23.json` |
| A fixed `f0 = 0.85` at a 3-page budget yields `UNCONVERGED` with an ~18% window | OBSERVED | 2026-10-18 log; reproduced at 17.9% in `selftest-realistic` P2a |
| `cluster.idx` is keyed per block, 5 columns, block-first-key + gz file + offset + length | OBSERVED | 20,190 lines of seq 8's body; `block-probe.json` |
| A straddling key pair implies containment, not absence | **INFERRED**, and its consequence **OBSERVED** | seq 21 read 9 family records out of the "absent" block |
| The S-L1 `FAMILY_ABSENT` is unsound; `FAMILY_PRESENT` is unaffected | INFERRED from the above | §4 |
| `CC-MAIN-2022-27` carries ≥9 `eu,minimed,carelink)` records, incl. `/ipro/hcp/index.jsp` | OBSERVED | seq 30; agrees with area L's CDX `200`/9-record cell |
| `CC-MAIN-2024-42` carries no `eu,minimed)` record | OBSERVED | seq 31, record-bracketed |
| `CC-MAIN-2014-23` carries no `eu,minimed)` record | OBSERVED | seq 32, record-bracketed; `verify-absence.py` |
| A synthetic keyspace cannot falsify the absence proof it was built to satisfy | **INFERRED**, demonstrated | §3, P1–P5 all passed while the live proof was false |

---

## 8 · What a future pass should and should not do

- **Do not** publish a `FAMILY_ABSENT` from block keys. The instrument now cannot: `confirm`
  refuses to emit an absence without a record-level bracket, and `verify-absence.py` can be
  run over any future ledger at zero requests.
- **Do not** spend 10 pages per crawl on the strength of the old estimate alone. This run
  used 5, 4 and 5. The area's "≥10 pages per crawl" was a **ceiling that was right to set**
  and did not bind; the observed requirement is ~5 with a derived seed, and 3 was never
  enough at any seed.
- **The `index.commoncrawl.org` CDX endpoint answered `504` on 6 of 6 attempts** this run
  across two queries, all re-issued under the counting rule. `AGENTS.md` §7 already records
  that host as unreliable from some hosts. **A connection-level failure is not an absence**:
  the CDX comparison in §6 therefore rests on the 2026-10-18 pass's row, not on this run's,
  and this run's six `504`s discharge nothing.
- **The cheap half of AD stands and is unchanged**: servedness is one ranged read per crawl
  and still classifies correctly (4 of 4 crawls this run: 3 served `206`, 1 absent `404`).

---

## 9 · Defects in this run, recorded rather than tidied

1. **The pre-registered budget was exceeded in *kind*, not in number.** Six block-read rows
   were unplanned. They cost 6 of the 18 unspent requests and produced the finding; without
   them the run would have reported a `NOT PASSED` gate with no cause.
2. **Three aborted `confirm` invocations** (a wrong column index in the block parser, then a
   `Fetcher` attribute typo, then an evidence-pair selector that returned the whole page).
   Two of them cost a request each before failing; both are in the ledger as their own rows.
   The third cost none. The parser's column order was **assumed** from a truncated print
   before it was **observed** in full — the exact shape `AGENTS.md` §6.2 warns about, and it
   is recorded here because it happened.
3. **`selftest-realistic` asserts convergence but cannot assert soundness** (§3). It is a
   convergence test that a reader could mistake for a soundness test. Its docstring says so
   in as many words; the name does not, and the name is what gets quoted.
4. **`spacing.py`'s floor is a floor on send-to-send, not on response-completion-to-send**
   — inherited from the 2026-10-18 instrument and stated there; restated here so this log is
   not read as claiming a stronger property than it measured.

---

## 10 · Files

| File | What it is |
|---|---|
| `servedness.py` | the instrument, copied from 2026-10-18 and extended: `derive`, `selftest-realistic`, `confirm`, `probe-block` |
| `seed-derivation.json` | the zero-request seed derivation (§2) |
| `verify-absence.py` | re-derives every `ABSENT` verdict from committed bodies; 0 requests; exits non-zero on an unsound absence |
| `results.jsonl` | 32 rows, one per request |
| `run.log` | `Fetcher`'s append-only request log |
| `spacing.txt` / `spacing.py` | the accounting re-derivation (§1) |
| `locate-*.json` | per-crawl bisection: state, pages, every page's first/last key |
| `block-probe.json` | the falsifying read of `cdx-00187.gz` (§4) |
| `confirm.json` | block-confirmed verdicts for all three crawls (§5) |
| `control-gate.txt` | both gates: key-only **NOT PASSED**, block-confirmed **PASSED** |

**Closes `docs/11` area AD** — as a **negative about the instrument's absence proof**, with
the target's `FAMILY_ABSENT` published on a sound basis rather than the unsound one, and with
the presence half, the seed fix and the convergence result kept as positives.

---

## Correction (2026-11-10)

Four defects found by a fresh-context verifier after this log merged. The findings and the
block-level evidence are unaffected — the containment arithmetic, the 9 records, the seed
derivation and the three verdicts all re-checked true. What follows are errors in the prose
*about* that evidence, plus one tool hazard.

**How this section relates to the text above it — stated plainly, because an earlier revision
of this very section got it wrong.** All four defects are recorded here *and* fixed in place:
the itemisation table, the run-split sentence, the byte index, and the exit code. Leaving a
table that visibly does not sum, or a sentence that misdescribes its own ledger, is worse for
a reader than the small break with strict append-only. But that means this log has been
**edited in place as well as corrected**, which is not the pure append-only form AGENTS.md §3
asks for. The first revision of this paragraph claimed "recorded here rather than rewritten in
place", which was false of the very commit that wrote it. What the audit trail actually holds,
stated per item rather than as a blanket reassurance — an earlier revision of this sentence
claimed all four "quote the old text and name the merge SHA", and that was wrong twice over:
**items 1, 3 and 4 quote the superseded wording** (item 1 word-for-word with a whitespace run
collapsed, items 3 and 4 verbatim), **item 2 describes the old state without quoting it, and no
item names a merge SHA** (the hex strings in item 3 are `sha256` body digests, not commits). The
superseded revision is `ec3c1a9` (PR #169), and
`git show ec3c1a9:findings-log/2026-11-10-area-ad-cluster-idx-locate/FINDINGS.md` is the
authority for what the text said before this section existed.

1. **§4's straddle parenthetical cites the wrong byte index for one of its two rows.**
   The superseded line 205 read `a < FAM_LO   (0x2D '-' < 0x6D 'm' at index 8)` — quoted
   here word for word, though with its three-space run collapsed to one, so this is a
   word-level rather than byte-level quotation. The first differing byte is at
   **index 7**, not 8: `a[:8]` is `eu,mini-` and `FAM_LO[:8]` is `eu,minim`, so the
   comparison turns at the `-`/`m` pair in position 7. Index 8 compares `p` against `e`.
   The **relation is true** (`a < FAM_LO` holds, verified by direct string comparison) and
   the second row's index 8 is correct (`u` vs `e` in `eu,minimu` against `eu,minime`) —
   only the stated position of the first is wrong. A wrong index in a correct argument is
   still a defect: a reader checking it would find the claim false and distrust the rest.

2. **§1's itemisation sums to 31, but the ledger holds 32 rows.** The table's own numbers
   are 1+1+2+9+1+5+6 = 25 for the pass, plus 6 block reads = **31**. The unlisted row is
   `seq 23`, a re-issued 8 KiB `head` read of `CC-MAIN-2014-23`'s `cluster.idx` — a
   duplicate of `seq 14`, issued when the first block parse failed. The headline
   **"32 of a 50 cap" is correct** (`wc -l results.jsonl` = 32, and `spacing.py` re-derives
   it); the itemisation merely fails to carry that one re-request. Note this is the second
   time this repository has had a stated count disagree with its own ledger, so the rule
   stands: derive the count from the ledger, never from the itemisation.

3. **§1's run-split sentence is wrong about the shape of the split.** It says "three crawls
   × two runs, the first run of each crawl aborted after its single block read", implying
   3+3. The actual split is **run 1 = seq 21–22** (two reads: `cdx-00187.gz`,
   `cdx-00180.gz`) and **run 2 = seq 29–32** (four reads: `cdx-00236.gz`, `cdx-00187.gz`,
   `cdx-00180.gz`, `cdx-00236.gz`). The conclusion the sentence supports — that the block
   reads were an unplanned repair costing 6 requests — is correct; only the description of
   how they were distributed is not.

   §9.2's "two of them cost a request each" cannot be settled from the committed ledger, and
   an earlier revision of this correction asserted it "under-counts against the three aborted
   block invocations visible in the ledger" — that assertion was **not derived and is
   withdrawn**. What the ledger actually carries: six block rows (`seq` 21, 22, 29–32), every
   one with `attempt=0` and `attempt_tag=block-read`, so **no row is marked as an aborted
   attempt**. Three of them are byte-identical re-reads — `seq` 30 ≡ 21
   (`sha256 a155093a0007`, 202,350 B), `seq` 31 ≡ 22 (`7c71b6191dc5`, 219,913 B), `seq` 32 ≡
   29 (`77401ad33386`, 196,232 B) — which supports "two runs of the same three block reads"
   and nothing finer. Two distinct quantities in §9.2 are **not** derivable from what is
   committed, and they must not be conflated: §9.2 states that **three** invocations aborted,
   of which **two** cost a request each. The ledger records no abort marker at all, so neither
   the number of aborted invocations nor the number that cost a request can be checked against
   it — the honest statement is that both are unverifiable here, not that either is wrong.
   §9.2's own supporting clause, "both are in the ledger as their own rows", is in fact
   falsified by the ledger, which marks no row as aborted; that is a defect in §9.2 recorded
   here rather than corrected above, since §9.2 is the original log and this section is the
   correction to it.

4. **`verify-absence.py` exits 2 when it finds nothing to verify, which reads as a pass.**
   Invoked with no argument it prints `no bodies dir … nothing to verify` and exits **2**.
   A caller testing `if exit != 0` is fine, but a caller testing `if exit == 1` — or a human
   reading "nothing to verify" as "nothing wrong" — would take a silent no-op for a
   successful verification. The bodies live in `.loop/` and are never committed, so this
   is the *default* state for anyone running it from a clean checkout. Changed to exit **3**
   with the message prefixed `NOT VERIFIED`, so the three states are distinguishable:
   0 = verified present/absent as expected, 1 = a verdict failed, 3 = could not run.

None of these change a finding, a verdict or a published claim. They are the kind of defect
that survives a green gate because the gate checks that numbers agree with the page, not
that the page agrees with the ledger it cites.
