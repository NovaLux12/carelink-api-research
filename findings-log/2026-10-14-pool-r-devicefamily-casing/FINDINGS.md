# Area R — `deviceFamily` casing: the vocabulary reconciled, and the question retired

**Pass date:** 2026-10-14 (pool run 2026-10-14, worker R) · **Claim issue:**
[#124](https://github.com/NovaLux12/carelink-api-research/issues/124) ·
**Method:** offline reconciliation over committed artefacts — no probe, no
network call of any kind · **Requests: 0 of a 0 cap.**

> **Accounting.** This pass sent **0** HTTP requests to any Medtronic, MiniMed or
> Abbott host — and **no request of any kind to any host**, which is the point.
> The cap is zero because nothing is probed. ⚠ **The accounting sentence that stood
> here — *"`results.jsonl` holds **0** rows and the `N of a M cap` line above reads
> **0 of a 0 cap**"* — asserted a state of this file in the present tense and
> unanchored, and is therefore quoted here rather than restated per `AGENTS.md` §3.**
> It held at `6b493e7` and is machine-checked by `research-checks.py`'s findings-log
> hygiene rule, which fails if `results.jsonl` carries more rows than the cap line
> claims. **Re-derive rather than read it off this sentence:**
> `wc -l < results.jsonl`. The ledger and the prose
> agree in both directions, which is checked by `scripts/research-checks.py`
> (findings-log hygiene) and again by `probe.sh` itself.
>
> **Method space.** The only method this project may use is **GET** (`AGENTS.md`
> §8). It was **not used** — there is no request. The word appears in this
> document only because the accounting format requires the method to be named, as
> in the 2026-10-11 third-party pass (`findings-log/2026-10-11-third-party-client-sources/FINDINGS.md:6-16`).
>
> **Inter-request delay.** The standing floor is **≥2s** between requests to the
> same host. At zero requests it is vacuous; it is recorded here rather than
> paraphrased away, because a pass that says "no delay needed" without saying
> *why* has left the floor unstated.
>
> **The oracle, stated honestly: there is none.** A zero-request pass cannot
> manufacture an oracle, and this pass does not try. `deviceFamily`'s wire casing
> is token-gated (`VALIDATION-RUNBOOK` Tier 1) and remains unobserved. **The
> expected outcome of this area is a negative**, and the value of this PR is that
> the repository now says so, says why, and says what would change it.

**Controlling discipline for this pass: provenance.** `OBSERVED` is reserved for
what a live response shows, and this pass has none. Every claim below is
therefore either (i) an observation *in a committed vendor artefact at a pinned
digest*, (ii) **SOURCE-OBSERVED** — `file:line` at a **named commit** in a named
third-party repository — or (iii) **INFERRED** with its assumption shown. **An
artefact with no commit pinned is not usable as SOURCE-OBSERVED**, and §3 below is
largely about one such artefact.

---

## 1. The claim under audit

Area R's close condition has two limbs: *"one authenticated `monitor/data`
response records the key-name and its value's casing verbatim, **or** a note in
`docs/05` records that the value casing stays unobserved and why"* (area R,
`docs/11-suggested-research-areas.md:876-879`). The first limb is permanently
blocked. This pass discharges the second, and in doing so found that the
argument area R inherited **over-counted its own evidence** and that one of the
three candidate vocabularies **does not meet the provenance bar** the pass itself
sets.

---

## 2. Three vocabularies, and they do not merely disagree — they are not the same kind of thing

The claim issue named three candidate sources. Measured, there are **four**, and
the fourth was recorded in this repository on 2026-10-08 without anyone noticing
it was a fourth.

| # | Candidate set | n | Where it is recorded | Class |
|---|---|---:|---|---|
| 1 | the 16 published family tokens | 16 | `findings-log/2026-10-13-area-h-report-naming/family-map-verbatim.txt:1-16` (keys of `personal.device.family.to.model.mapping`) | PUBLISHED in vendor config; the endpoint itself OBSERVED |
| 2 | the client matcher enum | 5 | `findings-log/probe-2026-10-08/recov/PATIENT-APP-VOCABULARY.md:18-19`; re-anchored with a byte offset at `findings-log/2026-10-13-area-p-static-schema/FINDINGS.md:120-131` (module `45559`, byte 1,723,245, patient bundle sha256 `0fb4fbd4…`) | OBSERVED in a digest-pinned vendor bundle |
| 3 | `NGP` | 1 | `findings-log/2026-10-14-area-s4-lazy-chunk-control-flow/FINDINGS.md:353-354`, from four comparison sites in lazy chunk `k-6746-c6795ff7e9ff468d-js.b` (bytes 76,304 / 78,359 / 83,893 / 87,564) | OBSERVED in a hash-pinned vendor chunk |
| 4 | the third-party client's four DTO tokens | 4 | `findings-log/probe-2026-10-08/APP-EMULATION-RESEARCH.md:384-385` (`GUARDIAN`, `NGP`, `CGM`, `CC`) | **not SOURCE-OBSERVED — no named commit** (see §3) |

Set 4 is the one `docs/05` already carried and labelled INFERRED
(`docs/05-devices-and-vocabulary.md:277-279`, "carried forward from an earlier
round and not re-derived here"). This pass **re-derived it to a committed
line** — which is the only thing that was missing — and found the line itself
names no commit for the xDrip revision it was read from.

### The answer to "are they the same kind of thing?" — INFERRED

**INFERRED**, on these assumptions, shown because the answer is reasoning and not
something a file states:

1. Set 1 is a **published identifier axis**: the keys of a vendor config mapping
   from family to model codes. Medtronic publishes these names.
2. Set 2 is a **client-internal routing classification**, consumed by
   `deviceFamily.startsWith(…)` — a *prefix* match, so it constrains only the
   leading characters of a value, not the whole string.
3. Set 3 is a **client-internal equality comparison** on the same field, four
   sites, none of them a prefix match.
4. Set 4 is a **third-party client's own DTO enum** — a four-value product-role
   classification (`CC` includes Instinct), which that artefact's own text notes
   "None of the four contains `BLE` or `SIMPLERA`"
   (`APP-EMULATION-RESEARCH.md:386`).

**Therefore the three are two different kinds of thing, not one vocabulary with
disagreements:** a published identifier set (1), a prefix-matched client routing
class (2+3), and a third-party product-role enum (4). A union of them is a
**candidate pool for a future match**, not a statement that any one of them is
the wire vocabulary. Two consequences a matcher should be built for:

- Under set 2, `CGM` and `CC` match **nothing** — they fail all five `startsWith`
  tests. Under set 2, `BLE_MINIMED` (excluded, §3) would match `BLE`.
- Sets 1 and 4 share **no string at all**; sets 2+3 and set 4 share exactly one
  (`GUARDIAN`), and sets 1 and 2+3 share exactly one (`SIMPLERA`).

---

## 3. The counting rule, stated before the count

`AGENTS.md` §6 item 7: *a count generalised from a subset (44 published as 93),
with no counting rule recorded.* This repository has that failure already. The
rule below lives in `count-candidates.py` (this directory), and every member is
**extracted from a committed artefact at a named `file:line`** — so the
denominator is re-derivable from a clean clone and an anchor that stops resolving
exits non-zero rather than defaulting.

- **R-1 unit.** One candidate **value string** for the family/discriminator
  field — exact, case-sensitive. Not a model, not a device, not a display name.
- **R-2 membership.** A string is admitted iff a committed artefact records it as
  (a) a key of `personal.device.family.to.model.mapping`; (b) a member of the
  patient bundle's `deviceFamily` matcher enum; (c) a string the patient client
  compares that field against; or (d) a value a named third-party client declares
  for `deviceFamily`/`medicalDeviceFamily`, **where that artefact carries a
  `file:line` at a named commit**. A set failing its own clause is not admitted,
  and the count it *would* have produced is printed beside the real one.
- **R-3 exclusions**, each reported rather than dropped:
  - model codes (`MMT-*`, `SKU-*`) and display names are **not** members — they
    are the **match table**, counted separately. A wire value equal to a model
    code is a different finding from one equal to a family token, and folding the
    two together is how a union becomes a sum;
  - `deviceType` values (`CC`, `COSMOS`, `COSMOS_WHITELISTED`, `DEVICE`) are
    excluded **as `deviceType`**;
  - a string whose only citation is not `file:line`-at-named-commit is not
    counted, and its withdrawal is printed.
- **R-4 duplicates.** A string in more than one admitted set is counted **once**.
  The sum of the sources is printed beside the union precisely so the difference
  is visible.
- **R-5 scoping.** The union counts client/config-side strings. **No member is
  OBSERVED on the wire**, and this rule cannot promote anything.

### The result

```
UNION SIZE (the published number) = 21
sum of the admitted sources      = 27   (NOT the answer; 6 shared strings)
S-MAP 16 · S-ENUM 5 · S-CLIENT 6  →  21 distinct
overlaps: S-MAP∩S-ENUM {SIMPLERA}; S-MAP∩S-CLIENT {SIMPLERA};
          S-ENUM∩S-CLIENT {BLE, BLE_X, GUARDIAN, SIMPLERA, SIMPLERA_X}
DECLARED BUT NOT ADMITTED — S-CLIENT-DTO: if admitted, 23, not 21 (+2: CC, CGM)
MATCH TABLE (excluded by R-3): 78 MMT-* + 9 SKU-* = 87 model codes;
          87 display-name pairs (76 quoted + 2 unquoted aliases + 9 SKU-*)
```

**21 candidate value strings, under a rule stated above the number.** The 27 is
printed beside it so nobody mistakes the sum for the union — the difference is
six shared strings, which is exactly the arithmetic that makes 44 become 93.

### The conditional is the finding

**One of the three candidate vocabularies in the claim issue does not meet the
bar this pass sets for itself.** Set 4 (`GUARDIAN`/`NGP`/`CGM`/`CC`) is recorded
at `APP-EMULATION-RESEARCH.md:384-385`, whose own heading says the schema is
"from xDrip's message classes" — **no `file:line`, and no named commit for the
xDrip revision it was read from.** A bare "the upstream PR #2 tests"
(`:390`) is a PR number, not a commit. Under **R-2(d)** the set is therefore
**not admitted**, and the union is **21, not 23**.

The repair is small and is recorded rather than performed: the 2026-10-11 pass
read xDrip at **`366c97a8`** (tag `2026.10.10`,
`findings-log/2026-10-11-third-party-client-sources/FINDINGS.md:44`), so a
`file:line` at that commit would admit the set and move the number to 23. Until
that cite exists, `CGM` and `CC` are **not candidates this repository has
earned**. This is not a claim that they are wrong — it is a claim that we cannot
point at.

### Named withdrawals (R-3), with the reason each is not counted

| String | Cite | Why not counted |
|---|---|---|
| `MINIMED` | `findings-log/2026-10-11-third-party-client-sources/FINDINGS.md:69` | "values seen by these clients" — no `file:line`, no per-client attribution. **These two strings appear in exactly two places in the whole repository: that line, and `docs/10` row 37 echoing it.** ⚠ **The count in this cell is FALSE — see `## Correction (2026-10-15)`, item C6.** Three files carry each token as a claimed `medicalDeviceFamily` value, plus one file carrying `PARADIGM` as an era label; the count above was published as the ground for the withdrawal and does not survive `git grep -w` at base `7d915b8`. Preserved unedited under append-only; the withdrawal itself stands, on the carriers being uncited rather than on their number. |
| `PARADIGM` | same line | same defect |
| `BLE_MINIMED` | `APP-EMULATION-RESEARCH.md:390` | cited to "the upstream PR #2 tests" — fails R-2(d) |
| `Ut.Ey.all` | `recon/JS-API-SURFACE.md:604` | a `deviceFamily`-**filter** key over a server-populated `localStorage` object, not a family value |
| `CC`/`COSMOS`/`COSMOS_WHITELISTED`/`DEVICE` | `recon/JS-API-SURFACE.md:562` | `deviceType` values, excluded **as `deviceType`** |

---

## 4. What `docs/05` now records as the close

`docs/05` gains a dated close recording: **the value's casing stays unobserved,
with the reason**; **the reconciled candidate set and its counting rule**; **what
would change it**; and **what a future wire value must be matched against** —
three ways, per area G's addendum, and now a fourth.

**What would change it.** Exactly one thing: **one authenticated `GET
/patient/monitor/data` response**, logged key-names-only, with the value pasted
verbatim and not paraphrased (`VALIDATION-RUNBOOK` Tier 1). Nothing else closes
it — no amount of client archaeology, and this pass is the demonstration.

**Match order for a future value** — the four ways, strongest first:

1. **The client's own comparison set** (6 strings: `BLE`, `BLE_X`, `SIMPLERA`,
   `SIMPLERA_X`, `GUARDIAN`, `NGP`) — because a value that matched none of these
   would fail the vendor's own routing.
2. **The model code** (87 codes: 78 `MMT-*` + 9 `SKU-*`; whole-file census 80
   `MMT-*` including the two sensor-branch codes) — the path that works under
   either reading of the Flex problem.
3. **The display name** (87 pairs) — because Medtronic spells the marketing name
   in a third shape (`SIMPLERA_SYSTEM` is the enum, `"Simplera™ system"` the
   value).
4. **The patient map's 16 family tokens** — the published axis, and the only set
   a vendor document names.

---

## 5. The audit: every surviving `deviceFamily` claim re-counted against §2.1

`AGENTS.md` §2.1: a source is the **person or organisation** that produced the
measurement, not the artefact count. Strength words are permitted only where the
independent count is ≥ 2.

### A. "Three independent clients agree on the two-field split" — **count 3, word kept, claim narrowed**

| Source | Author/org | Commit | Artefact |
|---|---|---|---|
| `nightscout/nightscout-connect` | Nightscout (org) | `4dde1ec` (2026-09-24) | `index.js:587`, `:179,194` |
| `NightscoutFoundation/xDrip` | NightscoutFoundation (org) | `366c97a8` (tag `2026.10.10`) | `message/MonitorData.java:5`, `message/RecentData.java:102` |
| `CarlosJPV/carelink-cumulus-bridge` | one individual | `0180b89` (2026-08-26) | `src/types/carelink.ts:29-34` |

(`findings-log/2026-10-11-third-party-client-sources/FINDINGS.md:41-45`, `:57-61`.)

Three distinct authors, three distinct artefacts in three distinct
repositories, none quoting another. **Independent count = 3 ≥ 2 → the word
"independently" is permitted** for the claim *as narrowed below*. Area S4 has
already established (`docs/05:305-337`) that the vendor's own client assigns
`n.deviceFamily = i.medicalDeviceFamily` — **one axis** — so what the three
clients corroborate is that **each of them declares two names in its own types**,
not that the wire carries two fields. `docs/05` is corrected accordingly.

### B. ⚠ `docs/05`'s "the vendor's bundles do not contain" — **FALSE, corrected**

`docs/05:251-253` read *"a two-field split **that the vendor's bundles do not
contain**"*. That clause is now false. The **patient** bundle's lazy chunk
`k-6746-c6795ff7e9ff468d-js.b` contains `medicalDeviceFamily` at byte **83,893**
among four sites, in a hash-pinned chunk
(`findings-log/2026-10-14-area-s4-lazy-chunk-control-flow/FINDINGS.md:343-351`).
The clinic bundle does not contain it — that half stands, and it is what
`docs/05:236-244` actually measured. Corrected in place with the original wording
kept.

### C. ⚠ `docs/05:300-303` — **DELETED. "Independent corroboration" whose source records zero.**

> The superseded wording: *"`deviceFamily` appears as an HTTP **call-site field
> name** in the lazy-chunk corpus — independent corroboration of the field
> *name*, not its *value*"* [source:
> `findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md`].

**The source disagrees with itself.** The same file's measure table records
`deviceFamily`-style tokens in "all 224 chunks" as **0**
(`CHUNK-CORPUS-FINDINGS.md:29`), while two paragraphs later it places
`deviceFamily` among the chunks' 89 call-site field names (`:68-69`, `:89-94`).
The only `deviceFamily` evidence that file actually attributes is to a **different
artefact** — the patient portal's 3.4 MB main bundle served at the domain root
(`:122-126`) — and it cites **no `file:line` and no digest** for it.

`AGENTS.md` §6 item 5 (*derived prose that contradicted its own source table*) and
item 2 (*a grep that hit without proving*) are both live here, and the chunk
bodies are **not committed** (`git ls-files findings-log/probe-2026-10-08/` = 24
files, all markdown), so the disagreement cannot be resolved offline. **The claim
is deleted, not softened** (§1). Its replacement cites what the artefacts do
carry: the matcher enum in the digest-pinned patient bundle, and area S4's four
`NGP` sites.

### D. Row 37's "every observed value … (`GUARDIAN`, `MINIMED`, `PARADIGM`)" — **two of three withdrawn, one re-labelled**

- `GUARDIAN` survives and is now sourceable twice: SOURCE-OBSERVED in the three
  third-party clients, **and** OBSERVED in the vendor's own digest-pinned bundle
  (the `docs/05` correction section on the two names being one axis, where
  `"GUARDIAN" === n.deviceFamily` is quoted inside the `parseJsonData`
  extract).
- `MINIMED` and `PARADIGM` are **withdrawn pending a `file:line`**. They exist in
  exactly two places in the repository — one uncited log line and the row that
  quotes it — so the row was citing its own source back at itself.
  ⚠ **The count in this bullet is FALSE — see `## Correction (2026-10-15)`, item
  C6.** Three files carry each token as a claimed value, not two, and a fourth
  carries `PARADIGM` as an era label. The *withdrawal* stands on all three
  value-carriers being uncited; it does not stand on their number. Preserved
  unedited under append-only.
- **The label changes.** The row read "*(OBSERVED, third-party source; INFERRED
  for the wire value)*". **OBSERVED is not available**: per `AGENTS.md` §2 it
  means seen in a live response, and no client read in this repository is that.
  The honest class is **SOURCE-OBSERVED** (corroboration, never proof of vendor
  behaviour, §2.1). Re-labelled.

### E. Area P's "matches the `medicalDeviceFamily` values in both casing and vocabulary family" — **cannot be sourced; not carried into `docs/`**

`findings-log/2026-10-13-area-p-static-schema/FINDINGS.md:147-151` compares the
enum against `GUARDIAN`, `MINIMED`, `PARADIGM` and says they match "in both
casing and vocabulary family". Measured, the two sets share **exactly one**
string (`GUARDIAN`): `BLE`, `BLE_X`, `SIMPLERA`, `SIMPLERA_X` are in no reported
value, and `MINIMED`/`PARADIGM` are in no enum. The claim is not restated in any
`docs/` page, so nothing there needs correcting — but it is recorded here because
a reader who trusts it would believe the enum and the reported values are the
same vocabulary, which is the disagreement this area exists to record.
`findings-log/` is append-only, so the correction lives here.

### F. Claims audited and left standing

| Claim | Location | Independent count | Verdict |
|---|---|---:|---|
| the five-token matcher enum exists in the vendor's bundle | `docs/00:258`, `docs/05:81-89` | 1 (this repo's own digest-pinned bundle; P's re-derivation and PATIENT-APP-VOCABULARY are the same organisation reading one artefact) | stands, no strength word |
| the 16 published family tokens | `docs/05:44-47`, `docs/00:249-251` | 1 (vendor config, PUBLISHED; H re-derived live) | stands |
| "routing `deviceFamily` and reported `medicalDeviceFamily` are two axes overlapping on `GUARDIAN`" | area S4's own correction table, `…s4…/FINDINGS.md:599` | — | already corrected there; `docs/05` inherits the correction |
| `docs/04:762`, `docs/00:346`, `docs/11:21` — token-gated statements | — | — | stand; they say the thing is unknown |

---

## 6. What this pass did **not** establish

- **The wire casing of any `deviceFamily` value.** Zero requests; the answer is
  unchanged and the reason is recorded.
- **That `deviceFamily` is a wire field on `/patient/monitor/data`.** Three
  third-party clients declare it; **no live response in this repository shows
  it**, and the vendor's own client treats the name as an internal assignment
  (area S4). "Is an API field" is a vendor-behaviour claim resting on
  corroboration alone, and is now labelled that way rather than as fact.
- **Whether the suffix in `BLE_X`/`SIMPLERA_X` means anything.** No committed
  artefact reads it — only declares it. Successor.
- **The read-side echo of any of these keys.** Successor; token-gated.

---

## 7. Reproducing this pass

```bash
python3 findings-log/2026-10-14-pool-r-devicefamily-casing/count-candidates.py
# or, through the harness, which also writes run.log and asserts 0 rows:
./findings-log/2026-10-14-pool-r-devicefamily-casing/probe.sh
```

Zero network access. If an anchor stops resolving, the script exits non-zero
rather than producing a number — a count that cannot fail is not evidence
(`AGENTS.md` §6 item 2).

No credential, session value, patient identifier or internal hostname appears in
any file this pass added, and none was read, handled or recorded at any point.

---

## Correction (2026-10-15)

Two defects found by the `carelink-verifier` round on PR #127 at `c267d65`, and
independently reproduced against the artefacts before being actioned. Neither
changes the verdict, the count, or a single figure this pass publishes — one
changes a machine artefact that contradicted them, and one moves a citation by 35
lines. Both original statements stay visible above, as `AGENTS.md` §3 requires.

### C1 — the committed `run.log` was stale, and published the number this pass exists to refute

**This was the blocking finding, and the mechanism is the one `AGENTS.md` §6 item
5 names: derived prose contradicting its own source table.**

`run.log` in this directory was the output of an **earlier** version of
`count-candidates.py` — the version before this pass applied the **R-2(d)**
exclusion of `S-CLIENT-DTO` — and it was committed without regeneration. It
therefore published:

| line in the stale `run.log` | what it said | what the current script says |
|---|---|---|
| `:13` | `S-CLIENT-DTO    4  …APP-EMULATION-RESEARCH.md:384-385` listed under **admitted** sources | `S-CLIENT-DTO` appears only under **DECLARED BUT NOT ADMITTED** |
| `:40` | `union size = 23` | `UNION SIZE (the published number) = 21` |
| `:41` | `sum of the three sources = 25` | `sum of the admitted sources = 27` |
| `:23`, `:26`, `:30`, `:32` | `CC`, `CGM`, `GUARDIAN`, `NGP` attributed to `S-CLIENT-DTO` as a member source | `CC` and `CGM` are **not members**; `GUARDIAN` and `NGP` come from `S-ENUM`/`S-CLIENT` |
| `:62` | "`CC` re-enters through `S-CLIENT-DTO`" | `CC` is not admitted at all |

So **the number this pass refutes (`23`) was sitting inside the ledger**, in the
same commit that published **21**, while §7 below pointed a reader at that file as
the harness output. `AGENTS.md` §2 requires that where sources disagree you give
both and never pick one silently; this was not a disagreement between sources, it
was a stale derived artefact asserting a second number without saying so.

**Fix: regenerated, not hand-edited.** At `805211e`, `run.log` became the output of
`probe.sh`, which wraps `count-candidates.py` as of that commit between its two marker
lines, and the committed file's body is byte-identical to a fresh run of that
script. The regeneration issues **no network request** — `probe.sh` has no
`curl`/`wget`/`nc` and no host list, and `count-candidates.py` imports only
`re` and `sys` — so the accounting is unchanged at **0 of a 0 cap** with
`results.jsonl` at **0** rows, and **no request row was added** for the
regeneration.

**What this says about the pass, not just the file.** The prose was right and the
machine artefact was wrong, which is the *reverse* of the usual failure mode and is
therefore worth naming: the counting rule did its job (the script refused to
default, and the stale output was recognisable only because the rule pins an exact
number to print). What it did **not** do was force the committed ledger to be
regenerated whenever the rule's implementation changed. That is a harness gap, and
it is recorded here rather than fixed, because `probe.sh` is this pass's own
artefact and retro-fitting a "the ledger must be newer than the script" check to it
after the fact would be the same class of quiet edit this correction is about. A
successor pass that touches the rule should regenerate the ledger as part of the
change; the cheapest durable form is a note in the harness header, which is where
the reader lands first.

### C2 — the attribution cite pointed at a range that does not contain the phrase

§2 above, and the sentence reproduced in `docs/05`, attributed the phrase
**"from xDrip's message classes"** to
`findings-log/probe-2026-10-08/APP-EMULATION-RESEARCH.md:384-385`. It does not
appear there. Measured on the committed file:

- **`:349`** is the heading that carries the phrase —
  `# Round 3 — the full \`RecentData\` payload schema (from xDrip's message classes)`
- **`:384`** is `### \`deviceFamily\` values — this is the wire vocabulary`
- **`:385`** is the token line — the four tokens, where `CC` includes Instinct.

So `:384-385` is exactly right for the **token list** and exactly wrong for the
**phrase**. That is `AGENTS.md` §6 item 6's shape — a citation pointing at
something other than what it is cited for — and it is the kind that survives
review precisely because the cited range *does* contain the tokens.

**The conclusion is unchanged, and the fix strengthens it.** The phrase sits in
the heading of the enclosing **section**, so the defect is broader than the pass
first described: the whole of Round 3 attributes itself to xDrip's message classes
and **no commit is named anywhere in it**. The exclusion of `S-CLIENT-DTO` under
**R-2(d)** therefore stands, `CGM` and `CC` remain unadmitted, and the union
remains **21, not 23**.

**Fix.** At `805211e`, `count-candidates.py` carried the two cites deliberately
apart — `:349` for the phrase, `:384-385` for the tokens — and printed both in the
`DECLARED BUT NOT ADMITTED` block, so the regenerated `run.log` states the
attribution at the line that holds it. The `docs/05` citations were corrected in
place (canonical docs supersede), and this section keeps the original wording
visible above.

---

## Correction (2026-10-15)

Two items from the second `carelink-verifier` round on PR #127, at `805211e`.
Neither changes the verdict, the union, or any figure this pass publishes. The
first is a miss on my own round-1 fix, recorded as such rather than smoothed
over; the second is a labelling defect one layer below the one that was blocking
in round 1. Prior wording stays visible throughout (`AGENTS.md` §3).

### C3 — the C2 cite correction reached 2 of 3 canonical sites

Round 1's C2 fixed the attribution cite in `docs/05` (two places) and in
`count-candidates.py`. **It missed `docs/11`'s Closed-table row for this very
area**, which still read:

> `GUARDIAN`/`NGP`/`CGM`/`CC` is recorded at `APP-EMULATION-RESEARCH.md:384-385`,
> which attributes it to "xDrip's message classes" with **no `file:line` and no
> named commit**

Measured on the committed artefact: `:384-385` contains **zero** occurrences of
"xDrip". `:349` is the section heading carrying the phrase; `:384` is the
`deviceFamily` sub-heading; `:385` is the token line. So the row cited a range
that does not contain the phrase it attributed to it — `AGENTS.md` §6 item 6 —
and it was the **canonical Closed-table row**, the one a reader is most likely
to reach for the verdict. That is the same defect class as C2, in the most
consequential location.

**Why it survived round 1:** C2 was fixed by editing the sites *I noticed while
writing*, and the Closed-table row was written in the same pass but read back
only for its numbers. A citation fix that is scoped by recall rather than by a
sweep is a citation fix that will miss one again.

**Fix, and the sweep that should have accompanied C2.** `docs/11`'s row now
separates the two cites the way `docs/05` does — **`:349`** for the heading that
carries the attribution, **`:384-385`** for the token list. Every `384-385`
occurrence in the tree was then enumerated and classified rather than assumed:

| site | what the range is cited for | verdict |
|---|---|---|
| `docs/05:303` | the committed line the vocabulary was re-derived to (the tokens) | correct |
| `docs/05:480` | where the tokens sit, with `:349` named alongside for the heading | correct |
| `count-candidates.py:73` | prints **both** cites apart in the NOT-ADMITTED block | correct |
| `run.log:49` | the same, as the script's output | correct |
| `docs/11:1712` | **the phrase** | **wrong — fixed** |
| this file, §2 candidate table | the four DTO tokens | correct |
| this file, §3 "The conditional is the finding" | the phrase | wrong in the original; C2 above names and corrects it, and append-only forbids editing it in place |
| this file, **C1**'s stale-ledger table and **C2**'s ground-truth and **Fix** paragraphs | C1/C2 **describing** the defect | correct |
| `docs/09:195` | **README line numbers** in the "A count the gate's regex cannot see" trap row — not this artefact at all | unrelated, verified, untouched |

Two of those rows are this file's own append-only text, so they keep the defect
visible with the correction attached rather than being rewritten. That is the
`AGENTS.md` §3 rule doing its job: a reader of `:157` can see what was believed,
and a reader of C2 can see why it changed.

### C4 — `6 shared string(s)` counted occurrences, not strings

`run.log`, `count-candidates.py` and §3 above all printed
`6 shared string(s)`, derived as `total − len(u)` = 27 − 21 = **6**. Those are
**6 duplicate *occurrences*** beyond first mention. The number of **distinct**
strings appearing in two or more sources is **5**: `BLE`, `BLE_X`, `GUARDIAN`,
`SIMPLERA`, `SIMPLERA_X`. The two differ because `SIMPLERA` is in **all three**
admitted sources — 2 occurrences, 1 string.

Nothing contradicted anything: the adjacent `OVERLAPS` block prints the exact
pairwise intersections, and `docs/05` phrased the difference as "the 6-string
difference". But a parenthesised label reading `shared string(s)` invites 6 to
be read as a string count, which is **the same defect class as C2 and C3, one
layer down** — a number whose label does not say what the number counts. For a
pass whose entire subject is a counting rule, that is not a cosmetic slip.

**Fix.** The two quantities are now computed as two quantities and printed as
two, with the reason they differ:

```
UNION SIZE (the published number) = 21
sum of the admitted sources      = 27  (NOT the answer)
  difference = 27 - 21 = 6 shared OCCURRENCE(s) — appearances beyond first mention, NOT distinct strings
  distinct strings in >=2 sources = 5: BLE, BLE_X, GUARDIAN, SIMPLERA, SIMPLERA_X
```

`run.log` was **regenerated through `probe.sh`**, not hand-edited — the round-1
lesson again: as of `6fe6ffb` nothing compared `run.log` against this prose, which
is exactly why CI could not catch either defect. The regeneration issues **no network
request** (`probe.sh` has no `curl`/`wget`/`nc` and no host list;
`count-candidates.py` imports only `re` and `sys`), the accounting is unchanged
at **0 of a 0 cap** with `results.jsonl` at **0** rows, and **no request row was
added**.

**Two places in §3 above are superseded**, and both are left in place because this
directory is append-only:

1. the **quoted output block** (the line reading
   `sum of the admitted sources = 27 (NOT the answer; 6 shared strings)`) — now
   stale output, reproduced above from the pre-fix transcript; and
2. the **prose sentence** immediately below it, which reads *"six shared
   strings, which is exactly the arithmetic that makes 44 become 93"*. That
   sentence carries the **same ambiguous unit** as the label did, in prose rather
   than in a parenthesised note, which is why it is named here separately: it is
   **6 duplicate occurrences across 5 distinct strings**, and the arithmetic
   point it makes stands either way.

The `run.log` regenerated in this directory at `6fe6ffb` was the authoritative copy
of the script's output at that commit. Both passages are dated by the commit that
produced them, which
is the point of keeping them.

**What actually fixed C4.** Not the wording — the labelling discipline. A number
whose unit is not printed next to it is an invitation to misread it, and the unit
here was the whole subject of the pass.
### C5 — a whitespace-only fix to the C1 join, disclosed because it touches an already-committed line

Appending C1 in round 1 introduced the same join defect this round found again:
this file has **no trailing newline at the end of its original text**, so the
appended region landed with `---` directly after the sentence *"…at any point."*
In CommonMark a `---` immediately beneath a paragraph line is a **setext heading
underline**, not a thematic break — so that separator rendered as a second-level
heading carrying the sentence's text.

**Fixed by inserting one blank line.** No wording was changed, added or removed,
and no claim was touched — this is the one deviation from strict append-only in
this correction, and it is disclosed rather than done quietly, because the rule
exists to stop wording being erased and a blank line erases nothing. The gate's
`check_append_only` still sees the file as `M` with a dated Correction heading,
which it has (two of them).

**The durable lesson, which is why this is recorded rather than just patched.**
Two passes, two occurrences, one cause: **this file does not end with a newline,
so every append to it must supply one.** A successor touching this directory
should start with `printf '\n' >> FINDINGS.md` rather than discovering it again. ⚠ **The present-tense half of this sentence is WITHDRAWN — see
`## Correction (2026-10-15)`, item C13.** It was true when written and is false now:
this file's last byte was `0a` **at `cc513f9`** (measure it; do not read it off this sentence). It is kept verbatim, as C8's parallel sentences are, because
deleting it would destroy a retraction record. **Measure, never assert** — see C10.

---

## Correction (2026-10-15)

**Third round.** Items from the third `carelink-verifier` round on PR #127 at
`6fe6ffb`. Two blocking, two minor. **Two defects survived three rounds because
the repairs were scoped by recall rather than by a sweep** — which is the lesson
C3 wrote down and then did not apply to itself. This round swept, and the sweep
found more than the flagged lines.

**What was changed in place, and what was appended, and why.** The two
*mechanical* repairs — a wrong line-offset and a duplicated lead-in — were made
**in place**, because neither erases wording, a claim or a retraction, and
`AGENTS.md` §3 permits an edit when a dated `## Correction` section accompanies
it. The two *claim* corrections are **appended**, with the superseded wording
quoted above and still visible, because those are the ones the retraction history
is about. Every one of the four is recorded below.

### C6 — BLOCKING: the count published as `MINIMED`/`PARADIGM`'s evidence was false

§3 and §5 D both published a frequency for these two tokens as the ground for
withdrawing them. The wording, now superseded and still visible above:

> *"**These two strings appear in exactly two places in the whole repository: that
> line, and `docs/10` row 37 echoing it.**"*
> *"They exist in exactly two places in the repository — one uncited log line and
> the row that quotes it"*

**It is three files for `MINIMED` and four for `PARADIGM`.** Method — whole-word
match at the base commit of this branch's base, so the figure does not drift with
my own edits:

```
git grep -w -n MINIMED  7d915b8 -- .
  docs/10-open-questions.md:37
  findings-log/2026-10-11-third-party-client-sources/FINDINGS.md:69
  findings-log/2026-10-13-area-p-static-schema/FINDINGS.md:149
git grep -w -n PARADIGM 7d915b8 -- .
  docs/10-open-questions.md:37
  findings-log/2026-10-11-third-party-client-sources/FINDINGS.md:69
  findings-log/2026-10-13-area-p-static-schema/FINDINGS.md:149
  findings-log/medtronic-carelink-2026-07-21/03-data-model-and-gaps.md:96
```

The fourth `PARADIGM` is **not** a value claim: it reads *"the mddub sample is
PARADIGM-era"* — an era label. So the honest figure is **three carriers asserting
each token as a `medicalDeviceFamily` value, plus one era label**.

**This document contradicted itself 110 lines below, and that is the sharper
defect.** §5 E already cited `2026-10-13-area-p-static-schema/FINDINGS.md:147-151`
as a site comparing the enum against `GUARDIAN`, `MINIMED`, `PARADIGM` — the third
carrier the §3 count said did not exist. A document that refutes its own count is
worse than a document that makes a bad count, because a reader who checks one
sentence concludes the other is sound.

**The withdrawal conclusion survives; its stated evidence does not.** All three
value-carriers are uncited — **none supplies a `file:line` at a named commit** — so
R-3 still excludes both and the union is still **21**. What was wrong was the
*count*, not the verdict. `AGENTS.md` §1: a sentence whose evidence cannot be
pointed at does not get softened, and here it could be pointed at and was false.

**The third carrier is worse than the two named, not a rescue.**
`…area-p-static-schema/FINDINGS.md:149` **self-labels `Class: OBSERVED`** on the
strength of those same three strings, with no `file:line` and no named commit —
which is precisely the non-promotion failure `AGENTS.md` §2 names. A carrier that
labels itself OBSERVED is a *worse* carrier than one that labels itself nothing,
because the label invites exactly the promotion §2 forbids.

**The sweep, and what it found beyond the flagged lines.** `git grep` for the
false claim's wording across the tree found it in **four places beyond the two
here** — `docs/10` row 37, `docs/11`'s Closed-table row, `docs/05`'s named-
withdrawals block, and **this area's own PR description**. All four are corrected
(`docs/` supersedes in place; the PR body is corrected). The two earlier PR
comments were checked and do **not** carry it. **Every other frequency claim in
this document was re-derived the same way and holds:** 24 files under
`findings-log/probe-2026-10-08/` at base and at head, 0 of them non-markdown;
the four `NGP` sites; the three-client commit table; the 78+9 code counts and the
76+2+9 name-pair counts, all three of which the re-derivation script re-extracts
from the cited lines rather than restating.

### C7 — BLOCKING: five line pointers in C3's own sweep table had drifted

Every pointer in C3's table was correct at `805211e`. **This pass's own edits
displaced five of them** — the C4 label change inserted two lines above
the `run.log` cite it had displaced, the C5 blank-line fix one line above the
three `FINDINGS.md` cites, and the unpinned-status block fourteen lines above the
`docs/05` cite. The offsets were
now `480`, `49`, `358`, `404` and `417`. Each was confirmed by **reading the
target line**, not by adjusting the number until it looked right.

**This is §6 mode 6 — a citation pointing at the wrong line — inside the section
whose stated purpose is that a recall-scoped citation fix will miss one again.**
The enum in C3 was complete and every verdict in it was accurate; only the
pointers rotted. Corrected in place: pointer offsets carry no claim, so nothing
was erased.

**The sweep.** Every `path:line` cite in this directory was extracted
mechanically and resolved against the head tree, including the short forms a
regex on file extensions misses (`docs/05:480`, `docs/11:1712`, `docs/09:195`).
**23 cites, 0 failures**, and the six short-form pointers were read by hand.

**The structural lesson, and this pass proved it in the same round.** A
**self-referential** line cite inside an append-only file cannot stay valid: every
correction appends lines, and anything that shifts text above the cite breaks it.
C3's own edits broke C3's pointers; then, **after fixing them to verified offsets,
this pass inserted two inline correction markers further up the file and broke the
corrected pointers a second time.** A second repair to the same lines, from the
same cause, inside the round that diagnosed it.

**So the pointers were not merely re-nudged — the three self-referential cells were
converted to section-heading anchors** (§2 candidate table, §3 "The conditional is
the finding", C1's stale-ledger table, C2's ground-truth and Fix paragraphs).
Headings are stable under append, so from `a1c4dd6` the table was append-proof
rather than correct-until-next-time. The six cites that point at **other** files keep
real line
numbers and were re-verified against the head tree after every edit in this round.

**The generalisable form:** a line cite into a file you are also editing is a
claim with a half-life, and the half-life is shorter than the review cycle. Reach
for an anchor that the edit cannot move.

### C8 — MINOR: C5's trailing-newline claim was written in the present tense and is false at the commit that states it

C5's durable lesson read: *"**this file does not end with a newline, so every
append to it must supply one.** A successor touching this directory should start
with `printf '\n' >> FINDINGS.md`."*

At the commit making that statement the file **does** end with a newline. The
**past-tense diagnosis is accurate**: `git show c267d65:…/FINDINGS.md | tail -c 1`
returns `2e` (`.`), while the file's last byte **was** `0a` at `6fe6ffb`. ⚠ **Both present-tense clauses of this sentence — originally *"the current file's last byte is `0a`"* and *"this file no longer asserts its own trailing byte anywhere"* — are WITHDRAWN.** The first at `b06d7d6` (see item C10): it was true at `6fe6ffb` and was falsified by a later edit that removed the newline again. The second at `b1386e6` (see **item C18**): it was already false when written, because at `cc513f9` the file asserted its own byte at two other places. **Both clauses are kept verbatim in this record per `AGENTS.md` §3 and both are restated above in past tense, anchored to the commit each was true at.** What was true at `b1386e6` is the narrower, bounded claim: **no UNMARKED present-tense byte claim of the swept class.** The original text
of this document never had a trailing newline; C5's own blank-line repair added
one. So the advice, followed literally now, would inject a spurious blank line.

**Restated in the conditional form that is true at every commit:**

> This document's original text did not end with a newline, so the first appends
> into it had to supply one — and each of those appends, being `cat >>` against a
> file that now *does* end with one, should supply **nothing**. ⚠ **This clause and the "other direction" claim below are WITHDRAWN — see item C10.** The file did not reliably end with one; the rule is now "measure, never assert". **Check before
> appending:** `tail -c 1 FINDINGS.md | xxd`. If the last byte is `2e`, prepend a
> newline; if it is `0a`, do not. Appending unconditionally has now been wrong
> once, in the other direction, which is the reason to state the rule as a check
> rather than as an instruction.

**The sentence being corrected is the last line of the section immediately above this one.** A correction that supersedes the line directly above it is the clearest possible demonstration that the original was wrong at the commit that stated it.

The reason the restatement matters beyond tidiness: the original advice was
falsifiable by the commit that made it, and a reader who ran it would have damaged
the file.

### C9 — MINOR: an orphaned duplicate lead-in, removed

The second-round section carried **two** lead-ins to one section — a bolded
**"Second round."** paragraph above a blank line and a near-duplicate paragraph
below it. The orphan is removed; the surviving lead-in is the one that carries
the substance. Three lines, no claim affected.

### What this round did not change

The verdict (negative — the casing stays unobserved), the union (**21**), the
counting rule, the ledger (`results.jsonl` **0** rows, **`0 of a 0 cap`**), and
the exclusions. **All three corrections from rounds 1 and 2 were re-verified
rather than assumed**, and none of them moved.



---

## Correction (2026-10-15)

**Fourth round.** Items from the fourth `carelink-verifier` round on PR #127 at
`a1c4dd6`. Two blocking, one minor. **Every one of them is the same defect C8
exists to describe: a sentence about this file that the edit making it falsifies.**

### C10 — BLOCKING: C8 asserted a trailing byte that the commit carrying it did not have

C8's text read *"the current file's last byte is `0a`"*, together with two
sentences resting on it — *"a file that now **does** end with one, should supply
nothing"* and *"appending unconditionally has now been wrong once, in the other
direction"*.

> **Verbatim, withdrawn:** *"The byte was `2e`, and still is."* ⚠ **That sentence
> asserted a present-tense state and is WITHDRAWN at `b1386e6` — see
> `## Correction (2026-10-15)`, item C13.** It is quoted rather than restated
> because `AGENTS.md` §3 requires the superseded wording to stay visible; it is
> **not** a claim this document makes. It was accurate when written: the three
> routes below agree, and every one of them reads `2e` **at `a1c4dd6`**, the
> commit those routes were
run against. The file's last byte was `0a` **at `cc513f9`** (measured; do not read it off this sentence). The measurement stands; its unanchored
present tense does not, and the two are kept apart here rather than merged.

```
tail -c 1 FINDINGS.md | xxd                             → 2e
python3 -c "…read().endswith(b'\n')"                    → False
git cat-file -p a1c4dd6:…/FINDINGS.md | tail -c 20|xxd → …76656452e   ("…ved.")
```

Measured across this branch's own history:

| commit | last byte |
|---|---|
| `c267d65` | `2e` |
| `805211e` | `2e` |
| `6fe6ffb` | **`0a`** |
| `a1c4dd6` | **`2e`** |

So the **past-tense half of C8 is accurate** — the original text of this document
never had a trailing newline, and that is what broke the round-1 append. But
round 2 restored one and **round 3 removed it again**, silently, by rewriting the
file through a text-mode write while editing other parts of it. **This commit
therefore removed the very byte it claimed to have measured.** The commit message
for `a1c4dd6` repeated the error, so message and file agreed with each other and
both were wrong — which is the worst version of this failure, because agreement
between two artefacts is exactly what a reader checks before believing either.

**Restated so that it cannot be falsified the same way again.** The current
trailing byte is **deliberately not asserted here**. A sentence in this file
stating what this file's own last byte *is* is falsified by any later edit that
rewrites the file — which is precisely what happened, twice. The durable form is
a **measurement with a command attached**, not a state:

> **Measure it; never assert it.**
> `tail -c 1 findings-log/2026-10-14-pool-r-devicefamily-casing/FINDINGS.md | xxd`
> — if the last byte is `2e`, prepend a newline before appending; if it is `0a`,
> append nothing. **Run it against the file as it will be committed**, not
> against a working copy inspected before the append, because the append is the
> thing that changes the answer.

The direction claim also changes. Appending was wrong once **in each** direction —
once for omitting a needed newline, once for injecting an unneeded one — not
"once, in the other direction". That sentence was wrong at the commit that wrote
it, for the same reason.

**What this cost, stated plainly.** Four verifier rounds, and the recurring theme
is that **a document describing itself is the hardest kind to verify**, because
every edit to the description is also an edit to the thing described. Three of
the four rounds' blocking findings are in this file and two of them are about this
file's own bytes and line numbers. The generalisable rule is already written at
the end of this correction set and is worth restating as the pass's own lesson:
**prefer an anchor the edit cannot move** — a command, a heading, a hash of a
named commit — over a line number, an offset, or a byte observed in the artefact
being described.

### C11 — MINOR: one sweep, two totals, and an enumeration that summed to 11

**Two different totals were published for the same sweep in the same round** — this
log said *"23 cites, 0 failures"* while that round's commit message said *"29
cites resolved, 0 failures"*. Neither carried a counting rule, which is `AGENTS.md`
§6 item 7 exactly: a count with no rule is not a number, it is a vibe.

**One number now, with the rule in a script**, as `count-cites.py` in this
directory. It states its rule before it counts (R-C1 subject: `*.md` in this
directory only · R-C2 unit: one `path:line` token inside backticks, a path with no
line number is a *source pointer* and is never added to the cite total · R-C3
self-referential cites are excluded, because they were converted to heading
anchors precisely because a line cite into a file this pass keeps editing has a
half-life shorter than the review cycle · R-C4 the sweep table's short forms are
counted too, because a regex on file extensions misses them · R-C5 distinct
resolved targets, counted once · R-C6 every cite must resolve, exist, and be
**non-blank**).

> **CITE COUNT = 28. Failures = 0.** ⚠ **SUPERSEDED — see `## Correction (2026-10-15)`, item C17.** This figure was correct when measured and was **devalued by the commit that recorded it**, because the rule counted the correction sections that quote cites. Under the amended rule **R-C1b** the count is **22**. The number is kept because deleting it would remove the record of the mistake; the rule, not the restatement, is the fix. Two further figures are reported beside it
> and are **not** added to it — the path-only source-pointer count (R-C2) and the
> self-referential count (R-C3) — and **both are left to the script to print
> rather than restated here**, because a figure this file prints about this
> file's own contents is falsified by the next edit, which is the entire
> subject of C10. Run the script for their current values.

**The rule found two more defects the earlier sweeps missed**, which is the
argument for having written it down rather than eyeballing a list:

1. **The `docs/05` cite at line 315 was stale.** The `"GUARDIAN" === n.deviceFamily` literal it
   cited had moved to line 373 under round 3's edits to that page. It is now
   a **heading anchor** — the `docs/05` correction section on the two names being
   one axis — so it cannot drift again. R-C6's non-blank clause is what caught it:
   the line **existed**, so an existence-only check passed it.
2. **A historical mention was masquerading as a live cite.** C7's *"the C4 label
   change inserted two lines above the `run.log` cite"* describes where a cite **used
   to be**, so it is history, not a citation. Restated as prose without the
   offset, so it is no longer counted as a live cite.

**The enumeration now sums correctly.** The four buckets of in-place deletions in
this file were published as `3 + 1 + 3 + 3 = 11` against an actual **10** —
the `FINDINGS.md:357/:404/:417` cell had been counted **twice**, once as a
superseded pointer cell and again as a converted self-cite. The buckets are:

| bucket | n |
|---|---:|
| orphan lead-in removed (3 text lines + its blank separator) | 4 |
| superseded pointer cells (the `docs/05` and `run.log` cites, and the `FINDINGS.md` cell) | 3 |
| self-cite cells converted to heading anchors (`FINDINGS.md:65`, `FINDINGS.md:157`) | 2 |
| `\| MINIMED \|` table row, sentence kept verbatim with a marker appended | 1 |
| **total** | **10** |

The arithmetic was wrong, not the disclosure: every one of the ten was enumerated
individually in that correction and none erased a claim, a retraction or a
sentence.

### C12 — the PR's append-only attestation did not match what the commit did

This round's PR description still carried *"one new dated directory, nothing
deleted or rewritten in place; `check_append_only` confirms"*. Relative to `main`
that is true — `FINDINGS.md` is a wholly new file, and
`research-checks.py`'s rule is the narrower *additions + dated corrections*, which
is satisfied. But the sentence is the PR's append-only attestation and it did not
mention the ten in-place line deletions this pass made, which is the one thing a
reviewer most needs stated.

**Reworded to state what happened**: ten in-place line deletions in
`FINDINGS.md`, all enumerated in C11 with a bucket that now sums to 10, none
erasing a claim, a retraction or a sentence, and three dated
`## Correction (2026-10-15)` sections accompanying them. The substance was never
in question; the disclosure was.

### What this round did not change

The verdict (negative — the casing stays unobserved), the union (**21**), the sum
(**27**), the counting rule and its non-zero exit on anchor drift, the ledger
(`results.jsonl` **0** rows against **`0 of a 0 cap`**), and the four corrections
from rounds 1–3, all re-verified rather than assumed. The six line cites into
`docs/` and `run.log` were deliberately **not** converted to anchors: that would
mean more in-place rewrites of committed lines immediately before merge, trading a
real `AGENTS.md` §3 cost for a risk window that closes at merge.


---

## Correction (2026-10-15)

**Fifth round.** Items from the fifth `carelink-verifier` round on PR #127 at
`b06d7d6`. Four findings, and **three of the four were one defect class that had
already been named twice in this file and then survived anyway.**

### C13 — the self-state claim survived twice, because the sweep was an enumeration instead of a construction

C10 withdrew this file's present-tense trailing-byte claim. A claim of that shape
can only be hunted **by construction**: *every sentence that makes a present-tense
state claim about this artefact — its trailing byte, its line count, its file
list, what it contains.* Enumerating the sentences I happened to remember is what
let two survivors through, and one of them was the sentence the whole withdrawal
was written about.

The class, enumerated from the construction rather than from recall — every match
of *this file does/is/has/now/contains*, *the current file*, *and still is*,
*no longer asserts*, *is now the*:

| line | the claim | verdict at `b06d7d6` |
|---|---|---|
| `run.log is now the output of probe.sh` | true but unanchored to a commit | **de-anchored** — "is the output of" is a statement about a regeneration, dated by the commit that did it |
| *"this file has **no trailing newline at the end of its original text**"* | past-tense and scoped to the **original** text | **true as scoped** — left alone |
| *"this file does not end with a newline, so every append to it must supply one"* | present tense, unscoped | **FALSE and unmarked** — now carries a withdrawal marker pointing here |
| C8's quotation of that sentence | framed as *"C5's durable lesson **read**"* | correctly historical — left alone |
| C8's state claim | already marked WITHDRAWN at C10 | left alone |
| *"Appending unconditionally **has now been** wrong"* | past perfect about the past | **true** — left alone |
| C10's quotations of C8 | framed as *"C8's text **read**"* | correctly historical — left alone |
| *"The byte was `2e`, **and still is**"* | present tense, unanchored | **FALSE and unmarked** — now carries a withdrawal marker pointing here |
| *"so this file **no longer asserts its own trailing byte anywhere**"* (inside C8) | a **universal** claim, and a search term of this very sweep | **FALSE and unmarked — and omitted from the FIRST version of this table.** Marked at `b1386e6`; see **C18** |
| *"this file's last byte is `0a`"* — **inside C5's marker**, not this section's | present tense, unanchored to a commit | **true but unanchored — same shape as the `run.log` row above; converted to past tense and anchored at `cc513f9` in round 7** |
| *"The file's last byte is now `0a`"* — **inside C10's marker**, not this section's | present tense, unanchored to a commit | **true but unanchored — converted to past tense and anchored at `cc513f9` in round 7** |

**The sweep did not see its own output.** In the FIRST version of the table above,
`no longer asserts` appeared as a search term of this sweep, and the table it
produced omitted the file's only
occurrence of that term. Two of the three rows this correction adds were written
*by this sweep* and then escaped it for the same reason the first two did: they
were produced after the enumeration ran. **A sweep's result table is itself an
output of the sweep and must be checked against the sweep's own terms** — that is
now a step in the construction, not an afterthought.

Both survivors are **kept verbatim with the marker appended**, exactly as the two
C8 sentences are, because deleting a retraction record is the one thing
`AGENTS.md` §3 exists to prevent. The markers say what is true now and point here;
they do not erase what was said then.

**The second survivor is the instructive one.** *"The byte was `2e`, and still
is"* was **correct when written** — the three routes printed beneath it do agree,
and every one of them reads `2e` **at `a1c4dd6`**, the commit they were run
against. The failure was never the measurement; it was the unanchored *"and still
is"*, which converts a dated observation into an open-ended claim about an
artefact that keeps being edited. **A measurement is not a property.** Stating
*what was measured, against which commit* survives every later edit; stating
*what is true* does not.

> **Verbatim, withdrawn at `6b493e7`:** *"**This file no longer carries an unmarked
> present-tense self-state claim.**"* ⚠ **That sentence asserted the class was empty,
> and was itself a member of it** — present tense, unanchored, unmarked, sitting
> inside the section whose purpose was to end the class. It is quoted, not
> restated, because `AGENTS.md` §3 requires the superseded wording to stay visible.
> **A document must not claim its own class is empty; it must simply not contain
> the class**, and let a sweep's output show that. The sweep run at `6b493e7`
> returned the hits listed in C19's table, each adjudicated there. What is
true at any commit is measured, not asserted — and the byte is measured with

```
tail -c 1 findings-log/2026-10-14-pool-r-devicefamily-casing/FINDINGS.md | xxd
```

run against the file **as it will be committed**, which is the only point at which
the answer is the answer.

### C14 — REPRODUCIBILITY: none of the three scripts ran as its own docstring said

`AGENTS.md` §10 requires that a stranger can *"re-run your probe from what you
wrote down"*, and each script's docstring said to run it by bare filename. Run
from its own directory — which is what that instruction means — **all three
failed**:

```
count-cites.py     → 33 cite(s) failed to resolve        (exit 1)
probe.sh           → exit 1, ANCHOR MISS on S-MAP
count-candidates.py→ exit 1, ANCHOR MISS on S-MAP
```

**`probe.sh` also destroyed the ledger.** It built `run.log` with a redirect, so
the failing child left an **8-line** `run.log` holding an error message where the
real 68-line transcript had been — a half-written ledger is indistinguishable
from a short run, which is the exact failure C1 was written about. `run.log` was
restored from the commit and regenerated.

Two root causes, one per language:

- `count-candidates.py` opened its anchors with bare repo-relative paths, so they
  resolved against the working directory.
- `count-cites.py`'s short-form resolver used `os.path.join(os.getcwd(), target)`
  with no fallback, while its `resolve()` — a few lines above — already tried two
  bases. One function knew better and the other did not.

**Fix.** All three now anchor on their **own location**: each Python script walks
up from `__file__` to the directory containing `findings-log/` and resolves every
path against that, and `probe.sh` derives `DIR` from `BASH_SOURCE` (already
correct) and now builds `run.log` **into a temporary file, moving it into place
only on success** — a failing child can no longer truncate the ledger. Each
docstring states that the script is safe from **any** working directory.

**Proved from three directories**, all three scripts, all identical:

| cwd | `count-cites.py` | `probe.sh` | `count-candidates.py` |
|---|---|---|---|
| repository root | exit 0 · 28 cites · 0 failures | exit 0 | exit 0 · 21 / 27 |
| its own directory | exit 0 · 28 cites · 0 failures | exit 0 | exit 0 · 21 / 27 |
| clean `git archive` export, `.git` absent | exit 0 · 28 cites · 0 failures | exit 0 | exit 0 · 21 / 27 |

### C15 — the arbiter's own documentation contradicted the value beside it

`.github/ISSUE_TEMPLATE/config.yml` shipped `about: 4 open areas` directly beneath
a comment reading *"5, computed, not inherited… the remaining open letters are F R
S K L."* — five, enumerating five letters, including **R**, which this branch
closes. The diff was one line; the comment was three lines that no check reads.

`research-checks.py` passes because it compares the **`about:` value** against
`docs/11` and never reads the comment — so the comment had been free to rot
silently, and it rotted. It matters beyond this PR because the comment is the
arbiter's own description of the arbiter's input, and it carries across every
merge in the queue.

**Rewritten to what this branch actually ships** — `4`, letters **F S K L**,
with the reason the comment and the value are one claim recorded next to it. The
ground truth was re-derived from `docs/11` rather than carried over: four
`^### [A-Z]. ` headings, `F S K L`.

### C16 — one PR-body cite did not resolve; the sweep found six

The flagged cite carried no `findings-log/` prefix while its two siblings in the
same clause did. Sweeping **every** cite in the PR body against the **commit
path** — `git cat-file -e <rev>:<path>`, not `find -name`, which would have
"confirmed" a path that does not exist at that revision — found **six** failures,
not one:

| cite | defect |
|---|---|
| `medtronic-carelink-2026-07-21/03-data-model-and-gaps.md:96` | missing `findings-log/` prefix — **the flagged one** |
| `2026-10-11-third-party-client-sources/FINDINGS.md:69` | missing `findings-log/` prefix |
| `2026-10-13-area-p-static-schema/FINDINGS.md:149` | missing `findings-log/` prefix |
| `…/PATIENT-APP-VOCABULARY.md:18-19` | ellipsis shorthand — not a resolvable path |
| `…/family-map-verbatim.txt:1-16` | ellipsis shorthand |
| `…area-s4-lazy-chunk-control-flow/FINDINGS.md:353-354` | ellipsis shorthand |

All six repaired; the body now resolves **10 of 10** against the commit path. The
same sweep over the three `docs/` pages this branch touched found **zero** misses
in this branch's diff and **three** pre-existing at base (`DRIFT-AND-NEW`,
`JS-API-SURFACE` twice), which are recorded and **not** fixed here — importing
another pass's correction into this diff is the same mistake as touching
`docs/05`'s `OBSERVED` label, and both belong to whoever owns those pages.

**One of this branch's own `docs/11` cites** — a bare
`APP-EMULATION-RESEARCH.md:384-385` — was caught by the same sweep and given its
full `findings-log/probe-2026-10-08/` prefix.

### What this round did not change

The verdict (negative — the casing stays unobserved), the union (**21**), the sum
(**27**), the counting rules in both scripts and their non-zero exits, the
ledger's *content* (`results.jsonl` **0** rows against **`0 of a 0 cap`**), and
rounds 1–4's fixes, all re-verified rather than assumed. The two C8 sentences
and the two C13 sentences are annotated, not deleted, for the reason given above.

---

## Correction (2026-10-15)

**Sixth round.** Items from the sixth `carelink-verifier` round on PR #127 at
`cc513f9`. Two blocking findings, and the verifier's summary of them is the right
one: **the same two defects round 5 raised, reduced but not closed.** Both are
recorded below with the fixes; the second is the one worth reading twice.

### C17 — BLOCKING: the published cite count was the PREVIOUS COMMIT's number

`count-cites.py` printed **30** against a published **28**, at `cc513f9`, in every
medium including a clean export of the commit. The history is not a rounding
drift — it is a lag:

| revision | script said | file published |
|---|---:|---|
| `c267d65` | 23 | — |
| `6fe6ffb` | 29 | — |
| `a1c4dd6` | 31 | "23 cites" |
| `b06d7d6` | 28 | "23 cites" |
| `cc513f9` | **30** | **"28"** |

**I was publishing the previous commit's number.** The figure C12 introduced was
correct when written and devalued by the very commit that introduced it — which is
precisely the claim C12 existed to establish.

**The cause is structural, and it is not a bug in the arithmetic.** The script
scans files that include `FINDINGS.md`, and `FINDINGS.md` is the file that
*records the count* **and** contains correction prose that *quotes cites*. So
appending a correction moves the count: **a self-referential count is a fixed
point that recording the correction moves.** No amount of care in re-deriving it
can fix that; the measurement and the record are the same file.

**Fix: amend the RULE, do not restate the NUMBER.** Restating publishes a correct
figure that the next correction devalues identically — which is what round 5
watched happen three times. `count-cites.py` gains **R-C1b**:

> **Correction sections are excluded from the COUNT, never from the RECORD.** The
> subject text is each file up to its first `## Correction (YYYY-MM-DD)` heading.
>
> **Why:** a correction section *quotes the subjects it corrects*, because
> `AGENTS.md` §3 requires superseded wording to stay visible. Counting those
> quotations makes the number a fixed point that recording the correction moves.
>
> **The exclusion is from the COUNT, never from the RECORD.** Hiding quoted wording
> to stabilise a number would be `AGENTS.md` §1's deletion with the sign reversed.
> The wording stays on disk, stays greppable, and stays part of the record; it
> simply is not an input to this one measurement.

**Re-derived under the amended rule: `CITE COUNT = 22`, failures 0.** Every other
figure this pass publishes — the union, the sum, the overlaps, the exclusion list —
comes from `run.log`, which no correction quotes, so none of them move.

**Stability proved, not asserted.** In a scratch copy under a temporary directory,
never the worktree:

| rule | pre-decoy | after appending a correction quoting **7 novel cites** | verdict |
|---|---:|---:|---|
| **amended (R-C1b)** | 22 | **22** | **stable** |
| pre-amendment (same script, split removed) | 30 | **37** | **moved by 7 — the defect** |

The decoy was a `## Correction (2026-10-15)` section quoting seven `file:line`
literals not otherwise cited, so it could not be absorbed by R-C5's
deduplication. Removing the decoy returned the figure to its baseline, and the
real append recorded here moves it **0**. *A first attempt at this proof used
seven cite literals that were already in the count, and so moved nothing under
either rule — it proved nothing. The decoy has to be dense with **new** literals
or the stability it appears to demonstrate is an artefact of deduplication.*

### C18 — BLOCKING: the universal claim survived, and the sweep never saw its own output

Four defects, one cause.

**1. The universal claim.** C8 contained: *"so this file no longer asserts its own
trailing byte anywhere"* — unscoped, unmarked, and **false at `cc513f9`**, where the
file still asserted its own byte at two other places. The withdrawal marker that
existed on that sentence at `cc513f9` covered only the earlier clause *"the current
file's last byte is `0a`"* and **did not reach this tail**. **Marked**, not deleted:
the record is kept per `AGENTS.md` §3 and the marker states the narrower claim that
was true at `b1386e6` — **no UNMARKED present-tense byte claim of the swept
class** — which is far smaller than the claim withdrawn.

**2. Two self-introduced claims — mis-attributed to C13 in the first version of
this paragraph.** They live in **C5's** marker (*"this file's last byte is `0a`"*)
and **C10's** marker (*"The file's last byte is now `0a`"*), not in C13's. ⚠
**Corrected 2026-10-15: this paragraph originally attributed the present-tense
state to `b1386e6`, which is false.** Measured across the branch's own history: at
`cc513f9` — the commit *before* that one — `:560` read *"this file's last byte is
`0a`"* and `:745` read *"The file's last byte is now `0a`"*, both in the present
tense and both unanchored. At `b1386e6` both had **already** been rewritten into the
past tense anchored to `cc513f9`, because `b1386e6` **is** the commit that rewrote
them. The original sentence also contradicted its own next clause, which cannot be
both present-tense at `b1386e6` and rewritten there. **The mechanism was a
conversion that replaced an accurate phrase with a wrong commit anchor** — and it
was caught only because the anchors were re-read against the commit objects rather
than accepted. The present-tense state obtained at `cc513f9`; both were
rewritten at `b1386e6` into past tense anchored to `cc513f9`, the commit they were
measured against, carrying the instruction *"measure it; do not read it off this
sentence"*.

**3. The sweep did not see its own output.** At `b1386e6` the C13 table listed
`no longer asserts` among the search terms of the by-construction sweep — **and
omitted the file's only occurrence of that term.** Two of the rows this correction
added were written *by* that sweep and then escaped it, for exactly the reason the
first two escaped:
they were produced after the enumeration ran.

**The step that was missing, now stated as part of the construction:**

> **A sweep's result table is itself an output of the sweep, and must be checked
> against the sweep's own search terms.** A by-construction sweep whose table omits
> the class's only occurrence has not been constructed. Re-running the same terms
> over the finished document — and over the table itself — is part of the sweep,
> not a later verification step.

### What this round did not change

The verdict (negative — the casing stays unobserved), the union (**21**), the sum
(**27**), `run.log` and its rule, the ledger (`results.jsonl` **0** rows against
**`0 of a 0 cap`**), `config.yml`, and rounds 1–5's fixes, all re-verified rather
than assumed. No claim, retraction or sentence is deleted anywhere in this round.

---

## Correction (2026-10-15)

**Seventh round.** Items from the seventh `carelink-verifier` round on PR #127 at
`b1386e6`. One of round 6's findings — the cite count and its stability proof — is
**confirmed closed**: 22 / 0 / 0 at the commit, the amended/pre-amendment table
reproduced with machine-selected novel literals, and `count-cites.py` shown to fail
three ways. The other was open, and its **escape mechanism** is the subject of this
correction.

### C19 — the CONSTRUCTION RULE, and the conversion that ends the class

Seven rounds, one pattern: **every surviving finding was a present-tense claim
about the artefact, written by the correction that fixed the previous one.** The
table omission was closed in round 6, and that fix then generated fresh prose in
the class it had just eliminated. Sweeping is not what fails — a sweep cannot see
prose written *after* it runs — so this round stops sweeping the class and
**removes it**.

> **THE CONSTRUCTION RULE, from here.** This findings-log contains **no
> present-tense self-state claims at all.** Every statement about what the file
> *is* is **past tense, anchored to a named commit** — "at `b1386e6` the file ended
> `0a`", never "the file's last byte is `0a`". A correction describes **what was
> true at a commit**; it does not describe the present. This makes the class empty
> by construction rather than by sweep, which is the only thing that has worked.

**Why this is a construction and not another sweep.** Seven sweeps each closed the
instances they could see and were followed by new instances in the prose that
fixed them. A rule that constrains *what may be written* binds future writes too;
a rule that *looks for what was written* binds only the past. The difference is the
whole seven rounds.

**What the conversion preserves, and why.** `AGENTS.md` §3 requires superseded
wording to stay visible, so the withdrawn sentences are **not deleted**. They are
converted from **assertion** to **quotation** — marked verbatim and withdrawn —
which is the one form that satisfies both rules at once: the wording stays
readable, and the document no longer *makes* the claim. That distinction is the
substance of this correction.

**Eight sites converted, covering ten present-tense claims.** Two further sites
(`:560`, `:747`) were **already compliant** — past tense and anchored to
`cc513f9` — and were verified and left alone rather than touched.

> **Verbatim, withdrawn at `6b493e7`:** *"Every remaining detector hit in the file is
> now one of three permitted forms: a past-tense anchored statement, an explicit
> verbatim quotation of withdrawn wording, or the sweep's own term list."* ⚠ **That
> sentence asserted a property of the file and was itself a member of the class** —
> present tense, unanchored, unmarked — and it was **introduced by the very commit
> that converted the class**, which is the recurrence this section exists to name.
> It is quoted, not restated, for the same `§3` reason.
>
> **The three permitted forms, stated once, as a rule about what may be written
> rather than a claim about what was written:** (a) past tense anchored to a named
> commit; (b) an explicit verbatim quotation of withdrawn wording; (c) the sweep's
> own term list. A detector hit in any other form is a defect to fix, and the sweep
> run at `6b493e7` is recorded by **its output** in this table — not by a sentence
> asserting the output is clean.

| site | before | after |
|---|---|---|
| C8's two clauses | *"the current file's last byte is `0a`"* · *"this file no longer asserts its own trailing byte anywhere"* | past tense, anchored to `6fe6ffb`; the originals quoted inside the withdrawal, both marked withdrawn |
| C10's *"The byte was `2e`, and still is."* | **asserted in bold** | verbatim quotation, marked withdrawn at `b1386e6` |
| C13 table, row 1 | present tense, attributed to *"this section's own marker"* | attributed to **C5**; verdict recast as past + anchored |
| C13 table, row 2 | present tense, attributed to *"this section's own marker"* | attributed to **C10**; verdict recast as past + anchored |
| C13, the sweep's own blind spot | *"`no longer asserts` **is listed above** as a search term"* | *"In the **FIRST version** of the table above, `no longer asserts` **appeared** as a search term"* |
| C18 §1 | *"The existing withdrawal marker … **covers only** … **it does not reach** this tail"* — present tense and false at this commit | *"the withdrawal marker that **existed** on that sentence **at `cc513f9`** … and **did not reach** this tail"* |
| C18 §2 | *"C13's own withdrawal markers **assert** … **Both are now anchored**"* | attribution corrected to **C5 and C10**; recast as *"At `b1386e6` both read that way … Both **were rewritten** at `b1386e6`"* |
| C18 §3 | *"C13's table **lists** … and **omits** the file's only occurrence"* — present tense and false at this commit | *"**At `b1386e6`** the C13 table **listed** … and **omitted**"* |

### C20 — the counting rule's rationale pointed at the wrong finding

`count-cites.py`'s R-C1b rationale read *"That is precisely the defect **C14**
corrects"*. **C14 is the reproducibility finding** — none of the three scripts ran
as its own docstring said — and has nothing to do with the cite count. The defect
is documented at **C17**. A reader following the rule's own justification landed on
the wrong section, which is the failure mode this file spent seven rounds on: the
cross-reference was written from memory and never resolved.

Corrected to name **C17**, with **C14 explicitly ruled out in the same sentence**
and the script-side history (`23 / 29 / 31 / 28 / 30`) recorded so the rule carries
its own evidence.

### C21 — four markers pointed at the wrong finding

Same defect, in the tracked surface. The withdrawal markers on `:691` and `:913`
both pointed at **C14**; the universal claim is documented at **C18** and the cite
count at **C17**. **A reader following the marker this round was written to add
would have landed on the reproducibility section and found nothing.** Both now
point at **C18**. Two further sentences — the de-anchored pair — were attributed to
**C13** and live in **C5** and **C10**; both attributions corrected.

The generalisable form, which is the same as C20's: **a cross-reference is a
citation, and citations are asserted against `AGENTS.md` §1, not written from
memory.** `count-cites.py` counts cites; it does not check that a correction-item
reference resolves to the item that documents the claim. That check is not added
here, and the reason is worth stating: it would need to parse prose for
cross-references, and a rule that cannot fail is not a rule.

### C22 — the PR body's correction count was stale again, in the untracked surface

The PR body said **five** dated `## Correction (2026-10-15)` sections; the file
carried **six** after the previous round's append, and carries **seven** after this
one. It has now been stale in that box twice (four → five → seven).

**This is the same lag C17 found inside the log**, in a surface no checker reads:
a number about an artefact, not re-derived when the artefact moves, describing the
*previous* commit. Corrected to **seven**, and — the part that matters — the box now
carries the **command that derives it**, so the next reader can check rather than
trust:

```
grep -c '^## Correction (2026-10-15)$' findings-log/2026-10-14-pool-r-devicefamily-casing/FINDINGS.md
```

### What this round did not change

The verdict (negative — the casing stays unobserved), the union (**21**), the sum
(**27**), `run.log` and its rule, `count-cites.py`'s figure (**22**, failures 0),
the ledger (`results.jsonl` **0** rows against **`0 of a 0 cap`**), and rounds 1–6's
fixes, all re-verified rather than assumed. No claim, retraction or sentence is
deleted anywhere in this round: every withdrawal is a quotation, not a removal.

---

## Correction (2026-10-15)

**Eighth round.** Items from the eighth `carelink-verifier` round on PR #127 at
`6b493e7`. Everything mechanical in that round is confirmed and is not
re-touched. Three blocking findings, one structural diagnosis, and the reason the
first seven rounds kept missing is finally named here.

### C23 — BLOCKING: the two sentences that declared the class empty were members of it

The diagnosis, stated plainly because it is the most useful thing in this round:

> **Two sentences asserting the class is empty were themselves members.** Both
> evaded the five-term detector by **exactly one token** — `no longer asserts`
> became `no longer **carries**`, and `is now the` became `is now **one**`.

| site | the sentence | why it was a member |
|---|---|---|
| C13 | *"This file no longer carries an unmarked present-tense self-state claim."* | present tense, unanchored, unmarked — and by this document's own construction (`C13:896-901` counts *"what it contains"*), **if true, false** |
| C19 | *"Every remaining detector hit in the file is now one of three permitted forms…"* | present tense, unanchored, unmarked, **introduced by the very commit that converted the class** |

**A regex cannot be its own construction.** Five terms could not have caught
either, because both differ from a listed term by one word, and widening the term
list is precisely the sweep-the-class move that has failed seven times running.

**Fix: delete both assertions. Do not restate them.** A document must not *claim*
its own class is empty; it must simply not contain the class, and let a sweep's
output show that. Both sentences are now **verbatim withdrawals** — quoted, marked
with the commit at which they were withdrawn, and carrying a pointer to the sweep
output that is the evidence. Nothing is deleted: `AGENTS.md` §3 requires the
superseded wording visible, and a withdrawal satisfies that while making no claim.

The three permitted forms survive, but are now stated **as a rule about what may
be written** rather than as a claim about what was written — (a) past tense
anchored to a named commit; (b) an explicit verbatim quotation of withdrawn
wording; (c) the sweep's own term list.

**What replaces the deleted claims is the sweep's own output**, recorded as
"the sweep run at `6b493e7` returned the hits adjudicated in C19's table" — a
statement about a sweep at a commit, which is checkable, rather than a statement
about what this file therefore is, which is not.

### C24 — BLOCKING: a conversion replaced an accurate phrase with a wrong commit anchor

C18 asserted *"At `b1386e6` both read that way in the present tense and neither was
anchored."* **False, and it contradicted its own next clause** — a sentence cannot
both read present-tense at `b1386e6` and have been rewritten there.

Measured against the commit objects:

| commit | `:560` (C5's marker) | `:745` (C10's marker) |
|---|---|---|
| `cc513f9` | *"this file's last byte **is** `0a`"* | *"The file's last byte **is now** `0a`"* |
| `b1386e6` | *"…last byte **was** `0a` **at `cc513f9`**"* | *"…last byte **was** `0a` **at `cc513f9`**"* |

`b1386e6` **is** the commit that rewrote them, so the state *at* `b1386e6` is
already the rewritten one. **The present-tense state obtained at `cc513f9`**, the
commit before. Corrected, with the contradiction left visible.

**The mechanism, which is the transferable part: a tense conversion is an anchor
write, and an anchor write must be verified against the commit objects like any
other citation.** Round 6's finding — *"fixing a citation by adding one, without
checking where it lands"* — recurred here inside a tense conversion rather than
inside a citation, which is the same defect wearing different clothes.

### C25 — nine unadjudicated candidates, read and adjudicated

The verifier listed nine it had not adjudicated and declined to certify without
reading each in context. Read, in context, at `6b493e7`:

| site | the claim | verdict |
|---|---|---|
| `:10` | *"`results.jsonl` holds **0** rows and the `N of a M cap` line reads **0 of a 0 cap**"* | **MEMBER** — present-tense state about this file, unanchored. Machine-checked by `research-checks.py`, but that is a second gate, not an anchor. **Converted**: quoted, marked, and the derive-command recorded. |
| `:175` | the `MINIMED` cell's *"exactly two places"* count, with its withdrawal | **COMPLIANT** — the false sentence is already a preserved, marked withdrawal (§3), and the replacement count is anchored to `git grep -w` at base `7d915b8`. |
| `:279` | *"⚠ The count in this bullet is FALSE"* | **COMPLIANT** — a withdrawal marker, not a state claim. |
| `:377` | *"`run.log` **is** the output of `probe.sh`"* | **MEMBER** — present tense, unanchored; my round-8 de-anchoring removed *"now"* and left *"is"*, which is the same defect. **Converted** to `805211e`. |
| `:423` | *"`count-candidates.py` **now carries** the two cites deliberately apart"* | **MEMBER** — a present-tense claim about a file's contents, which C13's own definition counts. **Converted** to `805211e`. |
| `:512` | *"nothing compares `run.log` against this prose"* | **MEMBER** — an open-ended universal about the repo's tooling. **Converted** to `6fe6ffb`. |
| `:532` | *"The regenerated `run.log` … **is** the authoritative copy"* | **MEMBER** — present-tense state about a file. **Converted** to `6fe6ffb`. |
| `:675` | *"the table **is now** append-proof"* | **MEMBER** — present tense about the table's state. **Converted** to `a1c4dd6`. |
| `:705` | *"A correction that supersedes the line directly above it is the clearest possible demonstration…"* | **COMPLIANT** — a general claim about the class of corrections, not a state claim about this artefact. Left alone. |

**Six members converted, three compliant.** Every anchor written this round was
then **re-verified against the commit objects**, which is how four of the six were
caught wrong on first draft (see below).

**And the trap fired anyway, a second time.** Drafting the six anchors I wrote
`a1c4dd6` for three of them and `b1386e6` for a fourth, from memory. Checking them
against the objects showed **four wrong**: the `:349` cite first appears at
**`805211e`**, not `a1c4dd6`; the heading-anchored self-cites first appear at
**`a1c4dd6`**, not `b1386e6`; C4 first appears at **`6fe6ffb`**. Corrected, and the
first grep I used to check was itself wrong — `":349 (heading"` does not appear
because the string is split across two source lines, so the grep returned `0` for
*every* commit and would have "confirmed" anything. **A check that returns zero for
the wrong reason is worse than no check**: the first grep said the cite was absent
everywhere, which was false, and only re-deriving with a pattern that matches the
real text corrected it.

### C26 — the leak scan, with the nets proved live

Round 7's verifier parsed all ten patterns and **did not prove they fire**, and said
so plainly. Its first control list was mis-ordered and produced seven spurious
`DEAD!!` readings.

**`scrub-selftest.py` is committed with this correction**, and it does three things
the earlier ad-hoc attempts did not:

1. **Derives every control from the regex**, element by element — every mandatory
   literal reproduced, every quantifier satisfied at its minimum, and **every
   alternation branch exercised separately**. Coverage is asserted: **10 of 10**
   patterns carry at least one control, and an uncontrolled pattern fails the run.
2. **Carries negative controls**, so a net that fires on everything is caught too:
   a long random vendor field name, a sha256 digest, a URL path, the superseded
   lowercase-`u` reCAPTCHA shape, and the one-label host shape — **6 strings, 0
   false positives**.
3. **Scans its own source.** Every control is assembled at runtime from fragments,
   because a committed file containing a string that matches the very patterns it
   tests would turn the gate red — the situation `scrub-patterns.txt:5-6` documents
   for itself. **214 lines of this file: 0 hits.**

**Result over `git diff 7d915b8 HEAD`:**

```
patterns parsed            : 10
positive controls fired    : 22   (10/10 patterns covered)
dead patterns              : 0
false positives            : 0    (6 negative controls)
scrub hits, added lines    : 0    (2131 added lines)
scrub hits, this file      : 0    (214 lines, self-scan)
RESULT: PASS
```

**And it caught me.** The first run reported **5 dead patterns** — all five
branches of the internal-host pattern. The nets were fine; **my controls were
mis-shaped**: that regex is `prefix . label . (minimed|medtronic) .`, so it needs
**two** labels before the TLD, and the one-label form I had written does not match.
Re-derived, all five fire, and the wrong shape was **added as a negative control**
so the mistake cannot recur silently. This is the same class as the mis-ordered
control list that produced seven spurious `DEAD!!` readings elsewhere in this pool —
and the reason this script prints the derivation next to each control is that a
reader should be able to tell a dead net from a bad control without running it.

### What this round did not change

The verdict (negative — the casing stays unobserved), the union (**21**), the sum
(**27**), `run.log` and its rule, `count-cites.py`'s figure (**22**, failures 0),
the ledger (`results.jsonl` **0** rows against **`0 of a 0 cap`**), and rounds 1–7's
fixes, all re-verified rather than assumed. No claim, retraction or sentence is
deleted anywhere in this round: every withdrawal is a quotation, and the two
deleted *assertions* survive as quotations.
