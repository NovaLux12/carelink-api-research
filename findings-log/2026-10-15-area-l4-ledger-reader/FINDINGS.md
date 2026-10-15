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
  wanted a request and did not issue it — see §6, *Successors* 1 and 2.

The work is a local read. `probe.sh` records the four commands that were run;
none of them can be made to send a request by editing an argument.

## 1. The population, counted before it is read

**Counting rule R1**, recorded here and implemented in `read-area-l.py`'s
`population()` mode, in this order:

1. `git ls-files 'findings-log/**/results.jsonl'` — **44** committed ledgers
   **at this branch's head**. This number **moves as passes land**: it was 43
   before this pass added its own ledger, and any later merge moves it again.
   Only step 2's answer (8) is meant to be stable, and step 2 is re-checked
   against rule R2 below rather than trusted.
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
(19 rows): **39 rows, 10.3% of the 380-row population** (39 ÷ 380 = 0.10263),
**not in the corpus the census was derived from.** Both are area-L work by their own `**Area:**` lines above. This
is a finding, not a style note: a census that says "re-derived from the ledgers"
was re-derived from six of the eight.

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
and each is exercised by `python3 read-area-l.py self-test` (exit 0, **25
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
(`AGENTS.md` §2.1, artefact 3). Same for `docs/11-suggested-research-areas.md`
lines 1736 and 1738, which already list both crawls' members and mark them
`(prior)`. **One source, three times quoted.**

**The repo therefore already contradicted itself, and the contradiction was
visible without any new evidence.** `docs/11:1736` lists
`CC-MAIN-2014-10 /ipro/hcp/login.jsf` at 2014-03-10, and `docs/11:1738` lists
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

`docs/11-suggested-research-areas.md:1650` and the closed-area table at `:2170`
both publish:

> **`/ipro/hcp/` is absent from 65 of the 84 in-window crawls**

**That reconciles with neither available reading, and the arithmetic is the
check:**

| reading | in-window RECORD | absent = 84 − RECORD | states |
|---|---|---|---|
| `census-84.txt` as committed | **65** | **19** | absent from **19** |
| this pass's re-derivation | **72** | **12** | absent from **12** |
| `docs/11:1650` / `:2170` | — | — | absent from **65** |

**65 is the census's RECORD cell read into the *absent* slot.** Under the
committed census the correct absent count is 19, not 65; under the re-derivation
it is 12. The same 65 cannot be an absence count under either, and 84 − 65 = 19
is exactly the number the committed file supports.

**Recorded, not fixed.** Both lines are out of this pass's lane — `:1650` sits in
area prose and `:2170` is in the closed-area table, neither of which belongs to
the S-L4 paragraph — so the finding is a successor (§8.5) with all three readings
standing. It is worth naming that this pass hunted this exact class twice
(`docs/11:1736`/`:1738` against `census-84.txt:36`/`:102`), wrote a successor for
each, and **missed a third instance on the same page** that its own new figure
made checkable in one subtraction.

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

- **A non-zero count can be a floor.** A reader cannot distinguish "this crawl
  holds 3 members" from "this crawl holds at least 3, and the pass read one page".
  Nothing published here claims an upper bound on any crawl's members.
- **A `0` is only as good as the row it came from.** Which is why `CC-MAIN-2013-48`
  is now **NOT DERIVABLE** rather than `0`: its only member-bearing DATA row is a
  **502**, and an empty list on a failed query carries no information at all.

Closing this needs either the bodies (a disclosure decision, not a research pass's)
or a ledger field distinguishing "computed, found none" from "not computed"
(successor §8.3). Both are named; neither is claimed.

## 8. Successors

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
3. **Every member count is a floor, not an exact total, and nothing in the tree can
   say otherwise** (§7a). **Blocker:** the response bodies are outside the tree by
   `AGENTS.md` §7, so "does a committed `200` row's member list enumerate every
   member in that crawl" is undemonstrable offline. **Closes when** either the
   bodies are made available under a disclosure decision, or every ledger row
   carries a field distinguishing "computed, found none" from "not computed" — a
   `shape` field as `ipro-hcp` already has, or an explicit `members_computed`.
   **Zero requests** for the second route. **Assumptions (INFERRED):** that a
   boolean in the ledger is enough for the second route; nothing in the tree says a
   later pass would populate it.
4. **One reader for the other 36 committed ledgers** (the claim's own successor,
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
   the other 36 should expect the name rule and the `**Area:**` line to disagree
   and should report both.
5. **`docs/11:1650` and `:2170` publish an absence count that reconciles with
   neither reading — the census's own RECORD cell, read into the absent slot.**
   `"/ipro/hcp/ is absent from 65 of the 84 in-window crawls"`. Under the committed
   census the absent count is **19** (84 − 65); under this pass's re-derivation it is
   **12** (84 − 72). **65 is neither.** **Blocker:** both lines are outside this
   pass's lane — `:1650` is area prose, `:2170` is the closed-area table, neither is
   the S-L4 paragraph. **Closes when** one of the three readings is chosen on stated
   grounds and the other two are retired with their arithmetic shown, or the
   sentence is re-derived from a named verdict rule. **Zero requests.**
   **Assumptions (INFERRED):** that "absent from X of 84" means *no member found*
   rather than *no `200`-bearing probe* — the two coincide only if RECORD and
   member-carrying are the same set, and this pass's own re-derivation shows they
   are not (12 crawls carry members; 72 answered `200`). **Stated because this pass
   hunted this exact class twice and missed a third instance on the same page.**

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
| 4 | "**43** committed ledgers" (§1, step 1 of R1) | "**44** … **at this branch's head**, and this number moves as passes land" | 43 was true before this pass added its own ledger. The recorded rule must reproduce at the commit under review; the **answer (8) is unchanged**. |
| 5 | *(new §6 subsection + successor §8.5)* | — | `docs/11:1650`/`:2170` publish "absent from 65 of the 84", which reconciles with neither the committed census (19) nor this pass's re-derivation (12). Recorded as a successor; **out of lane, not fixed.** |
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

| file | what |
|---|---|
| `read-area-l.py` | the reader. `population` · `schemas` · `manifest` · `census` · `self-test` |
| `manifest.tsv` | the 8 ledgers in precedence order, generated by `manifest` |
| `results.jsonl` | **0 rows** — correct for a 0-request pass, not a missing file |
| `run.log` | the five invocations and their exit status; no per-request table, because there are no requests |
| `probe.sh` | the record of what was sent: nothing |

Re-derive everything above with `python3 read-area-l.py census` — offline, no
request, no response body needed. `python3 read-area-l.py schemas` re-derives
every schema figure in §2 and §2b under rules K1–K3.