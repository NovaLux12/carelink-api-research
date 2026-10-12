# Area D — the 18-country sweep, completed

Run date: **2026-10-12**. Claim issue:
[#22](https://github.com/NovaLux12/carelink-api-research/issues/22).
Harness: [`probe.sh`](probe.sh), run **once**. Ledger: `results.jsonl`
(119 rows, one per request). Per-country verdicts:
[`verdicts.jsonl`](verdicts.jsonl) — one record per country, produced by
[`reader.py`](reader.py), which issues **zero** requests. The complete
country × key state matrix is [`matrix.tsv`](matrix.tsv) and the enumeration
is [`contradictions.tsv`](contradictions.tsv).

This file records what came off the wire and what the reader made of it. Where
a value was absent, the literal `(none)` stands in place of the value.

---

## 1. Request accounting

- **119 of a 130 cap.** Composed of **118 country codes** (the offline-derived
  candidate list, §2) plus the `ZZ` absent-code control. **0** hurl
  pin-validation requests were used; the four new assertions added to
  `regression/hurl/05-public-config.check.sh` are validated by running that
  suite, which is a single extra request per suite run and is accounted for in
  that file, not here. **11** of the cap are unused.
- `wc -l results.jsonl` = **119**, `seq` contiguous 1..119, no gaps, no extras.
  `run.log` holds the same 119 request rows plus its one header line.
- **GET only.** 119 of 119. No POST, no token exchange, no authentication. No
  `Authorization`, no `Cookie`, no `x-api-key`. The only header `probe.sh` adds
  is a `User-Agent`, plus `Accept-Encoding` from `curl --compressed`.
- One host: `carelink.minimed.eu`. Every other vendor host was left alone.
- `probe.sh` carries a `CAP=130` guard that exits 9 *before* issuing a request
  past the cap, and refuses to run a second time if `results.jsonl` or `run.log`
  already exists. The harness count cannot silently double.
- **Nothing was re-requested.** Every parse, comparison and re-derivation in
  this pass ran against the bytes already on disk.

### Delay between requests

`probe.sh` sleeps **2.5 s between requests to the same host**, inside the
per-host lock (three other pool workers share this machine and this host).

**The canonical measurement is the body-file mtime series, not the harness's own
`date` series.** `curl` wrote each body with `-o bodies/cc-XX.json`, so the
**kernel** set that mtime when the write completed — a series independent of the
`date` calls that are themselves under suspicion.

**Counting rule**, so this number cannot be re-derived differently: one gap per
consecutive pair **in request order** taken from `run.log` (4 controls first,
then the sweep in `candidates.txt` order), measured as `mtime[n+1] − mtime[n]`;
**119 bodies, 118 gaps**; the two 400 envelopes (`ZZ`, `ID`) included, since
they were requested like any other and carry the same mtimes.

| Series | gaps | >=2.5 s | **<2.5 s** | **<2.0 s** | min | max |
|---|---|---|---|---|---|---|
| **`bodies/` mtime (kernel-set) — canonical** | 118 | **118** | **0** | **0** | **2.575 s** | 2.636 s |
| `t_sent` (harness `date`, in-lock) | 118 | 104 | 14 | 8 | 1.642 s | 3.515 s |
| `t_queued` (harness `date`, pre-lock) | 118 | 108 | 10 | 2 | 1.792 s | 3.377 s |

**The `>= 2 s` repository floor was never breached: 0 of 118 gaps below it.**

The mtime span is **304.9 s**, which equals both harness spans (304.9 s) to the
tenth of a second — the cross-check `ledger.py` now emits, and the reason the
series can be trusted as the run's own files rather than a checkout artefact.

**Limit of this oracle, stated because it bounds its reuse.** Git does **not**
preserve mtimes: on a fresh clone or `git archive` the 119 body files all carry
the checkout time and the spread collapses to **0.0 s** (verified). So this
measurement is valid **only on the machine that ran the probe**, and what gets
committed is the **number**, not the ability to re-derive it. `ledger.py`
re-checks the span on every run and says so either way.

**Why the two `date` series are reported at all, given the above.** They are the
fourth pass in a row to record a same-host gap below its own declared sleep, and
this pass added the evidence that the series is not to be trusted: **11 of 119
requests carry a NEGATIVE duration** (`t_done` earlier than `t_sent`), which is
impossible, and **10 of the 14 sub-2.5 s gaps are predicted to within 0.020 s**
by `2.5 + duration(n)`:

| pair | observed sent-gap | predicted `2.5 + dur(n)` | residual | dur(n) |
|---|---|---|---|---|
| 4 → 5 | 1.970 s | 1.950 s | +0.020 s | −0.550 s |
| 16 → 17 | 2.179 s | 2.159 s | +0.020 s | −0.341 s |
| 28 → 29 | 1.964 s | 1.945 s | +0.019 s | −0.555 s |
| 40 → 41 | 1.873 s | 1.853 s | +0.020 s | −0.647 s |
| 52 → 53 | 1.792 s | 1.772 s | +0.020 s | −0.728 s |
| 64 → 65 | 1.733 s | 1.714 s | +0.019 s | −0.786 s |
| 76 → 77 | 1.793 s | 1.773 s | +0.020 s | −0.727 s |
| 81 → 82 | 1.907 s | 1.887 s | +0.020 s | −0.613 s |
| 93 → 94 | 2.013 s | 1.994 s | +0.019 s | −0.506 s |
| 105 → 106 | 2.011 s | 1.992 s | +0.019 s | −0.508 s |

**Four gaps are NOT explained this way** — 45→46, 57→58, 69→70 and 117→118.
Three follow a request with a *positive* duration and a residual of −0.65 to
−0.86 s, so the shortfall sits in the `t_done → t_sent` interval, which is not
the interval the sleep occupies. 69→70 straddles a negative-duration request
and does not fit cleanly either.

**No cause is asserted** for the `date` series' behaviour, consistent with
`docs/09` §4. What is established, and is the operationally relevant fact:
**the `>= 2 s` rule was met**, by the one series not produced by the suspect.

---

## 2. Candidate list — 118 codes, derived offline, zero requests

The list is **the union of the country codes the vendor's own published public
config enumerates**, computed by [`candidates.py`](candidates.py) from the
three config documents captured on 2026-10-12. **Counting rule** (stated so the
number cannot be re-derived differently): a country code is any 2-character
`A-Z` string appearing, inside the value of a top-level key whose name contains
`countr` (case-insensitively), as an array element, as an object key, or as the
value of a member named `country`; unioned over `carelink.minimed.eu`,
`carelink.minimed.com` and `carelink-trials.minimed.com`.

The 118 codes, with the document that lists each, are in
[`candidates.txt`](candidates.txt). Provenance: **110** appear in all three
config documents, **6** in `eu`+`trials` only, **2** in `eu` only (`BO`, `PY`).

> ⚠ **The count in the area statement does not reproduce.** `docs/11` and the
> claim issue both say **109** recorded country codes. Measured from the
> captures on disk with the rule above: **118**. The difference is **not
> reconciled here** — the earlier number has no counting rule recorded with it
> (AGENTS.md §6.7), so this pass can neither confirm nor explain it, and it
> states only what it measured. The 2026-10-10 drift note records the lists
> growing 17 → 26 → 29 during a live rollout
> ([`DRIFT-AND-NEW`](https://github.com/NovaLux12/carelink-api-research/blob/main/findings-log/probe-2026-10-08/recon/DRIFT-AND-NEW-2026-10-10.md)),
> so a stale count is plausible and an arithmetic slip is equally plausible.
> **Both readings are left standing**; the number this pass used is 118 and the
> rule for it is in `candidates.py`.

The three config captures are **gitignored** (that pass found credential-shaped
values in the config document and chose redaction over capture), so `118` is
**not re-derivable from a clean clone** without re-fetching them. The full code
list is committed in `candidates.txt` so the sweep can be repeated without it.

---

## 3. Controls — 4, sent FIRST, before any candidate

| seq | code | role | status | what it proved |
|---|---|---|---|---|
| 1 | `GB` | CONTROL-live | **200** | The endpoint serves and the reader parses: **33 keys**, all 33 reference keys resolved, **zero** contradictions, zero flags. The two unit keys agree (`MMOL_L`/`MMOL_L`). A known-live positive control on the recorded shape (OBSERVED, `docs/04-configuration.md:340`). |
| 2 | `BE` | CONTROL-contradiction | **200** | **The detector reproduces the repo's only positive contradiction evidence.** `bgUnits = MG_DL`, `glucoseUnitsDefault = MMOL_L`, exactly as `docs/04:379` records. The reader is validated against a known contradiction before 115 further requests are spent on it. |
| 3 | `CH` | CONTROL-contradiction | **200** | Served, but **did not reproduce** — `docs/04:379` records CH as the second contradicting country and **CH is coherent today** (§4). Reported as a **correction**, not smoothed over. |
| 4 | `ZZ` | CONTROL-absent | **400** | `{"field":null,"message":"Error! Country:ZZ Not Supported","params":{}}`, 87 B. A missing country is a **3-key error envelope, not a short document** — which is what makes "key absent" and "value null" distinguishable at all, and matches `docs/04:337`. |

**The BE/CH control did what it was sent for, including by failing.** Had CH
come back contradicting as recorded, this pass would have reported a
two-country finding. It did not, and that is the single most consequential
thing the controls established.

### One candidate is refused, and it is not `ZZ`

`ID` — Indonesia — is enumerated by **all three** vendor config documents, and
the endpoint answers **`400 "Error! Country:ID Not Supported"`** (87 B, the same
envelope as `ZZ`). **OBSERVED.** So the union of the vendor's published country
lists and the set of countries this endpoint will serve are **not the same
set**: at least one code the vendor publishes is refused by the vendor's own
country endpoint. `ID` is the **only** one of the 118 refused.

---

## 4. The headline finding — the recorded contradiction is not a two-country quirk

`docs/04:364-383` records exactly two contradicting countries, BE and CH. Swept
across every country the vendor's own config lists, the shape is far larger:

| `bgUnits` | `glucoseUnitsDefault` | countries | client consequence |
|---|---|---|---|
| `MMOL_L` | `MMOL_L` | 51 | none — coherent |
| `MG_DL` | `MG_DL` | 36 | none — coherent |
| **`MG_DL`** | **`MMOL_L`** | **30** | **a client reading either key scales glucose by a factor of ~18** |

**30 of the 117 served countries** return `MG_DL` from `bgUnits` and
`MMOL_L` from `glucoseUnitsDefault`. Full list, with both values per country:
the first 30 rows of [`contradictions.tsv`](contradictions.tsv).

```
AE AR AW BE BO BR CO CW EC EG ES GR IL IN IT JM JP KR LB MV MX NC PE PK SA SD TH TT UY VE
```

> ⚠ **Correction to a published claim.** `docs/04:379` — "**BE and CH report
> `MG_DL` for `bgUnits` but `MMOL_L` for `glucoseUnitsDefault`**" — is
> **incomplete and, for CH, no longer true.**
>
> - **BE reproduces.** `MG_DL` / `MMOL_L`, unchanged since 2026-10-08.
> - **CH no longer contradicts.** Live `CH` returns `bgUnits = MMOL_L` and
>   `glucoseUnitsDefault = MMOL_L`. The recorded `MG_DL` for CH is not what
>   the endpoint returns on 2026-10-12.
> - **The set grew in the other direction.** Of the 18 countries swept on
>   2026-10-08, **`IT` and `ES` have drifted into the contradiction**:
>   both were recorded `MG_DL`/`MG_DL` and both return `MG_DL`/`MMOL_L` today.
>
> **Counting rule, so these numbers cannot be read as generalisations:** the
> comparison is `bgUnits` vs `glucoseUnitsDefault` on the live 2026-10-12
> document, and **only** documents that parsed as an object are counted —
> 119 requests, 117 country documents, 2 error envelopes (`ZZ`, `ID`) excluded.
> The three drifted countries are computed by comparing each live value against
> the value recorded at
> [`docs/04-configuration.md:376-377`](https://github.com/NovaLux12/carelink-api-research/blob/main/docs/04-configuration.md);
> the other 15 of the 18 reproduce exactly.

**This is the finding that changes what a client must do**, and it is the reason
the area was worth doing. A bridge that reads `bgUnits` and a bridge that reads
`glucoseUnitsDefault` will render the same reading on a screen 30 countries
apart, in units differing by ~18×.

---

## 5. The full contradiction enumeration

**51 tier-1 contradictions** across **10 distinct classes**, all internal to a
single country response, every one with both values recorded in
[`contradictions.tsv`](contradictions.tsv). Tier 1 means: two keys that draw
from the **same closed vocabulary** and disagree, so no benign reading is
available from the document.

| # | class | n | countries |
|---|---|---|---|
| 1 | **glucose-unit disagreement** | **30** | AE AR AW BE BO BR CO CW EC EG ES GR IL IN IT JM JP KR LB MV MX NC PE PK SA SD TH TT UY VE |
| 2 | **carbohydrate-unit disagreement** | **5** | AE AM ES GE KZ |
| 3 | **legal-document path names a language the document does not list** | **5** | MO MY SI TH VN |
| 4 | **postal format rejected by its own regex** | **3** | KZ (×1), PR (×2) |
| 5 | **HR_12 with a pattern carrying no meridiem** | **2** | BW MD |
| 6 | **24/7 hours on a days list that omits a day** | **2** | MD UZ |
| 7 | **duplicate report entry** | **1** | DO |
| 8 | **MFA `REQUIRED` with `gracePeriod` 0** | **1** | NO |
| 9 | **US region with no subdivision list** | **1** | PR |
| 10 | **date separator differs between the two date fields** | **1** | RS |

The five that are worth more than a table row:

**2 — carbohydrate units (5 countries).** `carbDefaultUnit` vs
`carbohydrateUnitsDefault`, the same closed enum (`GRAMS` / `EXCHANGES`).
Across the corpus: `GRAMS`/`GRAMS` 109, `EXCHANGES`/`EXCHANGES` 3,
`EXCHANGES`/`GRAMS` 4, and **`grams`/`GRAMS` 1 (AE)**. AE's `carbDefaultUnit` is
lowercase `'grams'` where every other document in the corpus uses the enum
member `'GRAMS'`; the same document supplies `carbExchangeRatioDefault = 15.0`,
which is only meaningful for grams, so "a second unit choice" is not an
available reading. A client doing an exact-match on the enum silently misses
AE. `AM`, `ES`, `GE`, `KZ` genuinely select exchanges in one key and grams in
the other.

**3 — legal-document paths in an unlisted language (5 countries).** The
strongest statement this document supports about its own paths: every locale
segment in `pathDocs` must name a language the document's **own `languages`
array** lists. `MO` serves an FAQ under `/en/` while listing only `ZH-HANT`;
`SI` serves an FAQ under `/sv/` while listing `SL`+`EN`; `MY` serves four
documents under `/ms/` while listing only `EN`; `TH` under `/th/` listing only
`EN`; `VN` under `/vi/` listing only `EN`. These are the client's
**privacy-notice and terms-of-use URLs** — the documents a consent flow points
a patient at.

**4 — postal format rejected by its own regex (KZ, PR).** Each document
publishes `postal.postalFormat` examples and `postal.regExpStr`, and the
expression rejects the document's own examples: `KZ` publishes `["999999"]`
against `^[0]{1}[0-9]{5}$`; `PR` publishes `["99999-9999","99999"]` against
`00[6-9]\d{2}([\-]\d{4})?`, which matches neither. `GB` and `US` both pass
their own expressions. A client validating an address against the published
expression rejects every address the document itself shows.

**8 — `NO` is the one country with MFA `REQUIRED` and a 0-day grace period.**
This reproduces the recorded NO-is-`REQUIRED` fact and adds the pairing: a
mandatory factor with no enrolment window.

### Tier 2 — 124 disagreements where a benign reading IS available

Not counted as contradictions, and kept separate so the tier-1 count stays
honest. `name` vs `defaultCountryName` differ in **50** countries
(`Belgium`/`België`, `Switzerland`/`Schweiz`, …) — **the localisation reading
is strongly supported**: BE's `defaultLanguage` is `NL` and its
`defaultCountryName` is `België`, so the pair is "English name" and "name in the
default language". `mfa.fromDate` disagrees with the document's own date format
in 24 countries by ordering and 50 by separator (US publishes a `-` separator
and a `/`-separated `fromDate`). These are observations, not demonstrated
faults.

### Flags — 74, INFERRED rules, reported and not counted

`techHours` outside a strict `H:MM - H:MM` shape in **74** countries. This
extends the repo's recorded NL finding (`findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md:239`) to 74 countries, and the
shape varies (`08:30-17:00`, `8.30 - 17.00`, `7:00 am - 7:00 pm CST`). The rule
is an assumption about parsers, not a claim about the vendor, so it is a flag.

---

## 6. Absent is not null, and 2026-10-12 proves it across 117 countries

The reader resolves every key of every document to **ABSENT / NULL / VALUED**
using an explicit `has()` on a path walked **one segment at a time** with a
container-type assertion at each step — never `//`, never a bare dotted
`dict.get` (`docs/09` §4, §5.3). The full matrix is
[`matrix.tsv`](matrix.tsv); this is the artefact area W's successor needs.

> ⚠ **Two corrections to `docs/04`, both from the `absent`-vs-`null` confusion
> this repo has already been bitten by twice.**
>
> - **`cpMobileAppAvailable`** — `docs/04:428` says it "is `false` for 16
>   countries and **`null` for GB and IE only**". Measured across 117 live
>   documents: **ABSENT in 41**, `false` in **75**, `true` in **1** (AU), and
>   **`null` in zero of 117**. So the key is **never null**, it is **absent in
>   GB and IE**, and the "16 countries" undercounts by 59. The repo's own
>   regression suite already says the stronger thing — `04-deep-surface.hurl`
>   pins `jsonpath "$.cpMobileAppAvailable" not exists` for GB, with the
>   comment "**GB does not even carry the flag — the key is absent, not
>   false**". **`docs/04` was contradicting the repo's own pinned assertion.**
> - **`stateCodes`** — `docs/04:418` says it is "`null` for all 17 others".
>   Measured: **ABSENT in 115 of 117**, present in exactly **CA** and **US**,
>   and `null` in **none**.

**The key set is 33, 34 or 35 keys** — the document is **not uniform**, which is
the fact area W needed and did not have:

| keys | countries | what is missing relative to the 35-key set |
|---|---|---|
| **35** | 2 (CA, US) | — |
| **34** | 74 | `stateCodes` |
| **33** | 41 | `stateCodes`, `cpMobileAppAvailable` |

The full 35-key vocabulary is in [`reference-keys.json`](reference-keys.json).
**No key outside that vocabulary appeared in any of the 117 documents**, and the
report-name vocabulary is exactly the 11 names already recorded — **zero
vocabulary deltas**.

---

## 7. Three reader defects this pass found in itself

Recorded because a reader that cannot fail is worse than no reader
(`docs/09` §5), and each of these would have manufactured a finding:

1. **A case-sensitive meridiem pattern read the US document as a 24-hour
   pattern.** GB ships `shortTimeFormat = "h:mm a"`, US ships `"h:mm A"`. The
   offline self-test flagged US as *"HR_12 with a 24-hour pattern"* — a
   contradiction that does not exist. Fixed to a case-insensitive pattern.
2. **Two rules asserted things the repo's own record refutes.** A rule firing on
   *any* endpoint host not matching the region flagged **US and PR** — but
   `docs/04:427` records `blePereodicDataEndpoint` as **constant** at
   `clcloud.minimed.eu` across all 18 swept countries, US included, so the `.eu`
   value is a recorded constant and the rule would have invented a finding.
   A second rule flagged **CA** for carrying subdivisions on a non-US region —
   but CA ships 13 **Canadian province** codes (`CA-ON`, `CA-QC`, …), the key is
   named `stateCodes` while holding whatever country's subdivisions were asked
   for, and the document is self-consistent. Both rules were rewritten to claim
   only what the document supports. CA and US no longer appear in the
   enumeration; PR appears once, for a genuinely different reason (§5, row 9).
3. **A normalisation bug reported a naming convention as 15 contradictions.**
   HK, MO and TW set `defaultLanguage = "ZH-HANT"` and serve paths under `/zh/`.
   A literal comparison called every one of their paths a contradiction. The
   rule now normalises script subtags and asks the question the document can
   actually answer — *is this locale in the document's own `languages` array* —
   which cut 18 reported findings to **5**, all of which survive verification.

The self-test that caught (1) ran on the three country documents already on disk
from the 2026-10-12 published-pointers pass, at **zero requests**. A fourth
defect — a `report.py` comprehension that bound the record instead of the
finding — was caught by running it.

---

## 8. What this pass did not do

- **No cross-country difference table.** The area's instruction is to attack
  internal contradictions, not differences between countries. `matrix.tsv` is a
  **state** matrix (ABSENT/NULL/VALUED) and deliberately carries no per-key
  value comparison. Deriving the cross-country tables is area W's subject.
- **No new host, no new route, no DNS, no POST, no token.** One host, one route,
  one query parameter.
- **No wordlist.** Every candidate is a code the vendor's own published config
  enumerates.
- **No re-request.** Every verdict is derived from bytes on disk.
- **No client-bug filing.** Nothing here is a bridge defect; the consequences
  named are consequences *for* a client that reads these keys, and §9 says which.

---

## 9. Downstream

The `bgUnits` / `glucoseUnitsDefault` split is exactly the class AGENTS.md §3
calls out: a finding that changes a value a client pins. **A bridge reading one
unit key mis-scales glucose in 30 countries, not the 2 `docs/04` records.**
That is a `downstream-bridge` matter and is filed as such, separate from this
PR, naming the pinned constant:
[#29](https://github.com/NovaLux12/carelink-api-research/issues/29).

---

## 10. Files in this log

| File | What it is |
|---|---|
| `probe.sh` | the harness, as sent |
| `run.log` | 119 request rows + column header; three timestamps each |
| `results.jsonl` | the request ledger, one row per request |
| `headers/` | response headers per request |
| `bodies/` | response bodies per request |
| `candidates.py` | derives the 118-code candidate list offline; counting rule in its docstring |
| `candidates.txt` | the 118 codes with per-code provenance |
| `reference-keys.json` | the reader's 35-key vocabulary |
| `reader.py` | per-key state + contradiction rules; zero requests |
| `ledger.py` | builds `results.jsonl` and `spacing.txt`; zero requests |
| `report.py` | renders `verdicts.jsonl`, `matrix.tsv`, `contradictions.tsv`, `summary.txt`; zero requests |
| `verdicts.jsonl` | one reader record per country |
| `matrix.tsv` | country × 35-key ABSENT/NULL/VALUED matrix |
| `contradictions.tsv` | the enumeration, both values per finding |
| `summary.txt` | the counts this file quotes |
| `spacing.txt` | both gap series, every sub-2.5 s gap listed |
---

## 11. Follow-up rounds — verifier findings and the counting-rule correction

Two later rounds changed bookkeeping, not findings. **Every research result in
this log is unchanged**: the 30-country set, the 51 tier-1 contradictions across
10 classes, `verdicts.jsonl`, `bodies/`, `headers/`, `results.jsonl` and
`run.log` are byte-identical to what the first pass produced.

### Round 1 — a fresh-context verifier, zero vendor requests

It re-derived every result from raw bytes by a route that does not pass through
this prose, and cleared the two claims it pressed hardest:

- **The delay was never breached.** From the body-file mtimes (§1) — **118 gaps,
  minimum 2.575 s, 0 below 2.5 s and 0 below the `>=2 s` floor.** The harness
  `date` series reported 1.642 s and 8 sub-2 s gaps; those timestamps carry 11
  negative durations, so they cannot all be faithful. **The settling evidence
  was on disk and nobody looked** — which is why §1 now leads with the mtime
  oracle and `docs/09` §4 records the method and its counting rule.
- **`cpMobileAppAvailable`**: the reader's distribution (ABSENT 41 / false 75 /
  true 1 / null 0) reproduced exactly under an independent reader; the pin is
  right, `docs/04` was wrong, and `04-deep-surface.hurl`'s `not exists` for GB
  must not change.

Four defects it found in this pass's own bookkeeping, all fixed:

1. **`reader.py` did not reproduce the artefact it shipped with.** Two causes:
   `name[:-5]` yielded `cc-XX` from `cc-XX.json`, so the subdivision-prefix rule
   tested `cc-CA-` and emitted two spurious tier-1 findings (53 vs the committed
   51); and **sorting filenames reordered every row**, so the output differed
   byte-for-byte even once the records were identical. The shipped command now
   reproduces `verdicts.jsonl` byte-identically. *The first fix alone would have
   looked like it worked* — the second only showed up when the bytes were
   compared rather than the counts.
2. A docstring said US carries **51** subdivision codes; it carries **50**.
3. The canonical spacing statement was a `date` reading; it is now the mtime
   series, and `docs/09` §4 gains the method.
4. Stale `docs/04` line citations, re-derived against this HEAD. Two were wrong
   **even at the base commit**: `docs/04:238` never pointed at NL's dotted clock
   (that line reads "itemised in any source") and now cites
   `CONFIG-NAMESPACE-DEEP.md:239`, its real source.

It also found that **this PR asserted a `downstream-bridge` issue was filed when
it was not.** It was not, and per `AGENTS.md` §3 the finding was incomplete
until the consumer was linked — [#29](https://github.com/NovaLux12/carelink-api-research/issues/29)
now exists, names both keys and links the PR.

### Round 2 — the counting rule (owner decision)

Area D added four checks inside an `if`/`else` in `05-public-config.check.sh`.
They are **indented**, and `measure_assertions.py` used indentation as its proxy
for "inside the 16-family loop":

```python
if line[0] in ' \t': loop_sites += 1
```

Indentation says a line is **nested**, not that it is nested *in a loop*, so
four once-executed checks were multiplied by 16 — `executed_05` **61 → 125**,
derived runtime **359 → 423**, against the **363** the suite actually printed.

**Both numbers stood in prose** (README.md ×2, docs/00, docs/09) and the gate
was green against one of them, because the gate's numbers check reads the
*derived* figure when no suite log is present and the *measured* one when it is
— so the same tree could be checked against two different numbers. The owner
ruled it a rule bug. **Prose is unchanged at 363**, which is what the corrected
rule now measures.

**Evidence the fix discriminates rather than merely differing:**

| tree | check sites | old (indent) | new (structural) |
|---|---|---|---|
| base `b275e2b` (miscount absent) | 41 | 1 | **1** |
| this branch (4 in an `if`/`else`) | 45 | 5 | **1** |

The old rule was **right at base by accident** — nothing indented existed there
to misread — so it cannot distinguish the two trees. The corrected rule returns
**1 on both**, and its `executed_05_derived` (65) equals the live `N passed`
(65) without being passed it. The under-count direction is covered too:
`--self-test` asserts that a check inside an `if` **nested in a loop** is still
a loop site, alongside 15 other shell shapes.
