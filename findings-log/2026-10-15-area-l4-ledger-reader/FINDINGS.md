# One reader for the area's ledgers — S-L4

**Date:** 2026-10-15 · **Slug:** `2026-10-15-area-l4-ledger-reader` ·
**Claim issue:** #133 · **Reads only:** `findings-log/**/results.jsonl`,
`census-84.txt`, and the passes' own `FINDINGS.md`.

## Request accounting

- **0 of a 0 cap.** Zero requests. `results.jsonl` is present and carries **0
  rows**, which is the correct and complete record for this pass, not a missing
  file.
- **Methods: none.** No `GET`, no `OPTIONS`, no `POST`, no token exchange, no
  authentication, no DNS, no archive host, no Common Crawl API. The literals
  `GET` / `OPTIONS` / `POST` appear here only to record that each was zero.
- **Inter-request delay: ≥2s — not applicable, because there were no requests.**
  No gap exists to report. The rule that would have applied is `AGENTS.md` §8's
  "sleep ≥2s between requests to the same host". Nothing was sent under a host
  lock, because nothing was sent.
- **Where the scope drifted, it was recorded and not sent.** Twice this pass
  wanted a request and did not issue it. Both became successors — **S-L4a** and
  **S-L4b**, the sixth and third entries of the list under `## 8c. Successors`.

The work is a local read. `probe.sh` records the commands that were run; none
none of them can be made to send a request by editing an argument.

## 1. The population, counted before it is read

**Counting rule R1**, recorded here and implemented in `read-area-l.py`'s
`population()` mode, in this order:

1. `git ls-files 'findings-log/**/results.jsonl'` — every committed ledger. **The
   count is deliberately not published** (an earlier revision carried it): it moves
   with every pass that lands a ledger, and it was 43 before this pass added its
   own. Run the command on your tree. Only step 2's answer (8) is meant to be
   stable, and step 2 is re-checked against rule R2 below rather than trusted.
2. Keep a ledger iff its `<date>-<slug>` slug, **past its date prefix**, carries
   `area-l`, `pool-l` or `l7crawl` on a dash boundary. — **8** ledgers.

**8 ledgers, 380 rows.** Per ledger: `7crawl-reissue` 40 · `early-crawl-reissue`
17 · `ipro-hcp` 44 · `ipro-early-crawl-supplement` 12 · `pool-l-crawlcontrol` 20
· `pool-l-ipro-hcp-census` 40 · `pool-s7-l7crawl` 19 ·
`pool-l-ipro-census-cont` 188.

**Rule R2, the check on R1.** R1 is a name rule, and a name rule can be wrong.
Each of the eight was therefore read for its own area statement. All eight
name area L or an area-L successor:

| ledger | its own statement | class |
|---|---|---|
| `2026-10-13-area-l-7crawl-reissue` | `FINDINGS.md:1` "Area L — re-issue of the seven indeterminate crawls, 2026-10-13 (claim #79)" | SOURCE-OBSERVED |
| `2026-10-13-area-l-early-crawl-reissue` | `FINDINGS.md:1` "Area L — early-crawl fill-in" | SOURCE-OBSERVED |
| `2026-10-13-area-l-ipro-hcp` | `FINDINGS.md` `**Area:**` "Tier 3, **L — Recovery of the retired `ipro/hcp` JSF surface**" | SOURCE-OBSERVED |
| `2026-10-14-area-l-ipro-early-crawl-supplement` | `FINDINGS.md:1` "Area L — supplemental independent control of three crawls" | SOURCE-OBSERVED |
| `2026-10-14-pool-l-crawlcontrol` | `FINDINGS.md:4` "**Area:** L successor — per-crawl control that returned records on each named crawl" | SOURCE-OBSERVED |
| **A re-derivation is welcome if it says what changed** — this table is exactly that | — | `CONTRIBUTING-research.md:212` |
| `2026-10-14-pool-l-ipro-hcp-census` | `FINDINGS.md` `**Area:**` "L — Recovery of the retired `ipro/hcp` JSF surface" | SOURCE-OBSERVED |
| `2026-10-14-pool-s7-l7crawl` | `FINDINGS.md:4` "## Area: open successor — re-issue of the seven indeterminate early-era Common Crawl crawls (`CC-MAIN-2013-20`, `-2013-48`, `-2014-10`, `-2015-22`, `-2021-04`, `-2021-25`, `-2022-05`)" — the same seven crawls `pool-l-crawlcontrol` names | SOURCE-OBSERVED |
| `2026-10-15-pool-l-ipro-census-cont` | `FINDINGS.md:1` "Pool L — area L continuation: the census over the 64 unread in-window crawls" | SOURCE-OBSERVED |

**R1 and R2 agree at 8 — and that agreement is not corroboration.** Both rules
are this pass's own work, one author, and §2.1 counts sources by author. It is
consistency, not multiplicity, and is labelled as such here so a later reader
does not upgrade it.

### The population the committed reader was using is 6, not 8

`findings-log/2026-10-15-pool-l-ipro-census-cont/derive.py:169-170` builds its
input list as:

```python
LEDGERS = sorted(glob.glob('../2026-10-1[34]-area-l-*/results.jsonl')) + \
          ['../2026-10-14-pool-l-ipro-hcp-census/results.jsonl', 'results.jsonl']
```

That is 4 from the glob plus 2 named — **6 ledgers**. It misses
`2026-10-14-pool-l-crawlcontrol` (20 rows) and `2026-10-14-pool-s7-l7crawl`
(19 rows): **39 rows, 10.3% of the 380-row population**, **not in the corpus the
census was derived from.** Both are area-L work by their own `**Area:**` lines
above. This is a finding, not a style note: a census that says "re-derived from
the ledgers" was re-derived from six of the eight.

**Rounding rule for that percentage, stated because round 2 found it inline but
unstated, and round 3 found the rule did not produce its own figure.** A share of a
count is quoted to **one decimal place, ROUNDED half-up**, and the exact quotient is
printed beside it: **39 ÷ 380 = 0.10263 → 10.3%**.

⚠ **An earlier revision said "truncated", which is a different operation and yields
10.2%, not 10.3%** — so that sentence's rule and its figure disagreed and only the
figure was right. **Round 1 published `9.7%`, which is not 39/380 under either rule.**
The counts — 39 rows, 380 rows — were right in every revision; only the share was
ever wrong. Round 3's lesson generalises: **a rounding rule that does not reproduce
its own figure is worse than no rule at all, because it looks checkable.**

## 2. What each pass actually wrote — counted, not remembered

| ledger | rows | DATA | CTRL | member field | distinct `role` values |
|---|---|---|---|---|---|
| `2026-10-13-area-l-7crawl-reissue` | 40 | 21 | 19 | `ipro_hcp_urls` | 31 |
| `2026-10-13-area-l-early-crawl-reissue` | 17 | 10 | 7 | `ipro_hcp_urls` | 3 |
| `2026-10-13-area-l-ipro-hcp` | 44 | 31 | 13 | `ipro_hcp_members` (11 of 44 rows) | 30 |
| `2026-10-14-area-l-ipro-early-crawl-supplement` | 12 | 8 | 4 | `ipro_hcp_urls` | 2 |
| `2026-10-14-pool-l-crawlcontrol` | 20 | **0** | 20 | `ipro_hcp_urls` | 2 |
| `2026-10-14-pool-l-ipro-hcp-census` | 40 | 19 | 21 | `ipro_hcp` | 6 |
| `2026-10-14-pool-s7-l7crawl` | 19 | 10 | 9 | **none** | **no `role` key at all** |
| `2026-10-15-pool-l-ipro-census-cont` | 188 | 99 | 89 | `ipro_hcp` | 2 |

**The two component facts that broke the committed reader, each with its own
count.** An earlier draft of this section tried to compress these into one
number ("five schemas, not three") and **that number is withdrawn** — see the
Correction at the end of this file and §2b. The measured facts are:

| | count | command |
|---|---|---|
| rows carrying **no `role` key** | **19 of 19** in one ledger (`pool-s7-l7crawl`, all 19 rows; 0 in the other seven) | `read-area-l.py schemas` |
| rows whose raw status is **opaque** to a `== "200"` test | **19 of 19** in the same ledger; **0** in the other seven | `read-area-l.py schemas` |
| ledgers with **no DATA cell at all** | **1** (`pool-l-crawlcontrol`, 0 DATA of 20 rows) | `read-area-l.py schemas` |
| distinct row **key-sets** across the population | **10** | `read-area-l.py schemas` (rule K1) |
| distinct **member fields** | **3** (`ipro_hcp`, `ipro_hcp_urls`, `ipro_hcp_members`) — the three S-L4 names | `read-area-l.py schemas` (rule K2) |

**S-L4's "three schemas" is not wrong; it is a count of member-field shapes, and
that is exactly what rule K2 measures and returns.** The gap S-L4 named — a
reader that only handles three shapes — is real, but it did not need a fourth or
fifth *schema* to be real. It needed this population to include two ledgers the
committed reader never read.

## 2b. Why there is deliberately no "number of schemas" headline

A count is only meaningful with the rule that produced it, and an earlier draft
of this pass published one without either. `read-area-l.py schemas` now prints
**three separate rules and three separate answers** — K1 distinct key-sets (**10**),
K2 distinct member fields (**3**), K3 three *properties* (no-`role` rows,
opaque statuses, no-DATA ledgers) — and refuses to sum them, because **"no DATA
cell" is a property of what a pass chose to query, not of the shape of a row.**
Adding a row-schema count to a query-derivation count is how "five" was
manufactured from facts that were each individually true.

## 3. The reader, and why one code path is the right shape

`read-area-l.py` resolves the whole population **without ever reading `role`**.

The census's job for a row does not depend on what its author *called* it. It
depends on **what the row queried** — and the query is in `path`, which every
committed schema carries. So:

- **CELL RULE** — a row is part of the DATA cell iff its `url=` parameter is
  `minimed.eu` or `carelink.minimed.eu`. Everything else is CONTROL/OTHER.
  `medtronic.eu` appears as a control target in one ledger and is **not** a data
  target, so it is not folded into the data cell. Stated because getting it
  wrong would silently move a `502` control into a verdict.
- **CRAWL** — from the `path` first (`/(CC-MAIN-\d{4}-\d{2})-index`), from a
  `crawl` field second. The fallback exists because `pool-s7-l7crawl` needs it.
- **STATUS** — resolved to an `int` and `assert isinstance(v, int)`. See §4.
- **VERDICT** — `census-84.txt:18-20`'s own rule, applied per crawl: RECORD if
  the last DATA row answered 200; ABSENCE if 404 and some row for that crawl
  answered 200; INDETERMINATE if 404 with no 200 anywhere; FAILURE otherwise.
  502/504/503/400 is a FAILURE, never an absence.
- **PRECEDENCE** — a later ledger supersedes an earlier one's *verdict*, because
  the manifest is chronological and a later pass is an addendum. Member counts
  are taken from the last DATA row **that both answered 200 and carries a member
  field**, whichever that is; the reader prints every DATA row that could not
  supply a count, so the asymmetry is visible rather than resolved silently.
  This is not hypothetical: it decides `CC-MAIN-2014-10`, whose verdict comes
  from `pool-s7-l7crawl` (2026-10-14) and whose member count can only come from
  `7crawl-reissue` (2026-10-13).
- **MEMBER-SOURCE RULE (the `200` requirement is load-bearing, not decoration).**
  An empty member list on a **404 or a 502** says nothing — the query returned no
  records, so there was nothing to find — and reading it as a zero would convert a
  **FAILURE into an absence**, which `census-84.txt:20` forbids in terms. Only a
  `200` row may supply a count. This is not hypothetical either: `CC-MAIN-2013-48`'s
  only member-carrying DATA row is a **502**
  (`2026-10-14-area-l-ipro-early-crawl-supplement` seq 3), so its count is
  **not derivable from the tree** and the reader prints `NOT DERIVABLE` rather
  than `0`. See the Correction at the end of this file.

**A mapping table a human fills in would have been the wrong deliverable.** It
would restate the free-text `role` vocabulary as a second table someone has to
keep true, and nothing in the tree would check it. A per-cell derivation is
checked by `self-test`.

## 4. Two traps this reader had to be built not to fall into

**A string that looks like a status code.** `2026-10-14-pool-s7-l7crawl` writes
`"http_status": "200 (curl)"`, not `200`. The status comparison the committed
reader uses, `r['http_status'] == '200'`, is **False** for every row of that
ledger. This is `AGENTS.md` §6 item 3 in its most literal form in this tree: a
comparison that cannot distinguish a `200` from nothing, and would report a
crawl as unread rather than read. The reader resolves to `int` and asserts the
type.

⚠ **The first version of this section claimed `self-test` "exercised" that trap
by asserting `('200 (curl)' == '200') is False`. That check was vacuous**: it
compared two literals, so it was False by construction and could not fail
whatever the reader did — a control wearing a control's name. It is replaced by
two checks that read the **committed 19-row ledger**: a raw `== "200"` test finds
**0 of 19** rows, while the reader resolves **10 of 19** to an `int` 200. If the
reader stopped normalising, the second check fails. See the Correction.

**A row with no member field is not a row with zero members, and an empty member
list on a non-200 row is not a zero either.** `members_of()` returns `None`,
never `0`, when no recognised member field is present; and `derive()` will only
take a count from a row that **answered 200**. A zero, an absence and a
not-derivable are three different facts and the reader does not merge them —
`CC-MAIN-2013-48` is the cell where the third appears.

## 5. The controls — internal, and stated as such

**These are internal controls. They are not network controls and nothing here
speaks to a vendor surface.** They are the controls this area's own brief names,
and each is exercised by `python3 read-area-l.py self-test` (exit 0, **33
checks, 0 failures**). The count is **printed by the test function itself** and
is not asserted here: `grep -c PASS` over that output would over-count by one,
because the summary line contains the word `PASS` — which is how an earlier
draft of this pass published "23 checks" for 22.

| control | what it does | how it can fail |
|---|---|---|
| **Population** | R1 then R2, both recorded above, applied before any row is interpreted | a name rule that matched nothing would print a population of 0 and read as a clean negative |
| **Arithmetic** | rows read == rows in the population, compared as `int` | `SystemExit` on mismatch; `assert isinstance(len(recs), int)` before the comparison |
| **Exhaustiveness** | every ledger in the population contributes ≥1 record; the manifest must equal the population exactly; an empty output over a non-empty population is a `SystemExit`, not `ok` | a crawl whose rows are all controls yields **no verdict** (`None`), which `self-test` asserts |
| **Negative — rows** | 5 synthetic rows the reader must **refuse**: an `ipro_hcp` entry with no timestamp, a member field that is a bare string, `ipro_hcp_count` disagreeing with its list, a member dict with no `ts`/`path`, a URL that does not parse | each raises `Unreadable`; the check fails if the row *parses* |
| **Negative — integration** | one unreadable row appended to a **real** 40-row ledger | `read_ledger` raises `SystemExit` — the census refuses to print over 40 of 41 rows; with `--allow-unreadable` it keeps 40 records and records 1 UNREADABLE instead of dropping it |
| **Negative — vacuity** | the status trap is checked over the **committed 19-row `s7` ledger**, not over two literals | a raw `== "200"` finds 0 of 19; the reader must resolve 10 of 19. Stop normalising and this fails |
| **Member-source** | only a `200` DATA row may supply a member count | a lone `502` row with an empty list must yield `None`, not `0` — checked both ways |

The integration control is the one that matters. A reader that downgraded an
unreadable row to a warning would emit a census over 8 of 9 rows and call it
complete. The repo has the precedent this is modelled on: a `scrub-check.sh`
that resolved the repo root one level too high, iterated zero patterns, and
printed `PASS`.

**Set difference.** Any set difference this pass needed was taken over inputs
sorted with `LC_ALL=C sort -u`; the manifest/population comparison above is done
with Python `set` difference over a list already in `LC_ALL=C` order rather than
`comm`, because an unsorted `comm` warns and returns a wrong answer without
failing (`docs/09` §4).

## 6. The result — and the two cells that move

`older-schema` goes to **zero**. All eight resolve to a named row, and the
reader prints that row's ledger and `seq` for each (§5 of its own output):

| crawl | verdict | resolved from | members |
|---|---|---|---|
| `CC-MAIN-2013-48` | **ABSENCE** | `pool-s7-l7crawl` seq 6 (404, behind a 200) | **NOT DERIVABLE** — no DATA row of this crawl answered 200 in any ledger, so the tree holds no member count. It is not a zero. |
| `CC-MAIN-2014-10` | **RECORD** | `pool-s7-l7crawl` seq 9 (200) | **1** |
| `CC-MAIN-2015-06` | **RECORD** | `ipro-hcp` seq 43 (200) | 0 |
| `CC-MAIN-2015-22` | **RECORD** | `pool-s7-l7crawl` seq 12 (200) | 0 |
| `CC-MAIN-2017-04` | **RECORD** | `ipro-hcp` seq 28 (200) | 0 |
| `CC-MAIN-2019-51` | **RECORD** | `ipro-hcp` seq 29 (200) | 0 |
| `CC-MAIN-2020-24` | **RECORD** | `ipro-hcp` seq 38 (200) | **3** |
| `CC-MAIN-2021-25` | **RECORD** | `pool-s7-l7crawl` seq 16 (200) | 0 |

**Five of the six `0`s above are the *same* kind of claim, and one now is not.**
The five are read off `200` rows and rest on the internal-consistency argument
in §7. The sixth — `CC-MAIN-2013-48` — has no `200` row at all, so under the
member-source rule its count is **not derivable**. **No headline number moves
either way**: `census-84.txt` scored it `0`, and a not-derivable cell is not
carried in the member tally, so RECORD, ABSENCE, the member counts and the
in-window total are unchanged. The difference is honesty about what the tree
holds, not a different census.

**Cell-by-cell against `census-84.txt`, both values standing** (`AGENTS.md` §2 —
where sources disagree, give both; never pick one silently):

| cell | `census-84.txt` | re-derived | |
|---|---|---|---|
| published indexes | 128 | 128 | agree |
| in window | 84 | 84 | agree |
| RECORD | 65 | **72** | **differ** |
| ABSENCE | 10 | **11** | **differ** |
| INDETERMINATE | 1 | 1 | agree |
| FAILURE | 0 | 0 | agree |
| older-schema | 8 | **0** | **differ** |
| UNREAD | 0 | 0 | agree |
| crawls carrying ≥1 member (any window) | 11 | **13** | **differ** |
| …of which in window | 10 | **12** | **differ** |
| total in-window members | 35 | **39** | **differ** |

72 + 11 + 1 + 0 = 84, so the re-derived tally accounts for every in-window
crawl with none unassigned.

### `older-schema` was not a gap in the census. It was a gap in the parser, and it had already cost two cells

`census-84.txt:22-28` says this in its own header note: the eight crawls marked
`older-schema` "WERE read … and their verdicts are in those passes' logs". The
label is a parser bail-out, at
`findings-log/2026-10-15-pool-l-ipro-census-cont/derive.py:182-185`:

```python
probe = [r for r in rs if r.get('role') in ('probe-domain', 'probe-host', 'control-positive')]
if not probe:
    AV[c] = 'older-schema'
    continue
```

**It is worse than a missing label: two of the eight carry `/ipro/hcp/*` members
that the census's headline does not count.**

**`CC-MAIN-2020-24` carries 3 members.** SOURCE-OBSERVED, one source:
`2026-10-13-area-l-ipro-hcp/results.jsonl` seq 34 (`http_status` 200,
`record_count` 7, `ipro_hcp_count` 3, members `/ipro/hcp/index.jsp` 302,
`/ipro/hcp/login.jsf` 200, `/ipro/hcp/main/home.jsf` 302, all
`carelink.minimed.eu` @ `20200527212918-19`), repeated at seq 38 and tabulated at
that pass's `FINDINGS.md:549` (`| CC-MAIN-2020-24 | … | 30, 34, 38 | 504, 200,
200 | 7 | **3** |`) and `:265-267`.
`census-84.txt:102` scores it `older-schema` with `ipro_members 0`, and the
eleven-crawl list at `census-84.txt:168` does not contain it.

**`CC-MAIN-2014-10` carries 1 member.** SOURCE-OBSERVED, one source:
`2026-10-13-area-l-7crawl-reissue/results.jsonl` seq 21 (`http_status` 200,
`records` 1, `ipro_hcp_urls` `["https://carelink.minimed.eu/ipro/hcp/login.jsf"]`),
repeated by the host-scoped query at seq 22, and tabulated at that pass's
`FINDINGS.md:55` (`| CC-MAIN-2014-10 | 19 504, 20 502, 21 200 | 200 | 1 | 22 200
| 200 | 1 | 1 (/ipro/hcp/login.jsf, 2014-03-10, status 200) | capture |`).
`census-84.txt:36` scores it `older-schema` with `ipro_members 0`, and again it
is absent from the list at `:168`.

**Both are one source each, and the agreement is not corroboration.** The
2026-10-14 pass's `FINDINGS.md:277` cites `CC-MAIN-2020-24` and marks it
**`prior`** — it is quoting the 2026-10-13 pass, not measuring it again
(`AGENTS.md` §2.1, artefact 3). Same for `docs/11-suggested-research-areas.md`'s
own member list — `grep -n 'CC-MAIN-2020-24' docs/11-suggested-research-areas.md`
resolves it — which already records both crawls' members and marks them
`(prior)`. **One source, three times quoted.**

**The repo therefore already contradicted itself, and the contradiction was
visible without any new evidence.** `docs/11`'s family table lists
`CC-MAIN-2014-10 /ipro/hcp/login.jsf` at 2014-03-10, and the row below it lists
`CC-MAIN-2020-24`'s three paths, while `census-84.txt:36` and `:102` score both
crawls `older-schema` with **0** members and its member tally excludes them. The
pass that wrote `census-84.txt` did not have to be wrong about Common Crawl to
produce that; it had only to have a reader that could not see two ledger shapes.

### One cell is mis-framed in the committed census, and not because of any schema

`census-84.txt:168` publishes **11** crawls carrying a member, and its list
includes `CC-MAIN-2022-27` — which `census-84.txt:119` itself marks
`in_window` = `no`. So its **11 is 10 in-window + 1 out-of-window**, while every
tally directly above it on that file is scoped "IN-WINDOW crawls only"
(`census-84.txt:161`). Both framings are printed by the reader rather than one
being chosen. This is a separate defect from the schema change and is left for a
successor to close, because correcting `census-84.txt` is a page this pass does
not own.

### A third instance of this pass's own class, on the same page, found by its own figure

> ### ⚠ THIS PASS PUBLISHES NO `docs/NN:NNNN` POINTERS. THE GREPS ARE THE CITATION.
>
> Every pointer of that shape that has appeared in this file is stale or was stale
> within one commit. **The mechanism is not carelessness: this PR inserts lines into
> `docs/11` above most of the passages it cites, so any pointer past the S-L4 block
> moves the moment this PR lands.** (Round 4 recorded the inserted-line count as a
> number; the number is now itself a position, for the same reason.) Round 1 pointed
> at an unrelated area-F passage; round 2 corrected it; round 3 found that one stale
> too. **Correcting the numbers would fix four instances of a bug that has fired in
> every round**, so they are removed instead.
>
> **`dup-test.sh` is the single source for all of them**, and it derives every line
> number by `grep`, prints what each line actually contains, **and exits non-zero**
> if this file publishes a position in any spelling outside its Correction
> sections — so the policy is enforced by the artefact rather than asserted by the
> prose that states it:
>
> ```sh
> sh findings-log/2026-10-15-area-l4-ledger-reader/dup-test.sh
> ```

**No terminal position is published here, deliberately.** Round 4 caught this file
asserting one that was stale on the very SHA it shipped in: a "measured, now"
figure naming the *previous* commit's value. **Any position stated here expires on
the commit that adds lines above it, and this file is the thing adding them.** So:

> A position is never published in this file. Cite `locate.sh` — which resolves
> every landmark by content and prints the commit it measured at — or cite the grep.

The positions this file published and has now **withdrawn** are named in the
Correction sections below, because `AGENTS.md` §5 requires a correction to say what
it withdrew.

> **The one exception, deliberate.** The `## Correction` sections quote `docs/NN:NNNN`
> pointers **as history** — "superseded: `:2218`" — because `AGENTS.md` §5 requires
> corrections to be *preserved*, not smoothed over, and a record that deleted the
> wrong number would destroy the evidence it records. `dup-test.sh` therefore checks
> for pointers **outside** those sections and prints which it excludes.

The sentence — `"/ipro/hcp/ is absent from 65 of the 84 in-window crawls"` —
appears in three places, named here **without line numbers**:

| where | how to find it |
|---|---|
| **`docs/11`'s area-L addendum** | `grep -rn 'absent from 65 of the 84' docs/` |
| **`docs/11`'s Closed-area row `L`** | the same grep — this area's row in that table |
| **`docs/10`'s §1 row for this area** | the same grep — and that row contradicts itself internally |

> **`/ipro/hcp/` is absent from 65 of the 84 in-window crawls**

**That reconciles with neither available reading, and the arithmetic is the
check:**

| reading | in-window RECORD | absent = 84 − RECORD | states |
|---|---|---|---|
| `census-84.txt` as committed | **65** | **19** | absent from **19** |
| this pass's re-derivation | **72** | **12** | absent from **12** |
| area-L addendum in `docs/11` / Closed row `L` in `docs/11` / this area's row in `docs/10` §1 (no line numbers — see the recipe above) | — | — | absent from **65** |

**65 is the census's RECORD cell read into the *absent* slot.** Under the
committed census the correct absent count is 19, not 65; under the re-derivation
it is 12. The same 65 cannot be an absence count under either, and 84 − 65 = 19
is exactly the number the committed file supports.

**Recorded, not fixed.** All three are out of this pass's lane — two in `docs/11`
(area prose, and its Closed table) and one in `docs/10` §1 — so the finding is a
successor **S-L4d** in §8c, with all three readings standing.

**And the third instance is the one that makes the class undeniable: the
`docs/10` §1 row carrying this area's census** (found by the same grep), which
reads *"`/ipro/hcp/` is
absent from 65 of the 84"* in the same breath as *"`65 RECORD · 10 ABSENCE · 1
INDETERMINATE · 0 FAILURE`"* — **two sentences contradicting each other within one
table row**, checkable by reading a single line rather than by subtracting across
files. **It was found by the `grep` that finding 2 required**, not by a re-reading:
`grep -rn 'absent from 65 of the 84' docs/` returns five hits, three of them
pre-existing instances. That is the honest account of how it was found — the
mandated test found a finding the pass had missed twice. It is worth naming that this pass hunted this exact class twice
(the `docs/11` family table against `census-84.txt:36`/`:102`), wrote a successor for
each, and **missed a third instance on the same page** that its own new figure
made checkable in one subtraction.

**⚠ And this pass then pointed a reader at the wrong line — in every round since.**
Round 1 cited a `docs/11` line that does not contain the sentence; round 2 corrected
it to another; round 3 found *that* one stale as well. Each pointer was wrong by
roughly the number of lines **this PR inserts into `docs/11` below the target**, which
is the whole mechanism: the citation dies when its own PR lands.

**So the fix is the mechanism, not the number** — see the recipe at the head of this
section. No `docs/NN:NNNN` pointer is published in this file outside the Correction
sections, and `dup-test.sh` now *checks* that and prints **STALE** if one appears, so
the policy is enforced by the artefact rather than asserted by the prose it is in.

**A citation pointing at a passage that does not contain the claim is `AGENTS.md` §6
item 6, and the reason it survived rounds here is that the claim it carried was true**
— the worst way for a broken citation to survive.

## 7. What this reader cannot settle — the assumption, kept INFERRED

S-L4's stated assumption was that the three schemas carry the same facts. **This
reader does not settle it, and the honest answer is that it cannot be settled
from the tree.** What it does instead is measure the gap:

| member shape | rows carrying it | path | host | timestamp | HTTP status |
|---|---|---|---|---|---|
| `ipro_hcp` | 228 | yes | yes | yes | yes |
| `ipro_hcp_urls` | 89 | yes | yes | **NO** | **NO** |
| `ipro_hcp_members` | 11 | yes | yes | yes | yes |

- **Demonstrated (for the count and for path/host):** all three shapes normalise
  to the same record, and `self-test` asserts it on one fact written three ways.
- **NOT demonstrated (for timestamp and HTTP status):** `ipro_hcp_urls` carries a
  URL and nothing else. The `2014-03-10` and `200` that the census prose gives
  for `CC-MAIN-2014-10` live in that pass's `FINDINGS.md:55`, **not in its
  ledger.** The reader normalises the count and refuses to invent the rest.

**The second and larger limit, stated rather than smoothed over.** An empty
member list on a `200` row is read as a **zero** because the same ledger
populates the same field on a sibling crawl that does have a member — in
`7crawl-reissue`, seq 21/22 carry 1 member for `CC-MAIN-2014-10` and seq 25/26
carry an empty list with `records: 1` for `CC-MAIN-2015-22`. That is an internal
consistency argument **inside one pass's ledger**. It is not a demonstration
that the field was computed on that particular row, and the bodies that would
demonstrate it are outside the tree by policy (`AGENTS.md` §7). **The five zeros
in §6 rest on this argument, and it is labelled INFERRED rather than folded into
the table above.**

**So: the reader closes the *defect*. It does not close the *assumption*.** One
reader over the whole population, 8 of 8 resolved, no manual reading — and the
equivalence claim left standing as INFERRED, with the specific field-level reason
it is not yet a fact.

## 7a. The one thing that would have closed it, and did not

Every **member** resolution in §6 rests on a `200` row whose ledger already
carries the member list — the reader reads, it does not compute. So the
assumption is not "can a reader normalise three shapes" (it can, and `self-test`
asserts it); it is **"does a committed `200` row's member list enumerate every
member in that crawl"**. That is a property of Common Crawl's NDJSON pagination,
of what those bodies contained, and of what each pass chose to scan — and **no
artefact in this tree can demonstrate it**, because the bodies are excluded by
`AGENTS.md` §7.

Two things follow, and both are limits rather than results:

- **A non-zero count may be a floor.** See **§7b**: this was stated here as an
  open possibility, and §7b narrows it — two of the three mechanisms are measured
  and excluded, leaving completeness of the record set as the only undemonstrated
  one. Nothing here claims an upper bound on any crawl's members.
- **A `0` is only as good as the row it came from.** Which is why `CC-MAIN-2013-48`
  is now **NOT DERIVABLE** rather than `0`: its only member-bearing DATA row is a
  **502**, and an empty list on a failed query carries no information at all.

Closing this needs either the bodies (a disclosure decision, not a research pass's)
or a ledger field distinguishing "computed, found none" from "not computed"
(successor §8c.3). Both are named; neither is claimed.

### 7b. ⚠ NARROWED by §8b — two of the three mechanisms are now MEASURED AND EXCLUDED

Round 2 of the verifier confirmed the substance but could not close the carriage,
and running `docs/10` §1's own test changed what can honestly be claimed. The floor
argument above is **correct but was stated as an open possibility when two of its
three mechanisms are measurable from the committed tree.** They now are:

| mechanism | status | measurement |
|---|---|---|
| **`limit=` tail truncation** — `docs/10` §1: "a `limit` truncates from the **tail**, keeping the head of the SURT range" | **MEASURED, excluded for every qualifying row but the two that reached their own limit.** Cell **A** (per row — the cell that bears on the figures): **79 of 81**. Cell **B** (one per crawl — what `derive()` counts): **73 of 74** | 74 rows: **68** carry no `limit=`, **6** carry one, and of those 6 only **1 reached it** — `CC-MAIN-2020-50`, `pool-l-ipro-hcp-census` seq 7, records 5, limit 5. **Carrying a limit and reaching it are different predicates**, and only the second can cut a tail. Computed by `kib-detector.py` RULE 3 (§8b) |
| **whole-KiB truncation** — the detector `docs/10` §1 defines and `docs/10` §1's successor names | **MEASURED, excluded** | **0 candidates across 193 successful `200`s** over the whole population (§8b) |
| **completeness of the record set** — did the pass enumerate every member, or only what one response body held | **NOT MEASUREDABLE OFFLINE** | the bodies are excluded by `AGENTS.md` §7; `docs/10` §1 says of its own detector that *"clean for this test is not the same as complete"* |

**So the surviving claim is one mechanism wide, not three:** not "these counts
might be floors" but **"these counts are not floors *by truncation*, and
completeness remains undemonstrated."** A reader may not use §7a's original
phrasing, which was broader than the evidence supports. Every member figure is
still a **lower bound** — `≥3` is what the tree supports for `CC-MAIN-2020-24`, and
the reader prints it as a count because that is what the ledger holds, not because
the count is exact.

## 8. Successors

### 8b. The non-duplicate test, run for real — `CONTRIBUTING-research.md:199`

The quality bar for a successor fails it when it "is already in `docs/10` §1,
already in the Closed table, or already on the page — **grep both first**". Round
2 of the verifier found this pass never ran that grep for any of its four
successors, and pointed out that the absence of a recording the bar asks for is
itself the finding. **It is run now**, by `dup-test.sh`, which greps three
surfaces — `docs/10` §1, the `docs/11` Closed table, and `docs/11` whole — and
derives the section boundaries **by grep rather than by typing them**:

```
docs/10 section 1        the span between the '## 1. Open questions' and
                         '## 2. Searched and closed' headings
docs/11 Closed table     the line matching '^## Closed areas'
```

**Both are stated as greps because this PR edits `docs/11`, so every number a
reader copied from it expired when the PR landed.** Four review rounds found that
same defect at a new coordinate each time — because every fix added lines. The
coordinates themselves are deliberately **not reproduced here**: printing them is
the very defect under discussion, and an earlier revision of this paragraph was
one of the offenders. What the file offers instead is a resolver —
**`locate.sh` resolves every landmark this file names, by content, bound to the
commit it measured at:**

```sh
sh findings-log/2026-10-15-area-l4-ledger-reader/locate.sh
```

### The recorded table — and why this file does NOT carry one

Round 4 compared the table this section used to record against live output from
the script that produces it and found it **did not reproduce**: S-L4b `floor`
recorded **31** and read **30**; S-L4b `truncat` recorded **3** and read **5**.
**Transcription is what let it drift**, and §9's entire purpose was to make that
manual step unnecessary. So there is no table here, only the command:

```sh
sh findings-log/2026-10-15-area-l4-ledger-reader/dup-test.sh
```

It prints the hit count for every successor-subject against **three** surfaces —
`docs/10` §1, `docs/11` whole, and the Closed table — with the section boundaries
derived by grep. **What the reader must take from those counts, and nothing more,
is written below**; a count that a reader might want to quote is quoted by
re-running the script, never by copying this file.

**S-L4b's overlap is real and S-L4b is narrowed because of it.**
`docs/10` §1 already carries the question *"how many already-committed Common
Crawl record counts in this repo are floors rather than measurements?"* — answered
for area M, with the whole-KiB detector, and with its own successor: *"the same
one-command test over every other committed CC ledger."* `docs/10` §1 also already
answers the truncation half: **"a `matchType=domain` record query carrying **no
`limit`** is not truncated at these sizes"**, and *"a `limit` truncates from the
**tail**, keeping the head of the SURT range"*.

**So the general floor question is NOT this pass's to ask.** What remains
un-asked is narrower and is what S-L4b now says: the detector named there has
never been run over **area L's** ledgers, and S-L4b's own contribution is the
result of running its rule over this population.

**Run now, at zero requests**, by **`kib-detector.py`** — a committed script, because
round 3 found this table had **no artefact behind it**: `grep -rniE '1024|kib|193'`
over this pass's `.py`/`.sh` returned nothing, so the number was reproducible only by
hand. `AGENTS.md` §6 item 7: a count whose rule is not shipped is a typed number
wearing a script's name.

```sh
python3 findings-log/2026-10-15-area-l4-ledger-reader/kib-detector.py          # both cells
python3 findings-log/2026-10-15-area-l4-ledger-reader/kib-detector.py --json   # machine-readable
```

**RULE 1** — the detector's own rule, quoted from `docs/10` §1: *a record response
whose `body_bytes` is an exact multiple of 1024 was cut short, and one whose byte
count is not, ran to completion.* A correlation over the rows observed, never a proven
mechanism — `account.py`'s own docstring says so.

**RULE 2 — and this is what round 3 flagged: "successful `200`" needed stating.**
A row counts when the reader's own `status_of()` resolves it to the int 200. Every
`http_status` in this population is a JSON **string** (all 380 rows), and
`pool-s7-l7crawl` writes the opaque form `"200 (curl)"`. Three obvious rules give
three different answers, and the script prints all three:

| rule | rows |
|---|---|
| `raw == 200` (int) | **0** — misses every row |
| `raw == "200"` (exact string equality) | **183** — misses the opaque rows |
| **`status_of(row) == 200` (used)** | **193** |

The gap between the last two is exactly the **10** `"200 (curl)"` rows in
`pool-s7-l7crawl`. A reader applying the obvious rule gets 183 and concludes the
published figure is wrong, with no way to tell which is right — `AGENTS.md` §6 item 3.

**RULE 3 — the companion member-source cell, computed by the same script.** A
**member-source row** is one where the reader's own predicates agree on all three:
`query_of(row) in DATA_TARGETS`, `status_of(row) == 200`, and `members_of(row) is not
None`. **There are three such populations**, and round 3 caught this pass publishing a
numerator from one beside a denominator from another:

| cell | rows | carrying a `limit=` | carrying none | **at** their own limit | carried one, did not reach it |
|---|---|---|---|---|---|
| **A** every qualifying row | **81** | 9 | 72 | **2** | 7 |
| **B** one per crawl — what `derive()` uses | **74** | 6 | 68 | **1** | 5 |
| **C** B restricted to in-window | **72** | 5 | 67 | **1** | 4 |

**⚠ "Carrying a `limit=`" and "reaching it" are different predicates, and only the
second can cut a tail.** Cell **B** — what `derive()` actually counts — has **1** such
row, and cell **A** — every qualifying row, the cell that bears on the figures — has **2**: `CC-MAIN-2020-50`, `pool-l-ipro-hcp-census` seq 7, records 5, limit 5. Round 3's
re-derivation, made by *importing* this reader's predicates rather than reimplementing
them, returned **81 / 9 / 72 / 2** — cell **A** — which is right for the question it
asked. **The withdrawn figure `69 / 67` matched no cell at all** — `69` is not any
cell's row count (A is **81**, B **74**, C **72**), and `67` is cell **C**'s
"carrying none". The clause therefore mixed two cells in *both* directions, and
**the row counts, not just the split, were unverifiable from any rule this file
had shipped.** Both cells are now computed by a shipped script under a stated
rule, so a number can only be disputed by disputing the rule, which is visible.

| ledger | successful `200`s (RULE 2) | whole-KiB candidates (RULE 1) |
|---|---|---|
| `2026-10-13-area-l-7crawl-reissue` | 13 | **0** |
| `2026-10-13-area-l-early-crawl-reissue` | 3 | **0** |
| `2026-10-13-area-l-ipro-hcp` | 15 | **0** |
| `2026-10-14-area-l-ipro-early-crawl-supplement` | 2 | **0** |
| `2026-10-14-pool-l-crawlcontrol` | 10 | **0** |
| `2026-10-14-pool-l-ipro-hcp-census` | 20 | **0** |
| `2026-10-14-pool-s7-l7crawl` | 10 | **0** |
| `2026-10-15-pool-l-ipro-census-cont` | 120 | **0** |
| **total** | **193** | **0** |

**Zero candidates across 193 successful answers — the member counts are not floors
*by this detector*.** `body_bytes` is present on **193 of 193** of them, 143 distinct
values from 40 B to 1 280 724 B, none ≡ 0 mod 1024.

**⚠ And `docs/10` §1's own caution applies verbatim: "Clean for this test is not the
same as complete" — a truncation not aligned to 1024 would be invisible to it.**

**⚠ And `account.py` is handed on broken.** Run exactly as `docs/10` §1's successor
directs ("the same one-command test over every other committed CC ledger"), it
**crashes on a member of this very population**: `2026-10-13-area-l-ipro-hcp` seqs 1–4
carry a null `t_sent`, and `account.py:109` calls `strptime(None)` → `TypeError`.
Recorded-not-fixed is right for the **code** — another lane's file — and **not enough
for the handoff**, because the row naming the tool still stands. Carried as successor
**S-L4e** (the sixth entry in §8c).

**So the floor claim of §7a is NARROWED, not retired.** Under cell **A** (per row — the cell
that bears on the figures) the `limit=` mechanism is measured and excluded for **79 of
81** qualifying rows; under cell **B** (one per crawl, what `derive()` counts) for **73
of 74** (1 is AT its limit); the whole-KiB mechanism for **all 193**. **What remains undemonstrated is
completeness of the record set itself**, which no artefact in the tree can settle
because the bodies are excluded by `AGENTS.md` §7.

### 8c. The successors

1. **The eleven-crawl member tally is mis-scoped, and correcting it is a page
   this pass does not own.** `census-84.txt:168` counts 11 while every tally
   above it is in-window-only, and its list contains the one out-of-window crawl.
   **Blocker:** the correction belongs in `census-84.txt` and in the area-L prose
   in `docs/11`, both outside this pass's lane. **Closes when** the member tally
   states its window basis and `CC-MAIN-2022-27` is either excluded from it or
   named as the single out-of-window entry. **Zero requests.**
   **Assumptions (INFERRED):** that "crawls carrying a member" was meant to be
   in-window, since that is how the tally block above it is scoped — the header
   does not say so, and the reader publishes both framings rather than choosing.
2. **The two member-carrying cells the `older-schema` label hid.**
   **Blocker:** none, zero requests — the evidence is already in the tree and this
   pass has reduced it to named rows. **Closes when** `CC-MAIN-2014-10` and
   `CC-MAIN-2020-24` carry their members in the canonical census and the
   member count reads 39 in-window, or a later pass re-derives a different figure
   and both are published. **Assumptions (INFERRED):** that the three
   `/ipro/hcp/*` paths in `CC-MAIN-2020-24` are three distinct captures rather
   than one capture seen three times; the ledger's three distinct timestamps
   (`…212918`, `…212919` ×2) are consistent with either reading and the
   re-derivation does not settle it.
3. **NARROWED by §8b — the general floor question is already `docs/10` §1's, and
   this pass has run that row's own successor over area L.** What is left is the
   completeness of the record set, which the whole-KiB detector cannot reach.
   **Blocker:** the response bodies are outside the tree by `AGENTS.md` §7, so
   "does a committed `200` row's member list enumerate every member in that crawl"
   is undemonstrable offline. **Closes when** either the bodies are made available
   under a disclosure decision, or every ledger row carries a field distinguishing
   "computed, found none" from "not computed" — a `shape` field as `ipro-hcp`
   already has, or an explicit `members_computed`. **Zero requests** for the second
   route. **Assumptions (INFERRED):** that a boolean in the ledger is enough for the
   second route; nothing in the tree says a later pass would populate it.
   **Already done and not re-offered:** `docs/10` §1's own successor ("the same
   one-command test over every other committed CC ledger") has been run here —
   **193 successful `200`s, 0 whole-KiB candidates** (§8b) — so that half must not
   be claimed again by a successor.
4. **One reader for the committed ledgers outside area L** (the claim's own successor,
   carried here unchanged in substance). **Blocker, weakened from what this pass
   first wrote:** **not** "none". The population contains at least one ledger that
   is **not machine-readable at all** —
   `findings-log/2026-10-13-cors-method/results.jsonl` is **16 of its 24 rows
   malformed JSON** (`{"seq": "1", seq": "1", …` — an unquoted key mid-object),
   and it is malformed **on `origin/main` too**, from commit `8b7b7e9`. A reader
   that must handle it has to decide what a half-ledger counts as, and this pass
   did not decide that. Observed and recorded here; **not fixed** — it is
   pre-existing, outside this claim's lane, and rewriting another pass's committed
   ledger is not a research pass's side effect (`AGENTS.md` §3: append-only).
   **Closes when** every committed ledger resolves under the same
   query-derived cell rule, or each non-resolving ledger is named with its schema
   and the reason. **A negative counts.** **Assumptions (INFERRED):** that the
   other passes' schemas are independent of area L's — they were written by
   different passes on different days, and nothing in the tree asserts the schema
   set is closed. **Note from this pass:** area L's own population was **not** 6,
   the number its name rule most obviously suggests, but 8 — so a first pass over
   the ledgers outside area L (number deliberately not published: the population
   grows with every pass that lands a ledger) should expect the name rule and the
   `**Area:**` line to disagree
   and should report both.
5. **An absence count that reconciles with neither reading, in three places this
   pass originally named two of.** The area-L addendum in `docs/11`, that page's
   Closed-area row `L`, and this area's row in **`docs/10` §1** all read *"`/ipro/hcp/` is absent from
   65 of the 84"*, while the same rows publish `65 RECORD · 10 ABSENCE · 1
   INDETERMINATE` — so the `docs/10` row **contradicts itself inside one table
   row**. Under the committed census the absent count is **19** (84 − 65); under
   this pass's re-derivation it is **12** (84 − 72). **65 is neither** — it is the
   RECORD cell read into the absent slot. **Find them all with
   `grep -rn 'absent from 65 of the 84' docs/`**; no line numbers are published
   here because this pass's own commits move Closed row `L` on every landing, and a
   stale pointer is the failure this successor exists to report. **No position is
   published here either**; `locate.sh` resolves that row by content, bound to a
   commit. **Blocker:** all
   three are outside this pass's lane (`docs/10` §1, `docs/11` area prose,
   `docs/11`'s Closed table). **Closes when** one of the three readings is chosen
   on stated grounds and the others retired with their arithmetic shown, or the
   sentence is re-derived from a named verdict rule. **Zero requests.**
   **Assumptions (INFERRED):** that "absent from X of 84" means *no member found*
   rather than *no `200`-bearing probe* — the two coincide only if RECORD and
   member-carrying are the same set, and this pass's own re-derivation shows they
   are not (12 crawls carry members; 72 answered `200`). **Stated because this pass
   hunted this exact class twice and missed a third instance on the same page.**

6. **`account.py` is handed on broken, and this successor exists so it is not.**
   `docs/10` §1's own successor tells the next pass to run that tool over **"every
   other committed CC ledger"**. Run exactly that way it **crashes on a member of this
   population**: `2026-10-13-area-l-ipro-hcp` seqs 1–4 carry a **null `t_sent`**, and
   `account.py:109` calls `strptime(None)` → `TypeError`. This pass did not fix it —
   another lane owns that file — and **that is why the successor exists**: recording the
   crash as observed is not enough while the row naming the tool still points the next
   pass straight at it.

   **Blocker: none — and the earlier wording here was a routing note, not a blocker.**
   It said "the fix belongs to the lane that owns `account.py`", which names no owner
   and no route: `account.py` is a committed analysis script, not a live surface, and
   the next pass that runs it is a person reading `docs/10`. A successor that names an
   unowned fix and no owner describes the crash without stopping it. **What this
   successor actually asks for is a maintainer decision, and saying so plainly is the
   honest form.** **Closes when** EITHER the tool tolerates an absent `t_sent` — the
   spacing oracle needs only the rows that have one, so skipping them is sufficient and
   correct, not a loosening — OR the `docs/10` §1 successor is reworded to name the
   ledgers it can read, which costs nothing and is the smaller change. **Zero
   requests either way.** **Assumptions (INFERRED):** that the null is a malformed row
   rather than a deliberately blank field — 4 of that ledger's 44 rows, all at seqs
   1–4, and nothing in the tree says which. **Not fixed here; that is not this
   lane's file.**

## 8a. Correction (2026-10-15) — verifier round 1

Nothing in this file had been merged or published at a commit of record when the
independent verifier returned NOT CLEAN, so the figures below are corrected in
place **and** named here (`AGENTS.md` §5 — corrections are preserved, not smoothed
over; §6 item 7 — a count whose rule is not stated is how 44 became 93 here).

| # | superseded | corrected to | why |
|---|---|---|---|
| 1 | "the three schemas S-L4 names are not three, they are **five**" (§2), and "all **five** schemas" (§3) | **withdrawn.** Replaced by rules **K1** (distinct row key-sets = **10**), **K2** (distinct member fields = **3**, which *is* S-L4's three) and **K3** (three properties: **19/19** no-`role` rows in `pool-s7-l7crawl`; **19/19** opaque statuses there; **1** ledger with no DATA cell). New mode `read-area-l.py schemas`. | **No counting rule produced 5.** It added a row-schema property (distinct key-sets) to a query-derivation property ("no DATA cell"), which are not the same kind of thing. `AGENTS.md` §6 item 7. |
| 2 | "39 rows, **9.7%** of the population" (§1) | "**39 rows, 10.3% of the 380-row population** (39 ÷ 380 = 0.10263)" | 9.7% is not 39/380. The **rows (39) and the denominator (380) were right**; only the percentage was wrong. |
| 3 | "exit 0, **23 checks**, 0 failures" (§5) | "**25 checks**, 0 failures", and the count is now **printed by the test function** | 22 `check()` calls were being counted as 23 because the summary line also contains the word `PASS`. Three real checks were added (two over the real `s7` ledger, one for the `200`-only member rule) and the vacuous one removed — see #7. |
| 4 | "**43** committed ledgers" (§1, step 1 of R1) | round 2 replaced it with "**44** … at this branch's head"; **round 6 removed the number entirely** and states the command — see §8a-6 row 6 | 43 was true before this pass added its own ledger; 44 was true at this branch's head; both are then-values of a set **every pass in this pool extends**, so neither belongs in a live section. The recorded rule must reproduce at the commit under review; the **answer (8) is unchanged**. |
| 5 | *(new subsection + successor, now **S-L4d** in §8c)* | — | the `docs/11` area-L addendum, its Closed row `L`, and this area's row in **`docs/10` §1** all publish "absent from 65 of the 84", which reconciles with neither the committed census (19) nor this pass's re-derivation (12). **The third instance was found by running the grep that finding 2 required** — the mandated test surfaced a finding this pass had missed twice. Recorded as a successor; **out of lane, not fixed.** ⚠ Round 1 wrote the Closed-table pointer as **`:2170`**, which does not contain the sentence — corrected in §8a-2 #1. |
| 6 | `CC-MAIN-2013-48` members = **0** (§6 table) | **NOT DERIVABLE** | Its only member-bearing DATA row is a **502** (`supplement` seq 3). An empty list on a failed query is vacuous, and `census-84.txt:20` says a 502 is a FAILURE, never an absence. The reader now takes counts **only from `200` rows** and has two new controls for it. **No headline number moves.** |
| 7 | "self-test … so the trap is **exercised rather than described**" (§4) | The vacuous check is **removed** | `('200 (curl)' == '200')` compared two literals: False by construction, and unchangeable by anything the reader does. Replaced by two checks over the **committed 19-row `s7` ledger** — a raw `== "200"` finds **0 of 19**, the reader resolves **10 of 19**. |
| 8 | "`self-test` name: the **four** schemas agree on the member COUNT" | "the **three** fixtures agree…" | The check compared three fixtures, not four. |
| 9 | "an **independently** controlled crawl" (§2 R2 row) | "a **separately** controlled crawl" | `independently` is reserved for `AGENTS.md` §2.1 multiplicity, where the count is ≥2. Here it was ordinary English and would have been read as a corroboration claim. |
| 10 | `run.log` line counts | recomputed with `grep -c ''` | `printf '%s' … \| wc -l` drops the final newline, so every count was one low. |
| 11 | Successor "Blocker: none" for the other passes | weakened; **the malformed ledger is named** | `2026-10-13-cors-method/results.jsonl` is **16 of 24 rows malformed JSON**, on `origin/main` too (commit `8b7b7e9`). Pre-existing, outside this claim, **recorded and not fixed.** |

**Not changed, and re-checked after every edit above:** the population (8 ledgers,
380 rows), all five moved census cells, `older-schema` 8 → 0, the two
member-carrying cells, and the INFERRED limits. The verifier reproduced all of
them, and none of these corrections moves a cell the census prints.


## 8a-2. Correction (2026-10-15) — verifier round 2

Round 2 returned NOT CLEAN on three small points. **Two of the three were
introduced by round 1's own fixes**, which is the part worth taking seriously: the
corrections that fixed round 1's blocking findings introduced a wrong line pointer
and an arithmetic line that did not add up. Superseded text is named here
(`AGENTS.md` §5) and corrected in place.

| # | superseded | corrected to | why |
|---|---|---|---|
| 1 | S-L4d cited **`docs/11:2170`** for the Closed-table instance, in `FINDINGS.md` (5 places) and `docs/11` | **`docs/11:2218`**, Closed table row **L** | **`:2170` does not contain the sentence** — it is `All three dedicated routes answer 200 application/json on both`, the area-F addendum. The Closed table begins at `:2189`, so the parenthetical naming `:2170` as the table was wrong too. The finding was right; the pointer was wrong (`AGENTS.md` §6 item 6). |
| 2 | *(nothing recorded)* | **§8b, the non-duplicate test, run** | `CONTRIBUTING-research.md:199` requires it and it was never run for any of the four successors. Now run by `dup-test.sh` against `docs/10` §1, the Closed table and `docs/11`, with section boundaries derived by grep. |
| 3 | `run.log` self-test decomposition read `5 parses, 2 real-ledger, 3 normalisation, 2 member-source, 5 refuses, 3 exhaustiveness, 2 integration` = **22**, against **25** stated on the same line | correct grouping, summing to **25** | three middle checks were uncounted: the three fixtures agreeing on the member COUNT, on the path and host, and **not** on the timestamp. In a pass whose subject is counted arithmetic, a decomposition that does not sum is the defect this repo keeps paying for. |

**Also carried, because the verifier could not close them:**

| # | what | fix |
|---|---|---|
| 4 | the §7a floor claim's **carriage was unsigned** — `docs/11` publishes those figures in three places, and the hedge sat upstream of them | the floor now sits **in the same paragraph as each figure** in `docs/11`, and in the reader's own `census` output as a measured per-crawl block (§7a) |
| 5a | **K2 was a hand-maintained literal** — `ipro_hcp_count` excluded by rule, so a future fourth shape would be silently missed | K2 now scans every key by the name pattern `^ipro_hcp` with an **explicit, printed exclusion list** and a row count for what it excluded (**11 rows**). A fourth shape is counted, not ignored. |
| 5b | `run.log`'s self-test line count reconciled only if the capture included stderr | stated in `run.log`: captures are `2>&1`, so **stdout + 1 stderr**. (Round 2's value was **38 + 1 = 39**; the checks have grown since and `run.log` carries the current figure — a correction row quotes a then-value.) |
| 5c | the **10.3%** rounding was inline but unstated | **rounding rule stated** in §1: one decimal place, truncated, quotient printed beside it (39 ÷ 380 = 0.10263) |

**The floor claim is NARROWED, not retired, and the narrowing is the substantive
result of this round.** `docs/10` §1 already asks the general floor question and
already names its own successor — "the same one-command test over every other
committed CC ledger". **That test has now been run over area L** (§8b, by
`kib-detector.py`): **193 successful `200`s, 0 whole-KiB candidates**, and the tail-truncation mechanism `docs/10` §1 describes is measured and excluded for
**79 of 81** qualifying rows (cell **A**, per row — the cell that bears on the figures;
on cell **B**, one per crawl, **73 of 74**) — the exceptions are the `CC-MAIN-2020-50`
rows, printed as `FLOOR` wherever a figure is published. **What survives is narrower:** completeness of the
record set itself, which `docs/10` §1's own words anticipate — *"Clean for this
test is not the same as complete"* — and which no artefact in the tree can settle
because `AGENTS.md` §7 excludes the bodies. **A successor that re-asks the general
floor question is a duplicate, and this one now says so.**

## 8a-3. Correction (2026-10-15) — verifier round 3

Round 3 returned NOT CLEAN on eight points. The reviewer re-derived and confirmed
every substantive measurement across all three rounds — the population, all five moved
cells, `older-schema` as a genuine parser bail-out, both member-carrying cells,
`CC-MAIN-2013-48` as NOT DERIVABLE, the S-L4b narrowing, the §7a carriage, and
`research-checks.py` + `measure_assertions.py --self-test` both exit 0 — and wrote the
diagnosis plainly: **the defect class is pointers, predicates and prose, not
measurements.** Every finding below is of that class and needs no request.

| # | superseded | corrected to | why |
|---|---|---|---|
| 1 | this file published `docs/11:2218` for Closed row `L`, and "the Closed table begins at `:2189`" | **no position is published in this file, in any spelling.** `locate.sh` resolves every landmark by content, bound to a commit; `dup-test.sh` enforces it and exits non-zero | every pointer of that shape has been stale within one commit, because this PR inserts 142 lines into `docs/11` below most of what it cites. Correcting the numbers would fix four instances of a bug that has fired in every round |
| 2 | the no-line-numbers policy, while the same file published five `docs/NN:NNNN` pointers | the policy is now **enforced and fatal**: `dup-test.sh` greps `FINDINGS.md` for a position in the spellings it takes, outside the Correction sections, and **exits non-zero** | a policy the file stating it breaks is not a policy. The Correction sections are excluded **deliberately** — `AGENTS.md` §5 requires corrections preserved as history |
| 3 | "moved row `L` by **17 lines**" | **2094 → 2170 → 2218 → 2232 → 2236**; main → head **+142 at `23c4451`**, the round before **+18** | "17" was neither figure, and this round introduced it. The `+142` is a **then-value at that commit** — the count moves with every edit above row `L`, so no *current* one is published here; `locate.sh` resolves row `L` by content instead. See §8a-6 row 5 |
| 4 | "**67 of 69** member-source rows carry no `limit=`" | **RULE 3** stated and shipped in `kib-detector.py`. **A** every row **81 / 9 carry / 72 none / 2 at-limit** · **B** one per crawl, what `derive()` uses, **74 / 6 / 68 / 1** · **C** in-window, **72 / 5 / 67 / 1** | the published **69/67 matched no cell**, and **67** is cell C's "carrying none" beside cell A's denominator. The reviewer's re-derivation — *importing* this reader's predicates — returned **81/9/72/2**, cell **A**, which is right for its question |
| 5 | `read-area-l.py` printed *"every other member-source row carries no `limit=`, so no limit truncated it"* | the block now counts **four** numbers and says **"AT their own limit"** is the only predicate that can cut a tail | the sentence asserted one predicate (carries none) about rows selected by another (reached it). **7** member-source rows carry a limit without reaching it |
| 6 | "one decimal place, **truncated** (0.10263 → **10.3%**)" | "one decimal place, **rounded half-up** (39 ÷ 380 = 0.10263 → **10.3%**)" | truncating 10.2631…% gives **10.2%** — the rule did not reproduce its own figure |
| 7 | `account.py`'s crash recorded as "not fixed" | carried as **successor S-L4e** here and in `docs/11` | recorded-not-fixed is right for the **code** (another lane's file) and not enough for the **handoff**: `docs/10` §1's successor still sends the next pass into a crash |
| 8 | §7b's byte table citing "(§8b)" with **no artefact behind it** | **`kib-detector.py`** computes it, and **RULE 2** is stated: three obvious rules give **0**, **183**, **193** | `grep -rniE '1024\|kib\|193'` over this pass's `.py`/`.sh` returned nothing. An unstated counting rule is the class this repo has corrected twice |

**The mechanism behind 1, 2 and 3 is one thing: this pass's own insertions.**
Re-checked explicitly — nothing published now carries a pointer its own diff will move,
and `dup-test.sh` is the artefact that proves it rather than the prose asserting it.

**Unchanged and re-verified after every edit above:** the population (8 ledgers,
380 rows), all five moved census cells, `older-schema` 8 → 0, both member-carrying
cells, `CC-MAIN-2013-48` NOT DERIVABLE, the INFERRED limits. The only figures that moved
are the two that had no artefact behind them.

## 8a-4. Correction (2026-10-15) — verifier round 4

Round 4 returned NOT CLEAN on six points and, more usefully, said why four rounds
had not converged. The reviewer's own summary: *"the defect class is exactly what
three rounds of verifiers said it was: pointers, predicates and prose"* — and
*"fix 1 removed the spelling of the stale pointer and left the class intact."*

**The shape of the problem, recorded because it is the finding.** Every round fixed
a *coordinate*: `:2189` -> `docs/11:2170` -> `docs/11:2218` -> `:2232` ->
`:2236` -> `:2253`. **Each fix added lines, which moved what the log measured,
which required the next fix.** That is not bookkeeping error. It is a write-up
that cannot converge, because prose in this directory cited positions into a file
this PR edits. **So this round changes the shape, not the instances.**

| # | superseded | corrected to | why |
|---|---|---|---|
| 1 | §8b published `docs/11 Closed table begins at 2189` | **a grep**, no position | live on the shipped SHA, in §8b's body, **outside every Correction section** — the exact defect fix 1 was written to prevent, surviving the apparatus. Now a `grep '^## Closed areas'` |
| 2 | a verbatim duplicated block (the KiB table, "Zero candidates", the caution, the `account.py` paragraph, the narrowing paragraph) with **two broken cross-references**: one pointing at the wrong successor, one at `§8c.6` which did not exist | **deleted**; one canonical copy remains and §8c is now numbered contiguously `1 2 3 4 5 6` | the duplicate was the disclosed `git checkout` double-write, present in the shipped file. Two broken pointers **inside the file whose thesis is that broken pointers are the defect** |
| 3 | this file published a terminal position and "measured, now", plus an inserted-line count | **no terminal position — and no *current* line count — is published in any live section of this file.** Correction sections quote withdrawn values as then-values, because `AGENTS.md` §5 requires the retraction preserved; §8a-3 row 3 is one, and it now names the commit it was taken at | the "measured, now" figure named the *previous* commit's value on the SHA it shipped in. Any position stated here expires on the commit that adds lines above it — **and this file is the thing adding them** |
| 4 | §8b carried a **transcribed** copy of `dup-test.sh`'s output, which had drifted (`floor` 31 recorded / 30 live; `truncat` 3 / 5) | **the table is gone; only the command remains** | transcription is what let it drift, and §9's whole purpose was to remove that manual step. The script prints the counts live |
| 5 | "no line numbers are published here because this pass's own three commits moved row `L` by **17 lines**" — superseded in a Correction section, still live in §8c's body | **the body text is updated**; the Correction entries stay, because they are history | a correction recorded and not applied to the body is a correction that changes nothing |
| 6 | "see §6, *Successors* 1 and 2" (no such list) and "`probe.sh` records the **four** commands" (it runs **eight**) | both corrected | the successor list is under `## 8c`; `probe.sh` now runs **eight** |

**THE STRUCTURAL CHANGE, which is the point of this round.**

- **`locate.sh` is new.** It resolves every landmark this file names **by content**
  and prints `file:line` **bound to the commit it measured at**, exiting non-zero
  if any landmark cannot be found. **Every landmark is matched by its text, never by
  a typed line number** — that is what keeps it true when the file moves. Positions
  are now the output of a script, not claims in prose.
- **`dup-test.sh` enforces the CLASS, not the spelling, and is fatal.** The earlier
  regex required a colon, so a bare `2189` walked past it — which is `AGENTS.md` §6
  item 2 aimed at this repo's own check. It now matches a position in four
  spellings, scoped to files **this PR edits** (derived from the diff, not
  hardcoded), and **exits non-zero**. The prose's "fails loudly" and "enforced by the
  artefact" are now true rather than aspirational. **The absolute form of that
  first sentence is superseded by §8a-6 row 3** — the set of spellings is enumerated
  there, and the ones this scan cannot see are named.
- **The exemption is a kind, not a position.** It covers Correction **sections**,
  recognised by heading and ending at the next heading. The earlier `awk
  '/^## 8a/ {skip=1}'` skipped to EOF, exempting `## 9. Artefacts` and anything
  appended after it, forever. The script also **reports** a heading that looks like
  a Correction section and is not one, so the exemption cannot be widened by
  renaming.
- **Population rule R1 is pinned in `self-test`** (`AGENTS.md` §3: a claim that
  should not rot gets a check). It produced this pass's most consequential finding —
  `derive.py` read **6** ledgers where R1 finds **8** — and it was prose until now.
  **8 checks**, covering both edges: a lane-lettered slug is caught, an unrelated
  letter is not. No vendor pin needed; it is string analysis over committed ledgers.

**Unchanged and re-verified:** the population (8 ledgers / 380 rows), all five moved
census cells, `older-schema` 8 -> 0, both member-carrying cells, `CC-MAIN-2013-48` as
NOT DERIVABLE, the INFERRED limits, 193/0 whole-KiB, and zero members lost. **No
figure the verifier confirmed moved in this round** — the measurements were already
right, and the finding was that three of them had been *presented* in a form that
could not survive the next commit.

## 8a-5. Correction (2026-10-15) — verifier round 5

Round 5 returned NOT CLEAN on three blockers, all of them in the **apparatus**
rather than in the measurements — the same diagnosis as round 4, one level further
in. Round 4 fixed the *prose*; round 5's finding is that the *checker written to
police the prose* could not see the class it claimed to police.

| # | superseded | corrected to | why |
|---|---|---|---|
| 1 | `dup-test.sh` reported "0 positions" on this file while the file carried `docs/11:NNNN` pointers | the tokeniser held `:` OUT of a token, so `docs/11:2218` was torn into `docs/11` + `2218` and the colon test could never fire; `:` is now inside the token class and the subject is matched by path prefix | a check that catches only the spelling it was written for is `AGENTS.md` §6 item 2 aimed at this repo's own check. Mutating one line into the class now exits non-zero and names the line |
| 2 | the Correction exemption matched `^## 8a`, so any heading beginning `## 8a` opened it | **one** canonical pattern, `CORR_RE`, used by the exemption, the `FAKE` check and the listing, so the three cannot diverge; a heading that mentions "correction" but does not match `CORR_RE` is reported | the exemption is a kind, not a prefix |
| 3 | `read-area-l.py` read every ledger **twice** and appended each row again, so the member-shape cells printed **456 / 178 / 22** | the second pass is removed; the cells print **228 / 89 / 11**, the values §7 publishes | the same silent-overcount class the S-L2 section had already been corrected for twice — and the one blocker that moved a *published* figure |
| 4 | `run.log` recorded `dup-test.sh` at **66** output lines, and named `read-area-l.py` without its `python3 ` prefix | **65** lines, regenerated by re-running the invocations; every invocation named as `probe.sh` runs it | the count moved when the checker changed (which is correct — the transcript was stale); the missing prefix named a command that is not executable |
| 5 | `dup-test.sh`'s `awk` emitted `escape sequence` warnings on stderr, falsifying `run.log`'s rule 2 | the `awk` no longer escapes characters it does not need to escape, so **`dup-test.sh` writes nothing to stderr** and rule 2 holds | a file that states a rule its own tools break is the defect the rule exists to catch |
| 6 | §8a-2 row 5b quoted the round-2 self-test count (`38 + 1 = 39`) as though current | the **mechanism** is unchanged (`2>&1`); the count has grown with the checks and `run.log` carries the current figure | a correction row is history; its number is a then-value |

**The one substantive correction is #3, and it is why this round is recorded here
rather than as a footnote.** The double-append was not a citation defect — it
inverted a number this pass publishes in §7 (the member-shape cells). Every other
round found pointers, predicates or prose; this one found the reader disagreeing
with its own published table, which is `AGENTS.md` §6 item 5.

**Unchanged and re-verified after the edits above:** the population (8 ledgers /
380 rows), all five moved census cells, `older-schema` 8 → 0, both member-carrying
cells, `CC-MAIN-2013-48` NOT DERIVABLE, 193/0 whole-KiB, and the INFERRED limits.
**No other measured figure moved.**

## 8a-6. Correction (2026-10-15) — verifier round 6

Round 6 re-verified the round-5 fixes on the same SHA and returned NOT CLEAN. Its
first blocker was **self-inflicted**: the round-5 correction was pasted into the
middle of a sentence. The insertion anchored on the literal string `## 9. Artefacts`,
which occurs **twice** in this file — once as a section heading, and once *inside*
§8a-4's own prose, in the sentence "exempting `## 9. Artefacts` and anything appended
after it". The anchor matched the **first** occurrence, so §8a-5 landed inside the
sentence and left a phantom heading at line 939, an unterminated code span above it,
and §8a-4's closing bullets stranded under a section they do not belong to. That is
`AGENTS.md` §6 item 2 in its purest form: a search string known to be ambiguous, used
anyway, in a file whose whole subject is that mistake.

| # | superseded | corrected to | why |
|---|---|---|---|
| 1 | §8a-5 pasted mid-sentence; phantom `## 9. Artefacts\` and anything` heading; §8a-4's closing bullets orphaned beneath it | §8a-4's sentence restored verbatim; §8a-5 is a real section; the phantom heading is gone | an insertion anchored on a string that occurs twice is a coin toss, and this one lost |
| 2 | `run.log` recorded `sh dup-test.sh` at **65** output lines and blamed the earlier `escape sequence` warnings | the count is **70**, which is what `sh dup-test.sh 2>&1 \| grep -c ''` prints at this head. The `awk` fix did empty stderr; the phantom heading (row 1) is what moved the count back | the file's own rule is "printed, never transcribed", and this was a transcribed count whose stated cause was wrong |
| 3 | `dup-test.sh` claimed it "enforces the CLASS, not the spelling", and its echo advertised `docs/NN:NNNN` and `lines NNNN-NNNN` as covered | the claim is now **the spellings actually enforced**, listed one by one, with the residual **named** rather than left to be discovered: this line-based scan cannot see a position whose subject follows the number, nor one split across two lines | an absolute claim over an enumerated set is the defect this check exists to catch |
| 4 | `docs/11-suggested-research-areas.md lines 1736 and 1738` published in §6 with the subject ending one line and the numbers starting the next — a **live** instance of the class, in the file that polices it | the two rows are named by content; the sentence now carries the grep that resolves them | the check could not see it. Adding a predicate for every new spelling is the non-convergent game this pass is about, so the residual is stated and the instance is removed |
| 5 | §8a-4 said "no terminal position, **and no line count**, is published anywhere in this file", while §8a-3 published `+142` labelled "Measured, now" | §8a-3's figure is labelled a **then-value at `23c4451`**; §8a-4's "anywhere" is narrowed to the live sections | a correction may not outrun its own table |
| 6 | §1 published step 1's ledger count, and successor 4 published "the other **36**" | neither number is published: step 1 states the command, successor 4 is named by scope | four passes are landing in this file's population at once; a count over a set other passes extend is not this pass's to state |

**Nothing measured moved in this round.** The population (8 ledgers / 380 rows), all
five census cells, the member-shape cells (228 / 89 / 11), `older-schema` 8 → 0, 193/0
whole-KiB and the INFERRED limits are unchanged. Every blocker above is a defect in
this pass's **own apparatus**, found by turning that apparatus on itself — the one
pattern all six rounds share.


## 8a-7. Correction (2026-10-15) — verifier round 7

Round 7 returned NOT CLEAN on three blockers. **One of them does not hold**, and it is
recorded here as **refuted** rather than fixed, with the reproduction that settles it.
The other two are real, and they are the same class: structure that a fix round rewrote
without re-reading.

| # | as filed | disposition | how it was settled, at this commit |
|---|---|---|---|
| 1 | §8a-6's heading abuts the paragraph above it — the one `## ` heading in this file with no blank line on either side (filed as the blank line *after* the heading; the missing one is *before* it) | **fixed** — blank line inserted | a scan of every `## ` heading whose preceding line is non-blank returns exactly one offender, the §8a-6 heading |
| 2 | the body of this section's blockquote is shredded: a **doubled `>` marker**, a bare `>` **opening** a blockquote straight after a paragraph, a bare `>` **closing** one straight before a paragraph, and one line reflowed to **107** characters | **fixed** — the paragraph is rewrapped, both orphan markers become blank lines | four whole-file scans (`^> >`; a run not preceded by a blank line; a run ending in a bare `>`; blockquote lines over 100 chars) return **exactly four** offenders, all in this region |
| 3 | `dup-test.sh`'s rule B is narrower than its header claims — the **full path** as subject (`docs/11-suggested-research-areas.md lines 2236`) is said not to be caught | **REFUTED — no change made** | re-tested in a scratch clone at this SHA. With the mutant in **live** text the check exits **1** and names the line under rule B; it exits 0 only when the mutant sits inside a Correction section, which is the exemption working as designed |
| 4 | — (self-caught while applying rows 1–3) | **fixed** — this section first landed *after* §9, so a Correction section became the file's last section and `dup-test.sh`'s "sections AFTER the last Correction" listing emptied, because the exemption ran to EOF | the whole file's heading order is now printed by that listing itself: the corrections run §8a … §8a-7 and `## 9. Artefacts` is the only section after them. It is the same coupling §8a-5 row 3 describes, caught this time before it shipped |
| 5 | `docs/11`'s pointer at this pass cited the claim's evidence as `§8a, §8a-2, §8a-3` — a fixed subset of a correction series that grows every verification round | **fixed** — now `§8a and the correction sections that follow it` | the same shape as the count over a growing set this pass removed in §8a-6, one level up: a list of a growing set reads as an inventory while being a selection. The predicate is now open-ended — `dup-test.sh` itself requires any future correction section to be an `§8a*` heading — so a later round cannot make it stale |

**On blocker 3, stated so it can be re-run rather than believed.** Rule B's subject test
is `index(ed, W[i]) == 1` — the token must be a **prefix of** an edited path — so `docs/11`
and `docs/11-suggested-research-areas.md` both match. Four live spellings, re-tested here,
each with the mutant in live text:

```
docs/11:2236                                    exit=1   A file:NUMBER
docs/11-suggested-research-areas.md lines 2236   exit=1   B line NUMBER
docs/11 lines 2236                               exit=1   B line NUMBER
the table begins at 2236 in docs/11              exit=1   C positional verb
absent from 65 of the 84                         exit=0   (a quoted sentence, no position)
```

The mutation that reports exit 0 for the full path is one placed in an **exempt** span;
the same string in live text fires. That the refutation turns on *where* a mutant is
inserted is the point of this whole pass — and it is the same trap that produced §8a-6
row 1, in the opposite direction.

**Why this damage survived three rounds, which is the reusable part.** Rounds 3 and 4
both did `git checkout`/stitch surgery over this region, and each certifies the lines it
rewrote rather than the structure around the seam. `dup-test.sh` cannot see it — a
line-based scan holds no opinion about blank lines — and the gate's markdown hygiene does
not repair it. So: **a fix round re-reads the structure of the region it edits, not only
the values inside it.**

**One recorded count moved, and only because row 4 is a heading.** `run.log`'s
`sh dup-test.sh` entry goes **70 → 71**: the exempt-section listing prints one line
per Correction heading, and there is now one more of them. Nothing measured moved —
no count, offset, cell or figure in this pass changes this round. The repairs are
whitespace, one relocated section and one citation reworded to an open-ended form; the
refutation publishes an exit code.

## Correction (2026-10-17) — correction issue #139's eight findings, re-derived at this head

**This is a correction lane, not a probe: 0 of a 0 cap, no vendor host, no DNS, no
`curl`, no `hurl`.** Issue `correction: PR #135 S-L4 — eight blocking findings after
three rounds; claim holds, pointers and prose do not` (#139) filed **2026-10-15
15:55Z** against branch head `23c4451`. **PR #135 merged at 21:47Z the same day**
(merge commit `aa401b7`), and the branch carried **seven further commits after that
head, self-labelled rounds 3 through 9** — `24b9601` (round 3), `227a95c` (4),
`bfc8f55` (5), `741cca1` (6), `228519f` (7), `d88a879` (8), `f83137d` (9) — before
that merge. **The count is stated by the command, not by hand:**
`git log --oneline aa401b7^1..aa401b7 | grep -cE '^(24b9601|227a95c|bfc8f55|741cca1|228519f|d88a879|f83137d)'`
→ **7**, re-measured at this head. ⚠ **The unfiltered `git log --oneline
aa401b7^1..aa401b7` first stood here and prints 12 lines** — the merge itself, a
`Merge remote-tracking branch` commit, this pass's round 1–2 pair, its opening
finding commit, and the seven above — so a reader who ran it counted 12 beside a
stated seven. That is **#139's finding-3 defect class committed in the one
paragraph whose job is to get the history right**, and it is the same defect the
Correction below fixed in the *correction* row while leaving it live in this body.
The recipe is now the filtered one, whose output is the number printed beside it.
And **rounds 3, 4, 6 and 7** are the
commits that added a `## 8a-*` correction section — **round 5 added none**, and round 6
added both `§8a-5` and `§8a-6` — measured one commit at a time with
`git show <sha> -- …/FINDINGS.md | grep '^+## 8a'` (rounds 8–9 added none either, which
is why the series still ends at `§8a-7`). **So #139 is not an open list
of eight unfixed defects at this head: seven of the eight were answered by §8a-3 and
refined by rounds 4–9, and one was not.** Every row below was re-derived from the
tree, not from the issue's wording, and each carries the command that produced it.
⚠ **This sentence first read "four further rounds" beside the same seven SHAs — the
defect #139's finding 3 names, committed in the paragraph whose whole job is to get
the history right.** See the Correction section below.

| # | as filed in #139 | disposition at this head | re-derived by |
|---|---|---|---|
| 1 | `FINDINGS.md:673` publishes `docs/11:2218` as Closed-table row **L** | **already fixed** — no position is published in this file in any spelling outside the Correction sections (§8a-3 row 1). Find them with `grep -nE 'docs/(10\|11)[^ ]*:[0-9]+' findings-log/2026-10-15-area-l4-ledger-reader/FINDINGS.md`, run **from the repo root**: **every hit is inside a Correction section**, and that invariant is the claim — a Correction section may quote a withdrawn value (`AGENTS.md` §5). `sh dup-test.sh` is what enforces it, fatally. **No count is printed beside that recipe, deliberately: the row you are reading quotes `docs/11:2218` itself, so the recipe counts its own quotation and the number moves whenever this sentence is edited.** ⚠ The recipe also first carried an escaped `\|`, which in an ERE is a *literal* pipe — it matched nothing and returned **0**, which reads exactly like the clean negative it was not. **But the class is still live in `docs/11` itself** — see the note under the table | `sh dup-test.sh` (position check, fatal) |
| 2 | the no-line-numbers policy is contradicted one line-number away in the file that states it | **already fixed, and now enforced rather than asserted** — the policy is fatal in `dup-test.sh`, which exits non-zero on a position in any spelling outside a Correction section (§8a-3 row 2, widened in round 5 to cover the colon form) | `sh dup-test.sh` |
| 3 | "moved row `L` by **17 lines**" is neither measured figure | **already fixed** — the phrase survives **only inside Correction sections** (the §8a-3 row that withdrew it, and the §8a-4 row that applied the withdrawal to §8c's body), and **in no live section**. That invariant is the claim: `grep -n '17 lines' findings-log/2026-10-15-area-l4-ledger-reader/FINDINGS.md`, run **from the repo root**, returns the §8a-* rows and **this row**, which quotes the phrase; the earlier form of this cell also omitted the file argument, so the recipe read **stdin** and hung rather than answering | `grep -n '17 lines' findings-log/2026-10-15-area-l4-ledger-reader/FINDINGS.md` |
| 4 | "67 of 69 member-source rows carry no `limit=`" mixes two cells | **already fixed** — RULE 3 is stated and shipped in `kib-detector.py`, which prints three cells: **A** every row **81 / 9 carry / 72 none / 2 AT limit**, **B** one per crawl **74 / 6 / 68 / 1**, **C** in-window **72 / 5 / 67 / 1**. `69` is no cell's row count and `67` is cell C's "carrying none" — the withdrawn clause mixed a numerator from one cell with a denominator from another (§8a-3 row 4) | `python3 kib-detector.py` |
| 5 | the reader prints "every other member-source row carries no `limit=`, so no limit truncated it" — a predicate it does not mean | **already fixed** — `python3 read-area-l.py census` now prints **four** numbers (`carrying a limit=` / `carrying no limit=` / **`AT their own limit`** / `carried a limit WITHOUT reaching it`) and says *"ONLY \"AT their own limit\" means a limit could have truncated the tail"*, with the count that bears on the figures given as *2 of 81* (§8a-3 row 5) | `python3 read-area-l.py census` |
| 6 | `10.3%` published beside a rule that does not produce it ("truncated") | **already fixed** — §1 now states *"one decimal place, **ROUNDED half-up**, and the exact quotient is printed beside it: **39 ÷ 380 = 0.10263 → 10.3%**"*, and carries the retraction of the `10.2%` that truncation would give (§8a-3 row 6) | `sed -n '82,92p' FINDINGS.md` |
| 7 | `account.py` is handed on broken and the successor that names it would run it | **FIXED HERE — the one finding still open at this head, and it is now closed by the branch this pass named.** `account.py` tolerates an absent `t_sent`: `parse()` returns `None` for a non-string instead of letting `strptime(None)` raise `TypeError`, `spacing()` skips the two pairs touching a row that carries no timestamp and **prints how many it skipped**, and `inverted` uses `.get()`. The crash reproduced before the fix and does not after — see the reproduction below. **Also fixed, and found while verifying:** a **second** crash on the same handoff — a 0-row ledger raised `IndexError` at `rows[-1]['seq']`, so the newest committed CC ledger in the repo was one this tool could not open. It now prints that the ledger records a pass that sent nothing | `python3 account.py findings-log/2026-10-13-area-l-ipro-hcp/results.jsonl` |
| 8 | the `193` byte table cites `(§8b)`, which computes nothing, and the counting rule for "successful `200`" is unstated | **already fixed, and the finding's second half re-derives as WRONG at this head.** `kib-detector.py` **is** a committed artefact that performs the byte arithmetic: RULE 1 at its `body_bytes % 1024` test, RULE 2 as `status_of(row) == 200`, and it prints all three obvious rules (**0** / **183** / **193**). §8b exists, RULE 2 states the rule beside the number, and `docs/11`'s own floor table states it again. **What §7b still does not carry is the rule beside its own `193`** — it cites §8b instead — and this section is where that gap is recorded, because §7b is append-only (§8a-3 row 8) | `python3 kib-detector.py` (run in this directory); `cd findings-log/2026-10-15-area-l4-ledger-reader && grep -n '1024\|kib\|193' *.py *.sh` — **the `cd` is part of the recipe, because a bare `*.py *.sh` expands against whatever directory the reader is standing in** |

**One live instance of finding 1's class survived all of that, in `docs/11`.**
§8a-6 row 4 recorded that the log's copy of it was removed; the `docs/11` sentence
it was describing was not touched, and it read *"lines 1736 and 1738 above list both
crawls' members as `(prior)`"* — a position into the file its own PR edits, **wrong
at this head**: those lines are two successor bullets, and the two rows are found by
content with `grep -rn 'CC-MAIN-2014-10.*(prior)\|CC-MAIN-2020-24.*(prior)' docs/`,
run **from the repo root**. ⚠ **The recipe this paragraph first carried did not
execute and could not have found both rows**: it was `grep -n` with **no `-r`** over
a **directory** (GNU grep: `docs/: Is a directory`, **exit 2**, zero rows), and its
pattern named only `CC-MAIN-2020-24`, so even had it recursed it would have matched
**one** of the two rows and not the `CC-MAIN-2014-10` one. The replaced form returns
**three** lines — the two table rows plus **the sentence in `docs/11` that quotes the
recipe** — which is why **no count is printed beside it** (the same lesson as the
Correction section below). **`\|` is load-bearing there and is not the escaped
alternation the Correction below warns about:** this is plain `grep`, a BRE, where
`\|` *is* alternation; the defect there was `\|` inside `grep -E`, an ERE, where it is
a literal pipe. Both forms were re-run at this head. Fixed in place in the S-L4
block, with the withdrawn numbers left visible. **This is
the class finding 1 named, surviving its own fix on the other side of the file.**

**The counting rule for §7b's `193`, stated here because §7b cannot be edited
(AGENTS.md §3).** A row counts when the reader's own `status_of(row)` resolves it to
the **int** 200 — every `http_status` in this population is a JSON string, and
`pool-s7-l7crawl` writes the opaque form `"200 (curl)"`. The other two obvious rules
give **0** (`raw == 200`, the int) and **183** (`raw == "200"`, exact string
equality, missing the opaque rows). The gap is exactly the **10** `"200 (curl)"`
rows. **So the `193` is `status_of(row) == 200` and only that rule produces it** —
a reader applying the obvious one gets 183 and concludes the figure is wrong, which
is why the rule sits next to the number in `docs/11` and in `kib-detector.py` RULE 2.

**The crash, before and after — the reproduction for row 7, and the whole of it.**

```
$ python3 findings-log/2026-10-14-lane-s6-public-index/account.py \
      findings-log/2026-10-13-area-l-ipro-hcp/results.jsonl          # BEFORE
  File ".../account.py", line 109, in spacing
    a, b = parse(sel[i]["t_sent"]), parse(sel[i + 1]["t_sent"])
TypeError: strptime() argument 1 must be str, not None

$ … the same command                                                       # AFTER
    pairs skipped, no usable t_sent    4
    min gap, harness t_sent            4.102 s
  exit 0
```

⚠ **The `BEFORE` path above first read `findings-log/2026-0{9,8}-14-lane-s6-public-index/account.py`,
and neither expansion exists** — the lane's directory is `2026-10-14`, not `09-14`
or `08-14`, so the brace expanded to two paths and both were **MISSING**:
`python3: can't open file '…/findings-log/2026-09-14-lane-s6-public-index/account.py':
[Errno 2] No such file or directory`, exit 2. A reproduction a reader cannot run is
**`AGENTS.md` §6 item 6** — the same class as #139's finding 6, committed inside the
correction of #139, and the correction that had already been demanded of this file's
own earlier sections. **The path is now the one that resolves, and it was re-run at
this head**: the AFTER half above reproduces exactly (skipped **4**, min gap
**4.102 s**, exit 0), and all eight ledgers of `manifest.tsv` exit 0.

**All eight area-L ledgers now open, which is the whole of what `docs/10` §1's
successor asks for** (`for f in …; do python3 account.py "$f"; done`, exit 0 on
each; the 0-row ledger included). **Skipping a row without a `t_sent` is the correct
fix, not a loosening**: the spacing oracle needs only the rows that have one, and a
gap measured *across* a row with no timestamp would be a guess. The floor is still a
minimum over real gaps, and the number of skipped pairs is printed rather than
absorbed — because a floor computed over a subset that says so is a claim, and one
that does not is `AGENTS.md` §6 item 7.

**Inert for the tool's own lane, and checked rather than asserted.** That ledger has
**151** rows, **0** null and **0** absent `t_sent`. `python3 account.py` on it is
byte-identical before and after except for three added lines, and both new counters
read **0** — no gap, no sub-floor count, no inverted row and no detector figure moved.

**One disclosure added while fixing it, because the next reader will hit it.** This
tool's rule for *"successful 200 answers"* is `http_status == "200"` **exactly**, and
an opaque `"200 (curl)"` is **not** counted by it. Run over
`2026-10-14-pool-s7-l7crawl` it therefore reports **0** where RULE 2 reports **10** —
the same ledger, two rules, and no way to tell which is right from the number alone.
The count is deliberately **unchanged**: changing it would move a figure that lane has
published, for a ledger it has never run over. What was added is the rule beside the
number, the count of opaque-200 rows, and the name of the detector that resolves
them. **Stating the rule was the fix; changing the count would have been a new
claim.**

**`dup-test.sh` changed too, and it is a check, so it is recorded here.** Its
`CORR_RE` — the single pattern that decides what counts as a Correction section —
recognised only this pass's `## 8a-N. Correction (…)` headings. `scripts/research-checks.py`,
which **the gate runs**, requires `^## Correction (YYYY-MM-DD)` before it will accept
any edit to a file under `findings-log/`. The two disagreed, and the disagreement
punished correctness: a pass that wrote its correction in the form the gate demands
was reported by `dup-test.sh` as a **FAKE CORRECTION HEADING**, i.e. as an attempt to
widen the exemption by renaming. One alternative was added, and the position
spellings, the fail-closed guard, the enumerated residual and the exit code are
unchanged.

**Nothing measured moved in this correction.** The population, all five census cells,
`older-schema` 8 → 0, the member-shape cells, `CC-MAIN-2013-48` NOT DERIVABLE, the
193/0 whole-KiB cells and the INFERRED limits all re-derive unchanged from the
committed artefacts, and none was edited. **The seven rows marked *already fixed*
were not fixed by this lane** — they were fixed by this pass's own rounds 3–7 before
`aa401b7` merged, and this lane's contribution is the re-derivation that says so,
with the commands, rather than a second edit of the same text.

## Correction (2026-10-17) — verifier round 1 on PR #147: two prose defects, and a recipe that returned nothing

A fresh-context verifier returned NOT CLEAN on PR #147 (this lane's correction of
#139) with **seven claims CONFIRMED** — the history claim re-derived from a
`git archive origin/main` extract, the `account.py` fix on the crashing ledgers, both
crashes, the inertness diff, the `71 → 72` count move, the `CORR_RE` conflict, and
all eight ledger exits. **Nothing measured was contradicted. Both blocking findings
are in prose this lane wrote, and both are the same class as the findings being
corrected: a statement that does not survive being run.**

| # | as filed | corrected to | why |
|---|---|---|---|
| 1 | the Correction (2026-10-17) introduction read **"the branch carried four further rounds"** beside a list of **seven** SHAs, and *"refined by rounds 4–7"* | **seven further commits after `23c4451`, self-labelled rounds 3 through 9**, and *"refined by rounds 4–9"*; the count is stated by the command, not by hand | `git log --oneline aa401b7^1..aa401b7 \| grep -cE '^(24b9601\|227a95c\|bfc8f55\|741cca1\|228519f\|d88a879\|f83137d)'` → **7**. "four" appears to have migrated from the neighbouring clause — which is precisely **#139's finding-3 defect class**: a stated figure matching neither measurement, committed in the one paragraph whose job is to get the history right |
| 2 | the replacement recipe published in `docs/11` was `grep -n '…' docs/` — **no `-r`** | `grep -rn '…' docs/`, **re-run verbatim before the page ships**; the two rows it returns are quoted in the correction note in `docs/11` itself | GNU `grep` does not recurse without `-r`: `grep: docs/: Is a directory`, **exit 2, zero rows**. The fix for one unresolvable pointer published another, and §8a-6 row 4 of this file had already recorded that a check "could not see" that shape for want of a predicate |

**Two more instances of finding 2, in this lane's own recipes, found while fixing it
— which is round 8's lesson one level up.**

- **Row 1's recipe carried an escaped `\|` inside an ERE.** In an ERE `\|` is a
  **literal** pipe, so `(10\|11)` matches the text `10|11`, and the pattern matched
  **nothing**: `grep -nE 'docs/(10\|11)[^ ]*:[0-9]+' …` → **0 hits**. A zero that
  looks exactly like the clean negative it is not.
- **Row 3's recipe had no file argument**, so it read **stdin** and hung instead of
  answering. Both are now `grep` invocations that name their file, carry no escape,
  and are re-run from the repo root before this ships.
- **Two published counts were falsified by the quotations beside them.** Row 1 said
  its recipe "returns **5** hits"; it returns **6**, because row 1 itself quotes
  `docs/11:2218`. Row 3 said *"two lines"*; that recipe returns **3**, for the same
  reason. **So no count is printed beside either recipe now** — the invariant is
  published instead (*every hit is inside a Correction section*; the phrase survives
  **only** inside Correction sections), and `sh dup-test.sh` is the artefact that
  enforces the first. A recipe that counts the sentence quoting it is a then-value
  wearing a count's clothes.

**The generalisable finding, and the one worth keeping: a recipe that returns nothing
is not evidence of a negative.** Three of the four defects above — no `-r`, an escaped
alternation, no file argument — all produce *no output*, and all three read as "none
found" to anyone who does not look at the exit code. The discriminator is the exit
code, **measured on this host's `grep` (GNU grep 3.12): `1` for a pattern that ran and
matched nothing, `2` for a usage error, `0` for a match** — so the separation is 1
against 2. ⚠ **This sentence first read "**0** for a pattern that ran and matched
nothing", which is the inversion of the discrimination it claims to supply**, and
the values are re-measured here, not carried: an absent token → **1**, a usage error → **2** (the
no-`-r` directory form is one — `Is a directory` exits **2**), a matched phrase →
**0**. Round 3 returned on the sentence's other half too: re-derived over the
recipes this section publishes, **"none does" is false twice** — the withdrawn
no-`-r` `grep` publishes **exit 2** as the then-value it is, and **`research-gate.sh`
at the foot of this section publishes its own, exit 0**. The live ones name outputs
instead: `git log … | grep -cE '^(24b9601|…)'` → **7**, `grep -rn '…' docs/` with its
rows quoted in `docs/11`, and the escaped-alternation bullet carrying **0 hits** as
its then-output — so the three codes are stated in prose here, not deferred to the
recipes. The correction is applied to the body **and** recorded here — §8a-4
row 5's lesson, that *a correction recorded
and not applied to the body is a correction that changes nothing*.

**Nothing measured moved, and nothing was re-probed.** This remains a 0-request
correction pass; `research-gate.sh` re-run under the run's lock, exit 0. The verifier
found no credential, hostname or live-session material, and no value pinned in
`regression/hurl/` is touched by this PR.

## Correction (2026-10-17) — third pass of this date: four defects of this lane's own, found on the `origin/main` sync

Merging `origin/main` (`015689e`) into the branch before verification produced **no
conflict** — `docs/10` and `docs/11` both auto-merged, and `measure_assertions.py`
still reads **217 431** with no pin added. The re-derivation that the sync obliges
found **four defects in text this lane wrote**, none of them raised by a verifier and
all four in the same two classes #139 named. Each is fixed in place above with the
withdrawn form left visible, and each carries the command.

| # | defect | class | re-derived by |
|---|---|---|---|
| 1 | the `BEFORE` half of the crash reproduction cited `findings-log/2026-0{9,8}-14-lane-s6-public-index/account.py` — **neither brace expansion exists**; the lane's directory is `2026-10-14` | §6 item 6 (a citation that resolves to nothing) | `[ -f findings-log/2026-09-14-lane-s6-public-index/account.py ]` → **MISSING**, same for `08-14`, while `2026-10-14` → **EXISTS** |
| 2 | **two** sites stated **seven** commits beside the **unfiltered** `git log --oneline aa401b7^1..aa401b7`, which prints **12** lines — this file's body, and the same claim in `docs/11` | §6 item 7 / #139's finding 3 — a count the command's own output falsifies | `git log --oneline aa401b7^1..aa401b7 \| grep -cE '^(24b9601\|227a95c\|bfc8f55\|741cca1\|228519f\|d88a879\|f83137d)'` → **7**; `… \| wc -l` → **12** |
| 3 | the `docs/11` pointer recipe recorded in the first Correction section was `grep -n` with **no `-r`** over a **directory**, naming only `CC-MAIN-2020-24` — so it neither ran nor could have matched both rows | the same no-`-r` defect the second Correction section fixed in `docs/11`, left live in this file | the withdrawn form → `grep: docs/: Is a directory`, **exit 2**, **0 rows**; the replacement `grep -rn 'CC-MAIN-2014-10.*(prior)\|CC-MAIN-2020-24.*(prior)' docs/` → **3 rows** |
| 4 | the replacement recipe is published **without** saying that one of its three rows is the sentence quoting it — the exact omission the second Correction section made as its own lesson | §6 item 2 in spirit: a hit that does not mean what a reader assumes | the recipe re-run at this head, three rows, the third being `docs/11`'s own quotation |

**Defect 2 is the one worth naming.** The second Correction section caught a count
that matched neither measurement and fixed it **in its own row** — leaving the same
unfiltered command live in this file's *body*, four hundred lines up, where it
contradicted the same count. The lesson it drew ("a correction recorded and not
applied to the body is a correction that changes nothing") was right and was applied
one level too shallow: **the fix reached the row that quoted the error and not the
sentence that made it.** That is now both changed.

**Defect 3's `\|` is correct here and is not the defect the second section names.**
Plain `grep` is a BRE, where `\|` is alternation; the escaped-alternation bug was `\|`
inside `grep -E`, an ERE, where it is a literal pipe. Both spellings were re-run at
this head rather than reasoned about.

**Nothing measured moved.** `read-area-l.py self-test` → **33 checks, PASS**;
`census` → **2** rows AT their own limit and **7** carrying a limit without reaching
it; `kib-detector.py` → **0 / 183 / 193** under the three rules and the same three
census cells (**81/9/72/2/7**, **74/6/68/1/5**, **72/5/67/1/4**); `locate.sh` → every
landmark resolved; `sh dup-test.sh` → PASS with **0** positions outside the Correction
sections, and its output line count **unchanged at 73** because this pass added no
Correction heading to the log until this one — which moves it to **74**, recorded in
`run.log` under its own dated note, as the two earlier moves were.

**Still a 0-request correction pass, and still nothing re-probed.** The four fixes
above are offline: every one was made by running a command against the committed tree
and reading its exit code. No vendor host was touched, nothing in
`regression/hurl/` moved, and `scripts/measure_assertions.py` reads **217 431** with
no pin added by this PR.

## 9. Artefacts

| file | what |
|---|---|
| `read-area-l.py` | the reader. `population` · `schemas` · `manifest` · `census` · `self-test` |
| `dup-test.sh` | the non-duplicate test `CONTRIBUTING-research.md:199` requires, run for every successor — **printed, never transcribed**, plus the **position check**, which exits non-zero on a position in any spelling outside the Correction sections (§8b) |
| `locate.sh` | **resolves every landmark this file names, by content, bound to a commit.** The replacement for publishing a position: it prints `file:line` for a named SHA and exits non-zero if a landmark cannot be found |
| `kib-detector.py` | **RULES 1–3 of §8b**: the whole-KiB detector, the "successful `200`" counting rule, and the three member-source `limit=` cells. `--json` for machine-readable output. It computes the §7b table — before this script existed, that table had no artefact behind it |
| `manifest.tsv` | the 8 ledgers in precedence order, generated by `manifest` |
| `results.jsonl` | **0 rows** — correct for a 0-request pass, not a missing file |
| `run.log` | the eight invocations and their exit status; no per-request table, because there are no requests |
| `probe.sh` | the record of what was sent: nothing |

Re-derive everything above with **no request and no response body**:

```sh
cd findings-log/2026-10-15-area-l4-ledger-reader
python3 read-area-l.py population   # the population, counted before it is read
python3 read-area-l.py schemas      # rules K1-K3, the schema figures
python3 read-area-l.py census       # the census + the member-limit block
python3 read-area-l.py self-test    # 33 controls, count derived in code
sh       dup-test.sh                # the non-duplicate test + the position check
sh       locate.sh                  # every landmark, resolved by content, bound to a commit
python3  kib-detector.py            # rules 1-3, the truncation cells
```

Every number in this file comes out of one of the commands above.

