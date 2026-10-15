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
the object passed anywhere as a whole **0** (beyond the row-198 638 false hit).
So no iteration, no destructuring and no bracket read can be consuming a member
without showing up in the member-read table.

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
| `NGP` | **0** | 94 | — | cs is 0; all 94 ci hits are `ngP` inside unrelated identifiers |

The case-insensitivity control earns its place on `BLE`: 3 169 against 52 is a
**60.9×** noise multiplier, so "0 case-insensitive hits" would have been a
meaningless claim and "0 case-sensitive hits" is not. Read individually
(`census.txt` §E, all 52 windows committed):

- **2** are the declaration's key and value; **2** more sit inside the two `BLE_X`
  occurrences; **1** is the member read at 2 964 180.
- **47** are substring coincidences in unrelated tokens — `ENABLED` (5),
  `NOT_AVAILABLE` (4), `DATA_TABLE` (4), `IS_POSSIBLE` (5), `TABLE` (3),
  `DOUBLE_ZERO` (3), `VISIBLE_RANGE`, `DISABLE`, `VIRTUAL_SCROLLABLE`,
  `INELIGIBLE` (2), `CDK_TABLE`, `NO_DATA_AVAILABLE`,
  `PUMP_DISABLE_REMOTE_BOLUS`.
- **12 of those 47** are a **third, unrelated use of the same three letters**: bytes
  3 316 707 – 3 321 247 are a Bluetooth-protocol debug event table
  (`label:"BLE Param Update"`, `"BLE Pair Request"`, `"BLE long term key event"`),
  where `BLE` abbreviates Bluetooth Low Energy. Same token, different sense, same
  file. A pass that counted `BLE` hits would have reported a 52-member surface.

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
case-insensitive hits, **every one** of them the substring `ngP` inside
`numberingPlan` / `pendingPageScroll` / `marketingParams`-class identifiers. The
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

Rather than make the claim from a record known to be broken, both cells were
**re-sent** under a fixed instrument (`send.sh` now emits all four stamps from one
process, and `probe.sh` **refuses to write a row** whose stamp order is violated —
the assertion was dry-checked against run 1's stamps and does fire). The re-issue is
ledger rows **3–4**; both bodies came back **byte-identical** to run 1
(`80c3fe2a…` and `0fb4fbd4…` respectively), so the defect cost two requests and
changed no result.

**The spacing claim is made from rows 3–4.** Recomputed from `t_sent`:
**2.624 s**, floor 2.5 s, met. Row 1's defect is left in the ledger rather than
edited out: the retraction history is the evidence (`AGENTS.md` §3).

## 8. Evidence table

All rows are OBSERVED in one artefact, the digest-pinned patient bundle
`0fb4fbd4…` / 3 417 255 B. Byte offsets are offsets **into that file**.

| claim | class | source |
|---|---|---|
| Corpus reproduced its pinned digest and byte length | OBSERVED | `results.jsonl` seq 4; `census.txt` §A |
| Enum is 5 members, no comment, no sibling map, one export `G` | OBSERVED | `census.txt` §B, bundle bytes 1 723 196 – 1 723 341 |
| Module id `45559` occurs exactly twice → exactly one importer | OBSERVED | `census.txt` §C, bytes 1 723 196 / 2 962 721 |
| Exactly 3 member reads: `BLE`, `SIMPLERA`, `GUARDIAN` | OBSERVED | `census.txt` §D, bytes 2 964 176 / 2 964 215 / 2 964 259 |
| `BLE_X`, `SIMPLERA_X`: **0 reads** in this corpus | OBSERVED | `census.txt` §D, §E, §I |
| No bracket / iteration / spread / pass-on consumption shape | OBSERVED | `census.txt` §D (8 explicit shape sweeps, all 0) |
| Byte 198 638 `o.G` is a different binding, not a member read | OBSERVED | `census.txt` §D window |
| 47 of 52 `BLE` hits are substrings; 12 are a Bluetooth-protocol debug table | OBSERVED | `census.txt` §E |
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