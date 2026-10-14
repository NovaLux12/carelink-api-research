# Area K — the clinic 225-chunk corpus, mined for control flow

**Date:** 2026-10-14 · **Claim issue:** #121 · **Host probed:** `carelinkhp.minimed.eu` (clinic portal, one host only)
**Probe mode:** read-only GET. No POST, no token exchange, no auth header, no cookie, no port scan, no DNS brute force, no wordlist.
**Scheduling:** exclusive host lock `.loop/host-carelinkhp.minimed.eu.lock`; `sleep 2.5` held **inside** the lock before every request; `TS_SENT` emitted inside the lock immediately before `curl` execs.
**Byte-offset convention:** 0-indexed, start-inclusive. ⚠ **Corrected 2026-10-14 after independent verification:** an earlier version of this line claimed every offset points "at the start of the token or statement named". Several do not — e.g. `getLogBookConfig` is cited at 6,673 but begins at 6,756 (+83), and `getUrlWithPatientId` is cited at 6,657 but is defined at 6,678 (+21); seven more drift −33…−40. The offsets are reproducible and were each re-checked at the byte by the verifier against the hash-pinned body, so the findings stand; what was wrong is the *convention* claim, not the measurements. Offsets below are as-recorded, and a reader re-deriving one should expect a small negative or positive drift rather than an exact start.

Every figure below is re-derivable from the artefacts in this directory. Where a number is quoted from another pass it is quoted from that pass's **committed counter file**, never from the prose that summarises it — the error S4 §7.1 records.

---

## 0. Headline: the build did not move, and the corpus is body-verified

**OBSERVED. 225 of 225 chunk cells return `application/javascript`, 225 distinct body SHA256 digests, 0 duplicates, 0 empty bodies, and every one of the 225 body digests is byte-identical to the 2026-10-13 record.**

| comparison vs `2026-10-13-area-k-clinic-denominator/results.jsonl` | cells differing |
|---|---:|
| emitted filename | **0** of 225 |
| URL content hash | **0** of 225 |
| **body SHA256** | **0** of 225 |
| decoded body size | **0** of 225 |
| `Content-Type` | **0** of 225 |
| HTTP status | **0** of 225 |

Source: `crosscheck.json`, produced by `crosscheck.py` over both ledgers, offline, zero requests.

So the corpus is **not drifted**, and the 2026-10-13 denominator (225 JS chunks, 0 SPA fallback) stands re-confirmed one day later by an independent fetch.

### 0a. The map was re-derived from the build's own `f.u`, and diffed by HASH

`derive-map.py` read control C4's runtime body (8,597 B, `47939ec8…`), extracted `f.u`, and compared the re-derived map with `committed-map.txt` (copied byte-for-byte from the 2026-10-13 pass; both files sha256 `428a254b58e4f93473b59ceb207e2b51d461da0ae0000c579254f95dc179cb7b`).

```
f.p = ""                       -> the asset ROOT, no prefix
f.u = e => (2076===e?"common":e) + "." + { …225 entries… }[e] + ".js"
```

The ternary is **read out of the source**, not assumed — `derive-map.py` matches `(\d+)===\s*e\?\s*"([^"]*)"\s*:\s*e` and records the answer in `map-diff.json`. The special case is id `2076` → name `common`.

| re-derived vs committed | result |
|---|---|
| entries | 225 vs 225 |
| id → hash mapping identical | **yes** |
| hash SET identical | **yes** |
| 0 duplicate hashes | yes |
| emitted-name differences | **0** (the committed map already carried `common` for 2076) |
| runtime's own key order == committed order | **yes** |

**The hash is the join key, not the name** — a name diff cannot distinguish "same file, wrong name" from "two different files" (`docs/09` §4, trap row 3). Here both agree, and the sweep therefore proceeded on the committed list, re-fetching all 225 under the names `f.u` emits.

---

## 1. Request accounting

| | |
|---|---|
| **Requests used** | **231 of a 231 cap** (a 260 ceiling; the pass stopped at its own declared 231) |
| Method | GET only — `send.sh` carries no `-X`, no `-d`, no `--data`, no auth header, no cookie |
| Composition | **6 controls + 225 sweep cells**, one ledger row each |
| Unspent | 0 |

Every request that left this machine has a row in `results.jsonl` at **millisecond resolution** (`date -u +%Y-%m-%dT%H:%M:%S.%3NZ`). No request was issued by any tool other than `probe.sh`; nothing was issued by hand, so there is no row to append after the fact. The ledger is append-only and resumable (`probe.sh` reads the highest `seq` already present and continues), because a harness that truncates its own ledger on start-up is how a pass under-reports its own budget.

### 1a. Delay — declared ≥2.5 s vs MEASURED, both series

Measured by `crosscheck.py` over the committed ledger, offline, zero requests.

| series | gaps | min | max | under the declared 2.5 s | under the repo's 2.0 s floor | negative gaps |
|---|---:|---:|---:|---:|---:|---:|
| `t_sent` (harness clock) | 230 | **1.766 s** | 11.766 s | **30** | **5** | 0 |
| **kernel body-write mtime** | 230 | **2.635 s** | 11.772 s | **0** | **0** | 0 |

**Stated plainly, as `docs/09` §4 requires:** the declared delay is **2.5 s apart** (`sleep 2.5` inside the host lock before every request). The `t_sent` series measures **30 gaps below it and 5 below the repo's `>= 2 s` floor**, the smallest at **1.766 s** (seq 86 → 87); the five sub-floor gaps are 1.766, 1.937, 1.965, 1.986, 1.989 s. The kernel body-write mtime series — which is independent of the harness's clock, because `curl -o` makes the kernel set each body's mtime — measures **0 gaps below 2.5 s and 0 below 2.0 s**, minimum 2.635 s.

**No cause is asserted for the divergence between the two series.** `run.log` cannot distinguish truncation from a clock step from a post-hoc edit, and this pass does not claim to know which it is. The max gap of ~11.8 s in both series is the interval between the controls phase and the sweep phase, which ran as two separate invocations of `probe.sh` — that one is explained by the harness itself, and it is the only gap in the run with a stated cause.

The row-level figures are in `crosscheck.json` (`spacing_t_sent`, `spacing_body_mime`), which lists every sub-declared gap with both sequence numbers.

### 1b. Controls — numbered as actually sent, and what each one PROVES

Six controls, **all six sent before any data cell**, in this order. `results.jsonl` seq 1–6.

| # | seq | path | status | content-type | bytes | sha256 | what it PROVES |
|---|---|---|---|---|---:|---|---|
| **C1** | 1 | `probe-absent-9f8e7d6c5b4a.js` | 200 | `text/html; charset=UTF-8` | 5,518 | `0f2c5f62…` | **The oracle is `Content-Type`, never status.** This host answers `200` for *every* unknown path, so a status-only reading would score this as a live asset. It also re-pins the SPA shell's own digest to the value recorded on 2026-10-13 — the shell has not moved either. |
| **C2** | 2 | `main.fb5f8cb7eb60c4d5.js` | 200 | `application/javascript` | 3,397,615 | `2a7fa8e7…` | **The fetch-and-grep pipeline can detect the target tokens AT ALL.** Area P already records this bundle carrying `system.logbook.entry.validation.config` at byte 2,768,979; re-measured here at the identical offset and the identical digest. Without this control a zero over 226 bodies would be a broken matcher, not a finding. |
| **C3** | 3 | `12.cfb28fafc1fe9cf5e.js` | 200 | `text/html; charset=UTF-8` | 5,518 | `0f2c5f62…` | **"Does not exist" is distinguishable from "exists" on this exact path shape.** A real chunk id (12) with exactly ONE character of the content hash mutated, so the comparison is like-for-like and no path outside the committed list is invented. `probe.sh` asserts the mutation actually happened before sending, because a control that silently rebuilt the real path would be a false control. Byte-identical to C1. |
| **C4** | 4 | `runtime.a752bb828cca4b2c.js` | 200 | `application/javascript` | 8,597 | `47939ec8…` | **The corpus is CURRENT, not inherited.** The chunk map is re-derived from the build's own `f.u` and diffed by hash against the committed list — offline, zero requests (§0a). Without it the 225-cell sweep would be a re-read of another pass's note. |
| **C5** | 5 | `2076.a62bb847b4ea289e.js` | 200 | `text/html; charset=UTF-8` | 5,518 | `0f2c5f62…` | **The `f.u` name substitution is load-bearing on THIS corpus**, not merely inherited from the patient build. The id form of chunk 2076 does not exist here; the name `f.u` emits (`common.a62bb847b4ea289e.js`) does, and is cell 57 of the sweep. A sweep that trusted a committed id-form list would close on 225 cells carrying a verdict, one of which would be a verdict about a file that does not exist. |
| **C6** | 6 | `12.cfb28fafc1fe9cf5.JS` | 200 | `text/html; charset=UTF-8` | 5,518 | `0f2c5f62…` | **A name defect reads as ABSENT here.** A real chunk name with the extension uppercased. This namespace is case-sensitive, so a filename-casing slip produces the SPA shell rather than a chunk — which is why §0's per-cell digest comparison, not a filename comparison, is the verdict. |

⚠ **C6 is a control, not a chunk, and is NOT counted among the 225.** Its ledger row carries `"id": null` and a `role` beginning `C6-`. Chunk id 12 is separately and correctly fetched as lowercase `12.cfb28fafc1fe9cf5.js` at **seq 7**: 200 `application/javascript`, 2,224 B, sha256 `16da534b3d91d4a78d3bf4510f9617e2a16303e5386af4d0272552db4f15283e` — byte-identical to the 2026-10-13 record. `crosscheck.json` reports `sweep_cells_that_did_not_return_a_chunk: []`: **zero of the 225 sweep cells returned the SPA shell**, so no cell in the denominator carries a false verdict.

### 1c. A one-cell observation about content encoding

Across 231 responses on this host, in this run: **206 `br`, 1 `gzip`, 24 with no `content-encoding` at all.** The single `gzip` is C6, the uppercase-extension row. `docs/09` §4's brotli row records 183 `br` / 32 identity / **0 gzip** across 215 responses on `carelink.minimed.eu` (the *patient* host) — a different host from this one. **This is a fact about one cell in one run on one host and is not generalised in either direction**; the `gzip` in it is the reason the repo's "`curl --compressed` or every parse fails" rule is still the right instruction rather than a brotli-specific one.

### 1d. Transient bodies

Response bodies were written to a scratch directory **outside the repository** and are not committed. What is committed: per-request status, content-type, size, SHA256, a 90-byte body head, and the response heads in `headers/`. The 90-byte head matches the 2026-10-13 clinic pass's convention. No raw archive capture is committed.

---

## 2. The primary target: `system.logbook.entry.validation.config`

**This is the pass's main result, and it is POSITIVE. It COMPLETES area P's recorded negative for the clinic build; it does not refute it. Area P scoped its claim to "the reproducible, hash-verifiable web corpus" and stated the route literal is "followed by the next module; there is no adjacent field definition" — both hold, and the consumer is in a different file (see §5 and the barrel-hop note). P was correct about what it searched; its corpus was incomplete. The word "refuted" used earlier in this pass, in the commit subject and in the `docs/11` addendum, is withdrawn: a measurement and the inference drawn from it are separate artefacts, which is the rule area Z's measurement was kept under after a later sweep narrowed it.**

Area P recorded that the clinic and support bundles each contain the route literal only — `"hcp/configuration/public/system.logbook.entry.validation.config"` at offsets 2,768,979 / 2,769,017 — with no adjacent field definition, validator or default. That measurement was taken on the **eager main bundle**. The clinic build is a different webpack build and it puts the *consumer* in a lazy chunk.

### 2a. Where it is called, and what happens to the result — OBSERVED

All offsets in this section are in **`9481.6977c1a7bd7461f8.js`**, 188,467 B, the clinic logbook feature chunk, webpack module **79481**.

The whole service, offsets **6,108–6,930** — every one read at its byte offset:

| offset | method | code |
|---:|---|---|
| 6,108 | GET | `getLogbookEntries(o,n){ return this.http.get( this.getUrlWithPatientId($.KTJ,o) + n.toQueryParams() ) }` |
| 6,210 | GET | `getAvailableDataPoints(o,n){ return this.http.get( this.getUrlWithPatientId($.GC1,o) + n.toQueryParams() ).pipe( map(r => r?.dates) ) }` |
| 6,350 | PUT | `updateLogbookEntry(o,n){ return this.http.put( this.getUrlWithPatientId($.lwO,o), n ) }` |
| 6,432 | DELETE | `removeLogbookEntry(o,n){ return this.http.delete( this.getUrlWithPatientId($.lwO,o) + "/" + n.id.toString() ) }` |
| 6,532 | POST | `addLogbookEntry(o,n){ return this.http.post( this.getUrlWithPatientId($.lwO,o), n ) }` |
| 6,612 | GET | `lastEntries(o,n,r,s){ return this.http.get( this.getUrlWithPatientId($.PzB,o) + \`?date=${n}&type=${r}&zoneOffset=${s}\` ) }` |
| 6,657 | — | `getUrlWithPatientId(o,n){ return o.replace("((patientId))", n) }` |
| **6,673** | **GET** | **`getLogBookConfig(){ return this.http.get($.C40).pipe( catchError( () => of({}) ) ) }`** |
| **6,787** | **GET** | **`getLogBookEntryConfig(){ return this.http.get($.df4).pipe( catchError( () => of([]) ) ) }`** |

`$.C40` is `hcp/configuration/public/system.logbook.entry.validation.config` and `$.df4` is `hcp/configuration/public/logbook.supported.entry.types` — both exported from the eager main bundle's route table, webpack module 66703 (offsets 2,768,953 and 2,769,022). **OBSERVED: the route literal at 2,768,979 is not a dead end.** In the eager bundle `C40` has zero property reads outside a re-export map (0 of the 6 clinic logbook route constants do; 111 of the module's 188 route constants do), so the grep in area P could not have found this call site. The call site is in chunk 9481.

**The error fallback is `{}`** (offset 6,673) — an empty object — and `[]` for the entry-types config (6,787). OBSERVED and important: the clinic client treats *any* failure of the validation-config request, including the `null`/404 that area E measured unauthenticated, as "no configuration", and carries on. It never checks whether the document had fields.

The value is then threaded, unchanged, through the store and into the form:

| offset | step |
|---:|---|
| 15,295 | `patchState(() => ({ logbookConfiguration: h }))` — the response is stored **verbatim**, no field read here |
| 12,000 | `selectLogbookConfiguration$ = this.select(l => l.logbookConfiguration)` |
| 179,977 | `this.logbookConfiguration$ = this.componentStore.selectLogbookConfiguration$` (the `lib-logbook-list` component) |
| 184,356 | template binding `("logbookConfiguration", t.bMT(4,21, n.logbookConfiguration$))` |
| 159,541 / 160,513 | passed into the side-sheet dialog as `logbookConfiguration: this.logbookConfiguration` |
| **130,185 / 145,544** | **`ngOnInit(){ this.selectedEntryConfiguration = this.data.logbookConfiguration }`** |

### 2b. The FIELD SET — 36 reads of `selectedEntryConfiguration`, all read

`selectedEntryConfiguration` occurs **36 times** in chunk 9481. Reading each one: the document is an **object keyed by ENTRY TYPE**, and each per-type object carries the members below. The entry-type keys are members of the `u` enum at offset 4,890 (13 members, one of which — `AllEntries` — is a sentinel, so 12 real types, matching `docs/07`'s settled count).

| entry-type key | member read | what the code does with it | offsets |
|---|---|---|---|
| `SENSOR_INSERTION` | `.sensorLocations.options[]` | the drop-down options for `sensorInsertionLocation` | 102,656 |
| `SENSOR_INSERTION` | `.sensorLocations.freeText[]` | `.find(j => j.triggerOption === <control value>)` → shows the "other" free-text box | 81,623 · 106,154 |
| `SENSOR_REMOVAL` | `.sensorLocations.options[]` / `.freeText[]` | as above for `sensorRemovalLocation` | 102,823 · 106,443 |
| `SENSOR_REMOVAL` | **`.types`** | `Object.keys(config.SENSOR_REMOVAL.types)` — the **key set** of `types` decides the offered removal types | 103,483 |
| `SENSOR_REMOVAL` | `.types[<removalType>]` | `Object.keys(E??{}).length > 0 ? removalReason.setValidators([required]) : clearValidators()` — **config presence makes `removalReason` required** | 82,617 · 83,226 |
| `SENSOR_REMOVAL` | `.types[<removalType>].freeText[]` | `.find(l => l.triggerOption === removalReason)` → the validation applied to `removalDescription` | 99,642 · 104,193 |
| `SENSOR_PHYSICAL_DISTURBANCE` | `.sensorLocations.options[]` / `.freeText[]` | as above for `sensorPdLocation` | 102,478 · 106,741 |
| `SENSOR_PHYSICAL_DISTURBANCE` | `.type` | an **array** (`getSensorPhysicalDisturbanceType`) | 102,987 |
| `ADHESIVE_AND_TAPE` | `.sensorLocations.options[]` / `.freeText[]` | as above for `adhesivetapeLocation` | 103,334 · 107,037 |
| `ADHESIVE_AND_TAPE` | **`.questions[]`** | one form control per question, named `question_<index>` | 85,454 |
| `ADHESIVE_AND_TAPE` | `.questions[].label` | the emitted wire value of a question is its **`label`** | 97,600 |
| `ADHESIVE_AND_TAPE` | `.questions[].children[]` | `showChildren` gates each child on `conditionValue === <answer>` | 88,945 · 97,600 |
| `ADHESIVE_AND_TAPE` | `.questions[].children[].questions[]` | one further level of controls | 93,947 |
| `MEDICATION` | `.doseUnits.options[]` | the units offered for `medicationDoseUnit` | 103,183 |
| `MEDICATION` | `.doseUnits.freeText[]` | `.find(j => j.triggerOption === medicationDoseUnit)` | 88,945 · 107,323 |

Every one of the 36 reads is optional-chained and `??`-defaulted, so a `{}` document yields empty dropdowns and no required-`removalReason` validator — the client degrades rather than throwing. That is consistent with the `{}` fallback at 6,673 and is why the `catchError` shape matters.

**Recovered field set of `system.logbook.entry.validation.config`, as the client reads it (OBSERVED):**

```
<ENTRY_TYPE>                                     one member per logbook entry type
  <ENTRY_TYPE>.sensorLocations.options[]          array
  <ENTRY_TYPE>.sensorLocations.freeText[]         array of { triggerOption, … }
  <ENTRY_TYPE>.types                             object, keyed by removal type
  <ENTRY_TYPE>.types[<t>].freeText[]             array of { triggerOption, … }
  <ENTRY_TYPE>.type                              array          (physical disturbance only)
  <ENTRY_TYPE>.questions[]                       array          (adhesive & tape only)
  <ENTRY_TYPE>.questions[].label                 string
  <ENTRY_TYPE>.questions[].children[]            array
  <ENTRY_TYPE>.questions[].children[].conditionValue
  <ENTRY_TYPE>.questions[].children[].questions[]
  <ENTRY_TYPE>.doseUnits.options[]               array          (medication only)
  <ENTRY_TYPE>.doseUnits.freeText[]              array
```

**What this is and is not.** It is the field set **the shipped client reads**, and the control flow that consumes it. It is **not** the document: the server may carry members this build ignores, and every member's *value* — the option lists, the `triggerOption` vocabularies, the `conditionValue` pairs, the `types` keys — remains **token-gated** and is not settled by this pass. What is additionally recovered is the **semantics** of three members, above: `types` presence drives requiredness, `freeText[].triggerOption` drives which conditional free-text field is validated, and `questions[].children[].conditionValue` drives conditional question visibility.

**A wire-value inference, labelled INFERRED and bounded.** Offset 103,483 filters a fixed three-element list — `logbook.sensorRemoval.type.scheduledRemoval`, `…earlyRemoval`, `…notApplicableSensorNotInserted` — against `Object.keys(config.SENSOR_REMOVAL.types)`. Those three strings are therefore the client's **candidate** `removalType` values and the document selects among them. That they are the **wire** values is INFERRED from a client-side comparison and is not confirmed by a response.

### 2c. Why area P could not have found this, stated as a mechanism

`docs/09` §5 item 2 — "a grep that hit without proving". Area P's negative was correct **for what it searched**: the eager main bundle. In that bundle the route constant `C40` is defined at 2,768,953 and is referenced exactly twice afterwards, both inside `r.d(...)` re-export maps at 1,956,239 (barrel module 42205) and 3,317,161 (barrel module 97298). The consumer is four barrel hops away in a *different file*. No amount of additional grepping inside `main.js` reaches it; the corpus had to be swept. That is the transferable half.

---

## 3. Control-flow findings elsewhere in the clinic corpus

Every offset below is read at its byte offset. Evidence class on each.

### 3a. A third-party source for area P's write-payload finding — OBSERVED, two independent sources

Chunk 9481, offset **95,545**, the clinic client's submit builder:

```js
else if (this.form.valid) {
  if (this.result = { entryTs: o, type: this.entryType, id: this.isEmpty ? 0 : this.data.id },
     this.result.comment = this.form.controls.comment.value,
     this.result.attributes = {},
     [u.INFUSION_SET_CHANGE, u.OTHER, u.SENSOR_PHYSICAL_DISTURBANCE, u.MEDICATION,
      u.ADHESIVE_AND_TAPE, u.SENSOR_INSERTION, u.SENSOR_REMOVAL].includes(this.result.type)
       ? this.result.attributes = null
       : Object.keys(this.form.controls).forEach(l => {
           ["entryTs","additionalTime","minutesTime","comment"].includes(l) ||
           this.result.attributes && (this.result.attributes[l] = this.form.controls[l].value) }))
  … type-specific nested objects …
  this.entChanged.emit(this.result)
}
```

Area P recovered this from the **patient** lazy chunk `k-9799-ae484032a07c9d4f-js.b`. It is here again, in a **different build, a different chunk, a different file**, with the same seven-type exclusion list, the same four excluded control names, and the same `id: isEmpty ? 0 : data.id`. Neither artefact quotes the other. Counting rule of `AGENTS.md` §2.1: **different authors** (two Medtronic build outputs), **different artefacts** (patient chunk 9799 vs clinic chunk 9481), **neither derived from the other** — so this is **2 independent sources**, and the write-payload construction is corroborated rather than single-sourced. The `POST`/`PUT` bodies are that object unchanged (`addLogbookEntry` at 6,532 and `updateLogbookEntry` at 6,350 both pass `n` straight through), so **the verb, not `id`, distinguishes create from update** — corroborating the pool-K pass's INFERRED point (2026-10-14, `pool-k-controlflow` §4.2) on a second corpus.

### 3b. Three server error tokens the client branches on — OBSERVED

Chunk 9481:

- offsets **13,276** and **13,962**: `400 === err.status && "error.entry.not.found" === err.message` → the entry is dropped from local state and a translated toast is raised; **any other failure raises a generic error action**. So `400` + that exact message is a contract the client expects.
- offset **6,210**: the `/filled` response is read for a **`dates`** array (`r => r?.dates`), i.e. "which dates have data points" is the only member consumed.

### 3c. A request-body interceptor that trims strings one level deep — OBSERVED

Eager main bundle, webpack module 67628, offset **2,856,744**:

```js
intercept(N, ue) {
  const We = N.body;
  if (!We) return ue.handle(N);
  if ("object" == typeof We) {
    const _t = Object.keys(We).reduce(
      (Vt, hn) => (Vt[hn] = "string" == typeof We[hn] ? We[hn].trim() : We[hn], Vt), {});
    N = N.clone({ body: _t })
  }
  return ue.handle(N)
}
```

Every request with an object body is **rebuilt key by key**, each **string value `.trim()`ed**; non-strings pass through by reference, so **nested objects and arrays are not trimmed**. This is a request-shape rule no endpoint list carries, and it applies to the logbook `POST`/`PUT` bodies of §3a.

### 3d. Two more interceptors: the `X-System-ID` header and the auth token — OBSERVED

- offset **2,861,318**: `intercept(N,ue){ return N.url.includes("connect/retina") || (N = N.clone({ setHeaders: { "X-System-ID": "ProWeb" } })), ue.handle(N) }` — **every request whose URL does not contain `connect/retina` gets `X-System-ID: ProWeb`**. This is the header Oracle B names (412 when missing or invalid), and this is where the client supplies it.
- offset **1,527,043** and **1,527,774**: `addAuthToken(Ft){ let Mn = this.tokenStorage.getToken(); const ri = Ft.params.get("skipHeader"), Lt = localStorage.getItem("token"); return !j.c.production && Lt && (Mn = Lt), !Mn || ri ? Ft : Ft.clone({ headers: Ft.headers.set("Authorization", "Bearer " + Mn) }) }` — **the `Authorization: Bearer` header is added only when a token exists AND the request's own query params do not carry `skipHeader`**, i.e. a per-request opt-out; and **in a non-production build a token in `localStorage.token` overrides the token-store token**.

### 3e. A state-dependent error map — OBSERVED

Offset **1,527,043**, same interceptor, `switch (status)`:

- `"InvalidToken" === error?.type` → the token is removed from storage;
- `Forbidden`/`Unauthorized` → **rethrown without redirect if the URL contains one of two specific route constants**, else if the browser is on the clinic-outcomes page the user is navigated there, else a logout is dispatched;
- `InternalServerError`/`ServiceUnavailable`/`GatewayTimeout` → a `tech-error` flag is stored and the router navigates to `/tech-error/<status>`;
- default → rethrown.

The two exempted route constants are named at bytes 1,527,043 and 1,527,338. **I did not resolve those two to their literals** — the export chain terminates in a barrel that re-exports them from a second constants module I did not trace to its literals, and I record the gap rather than guessing it.

### 3f. Conditional logic that gates a *route*, not just a payload — OBSERVED

Eager main bundle, module 98458:

| offset | code | what it implies |
|---:|---|---|
| **3,332,316** | `getInpenUserStatus(Ae,J,he){ return J && he ? this.http.get(a.nJJ,{params:{patientId:Ae}}) : of(null) }` | the GET is **suppressed** unless two flags are truthy; the observable yields `null` with no request |
| **3,332,457** | `this.http.post(Me ? a.YIV : a.Gar, {duration:J, patientId:Ae})` | **one boolean selects between two different endpoints** |
| **3,332,981** | `getReportGenerationConfig$(Ae){ return Ae ? (cached ? of(cached) : this.http.get(a.BsL)…) : of(null) }` | a null argument suppresses the request entirely |

### 3g. A dev host and a vendor key compiled into the shipped bundle, behind a hard-false flag — OBSERVED

Module 98458 carries two `https://dev.commoncore.medtronic.eu/…` URLs at offsets **3,323,593** and **3,323,890**, and the known-published vendor API key at offset **3,323,593** (not reproduced in any artefact here — `scrub-check.sh` records the pattern name that pins it). They are reachable only through the mock branch:

- `this.isMock = !1` in the constructor, offset **3,325,665**;
- `getMetaDataServiceConfig()` / `getCCBrokerServiceConfig()` return the dev object only when `isMock` is true (offsets 3,326,378 and 3,331,617);
- `isMock` occurs **5 times in the whole bundle, all in module 98458**, and is never assigned `true` anywhere.

So the shipped clinic client contains a dev endpoint and a vendor credential that it never uses. Recorded and **left alone** — `AGENTS.md` §1's "dev/stage/test hosts are enumerated passively and listed, never probed" applies, and no request was made to either host.

My own instrument produced one false hit here, recorded because the class is this repo's most repeated: a naive `dev|test|stage` URL regex returned **3** matches, and the third, `https://angular.dev/best-practices/security#…` at offset 1,246,525, is a documentation reference, not a host.

### 3h. Menu-gating: two entries are mutually exclusive — OBSERVED

Eager main bundle, module 82194, offset **3,120,859**, the patient-detail side-nav builder:

```js
… Ce && !we && Le.push({ label:"patient.followup-history", … id:"pd-followup-history" }),
   we { const Je = Le.findIndex(vt => "pd-patient-profile" === vt.id);
        Le.splice(Je, 0, { label:"clinical.patient.logbook", link:e.SbO.logbook, … id:"pd-logbook-list" }) }
```

The logbook entry is inserted **only when `we` is truthy**, immediately before the profile entry; follow-up history requires `!we`. The two are mutually exclusive. `we` resolves, through four re-export hops, to module 92582 byte **3,291,541** — `x = select(productType => productType === STUDY)` where that module's own enum assigns **both** `POW` and `STUDY` the string `"pow"`; and `Ce` resolves to module 20695 byte **1,241,059** — `!!m.oH || state?.remoteMonitoringEnabled`.

**INFERRED, bounded:** because the logbook nav entry is gated on the clinic product context, the logbook routes are plausibly reachable only there. The gate is on the *menu*, not on the routes — the routes have no gate at their call sites (§3i) — so the inference stops there.

### 3i. How the clinic build addresses its routes — OBSERVED

Eager main bundle, module 66703 (the route table): **180 `hcp/`-prefixed route literals**; **20 distinct** carry a `((param))` template across **23 occurrences** (corrected 2026-10-14 after independent verification — an earlier "21" counted occurrences under a rule that was never stated, `AGENTS.md` §6 item 7); **exactly 1** carries a query string (`hcp/configuration/public/user-identifier-settings?countryCode=((countryCode))`). Substitution is a single `String.replace` per call site — 15 such sites, offsets 2,405,549 and 3,016,707–3,188,583 — so a route carrying two `((…))` markers would only get its first replaced. The **three** `/logbook/entries*` routes (`entries`, `entries/filled`, `entries/last`) carry `((patientId))` — corrected from "all four", which miscounted a fourth route that carries no such marker — and chunk 9481's helper at offset 6,657 does the same substitution.

This is the mechanism behind §3 of the cross-client differential: **the clinic client resolves every route through an exported-constant table; the patient client inlines literals.**

### 3j. The 89 call-site field names — re-measured, per file, with the false-hit class handled

`field-census.py` / `field-census.json` swept 59 names over all **231** bodies (225 chunks + main + runtime + controls). The 2026-10-08 sweep recorded these as "89 distinct field names at HTTP call-sites" without saying which file carried each. This pass can, because the corpus is body-verified:

- Every one of the logbook/marker names — `removalType`, `removalReason`, `adhesivetapeLocation`, `sensorInsertionLocation`, `sensorRemovalLocation`, `sensorPdLocation`, `timecapUnscrewed`, `timecapUnscrewed_additionalTime`, `timecapUnscrewed_minutesTime`, `entryTs` — occurs in **exactly one file of 231**: chunk **`9481.6977c1a7bd7461f8`**. Case-insensitive counts run ahead of case-sensitive for several of them (e.g. `timecapUnscrewed` 42 cs / 48 ci, `sensorPdLocation` 17 / 19), which is the same chunk also carrying `timeCapUnscrewed` and `sensorPdLocationOther` in a different casing.
- `entryTs` at offset 5,634 is part of the clinic's own entry-envelope enum: `e.id="id", e.type="type", e.comment="comment", e.entryTs="entryTs", e.attributes="attributes"` — the wire envelope the write payload of §3a is assembled into.
- `deviceFamily`: 2 occurrences in the eager main bundle, **32 in one chunk** (`2503.9475bb0f80c14743`), 0 elsewhere. Two different meanings: a selector `state?.deviceFamilyMapping` (main, offset 1,243,187) and a report filter default `Xr={deviceFamily:Ut.Ey.all, ageGroups:[Ut.Ey.all]}` (main, offset 2,874,214).

**Two control words were carried through the census deliberately, and one of them does not discriminate here:**

| control | hits | verdict |
|---|---:|---|
| `discover` | **12**, all in the eager main bundle | **The documented zxcvbn false-hit class, confirmed by reading every hit.** All 12 sit inside the bundled password-strength word lists (offsets 211,829 … 954,784). Exactly **1 of the 12** is the standalone word `discover` (offset 211,829, in a password list); the other **11 are substrings of longer words** — `discovered`, `discovery`, `discovers`, `discoveries`, `discoverer`, `discoverers`, `discovering`, `rediscovered`, `rediscover`, `rediscovery`, `undiscovered`. A naive `grep -o discover \| wc -l` therefore reports 12 "endpoints" of which **0 is an endpoint**. |
| `patient-timeline` | **0** | **This control does not fire on this corpus and is therefore not evidence of anything here.** It is a patient-plane name; its absence from the clinic build is consistent, but a control that cannot fire proves nothing about the matcher. Recorded as a failed control rather than quietly kept. |

---

## 4. The cross-client differential, and why it is reported as a **negative**

Per instruction, S4's own committed script was run over the clinic corpus — `extract-call-sites.py`, unmodified, parameterised by `S4_CORPUS`/`S4_OUT` — so that both sides are counted by ONE rule. `run-s4.sh` assembles two clinic corpora from the same bodies and runs it over each; `differential.py` does the set operation and the arithmetic.

### 4a. The two builds are genuinely different — checked FIRST, because a corpus compared with itself is a vacuous finding

Joined on **chunk id**, decided by **content hash**:

| | |
|---|---|
| clinic map entries / patient map entries | 225 / 210 (+1 patient entry with a non-numeric id, `common.206e355a4a593fbd.js`, counted separately and not silently dropped) |
| chunk ids present in both | **145** |
| **of those, ids with an IDENTICAL content hash** | **0** |
| ids with a different content hash | **145** |
| ids only in clinic / only in patient | 80 / 65 |
| eager main bundle | clinic `2a7fa8e7…` 3,397,615 B vs patient `0fb4fbd4…` 3,417,255 B |
| runtime | clinic `47939ec8…` 8,597 B vs patient `0dfea208…` 8,268 B |

Both builds publish the same global namespace name (`self.webpackChunkpow`) and both special-case chunk id 2076 to the name `common` — so a name-based join would have been meaningless and the hash is the only usable discriminator. Worked examples: id 12 → clinic `12.cfb28fafc1fe9cf5` / patient `12.c22952a522974f5f`; id 40 → `40.9cffbe2c518352c0` / `40.a88955898736c22e`; id 50 → `50.dcab8cd0fa8efd2c` / `50.2b6cd1f5da5f1501`. **0 of 145 shared ids agree, so the differential is not vacuous.**

### 4b. The set operation, as S4's own keys produce it

| set | n | by method |
|---|---:|---|
| clinic shapes S4's rule can name | **5** | GET 2, POST 3 |
| patient shapes S4's rule can name | **144** | GET 72, POST 49, PUT 14, DELETE 9, PATCH 0 |
| **shared** | **0** | — |
| clinic-only | 5 | `GET hcp/countries/dialCodes`, `GET {1}?locale={2}`, `POST /hcp/sso/auth/otc/send`, `POST hcp/patients/checkPhoneNumber`, `POST {1}?{2}` |
| patient-only | 144 | the whole `/patient/*` surface — listed in `differential.json` |

Set arithmetic: `5 + 0 = 5` and `144 + 0 = 144`.

### 4c. **The 5-vs-144 comparison must NOT be read as "the clinic client calls 35× fewer endpoints", and this pass does not claim it.**

The arithmetic that kills it, read from the two committed `counters.json` files:

| | patient (S4, committed) | clinic (this pass) |
|---|---:|---:|
| corpus files / bytes | 215 / 6,300,854 | 228 / 7,786,390 |
| `http_call_sites_total` | 233 | 225 |
| `sites_with_literal_path` | 154 | **5** |
| `sites_with_baseurl_resolved_path` | 20 | 0 |
| `sites_with_constant_resolved_path` | 1 | 0 |
| `sites_with_unresolved_variable_path` | **58 (25%)** | **220 (98%)** |

**220 of the 225 clinic call sites are UNRESOLVED under S4's rule.** That is the rule working correctly, not failing: S4's D2 requires the first argument to be a literal and its D3 says a call whose path is any other variable is "reported UNRESOLVED and is never guessed". The clinic client does not inline literals — it names an exported constant from the route table (§3i), so `this.http.get($.KTJ, …)` is outside D2's scope by construction. The visible first-argument expressions in `s4-full/unresolved.tsv` are `alias.CONST`, `alias.CONST.replace("((patientId))", u.toString())`, and a handful of bare identifiers.

**So the differential under S4's rule is a statement about the two builds' *source conventions*, not about their API surfaces.** The honest reading is: 5 of the clinic's call sites are inline literals and 220 route through a constant table; 154 of the patient build's 233 are inline literals. On the literal-only subset the two sets are **disjoint** (0 shared), which is a fact about namespace rather than about schema — the clinic's 5 are all `hcp/*` and the patient build's 144 are all `patient/*`.

**A shared schema cannot be shown or denied with the rule as it stands.** Closing this needs a resolver for the clinic's constant-table indirection (module 66703 exports 188 route constants, 180 of them `hcp/` literals). Writing one is a *rule change* to a script another pass owns, not a clinic-side side-effect, and per `AGENTS.md` §9's precedent ("changing the gate's own pattern in the same PR the gate passed is a decision for a maintainer, not a side effect of a research pass") it belongs to the owner. **This is the pass's successor recommendation and it is stated as a gap, not worked around.**

### 4d. S4's two arithmetic checks, re-derived from the committed files

The instruction asked for both, read out of the committed `counters.json` rather than out of S4's prose.

**Patient side — both hold:**

```
four columns: 154 + 20 + 1 + 58 = 233  ==  http_call_sites_total 233     ✓
by_method:    72 + 49 + 14 + 9 + 0 = 144  ==  distinct_pairs 144       ✓
leading slash: 99 + 45 = 144 == distinct_pairs                         ✓
interpolation: 44 + 100 = 144 == distinct_pairs                        ✓
```

**Clinic side — both hold, on the figures the same script emitted:**

```
four columns: 5 + 0 + 0 + 220 = 225  ==  http_call_sites_total 225      ✓
by_method:    2 + 3 + 0 + 0 + 0 = 5  ==  distinct_pairs 5             ✓
leading slash: 1 + 4 = 5 == distinct_pairs                            ✓
interpolation: 2 + 3 = 5 == distinct_pairs                            ✓
```

So S4's recorded note about its own receiver pattern and its constant-resolved labelling **does not surface as an arithmetic failure on either corpus** — both sets of columns sum correctly. That is what can be said from these files; whether an individual dropped call site exists inside a correctly-summing column is not decidable from the counters alone, and is not claimed.

---

## 5. Instrument defects found and fixed inside this pass

Recorded because each is the class `AGENTS.md` §6 item 2 describes, and each was caught only because a control existed.

1. **A literal detector that inverted every label after the first escape.** `mine.py`'s first implementation scanned global `"…"` spans. It reported 4 of the bundle's known route literals as bare code and labelled a 4-character run `,jn=` as a literal — somewhere upstream one quote was consumed as a *closing* quote where it opened a literal, flipping the parity of every subsequent span, and **nothing reported the flip**: the spans simply became the gaps. Caught by `mine.py self-test`, which was written before the answers were believed. Fixed by a local-evidence label that needs no parity (if the nearest preceding unescaped quote is a closer, no literal can contain the hit). The dead implementation is left in place as `_quote_spans()` with a docstring saying why not to reinstate it. `self-test` now passes **6 of 6**: two synthetic positives and two synthetic negatives (provable by construction, so a detector that labels everything "literal" cannot pass), two real-bundle positives, one absent-token negative.
2. **A scrub check that read no patterns and printed PASS.** `scrub-check.sh` resolved the repo root one level too high, found no `scrub-patterns.txt`, iterated zero patterns, and printed `scrub-check: PASS`. A dead net reporting clean. Fixed, and the script now **exits non-zero if the pattern file is unreadable or fewer than five patterns parse**, because the previous version had a note about this class and the note was not the fix.
3. **The uppercase-extension control read as a chunk.** C6's row is the one an automated reader would mistake for a swept cell. It carries `id: null` and a `C6-` role, and `crosscheck.py` counts only `SWEEP-` rows as swept — but the distinction is stated here too, because a reviewer should not have to derive it.

---

## 5a. Correction (2026-10-14) — first independent verification round

A fresh-context verifier reviewed this pass at SHA `031023a` and returned **NOT
CLEAN**. Its substantive findings were accepted and corrected here; this section
records them because the retraction history is the evidence (§3).

**Accepted and corrected:**

1. **The route-delta figure was false.** An earlier draft of the `docs/11`
   addendum published "168 shared, 1 chunk-only, 0 main-only". Measured on the
   **complete** corpus the correct set difference is **0 shared, 3 chunk-only, 184
   main-only**. Cause: the figure was computed while the sweep was mid-flight at
   **115 of 231 cells**, over a directory still being written to. A partial
   corpus inflates the "shared" figure, because routes not yet fetched cannot be
   counted as absent. This is `AGENTS.md` §6 item 7 — a count generalised from a
   subset — and the error ran in the dangerous direction.
2. **"Refuted" → "completes".** See §2 and the withdrawal at the head of this
   document. Area P was correct for what it searched.
3. **The mtime series is not the spacing authority.** `probe.sh`'s comment claimed
   it was. `mtime_gap == t_sent_gap + Δlatency` with Δlatency up to 0.895 s — larger
   than the margin under test — so it cannot exonerate a short `t_sent` gap. The
   comment is corrected in place and both series are now reported with neither
   elevated to authority.
4. **`body_mtime_ns` carries an unexplained constant 3600.000 s offset** from
   `t_sent` on a self-consistent clock. Provenance not established; the offset
   cancels in gaps so the reported figures stand, but it is not accounted for.
5. **Offset convention overstated** — see the corrected convention at the head.
   The measurements themselves were re-verified at the byte against the
   hash-pinned body and stand.
6. **"21 templates" → 20 distinct / 23 occurrences**; **"four logbook routes" →
   three.** Both re-derived on the corpus.
7. **A citation naming the wrong module.** The `docs/11` successor attributed
   offsets 2,761,878–2,769,023 to module 97298; they are in **module 66703**
   (which begins at byte 2,759,689). Fixed. A citation that resolves but says
   something else is worse than a broken one.
8. **"Not re-derivable from a clean clone" was wrong** for the mtime series —
   `results.jsonl` commits `body_mtime_ns` for all 231 rows and the verifier
   re-derived it with zero requests.
9. **The `corpus/full` set is 228 files = 225 chunks + main + runtime + one HTML
   SPA shell.** The SPA shell is deliberate (the analogue of S4's 404 page) but
   §4c's table quotes the file count without the composition. Noted rather than
   changed, since the shell can only add false hits.

**Disputed and declined:** the verifier proposed that `docs/06`'s OpenAPI negative
be re-examined. That is a **separate area with its own claim lifecycle** and is
filed as a successor in `docs/11`, not actioned here — §11 permits a pass to
propose, not to spend another area's budget.

---

## 6. What this pass did NOT settle

Stated as gaps, not smoothed over.

1. **The *values* inside `system.logbook.entry.validation.config`.** The field set the client reads is recovered (§2b); the option lists, `triggerOption` vocabularies, `conditionValue` pairs and `types` keys are all token-gated. `docs/10`'s remaining row stands for the values.
2. **Whether the document carries members this build ignores.** §2b is the client's view of it, which is an upper bound on usefulness and a lower bound on the document's size.
3. **The cross-client schema differential.** Not computed, and §4c says precisely why and what would close it.
4. **Two exempted route constants** named at main-bundle bytes 1,527,043 and 1,527,338 (§3e) — not resolved to literals.
5. **The read-side echo casing** of the logbook write payload. §3a establishes the client's serialisation; the server's returned casing is still unconfirmed.
6. **Whether `entryTs` is submitted in the server's timezone or the client's offset string.** Observable in the read URLs' `zoneOffset` parameter (offset 6,612) but not pinned.
7. **Source maps.** Not re-probed — out of scope for this pass, and the 2026-10-08 conclusion is unchanged by anything here.

---

## 7. Artefacts and how to re-run them

| artefact | what it is |
|---|---|
| `probe.sh`, `send.sh` | the harness, verbatim. `send.sh` is the exact string exec'd under the host lock. Six controls first, then the 225 in committed order. GET only. |
| `results.jsonl` | 231 rows, one per request, ms-resolution timestamps, `body_mtime_ns`, `role`, status, content-type, size, sha256, 90-byte head |
| `headers/` | one response head per request |
| `run.log` | per-request line + phase boundaries |
| `committed-map.txt` | the 2026-10-13 map, copied verbatim (sha256 matches the source) |
| `derive-map.py`, `map-diff.json` | re-derives the map from control C4's runtime body; diffs by hash |
| `crosscheck.py`, `crosscheck.json` | per-cell comparison against the 2026-10-13 ledger + both spacing series |
| `mine.py` | module index, token census with literal-vs-code labels, `self-test` |
| `field-census.py`, `field-census.json` | 59 field names over 231 bodies, per-file, with two control words |
| `run-s4.sh`, `s4-chunks-only/`, `s4-full/` | S4's own extractor run unmodified over two clinic corpora |
| `differential.py`, `differential.json` | build-distinctness proof, the set operation, the arithmetic |
| `scrub-check.sh` | screens every artefact here, including `.txt`/`.json`/`.jsonl`, which the repo's own gate does not read |

Zero requests for every analysis script. To re-measure spacing:

```bash
python3 crosscheck.py results.jsonl ../2026-10-13-area-k-clinic-denominator/results.jsonl crosscheck.json
```