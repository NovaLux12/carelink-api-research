# Area V — does any vendor client follow the published `baseUrlPde`?

**Pass date:** 2026-10-13 · **Claim issue:** #42
**Branch:** `research/v-baseurlpde-clients` · **Ledger:** `results.jsonl` (13 rows, one per HTTP request)
**Harness:** `probe.sh` + `send.sh` (requests, as sent) · `extract.sh`, `consumers.sh`, `spacing.sh` (offline, zero requests)
**Outputs:** `grep-out.txt`, `consumers-out.txt`, `spacing.txt`, `chunks.txt`

---

## Verdict

**The recorded negative the area predicted — and the reason is sharper than "nobody calls it".**

**No vendor-shipped web bundle in this corpus contains `baseUrlPde`, or `/connect/pde`,
or any `pde` token that is not a password-dictionary entry.** But the negative is
mostly a statement about a *different* document: **no web bundle in this corpus reads
the discovery document at all.** `baseUrlPde`, `baseUrlCumulus`, `baseUrlCms`,
`baseUrlAem`, `baseUrlCareLink`, `discover`, `discover/android`, `clcloud` and
`api/carepartner` are **0 quoted-literal hits in all four bundles**. The one
`baseUrl` the patient bundle does contain is `this.baseUrl`, assigned from
`getBaseCmsUrl()` and used to fetch a CMS media file (bytes 2027033, 2027209) — a
different `baseUrl`, not a published pointer. So the discovery document's client is
not on any of these hosts, and `docs/03` §9a's open inference is **re-framed, not
settled**: this pass cannot see the consumer it is about, because the corpus that
would contain it is not a web bundle.

**One genuine positive, on the sibling axis the area's own reasoning pointed at.**
The patient bundle **does** follow a published pointer — but not the one area T's
`transition.flags` subtree carries. It follows
`csr.cumulus.periodic.data.endpoints`: selector defined, exported, read once, and
at that read it destructures `display_message` and **POSTs** it. The same bundle
**names** `system.gc.gz.transition.flags`, defines a selector over it, exports it,
and **never reads it anywhere in the file**.

---

## Request accounting

**13 of a 24 cap.** **GET only** throughout — literal `GET`, no `-X`, no `-d`, no
`--data`, no `-H`, no token, no authentication, no port scan, no DNS lookup, no
wordlist. Nothing was requested that is not either a control or an asset name read
out of an entry document captured in the same run.

**Declared delay 2.5 s, sleep inside the per-host `flock`** — that is, requests to
the same host were issued **2.5 s apart** by construction (sleep and curl are one
`flock lock send.sh …` invocation per request, so the gap is real and not merely
intended — pool brief). Four hosts: `carelink.minimed.eu`, `carelink.minimed.com`,
`carelinkhp.minimed.eu`, `carelink-support.medtronic.eu`.

**Measured spacing floor, two independent series** (`spacing.txt`, counting rule:
one gap per consecutive pair in request order, so N requests on a host give N−1
gaps; 9 gaps over 4 hosts):

| series | n | min | max | under the declared 2.5 s | under the repo's `>=2 s` floor |
|---|---|---|---|---|---|
| **`t_sent`** (emitted *inside* the lock, immediately before `curl` execs) | 9 | **2.566 s** | 5.953 s | **0** | **0** |
| **kernel body `st_mtime_ns`** (independent of the harness clock) | 9 | **2.599 s** | 6.167 s | **0** | **0** |

Series validated before use, per `docs/09` §4: harness span (first `t_sent` → last
`t_done`) **39.318 s** against kernel mtime span **39.303 s** — agreement to 15 ms,
so the mtime series is this run's own. **No negative request durations** and no
body written before its own `t_sent`, so neither series carries the corrupt-`t0`
signature area D characterised. **No sub-declared gap occurred and no cause is
asserted for anything.** Four of the nine gaps exceed 2.5 s because the previous
request's own transfer time is inside the same lock; that is the design, not slack.

> **Harness improvement over area G, disclosed because it changes what the numbers
> mean.** Area G's `probe.sh` recorded `t_sent = t_queued` — a pre-lock timestamp —
> and measured spacing done-to-done as a conservative proxy. This pass emits
> `TS_SENT` from inside the lock immediately before `curl` execs (`send.sh`), so
> `t_sent` is the real send instant and the series is auditable per the pool brief.
>
> **One defect in this pass's own ledger, disclosed rather than smoothed over:**
> `results.jsonl`'s `body_mtime_epoch` column came from `stat -c%Y`, which
> **truncates to whole seconds** and therefore cannot resolve a 2.5 s sleep. The
> sub-second figures above are re-stat'ed at nanosecond resolution by `spacing.sh`
> from the still-present bodies. That means the mtime column is **not
> re-derivable from the committed ledger alone**, and git does not preserve mtimes
> on a fresh clone, so the mtime series is valid only on the machine that ran the
> probe. The `t_sent` series needs neither caveat.
>
> **One scrub applied to the ledger after the run, disclosed:** `run.log`'s start
> line carried the absolute path of the temp-body directory. `AGENTS.md` §7 forbids
> a machine path in any committed file, so it is redacted to `<TMPDIR>/…`. Nothing
> else in `run.log`, `results.jsonl` or `headers/` ever contained a path.

Asset bodies (3.4 MB each) are deliberately **not committed** — digests, sizes,
byte offsets and the full grep output are.

---

## Controls, in the order they were sent

Eight controls, **all sent before any asset on their host**, so the verdict is not
contaminated by the data it judges.

| # | Host | Control | Result | What it proved |
|---|---|---|---|---|
| 1 | `carelink.minimed.eu` | `GET /main.deadbeefdeadbeef.js` (fabricated, content-hash shaped) | **404** `text/html; charset=iso-8859-1`, 196 B, sha `80c3fe2a…` | The status code **is** an oracle on the patient plane — the clean Apache 404, not the 5518 B SPA page. Discriminate on `Content-Type`, and a `200` here can only be a real asset. |
| 2 | same | `GET /` | 200 `text/html; charset=UTF-8`, **1833 B**, sha `8dfb96a7…` | Real entry document (not the 5518 B page), and it **names today's assets** — so the bundle path is derived from this capture, never from a filename in this repo |
| 5 | `carelink.minimed.com` | same fabricated name | **404**, 196 B, **same digest** `80c3fe2a…` | Same oracle, same control body: the absent-path response is one artefact shared by both patient deployments |
| 6 | same | `GET /` | 200, **1833 B**, **same digest** `8dfb96a7…` | Patient `.eu` and `.com` are **byte-identical deployments** — not two lookalikes |
| 8 | `carelinkhp.minimed.eu` | same fabricated name | 200 `text/html`, **5518 B**, sha `0f2c5f62…` | SPA-fallback trap **live** here: a status-only read of an asset fetch would be worthless |
| 9 | same | `GET /` | 200, 5518 B, **same digest** `0f2c5f62…` | On this host family the fallback page *is* the index — so absent ≡ root is the expected result, and it anchors build identity |
| 11 | `carelink-support.medtronic.eu` | same fabricated name | 200 `text/html`, 5518 B, sha `f637c8d0…` | Same trap, the **other** build's digest — the two are distinguishable |
| 12 | same | `GET /` | 200, 5518 B, **same digest** `f637c8d0…` | Build identity anchored on host 4 |

**Verdict rule** (as committed in #42): an asset counts as real only on
`Content-Type: application/javascript` + sha256 + size — never on status, never on
length alone. All five assets pass it:

| Asset | Host | Bytes | sha256 (decompressed) | Content-Type |
|---|---|---|---|---|
| `main.6595daf83bd6d4b1.js` (seq 3) | `carelink.minimed.eu` | 3,417,255 | `0fb4fbd483b5f5d2…` | `application/javascript` |
| `runtime.79e2f9040b1dad8f.js` (seq 4) | `carelink.minimed.eu` | 8,268 | `0dfea208804facf8…` | `application/javascript` |
| `main.6595daf83bd6d4b1.js` (seq 7) | `carelink.minimed.com` | 3,417,255 | `0fb4fbd483b5f5d2…` | `application/javascript` |
| `main.fb5f8cb7eb60c4d5.js` (seq 10) | `carelinkhp.minimed.eu` | 3,397,615 | `2a7fa8e7af519c2b…` | `application/javascript` |
| `main.759cddab23085086.js` (seq 13) | `carelink-support.medtronic.eu` | 3,410,666 | `a054555a0f22176e…` | `application/javascript` |

### Build re-anchoring — what reproduced and what is new

| Artefact | 2026-10-12/13 record | 2026-10-13 | Verdict |
|---|---|---|---|
| clinic portal build | `2a7fa8e7af519c2b…`, 3,397,615 B (area A, area G) | identical | **reproduces** |
| support portal build | `a054555a0f22176e…`, 3,410,666 B (area G) | identical | **reproduces** |
| clinic/support entry docs | `0f2c5f62…` / `f637c8d0…`, 5518 B (area A, area G) | identical | **reproduces** |
| **patient build fingerprint** | `main.6595daf83bd6d4b1.js`, 3,417,255 B (`JSMAP-HUNT §5`, 2026-10-08) | same name, **same size**; sha256 was never recorded before | **size reproduces; digest is new and is the new baseline** |
| **patient chunk map** | "a 211-entry chunk map" (`JSMAP-HUNT §5`, 2026-10-08) | **211 entries** | **reproduces** |
| patient chunk `12.c22952a522974f5f.js` (2,224 B) and `985.47eb741416e9cd44.js` (18,851 B) | both listed with those hashes | **both hashes still current** in `chunks.txt` | **reproduces** |

**So the patient build has not bumped in five days**, and the 2026-10-08
`security/js/patient-main.js` capture this area hoped to grep offline is
**superseded by an identical build** rather than stale. The claim's stated
deviation — "the captures are not on disk, re-fetching them is the whole cost" —
is confirmed: this clone holds **no `.js` file at all** (`find . -name '*.js'` →
empty; `security/js/` does not exist). Bodies stay uncommitted, as area A and area
G did, for the same reason.

---

## The negative, and every hit that has to be accounted for

Full output in `grep-out.txt`. Method per `docs/09` §5: three counts per token
(case-sensitive `cs`, case-insensitive `ci` as the control, complete quoted literal
`q` as the strict test), byte offsets, and the maximal enclosing identifier for
every hit the insensitive count kept and the sensitive count did not.

### `pde`

| body | `pde` cs | `pde` ci | `"pde"` |
|---|---|---|---|
| `eu-main` / `us-main` (patient) | **0** | 25 | 0 |
| `hp-main` (clinic portal) | **5** | 32 | 0 |
| `sup-main` (support portal) | **5** | 32 | 0 |
| `eu-runtime` | 0 | 0 | 0 |

**All 5 case-sensitive hits in each portal build are substrings of zxcvbn
password-dictionary entries** — byte, enclosing word:

| byte | enclosing word | byte | enclosing word |
|---|---|---|---|
| 269182 | `dropdead` | 325138 | `herpderp` |
| 293243 | `helpdesk` | 326919 | `topdevice` |
| 535085 | `hampden` | | |

Both portal builds carry the same five at the same bytes. Context at 269182:
`…,zxcvbn1,dropdead,hitman47,…`. **Literal, not a directive** — a word in a
password-strength dictionary, which is exactly the false-hit class `docs/09` §5
records for `ngp`/`guardian` in this same bundle. A case-insensitive grep would
have reported "32 PDE references".

**All 25 case-insensitive hits in the patient bundle are substrings of seven
unrelated identifiers**, one distinct word each: `mapDeviceModelName` (×2),
`propDecorators` (×8, Angular's reflect-metadata decorator),
`getGroupDelayControl` (×2), `removeStylesOnCompDestroy` (×5, Angular Material),
`isDesktopDevice` (×4), `WPDesktop` (×3, a Windows-Phone user-agent string) and
`LoopDetected` (×2). **Case-sensitive `pde` in the patient bundle is 0.**

### `baseUrlPde`, `/connect/pde`

**0 / 0 / 0 in all five bodies**, case-sensitive, case-insensitive and quoted. Same
for `baseUrlCumulus`, `baseUrlCms`, `baseUrlAem`, `baseUrlCareLink`, `discover`,
`discover/android`, `clcloud`, `api/carepartner`. The only `baseUrl` hits are the
two CMS reads already described.

### `system.gc.gz.transition.flags` and its nine leaves

| token | patient | clinic | support | runtime |
|---|---|---|---|---|
| `system.gc.gz.transition.flags` | **1** @ 2189151 | 0 | 0 | 0 |
| `"system.gc.gz.transition.flags"` (quoted) | **1** | 0 | 0 | 0 |
| `guardianCumulusPeriodicAPI` | **2** @ 93819, 2189123 | 0 | 0 | 0 |
| `useCumulusUrls` | **0** | 0 | 0 | 0 |
| `csrDisplayMessageUrl` | **0** | 0 | 0 | 0 |
| `personalDisplayMessageUrl` / `carepartnerDisplayMessageUrl` | **0** | 0 | 0 | 0 |
| `pullGMInfoFromCumulus`, `pullSMSHistoryFromCumulus`, `sendDiagnosticLogsToCumulus`, `sendPeriodicToCumulus`, `sendSMSFromCumulus` | **0** each | 0 | 0 | 0 |

**Literal, not a directive**: byte 2189151 is
`…,D.guardianCumulusPeriodicAPI="system.gc.gz.transition.flags",D.logbookPageSize="logbook.entries.page.size",…`
— a key-constant table, where a minifier assigns each published config key name to
a property. **No leaf name appears anywhere**, so the client never spells them.

---

## The positive: a published pointer the patient bundle *does* follow

This is the part of the corpus where a token is not enough — a key named in a table
proves nothing about whether code acts on it (`docs/09` §5 item 2), so the chain is
resolved to a read, and a zero is proven as a zero rather than a failed lookup.

`consumers.sh §2`. The config-observer module is **id 4265**, bytes 91296–97138,
exporting 70 selectors. Two pointer subtrees:

| published subtree | constant | selector | export alias | property reads in the file |
|---|---|---|---|---|
| `csr.cumulus.periodic.data.endpoints` | `csrCumulusPeriodicDataAPI` @ 2188929 | `ne` @ 93547 | `cO` | **3 — one genuine** |
| `system.gc.gz.transition.flags` | `guardianCumulusPeriodicAPI` @ 2189123 | `be` @ 93800 | `z2` | **0** |

**Followed — `csr.cumulus.periodic.data.endpoints`.** Of the three `.cO` sites,
two (bytes 1522284, 1522483) are Angular Material's own `e.cO` injection token
inside a different module and are **disclosed here rather than counted as
consumers**. The third, byte **3373465**, is the real one, inside
`getUploadDeviceInfo(V)`:

```js
getUploadDeviceInfo(V){
  return (0,n.p)([this.getProfile(), this.store.select(p.cO).pipe((0,h.s)(1))])
    .pipe((0,S.n)(([R,{display_message:X}])=>{
      const Q={patientId:V||R.username, role:this.isCarePartner()?L.P.CARE_PARTNER:L.P.PATIENT, username:R.username};
      return this.http.post(X,Q)
    }), ...)
}
```

**OBSERVED:** the shipped patient bundle selects the `csr.cumulus.periodic.data.endpoints`
subtree out of the public config, destructures `display_message`, and **POSTs to
whatever that field holds** with `{patientId, role, username}`.
**PUBLISHED** (area T, pinned): that field's value is
`https://clcloud.minimed.eu/connect/csr/v2/display/message`, and
`connect/csr/v2/display/message` is **live and POST-only** on all three cumulus
hosts (area N). So area T's *inference* — "the vendor's own client is instructed
by public config to address `csr/v2`" — is now backed by the instruction being
**executed in shipped client code**, not only by the config value. **The client
does not hardcode the URL**: it reads it, so a config change would move the call.

**Named but not followed — `system.gc.gz.transition.flags`.** The key string occurs
once, the constant name twice (the assignment and the selector), the selector is
exported as `z2`, and **the substring `.z2` does not occur anywhere in the file** —
0 sites, printed in full at `consumers-out.txt §2`, so the zero is checkable and not
a lookup that returned `None` (`docs/09` §5 item 3). The two identical CSR URLs,
one in this subtree and one in the followed subtree, mean the client follows **one
of two pointers carrying the same value and ignores the other**.

### Same treatment for the rest of the table

**53 of the key constants have a value string occurring exactly once** in the file
(`consumers-out.txt §3`). Three of those have a **constant name** that also occurs
exactly once — named in the table and referenced by no code at all:
`FSN_ADMIN` (`"fsn_admin"`), `personalDobValidation`
(`"personal.dob.validation.enabled"`), and
`personalPatientTimelineHostURL` (`"personal.patient.timeline.host"`, see the area-F
addendum below). The remaining 50 are read through their selector; how far the
signal reaches is a control-flow question this pass does not attempt and does not
answer.

---

## How much of the published config surface the client acts on at all

**56 of area W's 69 published key names appear in the patient bundle as complete
quoted literals; 13 do not, and their raw substring count is 0 too** (`consumers-out.txt §1`).
Counting rule, stated so it can be reproduced: the key must appear as the complete
string literal `"<key>"`. The rule matters — **`captcha` is 5 quoted and 152 raw**,
because 151 of the raw hits are `captcha.*` translation keys. A raw-substring
census would have manufactured 152 reasons to believe the captcha config key is
used in code; 5 is the honest number, and it is the kind of inflation
`docs/09` §5 exists to stop.

Absent (13): `country.reports`, `csr.application.browser.check.configuration`,
`logbook.reset.time.on.type.change`, `personal.captcha.enable`,
`personal.communication.enabled`, `personal.landing.page.background.image`,
`personal.linking.request.interval`, `personal.myinsights.banner.supported.devices`,
`personal.notification.enabled`, `personal.retina.endpoint.config`,
`personal.user.skip.consent.click.mandate`, `praas.uri.path.reports.ping`,
`system.auth0.url.whitelist`.

---

## Scope limits, stated where a reader would otherwise over-read this

1. **Eager main bundles only.** Four `main.*.js` and one `runtime.*.js`. The
   **211 lazy chunks are not in this corpus** — `chunks.txt` is their complete
   current inventory, not their contents. Every "0 reads" above is a statement about
   the eager bundle.
2. **The discovery document's actual consumer is not reachable from any host
   probed.** Its own path names it: `discover/android/3.6`. This pass therefore
   cannot see whether a mobile client follows `baseUrlPde`, and says so rather than
   generalising a web-bundle negative to "no client".
3. **Two of the five portal hosts were not refetched** — `carelink.medtronic.eu`
   and `carelink.medtronic.com`, which area A showed serve the byte-identical clinic
   build. This pass re-anchored build A's digest on `carelinkhp.minimed.eu` today
   and it reproduces, so the identity still holds, but it is a one-day-old link in
   the chain and is labelled as one rather than restated as verified.
4. **`carelink-trials.minimed.com`** (the third patient deployment, and the only
   patient host not refetched) was not probed. Area O records all three patient
   deployments serving byte-identical `/patient/reports/*` bodies; a byte-identical
   *bundle* across three hosts is a stronger claim than that and is **not** made.
5. **This pass measured three distinct builds**, not four hosts: patient `.eu` and
   `.com` are byte-identical (index and main, same digests), so the patient plane is
   one build on two deployments, and the portal family is two builds.
6. **What code does with a followed key is not established.** `csr/v2` gets a
   named call site with a quoted payload; nothing here claims anything about the
   other 55 keys' consumers beyond the read count in `consumers-out.txt §2`.

---

## Addendum recorded for area F (not this area's scope)

The brief's scope guard applies: this pass does not answer "who calls
`patient-timeline` / `dialog-lite`". Two facts belong to area F and are handed over
in `docs/11`:

- **`patient-timeline` is 5 hits in the patient bundle and all 5 are Angular
  component selectors**, not a URL — `["app-patient-timeline"]` (byte 1718181),
  `"app-patient-timeline-filter-toolbar"` (1719243), two `t.nrm(0,"app-patient-timeline",25)`
  template calls (1963408, 1963661) and one `t.VBU({selectors:[["app-patient-timeline-filter-toolbar"]]})`
  (3340159). `dialog-lite` is **0 hits** in all five bodies. A grep on the bare
  name would have reported a `patient-timeline` integration.
- The bundle **does** carry `personal.patient.timeline.config` as a quoted literal
  (1 occurrence), reads it through selector `Nt` (exported as `bQ`, 3 reads), and a
  template reads `.featureEnabled` off it to choose between rendering the
  Patient-Timeline tab and not (byte 1966110:
  `…t.vxM(null!=(b=t.bMT(10,20,m.patientTimelineConfig$))&&b.featureEnabled?9:-1)…`).
- The bundle also names **`personal.patient.timeline.host`** — 1 occurrence, and its
  constant `personalPatientTimelineHostURL` occurs **once**, so nothing reads it.
  ⚠ The published key is **`personal.patient.timeline.config.host`** (`docs/04`;
  recorded as a further AWS gateway). `personal.patient.timeline.host` is **not** in
  area W's 69-name list, i.e. the bundle names a config key the public document does
  not publish. Which of the two is real is **not** settled here.

---

## Reproducing

```bash
TMPBODIES=$(mktemp -d)
bash findings-log/2026-10-13-area-v-pde-clients/probe.sh    # 13 requests, cap 24
TMPBODIES=$TMPBODIES bash findings-log/2026-10-13-area-v-pde-clients/extract.sh   > grep-out.txt
TMPBODIES=$TMPBODIES bash findings-log/2026-10-13-area-v-pde-clients/consumers.sh > consumers-out.txt
TMPBODIES=$TMPBODIES bash findings-log/2026-10-13-area-v-pde-clients/spacing.sh   > spacing.txt
```

Asset paths are derived from the entry document captured in the same run, so a
bundle bump changes them automatically and a stale name cannot be fetched by
mistake. `results.jsonl` rows carry `t_queued` / `t_sent` / `t_done` at
millisecond UTC resolution; `headers/` holds one `<tag>.h` per request.

---

## Evidence table

| Claim | Class | Source |
|---|---|---|
| 13 of a 24 cap, GET only, 8 controls first per host | OBSERVED | `results.jsonl` seq 1–13; `run.log` |
| Spacing floor **2.566 s** (9 send-series gaps, 0 under 2.5 s, 0 under the 2 s floor) | OBSERVED | `spacing.txt`; `results.jsonl` `t_sent` series |
| Spacing floor **2.599 s** by kernel body-mtimes; spans agree to 15 ms, so the series is usable | OBSERVED | `spacing.txt` |
| No negative request durations, no body written before its own `t_sent` | OBSERVED | `spacing.txt` |
| Patient-plane status oracle is sound (fabricated asset → 404, 196 B, one digest across both hosts) | OBSERVED | `results.jsonl` seq 1, 5 |
| SPA-fallback trap live on both portal hosts (fabricated asset → per-build 5518 B page, absent ≡ root) | OBSERVED | `results.jsonl` seq 8≡9, 11≡12 |
| Clinic build `2a7fa8e7…` and support build `a054555a…` reproduce areas A and G | OBSERVED | `results.jsonl` seq 10, 13 |
| Patient `.eu` and `.com` are byte-identical deployments (index `8dfb96a7…`, main `0fb4fbd4…`) | OBSERVED | `results.jsonl` seq 2≡6, 3≡7 |
| Patient main digest `0fb4fbd4…`, 3,417,255 B — **new baseline**; no digest was recorded before | OBSERVED | `results.jsonl` seq 3 |
| Patient fingerprint and 211-chunk map reproduce the 2026-10-08 record — the build has not bumped | OBSERVED | `chunks.txt`; `results.jsonl` seq 4; `findings-log/probe-2026-10-08/recon/JSMAP-HUNT.md §3.3, §5` |
| `baseUrlPde` and `/connect/pde`: **0 hits** in all five bodies | OBSERVED | `grep-out.txt` |
| No `baseUrl*` discovery key, no `discover`, no `clcloud`, no `api/carepartner` in any bundle | OBSERVED | `grep-out.txt` |
| The bundle's only `baseUrl` is a CMS media base from `getBaseCmsUrl()`, bytes 2027033 / 2027209 | OBSERVED | `grep-out.txt` |
| All 5 case-sensitive `pde` hits per portal build are zxcvbn dictionary entries (`dropdead`, `helpdesk`, `herpderp`, `topdevice`, `hampden`) | OBSERVED | `grep-out.txt`; `consumers-out.txt` |
| Case-sensitive `pde` is 0 in the patient bundle; its 25 insensitive hits are 7 unrelated identifiers | OBSERVED | `grep-out.txt` |
| `system.gc.gz.transition.flags` is a literal key constant at byte 2189151; its 9 leaves are 0 hits everywhere | OBSERVED | `grep-out.txt` |
| The client **follows** `csr.cumulus.periodic.data.endpoints`: 1 genuine read, `display_message` destructured and POSTed with `{patientId, role, username}` at byte 3373465 | OBSERVED | `consumers-out.txt §2` |
| That field's value is `…/connect/csr/v2/display/message`, and that route is live and POST-only on all three cumulus hosts | PUBLISHED | `findings-log/2026-10-12-published-pointers/FINDINGS.md §1`; `findings-log/2026-10-12-csr-cross-host/FINDINGS.md` |
| The client **does not follow** `system.gc.gz.transition.flags`: selector exported as `z2`, and `.z2` occurs 0 times in the file | OBSERVED | `consumers-out.txt §2` |
| Area T's inference that the vendor's client is *instructed* to address `csr/v2` is now backed by the instruction being executed in shipped code | OBSERVED (call site) + PUBLISHED (config value) | `consumers-out.txt §2`; `docs/04` |
| 56 of 69 published config keys appear as quoted literals in the patient bundle; 13 absent | OBSERVED | `consumers-out.txt §1` |
| `captcha` is 5 quoted / 152 raw — the counting rule, not the corpus, is the difference | OBSERVED | `consumers-out.txt §1` |
| `patient-timeline`'s 5 bundle hits are Angular component selectors, not a URL; `dialog-lite` is 0 | OBSERVED | `grep-out.txt` |
| The bundle names `personal.patient.timeline.host`, which is not a published key, and reads it nowhere | OBSERVED | `consumers-out.txt §2, §3` |
| **No web bundle reads the discovery document, so this corpus cannot see `baseUrlPde`'s consumer** | INFERRED | assumption: the consumer is the Android client the document's own path names (`discover/android/3.6`) and no mobile artefact is on any host probed — **not observed**, and stated as the limit rather than the finding |
| The area's INFERRED reading (dead `baseUrlPde` = retired service, not an ignore contract) | **unchanged, still unresolved** | `docs/03` §9a — this pass produced no evidence either way about intent |