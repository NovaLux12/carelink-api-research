# Area AU — the 211 patient lazy chunks, swept on their emitted names for the INSTINCT tail and the `model-mapping` route

**Pass date:** 2026-11-11 · **Claim issue:** [#217](https://github.com/NovaLux12/carelink-api-research/issues/217)
**Branch:** `research/lau` · **Host:** `carelink.minimed.eu` (one host, GET only)
**Cap:** 225 · **Used:** 214 · **Ledger:** `results.jsonl` (214 rows, one per HTTP request)
**Harness:** `probe.sh` + `send.sh` (the sweep) · `derive.py` (corpus re-derivation) ·
`census.py` (per-body census) · `clock-proof.sh` (spacing-clock control, zero network)
**Outputs:** `hits.tsv` (211 rows) · `census-all.jsonl` (211) · `all-hits.tsv` (32) ·
`response-heads.tsv` (214: status, content-type, content-encoding, bytes, digest per request) ·
`lists/derived.txt` (211) · `lists/list-diff.txt` · `census-eager.json` · `clock-proof.txt` · `run.log`

## Verdict

**Negative on the question as posed, and positive on one thing the question did not
name.** No `7896` SKU-tail occurrence appears in the 211 lazy chunks fetched from
`carelink.minimed.eu`, and no chunk carries a `model-mapping` route literal. **But one
lazy chunk does carry a second, richer device-naming implementation** — the same
`mapDeviceModelName` the eager bundle defines, re-implemented with a `shortName` fallback
the eager version does not have.

| question | answer | class |
|---|---|---|
| Does any chunk carry `7896[0-9]` as a SKU tail? | **No.** 6 digit-anchored occurrences exist and **all 6 are in one zxcvbn password-dictionary word list**; `sku_like = 0` across all 211. | OBSERVED |
| Does any chunk carry a `model-mapping` route literal? | **No.** `model-mapping` is 0 in 211 bodies; the eager bundle (control 3) is the only body in this corpus that has it. | OBSERVED |
| Does any chunk call a `model-mapping` variant the eager bundle never names? | **No.** The one `deviceModelMapping` reference in the corpus is a **property read off a service** (`this.userService.deviceModelMapping`), not a route. | OBSERVED |
| `productName` / `marketingName`? | `productName` 4 hits in 2 chunks, all Angular `@Input()` template bindings for the **global header**; `marketingName` **0**. | OBSERVED |
| An INSTINCT-specific table? | **No.** `Instinct` (case-sensitive) is **0** across 211 bodies; the 4 insensitive hits are one zxcvbn list (`instinct`, `instincts`, `instinctive`, `instinctively`). | OBSERVED |
| A second naming path? | **Yes — `mapDeviceModelName` in chunk `7187.87daa49216a1a9ef.js`**, arity 1, with a `shortName` fallback. | OBSERVED |

**The census negative is qualified in one place and the qualification is the finding.**
A bare `7896` grep over this corpus returns 15 hits; **all 15 are digit runs in a
password-strength word list** (`1478963`, `789654`, `7896321`, `0147896325`, …) in
`8141.650c358996e4c19a.js`. The digit-anchored `7896[0-9]` returns 6, all of them inside
that same list. Not one has a hyphen or a `SKU-` prefix, and `SKU-` is **0 hits in all 211
bodies**. So the area's token needed *two* refinements to be a SKU test rather than a
number test, and both were measured rather than assumed (§4).

## Method — three controls first, each with an asserted digest

The run **aborts** (`exit 3`) rather than sweeping if any control disagrees. Without them a
zero over 211 bodies says nothing: it could be a broken matcher, a stale corpus or a wrong
URL form.

| # | path | asserted | result | what it proves |
|---|---|---|---|---|
| 1 | `/common.206e355a4a593fbd.js` | 200, 21 157 B, `de1f782d…` | **PASS** | a chunk known to exist, on the **emitted name**; also the control for the id→name defect |
| 2 | `/runtime.79e2f9040b1dad8f.js` | 200, 8 268 B, `0dfea208…` | **PASS** | the corpus is re-derived from **today's** `f.u`, not inherited |
| 3 | `/main.6595daf83bd6d4b1.js` | 200, 3 417 255 B, `0fb4fbd4…` | **PASS** | the **matcher-positive**: `Instinct` = 2 (non-zero) and `7896[0-9]` = 0 in the same body |

**Control 3's matcher test is the load-bearing one.** It requires `Instinct` non-zero *and*
`7896[0-9]` zero in one body, so the census is proven able to return both answers before it
is trusted to return one of them over 211 bodies. It also caught a real trap: a bare `7896`
census over the eager bundle returns **8 hits, every one an SVG path coordinate**
(`C151.607628,35.1487896`, offsets 208 163–210 459). The bare token is a coordinate
fragment on this corpus; only the digit-anchored form is a SKU test. Both are counted and
both are reported in `hits.tsv`, so the difference cannot be swallowed.

### The list is re-derived, not copied — and the committed list is wrong in one place

`docs/11` §AU carries the defect: the committed `chunks-swept.txt` uses the **id** form
`2076.206e355a4a593fbd.js`, which 404s, while `f.u` emits that chunk under the **name**
`common`. `derive.py` rebuilds the list from the runtime body fetched at seq 2 and asserts
the map is 1:1; the sweep uses **only** the derived list. The offline diff
(`lists/list-diff.txt`) measures the divergence rather than assuming it:

```
derived from f.u (today's runtime bytes) : 211
committed chunks-swept.txt               : 211
same SET                                 : NO
in f.u but not committed (1):  + common.206e355a4a593fbd.js
in committed but not in f.u (1):  - 2076.206e355a4a593fbd.js
```

**So the two lists differ by exactly one member, by name and not by content**, and this pass
swept the name that resolves. Area K's committed corpus is otherwise identical: **213 paths
are shared and 0 of 213 digests differ** — `7187` included, `117 821 B /
a0017511156d4b2fce6056ba24058865b1c220582962f14c71444b8c32544251` on both passes. The
corpus has not drifted in the six weeks between the two sweeps.

## Request accounting — 214 of a 225 cap

**GET only throughout:** literal `GET`, no `-X`, no `-d`, no POST, no OPTIONS, no token, no
cookie, no authentication, no wordlist, no DNS. One host, `carelink.minimed.eu`.
**3 controls + 211 cells = 214. Eleven unspent** — the reserve existed for a transport
retry, and no retry was needed: **214 of 214 requests returned 200**.

**All 214 bodies are `application/javascript`, all `HTTP/2 200`.** 184 were served `br`-encoded
and 30 with no `content-encoding` (curl decompressed either way — `--compressed` is mandatory on
this host). The 211 sweep bodies total **2 874 939 B**
(smallest 78 B, largest 828 225 B = `8141`) with **211 distinct sha256 digests, 0 duplicates,
0 fallbacks** — so no two cells are the same file and no cell is an error page. The three
controls add 3 446 680 B, for 6 321 619 B fetched in total.

**The small bodies are real stubs, not failures**, and this was checked rather than assumed:
the two 78 B bodies (`1361`, `9296`) are complete webpack runtime registrations —
`(self.webpackChunkocl=self.webpackChunkocl||[]).push([[1361],{21361:()=>{}}]);` — i.e. a chunk
that declares an empty module. A 196 B body in this corpus is an HTML 404 (area K pinned
`80c3fe2a…`); none of the 211 is that size, and all 211 carry `application/javascript`.

**Declared delay `sleep 2.5` inside the per-host `flock`**, the sleep and the curl both
inside it, one host for the whole sweep: **≥ 2.5 s between requests to the same host**, which
is the whole of this sweep's cadence.

### Spacing — asserted from the kernel body-mtime oracle, because the harness clock is broken

**Measured same-host floor 2.641 s by body mtime, 213 gaps, 0 under 2.5 s** (median 2.667 s,
max 3.270 s).

⚠ **The `t_sent` series is unusable on this run and that is proven, not asserted.** It reads
**30 gaps under 2.5 s** (minimum 1.789 s) and **26 rows where `t_done` precedes `t_sent`** —
a negative duration, physically impossible for a completed request. Rather than attribute
that to the known corrupt-`t0` class and move on, `clock-proof.sh` runs **the identical
nesting with zero network**: parent `date` → flock sub-shell → inner `date`, 200 trials,
no socket in the loop. It reproduces the defect:

```
trials: 200
trials with at least one inversion: 5
requests sent by this script: 0
VERDICT: clock NOT monotone in 5 of 200 trials with ZERO network involved — the ledger's
negative durations are a HARNESS artefact, not a request that went out early.
```

The clearest instance is a **backward jump of 0.804 s** between consecutive trials
(`22:42:52.923Z` → `22:42:52.119Z`, `clock-proof.txt:28`). Since `date` here loses ~0.8 s
with no I/O, a negative `t_done − t_sent` in the ledger is explained by the clock and
carries **no** information about request timing. So the spacing claim rests on `st_mtime_ns`,
the one timestamp in the ledger the harness does not write. `clock-proof.txt` is committed
so a reader can check this rather than take it.

## 4. The census — every token, three counts, over all 211 bodies

Totals across the 211 sweep bodies (`census-all.jsonl`, summarised in `hits.tsv`). `cs` =
case-sensitive, `ci` = case-insensitive control, `q` = inside a JS string literal.

| token | `cs` | `ci` | `q` | bodies | classification |
|---|---|---|---|---|---|
| `7896` | 15 | 15 | 0 | 1 | **all 15** zxcvbn word list, `8141` |
| `7896[0-9]` | 6 | 6 | 0 | 1 | **all 6** same word list; `sku_like` **0** |
| `SKU-` | **0** | 0 | 0 | 0 | — |
| `productName` | 4 | 4 | **4** | 2 | Angular `@Input()` on the global header |
| `marketingName` | **0** | 0 | 0 | 0 | — |
| `Instinct` | **0** | 4 | 0 | 0 | one zxcvbn list (`instinct*`) |
| `model-mapping` | **0** | 0 | 0 | 0 | — |
| `modelMapping` | 0 | 1 | 0 | 0 | substring of `deviceModelMapping` |
| `ModelMapping` | 1 | 1 | 0 | 1 | `this.userService.deviceModelMapping` |
| `deviceModelMapping` | 1 | 1 | 0 | 1 | the same property read |
| `configuration/system` | **0** | 0 | 0 | 0 | — |

**No token hit 300 hits, so no count was truncated** (`census.py` caps per-token hit capture
at 300 and flags a truncation in the row; none fired).

### 4.1 The `7896[0-9]` hits — six strings, one list, zero SKUs

All six are in `8141.650c358996e4c19a.js` at offsets 18 030 / 42 199 / 47 778 / 54 236 /
70 807 / 180 686, and every one sits inside a **pure digit run** (`in_pure_digit_run = 6`,
`sku_like = 0`): `789654`, `7896321`, `789654123`, `789632145`, `78963214`, `789632147`.
The context is a comma-separated password dictionary — `…luckydog,789654,pistol,whocares…`.
**A SKU tail never appears as a bare digit run**: the vendor's own key form is
`SKU-78963-01`, with a hyphen and a suffix. That is why `sku_like` is a separate column
rather than a note: it separates "a number that starts 7896" from "a SKU tail", and the
answer to the latter is zero.

**This is the same chunk and the same word list area K found for `discover` and `pde`**
(`findings-log/2026-10-13-area-k-patient-chunks/FINDINGS.md` §5) — `8141`, 828 225 B. So the
false-hit class is already on the record; what is new is that the area's own token lands in
it, which is why §4's control (bare `7896` vs anchored) had to be built before the sweep.

### 4.2 `productName` — 4 hits, quoted, all header chrome

`985.47eb741416e9cd44.js` (offsets 654, 1 040) and `2356.ce46b9bb18508690.js` (9 993,
11 364). Every one is an Angular `@Input()` binding on `mat-legacy-global-header`:
`("productName",t.bMT(1,3,"landing.csr.login-subtitle"))` and
`("productName",…"landing.app-name")`. **It is the string in the page banner, sourced from a
translation key — not a device name.** The distribution across the corpus explains it: these
are the two `app-csr-header` / `app-third-party-consent` chunks, and the eager bundle carries
the same binding.

### 4.3 No `model-mapping` route anywhere in the corpus — and what the one hit is

`model-mapping` is **0 occurrences in all 211 chunks**. The eager bundle holds it exactly
once, at byte 3 374 413, in
`getDeviceModelMapping(V){return this.http.get(`patient/configuration/system/model-mapping/${V}`)}`
— area AM's source, reproduced here as control 3. **No chunk names that route, and no chunk
names a variant of it.**

The single `deviceModelMapping` occurrence in the corpus is at `7187`, offset 83 219:
`this.deviceModelConfig=this.userService.deviceModelMapping` — **a property read off the
injected `userService`, resolved by a router `resolve` in the eager bundle**
(`this.userService.deviceModelMapping=this.route.snapshot.data.deviceModelMapping`, eager
byte 1 949 368, wired to the resolver `Gd` at eager byte 2 166 205 which is the thing that
calls `getDeviceModelMapping`). So the chunk **consumes** the mapping the eager bundle
fetches; it neither fetches it nor names a second route. OBSERVED as code; **liveness of
the route is not re-tested here** and is not claimed.

## 5. The positive — a second `mapDeviceModelName`, with a `shortName` fallback

`docs/11` §AU asked whether a chunk carries "a second, richer naming path". **One does.**
`7187.87daa49216a1a9ef.js` (117 821 B) re-implements `mapDeviceModelName` rather than
importing it, and its version differs from the eager one in three measured ways.

**Chunk 7187, offset 80 246 (arity 1):**

```js
mapDeviceModelName(t){var n;for(const a of Object.values(this.deviceModelConfig))if(a.hasOwnProperty(t)){const l=a[t];return(null==(n=null==l?void 0:l.features)?void 0:n.dataCalendar)||(null==l?void 0:l.shortName)||t}return t}
```

**Eager bundle, byte 581 725 (arity 2):**

```js
mapDeviceModelName(Ye,Nt){var Ht;for(const gn of Object.values(Nt))if(Object.prototype.hasOwnProperty.call(gn,Ye)){const gt=gn[Ye];return(null==(Ht=null==gt?void 0:gt.features)?void 0:Ht.dataCalendar)||null}return Ye}
```

| | chunk `7187` | eager |
|---|---|---|
| arity | 1 | 2 |
| config source | `this.deviceModelConfig` (bound at 83 184 to `this.userService.deviceModelMapping`) | parameter `Nt` |
| property test | `a.hasOwnProperty(t)` | `Object.prototype.hasOwnProperty.call(gn,Ye)` |
| **fallback chain** | `features.dataCalendar` → **`shortName`** → `t` | `features.dataCalendar` → `null` |

**The difference that matters is the middle row of the fallback chain.** The eager
implementation returns `null` when `features.dataCalendar` is absent; the chunk falls back to
`shortName` and then to the raw model code. So the chunk renders a label where the eager path
renders nothing — and this is the only place in the 211-body corpus where a `shortName` is
read at all (`shortName` is 1 hit, at chunk offset 80 449, inside this function).

**What this does and does not answer.** It is a **second implementation of the same naming
function**, richer in that one respect, and it was not visible from the eager bundle. It is
**not** a new name source: it reads the same `deviceModelMapping` document area AM fetched,
so it cannot name a code that document does not name, and it introduces no `7896x` string
(the chunk's `7896` count is 0). **INFERRED:** that this is a duplicated legacy path rather
than a distinct feature — the reasoning is that both implementations are in the shipped
patient app on the same route family and read the same document, and the assumption is that
no build-time transformation rewrites one into the other, which this pass did not test.
Whether the two are reachable on different routes is **not established**.

## 6. Limits, stated

- **One host.** `carelink.minimed.eu` only, per the brief. No claim is made about `.com` or
  `-trials` chunk corpora, and the 213/213 digest match with area K is for `.eu` bodies.
- **Bodies are not committed.** Digests, sizes and the census are; the bytes are not, so a
  reader can verify the population without being handed 2.9 MB of vendor code.
- **The `clock-proof` result is host-specific.** It proves `date` is non-monotone on this
  machine at this time, which is enough to disqualify the ledger's `t_sent` series here. It
  does **not** establish a cause, and no cause is asserted.
- **`mapDeviceModelName` reachability is unobserved.** The chunk is shipped and its function
  is complete; no request in this pass exercises it, and liveness is not claimed in either
  direction.
- **The zxcvbn classification is by context, not by parsing the word list.** Every one of the
  21 numeric/`Instinct` hits sits inside a comma-separated alphabetic run of the shape
  `word,word,789654,word` — the same shape area K classified for `discover`/`pde`. No hit was
  a quoted string (`q = 0` for every token in §4), which independently rules out a JS literal
  assignment.
