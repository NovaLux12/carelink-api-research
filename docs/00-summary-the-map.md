# The map

One page. What exists on Medtronic's CareLink surface, confirmed read-only and
unauthenticated. **Dated 2026-10-10.** Everything here is dated; the full reasoning
lives in `findings-log/`.

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = in a vendor document
served without a login (live, or recovered from a public web archive) · **INFERRED** =
reasoned, not seen.

> **The set — 11 further pages.** This page is the entry point; every other page links
> back here.
>
> | | |
> |---|---|
> | [`01 hosts & estate`](01-hosts-and-estate.md) | every host, the namespace→host map, DNS/CDN/PKI, the trap list |
> | [`02 auth tenants & flows`](02-auth-tenants-and-flows.md) | the Auth0 tenants, the public client the bridge impersonates, PKCE, the dead Layer7 edge |
> | [`03 discovery & versions`](03-discovery-and-versions.md) | the discovery document and the two-axis version matrix — where `android/3.6` is pinned |
> | [`04 configuration`](04-configuration.md) | the unauthenticated 69-key public config, its per-key form, the real country axis |
> | [`05 devices & vocabulary`](05-devices-and-vocabulary.md) | 16 published families, three partial model tables, spelling traps, why family matching is unreliable |
> | [`06 patient API surface`](06-patient-api-surface.md) | every `/patient/*` route, and how to tell live from dead without a token |
> | [`07 admin portal & reporting`](07-admin-portal-and-reporting.md) | `carelinkhp` is the clinic portal: `hcp/*`, the report brokers, the AWS gateways |
> | [`08 security findings`](08-security-findings.md) | ranked hardening gaps F1–F10, and what was checked clean |
> | [`09 methodology & oracles`](09-methodology-and-oracles.md) | how any of this was probed, and the four ways this project has been wrong |
> | [`10 open questions`](10-open-questions.md) | what is unknown, what is closed, and exactly what would settle each |
> | [`11 suggested research areas`](11-suggested-research-areas.md) | areas to pick up, each with a stated blocker and a definition of done |

---

> **Who builds on this.** [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge)
> consumes this surface — it ships the pinned values recorded here (the discovery
> pin, the BLE version list, the family vocabulary) to Nightscout, and runs this
> repo's regression suites before a release. Bridge bugs (login, upload,
> crashes) belong in **that** repo; anything about the vendor surface itself —
> a route moved, a version list changed, a country list grew — belongs here.
> Bridge-side notes for contributors:
> [vendor-api index](https://github.com/NovaLux12/carelink-bridge/blob/main/docs/vendor-api/README.md)
> · [architecture](https://github.com/NovaLux12/carelink-bridge/blob/main/docs/ARCHITECTURE.md).

## Three deployments, one product

| Deployment | Patient host | Cumulus host | Auth tenant | Country default |
|---|---|---|---|---|
| EU / OUS | `carelink.minimed.eu` | `clcloud.minimed.eu` | `carelink-login.minimed.eu` | `GB` |
| US | `carelink.minimed.com` | `clcloud.minimed.com` | `carelink-login.minimed.com` | `US` |
| Trials / clinical | `carelink-trials.minimed.com` | `clcloud-trials.minimed.com` | `carelink-login-trials.minimed.com` | `US` |

Each host sends a given country to **its own** `clcloud` sibling — `.eu → .eu`,
`.com → .com`. Symmetric, no anomaly. `GB` is `region: OUS` (Outside US), not
`EU`. Host-by-host detail, including the shadow deployment, is in
[`01-hosts-and-estate.md`](01-hosts-and-estate.md).

⚠ **Correction — and a second correction to this correction (2026-10-12).**
`carelink.medtronic.com` serves a byte-identical copy of the *clinician* portal
bundle. This page then said **`carelink.medtronic.eu` does not** — it returns the
same 5518-byte SPA fallback as the `carelinkhp` trap (md5-identical), so it is a
**false positive** on any status-based check. **That second claim was wrong.** The md5
was right and still reproduces (`6aedf6c4004fbb29a298bc62128480be`); the conclusion was
not. Asked for the chunk **its own entry document names**,
`carelink.medtronic.eu` serves `main.fb5f8cb7eb60c4d5.js` at 3,397,615 B, sha256
`2a7fa8e7af519c2b` — **byte-identical to the other two clinic hosts, so it is a portal
deployment.** It was mis-classified because on this host family **the catch-all *is* the
entry document**, so a document-only probe cannot tell a portal from a fallback. There
is also **no fourth patient deployment**: all 16 recorded `*trials*` hosts are `.com`
[source: findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md §1].

A **fourth Auth tenant** exists on the shadow domain: `carelink-login.medtronic.com`
(OIDC live, different JWKS kids), and with `carelink-login-trials.minimed.com`
the estate is **five** tenants. **All five have completely disjoint signing
keys** — 10 keys, none shared — so the shadow deployment shares OAuth *policy*
but not keys, and a shadow token is not a key-reuse risk. Their discovery
documents are in fact **byte-identical** once each tenant's own hostname is
substituted out. Tenant-by-tenant comparison and the PKCE posture are in
[`02-auth-tenants-and-flows.md`](02-auth-tenants-and-flows.md).

## API namespaces

Route-by-route tables for the patient surface are in
[`06-patient-api-surface.md`](06-patient-api-surface.md); the configuration namespaces in
full are in [`04-configuration.md`](04-configuration.md).

| Namespace | Notes |
|---|---|
| `/patient/*` | What most third-party clients use. `monitor/data`, `countries/settings`, `users/me`, `connect/data`. Unauthenticated → `401 InvalidToken`. |
| `/patient/v2/configuration/public` | **Unauthenticated, 69 keys.** The single best find — see *Configuration*. |
| `/patient/v2/monitor/data` | **405 — POST-only.** *A live route exists here.* Previously unrecorded; the v2 tree is a real data plane, not just a config document. GET is undefined, so 405 rather than 404 is the tell. |
| `/patient/v2/users/me` | **401 — exists, token-gated.** ditto. |
| `/patient/configuration/system/<flat.name>` | **Unauthenticated per-key projection** of the 69-key doc. 21/21 non-null keys returned byte-identical subtrees in a `{"value": "<string>"}` envelope — **booleans arrive as the strings `"true"`/`"false"`**, so a `=== false` check silently never fires. |
| `/api/carepartner/v2/*` | What the app's `baseUrlCareLink` declares, but no client actually uses it. |
| `/connect/carepartner/v{11,12,13}/display/message` | The carepartner data endpoint. GET at v11/v12/v13; **v6 exists but is POST-only**; v1–5, v7–10, v14–16 have no route. |
| `/connect/carepartner/v13/discover/android/{3.6,3.7,3.8}` | The only cells that select Auth0 **and** cumulus v13. **This is the pin that matters.** |
| `/connect/pde/v3/*` | **Closed 2026-10-11, widened to all three hosts 2026-10-12 — no route on any tested method.** GET 403 + OPTIONS 403 with `MissingAuthenticationTokenException` across `pde/v{1,2,3}/display/message`, `pde/v3/discover/android/3.6`, `csr/v1` and `csr/v3`, on **all three** cumulus hosts. The no-route body is byte-identical across all three (42 B) [findings-log/2026-10-12-pde-csr-cross-host/FINDINGS.md] |
| **`baseUrlPde` — published, and unroutable** | The discovery document publishes `baseUrlPde = …/connect/pde/v3` on **every region of every document**, and that namespace has **no GET or OPTIONS route for either recorded path under it** — `display/message` and `discover/android/3.6` — **on all three cumulus hosts**. The vendor's one published PDE base URL cannot answer, everywhere it is published. (Two paths were probed, not the namespace: the bare `/connect/pde/v3` prefix itself was never requested, so "the namespace is unroutable" is a statement about the two recorded paths.) **INFERRED** that this is a retired service left in the document rather than an "ignore this key" contract — the route 403s before any application code runs, so no client-side evidence of intent exists either way [findings-log/2026-10-12-published-pointers/FINDINGS.md §2b] |
| `/connect/csr/v2/display/message` · bare `/connect/v2/display/message` | **Live, POST-only, on all three cumulus hosts** (verified 2026-10-12, byte-identical, no region split). In no prior note before 2026-10-11. GET 403 `MissingAuthenticationTokenException` + OPTIONS 200 `access-control-allow-origin: *` [findings-log/2026-10-12-csr-cross-host/FINDINGS.md] |
| **which of those two a config-driven client can address** | **`csr/v2` yes, bare `/connect/v2` no** — and the asymmetry is the point. The public config names `csr/v2` in two keys on all three deployments; **no published document names the bare `/connect/v2`** [findings-log/2026-10-12-published-pointers/FINDINGS.md §1, §4] |
| `/patient/reports/*` — **on all three patient deployments** | **Live on `carelink.minimed.{eu,com}` AND `carelink-trials.minimed.com`, with no region split.** All seven recorded paths re-probed live 2026-10-12: `supported` / `snapshotTimelinesRange` **401**, `generateReport` / `favoriteReports` / `snapshotTimelinesForCalendar` **405** + `Allow: POST, OPTIONS`, `reportStatus` **400**, `report` **404**. Responses are **byte-identical across all three hosts**. The oracle is real here — a certainly-absent path returns 404 on every host, so the 404 is a true absence. This **widens** the 2026-10-10 finding rather than replacing it, and the supersession it made still stands: previously this namespace was mapped only to `commoncore` and recorded unreachable, and that was wrong — the reports surface is not where this repo had recorded it [findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md] |
| ↳ **correction to the row above's own provenance** | It previously read "**Live**, gated 401/405" on `.eu` alone, citing the 2026-10-10 sweep. That sweep's committed artefact disclaims itself as a "**reconstruction from the agent's report**" with the command-level evidence "**not reproduced**" and the instruction "**re-verify before treating any row as OBSERVED**"; and the bundle inventory it produced names **none** of the camelCase paths. The only committed file naming `snapshotTimelinesRange` is the **archive** table, whose header states the codes are "as archived, **not** as measured live today" (window 2020-09-29 → 2021-03-31). So the *values* were right and the *evidence class* was not: there was no live probe behind "Live". The 2026-10-12 pass supplies the first live rows, and reproduces the archived codes 21/21 [findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md §2] |
| `commoncore.medtronic.{eu,com}/reports-{broker,metadata}/v1/ocl` | Still live at path but **CloudFront 502 "could not resolve the origin domain name"** — an origin-side DNS failure, not an absence. Never archived in any crawl. |

## The version axis serves exactly two documents

The full cell-by-cell matrix is in
[`03-discovery-and-versions.md`](03-discovery-and-versions.md).

Probing an `android/X.Y` cell past 3.8 does not give you a new API — it re-derives
one of two known documents. Every cell from 3.9 upward is byte-identical except
the echoed request string (`"config": "android,12.0"`). **The "enum is
open-ended" note is superseded: there is no undiscovered Auth0+v13 fallback.**

```mermaid
flowchart LR
    A["android/X.Y cell"] --> B{"which app version?"}
    B -->|"3.6 · 3.7 · 3.8"| C["Auth0 + cumulus v13 + CLINICAL"]
    B -->|"3.5"| D["Auth0 + cumulus v11"]
    B -->|"3.9 – 12.0"| E["one document<br/>no Auth0 · cumulus v2 · no CLINICAL"]
    C --> F["the pin the bridge uses"]
    E --> G["probing a new version<br/>re-derives this same document"]
    style C fill:#2f3b2f,stroke:#6f6,stroke-width:2px
    style E fill:#3b3b2f,stroke:#fd6
```

**`v12/display/message` is live** and was in no prior note. The downstream fork's
`BLE_API_VERSIONS = [13, 11, 6, 5]`
([src/carelink/client.ts:741](https://github.com/NovaLux12/carelink-bridge/blob/main/src/carelink/client.ts))
therefore contains a permanently dead `v5` and omits a live `v12` — nothing that
changes behaviour today (v13 answers first), but the list is inaccurate.

Re-evidenced 2026-10-12: the "live on all three hosts" half of that claim had **one**
raw row behind it (`.eu` only) and is now **3 of 3** — `401` + `x-ca-err: 990` on each
of the three `clcloud.*` hosts, so there is no region split (OBSERVED,
[source: findings-log/2026-10-12-area-b-v12-routing/FINDINGS.md §Finding 1]). `v12` also
carries a CORS preflight exactly like `v11`/`v13`, while `discover/android/3.6` returns a
`401` with **no** `Access-Control-*` header at any version. So the gateway does **not** add
CORS uniformly.

**⚠ Corrected 2026-10-12 (area X).** This page previously carried the caution that the
discovery route's `401`-without-CORS could not be read as "no preflight configured",
because across the captured heads every CORS-carrying response is a `200`. **The count was
right; the host scoping was not** — four of the ten CORS-less `200`s are on `clcloud.*`
itself — four across the three cumulus hosts, **two of them on `.com`**, so **a `200` carrying no
preflight does exist there** and
status was never standing in for CORS presence. Area X re-derived the cell on all three
hosts: **9 `200`-without-CORS responses, every one a `GET` of a discovery payload, and 0
non-2xx carrying CORS anywhere**
([source: findings-log/2026-10-12-area-x-cors-separation/FINDINGS.md §4]).

**The false premise does not close the question, and an earlier draft of this note claimed it
did — that claim is withdrawn.** "Demands a token on `OPTIONS`, non-2xx never carries CORS" is
**not excluded**; the draft's reason (a configured route would carry `ACAO` on its own `200`
`GET`) assumes the very thing in dispute, since `ACAO` may be emitted only on `OPTIONS`.
Neither is "configured per route" nor "emitted only on `OPTIONS`" excluded, and no
CORS-configured `clcloud.*` route is recorded that also answers `200` on `GET`. **The cause is
still unestablished.**

**What area X did exclude:** the mechanism "`ACAO` appears only when an `Origin` request header
is sent" — across the **6** route×method pairs where both a bare and an `Origin`-bearing
request were sent (controls excluded), status and the full `access-control-*` set were
**identical in all 6**. No earlier pass could test it; none sent an `Origin` at all.

**`v11/discover` is host-dependent**, and this **contradicts** an earlier claim
that the discovery document is global: `.com` serves an 18105 B legacy doc
(cumulus v2, no Auth0, no CLINICAL, no `baseUrlCms`); `.eu` and `-trials` serve
the 20345 B Auth0/v13 doc. The claim still holds for v13, re-verified
byte-identical to the on-disk capture.

## Configuration — the unauthenticated find

In depth — the 69 keys by group, the 34 regional keys, the per-key projection and the
country axis — in [`04-configuration.md`](04-configuration.md).

`GET https://carelink.minimed.{eu,com}/patient/v2/configuration/public`
(unauthenticated, gzip, 69 keys) exists on **all three deployments**. 34 of 69
keys are regional. It contains:

| key | what it gives you |
|---|---|
| `personal.device.family.to.model.mapping` | **The complete 16-family device vocabulary.** |
| `system.settings.transfer.feature.config.device.mapping` | `{"BLE780":"780G","CC880":"MiniMed™ Flex"}` — the Flex naming. |
| `logbook.supported.entry.types` | 12 entry types. |
| `system.logbook.entry.validation.config` | **`null` on both patient regions, full schema on trials** — 12 sensor locations, 5 clinical removal reasons, 8 dose units. |
| `csr.control.codes.settings` | Device **control** codes (`dpml`/`tup`/`vex`/`tcc`). **Not** the NGP alarm set. |
| `mmm.data.api.url`, `personal.patient.timeline.config.host` | Undocumented AWS API Gateways. |
| **`system.gc.gz.transition.flags`** | **The vendor's own migration switchboard, in no prior note until 2026-10-12.** `displayMessage.useCumulusUrls` is **`true` on all three deployments**, beside a three-way plane dispatch table `personalDisplayMessageUrl` / **`csrDisplayMessageUrl`** / `carepartnerDisplayMessageUrl`. Five sibling booleans — `pullGMInfoFromCumulus`, `pullSMSHistoryFromCumulus`, `sendDiagnosticLogsToCumulus`, `sendPeriodicToCumulus`, `sendSMSFromCumulus` — are **all `true`**, so five capabilities are already on the Cumulus plane [findings-log/2026-10-12-published-pointers/FINDINGS.md §2c] |

Hash-verified **global, not regional**: the family map, the Flex naming, the
logbook entry types and the control codes are byte-identical across all three
deployments.

**`?countryCode=` on the public config is accepted but ignored** — it is echoed
back as a 70th `countryCode` key while `default.country` stays `GB` regardless. The
document is region-parameterised by **host**, not by parameter. The real country
axis is `/patient/countries/settings?countryCode=…` (35 keys, swept across 18
countries), and that sweep found something that matters: **`bgUnits` and
`glucoseUnitsDefault` disagree in BE and CH** — `MG_DL` and `MMOL_L` in the
same response. Reading the one and not the other mis-scales every value.

Also country-dependent: `mfa.status` is `REQUIRED` only in Norway;
`INSULIN_ASSESSMENT` is absent in FR/RU/US; `dateOfBirthRequired` is false only in
RU.

Two caveats that matter for anyone parsing this:

- The endpoint **serves gzip unconditionally**, ignoring `Accept-Encoding`
  (RFC 9110 §8.4 violation).
- **68 of the 69 key *names* are literal dotted strings; exactly one — `captcha` —
  is a bare segment.** A walker that splits every key name on `.` misses `captcha`
  entirely. Note the distinction: 28–30 of the 69 keys hold **object values**, so
  "nested" describes a value's type and does not single `captcha` out.
- **`personal.data.csv.export.enable` is an object, not a boolean.** It is keyed by
  plane (`personal` / `csr`), each with `aggregatedData` and `rawData`. **⚠ Corrected
  2026-10-12** — the table above recorded it as a scalar `true`/`true`/`false`, which
  happened to match `personal.aggregatedData` and hid the `csr` plane, including
  trials' `csr.rawData = true`, the one value in that key that differs from every
  personal value [findings-log/2026-10-12-published-pointers/FINDINGS.md §3a].
- The `SIMPLERA` model list contains **trailing-whitespace padding**
  (`"MMT-5100       "`). An exact-match parser silently misses them.

## Device vocabulary

The family→model tables, the three partial sources and the spelling traps are in
[`05-devices-and-vocabulary.md`](05-devices-and-vocabulary.md).

Sixteen families, published by the vendor:

```
GM  BLE700  BLE720  BLE740  BLE770  BLE780  GST  SIMPLERA
SIMPLERACC  SIMPLERACCOLID  NMX7  CC840  CC880  NMX8  INSTINCT  EAGLE
```

**⚠ This section is weaker than it looks.** The vendor's **own patient app**
(matcher module `45559` of the patient-portal bundle, served at the root of
`carelink.minimed.eu`) matches family with:

```js
{ BLE, BLE_X, SIMPLERA, SIMPLERA_X, GUARDIAN }   // deviceFamily.startsWith(...)
```

`CC880` is **not** in that set, and nor is anything containing `FLEX`. So either
the vendor's app is out of date for its own shipping device, or there is a further
family value nobody has found. **The model-prefix path is therefore the reliable
one, not the family path** — the six Flex model numbers agree across every source
held. See `findings-log/probe-2026-10-08/recov/PATIENT-APP-VOCABULARY.md`.

`CC880` is the Minimed Flex and contains `MMT-8062/8063/8082-8085`. Note it
contains **no** `BLE` and **no** `FLEX` token — which is exactly why a matcher
that greps for those two strings misses the device entirely.

Medtronic is not internally consistent about spelling: `SIMPLERA_SYSTEM` is the
enum but `"Simplera™ system"` is the value; `COSMOS` is the enum but `"Cosmos"`
is the value. **Family matching must be case-insensitive and must handle the
display-name spelling.**

`MMT-8600`/`MMT-8601` are absent from the portal bundle's device table but
present in the patient config under `SIMPLERACC`. Two partial tables, both wrong.

## Existence oracles — how to probe without a token

This is the reusable method. Established with positive controls. The probing discipline
behind it, and the four ways this project has been wrong, are in
[`09-methodology-and-oracles.md`](09-methodology-and-oracles.md); the ranked security
posture built on these observations is in
[`08-security-findings.md`](08-security-findings.md).

| Host family | Signal |
|---|---|
| `clcloud.*` | `x-amzn-errortype: MissingAuthenticationTokenException` = **no route** (every fabricated control). `UnauthorizedException` + `x-ca-err: 990` = **request reached Medtronic's Layer7 authorizer**. An `OPTIONS` returning `access-control-allow-origin: *` proves the resource exists even when GET is undefined (this is how POST-only `v6` was found). The plain 403 status line is uniform and carries no signal. |
| `carelinkhp.*` (portal) | `200 JSON` published · `412` precondition (missing client header) · `401` exists but gated · `404` absent · `405` POST-only. Namespace is case-sensitive. |

Latency is not an oracle. `403` on a fabricated path and on a dead version is
byte-identical.

## Frontends

The clinician-portal bundle, the `hcp/*` surface it declares, and the AWS gateways it
names are in [`07-admin-portal-and-reporting.md`](07-admin-portal-and-reporting.md).

`carelinkhp.minimed.eu` is the **clinician portal, not the mobile app** — of 13
host literals in its 3.4 MB bundle, exactly one is Medtronic's, and it contains
zero `/patient/*`, `medicalDeviceFamily` or NGP tokens. Source it for `hcp/*`
and device tables, never for the patient API.

Its `hp-runtime.js` holds a **225-entry lazy-chunk manifest**. All 224 chunks
were fetched and mined: they are view code — 3 hosts, 3 path literals, 0 device
families, 0 NGP codes. Their value is **89 field names** at call-sites, including
the logbook/marker fields (`removalType`, `removalReason`,
`sensorInsertionLocation`, `timecapUnscrewed`) that the deferred work needed.

**No source maps exist** on any bundle (verified for all 224 chunks offline,
plus a stratified `.js.map` sample).

The clinician portal is deployed in **two builds across five hosts**, and the split is
**product role**, not region — `carelinkhp.minimed.eu`, `carelink.medtronic.eu` and
`carelink.medtronic.com` serve the clinic build byte-identically, and
`carelink-support.medtronic.eu` and `.com` serve a different one. The hardcoded-key
finding therefore spans **five hosts**, and **there is no `.com` `carelinkhp` host at
all** — every `carelinkhp*.minimed.{eu,com}` name outside the baseline is NXDOMAIN
[source: findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md §1–§2].

## Traps

Read the full list, with the fix for each, in
[`09-methodology-and-oracles.md`](09-methodology-and-oracles.md).

| Trap | Detail |
|---|---|
| `*.carelink.{eu,com}`, `*.clcloud.eu` | **Wildcard parking DNS.** A random string resolves; all 302 to a parked page. 49 collected names are false positives. |
| Portal 200-for-everything | `carelinkhp.minimed.eu` returns 200 + `text/html` (5518 B) for every unknown path. **And that 5518 B *is* the entry document** — so no document-path probe can tell a portal from a fallback, and 5518 B maps to ≥2 digests. Ask for a content-hashed chunk instead. |
| Unconditional gzip | `carelink.minimed.eu` ignores `Accept-Encoding`. |
| Raw archive captures | Common Crawl/Wayback contain live `jsessionid_*` and plaintext-base64 OAuth `sessionData`. Facts only. |

## What we still do not know

Every open question, with what would settle it, is in
[`10-open-questions.md`](10-open-questions.md); areas to pick up are in
[`11-suggested-research-areas.md`](11-suggested-research-areas.md).

| Question | Blocked on |
|---|---|
| Which field carries `deviceFamily`, and in what casing | an authenticated `monitor/data` response |
| The NGP alarm-code vocabulary | an authenticated `application` config — 73 `hcp/configuration/*` paths probed, all closed |
| `relativeOffset` semantics for pump-offset rounding | a real token |
| Report bodies from `commoncore` | an authenticated request — **never archived in any crawl** |

### Drift, 2026-10-10

The EU reporting-country list went **17 → 29 countries in one day**
(+AU HR CZ EG GE IL PL RO RS SK SI AE), moving in lockstep with the InPen country
list. Now pinned by a drift guard, because a silent rollout is how a bridge ends up
believing a feature is unavailable.

> **Settled 2026-10-11 by live read.** Two derived sources disagreed — one recorded
> 29 countries, the other 26, and `17 + the 11 named additions = 28`, matching
> neither. A direct unauthenticated GET of the config on 2026-10-11 returns **6359 B
> and 29 countries** (`AT DK FI DE IS NO ES SE CH GB BE NL LU IT ZA CL IE AU HR CZ
> EG GE IL PL RO RS SK SI AE`). **29 is correct**; the 26 figure is retired.
> This is the eighth recorded instance of a derived note disagreeing with a
> primary observation — which is why the assertion is pinned rather than the prose.

Also confirmed held: the discovery document is still byte-identical, all five
tenants still carry disjoint keys, and the `lhpro` vendor bug is still unfixed
— finding F6 in [`08-security-findings.md`](08-security-findings.md).

### Frontends — there are two apps, not one

The clinician bundle in detail is in
[`07-admin-portal-and-reporting.md`](07-admin-portal-and-reporting.md).

`carelink.minimed.eu` and `carelink-support.minimed.eu` serve a **patient-facing
client** — 70 `/patient/*` endpoints that appear nowhere in the clinician map. The
clinician bundle replicates across **five** hosts, not two.

`regression/hurl/` pins 193 of these facts so they fail loudly rather than rot.

---

## Pages

| | |
|---|---|
| [`01-hosts-and-estate.md`](01-hosts-and-estate.md) | Host families, deployments, what each is for |
| [`02-auth-tenants-and-flows.md`](02-auth-tenants-and-flows.md) | The five auth tenants, the code+PKCE flow, the redirect single-point-of-failure |
| [`03-discovery-and-versions.md`](03-discovery-and-versions.md) | The app-version axis — why only `android/3.6`–`3.8` matter |
| [`04-configuration.md`](04-configuration.md) | The unauthenticated 69-key config file and the country axis |
| [`05-devices-and-vocabulary.md`](05-devices-and-vocabulary.md) | 16 device families; why model-matching beats family-matching |
| [`06-patient-api-surface.md`](06-patient-api-surface.md) | Patient namespaces and the existence oracles |
| [`07-admin-portal-and-reporting.md`](07-admin-portal-and-reporting.md) | The clinician portal, `hcp/*`, reports, the undisclosed services |
| [`08-security-findings.md`](08-security-findings.md) | Ranked defensive findings, and what was checked and found clean |
| [`09-methodology-and-oracles.md`](09-methodology-and-oracles.md) | How to probe this safely — and the four ways this project got it wrong |
| [`10-open-questions.md`](10-open-questions.md) | What we don't know and exactly what would settle it |
| [`11-suggested-research-areas.md`](11-suggested-research-areas.md) | **Open areas you can pick up** |
