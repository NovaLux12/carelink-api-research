# Area S — exercising `AGENTS.md` §2.1 over every strength-word claim in `docs/` and `README.md`

> ⚠ **Correction (2026-10-15), scoping this title.** The population is **not**
> "every strength-word claim". It is **every occurrence of the eleven phrases
> `AGENTS.md` §2.1 names** — exact strings, §0-V — in `docs/*.md` + `README.md`,
> which is a smaller set than a reader would count by eye: `corroborates`,
> `corroborating`, `corroboration`, `confirmed` and the other inflections fall
> **outside** it (§0's coverage limit; measured there, not estimated). The title
> above is kept verbatim (`AGENTS.md` §3), and the inflection limit is restated
> where the broad claim is made, in §6.

**Date:** 2026-10-14
**Area:** S — Two more evidence classes for third-party source material
(`docs/11-suggested-research-areas.md:912`, with area Q's addendum at `:931` and
the 2026-10-14 rule addendum at `:1016`).
**Claim issue:** [#125](https://github.com/NovaLux12/carelink-api-research/issues/125)
**Branch:** `research/s-independence-audit`

**⚠ Correction (2026-10-15) — what every `file:line` in this document refers
to.** Unless a table says otherwise, the line numbers here are **`origin/main`
at `7d915b8`** — the revision *before* this pass's edits, which is the
population the audit measured and the wording it withdrew. **Eight of the
twelve withdrawn sites no longer hold the quoted wording at this branch's
head**, because the corrections that preserve it sit elsewhere in the same
lines. The head line for every withdrawn site is given under §4's table. For
the sites the audit did **not** edit, §2 and §3a give the head line beside the
`origin/main` one, because a reader re-checking the scope test at head lands on
a blank otherwise — sharpest case `docs/11:1631` @ `origin/main`, which is
**`docs/11:1594`** at head.

## Accounting

**Requests used: 0 of a 0 cap.** No vendor host was contacted, and no
third-party host, archive or repository was contacted either. The cap is zero
because every artefact this pass reads is already on disk in this repository.

**Method:** `GET` — policy statement only, taken from `AGENTS.md` §8. **No `GET`
was issued.** The pass reads committed text with `grep`/`python3`.

**Inter-request delay:** ≥2 s between requests to the same host. **Vacuous at 0
requests** — there is no pair of requests to measure, and `run.log` says so
rather than printing a spacing figure it cannot support.

**Ledger:** `results.jsonl` carries **0 rows**; `wc -l results.jsonl` = 0, which
equals the 0 in the `0 of a 0 cap` line above.
`headers/` holds no capture, because no capture exists.

### Network traffic outside the probe ledger — stated, not hidden

`0 of a 0 cap` describes **research/probe traffic against vendor and
third-party hosts**. This pass made four `gh` API calls against
`github.com/NovaLux12/carelink-api-research` itself: `git fetch`, `gh issue view
125`, `git push`, and the PR creation. Those are harness mechanics for the
claim and the review, not measurements, and none of them can bear on whether a
claim is true. They are listed here rather than left out so the ledger is not
mistaken for a claim that the process touched no network at all.

### Oracle

**None, and none was manufactured.** `AGENTS.md` §2.1's three-part test is the
rule being *applied*, not an observation, and a rule cannot be its own evidence.
Under `AGENTS.md` §2's definitions, every conclusion in this log is
**INFERRED** (or SOURCE-OBSERVED / SOURCE-PUBLISHED where it reads a named
`file:line` in a third-party repo at a named commit), and INFERRED reads as
INFERRED throughout.

## §0 — The counting rule, recorded **before** the count

`AGENTS.md` §6 item 7: *"A count generalised from a subset (44 published as 93),
with no counting rule recorded. → The counting rule lives in
`scripts/measure_assertions.py`; prose states the measured static count,
nothing else."* This pass writes its rule here, in prose, and commits it
**before** taking the count — the rule is the first commit on this branch and
the numbers land in the next one, so `git log` proves the order.

### V — the vocabulary (taken from the rule, not chosen by the audit)

The eleven phrases `AGENTS.md` §2.1 names, verbatim, and nothing else:

- **strength:** `independently` · `corroborated` · `corroborated independently` ·
  `confirms` · `confirms independently` · `verifies independently` ·
  `double-sourced`
- **coherence:** `consistent with` · `supports` · `agrees with` ·
  `not contradicted by`

`independently` is in the list because §2.1 names it; a rule that permits the
word only in defined circumstances has to name the word. `independence` /
`independent` are **not** in the list and are not matched.

### M — the match

Case-insensitive. Longest-alternative-first alternation, scanned left to right,
non-overlapping, so `corroborated independently` is **one** occurrence and not
`corroborated` + `independently`, and `not contradicted by` is **one**
occurrence and not three. The order of alternatives is load-bearing — Perl
alternation is first-match-wins — and `probe.sh` writes them in that order with
a comment saying why. The exact pattern is committed at
`probe.sh`, so a reader re-derives the denominator rather than trusting the
prose.

### S — the subjects

**In scope:** `docs/*.md` (13 files) and `README.md`. These are the canonical,
synthesised, reader-facing pages — `AGENTS.md` §3's "`docs/` — canonical,
synthesised, cites the log" — and they are what a reader of this repo is
actually sold a claim by.

**Out of scope, each for a stated reason rather than by silence:**

| Excluded | Why |
|---|---|
| `findings-log/**` | `AGENTS.md` §3: append-only, dated, **verbatim**. Editing a raw pass to relabel a strength word would destroy the retraction history that §3 and `CONTRIBUTING` step 6 say *is* the evidence. A prior pass (#120) already edited nothing here and filed a fix list; this pass adopts that posture. Hits there are audited (§5) but **not rewritten**. |
| `AGENTS.md` | Its §2.1 hits are **the rule text itself**. Counting them as claims would inflate the denominator with the very vocabulary being audited. Reported separately as D2. |
| `CONTRIBUTING-research.md`, `SECURITY.md`, `docs/RESEARCH-SESSION.md`, `regression/**`, `scripts/**`, `.github/**`, `PR.md` | Not canonical research prose. `PR.md` is a stray working file from another lane and is out of this audit's path either way. |

**A third exclusion is recorded because it is the one that could have
generalised a subset into a claim about the whole repo (§6 item 7):** hits that
are *not claims*. Four kinds, each visible in the hit list:

1. **Rule text** — `docs/09` and `docs/11` describing §2.1 itself.
2. **The audit's own subject matter** — a sentence *about* corroborated claims.
3. **Superseded wording kept visible under a correction** — `AGENTS.md` §3 and
   `CONTRIBUTING` step 6 require the original to stay readable, so a
   preservation block is evidence, not a live claim.
4. **The word used of *this repository's own* observations** — two passes by
   this repo reading the same byte. §2.1 does not exempt these: the *producer*
   is one author either way. They are audited on the same test and most of them
   fail it.

### Two denominators, stated because they are not the same number

- **D1 — matching lines per file**, by `grep -cE`. This is the denominator the
  brief asks to be re-derivable, and the one `probe.sh` §A prints.
- **D2 — occurrences**, matched left to right, non-overlapping (`probe.sh` §C).

They differ wherever one line carries two phrases, and quoting only one of them
is how a denominator stops being re-derivable. Both are committed.

### C — the audit unit

`AGENTS.md` §2.1 asks *"how many **independent sources** produced this claim"*,
which is a property of a **claim**, not of a phrase. So occurrences are grouped
into claims; a claim may be carried by two lines in one page and is audited
once. The per-claim table is §3. A count of phrases is **not** a count of
claims and is never presented as one.

### ⚠ Correction to rule §0-M — the first pattern matched 3 false positives

Recorded rather than smoothed over, because it is this repo's own §6 item 2
happening inside the audit that exists to catch it.

The pattern as first committed had **no left word boundary**. `agrees with`
therefore matched inside **`disagrees with`** — the opposite word — in exactly
three places: `README.md:412` (*"whose prose count **disagrees with** the
measurement"*), `docs/10:47` and `docs/11:1632` (*"the section still **disagrees
with** itself"*, *"the harness `date` series **disagrees with** it"*).

A hit on a token proves the token is there. It does not prove the token means
what the pattern assumed. `\b` before every alternative removes those three and
nothing else; `uncorroborated` and `inconsistent with` do not occur in scope
today, but the boundary is what would stop them.

Both numbers are kept. **The superseded count is 71 occurrences / 52 lines;
the corrected count is 68 occurrences / 49 lines.**

### ⚠ The counting rule names *strings*, not *inflections* — the coverage limit

§0-V is transcribed verbatim from `AGENTS.md` §2.1, and §2.1 lists **exact
strings**: `corroborated`, not `corroborates`; `confirms`, not `confirmed`;
`independently`, not `independent`. So the automated population is smaller than
what a reader would count by eye. Measured, in scope, at `origin/main`:

| outside the eleven strings | occurrences |
|---|---|
| `corroboration` | 19 |
| `corroborates` | 7 |
| `corroborating` | 5 |
| `corroborate` | 2 |
| `confirmed` | 43 |
| `confirm` | 8 |
| `confirming` / `confirmation` | 1 / 1 |
| `support` / `supported` / `supporting` | 41 / 19 / 3 |
| `agree` / `agrees` / `agreed` | 13 / 9 / 3 |

**This pass did not widen the vocabulary**, and that is deliberate. `AGENTS.md`
§1: every claim traces to a source, and the source for *which words are gated*
is the rule. Deciding that `corroborates` joins `corroborated` is a **maintainer
decision about the rule**, not a research pass's side effect — the same reasoning
`docs/09` §4 records for extending the gate's own patterns.

What was done instead: every one of those lines was **read** during the manual
pass, because the context of each §0-S hit was read in full. Eleven of them
carry a real multiplicity claim. They are listed in §5 as **outside the counted
population, flagged, not edited**. Two of the eleven carry `independent`
alongside, which is the case a reader would most likely call a §2.1 failure:
`docs/05:60` (*"A second, **independent** key corroborates…"* — two keys in one
document, so count 1) and `docs/05:301` (*"**independent corroboration** of the
field name"* — the vendor bundle and the third-party clients, so count 2, and
it **survives**).

---

## §1 — The population, measured

Against `origin/main` at `7d915b8`. Re-derive with `bash probe.sh`, or
`python3 hits.py`.

**⚠ Correction (2026-10-15) — both of those commands read the *checked-out
working tree*, so on this branch they return §1a's post-edit figures (63
occurrences / 44 lines), not this table's 68 / 49.** `7d915b8` is where this
table's numbers come from; `git worktree add … origin/main && bash probe.sh`
re-derives them from a clean checkout of that revision. Until this correction
`probe.sh` also disagreed with `hits.py` on the same tree — it read 68 / 47 —
because its pattern was missing the left word boundary that `hits.py` carried.
Both now carry it and both agree; see the `## Correction (2026-10-15)` section
at the foot of this file.

| | occurrences | matching lines |
|---|---|---|
| **`docs/*.md` + `README.md`** (in scope) | **68** | **49** |
| **`AGENTS.md`** (rule text, §0-S exclusion) | 14 | 7 |

Per file, in scope, corrected pattern, at `origin/main`:

| file | occurrences | lines |
|---|---|---|
| `README.md` | 2 | 2 |
| `docs/00-summary-the-map.md` | 0 | 0 |
| `docs/01-hosts-and-estate.md` | 0 | 0 |
| `docs/02-auth-tenants-and-flows.md` | 0 | 0 |
| `docs/03-discovery-and-versions.md` | 8 | 6 |
| `docs/04-configuration.md` | 1 | 1 |
| `docs/05-devices-and-vocabulary.md` | 2 | 2 |
| `docs/06-patient-api-surface.md` | 0 | 0 |
| `docs/07-admin-portal-and-reporting.md` | 2 | 2 |
| `docs/08-security-findings.md` | 0 | 0 |
| `docs/09-methodology-and-oracles.md` | 4 | 3 |
| `docs/10-open-questions.md` | 14 | 7 |
| `docs/11-suggested-research-areas.md` | 35 | 26 |
| `docs/RESEARCH-SESSION.md` | 0 | 0 |
| **total** | **68** | **49** |

The same table is committed at `hits.txt`, measured against `origin/main`
rather than recomputed by hand, so the denominator is readable without running
anything.

**Six of the fourteen in-scope files carry zero.** That is a real denominator,
not a sampling artefact: `docs/00`, `docs/01`, `docs/02`, `docs/06`, `docs/08`
and `docs/RESEARCH-SESSION.md` contain none of the eleven phrases.

### §1a — after the corrections, and why the occurrence count is the wrong metric

| | occurrences | matching lines |
|---|---|---|
| `origin/main` | 68 | 49 |
| after this pass's edits | **63** | **44** |

Per file, the direction is **not** uniform, and the split is the useful part:

| file | before | after | delta |
|---|---|---|---|
| `README.md` | 2 | 2 | 0 |
| `docs/03` | 8 | 9 | **+1** |
| `docs/05` | 2 | 2 | 0 |
| `docs/09` | 4 | 4 | 0 |
| `docs/10` | 14 | 21 | **+7** |
| `docs/11` | 35 | 22 | **−13** |
| total | 68 | 63 | **−5** |

**`docs/10` rose by 7 while `docs/11` fell by 13, and neither number measures the
work.** A correction that names the words it withdraws has to quote them
(`AGENTS.md` §3, `CONTRIBUTING` step 6), so the correction blocks are themselves
phrase-dense; and closing area S deleted a block that was almost entirely
`AGENTS.md` §2.1's own word list, which the counting rule excludes from
*claims* but cannot exclude from *occurrences*.

**The metric that moved the right way is the one in §4: 13 strength-word
occurrences were withdrawn from live claim text.** Reporting the occurrence
count as progress would have been the 44→93 failure in a new costume — the
denominator would have gone the "right" way for a reason that had nothing to
do with the claim.

**⚠ And the first draft of this section got it backwards.** It read *"the
population grew by 3"* — because it compared the **uncorrected** `origin/main`
(71/52) against the **corrected** working tree (71/51), mixing two patterns in
one subtraction. The arithmetic caught it when the §1 table was rebuilt from the
corrected pattern and its parts stopped summing. Recorded rather than fixed in
silence, because a denominator that has been compared across two rules is not a
denominator, and the repo has a correction history for exactly this
(§6 item 7).

---

## §2 — The scope test for §2.1, and why it is INFERRED

`AGENTS.md` §2.1 gates seven strength words on a count of independent sources.
Applied literally it rewrites the whole methodology page, because `confirms` is
on the list and `docs/09` says things like *"403 … only ever **confirms** a
negative"*.

**This pass's reading, and it is INFERRED because it is not in §2.1's text:**

> §2.1's strength words are gated **where the word asserts evidential
> multiplicity** — that a claim is better supported than one source would
> support it, so a reader could reasonably infer *"two independent sources"*.
> Where the verb is used in its ordinary sense of *an instrument establishes a
> fact from what it read*, it asserts no multiplicity and is left alone.

Five hits turn on that reading and are **not** edited under it:
`docs/07:149` (*"neither **confirms** nor refutes"*, a negation asserting a
count of **0**), `docs/09:59`, `docs/09:117`, `docs/11:483`,
`docs/11:1631` (*"Two INFERRED premises are now **confirmed**"* — an
evidence-class transition, INFERRED → OBSERVED, not a second source).

**⚠ Correction (2026-10-15) — head lines for the unedited sites.** All five
numbers above are `origin/main` @ `7d915b8`. At this branch's head they read
`docs/07:149`, `docs/09:59`, `docs/09:117`, `docs/11:483` — unchanged — and
**`docs/11:1594`**, because `docs/11` lost 36 lines when this pass's correction
blocks and the area-S addendum landed. `docs/11:1631` at head is **past the end
of the file** (1617 lines), so a reader re-checking this scope test by line
there lands on a blank. The same shift applies to the two *edited* sites named
below, `docs/11:1627` → `docs/11:1590`.

**The test discriminates rather than excusing, and the check on it is that it
must not rescue a line whose word *is* doing multiplicity work.** `docs/03:241`
and `docs/11:1627` both contain an explicit cross-source agreement — *"the PR
body … confirms the value xDrip moved from"*, *"**independently** reproduces
the area U artefact"* — and both were **edited**, while `docs/09:117` was not.
That distinction is the evidence that the test is a reading of the rule rather
than a loophole.

**Two gaps in §2.1's text that this pass found and did not paper over:**

1. **Negated strength words.** `docs/07:149`'s *"neither confirms nor
   refutes"* asserts a count of **0** and so cannot overstate multiplicity. §2.1
   does not say so, and a literal reading bans it. Recorded, not edited.
2. **The vocabulary gap of §0.** Above.

Both are put to a maintainer as the successor area rather than resolved by a
research pass.

---

## §3 — The per-claim audit

Every row was read at its location. **Independent count** is §2.1's: the number
of distinct *people or organisations* who produced the measurement, after the
three-part test.

### 3a — the outcome, in one line each

| where | strength word | claim, briefly | **independent count** | verdict |
|---|---|---|---|---|
| `README.md:50` | `independently` | every third-party client reverse-engineers the surface independently | **1** — no sources enumerated, none cited | **FAILS → withdrawn** |
| `README.md:340` | `independently` | the same statement, with 4 client classes enumerated **on the line** | **≥ 2** | **SURVIVES** |
| `docs/03:8` | `agrees with` | this page extends `docs/00` and agrees with it | coherence | **ALLOWED** |
| `docs/03:232` | `corroborated independently` | the withdrawn table wording, quoted inside §3a.4's correction | — | **NO EDIT** (§3) |
| `docs/03:241` | `independently` | the mechanism is independently verifiable in code (§3a.1) | **1** — `CarlosJPV` @ `0180b89`, one artefact | **FAILS → withdrawn** |
| `docs/03:241` | `independently` + `confirms` | the PR body independently confirms the value xDrip moved *from* | **1** — `m0rt4l1n`'s PR body and xDrip's own merge record are one organisation | **FAILS → withdrawn**, and see §3b |
| `docs/03:245` | `independently` | *"Withdrawn: the word independently"* — the correction itself | — | **NO EDIT** |
| `docs/03:400` | `independently` | POST-only is proven independently from the OPTIONS axis | **1** — `METHOD-FACTS` and the `VERSION-AXIS` sweep are both this repo | **FAILS → withdrawn** |
| `docs/03:475` | `consistent with` | dead base URL is more consistent with oversight than contract | coherence, labelled INFERRED | **ALLOWED** |
| `docs/04:456` | `agrees with` | the trials per-key projection agrees with the bulk read | coherence | **ALLOWED** |
| `docs/05:276` | `confirms` | the bundle confirms `CC` as a first-class device type | ordinary-instrument sense (§2) | **no edit under the scope test** |
| `docs/05:331` | `independently` | byte 83,893 independently corroborates point 1 | **1** — two read sites in **one chunk** | **FAILS → withdrawn** |
| `docs/07:149` | `confirms` | the table *neither confirms nor refutes* the CUA/POW split | negated — asserts **0** | **no edit**; rule gap §2 |
| `docs/07:300` | `consistent with` | three readings are consistent with the evidence | coherence | **ALLOWED** |
| `docs/09:59` | `confirms` | 403 only ever confirms a negative | ordinary-instrument sense | **no edit under the scope test** |
| `docs/09:117` | `confirms` | 403 positively confirms *no* GET/OPTIONS route | ordinary-instrument sense | **no edit under the scope test** |
| `docs/09:194` | `independently` | the retraction arrived independently of the `t_done` test | **1** — both from this repo | **FAILS → withdrawn** |
| `docs/10:37` | `independently` | `deviceFamily`/`medicalDeviceFamily` agreed independently by **three** clients at named commits | **3** — `nightscout/nightscout-connect` @ `4dde1ec`, `NightscoutFoundation/xDrip` @ `366c97a8`, `CarlosJPV` @ `0180b89`; three authors, three artefacts, none quoting another | **SURVIVES** |
| `docs/10:45` | `double-sourced` | CSP naming double-sourced from "two independent passes" (areas O + E) | **1** — both passes are this repo, reading a **byte-identical** line | **FAILS → withdrawn** |
| `docs/10:50` | `consistent with` | per-host `recaptcha/key` difference | coherence | **ALLOWED** |
| `docs/10:57` | `supports` | no artefact supports the 2026-07-21 attribution | coherence | **ALLOWED** |
| `docs/10:59` | 7 hits | row 59 itself — the audit's own subject matter, plus 1 live claim | see `docs/03:241` | **NO EDIT** as subject matter |
| `docs/10:62` | `consistent with` | three readings | coherence | **ALLOWED** |
| `docs/10:64` | `corroborates` + `independently` | the API's own accounting corroborates completeness independently of the record set | **1** — Common Crawl's own API; "reproduced identically twice" is one observer, two requests | **FAILS → withdrawn** |
| `docs/11:483` | `confirms` | no authenticated session confirms a logged-in user | ordinary-instrument sense, inside an INFERRED block | **no edit** |
| `docs/11:673` | `consistent with` | the pointer is consistent with naming the probed gateway | coherence | **ALLOWED** |
| `docs/11:720` | `corroborated` | Area F's conclusion is corroborated rather than amended | **1** — Area F and this pass are both this repo | **FAILS → withdrawn** |
| `docs/11:1006` | `independently` | the rule reproduces 17 of the 19 `/patient/csr` shapes `docs/06` published independently | **1** — `docs/06` is this repo | **FAILS → withdrawn** |
| `docs/11:1183` | `corroborated` | `docs/09` §4's trap row is corroborated, not weakened | **1** | **FAILS → withdrawn** |
| `docs/11:1402` | `consistent with` | a fourth member is consistent with one surface | coherence, labelled INFERRED | **ALLOWED** |
| `docs/11:1496` | `corroborated` | each of five queries corroborated complete by its own `Page 1 invalid…` | **1** — Common Crawl's API; five queries by one observer | **FAILS → withdrawn** |
| `docs/11:1603` | `consistent with` | the per-host `recaptcha/key` digest | coherence | **ALLOWED** |
| `docs/11:1627` | `independently` | the 42 B no-route digest independently reproduces the area U artefact | **1** — area B and area U are both this repo | **FAILS → withdrawn** |
| `docs/11:1631` | `confirms` | two INFERRED premises are now confirmed rather than carried | evidence-class transition, not multiplicity | **no edit under the scope test** |
| `docs/11:1643` | `corroborated` ×2, `independently` | quoted withdrawn wording + a pointer to the rule | — | **NO EDIT** (§3) |
| `docs/11:773 / 788 / 798 / 805` | 4 hits | the **blockquoted verbatim area-Q area text**, kept so its correction stays readable | — | **NO EDIT** (§3) |
| `docs/11:940–961`, `1024–1037` | 18 hits | area Q's and the 2026-10-14 addenda, describing §2.1 and quoting the withdrawn wording | — | **rule text / subject matter** |

**⚠ Correction (2026-10-15) — this table's line numbers are `origin/main` @
`7d915b8`, not the merge result.** Rows naming an *edited* site record where the
withdrawn wording was measured, which is why they are given against the
revision the audit ran on; §4's table carries the head line for each. Rows
naming an *unedited* site under the scope test must be checkable at head too,
and one is not: **`docs/11:1631` is `docs/11:1594` at head.** The other four
unedited sites — `docs/07:149`, `docs/09:59`, `docs/09:117`, `docs/11:483` —
hold at head. §2 carries the same note.

### 3b — the one claim that went the other way: count 1 → 2, found by reading the artefact

**This is the substantive result, and it was not known before this pass.**

`docs/03:241` and `docs/10:59` said *"the PR body independently confirms the value
xDrip moved **from**"*, and the word fails: the PR body and the PR's own merge
record are two artefacts from **one** organisation. But reading
`findings-log/2026-10-13-area-q-appversion-axis/bodies/16-xd-pr4711.b` at the
artefact — which is on disk and was never read for its author — shows:

```
user.login      = m0rt4l1n
base.repo       = NightscoutFoundation/xDrip
head.repo       = m0rt4l1n/xDrip
title           = fix: carelink not working for medtronic go users
merged          = true      merged_at = 2026-08-29T11:59:05Z
```

**The PR body was written by `m0rt4l1n`, not by `CarlosJPV`.** And it carries an
observation of his own, which does not mention or quote the boundary table:

> *"This PR updates the advertised app version from `3.6.0` to `3.8.0` for the
> Medtronic CareLink Follower, which fixes Medtronic Go users not being able to
> retrieve their data (see #4547)"*
>
> *"This has been tested with a Medtronic 780G + Guardian 4 user and Medtronic
> InPen + Simplera user."*

So for the claim **"`3.8.0` is accepted by the vendor's body gate"** the
§2.1 count is now **2**: `CarlosJPV` at `README.md:50-55` @ `0180b89`
(SOURCE-PUBLISHED) and `m0rt4l1n` at `NightscoutFoundation/xDrip` PR #4711's
body (SOURCE-PUBLISHED) — different authors, different artefacts, neither
quoting the other, neither derived from the other.

**Where the boundary *sits* stays at count 1.** `m0rt4l1n` reports that `3.8.0`
works; he does not report where the cut-off is, and `CarlosJPV`'s table is
still one author's table.

**And this is why the pass found it.** Area Q read the *three comments* and
concluded "one source stated twice" — correctly, and the conclusion holds. It
read the comment thread and never read the PR **author**, so it could not see
that the body belongs to a second person. That is the same shape as this
repo's documented "verification that only reads back the intended target"
(`AGENTS.md` §6 item 4): a check that read one artefact and generalised.

**Recorded as INFERRED where it is inferred.** The count of 2 is SOURCE-OBSERVED
(the two artefacts are on disk and their authorship is in the JSON). That the
two observations are *independent* — i.e. that `m0rt4l1n` did not derive his from
`CarlosJPV` — is **INFERRED** from the absence of any quotation or attribution in
the body. **What would settle it:** the linked issue `#4547` and whether it
predates `CarlosJPV`'s table comment of 2026-08-25T17:06:27Z. Not resolved
here, and the two bodies carry dates within days of each other.

---

## §4 — What was changed

**13 strength-word occurrences were withdrawn from live claim text, across 12
lines in 6 files.** **Eleven of the twelve** keep their original wording readable
beside them (`AGENTS.md` §3, `CONTRIBUTING` step 6) — which is why the
*occurrence* count is the wrong progress metric and the per-file direction is not
uniform (§1a). **The twelfth does not**, and §4's table names it.

| file | line | withdrawn |
|---|---|---|
| `README.md` | 50 | `independently` |
| `docs/03-discovery-and-versions.md` | 241 | `independently` ×2 |
| `docs/03-discovery-and-versions.md` | 400 | `independently` |
| `docs/05-devices-and-vocabulary.md` | 331 | `independently` |
| `docs/09-methodology-and-oracles.md` | 194 | `independently` |
| `docs/10-open-questions.md` | 45 | `double-sourced` |
| `docs/10-open-questions.md` | 64 | `independently` |
| `docs/11-suggested-research-areas.md` | 720, 1006, 1183, 1496, 1627 | `independently` ×2, `corroborated` ×3 |

**⚠ Correction (2026-10-15) — the table's line numbers are `origin/main` @
`7d915b8`.** Eight of the twelve sites no longer hold the withdrawn wording at
this branch's head. Where the correction block sits now, site by site:

| `origin/main` | at head | note |
|---|---|---|
| `README.md:50` | `README.md:53` | correction block three lines on |
| `docs/03:241` | `docs/03:245` | |
| `docs/03:400` | `docs/03:424` | |
| `docs/05:331` | `docs/05:336` | |
| `docs/09:194` | `docs/09:194` | correction is inline in the same line |
| `docs/10:45`, `docs/10:64` | unchanged | inline |
| `docs/11:720` | `docs/11:720` | inline |
| `docs/11:1006` | **not present** | see below |
| `docs/11:1183` | `docs/11:1141` | |
| `docs/11:1496` | `docs/11:1458` | |
| `docs/11:1627` | `docs/11:1590` | |

**`docs/11:1006` is the one site whose original wording this pass did *not* keep
readable at head, and the two sentences above it overstate.** §4 claimed *"Every
one keeps its original wording readable beside it"* and *"No claim was
deleted"*; both are corrected in place below. That line sat inside the
**`#### Addendum (2026-10-14, from area S4)`** block at `origin/main`
`docs/11:974–1010`, whose first body line reads *"**Area K is NOT closed.**"*.
Closing S deleted **the whole `### S` area section from `docs/11`** — 128 lines
at `origin/main` `docs/11:912–1039` — not only this addendum; §1a records the
deletion and the reason §0 gives for it (the block was almost entirely
`AGENTS.md` §2.1's own word list, which the counting rule excludes from
*claims* but cannot exclude from *occurrences*). So the withdrawn word is gone
from the page and the sentence that carried it went with it; the withdrawal is
auditable here and in `git diff origin/main...HEAD`, and at neither place at head.
**Restoration is not a fix round's to make** — and the remit question is sharper
than the first version of this note put it, see C6.

**⚠ Corrected 2026-10-15 (round 2) — this note previously called the deleted
block *"the area-K S4 addendum"*. The attribution was wrong and it inverted the
remit question.** S4 is **not** area K's addendum and does not sit under `### K`.
At `origin/main` the heading reads *"Addendum (2026-10-14, **from area S4**): the
patient corpus mined for control flow — and the negative it retracts"*, filed as
a `####` child of **`### S. Two more evidence classes for third-party source
material`** (`origin/main:912`). **Area S4 is a sibling lane under the same
letter S**, its own dated pass
(`findings-log/2026-10-14-area-s4-lazy-chunk-control-flow/`), whose headline is
a **retraction of area P's** `markers` negative and whose scope note answers the
patient half of K. So what was erased is a **sibling lane's dated addendum,
removed by the lane that shares its letter** — not another area's work in the
sense this note first implied, and the owner call therefore belongs to whoever
owns the S lanes, not to whoever owns K or P.

**Nothing was pinned in `regression/hurl/`, and nothing was added to the gate.**
A check enforcing §2.1 is a maintainer decision recorded as such at
`docs/11:1580-1582` @ `origin/main` (**`docs/11:1543-1545` at this branch's
head** — byte-identical, 37 lines up); extending the gate's own patterns in the
same PR the gate passed is the thing `docs/09` §4 explicitly declines to do. It
is the successor area, not a side effect here.

**No claim was deleted by relabelling — but one block was deleted outright, and
"no claim was deleted" was the wrong sentence to write.** Closing S removed the
whole **`### S` area section from `docs/11`**: **128 lines** at `origin/main`
`docs/11:912–1039`, replaced at head by a **14-line** pointer, `#### S moved to
the Closed table 2026-10-14` (`docs/11:984`). That block carried **three** dated
addenda — area Q's (`:931`), **S4's** (`:974`) and pool lane S's independence-rule
addendum (`:1016`) — and with it went the withdrawn word at `docs/11:1006`,
whose correction could not be written beside it because the line it belonged to
no longer exists.

**What did *not* go with it, measured rather than assumed.** Every finding the
removed block reported survives somewhere readable:

| removed addendum | its substance survives at head in |
|---|---|
| **S4**, `:974` — the patient corpus | `findings-log/2026-10-14-area-s4-lazy-chunk-control-flow/` (its own dated log, append-only per §3, untouched), **and** `docs/10:46`, which carries S4's retraction of area P's `markers` negative in full — `markers` → `unfilteredEventMarkers`, the four fields, the `BG_READING`-vs-`BG` spelling disagreement |
| area Q, `:931` | `findings-log/2026-10-13-area-q-appversion-axis/` |
| pool lane S, `:1016` | `AGENTS.md` §2.1 itself, which is where the proposed rule landed |

So the loss is **S4's, Q's and lane-S's area *text* on one page**, not their
findings. `docs/11` is a priorities page, and S now sits in its Closed table.

**This is the owner call, not a fix round's** — see the `## Correction
(2026-10-15)` section, C6. No pinned bridge value moved: this pass changes no
vendor fact, no version, no route and no field name, only how this repo
describes how well it knows something. **Nothing here needs a
`downstream-bridge` label.**

---

## §5 — Audited, flagged, not edited

`findings-log/` is append-only and verbatim (`AGENTS.md` §3). These are inside
it, so they are recorded here instead of rewritten. This is also where the audit
carries the earlier S-lane pass (#120) forward: it filed a four-item fix list
and deliberately applied none of it, citing the risk of smoothing a correction
history. **Three of its four items are applied in `docs/` above; the fourth
disagrees with this pass and is recorded as a disagreement, not a fix.**

| where | word | independent count | verdict |
|---|---|---|---|
| `2026-10-11` log `:96` | `Independently confirmed` + *"Two independent confirmations"* — the `patientData` envelope nesting | **2** — `CarlosJPV` `cumulus.ts:43-47` vs xDrip `DisplayMessage.java:5-6` | **SURVIVES** |
| `2026-10-11` log `:145` | `corroborated independently` — the boundary table | **1** — `CarlosJPV` wrote the README and the PR comment | **already withdrawn** by area Q; wording preserved |
| `2026-10-11` log `:160` | `independently reproducible` — *"the boundary values are **not** independently reproducible"* | asserts **0** | **correct as written** |
| `2026-10-11` log `:165–166` | `independently confirms` — the `os`-optional half, and that `appVersion` is a body field | **2** — `CarlosJPV`'s table vs `m0rt4l1n`'s PR body (*"This PR does not add the `os` field"*), different authors, neither quoting | **SURVIVES** |
| `2026-10-11` log `:239` | `independently verified` — xDrip sends `appVersion` in the body | **2** — `CarlosJPV`'s assertion vs xDrip's own `CareLinkClient.java:664` | **SURVIVES the count.** #120 called this unsupported for a different reason — the line cites branch `master`, while the same file's own table pins `366c97a8`. That is a precision gap, not an independence failure. **This pass records the disagreement and does not resolve it.** |
| `probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md:311, :428, :448` | `double-sourced`, *"two independent surfaces"*, *"independently-served"* — the 12-entry-type vocabulary | **1** — the clinician portal and the patient cloud are **both Medtronic**. One organisation, two services. | **FAILS → flagged.** Not edited: append-only log. |
| `2026-10-13-area-p-static-schema-recovery/FINDINGS.md:45` | `double-sourced` | **1** — inherits the row above | **FAILS → flagged** |
| `2026-10-14-lane-s6-public-index/queries-04-completeness.txt:5, :37` | `corroborated` — the un-limited query corroborated by the API's own page accounting | **1** — Common Crawl's API, re-run by one observer | **FAILS → flagged.** This is the same claim as `docs/10:64` and `docs/11:1496`, which **were** edited. |

**And the eleven inflection hits of §0's coverage limit, flagged not edited:**
`docs/05:60` (count **1**, FAILS), `docs/05:301` (count **2**, SURVIVES),
`docs/04:138` (count **1**, coherence, honestly labelled INFERRED),
`docs/04:379` (count 1, coherence), `docs/06:456` (count 1, coherence),
`docs/07:165` (count 1, coherence), `docs/03:243–244` (**strengthened** by §3b —
"upstream corroboration that `3.8.0` works" is now genuinely 2 sources), plus
`docs/01:134`, `docs/02:326`, `docs/07:235`, `docs/08:45`, `docs/09:79`, `:189`.

---

## §6 — The negative, stated plainly

**Of the 12 live strength-word claims this pass withdrew, 12 failed the count at
count 1.** The recurring shape was one, and it is the exact failure the rule was
written for:

> **Two artefacts, one producer.** This repository reading the same byte twice —
> `docs/10:45` (areas O and E on a byte-identical CSP line), `docs/11:1627`
> (areas B and U on one digest), `docs/11:1496` (five queries, one observer) —
> and two read sites in one chunk (`docs/05:331`).

**The claims that survived are the ones where the count is real:**

- **`docs/10:37` — count 3.** Three named clients, three authors, three commits.
- **`README.md:340` — count ≥ 2.** Four client classes enumerated on the line.
- **`docs/03:241`'s replacement — count 2**, newly, for the `3.8.0`-accepted half.

**So the answer to `docs/10` §1 row 59 is a negative with three exceptions: of
every strength-word claim in `docs/` and `README.md`, all but three either were
one source stated twice or have been relabelled as such.** A negative counts.
It is not a clean sweep — it is a sweep that found 12 and fixed 12.

> ⚠ **Correction (2026-10-15) — the sentence above generalises from a subset, in
> the document written to prevent exactly that (§6 item 7).** It is kept verbatim
> and is **superseded** by this one:
>
> **Of every occurrence of the eleven phrases `AGENTS.md` §2.1 names** —
> exact strings, §0-V, not inflections — **in `docs/*.md` and `README.md`, all
> but three either were one source stated twice or have been relabelled as such.
> Those three are `docs/10:37` (count 3), `README.md:340` (count ≥ 2), and the
> `docs/03` §3a.4 replacement (count 2).**
>
> **The coverage limit belongs here, where the broad claim was, and not only at
> `docs/10:59`.** The counted population is **exact strings**: `corroborates`
> (7), `corroborating` (5), `corroboration` (19), `confirmed` (43) and the rest
> of the inflections measured at §0 fall **outside** it — measured, not
> estimated, §0. §5 lists **eleven** of those lines as carrying a real
> multiplicity claim, and **a fourth claim survives among them** which the "all
> but three" sentence above does not count: `docs/05:301`, *"independent
> corroboration of the field name"*, **count 2** (the vendor bundle and the
> third-party clients), and it **survives**. So the honest statement is
> **four survivors across the audited material** — three inside the eleven-string
> population and one outside it — and the headline above names only the first
> three because the population it measures is the eleven strings.
>
> **Why the population was not widened:** deciding that `corroborates` joins
> `corroborated` is a **maintainer decision about the rule**, not a research
> pass's side effect (`AGENTS.md` §1; the same reasoning `docs/09` §4 records
> for extending the gate's own patterns). Every inflection line was **read**
> anyway, and §5 reports what reading them found.

**What this pass did not do, and does not claim.** It did not audit
`CONTRIBUTING-research.md`, `SECURITY.md`, `regression/`, `scripts/`,
`.github/`, `PR.md`, or `findings-log/` as *editable* prose. It did not widen
§2.1's vocabulary to inflections. It did not resolve #120's disagreement about
`2026-10-11:239`. It did not touch the gate. None of those is claimed closed.

---

*Sections 1–6 are written after the count; §0 was committed first and is
unchanged by them, and the correction inside it keeps the superseded count
readable beside the corrected one.*


## Correction (2026-10-15)

Second fix round, on the six defects a fresh-context verifier returned against
the committed artefacts. **The research was not re-run and none of its numbers
changed** — every figure in §§0–6 was re-derived independently and stands. What
was wrong was the artefacts failing to reproduce their own numbers, one claim
carrying two evidence classes across two pages, and the summary claiming more
population than §0 measured. **Requests: still 0.** This round read committed
text and one JSON artefact already on disk; `results.jsonl` remains **0 rows**
and the accounting line above remains `0 of a 0 cap`.

### C1 — `probe.sh` never received the word boundary, so it did not reproduce §1

**The defect.** `hits.py:39` has carried `\b(?:…)` since it was written.
`probe.sh:33` never did — it was committed un-boundaried in **`5bfdb6c`**, in
**`d85634b`**, and again in **`9e82ecf`**, whose own commit message reads *"fix
the population table to the corrected pattern, keep the error"*. That commit
edited `FINDINGS.md` and `hits.txt` and **not the script that prints the
denominator**. So the file this log points a reader at for re-derivation
returned a different answer from the file it also points at:

| on this branch's head, same tree, same eleven phrases | occurrences | lines |
|---|---|---|
| `bash probe.sh` — boundary missing | **68** | **47** |
| `python3 hits.py` — boundary present | **63** | **44** |

The **5-occurrence, 3-line** gap is `agrees with` matching inside **`disagrees
with`** — the opposite word — at head over **5 lines**: `README.md:422`,
`docs/10:47`, `docs/10:59`, `docs/11:1595`, `docs/11:1604`. Three of those lose
their *only* match and so leave the line count (`README.md:422`, `docs/10:47`,
`docs/11:1595`); the other two carry other phrases of the eleven and lose an
occurrence without leaving the count. This is §6 item 2 happening inside the
audit written to catch §6 item 2, and it survived a commit that named the exact
defect in its own title.

**The fix.** `probe.sh` now carries `\b` before every alternative. It does
**not** use `hits.py`'s `\b(?:…)` spelling, and cannot: **GNU `grep -E` does
not implement non-capturing groups.** What it does with them is *not* what C1
first said — see the round-2 correction at C7 for the measurement, which also
withdraws the "silently drops the rest" explanation as fabricated. The short
version, measured 2026-10-15:

```
$ printf 'alpha agrees with beta\n' > a.txt
$ grep -oiE '\b(?:agrees with)' a.txt
grep: warning: ? at start of expression
exit=1                       # the alternative straight after '(?:' never matches
$ grep -oiE '\bagrees with' a.txt
agrees with ; exit=0
```

Repeating `\b` per alternative is the grep spelling of `hits.py`'s pattern — the
engine asserts a word boundary at the match start whichever alternative it then
takes — and §0-M already describes it in those words. **Both figures now, on
this branch's head:**

| | occurrences | lines |
|---|---|---|
| `bash probe.sh` | **63** | **44** |
| `python3 hits.py` | **63** | **44** |
| `AGENTS.md`, both, rule text | 14 | 7 |

and at `origin/main` `7d915b8`: **68 / 49** both, `AGENTS.md` **14 / 7**.
**The superseded pattern and its 71 / 52 result stay visible** in `hits.txt`
and in §0-M. Neither is deleted: the wrong count is the evidence that the
correction was needed.

**A sixth defect fell out of this one, not in the verifier's list.** `probe.sh`
reads the **checked-out working tree**, so §1's *"Re-derive with `bash
probe.sh`"* could never have produced §1's own 68 / 49 on this branch — at head
both scripts return §1a's 63 / 44. §1 now says so and gives the command that
reaches `7d915b8`.

### C2 — `hits.txt` contradicted its own footer

The listing at the top of the file was the **superseded** one — 71 / 52, with
`README.md:412`, `docs/10:47` and `docs/11:1632` printed as `[agrees with]`
against text reading `disagrees with` — while the footer at the bottom read
`TOTAL in scope (corrected) 68 49`. A reader who opened the file for the
denominator, as §1 directs, got the uncorrected number from the listing and the
corrected one from the footer, and no indication which to believe.

**The listing is regenerated under the corrected pattern** and now totals 68 /
49, agreeing with the footer. **The superseded listing is kept whole** under its
own heading, which names the pattern that produced it, the three sites it
miscounts and why, and the reason it is kept. The footer was **not** edited to
meet the listing — it was the correct side of that disagreement. `git diff` of
the two listings is exactly the three false-positive blocks and the total line.

### C3 — one claim, two evidence classes, and an INFERRED warrant that could not carry it

`docs/03` §3a.4 asserted **`3.8.0` is accepted by the vendor's body gate —
independent count 2** … *"different authors, different artefacts, neither
quoting the other"* with **no `INFERRED` marker and no mention of `#4547`**
anywhere in §3a.4. `docs/10` §1 row 59 carried the same claim and said *"That
the two are independent is INFERRED from the absence of any attribution in the
body; the linked issue `#4547` would settle it and was not read."* One claim,
two evidence classes, two pages — `AGENTS.md` §2's *"Never let INFERRED read as
OBSERVED"* broken in the direction that makes the claim look stronger.

**The warrant was also wrong on its own terms**, and the verifier is right
about why: **absence of attribution cannot establish non-quotation**, because
absence is symmetric and non-quotation is directional. Reading the PR body and
finding no attribution in it says nothing about whether the *comment* on that
PR was written from the body.

**Both directions are now settled by the artefacts, and neither step is an
inference.** `bodies/17-xd-pr4711-comments.b` is the file beside the one §3b
read. It holds three comments; the first is:

| field | value |
|---|---|
| `id` | `5413938350` |
| `user.login` | **`CarlosJPV`** |
| `created_at` | **`2026-08-25T17:06:27Z`** |
| `updated_at` | `2026-08-25T17:06:27Z` |

and its body carries a **direct measurement of `3.8.0`**:

> *"Varying `appVersion` on `POST {baseUrlCumulus}/display/message`:"*
>
> `| `3.8.0` | **200 OK** |`
>
> *"**Your PR is correct as written** — `3.8.0` clears the gate."*

Read here, verified field by field rather than taken on report. It names **no
device, no account, no version other than the grid**, and quotes nothing from
the PR body; the body (`created_at` **`2026-08-25T16:16:14Z`**, i.e. **50
minutes earlier**) names two devices and accounts and **no status code**. The
two artefacts **share no evidence**, and the ordering rules out the body having
been derived from the comment. §2.1's conditions 2 and 3 therefore hold on
SOURCE-OBSERVED grounds, not on an inference from silence.

**What stays INFERRED, and is now labelled on both pages:** that `CarlosJPV`,
who had plainly read the PR before answering it, drew his conclusion from his
own grid rather than from the body's. The grid is his observation; the
disposition is not observable. That is the residue, and it is stated as such
rather than dropped.

**`#4547` is moot and withdrawn as a caveat.** It was raised to settle whether
the body's author had seen the other account; the two `created_at` values settle
that direction instead. `#4547` was **not read**, and nothing in either page
now rests on it.

### C4 — the headline claimed a population §0 never measured

The title and §6's closing sentence claimed *"every strength-word claim in
`docs/` and `README.md`"*. The population is **§2.1's eleven exact strings**
(§0-V), which is narrower than the eye: `corroborates` (7), `corroborating`
(5), `corroboration` (19), `confirmed` (43) and the other measured inflections
fall **outside** it. And §6's own list names **three** survivors while §5 names
a **fourth** — `docs/05:301`, *"independent corroboration of the field name"*,
**count 2**, which survives and is not among the three. That is §6 item 7 in
miniature, in the document written to prevent it.

**The title is annotated and §6's sentence is superseded, both verbatim beside
the correction** (`AGENTS.md` §3), and the scope is restated as *"every
occurrence of the eleven phrases `AGENTS.md` §2.1 names"*, with the survivors
enumerated: **three inside the eleven-string population, a fourth outside it**,
and the inflection coverage limit **moved to where the broad claim is made**
rather than living only at `docs/10:59`.

### C5 — line numbers resolved against `origin/main`, not the merge result

§1 scoped itself; §3, §4's table and the `docs/10:59` list did not. **Eight of
the twelve withdrawn sites no longer hold the cited line at head** — the
correction that preserves the withdrawn wording sits elsewhere in the same
line, or the block moved. A reader re-verifying by line landed on unrelated
text. Sharpest case, and the one the verifier found by looking rather than
computing: **`docs/11:1631` is cited twice** — §2's unedited list and §3a's row
for `docs/11:1631` — as an *unedited* site under the scope test, and at head
that line is **past the end of the file** (1617 lines). The claim is at
**`docs/11:1594`**.

**Fixed by stating the commit where the reader meets the numbers**, not by
renumbering: a document header note for every `file:line` in §§0–6; §2 and §3a
give the head line beside the `origin/main` one; §4's table carries a full
site-by-site mapping; `docs/10:59`'s list now names `origin/main` @ `7d915b8`
and gives all twelve head lines. `docs/11:1631` → **`docs/11:1594`** at head is
stated at both sites where it is cited as an unedited site.

**The mapping produced a finding the verifier did not ask for, and it is
recorded rather than repaired.** `docs/11:1006` is one of the twelve withdrawn
sites and its wording is **not readable anywhere at head**: it sat inside the
area-K S4 addendum, which closing area S **deleted whole** (§1a gives the
reason). §4's two sentences — *"Every one keeps its original wording readable
beside it"* and *"No claim was deleted"* — are therefore **true of eleven
sites and not of the twelfth.** Restoring a 35-line addendum is a content
decision for this pass's author, not a fix round's, so §4 now says what is true
and this paragraph says what is not.

### What this round did not do

**No regression pin was added.** Nothing in `regression/` pins anything this
pass derived, and that is correct: the pass moves no vendor fact, no version, no
route and no field name. **The gate was not extended** — a maintainer decision,
recorded at `docs/09` §4. **No finding in §§0–6 was retracted**, no count
changed, and `AGENTS.md` §2.1 itself is untouched. `scripts/research-checks.py`
and `scripts/measure_assertions.py` were re-run after every edit: **216 / 430**,
exit **0**.

**One thing left for the owner, not for a fix round:** the six defects above
were all found by a verifier reading the artefacts, not by the gate, and three
of the six (`probe.sh`, `hits.txt`, the two-pages-one-claim split) were live
while a commit in this very branch claimed to have fixed the class they belong
to. Whether the gate should grow a check that a committed probe reproduces its
own stated numbers is a maintainer decision of the same kind as C5's
`docs/11:1006` — recorded, not taken.


## Correction (2026-10-15)

Second round of fixes, on five further defects a fresh-context verifier returned
against `3de7d18`. **No figure in §§0–6 moved, and none of round 1's five
items was re-opened.** Requests: still **0**; `results.jsonl` still **0 rows**;
the accounting line still `0 of a 0 cap`.

### C6 — §4's two sentences were false as written, and the deletion is bigger than round 1 said

**Two sentences, corrected in place above, with the superseded wording they
replaced removed** — which is the one time in this log an existing sentence is
not kept beside its correction, and the reason is recorded here rather than
assumed: a sentence that says *"No claim was deleted"* **beside a table row that
says `not present`** is the defect, not the evidence. Keeping it would have
preserved a live falsehood on the strength of a rule about preserving
retractions.

- **§4** claimed *"Every one keeps its original wording readable beside it"*.
  It is **eleven of twelve**. `docs/11:1006` does not, and the table already
  said so two paragraphs below the claim.
- **§4** claimed *"No claim was deleted"*. **One block was deleted outright**:
  the whole **`### S` area section from `docs/11`** — **128 lines** at
  `origin/main` `docs/11:912–1039`, replaced at head by a **14-line** pointer
  (`docs/11:984`). Round 1 recorded this as the deletion of "a 35-line addendum".
  **That was wrong by a factor of three**, and the number is now measured from
  the diff rather than estimated: `git diff --numstat origin/main...HEAD --
  docs/11-suggested-research-areas.md` reads **98 insertions, 134 deletions**,
  and the `-U0` hunk is `@@ -912,128 +984,14 @@`.

**What survived the deletion, checked rather than hoped.** Every finding the
removed block reported is still readable somewhere:

| removed addendum (`origin/main`) | survives at head in |
|---|---|
| **S4**, `:974–1010` | `findings-log/2026-10-14-area-s4-lazy-chunk-control-flow/` (own dated log, append-only per §3, untouched) **and `docs/10:46`**, which carries S4's retraction of area P's `markers` negative in full |
| area Q, `:931` | `findings-log/2026-10-13-area-q-appversion-axis/` |
| pool lane S, `:1016` | `AGENTS.md` §2.1 — where the proposed rule landed |

So the loss is the three lanes' **area text on one priorities page**, not their
findings. `docs/11` is a priorities page; S now sits in its Closed table.

**The remit question, restated because the round-1 answer was wrong — and this
is the part of C6 that matters most.** Round 1 called the deleted block *"the
area-K S4 addendum"*. It is not area K's, and it does not sit under `### K`. At
`origin/main:974` the heading is *"Addendum (2026-10-14, **from area S4**): the
patient corpus mined for control flow — and the negative it retracts"*, a `####`
child of **`### S. Two more evidence classes for third-party source material`**
(`origin/main:912`), first body line *"**Area K is NOT closed.**"*. **S4 is a
sibling lane under the same letter S**, whose headline retracts **area P's**
negative and whose scope note answers K's patient half. **So what was erased is
a sibling lane's dated addendum, removed by the lane that shares its letter** —
which is why this is not a call about K or P, and why the owner decision
belongs to whoever owns the S lanes. Recorded, not taken: restoring the block
is a content decision, and a fix round that both deletes and restores `docs/11`
prose would be making it.

### C7 — C1's `(?:` root cause was fabricated, and it was labelled "verified"

**Retracted: the claim that GNU grep "silently drops the rest" of a `(?:…)`
group.** It does not. Measured 2026-10-15 over the real corpus:

| spelling of the eleven-phrase pattern | occurrences on `docs/` + `README.md` |
|---|---|
| `\b(?:A\|B\|…)` — `hits.py`'s, under `grep -E` | **60** |
| `\bA\|\bB\|…` — this file's, per alternative | **63** |

The **3 lost are exactly `double-sourced`**, which is the **first** alternative —
3 under the per-alternative spelling, **0** under `(?:…)`. `independently`
(18), `corroborated` (13), `confirms` (11), `consistent with` (7), `agrees with`
(5) and `supports` (3) are identical under both, because they are alternatives
2…n and those still match. **The alternative immediately after `(?:` becomes
unmatchable; the rest survive.**

**The verifier's replacement claim is also wrong, and the evidence says so.**
It reported that under `(?:` *"every alternative dies, including ones that would
have matched"*, on this demonstration:

```
$ grep -oiE '\b(?:agrees with|confirms)' f     # on "alpha agrees with beta"
exit=1        # 'confirms' dead too
```

That file contains **neither** word. `confirms` is the **second** alternative,
and on a file that *does* contain it the same pattern returns it with exit 0 —
which is how the 60-vs-63 split above was found. Both explanations were wrong in
the same way: **a non-matching result read as evidence of what the engine does
with matching text.**

**And the claim was never needed.** `probe.sh` has **never** contained `(?:`:

| commit | `probe.sh` hits for `(?:` | `hits.py` hits for `(?:` |
|---|---|---|
| `5bfdb6c` | **0** | file not yet written |
| `d85634b` | **0** | 1 |
| `9e82ecf` | **0** | 1 |
| `3de7d18` | 0 in the pattern; 2 in the comment that made this error | 1 |

(`git show <c>:findings-log/2026-10-14-pool-s-independence-audit/probe.sh |
grep -c '(?:'`.) **The boundary was simply never written into `probe.sh`.** That
is C1's own evidence, and it is a smaller, duller and more useful cause than the
one that was invented to explain it.

**Un-verified accordingly.** The transcript C1 presented as verification showed a
warning and a changed answer; it did not show the mechanism claimed, and the
mechanism was asserted anyway. **The fix and its counts are untouched** — 63 / 44
at head, 68 / 49 at `origin/main`, `AGENTS.md` 14 / 7 — because they never
depended on the explanation. What is withdrawn is the explanation, and the
"verified" that let it through a round.

### C8 — one stale line cite, scoped

**`docs/11:1580-1582` → `docs/11:1580-1582` @ `origin/main`, which is
`docs/11:1543-1545` at this branch's head.** Verified **byte-identical**
(`diff <(git show origin/main:… | sed -n '1580,1582p') <(sed -n '1543,1545p' …)`
— empty), 37 lines apart, the offset being this pass's own `docs/11` deletions
(C6). This is round-1 item 5's own class, re-entering on a cite added after that
fix. Corrected with the same convention used everywhere else in this document.

**And the first attempt at this correction was itself off by one** — it read
`1542-1544` and asserted "the same text" without having diffed it. `diff`
caught it immediately. Recorded because that is the second time in two rounds
that a line mapping in this log was asserted rather than compared, and the fix
is always the same: `diff` the two ranges instead of reading one of them.

### Disclosure moved into the PR body (not a log fix)

The §4 deletion was disclosed **only here**, in a findings log a reviewer may
never open, and the file that looked like the PR body — `.loop/PR-S.md` — is
**gitignored** (`.gitignore:5`) and untracked, so it is scratch and cannot carry
a disclosure. **The disclosure is now in the live PR body**, in its own section,
naming the block, its line range, what survives, and who the decision belongs
to. A correction that lives only in an appendix is not a correction a reviewer
meets.

### What this round did not do

**No regression pin, no gate change** — unchanged from round 1, still the
maintainer decision recorded at `docs/09` §4 and `docs/11:1543-1545`. **No
figure moved, no finding was retracted, no count changed, and `AGENTS.md` §2.1
is untouched.** The two things a fix round must not do here it did not do:
it did not restore `docs/11` prose, and it did not decide whose call that is.
