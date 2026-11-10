# Area AE — is the `android/<app-version>` tail a lookup table, or a threshold?

Pass of **2026-11-10**. Claim issue **#161**. Branch `research/ae-appversion-tail`.
Prior art and harness template: `findings-log/2026-10-17-area-aa-appversion-axis/`.

**Answer, up front. It is a table keyed on the string, not a threshold.** The
ladder inside `(3.6, 3.9)` at base `v13` does not move the document class
monotonically. On `clcloud.minimed.com` the seven tails return the legacy class,
the legacy class, the **current** class, the legacy class, the **current**
class, the legacy class, the legacy class — `L L C L C L L` — and
`clcloud-trials.minimed.com` returns the same sequence. **A monotone step
function of the numeric value cannot leave a class and return to it (INFERRED;
the sequence it contradicts is OBSERVED, §4).** The cells that return the
current-generation document are exactly `3.7` and `3.8`; every other tail
strictly inside `(3.6, 3.9)` falls to the legacy document, and `3.6` itself is
current (area AA, OBSERVED). So the current-generation set among the strings
tested is `{3.6, 3.7, 3.8}` — which is the row `docs/03` §3 has carried for
`.eu` all along.

**18 of a 20 cap** — two requests unspent, GET only, cap not revised. No
failures, no retries, no deviation. **Same-host spacing floor measured at
3.427 s** across 16 gaps, 0 of them under 2.5 s (§2).

---

## 1 · Request accounting

Ledger: [`results.jsonl`](./results.jsonl) — **18 rows**, one per request, `seq`
1…18 with no gaps and no duplicates. Harness: [`probe.sh`](./probe.sh), whose
`CAP=20` is a single assignment at `:56` and is asserted against the **ledger
length**, not a process-local counter, so a second invocation cannot silently
exceed the pass budget. `DELAY=2.5` is `:57`, applied at `:150` — inside the
per-host `flock`, after the gate check.

Two invocations, one per host (`probe.sh host1`, `probe.sh host2`), each
controls-first. Order per host: `v99` absent, `v11` served, then the seven-cell
ladder `3.61, 3.65, 3.7, 3.75, 3.8, 3.85, 3.89`.

| # | host | base | tail | role | status | B | `body_sha256` | `erased_config_sha256` |
|---|---|---|---|---|---|---|---|---|
| 1 | `clcloud.minimed.com` | `v99` | `3.6` | control-absent | 403 | 42 | `f249b63cb2fc…` | — |
| 2 | `clcloud.minimed.com` | `v11` | `3.6` | control-served | 200 | 18105 | `2103b7e850c4…` | `7ac09335c7e4…` |
| 3 | `clcloud.minimed.com` | `v13` | `3.61` | data-ladder | 200 | 18106 | `2eb6d4102e5b…` | `7ac09335c7e4…` |
| 4 | `clcloud.minimed.com` | `v13` | `3.65` | data-ladder | 200 | 18106 | `cf321df805b3…` | `7ac09335c7e4…` |
| 5 | `clcloud.minimed.com` | `v13` | `3.7` | data-ladder | 200 | 20256 | `de96fb4dd27a…` | `7ad212402d7f…` |
| 6 | `clcloud.minimed.com` | `v13` | `3.75` | data-ladder | 200 | 18106 | `709b2fba43d1…` | `7ac09335c7e4…` |
| 7 | `clcloud.minimed.com` | `v13` | `3.8` | data-ladder | 200 | 20256 | `9d0458d0185b…` | `7ad212402d7f…` |
| 8 | `clcloud.minimed.com` | `v13` | `3.85` | data-ladder | 200 | 18106 | `4abbc6529c67…` | `7ac09335c7e4…` |
| 9 | `clcloud.minimed.com` | `v13` | `3.89` | data-ladder | 200 | 18106 | `3bcec8f07cdd…` | `7ac09335c7e4…` |
| 10 | `clcloud-trials.minimed.com` | `v99` | `3.6` | control-absent | 403 | 42 | `f249b63cb2fc…` | — |
| 11 | `clcloud-trials.minimed.com` | `v11` | `3.6` | control-served | 200 | 20345 | `94b739dda478…` | `def5847975c6…` |
| 12 | `clcloud-trials.minimed.com` | `v13` | `3.61` | data-ladder | 200 | 16370 | `bf769926555e…` | `9962b3db79b1…` |
| 13 | `clcloud-trials.minimed.com` | `v13` | `3.65` | data-ladder | 200 | 16370 | `62804ec08c0b…` | `9962b3db79b1…` |
| 14 | `clcloud-trials.minimed.com` | `v13` | `3.7` | data-ladder | 200 | 20256 | `de96fb4dd27a…` | `7ad212402d7f…` |
| 15 | `clcloud-trials.minimed.com` | `v13` | `3.75` | data-ladder | 200 | 16370 | `9ad089f575e4…` | `9962b3db79b1…` |
| 16 | `clcloud-trials.minimed.com` | `v13` | `3.8` | data-ladder | 200 | 20256 | `9d0458d0185b…` | `7ad212402d7f…` |
| 17 | `clcloud-trials.minimed.com` | `v13` | `3.85` | data-ladder | 200 | 16370 | `60977b7e4cfb…` | `9962b3db79b1…` |
| 18 | `clcloud-trials.minimed.com` | `v13` | `3.89` | data-ladder | 200 | 16370 | `4fff97e20a5e…` | `9962b3db79b1…` |

Every value above is the harness's own record at `results.jsonl:<seq>`, not a
re-read; `run.log` carries the same fields per request plus the bounded
structure projection. **No raw body is committed** — bodies were written to a
`mktemp -d` directory and reduced at send time to status, content-type, bytes,
`body_sha256`, `echo_n` and `erased_config_sha256` (`AGENTS.md` §7).
`gh-run-err.log` is **empty**, kept as evidence that the pre-send gate check ran
and wrote nothing.

### Controls, as actually sent

Both were sent **first on each host**, before any ladder cell:

- **certainly-absent** `v99` at `android/3.6` — `403`, 42 B, `application/json`,
  `x-amzn-errortype: MissingAuthenticationTokenException`, at the corpus no-route
  digest `f249b63cb2fcb66b…` on **both** hosts (`results.jsonl:1`, `:10`). The
  oracle is sound on both hosts, and the two 403 bodies are the same artefact.
- **served** `v11` at `android/3.6` — `200` on both hosts (`:2`, `:11`), which
  proves the route answers on each host before any ladder cell is read.

Recording the `v11` cells as they actually came back: `.com` served 18105 B
(legacy class, ctry 99) while `-trials` served 20345 B (the **current** class,
advCumulus `v13`, ctry 109, US SSO only). The `v11` control is not the same
document on the two hosts, which is why it is used only as a liveness control
and never as a class reference. This is also why the ladder is compared
**within** a host, never across.

### Spacing

[`spacing.py`](./spacing.py) → [`spacing.txt`](./spacing.txt). **Counting rule:**
one gap per consecutive same-host pair in request order, so 9 bodies per host
give **8** gaps per host and **16** in total. Two invocations ran, but a gap is
only counted between two requests to the same host, so the boundaries between
invocations are not gaps.

| host | gaps | min | max | gaps < 2.5 s | gaps < 2.0 s |
|---|---|---|---|---|---|
| `clcloud.minimed.com` | 8 | **3.499 s** | 3.918 s | **0** | **0** |
| `clcloud-trials.minimed.com` | 8 | **3.427 s** | 9.604 s | **0** | **0** |

**Measured floor: 3.427 s** over 16 same-host gaps — every request ≥ 2.5 s apart
from the previous one on that host, **0** gaps under the declared 2.5 s and **0**
under the repo's 2 s floor (`AGENTS.md` §8), spacing therefore never short. `spacing.py`'s
self-conviction check reports **0 of 18** rows with `t_done < t_sent`, so the
series is not self-refuting and its gaps are evidence. The 9.604 s maximum on
`-trials` is the host lock doing its job while the `.com` invocation finished.

---

## 2 · What the ladder returned — the class sequence

**OBSERVED.** [`structure.py`](./structure.py) → [`structure.txt`](./structure.txt),
zero requests, reading only the ledger's `erased_config_sha256` field, which
`probe.sh` computed on the transient body. **Counting rule:** one class per
distinct `erased_config_sha256`; a class of size 1 proves nothing about
constancy, and only a class of size ≥2 is cited as evidence that the tail did
not vary the rest of the body.

### 2.1 The echo is still there, and still the trap

Every one of the 16 `200` bodies matches `\{"config":"android,<requested
tail>",` and the requested tail occurs **exactly once** in the body bytes
(`echo_n=1` in all 16 rows). The raw digests therefore differ across every cell
even where the document is the same — `3.7` and `3.8` carry two different raw
digests (`de96fb4dd27a…`, `9d0458d0185b…`) for **one** document. **The status
line is constant `200` across the whole ladder and cannot see any of this**, which
is exactly the trap area AA recorded at `§4.1`. Nothing in this section is
readable from a status code.

### 2.2 The sequence

| tail | `clcloud.minimed.com` class | class | `clcloud-trials.minimed.com` class | class |
|---|---|---|---|---|
| `3.61` | `7ac09335c7e4` | legacy | `9962b3db79b1` | legacy |
| `3.65` | `7ac09335c7e4` | legacy | `9962b3db79b1` | legacy |
| `3.7` | `7ad212402d7f` | **current** | `7ad212402d7f` | **current** |
| `3.75` | `7ac09335c7e4` | legacy | `9962b3db79b1` | legacy |
| `3.8` | `7ad212402d7f` | **current** | `7ad212402d7f` | **current** |
| `3.85` | `7ac09335c7e4` | legacy | `9962b3db79b1` | legacy |
| `3.89` | `7ac09335c7e4` | legacy | `9962b3db79b1` | legacy |

Class sequence, in ladder order: **`L L C L C L L`** — identical on both hosts.

The two classes are not cosmetic. The **current** class (`7ad212402d7f`, n=2 per
host, 20256 B) advertises cumulus **`v13`**, carelink **`v2`**, **3** `CP[]`
entries and **109** countries, with SSO files
`oauth20_sso_carepartner_us_v6.json` + `oauth20_sso_carepartner_eu_v6.json`. The
**legacy** class is `v2` / `v1` / **2** `CP[]` / **99** countries with
`eu_sso_cp_eu_v6.json` + `sso_cp_us_v6.json` on `.com`, and `v2` / `v1` / 2 /
**76** countries with `sso_cp_us_v6.json` alone on `-trials`. Those are the same
two shapes area AA recorded, and `docs/03` §3b.2 characterizes as the substantive
selection.

### 2.3 Both classes re-derive area AA's cells exactly

- The **current** digest `7ad212402d7f` is the digest AA recorded for tail `3.6`
  on **both** hosts (`findings-log/2026-10-17-area-aa-appversion-axis/FINDINGS.md`
  §4.2, table row `3.6`). So `3.7` and `3.8` each produce the document `3.6`
  produces, and the three collapse to one erased digest.
- The **legacy** digests `7ac09335c7e4` (`.com`) and `9962b3db79b1` (`-trials`)
  are the digests AA recorded for tail `3.9` on each host (same table, row
  `3.9`). So every other ladder tail produces the document `3.9` produces.

This is a **re-derivation, not a new claim**, and per `AGENTS.md` §2.1 it is **one
source** — this repository — observed again, not a second source. No strength
word is used for it. What is new is not the identity of the documents; it is the
**ordering** of them along the ladder, which AA never had.

Stated precisely, because it is the mechanism: `de96fb4dd27a…` is the raw digest
of `3.7` on **both** hosts and `9d0458d0185b…` is `3.8` on **both** hosts, each
at 20256 B (`results.jsonl:5`, `:14`, `:7`, `:16`). So the current-class document
is byte-identical **across** the two hosts once the echoed tail is equal, while
the legacy class is not (`.com` 99 countries, `-trials` 76) — exactly what AA
§4.2 recorded.

---

## 3 · The verdict: table, not threshold

**OBSERVED:** the class sequence along the strictly increasing ladder
`3.61 < 3.65 < 3.7 < 3.75 < 3.8 < 3.85 < 3.89` is `L L C L C L L` on both hosts
(§2.2).

**INFERRED — and this is the whole argument:** a threshold rule is a **monotone**
step function of the numeric value. Once such a function leaves the legacy
branch at `3.65 → 3.7`, it cannot return to the legacy branch at `3.75` — a
step function has no way back down. The observed sequence does return, twice.
Therefore **no single-boundary and no multi-boundary threshold over the numeric
value can produce these cells**; the rule must be keyed on the **string**. That
is a table.

**Assumptions this inference rests on**, stated so they can be attacked:
that the response document is a function of `(host, base, tail)` with no fourth
input (AA's cross-product is consistent with this and area AE's brief inherits
it); that the seven cells are seven independent *requests* against one
deployment state, so a mid-ladder configuration change is not the explanation —
the two hosts agreeing cell-for-cell makes a transient change an unlikely but
not excluded cause; and that `3.61`/`3.65`/`3.75`/`3.85`/`3.89` are being
compared as strings by the server rather than truncated to one decimal place.
**That last assumption is not tested by this pass** and is a real limit: if the
server truncated to one decimal, `3.75 → 3.7` and `3.85 → 3.8` would be
expected, and the observed sequence would then be `L L C C?…` — it is not, so
truncation to one decimal is **excluded by the cells themselves**
(`3.75 → legacy`, `3.85 → legacy`, whereas `3.7` and `3.8` are current). What
remains untested is a *finer* normalisation than one decimal, which no cell here
addresses.

**What the table's members are among the strings tested.** Combining this pass
with AA (**one source**, so this is a set statement over this repo's own cells):
`3.6 → current` (AA), `3.7 → current`, `3.8 → current`, `3.5 → a third
document` (AA: advCumulus `v11`, carelink `v2`, ctry 109 — distinct from both
classes above), and every other tail tested at `v13` (`3.39`-side not swept;
`3.61`, `3.65`, `3.75`, `3.85`, `3.89`, `3.9`, and AA's fabricated
`absent-probe-871`) → legacy. So the current-generation entry is
**`{3.6, 3.7, 3.8}`** and the fabricated tail still lands on legacy, i.e. the
lookup falls through to a default rather than rejecting — **INFERRED** as a
fall-through default, since one unrecognised tail landing on legacy is equally
consistent with "anything unmatched gets the legacy document" and with "the
legacy document is the default for the whole current-generation gap".

**A negative that must be stated as a negative.** The successor area AE's brief
expected that a table, if that is what this is, might reveal itself as a **fourth
distinct document** inside `(3.6, 3.9)`. **It did not.** The ladder found **two**
classes, both already known, and no new document. The table verdict rests on the
**ordering**, not on document count. Anyone reading this log should hold exactly
that: the count evidence is absent, the ordering evidence is present and strong.

---

## 4 · What the rows do not establish

- **The table's full membership.** Only `X.Y` and `X.YY` strings were sent. Whether
  `3.60`, `3.70`, `3.700` or `3.6.0` map to current is **not measured here** —
  area Q's body-axis work records that `3.6.0`/`3.7.0`/`3.8.0` are forms clients
  actually ship, and they are **unobserved on this path**. If normalisation
  exists, it lives in that gap.
- **Why `3.7` and `3.8` are in the table at all.** A plausible reading is that
  the table enumerates the client versions Medtronic has shipped — `docs/03` §3
  records `3.8` as the version the readable client pins and `3.7` as the value
  xDrip moved from. That reading is **INFERRED** and this pass adds no cell that
  tests it.
- **Whether the table is complete above `3.9`.** Not swept. Carried to successor
  AG.
- **The `-trials` `v11` document.** The served control returned the **current**
  class there and the legacy class on `.com` — a host difference on a base this
  pass did not vary. Not investigated, not claimed.
- **The legacy class's host difference** (99 countries and an EU SSO entry on
  `.com` against US-only 76 on `-trials`). Re-observed, not explained; AA §6
  carries it unchanged.
- **`x-cum-signature`.** Not re-examined; no claim made about it.

---

## 5 · Effect on `docs/03` — a change is made, because the table reading retires a reading

**This pass changes what `docs/03` says, so `docs/03` is edited and cites this
log.** Three edits, and the third is the one that matters:

1. **§3b.6 is new** — it records the `L L C L C L L` sequence, the table verdict,
   the `{3.6, 3.7, 3.8}` membership among strings tested, and the two open gaps.
2. **§3b.5 is superseded in place, not deleted** — its blockquote says what failed.
3. **The reading §3b.2 left open is retired, and that is the substantive change.**
   §3b.2 presented the axis as "three documents, selected by the tail" and left the
   rule's shape unstated, which admitted a **generation-step** reading (current up to
   a version, legacy above it). §3's own `.eu` table — `3.6, 3.7, 3.8 → v13`; `3.9`+
   → legacy — is the *same pattern*, and the ladder is what says the table was right
   and the step reading was an artefact of sampling only the two ends of the
   interval. **Those two readings are not both true, and the cells decide which.**

The practical consequence, now stated in `docs/03`: the pin `android/3.6` is a
**table entry**, not a point above a threshold, so a boundary moving underneath it
cannot make it stale — a weaker failure mode than §3's ADR-0002 discussion assumes.
What it *can* lose is its entry, which is the change worth watching and the reason
this pass added no pin (§6).

§3's own `.eu` cells are **not** touched: this pass sent no `.eu` request and
makes no claim about that host.

---

## 6 · No pin added — and why the tempting one is still declined

**No assertion is added to `regression/hurl/`.** The candidate is obviously the
`3.75 → legacy` / `3.8 → current` pair, which is the pair that distinguishes a
table from a threshold and is the most valuable single assertion this corpus
could hold.

It costs **2 vendor requests on every PR gate** and again in the weekly drift
sweep (`scripts/research-gate.sh` executes the `05-public-config` suite, which
CI runs on every push). Two requests is cheap. The reason to decline is the same
one AA gave and it has not changed: **the change that would matter is the
`3.6`-class document departing or the pin's entry being removed from the table**,
and neither of those is detected by re-asserting that `3.75` is legacy. A pin
that fires on the wrong change is worse than no pin, because it trains a reader
to ignore it. **Measure.** Recorded here rather than silently omitted.

---

## 7 · Independence

One lane, one run, one ledger, one author. Under `AGENTS.md` §2.1 the count is
**1** for every claim in this log, including the cross-host agreement of the
class sequence and the re-derivation of AA's digests — this repository's own
earlier pass is the same source, so the words *independently*, *corroborated*,
*confirms* and *double-sourced* carry no claim here. Where agreement is worth
reporting it is named as coherence (*consistent with*, *re-derives*) rather than
multiplicity.

---

## 8 · Evidence table

| # | Claim | Class | Source |
|---|---|---|---|
| 1 | 18 requests sent, 18 ledger rows, cap 20 not revised, 2 unspent | OBSERVED | `results.jsonl:1-18`; `probe.sh:56` |
| 2 | Same-host spacing floor 3.427 s over 16 gaps, 0 under 2.5 s | OBSERVED | `spacing.txt` |
| 3 | `v99` control `403` at `f249b63cb2fc…` on both hosts | OBSERVED | `results.jsonl:1`, `:10` |
| 4 | `v11` control `200` on both hosts | OBSERVED | `results.jsonl:2`, `:11` |
| 5 | All 16 `200` bodies echo the requested tail exactly once | OBSERVED | `structure.txt` §Per-cell, `echo_n=1` |
| 6 | The class sequence across the ladder is `L L C L C L L` on both hosts | OBSERVED | `structure.txt` §Classes; `results.jsonl:3-9`, `:12-18` |
| 7 | The current class is `v13`/`v2`/CP 3/109 ctry; the legacy class is `v2`/`v1`/CP 2/99 (`.com`) and /76 (`-trials`) | OBSERVED | `results.jsonl` `structure` field, seq 5,7,16 vs 3,4,6,8,9 |
| 8 | The rule is keyed on the string, not a threshold | INFERRED | §3; the refuted object is the OBSERVED sequence at row 6 |
| 9 | `3.7`/`3.8` reproduce AA's `3.6` digest `7ad212402d7f`; the other five reproduce AA's `3.9` digests | OBSERVED | `structure.txt`; `findings-log/2026-10-17-area-aa-appversion-axis/FINDINGS.md` §4.2 |
| 10 | Truncation to one decimal is excluded | INFERRED | `3.75`/`3.85` → legacy while `3.7`/`3.8` → current (row 6) |
| 11 | Unmatched tails fall through to the legacy default | INFERRED | AA's fabricated tail on legacy; no rejecting status observed at any cell |
| 12 | The table found no fourth document inside `(3.6,3.9)` | OBSERVED | `structure.txt` §Classes: 2 distinct classes, both known |
| 13 | Every claim above rests on 1 source | INFERRED | an audit conclusion about source identity, not something seen in a response |
