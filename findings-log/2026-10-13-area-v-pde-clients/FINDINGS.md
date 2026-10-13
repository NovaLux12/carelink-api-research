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
> a machine path in any committed file, so it is redacted to the literal `<REDACTED>`,
> which is what `run.log` line 1 reads. Nothing else in `run.log`, `results.jsonl`
> or `headers/` ever contained a path. **Corrected in round 2:** the first redaction
> said `<TMPDIR>/…` while the file said `<REDACTED>` — two safe strings that were not
> the same string, i.e. prose describing its own source without having read it. And
> that redaction was applied **by hand to a committed artefact**, so any re-run wrote
> the machine path straight back; `probe.sh` now redacts **at the point of
> generation**. A hand-scrub of an artefact is a one-off, not a control.

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
unrelated identifiers**: `propDecorators` (**×8**, Angular's reflect-metadata
decorator), `removeStylesOnCompDestroy` (**×6**, Angular Material), `WPDesktop`
(**×3**, a Windows-Phone user-agent string), `mapDeviceModelName` (**×2**),
`getGroupDelayControl` (**×2**), `isDesktopDevice` (**×2**), `LoopDetected` (**×2**).
8+6+3+2+2+2+2 = **25**. **Case-sensitive `pde` in the patient bundle is 0.**

> **⚠ CORRECTED 2026-10-13 — see [Correction (2026-10-13)](#correction-2026-10-13)
> §B.** The multiplicities above originally read `removeStylesOnCompDestroy` **×5**
> and `isDesktopDevice` **×4**. Those were **wrong**, they summed to **26** against a
> stated total of **25**, and the two errors **cancelled** (+1/−2) so the total looked
> right. They were also **unsourced**: `grep-out.txt` §2 deduped by enclosing
> identifier and printed one offset each, so no per-identifier count existed anywhere
> in a committed artefact. `extract.sh` is fixed — §2 is now unfiltered, prints `×N`
> with every offset and the first-hit context, and **asserts that the multiplicities
> sum to the token total** so this class cannot recur silently.

### `baseUrlPde`, `/connect/pde`

**0 / 0 / 0 in all five bodies**, case-sensitive, case-insensitive and quoted. Same
for `baseUrlCumulus`, `baseUrlCms`, `baseUrlAem`, `baseUrlCareLink`,
`discover/android`, `clcloud`, `api/carepartner`. The only `baseUrl` hits are the
two CMS reads already described.

> **⚠ CORRECTED 2026-10-13 — see [Correction (2026-10-13)](#correction-2026-10-13)
> §A.** This paragraph originally read *"0 / 0 / 0 … Same for … **`discover`**"* and
> was **wrong**: `discover` is **0 in the patient bundles and the runtime, and 12 in
> each portal build**. All 12 are zxcvbn dictionary words, at **identical byte offsets
> in both builds** — so the conclusion survives and the negative gets *stronger*, but
> the number published here was wrong and had already been propagated to four
> canonical pages. Corrected counts are in the `discover` table below; the original
> wording is preserved verbatim in the Correction section and is not deleted.

**The corrected `discover` census** (case-sensitive; `grep-out.txt` §2 for the
enclosing identifiers and every offset):

| body | `discover` cs | what every hit is |
|---|---|---|
| `eu-main` / `us-main` (patient) | **0** | — |
| `hp-main` (clinic portal) | **12** | zxcvbn password-dictionary words |
| `sup-main` (support portal) | **12** | zxcvbn password-dictionary words, **same 12 at the same bytes** |
| `eu-runtime` | **0** | — |

The 12, identical in both portal builds: `discover` @211829, `discovered` @449173,
`discovery` @456020, `discovers` @469461, `discovering` @491815, `discoveries`
@492201, `rediscovered` @522387, `discoverer` @558582, `rediscovery` @581388,
`discoverers` @684648, `rediscover` @941540, `undiscovered` @954784. Each is a
comma-separated entry in the embedded wordlist — e.g. @211829 sits between
`oakland` and `ranger1`. **Literals in a password-strength dictionary, not
directives.**

**So the portal builds carry 17 dictionary-word hits each — 12 `discover` + 5 `pde` —
and zero of either token is anything else.** That is a stronger negative than "0", and
a reader can re-derive it from `grep-out.txt` alone.

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
  (1 occurrence) and reads it through selector `Nt`, exported as `bQ` — **3 property
  reads, at bytes 1968178, 3326686 and 3327799** — and a template reads `.featureEnabled`
  off the selected value to choose between rendering the Patient-Timeline tab and not
  (byte 1966110:
  `…t.vxM(null!=(b=t.bMT(10,20,m.patientTimelineConfig$))&&b.featureEnabled?9:-1)…`).
  **All four facts are now printed by `consumers.sh §2`** — the selector chain and every
  read site, under *`personal.patient.timeline.config`* and *the Patient-Timeline tab
  gate* in `consumers-out.txt` — so they are **sourced rather than asserted**
  (`AGENTS.md` §1). They were unsourced in the first two rounds, which was a defect in
  its own right however load-bearing-free and out-of-scope they were.
  ⚠ **3 counts `.bQ` occurrences, not consumers**: a two-character export alias is not
  unique across a bundle, and 2 of the 3 sites belong to other modules (`f`, bound to
  module 90669). That split is a **hand check**, and `consumers.sh` now says so where a
  reader meets the number instead of letting it stand as a consumer count.
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
| No `baseUrl*` discovery key, no `discover/android`, no `clcloud`, no `api/carepartner` in any bundle | OBSERVED | `grep-out.txt` |
| ⚠ **CORRECTED 2026-10-13:** `discover` is **0** in the patient bundles and runtime and **12** in each portal build — all 12 zxcvbn dictionary words, same bytes in both. Portal builds therefore carry **17 dictionary hits each** (12 `discover` + 5 `pde`), none a pointer | OBSERVED | `grep-out.txt` §2; `FINDINGS.md` §Correction (2026-10-13) §A |
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

---

## Correction (2026-10-13)

Two errors in this log, both found by a verifier reading the committed artefacts
against the committed prose. **Both were mine**, both were re-derived here on the
digest-matched bodies (`hp-main` `2a7fa8e7af519c2b…` / 3,397,615 B, `sup-main`
`a054555a0f22176e…` / 3,410,666 B, `eu-main` `0fb4fbd483b5f5d2…` / 3,417,255 B —
**digest asserted before any comparison** — ⚠ **that clause was FALSE and is withdrawn;
the assertion is now real, see [§F](#f--the-guard-advertised-a-digest-check-it-did-not-perform)**),
and both originals
stay visible above and here. `AGENTS.md` §3: corrections are appended, never edited
away.

### §A — `discover` was published as `0` in all five bodies. It is `12` in each portal build.

| | original text | corrected |
|---|---|---|
| `discover`, `hp-main` | 0 | **12** |
| `discover`, `sup-main` | 0 | **12** |
| `discover`, `eu-main` / `us-main` / `eu-runtime` | 0 | **0** (unchanged) |

**What was written.** FINDINGS.md: *"**0 / 0 / 0 in all five bodies**, case-sensitive,
case-insensitive and quoted. Same for `baseUrlCumulus`, `baseUrlCms`, `baseUrlAem`,
`baseUrlCareLink`, **`discover`**, `discover/android`, `clcloud`,
`api/carepartner`."* — and, in the evidence table: *"No `baseUrl*` discovery key,
**no `discover`**, no `clcloud`, no `api/carepartner` in any bundle | OBSERVED"*.

**Why it was wrong, at the root.** `extract.sh`'s §2 printed an offset list for a
hand-picked list of five tokens and nothing for the rest:

```python
if tok not in ('pde', 'PDE', 'NGP', 'GUARDIAN', 'deviceFamily'):
    continue
```

`discover` was outside that list, so its 12 hits appeared in §1 as the bare number
`cs=12` with no context, and the number **above** them (`cs=0`, for `discover/android`)
was read as the answer. This is `AGENTS.md` **§6 item 2** — a grep that hit without
proving — and I had applied my own doctrine to `pde` and then skipped it for
`discover`, which is the shape of the failure, not an unrelated one. It propagated
into four canonical pages as **§6 item 5**, including one table labelled **OBSERVED**
whose clinic and support columns were wrong.

**What the 12 actually are.** zxcvbn password-dictionary words, **identical in both
portal builds at identical byte offsets**: `discover` @211829 (between `oakland` and
`ranger1`), `discovered` @449173, `discovery` @456020, `discovers` @469461,
`discovering` @491815, `discoveries` @492201, `rediscovered` @522387, `discoverer`
@558582, `rediscovery` @581388, `discoverers` @684648, `rediscover` @941540,
`undiscovered` @954784.

**The conclusion is unchanged and the negative is now stronger.** The load-bearing
claim — *no web bundle in this corpus reads the discovery document* — does not depend
on the token count at all; it rests on `baseUrlPde`, `baseUrlCumulus`, `baseUrlCms`,
`baseUrlAem`, `baseUrlCareLink`, `discover/android`, `clcloud` and `api/carepartner`
all being **0**, which they still are, and on the only `baseUrl` in the patient
bundle being `this.baseUrl = getBaseCmsUrl()` (bytes 2027033, 2027209). What improves
is the honest form of the claim: the portal builds carry **17 dictionary-word hits
each — 12 `discover` + 5 `pde` — and none of them is a pointer.**

**What the fixed script additionally surfaced — a complete `pde` accounting for the
portal builds, which the filtered §2 never gave.** With §2 unfiltered, the portal
builds' `pde` `ci=32` now resolves in full: **5 case-sensitive** zxcvbn words
(`dropdead`, `helpdesk`, `herpderp`, `topdevice`, `hampden`) plus **27
case-insensitive-only** hits in **eight unrelated identifiers** — `propDecorators` ×8,
`removeStylesOnCompDestroy` ×6, `AppDefault` ×3, `WPDesktop` ×3, `LoopDetected` ×2,
`WebPDecodeRGBA` ×2, `mapDeviceModelName` ×2, `WebPDequantizeLevels` ×1.

**Counting rule, so this number is reproducible** (`AGENTS.md` §6 item 7 — a count with
no rule is a count nobody can check): one row per **distinct maximal enclosing
identifier** in §2, restricted to hits whose matched text is **not** the token itself
(`pde` matched verbatim ⇒ case-sensitive survivor ⇒ the zxcvbn group). **13** distinct
identifiers, of which **5** survive a case-sensitive grep, leaving **8**; and 5 + 27 =
32 = §1's `ci` for that token. Every multiplicities table in this log is pinned in
`expected-multiplicities.txt` and checked by `extract.sh` §3 — §C below.

> **⚠ CORRECTED 2026-10-13 (round 2) — this sentence first read "seven unrelated
> identifiers" while listing eight.** "Seven" is the *patient* bundle's distinct
> identifier count over its 25 hits, carried across to the portal builds' 32 hits. The
> two figures are unrelated, and the paragraph is headed *"a complete accounting"* — so
> the item count of the very thing claiming to be complete was wrong.

**So both portal builds' entire `pde` token set is now accounted for, item by item** —
which the first version of this pass could not claim. A verifier read all **27**
previously-unexamined case-insensitive hits at byte level and confirmed **every one is
incidental**: Angular reflect-metadata and `@Input()` decorators (`propDecorators`,
`removeStylesOnCompDestroy`), a jsPDF `PrintScaling` enum member (`AppDefault`), a
UA-sniff string (`WPDesktop`), an RFC 9110 status enum (`LoopDetected`), two WebP
decoder identifiers (`WebPDecodeRGBA`, `WebPDequantizeLevels`) and a reports
device-model mapper (`mapDeviceModelName`). Every one is `pDe` / `PDe` / `PDE` with a
capital; **none is a route, key, config value or directive, so no genuine PDE reference
hides among them.** Offsets in `grep-out.txt` §2.

**Fixed at the root, not just in the prose.** `extract.sh`'s §2 is now **unfiltered**:
it prints enclosing identifier, `×N` multiplicity, every offset and the first-hit
context for **every token with at least one hit**. Re-running it reproduces every
number in this section. **§C** below is the guard that checks those numbers, and **§D**
records the two defects round 2 found in this fix itself — one of them a guard that
could not fail while this log described it as protection.

### §B — two `pde` multiplicities were wrong, and unsourced.

| identifier | published | actual | offsets |
|---|---|---|---|
| `propDecorators` | ×8 | ×8 ✓ | 733029, 733047, 733066, 733092, 834961, 834994, 835023, 835044 |
| `removeStylesOnCompDestroy` | **×5** | **×6** | 1840258, 1840750, 1841416, 1845706, 1845875, 1846132 |
| `WPDesktop` | ×3 | ×3 ✓ | 2887697, 2889198, 2889490 |
| `mapDeviceModelName` | ×2 | ×2 ✓ | 581421, 581727 |
| `getGroupDelayControl` | ×2 | ×2 ✓ | 1603222, 1607946 |
| `isDesktopDevice` | **×4** | **×2** | 1967564, 1974820 |
| `LoopDetected` | ×2 | ×2 ✓ | 3147133, 3147152 |
| **sum** | **26** | **25** | 25 hits, 7 distinct identifiers |

The stated total (25) and the distinct-identifier count (7) were both right; only the
per-identifier numbers were wrong, in **opposite directions**, so the arithmetic
appeared to close. **They were also not in any committed artefact**: §2 deduped by
enclosing identifier and printed the first offset only, so `×5` / `×4` was prose with
nothing behind it — the `AGENTS.md` §1 failure (a claim with no source line) wearing
the costume of a measurement. The offsets above, and the `×N` beside each, are now in
`grep-out.txt` §2 and are re-derivable by re-running `extract.sh` with zero requests.

### §C — the arithmetic guard could not fail, and this log called it protection

**ROUND-2 CORRECTION, and the most serious of the three.** The round-1 fix added an
"arithmetic assertion" and described it here as stopping a class of error *silently*.
It could not fail. It compared:

```python
total = sum(len(v) for v in groups.values())   # 10 in the verifier's counterexample
if total != len(hits):                        # len(hits) is ALSO 10 -> never fires
```

`groups` is built by iterating `hits`, so the partition sum **is** the size of the set it
partitions — a quantity compared with itself. A prose table reading `propDecorators ×5,
WPDesktop ×3, dropdead ×2` over 5 hits, which is exactly the +1/−2 cancellation round 1
caught, sails straight through. What it proved was that the script's own grouping was
self-consistent, which was never in doubt.

**Both readings of the remedy were open and the honest one is implemented: made real,
with its limit stated.** `extract.sh` now has **§3**, which checks §2 against
**`expected-multiplicities.txt`** — a separate committed input, one row per
`<body> <token> <enclosing identifier> <multiplicity>`, **238 rows**, generated
mechanically (`MODE=--emit`, sorted so the generator is deterministic) rather than
typed. It fires on a changed multiplicity **or** a row with no recomputed counterpart,
prints the diff, and exits non-zero.

**Demonstrated, not asserted** — the guard was run against a deliberately corrupted
input and against the exact round-1 error:

| injected fault | exit | reported |
|---|---|---|
| `hp-main pde propDecorators 5` (the real round-1 value; truth is 8) | **1** | `CHANGED hp-main pde 'propDecorators': published 5, computed 8` |
| one row deleted (`hp-main discover undiscovered`) | **1** | `NEW hp-main discover 'undiscovered': computed 1, published NOTHING` |
| none (committed file) | **0** | `ok 238 group(s) match the published multiplicities exactly` |

**What §3 is, stated exactly so it is not over-read again.** It is **drift detection
between the published numbers and the bytes.** It is **not** proof the published numbers
were right the first time: `expected-multiplicities.txt` was authored by this same pass
from these same bundles, so a wrong *first* derivation would sit in both and §3 would
agree with it forever. Every row was re-derived independently and set-compared before
being committed — that review is what this guard stands in for, and it is not
mechanical.

**One more defect found while checking my own work, recorded because the way it was
found is the point.** §3 located `expected-multiplicities.txt` via
`os.path.dirname(os.path.abspath(__file__))` — but the script's Python runs from a
heredoc, so `__file__` is `<stdin>` and that resolved to **the caller's working
directory**. Every test I had run was from inside this directory, so it passed; run from
the worktree root, the guard reported the file *absent* and exited 1. **A guard that
depends on your cwd is not a guard.** `HERE` is now derived in the bash preamble and
passed in, and the script is byte-identical whether invoked from the repository root or
from this directory. It was found by running the thing I had just claimed was verified,
from somewhere I had not run it before — which is the only check that found it.

`extract.sh` also keeps a second, weaker check, now **labelled as weak**: §2's
per-identifier multiplicities must sum to §1's `ci` for that token. That one compares
two *different* routes to the same number (§1 counts with `len(re.findall(...))` over
the text; §2 arrives by grouping matches), so it can fire — but it catches a counting
bug, not a wrong published number. It was the old tautology's replacement, not its
alibi.

**Artefact digests after this change**, so a reader can confirm they have the same files:
`grep-out.txt` `sha256 2f86b0d6988d7c7b065db81d3d4f1338c8c0635dc1be94194a0f3b7b9e0998b9`,
`expected-multiplicities.txt`
`sha256 3e46f92cef313ed6e91b1ba5c0ed2be16fa92546b06a8ec8ef0e392566491aa9`. Two
consecutive runs of the fixed script are byte-identical, and `MODE=--emit` reproduces
`expected-multiplicities.txt` **byte-for-byte** — header, digest rows and multiplicity
rows — because the header now lives in its own committed file,
`expected-multiplicities.HEADER`, which `--emit` copies verbatim and `--check` verifies.
Demonstrated, not asserted: `--emit` output is `diff`-clean against the committed file,
and truncating the HEADER file changes the emitted file's first line, which is what
proves the header is an *input* rather than something the generator rewrites (§F).

### §D — §2 asserted the opposite of the distinction under audit

**ROUND-2 CORRECTION.** §2 chose its label from `cs == len(hits)`, so a **partial** token
(`0 < cs < ci`) fell into the `else` branch and was printed as *"case-insensitive ONLY
(case-sensitive grep drops every one)"*. That is false for the partial case and it
contradicted §1's own `cs=` number **on the same page**. Six cells were wrong:

| body | token | §1 said | §2 said (wrong) | §2 says now |
|---|---|---|---|---|
| `hp-main`, `sup-main` | `pde` | `cs=5 ci=32` | "drops every one" | `PARTIAL — 5 of 32 survive a case-SENSITIVE grep` |
| `eu-main`, `us-main` | `GUARDIAN` | `cs=3 ci=12` | "drops every one" | `PARTIAL — 3 of 12 survive` |
| `eu-main`, `us-main` | `deviceFamily` | `cs=5 ci=8` | "drops every one" | `PARTIAL — 5 of 8 survive` |

This is `AGENTS.md` §6 item 2 and it was **new** — the pre-fix script had no such line —
and it mattered most for `pde`, the token the whole correction is about: §A's thesis is
that `pde` **is** 5 case-sensitive hits per portal build, and §2 asserted the reverse. A
verifier re-deriving from §2's header would land back on `cs = 0`.

The test for "case-insensitive ONLY" is **`cs == 0`**, not `cs == len(hits)`. §2 now has
three states — `ci` (`cs == 0`), `cs` (`cs == ci`), `partial` (`0 < cs < ci`) — each
printing the observed counts, and the class is stored **nowhere** in the expected file so
the two cannot disagree about it.

### §F — the guard advertised a digest check it did not perform

**ROUND-3 CORRECTION, and the third instance of one pattern in this PR.** Round 1
published a corroboration that did not exist. Round 2 shipped a guard that compared a
partition sum to the size of the set it partitioned, and called it protection. Round 3
shipped a *replacement* guard that **printed** each body's sha256 and had three places
claiming it **asserted** the digest before any comparison and that **a bundle bump makes
the guard say so**. None of that was true. The pattern across all three is the same:
**a control describing more than it checks** — `docs/09` §5's verdict on the shape, *"a
check that looks like it ran is worse than no check, because it converts a gap into a
green tick."*

**Reproduced here before the fix**, on the digest-matched bodies (§6 item 3 discipline
carried into the test, not into a claim):

| body | size | sha256 | guard exit |
|---|---|---|---|
| published `eu-runtime` | 8,268 B | `0dfea208804facf8…` | **0** |
| bumped `eu-runtime`, every group and multiplicity identical | **13,272 B** | **`1cdfa1ea2103b29a…`** | **0** |

Different digest, different size, every byte offset moved — **exit 0**, with the wrong
digest printed two hundred lines above the green tick.

**The claim is now real rather than withdrawn**, for the same reason round 2's was: the
consistent choice across rounds is to make a control do the thing it says.
`expected-multiplicities.txt` now carries **5 digest rows** —
`<body> sha256 <hex>` — alongside the 238 multiplicity rows, and `extract.sh` §3
**compares the digests FIRST**, before any multiplicity is read. A bundle bump now
fails the guard on the digest and the multiplicities are never consulted.

| test | exit | reported |
|---|---|---|
| clean, committed file | **0** | `ok 5 body digest(s) match` · `ok 238 group(s) match` |
| **bumped body, identical multiplicities** (the verifier's demonstration) | **1** | `FAIL 1 body digest mismatch(es) — the bytes being compared are NOT the bytes that were published` |
| `propDecorators 5` (the round-1 error) | **1** | multiplicity CHANGED |
| a deleted row | **1** | multiplicity MISSING |
| a phantom row | **1** | multiplicity NEW |

**The limit, stated in three places — this file, `extract.sh`'s header, and
`expected-multiplicities.HEADER` — because it is the thing that has now been got wrong
three times.** §3 is **drift detection** between the published rows and the bytes on
disk; the digest rows additionally prove the bytes being compared **are** the bytes that
were published. **Neither detects a wrong first derivation**: the multiplicities *and*
the digests were produced by this same pass from these same bundles on 2026-10-13, so a
bundle misread on the first pass is misread here identically. What replaces a first
derivation is re-derivation plus review by hand — §A's and §B's re-derivations were
done by a reviewer who had not built the numbers, and that is precisely the step no
script in this directory can perform. **It is stated in the artefact's own header so a
reader who opens the data file — not this log — still gets it.**

**And the fourth thing round 3 checked, which I got wrong again in the other
direction.** `MODE=--emit` used to write its own short header over the committed
rationale header, destroying the digest table and every explanation of how the numbers
were derived, while this log claimed it "reproduces the expected file". The header now
lives in **its own committed file**, `expected-multiplicities.HEADER`, which `--emit`
copies verbatim, and `--check` **verifies the emitted file begins with it** — so a
rewritten header is a guard failure, not a silent overwrite. Demonstrated rather than
asserted: `--emit` output is `diff`-clean against the committed file, and truncating the
HEADER file changes the emitted file's first line, which is what proves it is an input.

**A control I built and then withdrew, recorded because the failure mode is the point.**
To make the read counts more precise I added a resolver mapping each `.<alias>` site to
the module its namespace is bound to. It reported the `.cO` read at byte 3373465 as
**not** genuine, contradicting a round-1 finding. It was the resolver that was wrong:
that site is in module **99040**, whose head binds **`p = i(4265)`**, so it *is* genuine
— minified identifiers are shadowed per function scope, and a nearest-preceding-binding
search finds the wrong one. Shipping it would have been the fourth round of the same
meta-pattern, so it is **withdrawn**, and `consumers.sh` now prints the warning where a
reader meets the number: 3 `.bQ` sites, 2 of them another module's same-named export,
hand-checked not machine-resolved.

### §G — a disclosure that travelled less far than it should

The `body_mtime_epoch` caveat below (whole seconds, `stat -c%Y`, so the sub-second
mtime figures are **not re-derivable from the committed ledger** and git does not
preserve mtimes) sat about twenty lines after the table printing `2.599 s`, and did not
travel into `docs/11` at all, where a reader sees only that number. It now travels
with the number at every site. Stated as a disclosure weakness, not a wrong claim: the
figure itself is correct and the load-bearing floor is the millisecond `t_sent`
series, which reproduces from `results.jsonl` alone.

### Not changed, and why

`baseUrlPde`, `/connect/pde`, `baseUrlCumulus`, `baseUrlCms`, `baseUrlAem`,
`baseUrlCareLink`, `discover/android`, `clcloud`, `api/carepartner` — re-counted on the
digest-matched bodies, still **0 everywhere**. The 5 `pde` hits per portal build, the
`system.gc.gz.transition.flags` key constant at 2189151, the `.z2` zero-read result,
the 56-of-69 key census, the 211-chunk map, the 2.566 s `t_sent` floor and the pin are
untouched by this correction and were re-checked rather than assumed.
