# FINDINGS — area R successor 2: is the `_*` suffix on the client deviceFamily enum consumed anywhere?

**Pass:** `2026-10-15-area-r2-x-suffix` · **Claim issue:** #132 · **Lane:** B
(2026-10-15 research pool) · **Corpus:** the patient eager main bundle, one file,
digest-pinned.

---

## 0. Accounting

**4 of a 8 cap** used. `GET` only — the two method words this pass did *not* use
are named so the record is unambiguous: **0 `POST`**, **0 `OPTIONS`**, **0 `HEAD`**.
One host: `carelink.minimed.eu`. Delay **2.5 s apart**, enforced by a `sleep`
*inside* the shared per-host `flock`, with the send-stamp taken immediately before
`curl` execs. Declared floor **≥2 s** (`AGENTS.md` §8); this pass declares and
measures **2.5 s**.

`wc -l results.jsonl` = **4**, equal to the 4 in the line above.

| # | role | method | status | bytes | body sha256 |
|---|---|---|---|---|---|
| 1 | CONTROL, certainly-absent path | GET | 404 `text/html; charset=iso-8859-1` | 196 | `80c3fe2a…` |
| 2 | DATA cell + POSITIVE control (corpus) | GET | 200 `application/javascript` | 3 417 255 | `0fb4fbd4…` |
| 3 | CONTROL, certainly-absent path (**re-issue**, see §7) | GET | 404 `text/html; charset=iso-8859-1` | 196 | `80c3fe2a…` |
| 4 | DATA cell + POSITIVE control (corpus, **re-issue**) | GET | 200 `application/javascript` | 3 417 255 | `0fb4fbd4…` |

The 4 remaining requests of the cap were **not spent**. The population this pass
counts is defined by the artefact, not by how often it is read: re-fetching the
same digest would widen nothing. They are reported as unspent, not as deferred
work.

**Controls, numbered as they were actually sent.**

- **C1 — certainly-absent path (seq 1, re-issued as seq 3).** `/zzzz.not-a-bundle-<12-byte-urandom-nonce>.js`,
  derived by taking the corpus's own `*.js` path shape and substituting a nonce no
  vendor build emits. Answer: **404**, `content-type: text/html; charset=iso-8859-1`,
  **196 B**, body `<title>404 Not Found</title>`. It went out **before** the data
  cell it judges, so "this host 404s here" is a measurement and not a reading of
  the 200 afterwards.
- **C2 — anchor gate + positive control (seq 2, re-issued as seq 4).** The corpus
  must reproduce its pinned identity before anything is read. sha256
  `0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa` and
  3 417 255 B, **MATCH** both. This doubles as the positive control: it proves the
  fetch-and-grep pipeline resolves and finds tokens *at all*, so a zero in §3 is a
  zero and not a broken matcher. `xsuffix-analyse.py` refuses to print anything
  else on a mismatch (exit 3).
- **C3 — case-sensitivity control. 0 requests.** The same token set re-run
  case-insensitively, in §3.2. Cost is 0 because the body is already in hand and
  its digest is already pinned in this pass's own ledger row; re-fetching to run a
  search would spend a request to re-observe a byte-identical artefact.
- **C4 — literal-vs-directive control. 0 requests.** Four literals known present by
  committed prior work must all come back non-zero or the zeros are void (§3.3).

---

## 1. The question, and the verdict

> Is the `_*` suffix a transport axis, a model axis, or a build discriminator — or
> is the enum declared and never read?

**Verdict: in the eager main bundle the suffix is inert at every read, and no call
site branches on it.** Three of the five declared members are read; `BLE_X` and
`SIMPLERA_X` are **not read anywhere in this corpus**. They are not *ignored* —
they are **inert**: the members are unreachable as code, even though the *values*
they name are matched, because the one consumer tests `startsWith("BLE")` and that
is already true of `"BLE_X"`. Deleting both members would change no branch for any
input, including the members' own values.

This is the **negative** the row allows, stated as the row asks: the suffix is
**declared and unused** here. It is not evidence that the suffix is meaningless on
the wire — that half needs an authenticated response and is untouched (§5).

---

## 2. The enum, read verbatim

Bundle module header at byte **1 723 196**; object literal at bytes
**1 723 245 – 1 723 341**:

```
45559:(Je,_e,i)=>{"use strict";i.d(_e,{G:()=>e});const e={BLE:"BLE",BLE_X:"BLE_X",SIMPLERA:"SIMPLERA",SIMPLERA_X:"SIMPLERA_X",GUARDIAN:"GUARDIAN"}}
```

Read in code, not transcribed from prose (`census.txt` §B):

| member | key byte | value byte | key == value |
|---|---|---|---|
| `BLE` | 1 723 254 | 1 723 259 | yes |
| `BLE_X` | 1 723 264 | 1 723 271 | yes |
| `SIMPLERA` | 1 723 278 | 1 723 288 | yes |
| `SIMPLERA_X` | 1 723 298 | 1 723 310 | yes |
| `GUARDIAN` | 1 723 322 | 1 723 332 | yes |

Order, count and spelling all reproduce area P's record
(`findings-log/2026-10-13-area-p-static-schema/FINDINGS.md` §4 item 1, "byte offset
1,723,245"). Two things that record does not state, both visible above: there is
**no comment and no sibling map** attached to the literal, and the module exports
exactly one binding (`G`) via `i.d(_e,{G:()=>e})`.

> ⚠ **Correction to the row that opened this pass.** `docs/11` §"Addendum
> (2026-10-14, from area R, issue #124)" successor 2 reads *"declares **four**
> `_X`-suffixed variants"*. There are **two**: `BLE_X` and `SIMPLERA_X`, out of
> five members. Measured case-sensitively, each occurs exactly twice in the corpus
> and both occurrences are the declaration's own key and value (§3.2). The row's
> sentence is **not edited by this pass** — it is another area's record of what was
> believed when the area opened, and a correction that overwrites the belief leaves
> no evidence the belief existed. Recorded in both places.

## 3. Every read, and every hit read

### 3.1 The consumer population is bounded, then closed

A webpack module is reachable only by id, so counting the id bounds the
population of possible consumers before any search over member names runs. The
string `45559` occurs **twice** in the body (`census.txt` §C):

- **@1 723 196** — the definition.
- **@2 962 721** — one importer, `o=i(45559)`, inside module `83644`.

One importer, binding `o`. Every occurrence of `o.G` in the body is **four**
(`census.txt` §D), and each was read:

| byte | what | verdict |
|---|---|---|
| 198 638 | `(0,o.G)((0,o.d)(Q),!1,this.timeUnits,this.reportDateFormat)` | **false hit** — same token, different binding; this `o` is another module's exported *function*, called |
| 2 964 176 | `p.startsWith(o.G.BLE)` | **member read** `BLE` |
| 2 964 215 | `p.startsWith(o.G.SIMPLERA)` | **member read** `SIMPLERA` |
| 2 964 259 | `p.startsWith(o.G.GUARDIAN)` | **member read** `GUARDIAN` |

The byte-198 638 row is the hazard `AGENTS.md` §6.2 names, caught by reading rather
than by counting: `grep '\.G'` returns 4 and the answer is 3.

Consumption shapes that are *not* `<binding>.G.<member>` would not appear in that
table, so they were swept explicitly rather than assumed absent (`census.txt` §D):
`o.G["X"]` **0**, `o.G['X']` **0**, `Object.values(o.G)` **0**,
`Object.keys(o.G)` **0**, `Object.entries(o.G)` **0**, `{...o.G}` **0**,
`o.G` passed as a whole call argument, `**(o.G)**` **0** — that is **7 of the 8
sweeps at zero**. The 8th returns exactly **1** hit, and it is the row-198 638
false hit already listed above: a *different* module's exported function, called.
So no iteration, no destructuring and no bracket read can be consuming a member
without showing up in the member-read table.

> ⚠ **The 8th sweep's pattern is now printed in `census.txt`, and this sentence's
> description of it was wrong.** It previously read *"the 8th, `o.G` followed by a
> comma or a semicolon"*. **The pattern actually run is `(?<![.\w])o\.G(?![\w.])`** —
> a negative lookbehind, and a negative lookahead that excludes a following word
> character **or a dot**. Reproducing the sweep as it was described —
> `o\.G[,;]` — returns **0**, not 1: the character after `o.G` at byte 198 638 is
> **`)`**, a comma and a semicolon appear nowhere at that site. The count was right
> and the hit was correctly adjudicated, but the description was false and
> `census.txt` printed only the label, never the regex, so a re-runner following
> this log would have reproduced a contradiction (`AGENTS.md` §6.2).
> `xsuffix-analyse.py` now prints `regex=` beside every sweep's label and count.

**Member reads: 3. Distinct members read: 3 of 5.** `BLE_X` and `SIMPLERA_X` have
**0 reads**.

> **THE BYTE FRAME, stated once and used everywhere.** This log reports offsets in
> **two** frames and they differ by 4, so a reader joining two of its own tables can
> come out with a different partition. Stated here, once:
>
> | frame | the three member reads | used for |
> |---|---|---|
> | **site offset** — the first byte of the whole `o.G.<MEMBER>` expression | 2 964 176 / 2 964 215 / 2 964 259 | §3.1's read table, `§8`, `census.txt` §D and §L |
> | **token offset** — the first byte of the member name itself | 2 964 180 / 2 964 219 / 2 964 263 | §3.2's `BLE`/`SIMPLERA`/`GUARDIAN` census and §11's partition |
>
> **The delta is 4: `len("o.G.")`.** And the *span width* matters as much as the
> frame: a "member read" spans `len("o.G." + MEMBER)` — 7 bytes for `.BLE`, 12 for
> `.SIMPLERA` and `.GUARDIAN`. Build that span any narrower — say `site..site+3`, the
> length of the token `BLE` — and the token at `site+4` falls outside it, and the
> §3.2 partition comes out **4 + 0 + 48** and **34 + 14** instead of the published
> **4 + 1 + 47** and **34 + 13**. **The published numbers are the correct ones**,
> because a member read *is* `o.G.<MEMBER>`, but the rule that selects them was
> undeclared until now, and a re-runner joining this log's own two tables got a
> different answer.

The single consumer, read in full — **bytes 2 964 111 – 2 964 344** inclusive, 234 B,
which is the whole `(0,a.n)(({deviceFamily:p})=>{…})` expression:

```js
(0,a.n)(({deviceFamily:p})=>{
  const F=null==p?void 0:p.startsWith(o.G.BLE),
        T=null==p?void 0:p.startsWith(o.G.SIMPLERA),
        v=null==p?void 0:p.startsWith(o.G.GUARDIAN);
  return F||T||v?this.userService.getUploadDeviceInfo(A):(0,e.of)(null)
})
```

### 3.2 Case-sensitive token census — every occurrence read

| token | cs | ci | ci/cs | reading |
|---|---|---|---|---|
| `BLE_X` | **2** | 2 | 1.0 | both are the declaration's key and value. **0 reads** |
| `SIMPLERA_X` | **2** | 2 | 1.0 | both are the declaration's key and value. **0 reads** |
| `BLE` | **52** | 3 169 | 60.9 | see below |
| `SIMPLERA` | **6** | 6 | 1.0 | 4 in the declaration, **1 read** at 2 964 219, 1 near-miss at 2 136 604 |
| `GUARDIAN` | **3** | 12 | 4.0 | 2 in the declaration, **1 read** at 2 964 263 |
| `NGP` | **0** | 94 | — | cs is 0; all 94 ci hits are `ngP`/`ngp` inside unrelated identifiers (§3.4) |

The case-insensitivity control earns its place on `BLE`: 3 169 against 52 is a
**60.9×** noise multiplier, so "0 case-insensitive hits" would have been a
meaningless claim and "0 case-sensitive hits" is not. Read individually
(`census.txt` §E, all 52 windows committed):

- **4** are the declaration itself: the `BLE` key at 1 723 254 and its value at
  1 723 259, plus the two inside the `BLE_X` occurrences (1 723 264 / 1 723 271).
  **1** is the member read at 2 964 180. **47** are neither, and those 47 split into
  two different kinds of noise that this log previously reported as one:
  - **34 are substrings** of a longer identifier — `ENABLED` (5), `IS_POSSIBLE` (5),
    `NOT_AVAILABLE` (4), `DATA_TABLE` (3), `DISABLED` (3), `DOUBLE_ZERO` (3),
    `INELIGIBLE` (3), `TABLE` (2), and `CDK_TABLE`, `NO_DATA_AVAILABLE`,
    `PUMP_DISABLE_REMOTE_BOLUS`, `TABLETS_RE`, `VIRTUAL_SCROLLABLE`,
    `VISIBLE_RANGE` (1 each). **Counting rule:** a hit is a substring when the
    maximal `[A-Za-z0-9_$]` run containing it is longer than the token, so
    `TABLETS_RE` counts once, under its own identifier, and not again as `TABLE`.
    These are summed in `census.txt` §E and total **34**.
  - **13 are standalone `BLE` tokens** — the maximal run *is* `BLE` — and they are a
    **third, unrelated sense of the same three letters**: `BLE` abbreviates
    Bluetooth Low Energy inside a **debug-log event catalogue**, whose records carry
    the shape `{type:…, label:…, severity:…, description:…}` and which is grouped
    into **three** arrays by log source. **The hits do not belong to one of them:**

    | group header | its own array | entries | of the 13 |
    |---|---|---:|---:|
    | `source:"sensor", label:"Sensor Traces"` @3 314 760 | 3 314 809 – 3 318 475 | 33 | **11** |
    | `source:"pump", label:"Pump Diagnostic Logs"` @3 318 479 | 3 318 533 – 3 320 922 | 20 | **1** |
    | `source:"app", label:"Mobile App Logs"` @3 320 926 | 3 320 974 – 3 322 899 | 17 | **1** |

    All 13 are a `label:` or a `description:` value: **6 `label:`** (`"BLE Param
    Update"`, `"BLE Param Update Complete"`, `"BLE Pair Request"`, `"BLE Key
    Exchange"`, `"BLE Key Received"`, `"BLE Connection"`) and **7 `description:`**
    (`"BLE connection parameters updated"`, `"BLE connection parameter update
    completed"`, `"BLE GAP pairing request"`, `"BLE GAP key exchange"`, `"BLE GAP
    key received"`, `"BLE long term key event"`, `"BLE connection parameter
    update"`). Same token, different sense, same file. A pass that counted `BLE`
    hits would have reported a 52-member surface.

> ⚠ **⚠ The span this section cited for the printed consumer, "bytes 2 964 176 –
> 2 964 322", bounded neither end.** The block starts **65 bytes earlier**, at
> 2 964 111, and ends **22 bytes later**, at 2 964 344. 2 964 176 is not the start of
> the code at all — it is the first `o.G.` **read** inside it. Same class as the
> span fault below: a bound that is neither a start nor an end is not a bound.

> ⚠ **⚠ This paragraph previously said "bytes 3 316 707 – 3 321 247 are the pump's
> Bluetooth debug-event catalogue", and that was wrong twice over.** The span is the
> span of **the 13 hits**, not the span of any catalogue — the first of them sits
> **1 898 bytes inside** the array it belongs to. And **only 1 of the 13 is the
> pump's**: 11 are `source:"sensor"`, 1 `source:"pump"`, 1 `source:"app"`. Calling a
> span that spans three owners by one of their names is `AGENTS.md` §6 item 5 — and
> it is F8's defect recurring verbatim, in the paragraph F8's own correction was
> written beside. It had also propagated into `docs/11` successor **(b)**, which
> proposes to enshrine it in the `docs/09` §4 register; both are corrected. The
> three-way split is re-derivable: `grep -o 'source:"[a-z]*"'` over each hit's own
> array.

> ⚠ **The enumeration above previously read "three hits … and **nine** more", which
> summed to 12 — one short of its own total.** The bytes give **6 `label:` + 7
> `description:` = 13**, so the word is **ten**. Corrected here because successor
> (b) proposes to enshrine this figure and its offsets in the false-positive
> register, where an off-by-one would propagate (`AGENTS.md` §6.5).

The arithmetic, so the split is checkable rather than asserted:
**52 = 4 (declaration) + 1 (member read) + 47 (other), and 47 = 34 (substrings) + 13
(standalone)**. An independent verifier re-derived all three numbers from the bytes
and reproduced them; see §11.

**The rule's scope, stated because it does not self-apply.** *Substring* and
*standalone* are defined here over the **47 hits in the "other" class** — the ones
that are neither in the declaration nor the member read. Applied to all 52 hits the
same rule gives **36 substrings / 16 standalone**, because the 4 declaration hits and
the 1 member-read hit are themselves standalone `BLE` tokens under it. Both splits
are correct on their own class; only one of them is the answer to "what noise is
this?", and that is the 47.

`SIMPLERA`'s near-miss at byte **2 136 604** is the one that would have produced a
wrong finding:

```js
this.isMinimedGoDevice=null==(gs=null==Dn?void 0:Dn.SIMPLERACC)?void 0:gs.includes(kn.split(",")[0])
```

`SIMPLERACC` (Simplera CGM) occurs **once** in the whole body and is a key of the
separate `deviceModelMapping` capability map, selected at 2 136 585 — a
**different axis** that shares a prefix. It is not a sixth enum member.

Lowercase `guardian` has 9 case-sensitive occurrences and **none** is the CGM
family: `guardianCumulusPeriodicAPI` (a config key, 93 819 and 2 189 123),
`report.settings.prefer.pump.data.over.guardian` (a translation key, 4),
`guardianParent` / `my_profile_edit_guardian_info` (a **human** guardian of a minor
patient's account). "Guardian" is two different things in this bundle.

### 3.3 Literal-vs-directive control (0 requests)

| literal | hits | why it must be present |
|---|---|---|
| `system.logbook.entry.validation.config` | 1 (byte 2 190 336) | route literal, area P recorded at main-bundle byte 2 768 979/2 769 017 |
| `deviceFamily` | 5 (first 2 964 121) | the destructured matcher parameter |
| `getUploadDeviceInfo` | 4 (first 2 963 710) | the branch's taken arm |
| `deviceModelMapping` | 7 (first 580 904) | the adjacent, different model axis |

All four **PRESENT**. The searcher resolves tokens in this body, so §3.2's zeros
are zeros.

### 3.4 A disagreement with a 2026-10-08 note, given rather than smoothed over

`findings-log/probe-2026-10-08/recov/PATIENT-APP-VOCABULARY.md:62-63` records that
the patient bundle's NGP search produced "three apparent matches … Samsung
user-agent strings", and `docs/09` §4 and `docs/05` repeat the figure. This pass
measures, on the digest-pinned 2026-10-13 build: **`NGP` case-sensitive = 0**. All 94
case-insensitive hits sit inside a longer identifier — **93** carry the letters `ngP`,
and **one** carries lower-case `ngp` (inside `bingpreview`) — in
`numberingPlan` / `pendingPageScroll` / `marketingParams`-class names. The
Samsung user-agent regexes *are* present (**17** `Samsung` occurrences, first at byte
2 240 566, last **starting** at 2 888 910 and ending at 2 888 916 inclusive — a
browser-sniffing library) — and none of them carries `NGP`.

> ⚠ **⚠ The word "every" was removed from the sentence above, not softened.** Round 2
> corrected the count beneath it and left the universal standing — *"**every one** of
> them the letters `ngP`"* — which its own next clause denied eight words later. A
> universal that its own sentence refutes is false, and `AGENTS.md` §1 says fix it or
> delete it. It is deleted: the claim that survives is the one that is true, namely
> that **all 94 sit inside a longer identifier**, and the 93/1 split is stated as a
> fact rather than as an exception to a rule that does not hold.

> ⚠ **The span's upper bound was wrong and is corrected above.** This section
> previously read *"bytes 2 240 566 – 2 888 911"*. The **count (17)** and the
> **lower bound** were exact; the upper bound matched neither reading available:
> the last occurrence **starts at 2 888 910**, and its 7-byte span **ends at
> 2 888 916** inclusive. A bound that is neither a start nor an end is not a bound.

Both readings are recorded. This pass does not claim the earlier figure was wrong;
it records that the figure does not reproduce as 3 on the build this pass names,
and that on this build the case-sensitive count is 0. **Neither `docs/05` nor
`docs/09` was edited on this point** — both are outside this lane, and the
difference is theirs to resolve.

---

## 4. The redundancy test — the shape of the negative

The one consumer applies, per read member, `value.startsWith(member)`, and takes the
CSR arm iff any is true. Truth table, computed by `census.txt` §J:

| wire value | `startsWith` BLE/SIMPLERA/GUARDIAN | same, with `_X` members deleted | verdict |
|---|---|---|---|
| `BLE` | true | true | read — the code names it |
| **`BLE_X`** | **true** | **true** | **inert: removing it changes no arm** |
| `SIMPLERA` | true | true | read — the code names it |
| **`SIMPLERA_X`** | **true** | **true** | **inert: removing it changes no arm** |
| `GUARDIAN` | true | true | read — the code names it |

`"BLE_X".startsWith("BLE")` is already true, so the suffixed value lands on the same
arm as its base token **for every input**. Two consequences, stated at the strength
the evidence carries:

- The suffix is **not a transport axis at this call site**. The branch's
  consequence is real and is a transport decision — `getUploadDeviceInfo(A)` POSTs
  to the URL the public config supplies as `csr.cumulus.periodic.data.endpoints.display_message`
  (function at byte **3 373 390**, `display_message` destructured at byte
  **3 373 507**; `findings-log/2026-10-12-published-pointers/FINDINGS.md` §3 maps it
  to `clcloud … /connect/csr/v2/display/message`), against `(0,e.of)(null)` —
  but that decision is made on the **base** token and does not distinguish the
  suffixed values. **OBSERVED** in the digest-pinned bundle.
- The suffix is **not a model axis at this call site** either. The model axis in
  this corpus exists and is nearby — `deviceModelMapping` (byte **580 904**) with its
  `StandaloneCGM` (byte **2 136 000**) and `SIMPLERACC` (byte **2 136 604**) keys —
  but it is keyed by model and its keys are **not** members of this enum. **OBSERVED.**

---

## 5. What this pass does *not* decide

- **That the suffix is meaningless — and one reason not to read it that way.** This
  repository holds a note from 2026-07-21 stating that the bridge detects
  `deviceFamily === 'BLE_X'`
  (`findings-log/medtronic-carelink-2026-07-21/05-official-docs-matrix.md` line 88).
  That is **not** a read of the bridge's source — it is an unattributed note with no
  `file:line`, so it is the weakest thing in this log and is cited only for what it
  bears on: **the suffix has at least one consumer outside the vendor's own client.**
  A vendor app that declares a member it never reads, and a third-party client that
  reads it as a distinct value, is a coherent shape — the declaration may exist to
  *name* a value for consumers rather than to branch on it. This pass does not
  measure that and does not adopt it; it is recorded so the negative in §1 is not
  over-read.

- **Whether `_X` carries meaning on the wire.** Still open, and unchanged by this
  pass. The discriminator's values arrive from `POST /patient/v2/monitor/data`
  (byte **3 372 491**; the route is already recorded as live and POST-only at
  `docs/06` §patient-api-surface), and this project does not make that call. Both
  readings the row lists — a semantic suffix, or a build/A-B discriminator — remain
  available, and the corpus is silent on which. **INFERRED that the corpus is
  silent; not OBSERVED that the suffix is meaningless.**
- **Whether the value is server-originated.** `getDeviceFamily` overwrites the
  response's field with `sessionStorage.getItem("deviceFamily")` when present
  (byte **3 372 603**), already recorded at
  `findings-log/2026-10-14-area-s4-lazy-chunk-control-flow/FINDINGS.md` §6.4. So a
  client-side `deviceFamily` may be a previous session's value, which is a further
  reason a static read cannot settle the wire vocabulary.
- **The lazy corpus.** See §6.

## 6. The scope limit, in the words the row requires

This pass swept the **eager main bundle only** — one file, 3 417 255 B.

> **0 reads in the eager main** is a true statement. **0 reads anywhere** is not
> one that can be made here.

Area K swept the 211 patient lazy chunks for *pointer* tokens, not for `_X` reads,
and did not sweep them for module `45559` at all. The negative is scoped to the
artefact this pass names. The patient lazy corpus is the successor that would close
it, and the candidate list for it is already committed and closed
(`findings-log/2026-10-13-area-v-pde-clients/chunks.txt`), so the sweep needs no
enumeration to be bounded.

## 7. The probe's own defect, disclosed

Run 1 wrote ledger rows 1–2 with `t_done` taken by the *caller* after `flock`
returned. Row 1 came out with `t_sent = 15:27:06.715Z` and `t_done =
15:27:06.137Z` — **a send-time later than its own completion-time**, which is
impossible, and a row whose `t_sent` therefore cannot carry a spacing claim. The
gap recomputed from run 1's stamps is **1.963 s**, below the declared 2.5 s.

**The same defect appears twice, and both instances are named here.** An
independent verifier found the second one, which §7 previously missed:

| # | where | what |
|---|---|---|
| 1 | `results.jsonl` seq 1 | `t_sent 15:27:06.715Z` later than its own `t_done 15:27:06.137Z` |
| 2 | `run.log`, run-1 block | the `run end:` stamp reads `15:27:09.116Z`, **earlier** than the `seq=2` line it encloses, stamped `15:27:09.621Z` |

Both are the same root cause — a stamp taken by the caller, after `flock`
returned, rather than by the process that sent. Nothing rests on instance 2: the
spacing claim is made from `results.jsonl` `t_sent`, and `run.log` is a
human-readable echo. It is recorded rather than tidied because the retraction
history is the evidence (`AGENTS.md` §3).

Rather than make the claim from a record known to be broken, both cells were
**re-sent** under a fixed instrument (`send.sh` now emits all four stamps from one
process, and `probe.sh` **refuses to write a row** whose stamp order is violated).
The re-issue is ledger rows **3–4**; both bodies came back **byte-identical** to
run 1 (`80c3fe2a…` and `0fb4fbd4…` respectively), so the defect cost two requests
and changed no result.

**The guard is demonstrated, not asserted — twice.** Both runs below are offline,
against a stubbed `send.sh`, and neither touches the network:

| run | stamps fed | outcome |
|---|---|---|
| violation | run 1's own triple (`lock 15:27:03.600Z`, `sent 15:27:06.715Z`, `done 15:27:06.137Z`) | `REFUSING TO LEDGER seq=1 — stamp order violated`; ledger **0 rows**, `tags.tsv` **0 rows**, violation line written to `run.log` |
| control | an in-order triple (`lock 15:30:48.139Z` < `sent 15:30:50.644Z` < `done 15:30:50.723Z`) | **2 rows written**, both fields intact |

The control is the half that matters: a guard that refused everything would look
identical on the first row and would have made the pass unable to ledger at all.

**The spacing claim is made from rows 3–4.** Recomputed from `t_sent`:
**2.624 s**, floor 2.5 s, met. Row 1's defect is left in the ledger rather than
edited out.

## 8. Evidence table

All rows are OBSERVED in one artefact, the digest-pinned patient bundle
`0fb4fbd4…` / 3 417 255 B. Byte offsets are offsets **into that file**.

| claim | class | source |
|---|---|---|
| Corpus reproduced its pinned digest and byte length | OBSERVED | `results.jsonl` seq 4; `census.txt` §A |
| The anchor gate **refuses** a corpus that does not reproduce its pin (exit 3, no findings printed) | OBSERVED | §11, fired against a deliberately wrong body |
| Enum is 5 members, no comment, no sibling map, one export `G` | OBSERVED | `census.txt` §B, bundle bytes 1 723 196 – 1 723 341 |
| Module id `45559` occurs exactly twice → exactly one importer | OBSERVED | `census.txt` §C, bytes 1 723 196 / 2 962 721 |
| Exactly 3 member reads: `BLE`, `SIMPLERA`, `GUARDIAN` | OBSERVED | `census.txt` §D, bytes 2 964 176 / 2 964 215 / 2 964 259 |
| The imported binding `o` is used **only** as `o.G.<MEMBER>` — no alias, no bare pass-on | OBSERVED | §11 and `census.txt` §L, module `83644` bounded by webpack delimiter (2 962 630 – 2 965 093) |
| `BLE_X`, `SIMPLERA_X`: **0 reads** in this corpus | OBSERVED | `census.txt` §D, §E, §I |
| No bracket / iteration / spread / pass-on consumption shape | OBSERVED | `census.txt` §D (8 explicit shape sweeps: **7 return 0**; the 8th returns only the already-counted same-token false hit @198 638) |
| Byte 198 638 `o.G` is a different binding, not a member read | OBSERVED | `census.txt` §D window |
| The 52 `BLE` hits partition as 4 declaration + 1 member read + 47 other, and the 47 as **34 substrings + 13 standalone tokens** | OBSERVED | `census.txt` §E; re-derived from the bytes, §11 |
| Case-insensitivity is a 60.9× noise multiplier on `BLE` | OBSERVED | `census.txt` §F |
| `SIMPLERACC` is a `deviceModelMapping` key, not an enum member | OBSERVED | `census.txt` §H, byte 2 136 604 |
| The branch is a transport decision made on the **base** token | OBSERVED | `census.txt` §D, §J; byte 3 373 390 |
| Deleting the two `_X` members changes no arm | OBSERVED (arithmetic over an OBSERVED predicate) | `census.txt` §J |
| Whether `_X` means anything **on the wire** | **INFERRED — open** | §5; needs authenticated `POST /patient/v2/monitor/data` |
| "0 reads anywhere" | **NOT CLAIMED** | §6 |

**Independence (AGENTS.md §2.1).** Every row above rests on **one** source: this
pass's own measurement of one digest-pinned file, plus the areas whose byte offsets
it reproduces (P, S4) — the same repository, so one source. **No claim here earns a
strength word**: everything this pass measures comes from one repository, so
`AGENTS.md` §2.1's independence count is 1 throughout, and the prose is written to
that count. §3.4's disagreement is recorded as two readings from two passes on two
captures, not as agreement.

## 9. Artefacts

| file | what |
|---|---|
| `FINDINGS.md` | this document |
| `probe.sh` | what was sent; resumable; asserts stamp order before writing a row |
| `send.sh` | one request under the shared per-host `flock`, sleep inside, 4 stamps |
| `results.jsonl` | 4 rows, one per request, `t_queued`/`t_lock_acquired`/`t_sent`/`t_done` |
| `run.log` | the same stamps per request |
| `headers/` | response headers. The re-issue reused run 1's tag names, so these are **run 2's** (rows 3–4); run 1's header files were overwritten. They carry `etag: W/"3424a7-659f36d017140"` and `last-modified: Wed, 26 Aug 2026 13:45:01 GMT`, byte-equal to the values recorded at `findings-log/2026-10-13-area-k-patient-chunks/results.jsonl` seq 2 — a **coherence** check (`AGENTS.md` §2.1: agreement, not multiplicity; same repository, same artefact, so no strength word is earned), not corroboration |
| `census.txt` | the full read: every occurrence of every token with offset, enclosing token, literal-vs-code and a 90-byte window; §D prints each shape sweep's **regex** beside its count, §L is the closure enumeration |
| `xsuffix-analyse.py` | the analysis; the census, the controls, the truth table and (§L) the closure enumeration. Offline, 0 requests; refuses to print past a failed anchor gate |
| `dup-test.sh` | the grep-first duplicate test, re-runnable, **printing the commit it counted at** and naming both tables that answer "the Closed table" (§10) |

## 10. The grep-first duplicate test, run and recorded

`CONTRIBUTING-research.md:196` requires a successor to be tested against
`docs/10-open-questions.md` §1, the Closed table and the page itself — **"grep
both first"**. Run 2026-10-15, **0 requests**. Counts are not verdicts, so each hit
is adjudicated below.

> **Every count in this section is bound to a commit, and the test is a script.**
> Re-run it: **`./dup-test.sh`**, which prints the SHA it counted at. Round 1 of this
> pass recorded bare counts and round 2 of verification found all three had gone
> stale **in the very commit that invalidated them** — this pass edited `docs/11` in
> six hunks and did not re-run or re-state them. Re-running and pasting new numbers
> would have fixed one instance of a bug that fires every time the page is edited,
> and it fires anyway, because four lanes in this pool edit `docs/11` at once.
>
> **Counts below are as of `3449e14bc0349c4e35b5f03342b701d1ed3ab267`** (this
> branch's head at the time of writing). The +2 over round 1 arrived with **that**
> commit, not this one — `git show 3449e14:docs/11-suggested-research-areas.md`
> piped through `grep -c 45559` already prints **9**, and the working tree prints
> **9** too — so **expect `docs/11` `45559` = 9, not the 7 recorded at round 1**
> (round 1's tree, `1e96ec2`, prints 7). Re-derive with `dup-test.sh` and cite the
> SHA it prints. **A count that names the tree it was taken on is re-derivable; a
> count that says "this branch's head" is a promise about a moving object**
> (`AGENTS.md` §1).
>
> **The per-hit verdicts below are the finding. The counts are evidence of where to
> look.** Verification round 2 re-derived every verdict; none of them moved, and none
> of them depends on a count staying still.

### The two tables that both answer "the Closed table"

`CONTRIBUTING-research.md:196` says "the Closed table" in the singular. **Two
tables answer that name and they disagree**, so both are tested explicitly and
neither is assumed:

| id | what it is | `45559` | `BLE_X` | `false-positive` | `Samsung` |
|---|---|---:|---:|---:|---:|
| **T1** | `docs/10-open-questions.md` §2, *"Searched and closed — do not re-run these"* | 0 | 0 | 0 | 0 |
| **T2** | `docs/11-suggested-research-areas.md` § *Closed areas*, the row table | 1 | 1 | 1 | 0 |

A test written against the bare placeholder `<Closed table>` cannot be re-run
without guessing which one was meant. `dup-test.sh` names both.

### (a) the patient lazy corpus, for module `45559` and `_X` reads

```
grep -c 45559 docs/10 section 1 (open questions)  -> 0
grep -c BLE_X docs/10 section 1 (open questions)  -> 1
grep -c 45559 T1 docs/10 section 2                -> 0
grep -c BLE_X T1 docs/10 section 2                -> 0
grep -c 45559 T2 docs/11 Closed areas             -> 1
grep -c BLE_X T2 docs/11 Closed areas             -> 1
grep -c 45559 docs/11 whole page                  -> 9
```

**Not a duplicate.** `docs/10`'s single `BLE_X` hit is row 37's *prescription* for
a future authenticated response — "the client's own comparison set (`BLE`, `BLE_X`,
`SIMPLERA`, `SIMPLERA_X`, `GUARDIAN`, `NGP`)" — not a proposal to sweep the lazy
corpus. The T2 hits are **not area R's own row**: both fall on the **area P** Closed-table
row ("recover the request schema from the vendor's own app, statically") — the row that
*proposed* this candidate, naming the `deviceFamily` enum and module `45559` as
"candidates for area R". Area R's own row contains neither token, so the grep found
the parent proposal, not a second one to sweep the corpus.

⚠ **The `docs/11` breakdown was wrong at round 1 and is corrected here.** The 7 then
recorded **summed to 8 under a heading of 7**, and at this commit the true count is
**9**. The partition at this tree:

| where | n |
|---|---:|
| area P's `docs/11` block (the byte-anchored declaration) | 1 |
| area P's `docs/11` Closed row | 1 |
| this area's successor-2 row (`Blocker:` line) | 1 |
| this area's successor-2 closed block, **including the §10 pointer added this round** | 6 |
| **total** | **9** |

None of the nine proposes the lazy sweep except successor (a) itself. T1, the other
table answering the same name, is **0** for both tokens — so on T1's reading this
successor is not merely non-duplicate, it is **unrecorded**, which is why it is
worth filing.

⚠ **One thing this grep surfaced, recorded rather than acted on:** `docs/10` row 37
prescribes matching a future value against that 6-member comparison set, two of
whose members this pass has just measured as unread in the eager main. That is
**not** a refutation of the row — `BLE_X`/`SIMPLERA_X` are unmeasured in the lazy
corpus, which is exactly what successor (a) would settle. It is why successor (a)
is worth running and why the row must not be read as settled by this pass.

### (b) the false-positive class, as offsets

```
grep -c false-positive   docs/10 whole file -> 0
grep -c "false positive" docs/10 whole file -> 1
grep -c false-positive   T2 docs/11 Closed areas -> 1
grep -c false-positive   docs/11 whole page  -> 1
grep -c BLE              docs/09 section 4 (the trap list) -> 0
```

**Not a duplicate, but the successor is narrowed by the grep.** `docs/10`'s one hit
is a *hostname* false positive (`carelink.medtronic.eu`), unrelated. T2's is **area
F**, which did this for a different token family (`timeline`) — so the deliverable
exists once, not twice.

The register itself already exists and is named: it is **`docs/09` §4 "The trap
list"**, whose rows carry Detail and Fix columns, and `docs/09` §5 item 2 is where
this class is already written up — it cites *this very token*: "the apparent
`ngp`/`guardian` matches … were zxcvbn dictionary noise (case-sensitive grep: 0
hits), and the patient bundle's three 'NGP' hits were Samsung user-agent strings."
⚠ **`docs/09` §4 currently has 0 occurrences of `BLE`**, so the `BLE`-shaped rows are
genuinely absent rather than duplicated — which is what makes successor (b) real
work and not a rewrite of something already there. Successor (b) is therefore
restated in `docs/11` as **adding the `BLE`-shaped rows and offsets to the existing
`docs/09` §4 trap list**, not as creating a new register. A successor that says "the
repo's own false-positive register" without naming it is the kind of claim that
turns out to describe nothing; naming it is what the grep bought.

### (c) the `NGP` figure that does not reproduce

```
grep -c Samsung docs/09 whole file                  -> 1
grep -c Samsung docs/05 whole file                  -> 1
grep -c Samsung docs/10 whole file                  -> 1
grep -c Samsung T1 docs/10 section 2                -> 0
grep -c Samsung T2 docs/11 Closed areas             -> 0
grep -c Samsung docs/11 whole page                  -> 3
```

**Not a duplicate.** `docs/09`'s hit *is* the claim in dispute
(`docs/09:236`, "the patient bundle's three 'NGP' hits were Samsung user-agent
strings"), and `docs/05:327` carries the same figure — both present in the bytes, so
§3.4's "docs/09 §4 and docs/05 repeat the figure" is accurate. ⚠ **`docs/10` also
carries one**, which round 1 of this pass did not report: row 38's "the patient
bundle's `N\d\d` tokens minify to Angular internals and a Samsung device regex". It
is **adjacent but not the same figure** — `N\d\d` tokens, not `NGP` — so it is named
here rather than folded into the disagreement, and the human resolving this should
see it. Both closed tables read **0**, so on either reading this disagreement is
recorded nowhere a future reader would meet it — which is precisely why it is
written down here rather than left to be rediscovered.

⚠ **`docs/11`'s count moved 2 → 3** between round 1 and this commit, because the
correction block above is itself inside the successor-2 block and contains the word.
This is the exact failure the SHA-binding above exists to make visible instead of
silent.

## 11. Re-derivation from the bytes, and two guards demonstrated

An independent verifier re-derived this pass's census from a **byte-identical**
copy of the corpus and found the prose wrong in three places — the `BLE` breakdown
(§3.2), the shape-sweep count (§3.1) and the §8 table. Those are corrected above.
What follows is what that re-derivation established, and the two assertions this
pass previously only *described*.

### The `BLE` split, re-derived: 52 = 4 + 1 + 47, and 47 = 34 + 13

Counting rule, so the split is checkable: a hit is a **substring** when the
maximal `[A-Za-z0-9_$]` run containing it is longer than the token, and a
**standalone token** when that run *is* the token. By this rule, `TABLETS_RE`
counts once, under its own identifier, and not again as `TABLE` — which is where
this pass's original list went wrong.

```
BLE cs total       : 52
  enum literal     :  4   [1723254, 1723259, 1723264, 1723271]
  member read      :  1   [2964180]
  other            : 47
    substrings     : 34
    standalone BLE : 13   [3316707 3316754 3316832 3316888 3317301 3317348
                          3317401 3317448 3317498 3317545 3317955 3320354 3321247]
```

### The consumer enumeration, closed by module boundary rather than by token

The global `\bo\.G\b` sweep counts **4** and stops there; one of the four is a
different module's function. Closing it properly means bounding the *module* and
enumerating every use of the imported binding.

**This is not a transcript of a reading — it is `census.txt` §L**, a mode of
`xsuffix-analyse.py` that runs against the digest-pinned body and prints all of it.
Verification round 2 found that the claim was previously labelled OBSERVED with no
artefact on disk that produced it, which is the one thing that makes a claim
un-re-derivable; the mode is the fix. Its output, verbatim:

```
  importing module id      : 83644
  module byte span         : 2962630..2965093  (2464 B)
  the import site          : 2962717  `o=i(45559),g`

  every identifier `o` in that module : 4
    member read      @2964176  'o.G.BLE),T=null='
    member read      @2964215  'o.G.SIMPLERA),v='
    member read      @2964259  'o.G.GUARDIAN);re'
    NOT a member read @2962717  'o=i(45559),g=i(1'

  module-level const/let/var `o` : []
  function parameters named `o`  : 0
  `i(45559)` sites in the WHOLE body : 1

  VERDICT: the binding is never aliased, never passed bare and never shadowed
  inside the module that imports it.
```

And the false hit, re-read **by module** rather than by token — which is what turns
a count into an adjudication:

```
  byte 198638 sits in module 8342 (bytes 191067..201118), which has its own
  'o=i(57707)' import at 191153
  — a different module's binding, same token, different sense.
```

So the binding is **never aliased, never passed bare, and never shadowed** inside
the module that imports it. With module `45559` exporting exactly one binding
(`G`), the enum object cannot leave module `83644` by any route this body
contains. This is a stronger closure than §3.1 argues, and it is why "0 reads" is
not a sampling result.

⚠ **The module span is `2 962 630 – 2 965 093` inclusive**, as `census.txt` §L
prints. An earlier draft of this section said `…094`, which is the exclusive end.
The verifier read the exclusive end; both describe the same span, and §L is the
authority.

### The anchor gate's failure branch, fired

Previously described, not exercised. Now run three times against deliberately
wrong bodies — **offline, 0 requests**, exit codes and byte counts as measured:

| case | body | stdout | exit | stderr |
|---|---|---|---|---|
| A — right length, **one byte flipped** (isolates the digest check) | 3 417 255 B, sha `6b987037…` | **499 B** — the §A gate block only, ending `…MISMATCH` | **3** | `FATAL: anchor gate failed — stopping` |
| B — truncated (isolates the length check) | 100 B | **498 B** | **3** | same |
| C — control, the pinned corpus | 3 417 255 B, sha `0fb4fbd4…` | 322 lines, all sections | **0** | — |

Case A is the one worth having: with the length still matching, a gate that
compared lengths alone would have passed it. `grep -c 'MEMBER-READ\|member
reads\|BLE_X'` over case A's stdout returns **0** — no finding leaks past a failed
gate, which is what §0 claims when it says the analyser "refuses to print anything
else".

### The stamp-order guard, fired twice

See §7 — a violating stamp triple yields `REFUSING TO LEDGER` and **0 rows
written**, and the in-order control writes **2**. Both offline against a stubbed
`send.sh`.

## 12. `downstream-bridge`: the decision, and the constant it turns on

`AGENTS.md` §3: *"When a finding changes a value the bridge pins — the discovery
pin, `BLE_API_VERSIONS`, **the family vocabulary**, the error taxonomy — the
finding is incomplete until the consumer knows."* §5 of this log is also evidence
that a non-vendor consumer reads `BLE_X` at all. So the question is not whether to
look, but whether a pinned constant moves. **I have decided it, below, with the
constants named.**

| pinned constant | moves? | why |
|---|---|---|
| `BLE_API_VERSIONS` | **no** | a BLE firmware version axis; this finding is about a `deviceFamily` *enum member*, in one bundle, at one digest. No version list is touched |
| discovery pin | **no** | `regression/hurl/01-discovery-pin.hurl` asserts JSON pointers into the discovery document. Untouched by this PR (0 files changed) |
| error taxonomy | **no** | no status code, error type or retry rule is claimed or altered |
| **family vocabulary** | **this is the one to examine** | see below |

**The family vocabulary is the constant that moves, and it is not a value change
but a *consumption* change.** Before: "the client matcher enum, 5 members",
propagated at `docs/05:498`, `docs/05:536-537` and `docs/10` row 37's 6-member
comparison set. After, **in the eager main only**: 5 declared, **3** matched by
`startsWith` (`BLE`, `SIMPLERA`, `GUARDIAN`), with `BLE_X` and `SIMPLERA_X` read
nowhere in that artefact. A bridge that built a matcher from the declared five
would be no worse off — `"BLE_X".startsWith("BLE")` already holds, which is the
inertness this pass measured — so **no bridge behaviour is wrong today**.

**But the reasoning is only as good as its scope, and the scope is the eager
main.** §8 records `"0 reads anywhere"` as **NOT CLAIMED** — a claim never made, so
there is nothing here for a later pass to falsify; what a later pass can falsify is
§6's scope limit. A bridge reading `BLE_X` (§5's note) is consistent with a consumer
outside this corpus.

> **My decision: this is a downstream-relevant finding, and it is NOT a stop
> condition for this merge.** No pinned value is demonstrated to have moved, and the
> consumption change is one that provably cannot alter a correct matcher.
>
> **The `downstream-bridge` trigger did not fire, so no issue is owed.** Round 2 of
> this pass wrote that the orchestrator *would* open a `downstream-bridge` issue.
> **That was a promise about an artefact that was never going to exist** — the same
> class as round 2's other blocking finding, and `AGENTS.md` §1's: a claim you cannot
> point at is a claim you delete. The owner has ruled that `AGENTS.md` §3's trigger
> **does not fire**, and the ruling is right, on this pass's own evidence:
>
> §3 fires *"when a finding changes a value the bridge pins"*. **No value changes
> here.** The family vocabulary's **values** — `BLE`, `BLE_X`, `SIMPLERA`,
> `SIMPLERA_X`, `GUARDIAN`, `NGP` — are exactly as they were and as this pass found
> them. What moved is a **consumption** fact *about the vendor's own client*: five
> declared, three matched. A bridge that built its matcher on the declared five is
> **no worse off, and arguably safer**, because `"BLE_X".startsWith("BLE")` already
> holds — so no matcher this pass measured can be wrong. An independent verifier
> re-derived that reading from the consumer's own bytes (2 964 111 – 2 964 344, the
> three `startsWith` arms and the branch they feed) rather than taking it from this
> log. **A notification about a value that did not change would be noise, and
> `AGENTS.md` §5 wants a pinned constant named — so there is no pinned constant to
> name.**
>
> **What I have and have not done.** I have **not** opened a `downstream-bridge`
> issue, and I am not going to: this pass is not authorised to open issues, and
> `AGENTS.md` §11 forbids automation writing the record. **No issue will be opened,
> because the trigger has not fired.** The state is re-derivable and was checked
> rather than assumed:
>
> ```
> gh issue list --label downstream-bridge --state all
>   -> #29 [CLOSED] "finding: bgUnits and glucoseUnitsDefault disagree in 30
>      countries, not 2 — a bridge reading one key mis-scales glucose"
>      (closed 2026-10-12)  — unrelated to this pass; none for #132
> gh issue view 132 --json labels
>   -> labels: research-area, claimed, automation      (no downstream-bridge)
> ```
>
> **A `downstream-bridge` issue would be owed only if a later pass finds a pinned
> value moving** — which is successor (a)'s clause below, and nothing more.

**What successor (a) would change, precisely — and what it would not.** If the 211
lazy chunks contain an importer of module `45559`, then two things follow and they
are *not* the same thing:

| | changes? | why |
|---|---|---|
| the **matcher-correctness** conclusion | **no** | §4's arithmetic is a property of the *predicate* `value.startsWith(member)`, not of the corpus size. `"BLE_X".startsWith("BLE")` holds whether the read set is 3 members or whether a second call site also reads `BLE_X`. A lazy importer reading `BLE_X` would make the declaration **load-bearing**, not the matching **wrong** |
| the **disclosure** obligation | **yes, and this is the real consequence** | ⚠ **§6's *scope limit* would be falsified, not a claim** — §8 records `"0 reads anywhere"` as **NOT CLAIMED**, and a never-made claim cannot become false. What changes is the *warrant*: "0 reads **in the eager main**, and the lazy corpus was swept" would stop being true. The §10(a) note about `docs/10` row 37 would harden from "unmeasured" to "refuted", and the six-member comparison set on that row would need correcting alongside `docs/05` |

So a successor (a) hit **does not by itself stop the merge**; it converts an
**unmeasured** question into a **measured** one and hands a second correction to
the same human who owes `docs/05` and `docs/09` the `NGP` figure. It becomes a
stop condition only if it also shows a bridge-relevant pinned value moving — which
is a separate finding from this one, and is not implied by an importer existing.

## Correction (2026-10-15)

**Verification round 1 returned NOT CLEAN on five findings. All five are fixed
here and in `docs/11` / `docs/05`. The central claim was not in question and is
unchanged; what moved were three numbers, one page's internal consistency, and two
absent records.**

1. **§3.2's `BLE` breakdown was wrong, and its own committed table said so.**
   This log read "**47** are substring coincidences" and "**12** of those 47 are a
   third, unrelated use". Measured: the 52 hits are **4** in the enum literal +
   **1** member read + **47** other, and the 47 are **34 substrings + 13 standalone
   tokens** — so 47 was the *other* total rather than the substring count, and the
   Bluetooth-sense count is **13**, not 12. `census.txt` §E lists 13 rows with
   `ident='BLE'`; the prose under-counted the file it cites. The per-identifier
   list also named `DISABLE` for `DISABLED`, omitted `TABLETS_RE`, and carried
   parentheticals that disagreed with the per-identifier counts (INELIGIBLE 2↔3,
   DATA_TABLE 4↔3, TABLE 3↔2). Corrected in place with the counting rule now
   stated (§3.2, §11).
2. **The shape-sweep count contradicted `census.txt` §D.** §8 read "8 explicit
   shape sweeps, **all 0**"; the table shows the 8th returning `1 hit(s)
   @[198638]`. Seven are 0; the eighth returns only the already-counted
   same-token/different-binding false hit. The substantive claim (no consumption
   shape) was never in doubt — the *number* did not match its own source. Fixed in
   §3.1, §8 and `docs/11`.
3. **`docs/05` contradicted itself, in the one file this PR opened to fix exactly
   this claim.** §87-88 said "only three are passed to it" while §416, §498 and
   §537 still said five. All three now carry the correction *beside* the original
   wording — §416 and §537 in place, §498 **outside** the blockquote, because that
   table is area R's preserved audit and editing inside it would destroy quoted
   history (`AGENTS.md` §3).
4. **`downstream-bridge` was silent.** Decided and recorded in §12, with the four
   pinned constants named and checked one by one. **It is not a stop condition for
   this merge** — no pinned value is demonstrated to have moved, and the change is
   one that provably cannot alter a correct matcher — but the family vocabulary is
   owed to the consumer before a bridge release, and successor (a) could widen the
   scope in a way that *would* stop the merge.
5. **The grep-first duplicate test (`CONTRIBUTING-research.md:196`) was nowhere
   recorded.** Run for all three successors in §10, with the commands, the counts
   and a per-hit verdict. It found no duplicate, narrowed successor (b) to name
   the register it means (`docs/09` §4, which already cites this token), widened
   successor (c) to name `docs/10` row 38 as adjacent-but-distinct, and surfaced
   that `docs/10` row 37 prescribes a 6-member comparison set two of whose members
   this pass measured as unread in the eager main.

Two guards this pass previously only *described* were then **fired** rather than
asserted (§11, §7): the anchor gate's failure branch, against a body with the
**right length and one flipped byte**, which exits 3 and prints no finding past
the gate verdict; and the stamp-order guard, which refuses on a violating triple
(0 rows) and writes 2 rows on an in-order one.

**Scope unchanged and still stated wherever the negative appears:** the eager main
bundle only. "0 reads in the eager main" is true; "0 reads anywhere" is not a claim
this pass can make.

## Correction (2026-10-15) — round 2

**Verification round 2 returned NOT CLEAN on two blocking findings and nine
advisories. The central claim was re-derived again, from the bytes:
module `83644` bounded to 2 962 630–2 965 093, four bare `o` identifiers (three `.G`,
one the binding itself), no module-level `o`, zero parameters named `o`, and
`i(45559)` at exactly one site body-wide. The `docs/05` resolution was judged
correct. What follows is what moved — plus one deletion of mine that had not been
recorded, which is item 6 and is the reason this heading exists twice.**

**Blocking 1 — §12 asserted an action that had not occurred.** This log said the
`downstream-bridge` notification was *"Filed as `downstream-bridge` on issue #132's
follow-up"*. It had not been. `gh issue list --label downstream-bridge --state all`
returns only **#29** (closed, `bgUnits`, unrelated); **#132** carries
`research-area, claimed, automation`. That was a claim about an artefact that did
not exist — the `AGENTS.md` §1 failure — and it sat in past tense, which is the one
unacceptable answer. §12 is now present tense and first person, states plainly that
the issue **does not exist yet**, names who opens it (the orchestrator; this pass is
not authorised to open issues), and prints the two `gh` commands so the state is
re-derivable. Deciding *not* to block was within remit; recording the notification
as already filed was not.

**Blocking 2 — §10's counts went stale in the commit that invalidated them.**
Round 1 recorded `docs/11` counts of **7** / **2** / **2** for `45559` /
`false-positive` / `Samsung`. At the round-2 head they were **9** / **1** / **3**:
this pass edited `docs/11` in six hunks and did not re-run or re-state them. All
three reproduce at `1e96ec2` and none at head. **Re-running and pasting new numbers
was rejected**: four lanes in this pool edit `docs/11` simultaneously, so a count
over that page moves under this pass whether or not it touches it. Instead:

- **`dup-test.sh` now exists** and prints **the commit it counted at**, with an
  explicit warning that its own §10 pointer and any other lane's hunks will move
  the numbers. The §10 verdicts are unchanged and none depends on a count.
- **Every count in §10 is bound to a SHA**, and the rule is stated: *a count that
  names the tree it was taken on is re-derivable; a count that says "this branch's
  head" is a promise about a moving object* (§1).
- **The `docs/11` `45559` breakdown was also arithmetically wrong** — the 7 summed
  to 8 under a heading of 7. The real partition at this tree is **1 + 1 + 1 + 6 = 9**,
  now tabulated.
- **`<Closed table>` was ambiguous and is now named twice.** Round 2 found two
  tables answer that singular name and they **disagree**: `docs/10` §2 *"Searched
  and closed"* reads 0/0/0/0 for `45559`/`BLE_X`/`false-positive`/`Samsung`, while
  `docs/11`'s closed-areas table reads 1/1/1/0. Both are tested explicitly; the
  adjudication content was unaffected.

**F3 — the enumeration I corrected still summed wrong.** Having fixed "12" to 13, the
sentence read *"three hits … and **nine** more"* = 12. The bytes give **6 `label:` +
7 `description:` = 13**, so the word is **ten**; both lists are now printed in full,
because successor (b) proposes to enshrine this figure in the false-positive
register. The same finding noted the rule does not self-apply: applied to **all 52**
hits it yields 36/16, and it is applied to the **47** "other" hits. Both splits are
correct on their own class; §3.2 now says which is which.

**F4 — the 8th shape sweep was described by a pattern that returns 0.** The prose
said *"`o.G` followed by a comma or a semicolon"*; the pattern run is
`(?<![.\w])o\.G(?![\w.])`, and the character after `o.G` at byte 198 638 is `)`.
Reproducing it as described, `o\.G[,;]`, returns **0**. The count was right and the
hit was correctly adjudicated — `census.txt` **§L** now re-reads it **by module**:
byte 198 638 sits in **module 8342**, which has its own `o=i(57707)`. **`census.txt`
now prints `regex=` beside every sweep's label and count**, so the label can never
again be mistaken for the pattern.

**F7 — my strongest claim had no committed artefact.** The closure enumeration was
labelled OBSERVED with nothing on disk that produced it: `census.txt` ran A–K and
none of them closed anything. **`xsuffix-analyse.py` now has the closure mode
(`census.txt` §L)**, which bounds the importing module by its own webpack delimiters
and enumerates every use of the binding, alias and bare-pass-on included. §11 cites
it and prints its output. The module span is `2 962 630 – 2 965 093` **inclusive**;
an earlier draft of §11 said `…094`, the exclusive end.

**F6 — four cross-refs pointed at §10 for content in §11.** `:199`, `:379`, `:383`
and `:387` now name §11, and the module-row cite names both §11 and `census.txt` §L.

**F8 — the Samsung span's upper bound matched nothing.** It read *"bytes 2 240 566 –
2 888 911"*. Count (17) and lower bound were exact; the last occurrence **starts at
2 888 910** and its 7-byte span **ends at 2 888 916** inclusive. A bound that is
neither a start nor an end is not a bound.

**F11 — `docs/05:420` mis-characterised the sentence it corrects, and my stated
reason for leaving `:512` alone did not match this page's own practice.** `:416`
asserts no count at all, so calling it "an over-count" was wrong; it now invokes the
**declared-vs-matched** distinction. And the justification for editing outside the
area-R blockquote was post-hoc — I cited `docs/05:497`, `:515` and `:524` as
corrections sitting inside blockquotes, and **all three had been moved off those
lines by this PR's own edits**; two of them hold prose, not corrections. The outcome
was right and is unaffected. ⚠ **The pointer form is withdrawn and replaced by a
grep**, per round 3's finding that this lane had now shipped line pointers its own
edits invalidated three times:

```
# pre-pass (merge base ab28f58) — where the correction blockquote actually lives:
git show ab28f58:docs/05-devices-and-vocabulary.md \
  | grep -nF '⚠ **What is and is not pinned here, stated rather than left to be discovered.**'
#   472
# post-pass (current tree) — same blockquote, shifted by this pass's edits:
grep -nF '⚠ **What is and is not pinned here, stated rather than left to be discovered.**' \
  docs/05-devices-and-vocabulary.md
#   509   (a third match at 573 is this pass's own quoted prose — the self-slice;
#          the naive grep below counts it, which is why it must not be trusted)
```

**No count is recorded, on purpose** — the same lesson as §10's SHA binding: a
number over a page this PR keeps editing is a property of a tree, not a fact, and
round 3 caught three of my own. The specific instance that settles it needs no
count: **area R wrote a correction into its own audit blockquote** — *"⚠ **What is and
is not pinned here, stated rather than left to be discovered.**"* (merge base
`ab28f58`, line 472 — resolved by content, not position: the full sentence as a needle returns
exactly one line of `docs/05`, while a shorter needle returns two, the second being
this pass's own quoted prose. No head line number is reproduced here, because this PR
edits that file) —
so the reason for leaving that table verbatim is **the number being true**, not a
convention the page holds to.

**Successor (a) — one clause tightened.** §12 previously read "the answer changes and
the merge queue should stop", which invites the stronger reading that a found
importer falsifies the matcher conclusion. It does not. §4's arithmetic is a property
of the **predicate** `value.startsWith(member)`, not of the corpus: a second reader
of `BLE_X` would make the declaration **load-bearing**, not the matching **wrong**.
What a successor (a) hit changes is the **disclosure** obligation — §6's **scope
limit** is what stops holding (not a claim: `"0 reads anywhere"` is `NOT CLAIMED`, and
a never-made claim cannot become false), and `docs/10` row 37's six-member set goes
from "unmeasured" to "refuted". §12 now tabulates the two separately.

6. **A deletion of mine that had not been recorded here.** In round 1 I rewrote
   §3.4's *"**every one** of them the substring `ngP`"* — a claim that was **false**,
   broken by one lower-case `ngp` inside `bingpreview` — and recorded no Correction
   entry for it. Five of round 1's six deletions were covered; that one was not, and
   `scripts/research-checks.py` accepts *any* dated Correction heading as a licence
   for *any* in-place edit, deletions included, which is why it passed CI silently.
   A pre-existing property of the repo, not something this pass changed, and not
   fixed here — widening or re-scoping a gate check in the same PR the gate passed is
   a maintainer's decision (`docs/09` §4). **The deleted wording was:** *"94
   case-insensitive hits, **every one** of them the substring `ngP` inside
   `numberingPlan` / `pendingPageScroll` / `marketingParams`-class identifiers."*
   It is now *"93 as `ngP` and one as lower-case `ngp` (inside `bingpreview`)"*, and
   the correction is written beside the claim rather than over it.

**Scope unchanged and still stated wherever the negative appears:** the eager main
bundle only. "0 reads in the eager main" is true; "0 reads anywhere" is not a claim
this pass can make.

## Correction (2026-10-15) — round 3

**Round 3 re-derived the central claim and the closure enumeration a third time — the
latter by a *different* method, brace-matching module boundaries with the verifier's
own identifier definition, to the same answers — and `xsuffix-analyse.py` reproduces
`census.txt` byte-for-byte at exit 0.** It also re-derived F2's tense, F3, F4, F6, F8 and
F11's substance, and held up the successor-(a) clause against a real test: the
predicate `p.startsWith(o.G.BLE)` is code, and `"BLE_X".startsWith("BLE")` is a
property of `String.prototype.startsWith`, not of the three reads on disk.

**What follows is four blocking findings and two advisories. Three of the four are
the same failure this lane has now produced in three consecutive rounds — a claim
whose scope is wider than its evidence — and two of those three were in the sentences
I had just written while fixing the previous round's. That pattern is the reason each
entry below names the check, not just the correction.**

1. **A span that named one owner where there are three.** §3.2 said *"bytes
   3 316 707 – 3 321 247 are the pump's Bluetooth debug-event catalogue"*. **Only 1
   of the 13 hits is the pump's**: 11 are in `source:"sensor"` *"Sensor Traces"*
   (array 3 314 809 – 3 318 475), 1 in `source:"pump"` *"Pump Diagnostic Logs"*
   (3 318 533 – 3 320 922), 1 in `source:"app"` *"Mobile App Logs"*
   (3 320 974 – 3 322 899). The quoted span is **the span of the hits, not of any
   catalogue** — the first hit sits 1 898 bytes inside the array it belongs to. This
   is F8's defect recurring verbatim, **in the paragraph F8's own correction was
   written beside**, and it had propagated into `docs/11` successor **(b)**, which
   proposes to enshrine it in the `docs/09` §4 register. Both are corrected, and
   successor (b) now states that a register row must carry each hit's own group or no
   span at all. Re-derived with `grep -o 'source:"[a-z]*"'` over each hit's own array.
2. **A supporting citation whose targets had moved.** The F11 entry and `docs/05`
   both cited `docs/05:497`, `:515` and `:524` as corrections sitting inside
   blockquotes. **`:497` holds an R-5 scoping fragment and `:524` holds "One declared
   vocabulary is NOT admitted" — prose, not corrections** — and this round's own 34
   added lines had moved all three off what they cited. **The pointer form is
   withdrawn and replaced by a grep** in both places, and **no count is recorded**,
   because a number over a page this PR keeps editing is a property of a tree (§10's
   SHA-binding lesson, now applied to my own text). The instance that settles it needs
   no count: **area R wrote a correction into its own audit blockquote**, so the
   reason for leaving that table verbatim is that the number is *true*, not a house
   style this page holds to.
3. **A false universal, softened rather than removed.** §3.4 still read *"**every one**
   of them the letters `ngP`"* while its own next clause reported one hit as lower-case
   `ngp`. **The word is deleted.** What survives is the claim that is true: all 94 sit
   inside a longer identifier, 93 carrying `ngP` and one `ngp`.
4. **§12 promised an issue that will not exist.** Round 2 wrote that *"the orchestrator
   opens the in-repo `downstream-bridge` issue"*. **The owner has ruled that `AGENTS.md`
   §3's trigger does not fire**, and the ruling is right on this pass's own evidence:
   §3 fires *"when a finding changes a value the bridge pins"*, and **no value changes
   here** — the six family values are exactly as they were; what moved is a
   **consumption** fact about the vendor's own client, and a matcher on the declared
   five is no worse off since `"BLE_X".startsWith("BLE")` already holds. **There is no
   pinned constant to name, so there is no issue to open, and none will be.** §12 now
   states the decision, the reasoning and the verifier's independent re-derivation from
   the consumer's own bytes (2 964 111 – 2 964 344), instead of a promise. A
   notification is owed **only** if a later pass finds a pinned value moving.

   **Secondary, same cell:** §12 said `"0 reads anywhere"` *"would become false"*, but
   §8 records it as **NOT CLAIMED**. **A never-made claim cannot become false.** What
   successor (a) would falsify is §6's **scope limit** — the warrant behind the
   negative — not a claim. Corrected in both places.

**Advisories.** **Byte frame now declared once.** This log published two frames 4 apart
— *site* offsets 2 964 176/215/259 (`§3.1`, `§8`, `census.txt` §D and §L) and *token*
offsets 2 964 180/219/263 (`§3.2`, §11`) — and never said so. **Span width matters as
much as the frame**: a member read spans `len("o.G." + MEMBER)`, and building it
narrower (`site..site+3`) drops the token at `site+4` and yields **4 + 0 + 48** and
**34 + 14** instead of the published **4 + 1 + 47** and **34 + 13**. The published
numbers are right; the rule that selected them is now stated, in one table, at §3.1.
**A second span bounded neither end:** §3.1 called the printed consumer *"bytes
2 964 176 – 2 964 322"*, but the block runs **2 964 111 – 2 964 344** (234 B) — the
cited start is the first `o.G.` read *inside* it, not the start of the code. **F4
residue:** `census.txt` §D's 8th sweep still carried the old false **label**
`o.G, o.G;` beside the correct `regex=` column; the label now reads *"o.G bare (no
member)"*, so the two columns agree, and `census.txt` was **regenerated** rather than
hand-edited.

**Left deliberately unchanged, because fixing it here would be the wrong move.** The
pointer form in §12's propagation list (`docs/05:498`, `docs/05:536-537`) names
*prose anchors a reader navigates by*, not a proof the gate can check; the F11 case was
different because it was offered as **evidence for a rule**. And the 13-hits census
keeps **offsets, not spans**, because a span is what started this.

**Scope unchanged and still stated wherever the negative appears:** the eager main
bundle only. "0 reads in the eager main" is true; "0 reads anywhere" is not a claim
this pass can make.

## 13. Four things no round had audited — audited here

Round 3 listed these as *unaudited rather than passing*, which is the honest way to
say "nobody looked". Four answers, three of them narrow the pass's own claims.

### 13.1 Should a pinned assertion exist for the declared-vs-matched change?

**No — and not because the pin would be inconvenient, but because the suite cannot
express it.** `regression/hurl/05-public-config.check.sh` asserts against **JSON
configuration documents**: `https://carelink.minimed.eu/patient/v2/configuration/public`
(line 31), `…/patient/countries/settings` (292), and an HCP config (130). Its
family-vocabulary pin is therefore on the **map axis** —
`check "family count is 16"` over
`["personal.device.family.to.model.mapping"]` (89). The declared-vs-matched
distinction is about **bytes inside a JavaScript bundle**
(`/main.6595daf83bd6d4b1.js`, `application/javascript`, 3 417 255 B).

> **`grep -rc 'main\.6595daf83bd6d4b1' regression/hurl/` returns 0.** No suite in
> this repository fetches the client bundle at all. A pin for this finding would
> require a new suite that fetches a 3.4 MB minified bundle and asserts on token
> offsets — a different instrument with a different vendor-request budget, and
> `docs/09` §4 records that widening a gate in the same PR the gate passed is a
> maintainer's decision. **So: the absence of a pin is correct and is now reasoned
> rather than merely true.** The re-derivation path stands in its place — `census.txt`
> §B, §D, §E and §L, all reproducible from one digest-pinned body.

### 13.2 `probe.sh` and `send.sh`, read line by line

- **`set -u` with no `set -e` is deliberate**, and the file is right not to have it:
  `req()` signals by `return 8` (stamp-order violation, 119) and `return 9` (cap,
  105), and `probe.sh` must still attempt the remaining cell and still write its
  `run end:` line. With `set -e` the first refusal would abort the pass.
- ⚠ **A property worth recording, found by reading: `probe.sh`'s exit code does not
  report whether a cell was refused.** The last statement is the `run end:` `echo`, so
  the script exits **0** after a guard refusal — which is exactly what the §7 dry-run
  shows (2 refusals, `exit=0`, **0 ledger rows**). Anyone scripting this harness must
  read `run.log` or count ledger rows, **not** the exit code. Recorded here rather than
  "fixed", because changing the exit contract is a change to the instrument, not to a
  finding, and no request in this pass depends on it.
- **`send.sh` is the fix for §7's defect and holds:** `t_lock` at 24, `sleep` at 25,
  `t_sent` at 27 **immediately before** `curl` at 28, `t_done` at 30 — four stamps in
  one process, in order, with the sleep inside the shared lock. `probe.sh:115` asserts
  `t_lock < t_sent < t_done` **before** the row is written.
- **Caveat on this review:** the original reading was performed **without** `shellcheck`
  installed, so §13.2 started as a reading, not a lint. `shellcheck` **is** installed here
  (v0.10.0); a shellcheck pass is now added alongside the reading:
  `shellcheck probe.sh` exits **0** with no warnings, and `shellcheck dup-test.sh`
  exits **0** with no warnings (run on 2026-10-15, both files). The reading stands;
  the lint reproduces the hand-checked stamps rather than replacing them, and the
  §7 dry-runs still exercise the guard end to end.

### 13.3 Every byte offset §4 and §K cite, re-checked against the body

Twelve citations, each tested by asserting the offset lands **exactly** on the needle:

```
@198635 (0,o.G)((0,o.d)(  @580904 deviceModelMapping   @1723196 45559:
@2136000 StandaloneCGM    @2136604 SIMPLERACC           @2190336 system.logbook.entry.validation.config
@2962721 45559)           @3372206 getDeviceFamily(V){  @3372491 /patient/v2/monitor/data
@3372603 sessionStorage.getItem("deviceFamily")        @3373390 getUploadDeviceInfo(V){
@3373507 display_message:X
```

**12 of 12 land on the cited needle.** The three `docs/05` prose offsets the brief also
listed (`416`, `512`, `537`) are prose anchors rather than byte claims; `416` and `537`
are quoted verbatim in this log's §12 and in `docs/05`'s own corrections, and the table
row at `512` is quoted in the correction beside it, so none of the three is load-bearing
as a pointer.

**Forward-verification note.** No vendor fetch was reopened this round (zero budget), so
the twelve offsets were re-checked against this pass's already pinned artefact,
`census.txt` §§B–D, rather than against a fresh body: every entry in the list above is
present in that file at the cited byte, and `xsuffix-analyse.py` reproduces the census
from the digest-pinned body at exit 0 (see `## Correction (2026-10-15) — round 3`).
Items re-verified this round against that artefact: `@198638`, `@580904`, `@1723196`,
`@2136000`, `@2136604`, `@2190336`, `@2962721`, `@3372206`, `@3372491`, `@3372603`,
`@3373390`, `@3373507` (12/12).

### 13.4 What CI's green settles about this round's findings

**None of them, and the reason is uniform.** Not one is a citation to a missing *file*,
not one is a count the numbers check reads, and the append-only arm accepts *any*
dated Correction heading as a licence for *any* in-place edit. Concretely:

| round-3 finding | why the gate cannot see it |
|---|---|
| the 3-owner span (blocking 1) | the file exists and the number is a byte offset, not an assertion |
| the moved citations (blocking 2) | `docs/05:497` **is** a valid line — it just holds the wrong thing |
| the false universal (blocking 3) | prose, and a Correction heading already exists for that section |
| the promised issue (blocking 4) | nothing in the gate reads `gh` output |

**CI settles** that no credential or internal hostname entered the diff, that every
`[source: …]` path resolves, that the 217/431 counts still agree, that no pre-existing
dated log was deleted or rewritten, and that the live 05 suite passes. It settles
nothing about whether a sentence is true, a span owns what it names, or a promise is
owed. That is what the independent rounds are for, and it is why the three of four
blocking findings here were in prose rather than in anything the gate reads.


### 13.5 Shell environment

`shellcheck` is **installed**, v0.10.0 (on `PATH` as `shellcheck`); proof:
`shellcheck --version` exits 0 and prints `version: 0.10.0`. Probe results recorded
in §13.2: `shellcheck probe.sh` → exit 0, 0 warnings; `shellcheck dup-test.sh` →
exit 0, 0 warnings. The earlier §13.2 caveat was written under the (false)
assumption that `shellcheck` was absent; it is corrected above, while the
reading-based conclusion (stamps, exit-code contract) stands.
