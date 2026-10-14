# Area R — `deviceFamily` casing: the vocabulary reconciled, and the question retired

**Pass date:** 2026-10-14 (pool run 2026-10-14, worker R) · **Claim issue:**
[#124](https://github.com/NovaLux12/carelink-api-research/issues/124) ·
**Method:** offline reconciliation over committed artefacts — no probe, no
network call of any kind · **Requests: 0 of a 0 cap.**

> **Accounting.** This pass sent **0** HTTP requests to any Medtronic, MiniMed or
> Abbott host — and **no request of any kind to any host**, which is the point.
> The cap is zero because nothing is probed. `results.jsonl` holds **0** rows and
> the `N of a M cap` line above reads **0 of a 0 cap**; the ledger and the prose
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
| `MINIMED` | `findings-log/2026-10-11-third-party-client-sources/FINDINGS.md:69` | "values seen by these clients" — no `file:line`, no per-client attribution. **These two strings appear in exactly two places in the whole repository: that line, and `docs/10` row 37 echoing it.** |
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
  (`docs/05:315`, `"GUARDIAN" === n.deviceFamily`).
- `MINIMED` and `PARADIGM` are **withdrawn pending a `file:line`**. They exist in
  exactly two places in the repository — one uncited log line and the row that
  quotes it — so the row was citing its own source back at itself.
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

**Fix: regenerated, not hand-edited.** `run.log` is now the output of
`probe.sh`, which wraps the current `count-candidates.py` between its two marker
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

**Fix.** `count-candidates.py` now carries the two cites deliberately apart —
`:349` for the phrase, `:384-385` for the tokens — and prints both in the
`DECLARED BUT NOT ADMITTED` block, so the regenerated `run.log` states the
attribution at the line that holds it. The `docs/05` citations were corrected in
place (canonical docs supersede), and this section keeps the original wording
visible above.