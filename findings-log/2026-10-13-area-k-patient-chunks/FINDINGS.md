# Area K — the 211 patient lazy chunks, swept for the discovery token set

**Pass date:** 2026-10-13 · **Claim issue:** #56
**Branch:** `research/k-patient-chunks` · **Ledger:** `results.jsonl` (215 rows, one per HTTP request)
**Harness (as sent):** `probe.sh` + `send.sh` (the sweep) · `probe-followup.sh` (one cell, §2)
**Offline, zero requests:** `runtime-map.py` · `extract.py` · `tables.py` · `spacing.sh`
**Outputs:** `chunks-swept.txt` · `verdicts.tsv` · `runtime-map.txt` · `grep-out.txt` · `tables.txt` · `spacing.txt`

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
**4265** (`_=o(4265)` at byte 579, `F=o(4265)` at byte 66109), and module `4265` is
**defined in the main bundle at byte 91298**, whose export table maps `z2:()=>be`, where
`be=(0,e.Mz)(f,gt=>gt.guardianCumulusPeriodicAPI)` and
`D.guardianCumulusPeriodicAPI="system.gc.gz.transition.flags"`. So this is not a
two-character alias collision — the identity is closed by **module id**, which is the
`AGENTS.md` §6 item 3 discipline applied to a minified export rather than to a hash.

> Area V's claim is **not retracted**. "`.z2` occurs 0 times in the main bundle" is
> **OBSERVED and re-measured here** (§4). What the sweep changes is which corpus the
> claim is about, and that is what a lazy chunk is for.

**Two secondary results, one of them a correction to a committed artefact.**

1. **The committed chunk list's URL form is wrong for exactly one entry.** `chunks.txt`
   carries `2076.206e355a4a593fbd.js`; the runtime's own `f.u` emits that chunk under
   the **name** `common`. The sweep requested the id, got a 404, and would have closed
   with a clean negative over 211 bodies in which one cell is a statement about a
   filename. Re-requested under the name the runtime emits, it resolves: **200,
   `application/javascript`, 21,157 B**. §2.
2. **`patient-timeline` and `dialog-lite` stay at zero across all 211 chunks**, and the
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
shows **0 gaps under 2.5 s and 0 under the 2 s floor** across all 214.

Series validated before use, per `docs/09` §4: harness span **648.073 s** against kernel
mtime span **647.799 s** — agreement to **0.274 s** over a 10-minute run, so the mtime
series is this run's own and not a checkout artefact. **No cause is asserted for the
`date` disagreement.** The two long gaps are both explained and both are *over* the
declared delay, not under it: **seq 4→5 = 34.017 s** is the harness restart described
below, and **seq 214→215 = 35.622 s** is the gap between the sweep finishing and the
one follow-up cell being issued (§2), during which four offline scripts ran.

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
> 3. **The 211 bodies (2.85 MB) and the 3.4 MB main bundle are deliberately not
>    committed.** Digests, sizes, byte offsets, verdict table and grep output are.
>    `body_mtime_ns` is recorded at **nanosecond** resolution in the ledger itself, so
>    unlike area V's `stat -c%Y` column the mtime series **is** re-derivable from the
>    committed artefacts — though the *files* it describes are not on disk in a clean
>    clone, since git does not preserve mtimes.

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

**211 cells, 211 distinct digests, 0 duplicates, 0 empty bodies.** 2,853,978 B total
(2.85 MB); smallest 78 B, largest 828,225 B, median 1,882 B. `tables.txt` §T1/§T4.

Every cell answered `200 application/javascript` except `/2076.…js`, which answered
`404` for the reason in §2 and was re-requested under the correct name. **All 211 cells
carry a verdict for the committed token set**, which is this area's close condition.

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
| 1 | `D.guardianCumulusPeriodicAPI="system.gc.gz.transition.flags"` | main bundle, byte **2189123**, module `51551` | OBSERVED |
| 2 | `f=(0,e.Mz)(t,gt=>gt.configuration)`, `be=(0,e.Mz)(f,gt=>gt.guardianCumulusPeriodicAPI)` | main, byte **93819**, module `4265` | OBSERVED |
| 3 | module `4265`'s export table contains `z2:()=>be`, and also `cO:()=>ne` and `X2:()=>ye` | main, byte **91298** | OBSERVED |
| 4 | `.z2` occurs **0 times** in the main bundle | main (re-measured; area V's claim) | OBSERVED |
| 5 | chunk `6746` module `16746` binds `_=o(4265)` | chunk, byte **579** | OBSERVED |
| 6 | chunk `6746` module `56358` binds `F=o(4265)` | chunk, byte **66109** | OBSERVED |
| 7 | **read 1** `select(_.z2).pipe(({displayMessage:l})=>…)` | chunk, byte **22260** | OBSERVED |
| 8 | **read 2** `this.store.select(F.z2).pipe(({displayMessage:v})=>…)` | chunk, byte **70054** | OBSERVED |

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

**Read 2** is a service method `getGuardianEndpoint()` in module `56358`, byte-for-byte
the same logic. Both destructure `displayMessage` and read **exactly the published
leaves** of `system.gc.gz.transition.flags` — `carepartnerDisplayMessageUrl`,
`personalDisplayMessageUrl`, `csrDisplayMessageUrl`, `useCumulusUrls` — which is a
structural match to area T's published subtree, not merely to a token.

**And the value is used, in the same chunk**, at byte **69200ff** in `getMessageRequest`:

```js
const L = h.useCumulusUrls && this.isCsrEnabled, E = h.messageEndpoint;
let y = `${this.userService.getIsM2MEnabled()
      ? `/patient/m2m/connect/data/gc/patients/${encodeURIComponent(v)}`
      : "/patient/connect/data"}?cpSerialNumber=NONE&msgType=last24hours&requestTime=${…}`;
return h.useCumulusUrls && (y = O!==Be.CARE_PARTNER || L ? E
                              : E.replace("{patientUsername}", encodeURIComponent(v))),
       L ? this.connectHttpService.getPeriodicDataWithPost({ reqUrl:y, … })
         : this.connectHttpService.getPeriodicDataWithGet(y);
```

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

### `discover` (12) and `pde` (5) — both dictionary noise, both accounted for

Both appear in exactly **one** chunk, `8141.650c358996e4c19a.js` (828,225 B), and every
hit is a **substring of a zxcvbn password-dictionary entry** in a comma-separated word
list. The `cs`/`ci` counts are equal for both, so the case-sensitivity control adds
**nothing** here — there is no second reading hiding behind the first.

- `pde` ×5 → `dropdead` (72313), `helpdesk` (96374), `herpderp` (128269),
  `topdevice` (130050), `hampden` (338216).
- `discover` ×12 → `discover`, `discovered`, `discovery`, `discovers`, `discovering`,
  `discoveries`, `rediscovered`, `discoverer`, `rediscovery`, `discoverers`,
  `rediscover`, `undiscovered`.

**These are the same five and the same twelve words area V found in the two portal
builds**, now shipping in the patient chunk corpus too — only the byte offsets differ.
They are literals in a password-strength wordlist, **not directives**. Same false-hit
class as `docs/09` §5 records for `ngp`/`guardian`, and a bare grep on either name would
have reported an integration that is not there.

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
python3 findings-log/2026-10-13-area-k-patient-chunks/tables.py "$TMPBODIES" \
        findings-log/2026-10-13-area-k-patient-chunks/results.jsonl \
        findings-log/2026-10-13-area-k-patient-chunks/chunks-swept.txt > tables.txt
bash    findings-log/2026-10-13-area-k-patient-chunks/spacing.sh \
        findings-log/2026-10-13-area-k-patient-chunks/results.jsonl > spacing.txt
```

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
| Spacing floor **2.636 s** by kernel body-mtimes — 214 gaps, **0** under 2.5 s, **0** under the 2 s floor | OBSERVED | `spacing.txt` |
| The harness `date` series disagrees: **min 1.835 s**, 22 under 2.5 s, **7 under the 2 s floor**, **16 negative durations**, 22 bodies written before their own `t_sent`; **no cause asserted** | OBSERVED | `spacing.txt`; `results.jsonl` |
| Series validated: harness span 648.073 s vs kernel mtime span 647.799 s, difference 0.274 s | OBSERVED | `spacing.txt` |
| The two long gaps are the harness restart (34.017 s) and the sweep→follow-up gap (35.622 s), both **over** the declared delay | OBSERVED | `results.jsonl` seq 4→5, 214→215 |
| Negative twin 404s at 196 B with one digest, byte-identical to area V's certainly-absent control | OBSERVED | `results.jsonl` seq 1 |
| Positive control resolves and **carries the token set** — so a zero sweep is a zero, not a broken matcher | OBSERVED | `results.jsonl` seq 2; `grep-out.txt` |
| Runtime re-fetched; **211 entries re-derived from `f.u`**, `f.p=""` (asset root) | OBSERVED | `runtime-map.txt`; `results.jsonl` seq 3 |
| Controls 1–3 reproduce area V's three digests **byte for byte**; the build has not bumped in 5½ hours | OBSERVED | `results.jsonl` seq 1, 2, 3 |
| 211 cells, **211 distinct digests**, 0 duplicates, 0 empty bodies, 2,853,978 B | OBSERVED | `tables.txt` §T4 |
| **The committed list's URL form is wrong for one entry**: `2076.…js` vs the runtime's `common.…js`, same hash; the id form 404s at control 1's digest, the emitted name resolves 200 / 21,157 B | OBSERVED | `runtime-map.txt`; `results.jsonl` seq 51, 215 |
| **Lazy chunk `6746.c6795ff7e9ff468d.js` reads the `system.gc.gz.transition.flags` selector twice**, at bytes 22260 and 70054, in modules `16746` and `56358` | OBSERVED | `grep-out.txt` §2; `tables.txt` §T3 |
| Both reads bind **module id 4265**; module `4265` is defined in the **main bundle** at byte 91298 and its export table maps `z2:()=>be` | OBSERVED | `grep-out.txt`; main bundle bytes 579, 66109, 91298, 93819 |
| `z2` resolves to `be=(0,e.Mz)(f,gt=>gt.guardianCumulusPeriodicAPI)` and `D.guardianCumulusPeriodicAPI="system.gc.gz.transition.flags"` | OBSERVED | main bundle bytes 93819, 2189123 |
| The value read **flows into the URL that is POSTed** — `useCumulusUrls` and `messageEndpoint` gate `getPeriodicDataWithPost` | OBSERVED | `tables.txt` §T3 (`getMessageRequest`, byte ~69200) |
| **No lazy chunk reads the discovery document**: `baseUrlPde`, `/connect/pde`, `baseUrlCumulus`/`Cms`/`Aem`/`CareLink`, `discover/android`, `clcloud`, `api/carepartner` are **0 / 0** across all 211 | OBSERVED | `grep-out.txt`; `tables.txt` §T2 |
| `discover` (12) and `pde` (5) are zxcvbn dictionary substrings in one chunk, `cs == ci` so no second reading hides behind the first; the same 5 and 12 words area V found in the portal builds | OBSERVED | `grep-out.txt` §2; `tables.txt` §T3 |
| Four of the nine `transition.flags` leaves appear, all in chunk `6746`; the **other five are 0 across all 211** | OBSERVED | `tables.txt` §T2, §T3 |
| `patient-timeline` and `dialog-lite` are **0 / 0 across all 211 chunks**; the main bundle's five `patient-timeline` hits reproduce area V's offsets exactly and classify as Angular component selectors | OBSERVED | `grep-out.txt` §2 |
| Area V's "`.z2` read 0 times in the main bundle" — **re-measured, still true**, scope corrected not retracted | OBSERVED | `grep-out.txt`; area V `consumers-out.txt §2` |
| The URL `…/connect/csr/v2/display/message` that `messageEndpoint` carries | PUBLISHED | `docs/04`; [findings-log/2026-10-12-published-pointers/FINDINGS.md §1] |
| The clinic build carries the **same** `2076→common` special case, and `CHUNK-CORPUS` records an unexplained SPA-fallback entry in the 224-chunk clinic sweep | OBSERVED | `findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md:1118`; `CHUNK-CORPUS-FINDINGS.md:13` |
| `carelink.minimed.com` and `carelink-trials.minimed.com` carry this chunk's logic | **INFERRED** — assumption: the three patient deployments serve one build, which area V measured for `.eu`/`.com` only. **Not probed here** | area V `FINDINGS.md` §Scope limits 4 |
| Whether `csrEnabled` is true in any real session, i.e. whether `getGuardianEndpoint()` ever executes | **INFERRED — and unobserved in both directions.** No session was authenticated; `AGENTS.md` §11 forbids it | — |
| Area T's reading that `baseUrlPde`'s deadness is a retired service rather than an ignore contract | **unchanged, still unresolved** — this pass produced no evidence about intent | `docs/03` §9a |