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
sweeps at zero**. The 8th, `o.G` followed by a comma or a semicolon, returns
exactly **1** hit, and it is the row-198 638 false hit already listed above: a
*different* module's exported function, called. So no iteration, no
destructuring and no bracket read can be consuming a member without showing up in
the member-read table.

**Member reads: 3. Distinct members read: 3 of 5.** `BLE_X` and `SIMPLERA_X` have
**0 reads**.

The single consumer, read in full (bytes 2 964 176 – 2 964 322):

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
    **third, unrelated sense of the same three letters**: bytes 3 316 707 – 3 321 247
    are the pump's Bluetooth debug-event catalogue
    (`label:"BLE Param Update"`, `label:"BLE Pair Request"`,
    `description:"BLE long term key event"`, `type:"BleConnectionEvent"`, and nine
    more `label:`/`description:` values in the same
    `{type:…, label:…, severity:…, description:…}` records), where `BLE` abbreviates
    Bluetooth Low Energy. Same token, different sense, same file. A pass that counted
    `BLE` hits would have reported a 52-member surface.

The arithmetic, so the split is checkable rather than asserted:
**52 = 4 (declaration) + 1 (member read) + 47 (other), and 47 = 34 (substrings) + 13
(standalone)**. An independent verifier re-derived all three numbers from the bytes
and reproduced them; see §10.

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
measures, on the digest-pinned 2026-10-13 build: **`NGP` case-sensitive = 0**; 94
case-insensitive hits, and **every one** of them the letters `ngP` inside a longer
identifier — 93 as `ngP` and **one** as lower-case `ngp` (inside `bingpreview`) —
in `numberingPlan` / `pendingPageScroll` / `marketingParams`-class names. The
Samsung user-agent regexes *are* present (17 `Samsung` occurrences, bytes
2 240 566 – 2 888 911, a browser-sniffing library) — and none of them carries
`NGP`.

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
| The anchor gate **refuses** a corpus that does not reproduce its pin (exit 3, no findings printed) | OBSERVED | §10, fired against a deliberately wrong body |
| Enum is 5 members, no comment, no sibling map, one export `G` | OBSERVED | `census.txt` §B, bundle bytes 1 723 196 – 1 723 341 |
| Module id `45559` occurs exactly twice → exactly one importer | OBSERVED | `census.txt` §C, bytes 1 723 196 / 2 962 721 |
| Exactly 3 member reads: `BLE`, `SIMPLERA`, `GUARDIAN` | OBSERVED | `census.txt` §D, bytes 2 964 176 / 2 964 215 / 2 964 259 |
| The imported binding `o` is used **only** as `o.G.<MEMBER>` — no alias, no bare pass-on | OBSERVED | §10, module `83644` bounded by webpack delimiter (2 962 630 – 2 965 094) |
| `BLE_X`, `SIMPLERA_X`: **0 reads** in this corpus | OBSERVED | `census.txt` §D, §E, §I |
| No bracket / iteration / spread / pass-on consumption shape | OBSERVED | `census.txt` §D (8 explicit shape sweeps: **7 return 0**; the 8th returns only the already-counted same-token false hit @198 638) |
| Byte 198 638 `o.G` is a different binding, not a member read | OBSERVED | `census.txt` §D window |
| The 52 `BLE` hits partition as 4 declaration + 1 member read + 47 other, and the 47 as **34 substrings + 13 standalone tokens** | OBSERVED | `census.txt` §E; re-derived from the bytes, §10 |
| Case-insensitivity is a 60.9× noise multiplier on `BLE` | OBSERVED | `census.txt` §F |
| `SIMPLERACC` is a `deviceModelMapping` key, not an enum member | OBSERVED | `census.txt` §H, byte 2 136 604 |
| The branch is a transport decision made on the **base** token | OBSERVED | `census.txt` §D, §J; byte 3 373 390 |
| Deleting the two `_X` members changes no arm | OBSERVED (arithmetic over an OBSERVED predicate) | `census.txt` §J |
| Whether `_X` means anything **on the wire** | **INFERRED — open** | §5; needs authenticated `POST /patient/v2/monitor/data` |
| "0 reads anywhere" | **NOT CLAIMED** | §6 |

**Independence (AGENTS.md §2.1).** Every row above rests on **one** source: this
pass's own measurement of one digest-pinned file, plus the areas whose byte offsets
it reproduces (P, S4) — the same repository, so one source. Nothing here is
labelled *independently*, *corroborated* or *confirms*. §3.4's disagreement is
recorded as two readings from two passes on two captures, not as agreement.

## 9. Artefacts

| file | what |
|---|---|
| `FINDINGS.md` | this document |
| `probe.sh` | what was sent; resumable; asserts stamp order before writing a row |
| `send.sh` | one request under the shared per-host `flock`, sleep inside, 4 stamps |
| `results.jsonl` | 4 rows, one per request, `t_queued`/`t_lock_acquired`/`t_sent`/`t_done` |
| `run.log` | the same stamps per request |
| `headers/` | response headers. The re-issue reused run 1's tag names, so these are **run 2's** (rows 3–4); run 1's header files were overwritten. They carry `etag: W/"3424a7-659f36d017140"` and `last-modified: Wed, 26 Aug 2026 13:45:01 GMT`, byte-equal to the values recorded at `findings-log/2026-10-13-area-k-patient-chunks/results.jsonl` seq 2 — a **coherence** check (`AGENTS.md` §2.1: agreement, not multiplicity; same repository, same artefact, so no strength word is earned), not corroboration |
| `census.txt` | the full read: every occurrence of every token with offset, enclosing token, literal-vs-code and a 90-byte window |
| `xsuffix-analyse.py` | the analysis; the census, the controls and the truth table |

## 10. The grep-first duplicate test, run and recorded

`CONTRIBUTING-research.md:196` requires a successor to be tested against
`docs/10-open-questions.md` §1, the Closed table and the page itself — **"grep
both first"**. Run 2026-10-15, **0 requests**, against `docs/11` at this branch's
head. Counts are not verdicts, so each hit is adjudicated below.

### (a) the patient lazy corpus, for module `45559` and `_X` reads

```
grep -c 45559 docs/10-open-questions.md          -> 0
grep -c BLE_X docs/10-open-questions.md          -> 1
grep -c 45559 <Closed table>                     -> 1
grep -c BLE_X <Closed table>                     -> 1
grep -c 45559 docs/11-suggested-research-areas.md -> 7
```

**Not a duplicate.** `docs/10`'s single `BLE_X` hit is row 37's *prescription* for
a future authenticated response — "the client's own comparison set (`BLE`, `BLE_X`,
`SIMPLERA`, `SIMPLERA_X`, `GUARDIAN`, `NGP`)" — not a proposal to sweep the lazy
corpus. The Closed-table hits are **area R's own row** ("Two successors filed under
the area: read-side echo casing, and whether the `_X` suffixes mean anything"),
i.e. the parent this pass closes. `docs/11`'s 7 hits are area P's block (2), this
area's row and closed block (5), and area P's Closed row — none proposes the lazy
sweep except successor (a) itself.

⚠ **One thing this grep surfaced, recorded rather than acted on:** `docs/10` row 37
prescribes matching a future value against that 6-member comparison set, two of
whose members this pass has just measured as unread in the eager main. That is
**not** a refutation of the row — `BLE_X`/`SIMPLERA_X` are unmeasured in the lazy
corpus, which is exactly what successor (a) would settle. It is why successor (a)
is worth running and why the row must not be read as confirmed by this pass.

### (b) the false-positive class, as offsets

```
grep -c false-positive docs/10-open-questions.md -> 0
grep -c "false positive" docs/10-open-questions.md -> 1
grep -c false-positive <Closed table>            -> 1
grep -c false-positive docs/11                    -> 2
```

**Not a duplicate, but the successor is narrowed by the grep.** `docs/10`'s one hit
is a *hostname* false positive (`carelink.medtronic.eu`), unrelated. The Closed
table's is **area F**, which did this for a different token family (`timeline`) —
so the deliverable exists once, not twice. The register itself already exists and
is named: it is **`docs/09` §4 "The trap list"**, whose rows carry Detail and Fix
columns, and `docs/09` §5 item 2 is where this class is already written up — it
cites *this very token*: "the apparent `ngp`/`guardian` matches … were zxcvbn
dictionary noise (case-sensitive grep: 0 hits), and the patient bundle's three
'NGP' hits were Samsung user-agent strings." Successor (b) is therefore restated
in `docs/11` as **adding the `BLE`-shaped rows and offsets to the existing
`docs/09` §4 trap list**, not as creating a new register. A successor that says
"the repo's own false-positive register" without naming it is the kind of claim
that turns out to describe nothing; naming it is what the grep bought.

### (c) the `NGP` figure that does not reproduce

```
grep -c Samsung docs/10-open-questions.md -> 1
grep -c Samsung docs/09-methodology-and-oracles.md -> 1
grep -c Samsung <Closed table>            -> 0
grep -c Samsung docs/11                    -> 2
```

**Not a duplicate.** `docs/09`'s hit *is* the claim in dispute
(`docs/09:236`, "the patient bundle's three 'NGP' hits were Samsung user-agent
strings"), and `docs/05:327` carries the same figure — both confirmed present, so
§3.4's "docs/09 §4 and docs/05 repeat the figure" is accurate. `docs/11`'s two
hits are successor (c) itself. ⚠ `docs/10` row 38 is **adjacent but not the same
figure** — it concerns the patient bundle's `N\d\d` tokens ("minify to Angular
internals and a Samsung device regex"), not `NGP`, so it is named here rather than
folded into the disagreement, and the human resolving it should see it.

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
enumerating every use of the imported binding:

```
enclosing module of the importer : 83644, bytes 2962630..2965093 (2464 B)
every identifier `o` in it       : 4
   followed by `.G`              : 3   -> o.G.BLE | o.G.SIMPLERA | o.G.GUARDIAN
   anything else                 : 1   -> o=i(45559
module-level const/let/var `o`   : []
function parameters named `o`    : 0
i(45559) sites in the whole body : 1   [2962719]
```

So the binding is **never aliased, never passed bare, and never shadowed** inside
the module that imports it. With module `45559` exporting exactly one binding
(`G`), the enum object cannot leave module `83644` by any route this body
contains. This is a stronger closure than §3.1 argues, and it is why "0 reads" is
not a sampling result.

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
look, but whether a pinned constant moves. **Decided here, with the constants
named.**

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
main.** §6: "0 reads anywhere" is **not claimed**. A bridge reading `BLE_X` (§5's
note) is consistent with a consumer outside this corpus. So:

> **This is a downstream-relevant finding and it is NOT a stop condition for this
> merge** — no pinned value is demonstrated to have moved, and the consumption
> change is one that provably cannot alter a correct matcher. **It is, however,
> owed to the consumer before a bridge release**, because the *documented* basis
> for its family vocabulary (5 members) is now known to be the declared set rather
> than the matched set, and that correction is the kind that should reach a
> consumer before it reaches a release note. Filed as `downstream-bridge` on issue
> #132's follow-up, naming the family vocabulary and stating plainly that the
> scope is the eager main and that successor (a) may widen it.

If successor (a) finds an importer in the lazy corpus, **the answer changes** and
the merge queue should stop.

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
