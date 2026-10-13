# Configuration — the unauthenticated public config

Dated 2026-10-10. Sources: `findings-log/probe-2026-10-08/PUBLIC-CONFIG-FINDINGS.md`,
`CROSS-REGION-CONFIG-FINDINGS.md`, `recon/CONFIG-NAMESPACE-DEEP.md`, `recon/CONFIG-NAMESPACE.md`.

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = in a vendor document
served without a login (live, or recovered from a public web archive) · **INFERRED** =
reasoned, not seen.

> **Navigation** — the map: [`00-summary-the-map.md`](00-summary-the-map.md) · ← prev:
> [`03-discovery-and-versions.md`](03-discovery-and-versions.md) · → next:
> [`05-devices-and-vocabulary.md`](05-devices-and-vocabulary.md) · related:
> [`06-patient-api-surface.md`](06-patient-api-surface.md) ·
> [`07-admin-portal-and-reporting.md`](07-admin-portal-and-reporting.md)

## The endpoint

```
GET https://carelink.minimed.{eu,com}/patient/v2/configuration/public
```

| fact | value | evidence |
|---|---|---|
| auth | none — no token, no api-key, 200 `application/json` | OBSERVED |
| deployments | all three: `.eu` (default `GB`), `.com` (`US`), `carelink-trials.minimed.com` (`US`, clinical) | OBSERVED |
| keys | **69 top-level**, identical key *set* on every host — one regionalised document, not three | OBSERVED |
| regional | **34 of the 69 keys differ by region** | OBSERVED |
| size (EU) | 6295 B compressed / 26692 B raw | OBSERVED |
| namespace | `/patient/v2/configuration/public` is the only member — no `v1`/`v3`, no unversioned `/configuration/public`, no siblings under `/patient/v2/configuration/`; trailing slash accepted | OBSERVED |
| growth | 20420 B compact (10-09) → 20586 B (10-10), same 69-key set; archived captures 2026-02-04 (18834 B) → 2026-09-26 | OBSERVED |

### Encoding — gzip is unconditional

The host returns `Content-Encoding: gzip` **without the client asking** (verified against
`identity`, `gzip`, `deflate`) — labelled an RFC 9110 §8.4 violation in
`docs/00-summary-the-map.md`. Parse gotcha: a plain `curl -o file` writes raw gzip bytes
and every later `jq` fails with `utf-8 codec can't decode byte 0x8b`. Use `curl
--compressed` or decompress locally; do **not** re-request to work around it
[source: findings-log/probe-2026-10-08/PUBLIC-CONFIG-FINDINGS.md].

## The 69 keys, by group

**The complete 69-name list is committed** at
[findings-log/2026-10-13-area-w-per-key/keys.txt](https://github.com/NovaLux12/carelink-api-research/blob/main/findings-log/2026-10-13-area-w-per-key/keys.txt)
(sorted, extracted live from the EU bulk document and asserted 69 in-harness).
The groups below organise those names; before 2026-10-13 the remaining names
were **Unknown** — not enumerated in any source.

| group | keys | notes |
|---|---|---|
| device vocabulary | `personal.device.family.to.model.mapping`, `system.settings.transfer.feature.config.device.mapping` | 16 families; `{"BLE780":"780G","CC880":"MiniMed™ Flex"}` — see `05-devices-and-vocabulary.md` |
| logbook | `logbook.supported.entry.types` (12 types), `logbook.enabled`, `logbook.entries.page.size` (= 30), `system.logbook.entry.validation.config` | validation config is `null` on both patient regions, full schema on trials |
| device control codes | `csr.control.codes.settings` | `dpml`/`tup`/`lhpro`/`lghpro`/`vex`/`ssd`/`tcc`/`gstpro`/`gstrc` with ranges. **Not** the NGP alarm set — no N-codes |
| disclosed service hosts | `retina.endpoints.config.personal.target_url` (+ `dashboard.base_uri`), `csr.cumulus.periodic.data.endpoints`, `mmm.data.api.url`, `personal.patient.timeline.config.host`, `praas.uri.path.reports.ping`, `nutrino.cc.{broker,metadata}.service.config` | five service families / nine endpoints, all recorded as previously unrecorded and confirmed live; `praas` and the CSR AWS VPC endpoint are internal and not publicly reachable — recorded, not probed. **`csr.cumulus.periodic.data.endpoints` now has its value read for the first time — see [The published pointer set](#the-published-pointer-set)** |
| **the vendor's own migration switchboard** | **`system.gc.gz.transition.flags`** | **Added 2026-10-12.** Absent from every key list this repo recorded before that date. `displayMessage.useCumulusUrls` = **`true` on all three deployments**, beside a three-way plane dispatch table; five sibling capability booleans are **all `true`**. See [The published pointer set](#the-published-pointer-set) |
| regional feature flags | `personal.clinical.environment`, `personal.safety.notices.enabled`, `personal.data.csv.export.enable`, `personal.cookie.consent.policy.enabledGlobally`, `personal.dob.validation.enabled`, `personal.mixpanel.analytics.settings.{enabled,token}`, `personal.username.as.email.settings.enabled`, `personal.inpen.supported.countries.enabledGlobally` | see the regional table below |
| country lists | `personal.common.core.reporting.enabled.countries`, `personal.countries.certification.enabled`, `personal.inpen.supported.countries` | grow over time — see the drift note |
| auth / redirect | `personal.integrations.redirect.scheme.whitelist`, `system.auth0.url.whitelist`, `captcha.key`, `personal.session.timeout` (= 30) | [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge)'s `com.medtronic.carepartner:/sso` redirect is **not** in the integrations whitelist — that whitelist governs deep links, not the OAuth callback, so this is context, not a contradiction |
| misc / operational | `personal.third.party.apps`, `outages.nextupdateat`, `default.country`, `personal.crm.settings`, `personal.retina.endpoint.config` | `captcha.key` is a reCAPTCHA **site** key, public by design |

Two `nutrino.cc.*` keys carry a `security_headers["x-api-key"]`. **The EU deployment
ships a literal placeholder** — 17 characters, not a credential. That much is
published; it explains the bug class and exposes nothing. The comparison against the
other two deployments is **held back** for a disclosure decision — see
[`07-admin-portal-and-reporting.md`](07-admin-portal-and-reporting.md). No value
appears anywhere in this repo, in any form [source:
findings-log/probe-2026-10-08/CROSS-REGION-CONFIG-FINDINGS.md].

### Global vs regional — hash-verified

sha256 of canonical JSON, identical on all three deployments:

| key | digest |
|---|---|
| `personal.device.family.to.model.mapping` | `8ce419a22fd3` |
| `system.settings.transfer.feature.config.device.mapping` | `90a93c057aec` |
| `logbook.supported.entry.types` | `98c562842920` |
| `csr.control.codes.settings.predefined_control_codes` | `c7c0f04fb4b0` |
| `system.logbook.entry.validation.config` | **DIFFERS** — `null` / `null` / schema |

So the published device vocabulary is **one authoritative map, not a regional one**. This
is pinned by `hurl/05-public-config.check.sh`.

> **⚠ Correction — preserved.** The first attempt at this comparison reported *four*
> "SAME" rows when only three were same: the walker looked up dotted-nested paths with a
> single `dict.get("a.b.c")`, got `None`, and hashed `None` — so two genuinely different
> values produced identical digests and looked like agreement. The check now walks path
> segment-by-segment, asserts the resolved type, and treats an all-zero digest
> (`e3b0c442…`, the sha256 of the empty string) as a failure. **A hash check over a
> lookup that can silently return `null` will manufacture consensus.**
> [source: findings-log/probe-2026-10-08/CROSS-REGION-CONFIG-FINDINGS.md]

## The published pointer set

**Added 2026-10-12** (area T). Until this pass, two of the keys in the table above were
recorded **by name and never read**. Both are endpoint-bearing, so the omission was
load-bearing: this repo knew a `csr`-prefixed "endpoints" key existed and did not know
what it pointed at
[source: findings-log/2026-10-12-published-pointers/FINDINGS.md].

**OBSERVED, 3 of 3 deployments, unauthenticated.** `csr.cumulus.periodic.data.endpoints`
is a two-key object:

| key | value (EU host) |
|---|---|
| `display_message` | `https://clcloud.minimed.eu/connect/csr/v2/display/message` — **the same route the 2026-10-11 pass found live and POST-only** |
| `periodic_packet` | an **AWS VPC-endpoint service name** carrying `/dev/connect/csr/v2/periodic/packet` — internal, **recorded not probed**; the endpoint identifier is redacted in this repo |

So the `csr/v2` namespace has **at least two members**, and "the `csr/v2` route" is
already an undercount. The `/dev/` stage prefix in the second one is also published.

### `system.gc.gz.transition.flags` — the client is told to use `csr/v2`

**OBSERVED**, identical on all three deployments. A six-key subtree that **no file in
this repository recorded before 2026-10-12**:

| key | value (3 of 3) |
|---|---|
| `displayMessage.useCumulusUrls` | **`true`** |
| `displayMessage.personalDisplayMessageUrl` | `…/patient/connect/data` |
| `displayMessage.csrDisplayMessageUrl` | **`…/connect/csr/v2/display/message`** |
| `displayMessage.carepartnerDisplayMessageUrl` | `…/patient/m2m/connect/data/gc/patients/{patientUsername}` |
| `pullGMInfoFromCumulus` | `true` |
| `pullSMSHistoryFromCumulus` | `true` |
| `sendDiagnosticLogsToCumulus` | `true` |
| `sendPeriodicToCumulus` | `true` |
| `sendSMSFromCumulus` | `true` |

`csrDisplayMessageUrl` is not a stray key — it is one arm of a **three-way plane
dispatch table** (`personal` / `csr` / `carepartner`), with `useCumulusUrls` as the
master switch, already `true` everywhere. **So the vendor's own client is instructed by
public config to address `csr/v2`, on every deployment, today.** That is a stronger
claim than "`csr/v2` is live", and it is the opposite of what area T set out to test.

The five sibling booleans say five capabilities — GM info, SMS history, diagnostic logs,
**periodic data**, SMS sending — are already on the Cumulus plane. `sendPeriodicToCumulus`
is what makes `csr.cumulus.periodic.data.endpoints` necessary in the first place; the two
facts corroborate each other. **INFERRED:** that `gc` → `gz` names a service migration
and these are its completion switches — the key names support it, no document on any
surface states it. The *values* are OBSERVED; the reading is not.

### Which of the two identical CSR pointers the shipped client actually follows

**Added 2026-10-13** (area V). The paragraph above is an *instruction*; this one is an
**execution**. A key being present in a minified bundle proves only that a token exists
(`docs/09` §5 item 2), so each pointer subtree was resolved to a **read** rather than a
mention: key constant → observable selector → webpack export alias → property reads.
Corpus: the patient bundle `main.6595daf83bd6d4b1.js` (3,417,255 B,
sha256 `0fb4fbd4…`), captured 2026-10-13 [source:
findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md].

| pointer subtree | named? | selector exported as | property reads |
|---|---|---|---|
| **`csr.cumulus.periodic.data.endpoints`** | yes (byte 2188929) | `cO` | **1 genuine read** |
| **`system.gc.gz.transition.flags`** | yes (byte 2189123) | `z2` | **0 — the substring `.z2` occurs nowhere in the file** |

**OBSERVED.** At byte 3373465 the bundle reads the first subtree, destructures
`display_message` and POSTs it:

```js
getUploadDeviceInfo(V){
  return forkJoin([this.getProfile(), this.store.select(p.cO).pipe(take(1))])
    .pipe(map(([R,{display_message:X}])=>{
      const Q={patientId:V||R.username, role:this.isCarePartner()?'CARE_PARTNER':'PATIENT', username:R.username};
      return this.http.post(X,Q)
    }), …)
}
```

(`forkJoin` / `take` / `map` are the unminified names of the module's own aliases
`n.p`, `h.s` and `S.n`; the minified source is quoted verbatim in the log.) So the
**live, POST-only `…/connect/csr/v2/display/message`** route is reached by a
config-driven `POST` carrying `{patientId, role, username}` — which is what area T's
inference needed and did not have. **The client does not hardcode the URL**: it reads
the field, so a config change moves the call. The other two of the three `.cO` sites
in the file are Angular Material's own injection token in a different module and are
**disclosed rather than counted** [source:
findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md §The positive].

**The sharp part is the contrast.** Two unrelated subtrees publish **the same CSR
URL**, and the client follows one and ignores the other: the `transition.flags`
subtree that carries `csrDisplayMessageUrl` — the key this section is built around —
is **named, given a selector, exported, and never read**, and **none of its nine leaf
names appears anywhere in any of the five captured bundles**. So `useCumulusUrls`,
`csrDisplayMessageUrl` and the five `*FromCumulus` booleans are **OBSERVED as
published values and absent as code**. That is a statement about the **eager main
bundle only**; the 211 lazy chunks were not fetched, and their current inventory is
now committed at
[findings-log/2026-10-13-area-v-pde-clients/chunks.txt](../findings-log/2026-10-13-area-v-pde-clients/chunks.txt).
**What any of the other 56 followed keys' consumers do is not established.**

### The route that config cannot address

`/connect/v2` — the **bare**, pre-`carepartner` route that the 2026-10-12 area-N pass
confirmed live and POST-only — is named by **no published document**: zero hits for
`/connect/v2` across all ten documents read. So of the two POST-only routes, `csr/v2`
is config-addressable and the bare one is not. That asymmetry is the durable negative
from this pass, and it is recorded with the searched set so it is auditable rather than
merely asserted.

### ⚠ Correction 1 — `personal.data.csv.export.enable` is an object, not a boolean

**Corrected 2026-10-12.** The regional table in this page recorded this key as a scalar
(`true` / `true` / `false`). **It is an object keyed by plane**, and the scalar reading
silently hides half the value:

| deployment | `personal` | `csr` |
|---|---|---|
| EU | `{aggregatedData: true, rawData: false}` | `{aggregatedData: true, rawData: false}` |
| US | `{aggregatedData: true, rawData: false}` | `{aggregatedData: true, rawData: false}` |
| trials | `{aggregatedData: false, rawData: false}` | `{aggregatedData: true, **rawData: true**}` |

Two consequences. A scalar reader misses `rawData` and the whole `csr` plane — and
**trials `csr.rawData` is `true` where every `personal` value is `false`**, so CSV-export
capability differs by plane in a way the scalar reading cannot express. And this is the
*same* silent-failure class documented above for the per-key projection's string
booleans — a `=== true` check against an object never fires — but in the **bulk**
document this time.

The old scalars happened to agree with `personal.aggregatedData` on all three
deployments, which is exactly why the error survived: **the note was right about the
numbers and wrong about the type.** Pinned on *type* in `hurl/05` so the shape cannot
silently revert.

### ⚠ Correction 2 — the document is 68 flat dotted keys and exactly one nested object

`docs/04` describes the document as "69 **top-level** keys". True, but a consumer cannot
assume a uniform shape:

- **68 of 69** are *literal top-level key names that contain dots* —
  `personal.device.family.to.model.mapping`, `system.gc.gz.transition.flags`,
  `outages.nextupdateat`. Their **values** are a mix of scalars, arrays and objects:
  **28 of the 69 hold objects** on EU and US, **30 on trials**.
- **Exactly 1** — `captcha` — has **no dot in its key**. That is the whole of its
  distinction: it is the only key whose *name* is a bare segment, not the only
  nested *value*. Its shape is `{enabled, key, testKey, type}`.

So the `captcha.key` / `captcha.testKey` names used elsewhere in this page are **not**
top-level keys; they are subkeys of `captcha`. A walker that splits every key on `.`
and does a dotted lookup — precisely the bug in
[`09-methodology-and-oracles.md`](09-methodology-and-oracles.md) §5 item 3 — will miss
`captcha` entirely, while finding `outages.nextupdateat` as a literal on the same
document. **Both shapes are in one document**, so the flattening must be checked, not
assumed.

**Also new, minor:** `captcha.testKey` is an **empty string on all three**
deployments — a published key that exists and carries nothing. A client that switches on
"testKey is present" rather than "non-empty" would enable test mode.

**A correction that was *not* needed.** `outages.nextupdateat` **is** populated on
trials only, exactly as this page states — a first reading of the 2026-10-12 pass
appeared to contradict it and does not. Recorded because the near-miss is the kind of
thing that otherwise gets written up as a correction of a correct claim.

### Credential-shaped values — structure only, comparison held

**The config publishes credential-shaped values.** Recorded here with **no value
printed, hashed, or compared**, preserving the hold-back stated at the top of this page:

| key | EU | US | trials |
|---|---|---|---|
| `nutrino.cc.broker.service.config.security_headers["x-api-key"]` | 17 chars, non-alphanumeric placeholder | **40 chars, alphanumeric** | **40 chars, alphanumeric** |
| `nutrino.cc.metadata.service.config.security_headers["x-api-key"]` | 17 chars, non-alphanumeric placeholder | **40 chars, alphanumeric** | **40 chars, alphanumeric** |
| `captcha.key` (reCAPTCHA **site** key, public by design) | 40 chars | 40 chars | 40 chars |
| `personal.mixpanel.analytics.settings.token` | 44 chars | 44 chars | **`""`** |

**What is new and structural:** the two `nutrino.cc.*` keys carry a **40-character
alphanumeric** value on the other two deployments — the credential class this repo's own
gate scrubs by prefix. So the EU placeholder is not merely *different*, it is the
**only** deployment where the published value is not credential-shaped.

**The cross-deployment comparison stays held.** Whether those 40-character values are
equal to each other is **not tested, not hashed, not inferred** here. The pass's
`credential-shapes.py` has no code path that could answer it — a scrubber that could
would be doing the thing the hold-back exists to prevent
[source: findings-log/2026-10-12-published-pointers/FINDINGS.md §5].

### Why the raw captures are not committed

The document this section is derived from is unauthenticated and contains the values
above, so the pass ships **the redaction, not the capture**: a re-runnable enumerator, a
scrubber that reads its patterns from `scripts/scrub-patterns.txt` rather than embedding
a credential in a second file, and a value-free structural report. The pass directory's
`.gitignore` covers the raw JSON. Re-deriving it is three commands
[source: findings-log/2026-10-12-published-pointers/FINDINGS.md].

## The 34 regional keys

Ten differing keys are documented. The remaining differing key names are **Unknown** — not
itemised in any source.

| key | EU | US | trials |
|---|---|---|---|
| `logbook.enabled` | false | false | **true** |
| `personal.clinical.environment` | false | false | **true** |
| `personal.safety.notices.enabled` | false | **true** | false |
| `personal.data.csv.export.enable` | true | true | **false** |
| `personal.cookie.consent.policy.enabledGlobally` | true | true | **false** |
| `personal.dob.validation.enabled` | true | true | **false** |
| `personal.mixpanel.analytics.settings.enabled` | true | true | **false**, empty token |
| `personal.username.as.email.settings.enabled` | true | true | **false** |
| `personal.inpen.supported.countries.enabledGlobally` | false | **true** | false |
| `personal.common.core.reporting.enabled.countries` | **29 countries** (17 before the 2026-10-09→10 rollout) | `["US","PR"]` | 21 — ⚠ **measured 13 on 2026-10-13**, see below |

⚠ **A dated disagreement in that row, both numbers left standing.** The trials
cell reads **21**; a direct GET of the trials bulk document on **2026-10-13**
returned **13** countries (`US NZ AU GB SI DE FR BE IT ES NL DK IL`), and the
trials **per-key** projection of the same key agrees with it cell for cell. The
EU figure in the same row was verified 2026-10-11 and this pass did **not**
re-probe EU, so it cannot say whether trials shrank, whether the earlier 21 was
a different reading, or whether the two rows were never the same measurement.
Both numbers stand; the trials one carries its date
[source: findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md §3].

`personal.safety.notices.enabled` is the medically relevant one: it is **true on the US
deployment only**, and safety notices are how Medtronic communicates device advisories to
patients. It is a regional difference, not a constant.

`logbook.enabled` is false on both patient regions, which is why the entry-validation
schema ships `null` there and populated only on trials.

Also regional: `personal.countries.certification.enabled` is `["FR","YT","NC","PF"]` on EU
(an EU MDR certification rollout in progress) and empty elsewhere;
**⚠ `personal.third.party.apps` is an ARRAY, not a string, and the count is 4 on EU,
1 on US, `null` on trials** (corrected 2026-10-12; this page recorded a single value per
deployment). Each entry is an object, and **the two planes' entries differ in shape**: EU
entries carry 7 subkeys, the single US entry carries those plus `consentDate` and
`expiresInDays` (9), so a client requiring `consentDate` sees it on one deployment only.
The four EU integrations and their three Auth0 clients were already recorded on 2026-10-08
[source: findings-log/probe-2026-10-08/recon/ARCHIVE-URLS.md §1]; what is new is that
**US has one and trials has none**. Same class as Correction 1 above: a scalar reading
of an array [source: findings-log/2026-10-12-published-pointers/FINDINGS.md §6].

Separately, and unaffected by the correction above: `outages.nextupdateat` is populated
on trials only (re-verified 2026-10-12), and each deployment has its own reCAPTCHA site
key and Mixpanel token.

**Live drift, recorded 2026-10-09 → 2026-10-10:**
`personal.common.core.reporting.enabled.countries` grew **17 → 29** (AU, HR, CZ, EG, GE,
IL, PL, RO, RS, SK, SI, AE) and `personal.inpen.supported.countries` grew in step. A
rollout is in progress [source: findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md].

## The per-key form — and its string-boolean trap

```
GET https://carelink.minimed.eu/patient/configuration/system/logbook.supported.entry.types
→ 200 application/json, 281 B (3470 B for the device map)
```

The grammar is the **v1** path, not anything under `/patient/v2/` — the hypothesis was
right, the predicted path was not [source: findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md].

Every response is a Java-style config envelope:

```json
{ "value" : "<the config value, as a STRING>" }
```

- Scalars arrive as the scalar; **booleans arrive as the strings `"true"`/`"false"`**;
  objects and arrays arrive as a JSON document *serialised into the string*. A naive
  `resp.value === false` check silently never fires. Unwrap, then `JSON.parse` again.
- **Swept COMPLETE on all three deployments.** EU by area W (2026-10-13); **`.com` and
  `-trials` by area E, same day**. Every key has a verdict on all three, and every
  column reconciles to **73** (69 bulk names + 4 `captcha` subkeys):
  **61 / 62 / 61 VALUED-match** (EU / `.com` / trials), **5 / 5 / 6 NULL-404**, plus
  **2 / 2 / 2** dedicated-route 404s, **4 / 4 / 4** subkey 404s, and **zero names
  outside the bulk document**. **⚠ Read EU's `61` as 61 *exact* matches, not 61
  valued cells** — EU carries a 62nd valued cell, the stray-bracket quirk below, so
  **valued cells are 62 / 62 / 61** (EU / `.com` / trials) and trials is the one that
  differs, by one, because it has one more null-valued key. Zero mismatches across
  the **123** valued cells of this pass's two hosts. **The negative holds and is now
  three-host evidenced: the 69-name vocabulary is deployment-portable and the
  per-key form is a projection everywhere, not an enumeration path to anything
  beyond the bulk document.** The "69-request enumeration path" framing is
  retired, not extended [source:
  findings-log/2026-10-13-area-w-per-key/FINDINGS.md;
  findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md §2].
- **What is *not* identical is which keys 404** — and that is downstream of the
  bulk document's null set, not of the per-key grammar. **EU and `.com` have the
  same five null-valued keys, name for name; trials has six.** Trials-only
  nulls: `mmm.data.api.url` (corroborating `07-admin-portal-and-reporting.md`
  §`dialog-lite` first-hand), **`personal.linking.request.interval`** (named in
  no page here), `personal.third.party.apps`. Trials-only non-nulls:
  `outages.nextupdateat` and `system.logbook.entry.validation.config`. Three keys
  are null on all three. **So the client-facing rule is unchanged but sharper:
  a per-key 404 means "null *on this deployment*, or served by a dedicated
  route", and the null set must be read from that deployment's own bulk
  document. A client that hardcodes "these five keys 404" is wrong on trials
  [source: findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md §2].
- **One key does not round-trip — and the defect is EU-only as measured.**
  `personal.common.core.reporting.enabled.countries` answers 200 on all three,
  but on **EU** its envelope value is the 29-country array **plus one extra
  trailing `]`** — not valid JSON, reproduced byte-identical on re-issue. On
  **`.com` (34 B, `["US","PR"]`) and `-trials` (122 B, 13 countries)** the same
  key's value parses cleanly and equals its own bulk subtree exactly, with no
  normalisation. **Two readings and neither is excluded:** that the quirk is a
  property of the EU serialisation (assumption: the EU cell still behaves as
  area W measured it the same day — it is cited, not re-measured here), or that
  it rides with value length (29 against 2 and 13). A consumer must strip **at
  most one** trailing `]` after a parse failure and must not assume the defect
  is confined to EU [source:
  findings-log/2026-10-13-area-w-per-key/FINDINGS.md §4;
  findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md §3].
- **Null-valued keys 404.** All five EU nulls (`country.reports`,
  `outages.nextupdateat`, `personal.inpen.redirect.url`,
  `personal.retina.endpoint.config`, `system.logbook.entry.validation.config`)
  404 per-key — and so do the identical five on `.com`. On trials the six
  nulls listed above 404 instead. A per-key consumer must treat 404 as
  "absent-or-null", not "key does not exist".
- Dedicated alias routes: `/patient/configuration/defaultCountry` → `{"value":"GB"}`,
  `/patient/configuration/recaptcha/key` → `{"value":"6LfUbuor…"}`.
  `/patient/configuration/messages/en` is live and returns `{"messages":[]}`.
- Control: `/patient/configuration/system/zzz.not.a.real.key.zzz` → 404 with
  `content-type: text/vnd.a`, so 404 is a genuine "absent", not a catch-all. Do not
  discriminate on that odd content-type — with one refinement 2026-10-13 (area W):
  the control's 404 carries `text/vnd.a` while all 11 real-key 404s in the area-W
  sweep (nulls, `captcha`, `default.country`, captcha subkeys — first written as 12
  in the pass log, corrected 2026-10-13: the enumeration sums to 11) carry **no**
  `content-type` at all. N=1 control shape — not an oracle, but a second header
  to check [source: findings-log/2026-10-13-area-w-per-key/FINDINGS.md §5].
- ⚠ **And a second refinement the same day, from area E: the split above does not
  hold on `-trials`.** There, **one of the twelve real-key 404s carries a
  content-type** — `personal.linking.request.interval`, `application/vnd.nervana`,
  `content-length: 0`, `x-cache: Error from cloudfront` — a value in **no prior
  reading on any host of this namespace**. On `.com` the split reproduces exactly
  (**11 of 11** real-key 404s carry no content-type; the trials denominator is 12
  because trials has one more null-valued key, not because this pass re-used
  area W's figure — **counting rule: a real-key 404 is a `NULL-404`,
  `DEDICATED-ROUTE-404` or `SUBKEY-404` row, i.e. a 404 against a name in the
  committed candidate list, with the absent-path control excluded**). So the discriminator is
  **three-valued, not two-valued**, and **"the control carries `text/vnd.a` and
  real keys do not" is false on one deployment of three** — a reader who built a
  test on area W's sentence would mis-classify exactly this cell. This does not
  make the header an oracle; it makes it worse as one, and it is the second
  independent reason to keep the standing instruction not to discriminate on it
  [source:
  findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md §4].
- `personal.device.family.to.model.mapping` also answers on `carelink.minimed.com` and is
  **identical to the EU body** — the vocabulary is global. (2026-10-13: area E went
  further — the **entire** 69-name vocabulary and its per-key projection were swept
  on `.com` and `-trials`, and the key *set* is identical on all three.)
- Rejected grammars: no per-key form under `/patient/v2/`; no
  `/patient/configuration/public/<key>` on the patient host; no flat-name
  `captcha.<enabled|key|type|testKey>` form (all four 404 — `captcha` answers
  only via `/patient/configuration/recaptcha/key`); `?countryCode=GB` on the
  per-key form is byte-identical, so the per-key namespace is **not** country-parameterised.

## `?countryCode=` on the public config is accepted and ignored

Sending `?countryCode=X` (GB/US/DE/FR tested) yields **69 keys in, 70 keys out**: the
parameter is echoed verbatim as a new top-level `"countryCode"` key and **nothing else
changes**. `default.country` stays `GB` even when `countryCode=US` is sent to the EU host.
The document is region-parameterised by **host, not by parameter** [source:
findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md].

Consequence: `hurl/05-public-config.check.sh`'s `check "config key count (was 69)"` **will
fail** if anyone runs it with a `countryCode` param — it would see 70. The assertion is
correct as written (bare URL).

## The real country axis — `/patient/countries/settings`

```
GET /patient/countries/settings?countryCode=XX   → 200 application/json, gzip, 35 keys
```

- No param → **400** with a JSR-303 body (`"field":"getCountryConfiguration.arg0"`,
  `"message":"must not be null"`). Bogus `ZZ` → **400** `"Error! Country:ZZ Not
  Supported"`. Both are clean, distinct error shapes — the country code is genuinely
  validated.
- Swept across **18 countries**: GB US DE FR IT ES NL SE NO DK FI CH AT BE IE ZA CL RU.
- **Swept COMPLETE 2026-10-12 (area D).** All **118** country codes the
  vendor's own published config enumerates were requested and every key given
  an ABSENT / NULL / VALUED verdict: **117 country documents** served, **33/34/35
  keys** depending on country, **no key outside the 35-key vocabulary**, no
  report-name vocabulary delta. **The document is not uniform in shape** — 35
  keys for CA/US, 34 for 74 countries, 33 for 41 — and the per-country × per-key
  matrix is on disk at
  [findings-log/2026-10-12-area-d-country-sweep/matrix.tsv](https://github.com/NovaLux12/carelink-api-research/blob/main/findings-log/2026-10-12-area-d-country-sweep/matrix.tsv).
  The 35 country-key names and the 69 bulk-config names have a **0-name
  intersection** — disjoint vocabularies (camelCase vs dotted/lowercase),
  compared offline 2026-10-13 against the committed name list
  [source: findings-log/2026-10-13-area-w-per-key/FINDINGS.md §3].
  **51 internal contradictions** were enumerated across 10 classes
  ([findings-log/2026-10-12-area-d-country-sweep/FINDINGS.md](https://github.com/NovaLux12/carelink-api-research/blob/main/findings-log/2026-10-12-area-d-country-sweep/FINDINGS.md) §5).
  ⚠ The `109` country-code count previously recorded on `docs/11` **does not
  reproduce**: the same counting rule over the captures on disk yields **118**.
  Both numbers are left standing — the earlier one has no counting rule recorded
  with it, so this pass can neither confirm nor explain it.
- **`ID` is enumerated by all three vendor config documents and refused by this
  endpoint** — `400 "Error! Country:ID Not Supported"`, the same envelope as the
  bogus-code control. The vendor's published country lists and the countries this
  endpoint serves are **not the same set** (OBSERVED, 2026-10-12).
- **The EU host will happily serve US market config.** With `countryCode=US` the reply
  carries `region:"US"`, `mediaHost:https://carelink.minimed.com`, US state codes and US
  legal-document paths — all from `carelink.minimed.eu`. The host is not the region
  boundary; the parameter selects the market, the host only supplies the default.

### ⚠ `bgUnits` and `glucoseUnitsDefault` disagree — in 30 countries, not 2

> ⚠ **Corrected 2026-10-12 by area D.** The claim below was written from an
> 18-country sweep and recorded a two-country anomaly. Swept across all **118**
> country codes the vendor's own published config enumerates, the shape is
> **30 of 117 served documents**. **BE still reproduces; CH no longer
> contradicts; IT and ES have drifted into the contradiction since 2026-10-08.**
> The original claim is kept readable below and the correction is not smoothed
> over it.

| key | MMOL_L | MG_DL |
|---|---|---|
| `bgUnits` | GB IE NL NO SE DK FI ZA RU | US DE FR IT ES AT BE CH CL |
| `glucoseUnitsDefault` | BE CH DK FI GB IE NL NO RU SE ZA | AT CL DE ES FR IT US |

**BE and CH report `MG_DL` for `bgUnits` but `MMOL_L` for
`glucoseUnitsDefault`.** Two keys, same country, different units. Reading one and not the
other mis-scales every value [source:
findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md].

**Swept live on 2026-10-12, the distribution across all 117 served countries:**

| `bgUnits` | `glucoseUnitsDefault` | countries | client consequence |
|---|---|---|---|
| `MMOL_L` | `MMOL_L` | 51 | none |
| `MG_DL` | `MG_DL` | 36 | none |
| **`MG_DL`** | **`MMOL_L`** | **30** | **a factor of ~18 between the two keys** |

The 30: `AE AR AW BE BO BR CO CW EC EG ES GR IL IN IT JM JP KR LB MV MX NC PE PK SA SD TH TT
UY VE`. **A client that reads one key and a client that reads the other render the same
reading on a patient's screen in 30 countries, ~18× apart** (OBSERVED,
[findings-log/2026-10-12-area-d-country-sweep/FINDINGS.md §4]). `CH` returns
`MMOL_L`/`MMOL_L` today and is **not** in the set; `IT` and `ES` were recorded
`MG_DL`/`MG_DL` on 2026-10-08 and return `MG_DL`/`MMOL_L` now.

**Carbohydrate units disagree the same way, in 5 countries** — `carbDefaultUnit`
`EXCHANGES` against `carbohydrateUnitsDefault` `GRAMS` in **AM ES GE KZ**, plus
**AE**, where `carbDefaultUnit` is the lowercase string `grams` where all 116
other documents use the enum member `GRAMS` [source:
findings-log/2026-10-12-area-d-country-sweep/FINDINGS.md §5].

**Pinned:** `regression/hurl/05-public-config.check.sh` asserts BE's two unit
values as **two separate checks**, because one check asserting "they differ"
would keep passing after a vendor fix.

**Downstream:** the 2 → 30 correction changes a value a client pins, so it is
tracked for the consumer at
[#29](https://github.com/NovaLux12/carelink-api-research/issues/29)
(`downstream-bridge`).

### Other country-dependent keys

| key | varies |
|---|---|
| `mfa.status` | **`NO` = `REQUIRED`**; all 17 others `OPTIONAL` |
| `mfa.gracePeriod` | NL/NO 0 · DE/DK/ES/FI 2 · GB/IE/IT/CL/RU/SE/US/ZA 5 · AT/BE/CH/FR 7 |
| `mfa.maxAttempts` / `rememberPeriod` | NO 5 / 10; every other country 3 / 3 |
| `INSULIN_ASSESSMENT` report | **absent in FR, RU, US**; present in the other 15 |
| `dateOfBirthRequired` | **`false` only for RU**; `true` everywhere else |
| `stateCodes` | ⚠ **corrected 2026-10-12**: **US and CA only** (US states, CA provinces) · **absent** in 115 of 117 · never `null` (previously recorded as "`null` for all 17 others") |
| `techHours` | 24/7 in GB, RU, CL only · US `7:00 am - 7:00 pm CST` · the rest weekday business hours |
| `carbDefaultUnit` / `carbohydrateUnitsDefault` | `EXCHANGES` for AT/ES/RU, `GRAMS` elsewhere |
| `defaultLanguage` / `languages` / `defaultCountryName` | 11 / 13 / 18 distinct values |
| `region` / `mediaHost` | **US → `US` + `carelink.minimed.com`; all 17 others → `OUS` + `carelink.minimed.eu`** |
| `pathDocs` | FR-only `ddms.certificationPdf`; US-only `marketingAuthTerms`, `privacyPractices`, `privacyStatement`, `termsOfUse` |

Constant across all 18 countries: `uploaderAllowed` = `true`, `smsSendingAllowed` = `true`,
`defaultDevice` = `"GM"`, `firstDayOfWeek` = `"Monday"`, `legalAge` = `18`,
`blePereodicDataEndpoint` = `https://clcloud.minimed.eu/connect/carepartner/v6/display/message`.
`cpMobileAppAvailable` is ⚠ **corrected 2026-10-12 by area D** — the earlier
"false for 16 countries and `null` for GB and IE only" was an
absent-read-as-null error, and it **contradicted this repo's own pinned
assertion** (`regression/hurl/04-deep-surface.hurl` asserts
`jsonpath "$.cpMobileAppAvailable" not exists` for GB). Measured over **117**
live documents: **absent in 41**, `false` in **75**, `true` in **1** (AU), and
**`null` in none**. So the key is never null — in GB and IE it is **absent**
[source: findings-log/2026-10-12-area-d-country-sweep/FINDINGS.md §6].

Report availability is 10–11 reports per country; `INSULIN_ASSESSMENT` is the missing one
in FR/RU/US. Full vocabulary: `ADHERENCE, ASSESSMENT_AND_PROGRESS,
BOLUS_WIZARD_FOOD_BOLUS, DAILY_DETAILS, DASHBOARD, DEVICE_SETTINGS, EPISODE_SUMMARY,
LOGBOOK, OVERVIEW, WEEKLY_REVIEW, INSULIN_ASSESSMENT`. This closes the loop on
`personal.data.csv.export.enable`: **CSV export is enabled per-region, but the report
types available inside it are per-country.**

### Two per-country MFA oracles

- `/patient/countries/mfaStatusForCountry?countryCode=GB` → **200, 8 B, a bare JSON
  string** (`OPTIONAL`). A second unauthenticated MFA oracle, independent of the settings
  blob. Never previously probed.
- `/patient/countries/mfaGracePeriod?countryCode=GB` → **401 InvalidToken** — so the MFA
  *status* is public but the *grace period* is gated, **and yet the grace period is
  published anyway inside the public settings document**. A gated endpoint whose value is
  obtainable unauthenticated from a sibling is a finding about the gate, not the value.
- `/patient/countries/account/types?countryCode=GB` → 400 `arg0 must not be null` — it
  exists but wants a different argument name. Not resolved; guessing argument names was
  out of scope.

## Traps

| trap | detail |
|---|---|
| `SIMPLERA` model list | several entries are **padded with trailing whitespace** — `"MMT-5100       "`, `"MMT-5100J      "`, `"MMT-5100CLXP   "`. An exact-match parser silently misses them |
| `hurl/05` key count | the "69 keys" assertion fails if run with `?countryCode=` (70 keys) |
| S3-backed `configs/v1/` bucket | **⚠ Correction — preserved:** this bucket returns `AccessDenied`, **not** `NoSuchKey`, for keys that do not exist, so a 403 is indistinguishable from "absent" and from "present but unreadable". Every 403 in the earlier hostname-scoping argument was never evidence of non-existence — the *conclusion* (configs are hostname-scoped) still holds, because it rests on the 200s. Report sibling-name sweeps as "no evidence of existence", never "confirmed absent" [source: findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE.md] |
| per-key 404 | means "absent-or-null", not "key does not exist" |

## What this does not answer

Token-gated: the real shape of a `monitor/data` payload, whether `deviceFamily` is
spelled exactly as published on the wire, the NGP alarm-code vocabulary, and which
namespace returns real EU data [source:
findings-log/probe-2026-10-08/PUBLIC-CONFIG-FINDINGS.md].
