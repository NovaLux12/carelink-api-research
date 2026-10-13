# Area K — the 211 patient lazy chunks, swept for the discovery token set

**Pass date:** 2026-10-13 · **Claim issue:** #56
**Branch:** `research/k-patient-chunks` · **Ledger:** `results.jsonl` (215 rows, one per HTTP request)
**Harness (as sent):** `probe.sh` + `send.sh` (the sweep) · `probe-followup.sh` (one cell, §2)
**Offline, zero requests:** `runtime-map.py` · `extract.py` · `tables.py` · `spacing.sh` · `resolve.py`
**Outputs:** `chunks-swept.txt` · `verdicts.tsv` · `runtime-map.txt` · `grep-out.txt` · `tables.txt` · `spacing.txt` · `resolve.txt`

---

## Verdict

**A positive, on the one axis this area was filed to test — and it corrects the scope of
a published negative rather than the negative itself.**

Area V established that the shipped patient bundle **names**
`system.gc.gz.transition.flags`, defines a selector over it, exports it as `z2`, and
**reads it 0 times in the file**, while it *does* read and POST
`csr.cumulus.periodic.data.endpoints` from the same file. Stated in the corpus, that
negative is scoped to the eager bundle, and the scope was load-bearing at every use.

**Lazy chunk `6746.c6795ff7e9ff468d.js` reads it — twice, in two different modules, and
the value it reads flows into the URL that is then POSTed.** Both reads bind module id
**4265** (`_=o(4265)` at byte 577, `F=o(4265)` at byte 66107), and module `4265` is
**defined in the main bundle at byte 91298**, whose export table maps `z2:()=>be`, where
`be=(0,e.Mz)(f,gt=>gt.guardianCumulusPeriodicAPI)` and
`D.guardianCumulusPeriodicAPI="system.gc.gz.transition.flags"`. So this is not a
two-character alias collision — the identity is closed by **module id**, which is the
`AGENTS.md` §6 item 3 discipline applied to a minified export rather than to a hash.

> Area V's claim is **not retracted**. "`.z2` occurs 0 times in the main bundle" is
> **OBSERVED and re-measured here** (§4). What the sweep changes is which corpus the
> claim is about, and that is what a lazy chunk is for.

**The flow into the POST is settled on disk, not inferred.** Bytes **69458-69866** are one
unbroken run of `getMessageRequest`: `E=h.messageEndpoint` -> the M2M template ->
`y = ... E ...` -> `getPeriodicDataWithPost({reqUrl:y, ...})`. `resolve.py` prints the
whole run and asserts it (`resolve.txt` section C, A7). Settled at **zero requests** --
the captures were still on disk.

**Two secondary results, one of them a correction to a committed artefact.**

1. **The committed chunk list's URL form is wrong for exactly one entry.** `chunks.txt`
   carries `2076.206e355a4a593fbd.js`; the runtime's own `f.u` emits that chunk under
   the **name** `common`. The sweep requested the id, got a 404, and would have closed
   with a clean negative over 211 bodies in which one cell is a statement about a
   filename. Re-requested under the name the runtime emits, it resolves: **200,
   `application/javascript`, 21,157 B**. §2.
2. **`baseUrl` in the lazy chunks is not area V's CMS base at all -- it is a hard-coded
   patient API base**, `this.baseUrl="/patient/csr"` and
   `this.baseUrl="/patient/csr/safety/notice/definitions"`, carrying **19 method x
   path shapes across 16 distinct path templates in 7 chunks** — none of which appears
   in any `docs/` page. OBSERVED as code;
   **liveness unobserved in both directions** -- nothing was requested. This is the
   pass's **second positive**, and it was a measured token the first version of this log
   left in no table and no prose at all. Section 5.
3. **`patient-timeline` and `dialog-lite` stay at zero across all 211 chunks**, and the
   eager bundle's five `patient-timeline` hits reproduce area V's byte offsets exactly
   and classify as Angular component selectors. Area F's caller question is not
   answered — it is narrowed. §6.

**And the negative the area predicted, on the discovery document, holds in full: not one
of the 211 chunks carries a single discovery-document token.** §5.

---

## Request accounting

**215 of a 230 cap.** **GET only** throughout — literal `GET`, no `-X`, no `-d`, no
`--data`, no `-H`, no `Cookie`, no `Authorization`, no token, no authentication, no
port scan, no DNS lookup, no wordlist, **no `OPTIONS` and no `POST` of any kind**. One
host only: `carelink.minimed.eu`.

**Declared delay 2.5 s, sleep inside the per-host `flock`** — i.e. requests to the same
host were issued **2.5 s apart** by construction: `flock <lock> send.sh 2.5 …` is one
invocation per request and `send.sh` sleeps before it execs `curl`, so the gap is real
and not merely intended. `TS_SENT` is emitted inside the lock immediately before
`curl` execs, so `t_sent` is the instant the request left this machine.

**Measured spacing floor, two independent series** (`spacing.txt`; counting rule: one gap
per consecutive pair in request order, so 215 rows give 214 gaps — `docs/09` §4):

| series | n | min | max | under the declared 2.5 s | under the repo's `>=2 s` floor |
|---|---|---|---|---|---|
| **`t_sent`** (`date`, emitted inside the lock) | 214 | **1.835 s** | 35.622 s | 22 | **7** |
| **kernel body `st_mtime_ns`** (independent of the harness clock) | 214 | **2.636 s** | 35.615 s | **0** | **0** |

**The two series disagree, and the disagreement is the finding.** The `date` series
records **16 impossible negative request durations** (`t_done` earlier than `t_sent`) and
22 bodies written *before* their own `t_sent` — the corrupt-`t0` signature `docs/09` §4
records in areas B, X, Z, D and E. The kernel series, which no harness clock feeds,
shows **0 gaps under 2.5 s and 0 under the 2 s floor** across all 214, and **0 negative
gaps** — the same corruption check measured by the instrument that is not suspect.

**The two series are now compared gap by gap**, because the span comparison the first
version of this log used **could not fail**:

> **⚠ Correction (2026-10-13, verification round 1): the span "validation" was
> arithmetic, not evidence.** `spacing.sh` computed
> `harness = max(max(sends),max(mtimes)) − min(min(sends),min(mtimes))` against
> `kernel = max(mtimes) − min(mtimes)`, whose difference **telescopes to
> `mtime[0] − send[0]`** — the first request's own latency — and to nothing else. Every
> interior timestamp cancels, so it could not have detected a corrupted series short of
> total collapse. "Agreement to 0.274 s over a 10-minute run" was a number that could
> not fail, and this log cited it as validation.
>
> **Replaced by the per-gap comparison, which fires.** Across **214 gaps**:
> **max |send − mtime| = 0.873 s**, median **0.015 s**, and **20 gaps disagree by more
> than 0.5 s** — each named in `spacing.txt` with both figures (worst: `seq1` send
> 3.697 s vs mtime 2.824 s; `seq160` send 1.835 s vs mtime 2.655 s). Every disagreement
> is a `date` timestamp that moved. The span check is kept but **relabelled for what it
> is**: a two-endpoint consistency check with differing left endpoints (first `t_sent`
> → last `t_done` = 648.080 s, versus first write → last write = 647.799 s, difference
> **0.281 s** = first-row latency 0.274 s + last-row latency 0.007 s). It confirms only
> that both series agree about the run's extent, and says nothing about the gaps.

The two long gaps are both explained, reported from **both** series, and both are *over*
the declared delay rather than under it:

| gap | kernel | `date` | explanation |
|---|---|---|---|
| **seq 4→5** | **34.016 s** | 34.017 s | the harness restart described below |
| **seq 214→215** | **35.615 s** | 35.622 s | the sweep finishing and the one follow-up cell being issued (§2), during which four offline scripts ran |

> The first version of this log quoted **34.017 s** and **35.622 s** in the very
> paragraph that said it was reporting the kernel series. **Both figures came from
> `date`.** The kernel figures are 34.016 s and 35.615 s, and are the ones above.

> **Three defects in this pass, disclosed rather than smoothed over.**
>
> 1. **The harness was launched detached and died with its parent shell after 4 rows.**
>    Those 4 requests were real. `probe.sh` was therefore made **resumable** — it appends
>    to the ledger, continues the sequence from the highest `seq` present, and skips any
>    path already in the ledger. Truncating on start-up would have deleted the record of
>    requests already spent, which is how a pass under-reports its own budget
>    (`pool brief`: *"a ledger with fewer passes silently, which is the worse failure"*).
> 2. **`verdicts.tsv`'s `hits` column is a count over the CORE token set only**
>    (`baseUrl*` / `discover` / `clcloud` / `api/carepartner` / `pde` /
>    `system.gc.gz.transition.flags` / `patient-timeline` / `dialog-lite`). It is a
>    one-glance summary, **not** the census. The wider census — including the nine
>    `transition.flags` **leaves**, which is where this pass's positive came from — is
>    `grep-out.txt` and `tables.txt`. Reading the column alone would have shown
>    `6746…js → 0` and missed the finding.
> 3. **The 211 bodies (2.87 MB) and the 3.4 MB main bundle are deliberately not
>    committed.** What *is** committed is the full census with byte offsets, the
>    enclosing identifiers, the verdict table, and — since verification round 1 —
>    **`resolve.txt`, which resolves every cited offset to its enclosing webpack module
>    and prints the module span and the bytes on both sides.**
>    `body_mtime_ns` is recorded at **nanosecond** resolution in the ledger itself, so
>    unlike area V's `stat -c%Y` column the mtime series **is** re-derivable from the
>    committed artefacts — though the *files* it describes are not on disk in a clean
>    clone, since git does not preserve mtimes.
>
>    > **⚠ Correction (2026-10-13, verification round 1): the first version of this
>    > bullet said "Digests, sizes, **byte offsets**, verdict table and grep output are"
>    > committed. The byte offsets were committed only *inside this prose* — `4265`
>    > appeared in no committed artefact at all, and the six offsets carrying the
>    > identity argument (91298, 579, 66109, 22260, 70054, 69249) existed nowhere but
>    > in the paragraphs below. The claim was true of the census and false of the
>    > headline.**
>    >
>    > **`resolve.py` is the fix.** It resolves all **11** chunk offsets and **3** main
>    > offsets to their enclosing modules, prints each module's span, prints the bytes,
>    > and asserts nine properties — each of which **exits non-zero on failure**, so it
>    > cannot report a clean run over a body that no longer supports the claim. All
>    > nine PASS (`resolve.txt` §C): `o(4265)` occurs **exactly twice** in the chunk;
>    > module `4265` is **one contiguous 5,842 B span** at 91298–97139 of the main
>    > bundle; its export table maps `z2:()=>be`; `be` selects
>    > `gt.guardianCumulusPeriodicAPI`; that key is assigned
>    > `"system.gc.gz.transition.flags"`; every `.z2` in the chunk sits in a
>    > 4265-importing module **and on the binding**; the value reaches the POST; and
>    > `.z2` is read **0** times in the eager main bundle.
>    >
>    > **Stated plainly: the bodies are still not committed, so re-deriving this needs
>    > the captures — 215 GETs at the recorded 2.5 s spacing. What is now committed is
>    > the resolution table, so a reader with the captures gets an automatic check
>    > instead of a promise, and a reader without them can at least audit which offsets
>    > and which module the claim rests on.**

---

## 1. Controls, in the order they were sent

Three controls went **before any of the 211 cells**, so the verdict is not contaminated
by the data it judges. A fourth was sent after, and is §2.

| # | Path | Result | What it proved |
|---|---|---|---|
| 1 | `/12.c22952a522974f5e.js` — the **negative twin**: the list's first real entry with **one hash character** changed | **404**, `text/html; charset=iso-8859-1`, 196 B, sha256 `80c3fe2ae1062abf…` | "Does not exist" is **distinguishable** from "exists" on this exact path shape, and the absent-path body is **one artefact** — the same digest area V recorded for its fabricated-asset control on this host. It is a mutation of a real entry, so the comparison is like-for-like rather than against a path outside the list. |
| 2 | `/main.6595daf83bd6d4b1.js` — the **positive**: the eager main bundle | **200**, `application/javascript`, **3,417,255 B**, sha256 `0fb4fbd483b5f5d2…` | **The matcher works.** The same body carries 8 core-token hits and 21 across the wider set, and its `patient-timeline` offsets reproduce area V's five **exactly** (§6). Without this, a zero over 211 bodies would be indistinguishable from a broken matcher. |
| 3 | `/runtime.79e2f9040b1dad8f.js` — **the runtime**, which *defines* the corpus | **200**, `application/javascript`, **8,268 B**, sha256 `0dfea208804facf8…` | The chunk filenames are re-derivable from the source rather than inherited from another pass's note — and re-deriving them is what caught the URL-form defect in §2. Also re-confirms `f.p=""` (**asset root**, no `/app` prefix) from the bytes. |

**Control 1 and control 3 both reproduce area V's recorded digests byte for byte**
(`80c3fe2a…` for the absent path, `0dfea208…` for the runtime, `0fb4fbd4…` for the main
bundle), so **the patient build has not bumped since 2026-10-13 09:44 UTC** — five and
a half hours before this sweep — and area V's numbers are re-measured, not inherited.

**Verdict rule, committed in #56:** a chunk counts as real only on
`Content-Type: application/javascript` + sha256 + size — never on status. On this host
family status *is* an oracle (the twin 404s at 196 B with a single digest), so the rule
is belt-and-braces rather than load-bearing here; it is on `carelinkhp.*` that it is
load-bearing.

---

## 2. The URL-form defect — a committed list is not a URL list

**OBSERVED.** `runtime-map.py` re-derives the 211 filenames from the runtime body
fetched in this run and diffs them against the committed list (`runtime-map.txt`):

```
entries re-derived from the runtime map : 211
entries in the committed list           : 211
hashes shared by both lists              : 211 of 211
of those, the NAME differs               : 1

  committed 2076.206e355a4a593fbd.js
  derived   common.206e355a4a593fbd.js
  hash      206e355a4a593fbd   (identical both sides -> only the NAME moved)
```

The runtime's own `f.u` is not a plain join:

```js
f.u = e => (2076 === e ? "common" : e) + "." + { 12:"c22952a522974f5f", 40:"a889…", … } + ".js"
```

One id is emitted under a **different name**. `chunks-swept.txt` (copied verbatim from
area V's list, `sha256 eacb0da44c491692…`, `cmp` clean) carries the **id** there.

**Both halves were then confirmed live, which is what makes this a finding and not a
reading of minified source:**

| Path | Code | Body | Digest |
|---|---|---|---|
| `/2076.206e355a4a593fbd.js` (the committed list's form) | **404** | 196 B `text/html; charset=iso-8859-1` | `80c3fe2ae1062abf…` — **byte-identical to control 1** |
| `/common.206e355a4a593fbd.js` (the name the runtime emits) | **200** | **21,157 B** `application/javascript` | `de1f782d13c4a459…` |

So the sweep's 404 at that cell was the **list** being wrong, not the corpus — and a
sweep that had trusted the list would have closed on "211 cells carry a verdict" with
one verdict about a file that does not exist. The corrected cell was issued as
**seq 215** under the same `flock`, the same sleep and the same ledger schema
(`probe-followup.sh`, which self-checks its row's key set against an existing row and
exits non-zero on drift). **The defect is the same in the clinic build**: the 2026-10-08
record of the clinic runtime carries the identical special case
(`f.u = e => (2076===e?"common":e)+"."+{12:"cfb28faf…"`,
`findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md:1118`), and `CHUNK-CORPUS-FINDINGS.md:13`
records that the 224-chunk clinic sweep had **"One entry returned the SPA fallback"** —
never explained. That is the successor (§8).

---

## 3. The sweep

**211 real chunks, 211 distinct digests, 0 duplicates, 0 empty bodies.** 2,874,939 B
total (2.87 MB); smallest 78 B, largest 828,225 B, median 1,905 B. `tables.txt` §T1/§T4.

> **⚠ Correction (2026-10-13, verification round 1): the counting rule.** The first
> version of this section said "211 cells" and reported **2,853,978 B**, computed by
> `role.startswith("SWEEP-")`. That definition **counted the 196 B HTML error page
> (`seq 51`) as a chunk and dropped the real 21,157 B chunk (`seq 215`, role
> `FOLLOWUP`)** — the two halves of the §2 defect. The ledger was never wrong, and
> neither was the substantive negative (`grep-out.txt` greps the ledger, not this
> selection), but **the denominator did not mean what it said**.
>
> **The rule is now: a chunk is a body answering `200` + `application/javascript`.**
> That gives **211 = 210 `SWEEP-*` 200s + 1 `FOLLOWUP` 200**, which the script asserts
> against the committed list length and **exits non-zero** if they disagree. Re-derived
> total: **2,874,939 B** — the old figure −196 +21,157. `tables.txt` §T4 prints the
> rule, the arithmetic, and the excluded row by name.

Every cell answered `200 application/javascript` except `/2076.…js`, which answered
`404` for the reason in §2 and was re-requested under the correct name. **All 211 real
chunks carry a verdict for the committed token set**, which is this area's close
condition.

`chunks-swept.txt` is committed here so the sweep is re-derivable without another pass's
note, and `verdicts.tsv` is the per-cell ledger (`chunk status bytes sha256 hits`).

### Response-header observations across all 215 cells (OBSERVED)

| header | distribution |
|---|---|
| status | **213 × `200`**, **2 × `404`** |
| `content-type` | 213 × `application/javascript`, 2 × `text/html; charset=iso-8859-1` |
| `content-encoding` | **183 × `br`**, **32 × absent**, **0 × `gzip`** |
| `x-cache` | 213 × `Miss from cloudfront`, 2 × `Error from cloudfront` |

The 32 with no `content-encoding` are the small bodies, including both 196 B 404s, which
the server is declining to compress. **`docs/09` §4's "Unconditional gzip" row carries a
dated note rather than an edit for this reason**: the *hazard* is confirmed and arguably
sharper (brotli is decoded less universally than gzip, so `curl --compressed` is not
optional), but the mechanism sentence did not reproduce today, and settling it would need
a capture taken *without* `--compressed`, which this repo does not hold. **Both readings
are left standing on that page**; see the addendum there.

Both 404s are `Error from cloudfront` — a CloudFront-level miss, which is the layer area
V recorded for this host's absent-path response and is consistent with the single 196 B
digest.

---

## 4. The positive — chunk `6746` follows `system.gc.gz.transition.flags`

Full output in `grep-out.txt` §2 and `tables.txt` §T3. Every offset below is a byte
offset in the named body.

### The chain, each link observable

| # | Link | Where | Class |
|---|---|---|---|
| 1 | `D.guardianCumulusPeriodicAPI="system.gc.gz.transition.flags"` | main bundle, byte **2189121**, module `51551` | OBSERVED |
| 2 | `f=(0,e.Mz)(t,gt=>gt.configuration)`, `be=(0,e.Mz)(f,gt=>gt.guardianCumulusPeriodicAPI)` | main, byte **93798**, module `4265` | OBSERVED |
| 3 | module `4265`'s export table contains `z2:()=>be`, and also `cO:()=>ne` and `X2:()=>ye` | main, byte **91298** | OBSERVED |
| 4 | `.z2` occurs **0 times** in the main bundle | main (re-measured; area V's claim) | OBSERVED |
| 5 | chunk `6746` module `16746` binds `_=o(4265)` | chunk, byte **577** | OBSERVED |
| 6 | chunk `6746` module **`59567`** binds `F=o(4265)` | chunk, byte **66107** | OBSERVED |
| 7 | **read 1** `select(_.z2).pipe(({displayMessage:l})=>…)` | chunk, byte **22252** | OBSERVED |
| 8 | **read 2** `this.store.select(F.z2).pipe(({displayMessage:v})=>…)` | chunk, byte **70046** | OBSERVED |

Links 5+6 are why this is not the alias trap this repo has been bitten by twice: a
two-character minified export is **not** unique, and area V said so about its own `.bQ`
count. Here both reads bind **the same module id**, and that module id resolves to the
main bundle's definition carrying the flags export. The identity is closed by module
id, not by name.

### What the two reads do

**Read 1** is a route resolver named `guardianEndpointData`:

```js
guardianEndpointData: () => {
  const r = I.c.csrEnabled, T = (0,P.WQX)(ge.D);
  return (0,P.WQX)(pe.il).select(_.z2).pipe((0,$.T)(({displayMessage: l }) => {
    const p = T.isCarePartner() ? l.carepartnerDisplayMessageUrl
                                : l.personalDisplayMessageUrl;
    return { useCumulusUrls:   l.useCumulusUrls,
             messageEndpoint:  r ? l.csrDisplayMessageUrl : p };
  }))
}
```

**Read 2** is a service method `getGuardianEndpoint()` in module **`59567`**, byte-for-byte
the same logic. Both destructure `displayMessage` and read **exactly the published
leaves** of `system.gc.gz.transition.flags` — `carepartnerDisplayMessageUrl`,
`personalDisplayMessageUrl`, `csrDisplayMessageUrl`, `useCumulusUrls` — which is a
structural match to area T's published subtree, not merely to a token.

> **Correction (2026-10-13, verification round 1): the first version of this log
> attributed read 2 to module `56358`. That is wrong and is corrected here.**
> Module `56358` occupies bytes **65421–65785** and its body is a device-settings
> enum (`d.CALIBRATION="CALIBRATION"`, `d.AUTO_BASAL_DELIVERY…`). Bytes 66109, 67348,
> The bytes 67391 (the `getGuardianEndpoint` CALL SITE), 67573, 69567, 70046 and
> 70254 are all inside module **`59567`**, which spans
> **65786–84396**. The binding, the offsets and the positive are unaffected; only the
> module id was wrong. `resolve.py` now resolves **every** cited offset to its
> enclosing module and prints the span, so the id is a derived value rather than an
> assertion, and the assertion `every .z2 sits in a 4265-importing module` is allowed
> to fail (`resolve.txt` §C, A6).

**And the value is used, in the same chunk**, in `getMessageRequest` — **definition at
byte 69249** in module `59567`, **called** at byte **67573**. The flow, at exact
offsets:

> **⚠ Corrected 2026-10-13 (verification round 2): `getGuardianEndpoint`'s call site and
> definition were swapped.** An earlier version of this log gave **67391** as the
> *definition*. It is the **call site** — `guardianEndpointData:this.getGuardianEndpoint()`
> inside a factory object. The **definition** is at **69982**:
> `getGuardianEndpoint(){const i=ee.c.csrEnabled;return this.store.select(F.z2)…`.
> The verifier's trace had this right and this log had it backwards; the substance
> is unchanged and the chain is now stated in the order the bytes actually run.

```js
// byte 69458 — the value is unpacked out of the object getGuardianEndpoint() returned
const L = h.useCumulusUrls && this.isCsrEnabled, E = h.messageEndpoint;
// byte 69567 — the M2M branch of the template
let y = `${this.userService.getIsM2MEnabled()
      ? `/patient/m2m/connect/data/gc/patients/${encodeURIComponent(v)}`
      : "/patient/connect/data"}?cpSerialNumber=NONE&msgType=last24hours&requestTime=${(new Date).getTime()}`;
// byte 69786 — the published endpoint value is substituted into the URL
return h.useCumulusUrls && (y = O!==Be.CARE_PARTNER || L ? E
                              : E.replace("{patientUsername}", encodeURIComponent(v))),
// byte 69866 — THE POST, and `y` is its reqUrl
       L ? this.connectHttpService.getPeriodicDataWithPost({ reqUrl:y, username:i, patientId:v, role:O })
         : this.connectHttpService.getPeriodicDataWithGet(y);
```

**The chain is contiguous, not inferred across a gap.** **THE RUN is bytes
69458–69866** — derived, not chosen: it begins at
`const L=h.useCumulusUrls…E=h.messageEndpoint` and ends at the `g` of
`getPeriodicDataWithPost({reqUrl:y`. `resolve.py` prints **THE WINDOW, bytes
69458–69898**, which is 32 bytes longer purely so the tail of the POST call is
visible; **the window is not a claim boundary.** `getMessageRequest`'s own definition
at **69249** shows `h` is its fifth parameter. So
`h.messageEndpoint` — a field of the object `getGuardianEndpoint()` built from the
`system.gc.gz.transition.flags` selector — is assigned to `E`, folded into `y`, and
passed as `reqUrl` to a POST. **The flags subtree does not merely get read: it selects
the URL that is POSTed.**

> **Link 9, settled 2026-10-13 (verification round 1).** The first version of this log
> asserted the flow from a ~200-byte window that stopped short of the POST call, and a
> verifier declined to sign CONFIRMS on it — correctly, because "the value is used
> somewhere in this method" is not the claim being made. **THE RUN, 69458–69866, is
> now printed in full** above and in `resolve.txt`; the POST is at **69866**.
> **No request was needed** — the bodies were still on disk, so this cost none of the
> 15 remaining cap, and the ledger stays at 215 rows.

> **⚠ Corrected 2026-10-13 (verification round 2): this log stated the same claim with
> THREE different ranges — "69458–69866", "bytes 69300–69700 are printed in full", and
> `resolve.py`'s own slice, which actually prints 69458–69898. None of the three
> agreed with any other.** One is a claim boundary, one is a display window, and the
> third was a third thing. `resolve.py` now labels both, in its own output, so the
> two cannot be conflated by a reader who only sees the numbers.

**So the flags subtree is not merely read — `useCumulusUrls` and `messageEndpoint`
select the URL that is then POSTed.** That is the vendor's own CSR pointer
`…/connect/csr/v2/display/message` (PUBLISHED, `docs/04`; `docs/10` §1) arriving in a
client by the documented route area V could not see.

**Read 1 and read 2 are both gated on `csrEnabled`** — which is the area's own
hypothesis stated exactly: *"a lazy chunk is exactly where a feature-gated call site
lives."*

### What this corrects, and what it does not

Area V's published claim is that the client **does not follow**
`system.gc.gz.transition.flags`. That claim is **OBSERVED-correct for the eager main
bundle and refuted for the patient corpus as a whole.** The correction is to the
**scope**, attached here with the original wording intact — not a retraction of the
measurement.

Two things are **not** claimed:

- **Not** that the same code is absent from the other patient deployments. `.eu`/`.com`
  were byte-identical at 09:44 UTC (area V, re-measured here on `.eu` only), so the
  `.com` deployment is **INFERRED** identical and was not probed this pass.
- **Not** anything about *intent* behind the live/dead `baseUrlPde` reading. This pass
  produced no evidence about that in either direction; `docs/03` §9a's INFERRED reading
  is unchanged and still unresolved.

### A second CSR consumer in the same chunk

`getBleEndpoint()` (byte ~70440) reads `F.cO` — module `4265`'s
`csr.cumulus.periodic.data.endpoints` selector — and destructures `display_message`,
mirroring area V's eager-bundle call site. So **`6746` carries both CSR consumers**,
and the pointer area V followed in the main bundle is followed here too.

---

## 4a. Verification round 2 — what the anchored check caught

Two of these are the pass's own worst habit, caught by the tool the pass wrote to
catch bad bytes. Both are recorded here rather than quietly repaired.

> **The offset check could not fail.** `resolve.py` asserted each cited byte with
> `re.search(pat, body[off-40 : off+120])` — a **neighbourhood** match. Prepending one
> byte to the chunk left every pattern matching while every printed offset and module
> span became wrong by one, and the script printed `VERDICT: all assertions PASS`. Its
> own docstring claimed it "cannot report a clean run over a body that no longer
> supports the claim." **It could, and did.** Fixed by `re.match` at the offset
> (`resolve.py`'s `anchored()`).
>
> **And the fix immediately falsified seven of my own published offsets.** They pointed
> at the position of the *evidence* rather than the start of the *token* — byte 579
> holds `o(4265),…` while `_=o(4265)` starts at **577**; 22260 → **22252**; 66109 →
> **66107**; 70054 → **70046**; 69787 → **69786**; main-bundle 93819 → **93798**;
> 2189123 → **2189121**. `AGENTS.md` §6 item 6 in offset form: a citation that does not
> resolve at the place it names. The corrected values are the ones in §4 and in
> `resolve.txt`, and all sixteen cited offsets are now asserted with `re.match`.
>
> **A guard that could not fire, found by the harness rather than by reading.** While
> renumbering the assertions, A9's guard was left reading `if not a8:` while assigning
> `a9` — and `a8` is the *POST-definition* flag, which is True. So A9 printed
> `FAIL` and the script still **exited 0**. `resolve.py` now cross-checks its own
> printed FAIL lines against its recorded failures and fails itself when they
> disagree.
>
> **The mutation test is committed, not promised.** `resolve-mutants.py` applies **12**
> mutations to throwaway copies — including the 1-byte prepend — and requires a
> non-zero exit with a named failure from each, plus **1 control** that must stay
> green. **12 of 12 caught, 1 of 1 control behaved** (`resolve-mutants.txt`). The
> 1-byte prepend is now caught with
> `A-offset read 1 import … at byte 577: expected '_=o(4265)'`.
>
> **"12 endpoint shapes" was a subset, and no rule produced it.** Chunk `5750` carries
> **four** `/patient/csr` offsets — `[775, 855, 985, 1076]`, all four already in this
> pass's own `tables.txt` §T3 — and the route table named one. Re-derived under a
> recorded rule (`patient-csr.py` → `patient-csr.txt`), a shape being one distinct
> **(method, path template)** pair: **19 shapes over 16 templates**, from **10 raw
> literals in 7 chunks**, with **7 calls excluded** because their first argument is a
> bare identifier and the URL comes from the caller. Three things moved that number and
> all three are in the rule: **ternaries count as both branches** (the 5750 ternaries);
> **a bare `this.baseUrl` is a shape, not an exclusion**; and **a runtime slot's NAME is
> a minifier artefact** — the same slot is `{t}`, `{o}` and `{c}` in three builds of one
> service, so slots are renumbered by position, without which the three safety/notice
> chunks never deduplicate against each other and the count triples.

## 5. The negative — and every hit that has to be accounted for

Full output in `grep-out.txt`, totals in `tables.txt` §T1/§T2. Method per `docs/09` §5
item 2: three counts per token (case-sensitive `cs`, case-insensitive `ci` as the
control, complete quoted literal `q` as the strict test), byte offsets, and the maximal
enclosing identifier for **every** non-zero count, unfiltered.

### Every discovery-document token is zero across all 211 chunks

| token | `cs` | `ci` | `q` | in the positive control |
|---|---|---|---|---|
| `baseUrlPde` | **0** | 0 | 0 | 0 |
| `/connect/pde` · `/connect/pde/v3` | **0** | 0 | 0 | 0 |
| `baseUrlCumulus` · `baseUrlCms` · `baseUrlAem` · `baseUrlCareLink` | **0** | 0 | 0 | 0 |
| `discover/android` | **0** | 0 | 0 | 0 |
| `clcloud` · `api/carepartner` | **0** | 0 | 0 | 0 |
| `system.gc.gz.transition.flags` (the key constant) | **0** | 0 | 0 | 1 |

**Not one lazy chunk reads the discovery document.** The corpus area V said it could not
see — 211 more bodies, 2.85 MB, **0 hits on every pointer-shaped token.** Area V's
negative converts from *scoped* to **unqualified over the patient web corpus**, and
`docs/03` §9c is updated accordingly.

### `discover` (12) and `pde` (5 `cs` / 34 `ci`) — both dictionary noise, and the control **did** find a second reading

`discover` appears in exactly **one** chunk, `8141.650c358996e4c19a.js` (828,225 B), and
every hit is a **substring of a zxcvbn password-dictionary entry** in a comma-separated
word list. For `discover` the `cs` and `ci` counts are equal (12/12), so there is no
second reading for that token.

- `discover` ×12 → `discover`, `discovered`, `discovery`, `discovers`, `discovering`,
  `discoveries`, `rediscovered`, `discoverer`, `rediscovery`, `discoverers`,
  `rediscover`, `undiscovered`.

> **⚠ Correction (2026-10-13, verification round 1): this section originally read
> "The `cs`/`ci` counts are equal for **both** … the case-sensitivity control adds
> nothing here." That was false for `pde`, and the prose contradicted the table it
> sat above.** Corpus-wide `pde` is **`cs=5`, `ci=34`** — the control found **29 hits
> the sensitive count missed**. All 29 are classified, and **none is a new identifier
> class**:

| enclosing identifier | `cv` hits | where |
|---|---|---|
| `propDecorators` | 8 | main |
| `removeStylesOnCompDestroy` | 6 | main |
| **`mapDeviceModelName`** | **6** | **4 in chunk `7187.87daa49216a1a9ef.js`**, 2 in main |
| `WPDesktop` | 3 | main |
| `isDesktopDevice` | 2 | main |
| `getGroupDelayControl` | 2 | main |
| `LoopDetected` | 2 | main |
| **total** | **29** | |

Every one matched the text `pDe` inside a longer camelCase identifier. **The seven
identifiers are exactly the seven area V already listed** for the patient bundle's 25
insensitive hits. The only corpus novelty is that **`mapDeviceModelName` also occurs in
lazy chunk `7187`** (offsets 74111, 77086, 80017, 80248) — the same identifier, so
**no new false-hit class is introduced by the lazy corpus**.

> **The prose was wrong because the tool could not have caught it.**
> `extract.py`'s §2 iterated the **case-sensitive** pass only, so §1's own pointer
> "ci adds 29, read §2" pointed at a section that could not show those 29. §2 now
> iterates the case-**insensitive** pass and labels every hit `cs` or `cv`
> (`grep-out.txt`), and `tables.py` T3 prints case-variant-only rows instead of
> omitting them. This is `AGENTS.md` §6 item 5 — prose that contradicted its own source
> table — and it survived because the table was correct and the sentence about it was
> not.

- `pde` ×5 **case-sensitive** → `dropdead` (72313), `helpdesk` (96374), `herpderp`
  (128269), `topdevice` (130050), `hampden` (338216).

**These are the same five and the same twelve words area V found in the two portal
builds**, now shipping in the patient chunk corpus too — only the byte offsets differ.
They are literals in a password-strength wordlist, **not directives**. Same false-hit
class as `docs/09` §5 records for `ngp`/`guardian`, and a bare grep on either name would
have reported an integration that is not there.

### `baseUrl` (30 `cs` across 4 chunks) — and it is the pass's **second** positive

`baseUrl` was measured (`extract.py`, `grep-out.txt`) at **32 corpus-wide hits, `q=0`**,
but it was **absent from `tables.py`'s token list and from this section** in the first
version of the log — a measured token in no table and no prose. It is accounted for
here, and it is not noise.

**2 hits in the eager main bundle**, and they are area V's finding unchanged: `this.baseUrl`
assigned from `getBaseCmsUrl()` to fetch a CMS media file (bytes 2027033, 2027209).
**Not** a discovery pointer.

**30 hits across four lazy chunks**, and here the token means something entirely
different — a **hard-coded patient API base**, not a config value:

| chunk | hits | the literal |
|---|---|---|
| `1635.…js`, `8942.…js`, `9807.…js` | 8 each | `this.baseUrl="/patient/csr/safety/notice/definitions"` |
| `common.206e355a4a593fbd.js` | **6** | `this.baseUrl="/patient/csr"` |

and the `/patient/csr` literal appears in **7 chunks / 10 case-sensitive hits** in all,
because three further chunks hard-code CSR paths without a `baseUrl` field:

| chunk | endpoint literal |
|---|---|
| `common.…js` | `GET/POST /patient/csr/incidents`, `GET/PUT /patient/csr/incidents/{id}`, `GET /patient/csr/incidents/configuration?region={region}` |
| `1635/8942/9807.…js` | `GET /patient/csr/safety/notice/definitions?…`, `…/{type}/file/url`, `…/{type}/users`, `POST …`, `PUT …/{id}`, `POST …/{id}/notification/date`, `GET …/{type}/users/csv` |
| `5109.…js` | `GET /patient/csr/configuration/whitelisted` |
| `5750.…js` | `GET /patient/csr/users/me/notifications/history/patients/{id}` |
| `6633.…js` | `GET /patient/csr/users/me/consent/history` |

**What this is, and what it is not.** It is **OBSERVED as code**: these are path
literals in shipped, lazy-loaded Angular services, reached by relative
`this.http.get(...)`/`post(...)`/`put(...)` against a hard-coded base — so the client
addresses them by **constant**, with no config field and no discovery document involved.
**It is NOT an existence claim.** No request was sent to any `/patient/csr/*` path:
these are outside the area's candidate list, and the area's scope was the discovery
token set. **Whether the routes are live is UNOBSERVED in both directions**, and these
**19 method x path shapes over 16 distinct path templates** appear in **no `docs/`
page** — I checked before writing this, and they are absent from
`docs/06-patient-api-surface.md` and from every other canonical page. The counting
rule, the raw evidence and the exclusions are in `patient-csr.txt`.

This **strengthens** the negative in §5 rather than weakening it: the lazy chunks do
not read the discovery document, and where they *do* carry API addresses they are
hard-coded constants. That is the opposite of a config-following client.

### The four `transition.flags` leaves that DO appear

| leaf | `cs` | chunks | offsets |
|---|---|---|---|
| `useCumulusUrls` | **6** | 1 (`6746…js`) | 22393, 22410, 69468, 69742, 70202, 70219 |
| `csrDisplayMessageUrl` | **2** | 1 | 22445, 70254 |
| `personalDisplayMessageUrl` | **2** | 1 | 22360, 70169 |
| `carepartnerDisplayMessageUrl` | **2** | 1 | 22329, 70138 |
| *remaining five leaves* | **0** | — | — |
| `display_message` | **2** | 1 | 22085, 70436 |
| `/patient/m2m` | **1** | 1 | 69567 |

Every one is in chunk `6746`, every one was classified **literal → property read on a
destructured config value**, and §4 traces the flow. **The other five leaves
(`pullGMInfoFromCumulus`, `pullSMSHistoryFromCumulus`, `sendDiagnosticLogsToCumulus`,
`sendPeriodicToCumulus`, `sendSMSFromCumulus`) are 0 across all 211 chunks** — a real
negative inside the positive, and the reason a single hit cannot be read as "the subtree
is consumed".

---

## 6. Addendum for area F — `patient-timeline` and `dialog-lite`

Recorded here because area V recorded the eager-bundle reading and this sweep is the
corpus that could have changed it. It did not.

- **`patient-timeline`: 0 case-sensitive, 0 case-insensitive, across all 211 chunks.**
  `dialog-lite`: **0 / 0** across all 211 chunks, and **0 in the positive control too** —
  so the second is a true zero rather than an untested matcher.
- The **five hits in the eager main bundle reproduce area V's byte offsets exactly** —
  1718181, 1719243, 1963408, 1963661, 3340159 — and the classifier independently reaches
  area V's reading from the bytes: **Angular component selectors, not URLs**
  (`["app-patient-timeline"]`, `app-patient-timeline-filter-toolbar`, two template calls,
  one `selectors:` array).
- The **main bundle is byte-identical to the one area V measured** (3,417,255 B,
  `0fb4fbd4…`), so this is a re-measurement and not a second opinion about different
  bytes.
- `personal.patient.timeline.config` (1), `personal.patient.timeline.host` (1) and
  `personalPatientTimelineHostURL` (1) are **1 in the main bundle and 0 in all 211
  chunks** — so area V's record that the bundle *names* a timeline host that no document
  publishes, and *reads* the config key, stands unamended and now also unamended by the
  lazy corpus.

**What this does not do:** it does not answer "who calls `patient-timeline`". The
backend is the only thing that calls it, and §4 shows what the client does when
`csrEnabled` is false — it routes elsewhere. Area F's three candidate explanations for
the gateway's 403s are untouched.

---

## 7. Scope limits, stated where a reader would otherwise over-read this

1. **One deployment.** `carelink.minimed.eu` only. `carelink.minimed.com` served a
   byte-identical bundle at 09:44 UTC (area V) and is **INFERRED** identical here;
   `carelink-trials.minimed.com` was not probed.
2. **One build.** 211 chunks + `main` + `runtime` of the build fingerprinted
   `main.6595daf83bd6d4b1.js` / `0fb4fbd4…`. The clinic (`2a7fa8e7…`) and support
   (`a054555a0f…`) builds were not swept; the clinic corpus is the successor (§8).
3. **A 404 here is a true absence**, but a **200 is not** a proof of use. Chunk `6746`
   is reachable from the route table and its module is imported by two other modules in
   the same chunk; whether a given session executes `getGuardianEndpoint()` depends on
   `csrEnabled`, which is **not observed** — no session was authenticated and none was.
4. **The value read is not observed.** What `useCumulusUrls` and `messageEndpoint` hold
   at runtime comes from the published config document, not from this corpus. The
   *code path* is OBSERVED; the *value* is PUBLISHED
   ([findings-log/2026-10-12-published-pointers/FINDINGS.md §1]).
5. **The 211 bodies are not committed**, so the grep cannot be re-run from a clean
   clone. What is committed is the verdict table, the full census with byte offsets and
   the enclosing identifiers — which is what makes each claim checkable without
   re-fetching 2.85 MB.
6. **The `date` series is not trusted** for this pass and no cause is asserted for it.
   Every spacing claim above is made from the kernel series, with the `date` series
   reported beside it and never instead of it.

---

## 8. Reproducing

```bash
# the sweep — 3 controls, then 211 cells, one host, 2.5 s inside the flock
export TMPBODIES=<a writable dir>          # bodies land here and are never committed
bash findings-log/2026-10-13-area-k-patient-chunks/probe.sh        # cap 230

# the one follow-up cell for the URL-form defect (§2)
bash findings-log/2026-10-13-area-k-patient-chunks/probe-followup.sh /common.206e355a4a593fbd.js

# offline, zero requests
python3 findings-log/2026-10-13-area-k-patient-chunks/runtime-map.py \
        "$TMPBODIES/k-runtime.b" \
        findings-log/2026-10-13-area-k-patient-chunks/chunks-swept.txt \
        findings-log/2026-10-13-area-k-patient-chunks/results.jsonl > runtime-map.txt
python3 findings-log/2026-10-13-area-k-patient-chunks/extract.py "$TMPBODIES" \
        findings-log/2026-10-13-area-k-patient-chunks/results.jsonl > grep-out.txt
python3 findings-log/2026-10-13-area-k-patient-chunks/resolve.py "$TMPBODIES"  > resolve.txt
python3 findings-log/2026-10-13-area-k-patient-chunks/tables.py "$TMPBODIES" \
        findings-log/2026-10-13-area-k-patient-chunks/results.jsonl \
        findings-log/2026-10-13-area-k-patient-chunks/chunks-swept.txt > tables.txt
bash    findings-log/2026-10-13-area-k-patient-chunks/spacing.sh \
        findings-log/2026-10-13-area-k-patient-chunks/results.jsonl > spacing.txt
```

`resolve.py` **exits non-zero if any of its nine assertions fails**, so it cannot print a
clean run over a body that no longer supports the headline. It is the re-derivation path
for section 4: it resolves every cited byte offset to its enclosing webpack module and
prints the module's span.

`probe.sh` is **idempotent**: re-running it skips every path already in the ledger.
`results.jsonl` rows carry `t_queued` / `t_sent` / `t_done` at millisecond UTC resolution
plus `body_mtime_ns`; `headers/` holds one `<tag>.h` per request; `verdicts.tsv` holds
one row per cell.

---

## Evidence table

| Claim | Class | Source |
|---|---|---|
| **215 of a 230 cap**, GET only, one host, no `OPTIONS`, no `POST`, no token | OBSERVED | `results.jsonl` seq 1–215; `run.log` |
| Declared delay 2.5 s with the sleep **inside** the per-host `flock` | OBSERVED | `probe.sh` `req()`; `send.sh` |
| Spacing floor **2.636 s** by kernel body-mtimes — 214 gaps, **0** under 2.5 s, **0** under the 2 s floor, **0 negative kernel gaps** | OBSERVED | `spacing.txt` |
| The harness `date` series disagrees: **min 1.835 s**, 22 under 2.5 s, **7 under the 2 s floor**, **16 negative durations**, 22 bodies written before their own `t_sent`; **no cause asserted** | OBSERVED | `spacing.txt`; `results.jsonl` |
| CORRECTED 2026-10-13 (verification round 1): the span "validation" was arithmetic that **telescoped to the first row's own latency** and could not detect interior corruption. Replaced by a **per-gap** comparison that fires: **max abs(send − mtime) 0.873 s**, median 0.015 s, **20 of 214 gaps disagree by >0.5 s**, each named | OBSERVED | `spacing.txt` §PER-GAP SERIES COMPARISON |
| The two long gaps, **kernel series**: **34.016 s** (seq 4→5, harness restart) and **35.615 s** (seq 214→215, sweep→follow-up), both **over** the declared delay. The first version quoted 34.017 / 35.622 — the `date` figures — in a paragraph naming the kernel series | OBSERVED | `results.jsonl` seq 4→5, 214→215; `spacing.txt` |
| Negative twin 404s at 196 B with one digest, byte-identical to area V's certainly-absent control | OBSERVED | `results.jsonl` seq 1 |
| Positive control resolves and **carries the token set** — so a zero sweep is a zero, not a broken matcher | OBSERVED | `results.jsonl` seq 2; `grep-out.txt` |
| Runtime re-fetched; **211 entries re-derived from `f.u`**, `f.p=""` (asset root) | OBSERVED | `runtime-map.txt`; `results.jsonl` seq 3 |
| Controls 1–3 reproduce area V's three digests **byte for byte**; the build has not bumped in 5½ hours | OBSERVED | `results.jsonl` seq 1, 2, 3 |
| CORRECTED 2026-10-13 (verification round 1): **211 real chunks = 210 `SWEEP-*` 200s + 1 `FOLLOWUP` 200**, counting rule = `200` + `application/javascript`, asserted against the committed list and **exiting non-zero on disagreement**. The first version selected on `role.startswith("SWEEP-")`, counting the 196 B error page as a chunk and dropping the real 21,157 B one. **211 distinct digests**, 0 duplicates, 0 empty, **2,874,939 B** (was mis-reported as 2,853,978) | OBSERVED | `tables.txt` §T4; `tables.py` counting rule |
| **Lazy chunk `6746.c6795ff7e9ff468d.js` reads the `system.gc.gz.transition.flags` selector twice** — bytes 22252 and 70046 | OBSERVED | `grep-out.txt` §2; `tables.txt` §T3; `resolve.txt` §A |
| CORRECTED 2026-10-13 (verification round 1): read 1 is in module **`16746`** (177–32151) and read 2 in module **`59567`** (65786–84396). The first version attributed read 2 to `56358`, whose body is a device-settings enum at 65421–65785 | OBSERVED | `resolve.txt` §A |
| Both reads bind **module id 4265**; module `4265` is **one contiguous 5,842 B span** at main-bundle bytes 91298–97139 and its export table maps `z2:()=>be` | OBSERVED | `resolve.txt` §C A1–A3 |
| `z2` resolves to `be=(0,e.Mz)(f,gt=>gt.guardianCumulusPeriodicAPI)` and `D.guardianCumulusPeriodicAPI="system.gc.gz.transition.flags"` | OBSERVED | main bundle bytes 93798, 2189121; `resolve.txt` §C A4–A5 |
| **The value demonstrably flows into the POSTed URL**: `E=h.messageEndpoint` at **69458** → the template → `y=…E…` at **69786** → `getPeriodicDataWithPost({reqUrl:y` at **69866**, one contiguous run inside `getMessageRequest` (defined **69249**, module `59567`). THE RUN is **69458–69866**; the window `resolve.py` prints is **69458–69898** | OBSERVED | `resolve.txt` §C A7 |
| **No lazy chunk reads the discovery document**: `baseUrlPde`, `/connect/pde`, `baseUrlCumulus`/`Cms`/`Aem`/`CareLink`, `discover/android`, `clcloud`, `api/carepartner` are **0 / 0** across all 211 | OBSERVED | `grep-out.txt`; `tables.txt` §T2 |
| CORRECTED 2026-10-13 (verification round 1): `pde` is **`cs=5` / `ci=34`** — the control found **29 case-variants**, not none as the prose said. All 29 classified into **7 identifiers, exactly the 7 area V listed**; the only corpus novelty is `mapDeviceModelName` also in chunk `7187` ×4. `extract.py` §2 now iterates the insensitive pass and labels every hit `cs`/`cv` | OBSERVED | `grep-out.txt` §2; `tables.txt` §T3 |
| `discover` ×12 and `pde` ×5 `cs` are zxcvbn dictionary substrings in one chunk; the same 5 and 12 words the portal builds carry | OBSERVED | `grep-out.txt` §2; `tables.txt` §T3 |
| ADDED 2026-10-13 (verification round 1): **`baseUrl` is 30 `cs` across 4 chunks and is a hard-coded patient API base, not a CMS base** — `this.baseUrl="/patient/csr"` (×6 in the corrected `common` chunk) and `this.baseUrl="/patient/csr/safety/notice/definitions"` (×8 in each of 3 chunks), with `/patient/csr` literals in **7 chunks / 10 hits**. **OBSERVED as code literals only; liveness UNOBSERVED in both directions** — no request was sent to any of them, and these resolve to **19 method x path shapes over 16 path templates**, in **no `docs/` page** | OBSERVED (literals) · UNOBSERVED (liveness) | `grep-out.txt` §2; `tables.txt` §T2/§T3; `FINDINGS.md` §5 |
| Four of the nine `transition.flags` leaves appear, all in chunk `6746`; the **other five are 0 across all 211** | OBSERVED | `tables.txt` §T2, §T3 |
| `patient-timeline` and `dialog-lite` are **0 / 0 across all 211 chunks**; the main bundle's five `patient-timeline` hits reproduce area V's offsets exactly and classify as Angular component selectors | OBSERVED | `grep-out.txt` §2 |
| Area V's "`.z2` read 0 times in the main bundle" — **re-measured, still true**, scope corrected not retracted | OBSERVED | `grep-out.txt`; area V `consumers-out.txt §2` |
| The URL `…/connect/csr/v2/display/message` that `messageEndpoint` carries | PUBLISHED | `docs/04`; [findings-log/2026-10-12-published-pointers/FINDINGS.md §1] |
| The clinic build carries the **same** `2076→common` special case, and `CHUNK-CORPUS` records an unexplained SPA-fallback entry in the 224-chunk clinic sweep | OBSERVED | `findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md:1118`; `CHUNK-CORPUS-FINDINGS.md:13` |
| `carelink.minimed.com` and `carelink-trials.minimed.com` carry this chunk's logic | **INFERRED** — assumption: the three patient deployments serve one build, which area V measured for `.eu`/`.com` only. **Not probed here** | area V `FINDINGS.md` §Scope limits 4 |
| Whether `csrEnabled` is true in any real session, i.e. whether `getGuardianEndpoint()` ever executes | **INFERRED — and unobserved in both directions.** No session was authenticated; `AGENTS.md` §11 forbids it | — |
| Area T's reading that `baseUrlPde`'s deadness is a retired service rather than an ignore contract | **unchanged, still unresolved** — this pass produced no evidence about intent | `docs/03` §9a |
---

## Correction (2026-10-13)

Raised by verification round 3, after this branch merged `origin/main` (PR #65,
`2306477`). **No claim above changed; seven defects in how the pass's own evidence was
presented were corrected, and two of the corrections found a defect the pass's
instruments could not see in themselves.** Appended rather than edited in place, per
`AGENTS.md` §3.

### 1. A published endpoint that dropped a runtime slot

`docs/06:559` published `/patient/csr/safety/notice/definitions/users/csv`. This
pass's own corpus records **`/patient/csr/safety/notice/definitions/{1}/users/csv`**
(`patient-csr.txt`, RESOLVED ENDPOINT SHAPES). The slot was not renamed — it was
**absent**, while the three rows above it in the same table all carry `{id}` or
`{type}`. **A reader following `docs/06` requests a path with no route.** The same
slip was in this file's §5 table, whose column header promises the *endpoint
literal*. Both now carry the slot.

⚠ **One INFERRED element, labelled rather than hidden.** The corpus cannot distinguish
`{id}` from `{type}` — the minifier emits one positional slot and the corpus
canonicalises it to `{1}`. `{type}` is used because the row's immediate sibling is
`definitions/{type}/users`; that is a choice for table consistency, **not** something
the corpus establishes. **Also recorded, not fixed here:** the renumbering rule printed
directly above that table in `docs/06` says slots "are renumbered `{1}`, `{2}`, … by
position", and the table then uses `{id}`/`{type}` throughout. That inconsistency is
pre-existing, is wider than this row, and is **not this pass's to settle** — it is
named here so the next reader meets it knowingly.

### 2. A retracted byte range still published in this pass's own claim table

This file's evidence table carried "Bytes 69300–69700 printed in full" — a range the
pass had already retracted in §4 and that `resolve.txt` contradicts. **THE RUN is
69458–69866** (the span the claim is about); **THE WINDOW is 69458–69898** (what
`resolve.py` prints, and a printing convenience, not a claim boundary). The table now
states both and labels them. The retraction itself is unchanged and was never deleted.

### 3. `leak-screen.py` had never been shown to fail

`leak-screen.py` carried a SELF-TEST, but it proved the **patterns** fire on their own
targets. Nothing had ever run the **screen's** failure path — the subject walk, the hit
recording, the `file:line` output, the non-zero exit — because on this pass's real
artefacts the honest answer is zero hits. `leak-screen-proof.sh` now plants three
pattern violations at known lines in a throwaway copy and asserts: exit non-zero; the
output names `file:line`; **the named line is the planted line** (locator correctness,
not merely presence); every planted pattern is named in the FAILURES block and no value
is reprinted; **and the control — the same screen on a clean tree — exits 0**, without
which "exits non-zero" is satisfied by a script that always fails. Result in
`leak-screen-proof.txt`: exit 1 on the poisoned tree, 3 of 3 hits named at lines 3, 4
and 5, exit 0 on the clean tree.

⚠ **The proof found a real defect, in `leak-screen.py` itself.** Run against the real
repository, the screen reported hits on **its own committed output**: the SELF-TEST
printed its probe strings with `%r`, and a `.txt` screen output is exactly what the
screen reads. The fragmentation in that self-test was self-defeating — it assembled the
material at runtime and then wrote the assembled string to a committed file, which is
what it existed to prevent. Two further trips were found on the same run: this proof
script echoed `$TMP`, a path under this account's home directory, into its own report;
and the screen read that back. **Fixed in `leak-screen.py` (length only, never the
value), in `leak-screen-proof.sh`, and both artefacts regenerated.** A screen that finds
a leak in its own report is the most direct evidence available that it can fail at all,
which is what this proof existed to establish.

### 4. `resolve.py`'s self-consistency check tested emptiness, not correspondence

The block's comment claimed "every line above that says FAIL must have produced an
entry in `failures`"; the code tested only that the two collections were not both
empty. **Two printed FAILs with one recorded entry printed `consistent`** — the
`if not a8:` defect a second time, a printed verdict with no consequence, inside the
block written to close it.

**Counting rule, recorded because it decides what the check can mean.** Several
assertions append **inside a loop** (A6, A7, A8 and the A-/B-offset sweeps), so one
printed FAIL line may legitimately correspond to several entries; a raw equality of the
two counts would fail a correctly reported run. The correspondence claimed and
checkable is therefore **directional**, and both directions are now enforced: every
printed FAIL is backed by ≥1 recorded entry, and every recorded entry by ≥1 printed
FAIL. **Group-level correspondence is NOT checked** — proving a given entry belongs to
the assertion whose line printed FAIL needs each site to label its own output. Two
failing assertions on one run can still satisfy both directions while one records
nothing of its own. That limit is stated in the code, not glossed.

The rule is a pure function and is now exercised on **seven synthetic counts**,
including the case the old code let through (2 printed, 1 recorded) and a worse one
(3 printed, 2 recorded). All seven behave as the rule states.
⚠ **`resolve.txt` has NOT been regenerated and is not byte-exact with the corrected
script** — the corpus bodies it reads are **not committed** (`resolve.py` takes the
bodies directory as `argv[1]`, and no such directory exists in the repository). The
correction is **additive and touches no assertion**, so no figure in `resolve.txt`
changes; what changed is a diagnostic block. Stated rather than left to look
regenerated.

### 5. `patient-csr.py`: the printed rule list renumbered the rules it summarised

The module docstring defines **rules 1–8**. The printed summary listed only **1–5** and
printed `rule 5 verbs` — but the code's own inline citations use the docstring's
numbering (`rule 5: BOTH branches` for ternaries, `rule 4` for the bare-identifier
exclusion, `rule 8` for out-of-scope). **A reader who followed the printed output to
"rule 5" landed on the wrong rule**, and the two rules the summary omitted are the two
that most move the figure (slot canonicalisation and scope). The summary now prints
all eight, matching the docstring one for one.

⚠ **`patient-csr.txt` is not byte-exact with the corrected script**, for the same reason
as §4: the corpus is not committed. Verified that the edits are a raw-docstring prefix
plus added `w(...)` lines — **no logic changed, so every figure in the artefact stands**.
It also cannot be: the original capture was **not** byte-exact either, because line 24
of the script contained `\`` in the docstring, an invalid Python escape. Every run
emitted `SyntaxWarning: "\`" is an invalid escape sequence` **to stderr**, and a future
Python makes it a `SyntaxError`. The docstring is now a raw string, so the script
compiles with **zero warnings** — verified with `warnings.simplefilter("always")`.

### 6. An independent re-derivation, and the mistake it caught in the re-deriver

`spacing-recheck.sh` re-derives every figure `docs/09` §4 quotes for this pass, from
`results.jsonl`, **by a second implementation and with zero requests** — a screen that
has only ever agreed with its own source has not been tested. All **13** checks
re-derive: 215 rows, 16 impossible durations, 22 bodies written before their own
`t_sent`, 214 same-host gaps, 22 under 2.5 s and 7 under 2 s by `date` against 0 and 0
by kernel mtime, floor 2.636 s / 1.835 s, max per-gap disagreement 0.873 s, 20 gaps
disagreeing by >0.5 s.

**Two things worth publishing because they are the kind of thing that is silently
wrong:**

- **The 16-set and the 22-set are different questions.** The 22 bodies written before
  their own `t_sent` **contain** the 16 impossible durations plus
  `{47, 73, 117, 140, 190, 207}`. A duration and a body-write offset are different
  measurements and this pass's earlier prose moved between them as though they were
  one.
- **The first attempt at the re-derivation was wrong, and the artefact was right.** It
  omitted `.replace(tzinfo=timezone.utc)` from its parser, so every timestamp shifted by
  3600 s and it reported "0 bodies written before their own t_sent" against the
  artefact's 22. `spacing.sh:47` pins the timezone. The mistake is published in the
  script rather than deleted, because anyone re-deriving this will make it.
- **One figure moved: the "median".** `spacing.txt` reports `sorted(ad)[n//2]` — the
  **upper-middle element** of an even-length list — as the median. The true median is
  the mean of the two central elements: **0.0145 s against the printed 0.0149 s**. Both
  are now stated. This is the only disagreement between the artefact and the
  re-derivation, and it is a definitional one, not a transcription error.

### 7. `docs/09` §4, re-derived rather than added to

This branch merged `origin/main`, where PR #65 had **rewritten** the sub-declared-gap
rows. The governing rule now reads: *where a pass's harness series is shown to carry an
impossible duration, its sub-declared gaps are artefacts of that corruption and are not
evidence of underspacing; the kernel mtime series is the counter.*

**This pass therefore contributes evidence, not a number.** Its 16 impossible durations
put it on the same side of that rule as the CORS-method pass, so **its 7 gaps below the
2 s floor are not added to the published 22**, which stays five passes.

⚠ **And re-deriving the class exposed that this page's pass list was short.** Eleven
passes show a sub-declared gap on their own `t_sent` series, not the five or six the
page's own prose implied: **B 1, X 1, Z 5, O 21, D 14, J 2, Q 2, E 4, F 1, CORS 1,
K 7.** **Three of them — E, J and Q — were never named on this page at all**, each
against its own committed `spacing.txt`. Ordering by the commit time at which each
pass's `FINDINGS.md` entered the repository (the only ordering proxy on disk, and
**INFERRED** — it dates the write-up, not the probe) makes **F the ninth** and **O the
fourth**, so **neither ordinal this page published re-derives**: F's *sixth occurrence*
and O's *sixth pass to exhibit the signature*. Both sentences are left standing rather
than edited away. **Q's instance is on `api.github.com`, not a vendor host** — which is
the point and not an excuse: the defect is in the harness's clock and does not need
Medtronic's edge to occur.

### 8. `docs/10` — area V's measurement and the inference drawn from it, separated

The open row for the discovery document's consumer carried both area V's measurement
and this pass's refutation of a generalisation, in one sentence that said the claim was
"correct for the eager main bundle and refuted for the patient corpus" and then
"the measurement stands". That reads as self-contradictory. It now says plainly: **area
V's measurement STANDS and is NOT retracted** (`.z2` is 0 in the eager main bundle,
re-measured here against area V's own offsets), it was scoped to the eager main bundle
and its published wording said so; **what this sweep refutes is the generalisation drawn
from it**. A measurement and the inference drawn from it are separate artefacts, and
here only the second one failed. This matches #64's own "What is NOT retracted" section.

### Not corrected, and named so a reader does not assume it was

- **`docs/09` line 188** (the CORS `allow-methods` row, on `origin/main`) carries a
  stray `|` that splits its **Fix** cell, and GitHub drops the overflow cell — so the
  advice *"pin the **exact** value, not `contains "POST"`"* **is not rendered on the
  page**. Pre-existing, unrelated to this pass, and **not fixed here**: a drive-by edit
  to another pass's row is not this pass's to make silently. Reported to the owner.
- **`patient-csr.txt` and `resolve.txt` cannot be regenerated from a clean clone.**
  Both scripts read response bodies that this repository does not commit. Every figure
  in both artefacts is unaffected by the corrections above; both artefacts are stated as
  predating the corrected scripts rather than as captures of them.
