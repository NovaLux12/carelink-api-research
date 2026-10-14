# Area S — exercising `AGENTS.md` §2.1 over every strength-word claim in `docs/` and `README.md`

**Date:** 2026-10-14
**Area:** S — Two more evidence classes for third-party source material
(`docs/11-suggested-research-areas.md:912`, with area Q's addendum at `:931` and
the 2026-10-14 rule addendum at `:1016`).
**Claim issue:** [#125](https://github.com/NovaLux12/carelink-api-research/issues/125)
**Branch:** `research/s-independence-audit`

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

| | occurrences | matching lines |
|---|---|---|
| **`docs/*.md` + `README.md`** (in scope) | **68** | **49** |
| **`AGENTS.md`** (rule text, §0-S exclusion) | 14 | 7 |

Per file, in scope, corrected pattern:

| file | occurrences | lines |
|---|---|---|
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
| `docs/10-open-questions.md` | 15 | 8 |
| `docs/11-suggested-research-areas.md` | 36 | 27 |
| `docs/RESEARCH-SESSION.md` | 0 | 0 |
| `README.md` | 3 | 3 |

**Six of the fourteen in-scope files carry zero.** That is a real denominator,
not a sampling artefact: `docs/00`, `docs/01`, `docs/02`, `docs/06`, `docs/08`
and `docs/RESEARCH-SESSION.md` contain none of the eleven phrases.

### §1a — after the corrections, the count goes **up**, and that is correct

| | occurrences | matching lines |
|---|---|---|
| `origin/main` | 68 | 49 |
| after this pass's edits | 71 | 51 |

**The population grew by 3 occurrences on 2 lines.** `AGENTS.md` §3 and
`CONTRIBUTING` step 6 require the superseded wording to stay readable next to
its correction, so each correction block necessarily re-prints the words it
withdraws. **The count of withdrawn strength words is the number that matters
and it went down: 13 occurrences of a strength word were removed from live
claim text** (§4). A pass that drove the occurrence count to zero would have
had to delete the retraction history, which is the one thing it must not do.

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
lines in 6 files.** Every one keeps its original wording readable beside it
(`AGENTS.md` §3, `CONTRIBUTING` step 6) — that is why the occurrence count went
**up** by 3 (§1a).

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

**Nothing was pinned in `regression/hurl/`, and nothing was added to the gate.**
A check enforcing §2.1 is a maintainer decision recorded as such at
`docs/11:1580-1582`; extending the gate's own patterns in the same PR the gate
passed is the thing `docs/09` §4 explicitly declines to do. It is the successor
area, not a side effect here.

**No claim was deleted.** No pinned bridge value moved — this pass changes no
vendor fact, no version, no route and no field name, only how this repo describes
how well it knows something. **Nothing here needs a `downstream-bridge` label.**

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

**What this pass did not do, and does not claim.** It did not audit
`CONTRIBUTING-research.md`, `SECURITY.md`, `regression/`, `scripts/`,
`.github/`, `PR.md`, or `findings-log/` as *editable* prose. It did not widen
§2.1's vocabulary to inflections. It did not resolve #120's disagreement about
`2026-10-11:239`. It did not touch the gate. None of those is claimed closed.

---

*Sections 1–6 are written after the count; §0 was committed first and is
unchanged by them, and the correction inside it keeps the superseded count
readable beside the corrected one.*
