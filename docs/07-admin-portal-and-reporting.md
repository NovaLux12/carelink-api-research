# Admin portal and reporting

> **Navigation** — the map: [`00-summary-the-map.md`](00-summary-the-map.md) · ← prev: [`06-patient-api-surface.md`](06-patient-api-surface.md) · → next: [`08-security-findings.md`](08-security-findings.md) · related: [`10-open-questions.md`](10-open-questions.md)

Dated 2026-10-10. Sources, all under `findings-log/probe-2026-10-08/`:
`recon/JS-API-SURFACE.md` · `recon/HCP-CONFIG-SCHEMA.md` · `recon/AWS-GATEWAYS.md` ·
`CROSS-REGION-CONFIG-FINDINGS.md` · `SECURITY-FINDINGS.md` · `AUTH-TENANT-FINDINGS.md`.

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = vendor document served
without a login · **INFERRED** = reasoned, not seen.

## `carelinkhp` is the clinic portal, not the mobile app

`hp-main.js` — 3,397,615 B, 102 lines, minified Angular 17 webpack (`webpackChunkpow`),
companion `hp-runtime.js` 8,597 B. The decisive negative: **zero** occurrences of
`/patient/*`, `/connect/carepartner/*`, `/api/*`, `/pde/*`, `/oauth/*`, `monitor/`, `NGP`,
`BLE`, `BLE_MINIMED` or `medicalDeviceFamily`, and of 13 distinct host literals **exactly
one is Medtronic's** (`dev.commoncore.medtronic.eu`); the other 12 are Pusher, Mixpanel,
cdnjs, webpjs and w3.org. Source it for `hcp/*` and device tables; never for the patient
API [source: findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md].

**The bundle is deployed on more than one host.** `carelink.medtronic.com` serves a
**byte-identical** copy (3,397,615 B, sha256 `2a7fa8e7af519c2b`, `cmp` identical to
`carelinkhp.minimed.eu`) and `carelink-support.medtronic.com` serves the same document. So
the hardcoded-key and build-config findings below span **two hosts**; a remediation
conversation naming only `carelinkhp` would fix half of it [source:
findings-log/probe-2026-10-08/SECURITY-FINDINGS.md].

`hp-runtime.js` holds a **225-entry lazy-chunk manifest**; all 224 chunks were fetched
(4.4 MB) and added **0** Medtronic hosts, **3** API path literals and **3** `MMT-*` codes —
all API definitions live in the eager main bundle. What they *did* add: new endpoint literals
(`POST /hcp/sso/auth/otc/send`, `GET hcp/countries/dialCodes`,
`GET hcp/patients/checkPhoneNumber`, `GET /connect/retina/searchfilter`,
`POST /connect/retina/searchfilter/feedback`) and **89 distinct field names at HTTP
call-sites**, including the
logbook/marker fields (`removalType`, `removalReason`, `sensorInsertionLocation`,
`adhesivetapeLocation`, `timecapUnscrewed`, `notes`, `entryTs`) [source:
findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md].

> **⚠ Correction — preserved.** An earlier note claimed neither `main.js` nor `runtime.js`
> contains a `sourceMappingURL` comment. **False** — `hp-main.js` contains the token at byte
> offset 1791807, though not as a directive: it is the string literal inside webpack's
> bundled `worker-loader`, carried alongside the workers. The conclusion stands; the reason
> originally given for it was wrong.

## The `hcp/*` surface

**183 distinct path literals**, 188 const bindings; 175 begin `hcp/` and 8 begin `/hcp/`
(a second binding of the same path, not additional endpoints). One literal is
`" /hcp/linkedPatient"` **with a leading space**, so a raw-byte grep for
`/hcp/linkedPatient` misses it. All live on the portal origin; no separate API host.

Counts by family: **`patients` 47** (incl. 18 `((patientId))/*`) · **`clinics` 40** ·
**`user` 29** · `configuration` 21 (6 direct + 15 `public/*`) · `reports` 10 (4 audit-log) ·
`insights/v1` 8 · `dataUpload` 6 · `fastLinking`/`linkedPatient`/remote-user 7 ·
`anonymization` 4 · `access-data` 4 (+ `hcp/v2/clinics/access-data`) · `follow-up` 4 ·
`sso` 3 (login/logout/reauth) · others 14 (`registrationCheck`, `ping/ping`, `locale`,
`countries`, `remoteLinking`, `settings-calculator`), of which 4 have **0** call sites in
the main bundle.

> **⚠ Unresolved source disagreement.** `JS-API-SURFACE.md` §2.1 records **12**
> `hcp/clinics/toggle/*` endpoints; §7.7 of the same file and `AUTH-TENANT-FINDINGS.md` §7
> enumerate **9** (`csv`, `patient-dashboard`, `blinded-cgm`, `therapy-data`,
> `remote-monitoring`, `clinic-outcomes`, `clinic-user-settings`, `titr-settings`,
> `status`), and the verbatim literal list in that same file contains **9 distinct**
> `hcp/clinics/toggle/*` paths. The count of 12 is not reconcilable with the enumeration.

**MFA / user / clinics counts.** `hcp/user/*` — **29 endpoints** (prior notes had 1), incl.
`getMfaUserStatus`, `verifyMfaCode`, `sendMfaCodeAfterReCaptcha` ⇒ **the portal enforces
MFA**; the reCAPTCHA site key arrives via authenticated `POST hcp/configuration/user`, so it
cannot be harvested unauthenticated. `hcp/clinics/*` — **40 endpoints** (prior notes had 2),
incl. the MFA policy quartet, the security-profile trio and the clinic-wide kill-switch list.
`hcp/patients/((patientId))/logbook/{entries,entries/filled,entries/last}` is the *read* side
of the logbook vocabulary: three endpoints, previously documented as one.
`hcp/patients/*otc-linking*` — 6 endpoints plus `ext-otc=true&username=` on the
`hcp/sso/login` redirect, with zero prior mention of `otc`; what the acronym stands for is
**Unknown** — not in any source, and deliberately not guessed. `hcp/sso/{login,logout,reauth}`
+ `hcp/ping/ping` is a **second, cookie-based** session mechanism, separate from the mobile
`/oauth/*` surface; Pusher channel names are reversible
(`(n²+n).toString(16)`, unkeyed), and `retinaEnabled`/`cuaEnabled` both ship **off**.

## `/hcp/configuration/*` and the header contract

`BASE = https://carelinkhp.minimed.eu`, `PREFIX = /hcp/configuration/public/<key>` — all
relative to the portal origin, no separate API host. The `hcp/` prefix is not guessed: it is
the literal the bundle's constants table binds.

`X-System-ID` is mandatory and its **value** is validated: absent, empty (`X-System-ID;`)
or invented (`NotARealClient`) all return **412, 0 bytes**; `ProWeb` **and** `proweb` both
return 200. It is a **client-identity selector the vendor enumerates**, rejected at the edge
**before routing** (`x-cache: Error from cloudfront`, `x-amz-cf-pop: LHR5-P7` — CloudFront
in front of an API Gateway). The value comparison is case-insensitive even though the **key
namespace is case-sensitive**; `Accept` is not load-bearing — the whole contract is
`X-System-ID: ProWeb`, and only the `public/` subtree is behind this check [source:
findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md].

With the header, **13 of the 15 bundle-declared `public/*` keys return JSON**, one is
token-gated (`personal/media/config/<locale>` → 401) and one is an empty `{}`
(`cms-config.json`). The notable bodies:

| key | what it publishes |
|---|---|
| `cua.control.codes.settings` | 778 B — the HCP twin of the patient `csr.control.codes.settings`. **Control** vocabulary (`dpml`, `tcc`, `tup`, `lhpro`, `lghpro`, `vex`, `ssd`, `gstpro`, `gstrc`), **no N-codes, no severity vocabulary** |
| `logbook.supported.entry.types` | 226 B — **byte-identical, list-for-list, to the patient-side key**. The key is unprefixed, and unprefixed means "shared", not "patient" |
| `user-identifier-settings?countryCode=…` | the only `public/*` key that takes a parameter and genuinely varies: US = bare 10-digit phone (`^\d{10}$`), EU/DE = 20-char Unicode class |
| `pow.crm.settings` · `cua.crm.settings` | `{"base.uri":"https://carelink.medtronic.eu/crm","product":"pow","version":"4.5"}` and the same shape with `base.uri` = `carelink-support.medtronic.eu/crm` — the **CUA (support) vs POW (clinic) CRM split**, confirmed on the wire |
| `hcp.banner.notifications` · `pow.follow.up.settings` · `pow.country.media.groups` · `pow.invite.to.personal.uri` | a disclosed **maintenance window** (`2026-08-20T16:00Z`→`16:45Z`) with `timezone:"PT"` hardcoded on an EU portal; email rate limits, a URL regex, a 3-domain allowlist; 37 + 51 country codes; a bare `https://carelink.minimed.eu` |
| `pow.nutrino.cc.{broker,metadata}.service.config` | the `commoncore` report hosts and sub-paths — see below |

Three divergences between the HCP `cua.*` and patient `csr.*` control-code documents matter
to any client written against one and pointed at the other: the `predefined_control_codes`
array is **absent** on HCP; `lhpro`/`lghpro` max is `4294967295` on HCP but `4292967295` on
the patient side (**almost certainly a typo** — `4294967295` is 2³²−1, and the same value
appears twice more in the same object); and the `expiration_period_settings` default key is
`"DEFAULT"` vs `"default"`.

### ⚠ The one sibling that answers with no header at all

On the **shadow** portal `carelink.medtronic.eu` (no header, unauthenticated), the same
family was probed. `/hcp/configuration/public/pow.crm.settings` → **200, 96 B**, while
**nine siblings** return **412** each — `cms-config.json`, `pow.invite.to.personal.uri`,
`pow.browser.check.configuration`, `pow.mmo.config`, `pow.udi.number`, `pow.udi.certificate`,
`logbook.supported.entry.types`, `cua.control.codes.settings`,
`system.logbook.entry.validation.config`. `pow.crm.settings.version` → 404;
`/hcp/configuration/{application,user,countries/getAllCountries}` → 405 (POST-only);
`/hcp/configuration/product/info` → 404.

One endpoint answers unauthenticated where all nine siblings require the client header. Low
sensitivity — a CRM base URI and a version string, no PII, no credential. **The finding is
the inconsistency, not the content.** It corroborates that the shadow deployment's content
namespace is `pow` (version 4.5) where the patient deployments use `ocl` (14.x → 15.5)
[source: findings-log/probe-2026-10-08/AUTH-TENANT-FINDINGS.md].

*Content-type, **settled** 2026-10-10 by live re-probe:* HTTP 200,
`application/octet-stream`, `content-length: 96`, JSON body. An earlier record in
`HCP-CONFIG-SCHEMA.md` said `application/json`; that record was wrong and the
source now carries the correction. The 200 was on the shadow host
`carelink.medtronic.eu`, not `carelinkhp.minimed.eu` — both were probed, both
return it. Worth noting for a client: the body parses as JSON but the *type* is
`octet-stream`, so anything branching on `content-type` will not parse a working
response.

### Portal existence oracle — full

| response | meaning on `…/configuration/public/<key>` |
|---|---|
| `200` + `application/json` | key exists, published unauthenticated |
| **`401` + `application/json` + `{"error":{"type":"InvalidToken","group":"AUTH"}}`** | **key exists but is token-gated** |
| **`404`, 0 bytes** | **key does not exist** |
| `412`, 0 bytes | header check failed |
| `405` | key exists but is POST-only |
| `200` + `text/html` + exactly 5518 B | **SPA fallback — means nothing about existence** |

Positive control: `…/public/personal/media/config/eu` → 401 (exists, gated) versus
`…/public/personal/media/config` → 404 and `…/public/zzz.this.does.not.exist.zzz` → 404.
Case-sensitivity control: `CSU.CONTROL.CODES.SETTINGS` → 404 while
`cua.control.codes.settings` → 200. **Existence is resolvable without authentication;
content is not.**

> **⚠ A hypothesis formed and refuted — the refutation is the finding.** HCP prefixes do
> **not** mirror patient prefixes: `hcp.control.codes.settings` → 404 (the key lives at
> `cua.`), `hcp.logbook.supported.entry.types` → 404 (unprefixed),
> `csr.logbook.supported.entry.types` → 404 (unprefixed). The `hcp.` namespace is a third
> namespace, not an alias family, so the 404 list stands as a list, not a proof by mapping.

**Verdict on the NGP alarm vocabulary: a firm negative.** 28 distinct key names across both
rounds, all 404, spanning every plausible vocabulary, and trustworthy because of the two
controls above; the corpora on disk agree (the 69-key patient config has zero `N\d\d` tokens;
`hp-main.js` scores 0 case-sensitive hits for `N24|N35|N40|N47|N48|N50|N55|N131`, `ALARM`,
`alarmCode`, `stop_using_pump`, `stopUsingPump`; the 224-chunk corpus none). Do not re-run.

## The report brokers — `commoncore.medtronic.*`

Bases: `https://commoncore.medtronic.{eu,com}/reports-broker/v1/ocl` and
`https://commoncore.medtronic.{eu,com}/reports-metadata/v1/ocl`. Six endpoints — broker
`/reports/{generateReport,reportStatus,reportCsv,reportPdf}` and metadata
`/reports/{ReportDataTimelinesRange/patients,ReportDataTimelinesForCalendar}` — all **403**
unauthenticated. `dev.commoncore.medtronic.eu` resolves but is **502** (backend down);
`commoncore.minimed.eu` is also 502 — a **different host**, not a twin [source:
findings-log/probe-2026-10-08/SECURITY-FINDINGS.md].

> [!CAUTION]
> **HELD BACK — not published.** A finding about these endpoints was
> removed from this repo before it went public, at the maintainer's instruction. The
> legitimate half is below; the rest is held for a disclosure decision.

### The remaining half of that finding

The **EU** deployment ships a literal placeholder in
`security_headers["x-api-key"]` — 17 characters, not a credential. That is
published here, and it is the useful part: it explains the *class* of bug, and it
exposes nothing.

What is withheld is the comparison against the other deployments. Held for a
disclosure decision, not a technical one.
production API base is a **`dev.` host** — **verified not live** (403 both with and without
the key against `commoncore.medtronic.{eu,com}`, 502 against `dev.`); (3) the inert

## The AWS API Gateways — structurally not browser-callable

Five `*.execute-api.*.amazonaws.com` endpoints are disclosed by the patient public config.
Bounded enumeration (90 requests, cap reached, GET + one OPTIONS preflight per host):

| service | regions | probe result |
|---|---|---|
| dialog-lite (`mmm.data.api.url`) | EU `/prodous/`, US `/prod/`, **null on trials** | **500 JSON** (Gateway up, root unrouted) |
| patient-timeline (`personal.patient.timeline.config.host`) | EU, US, trials | **403** `Missing Authentication Token` |
| CSR periodic (VPC endpoint) | one per deployment | timeout — private, as expected |
| CSR CRM · retina | `carelink-support.minimed.{eu,com}/crm` · `clcloud.*` + `/connect/retina/v1/personalWebView` | 403 · **401** JSON |

**The enumeration found no new paths, because the question was malformed.** On AWS API
Gateway **REST** APIs, `403 Missing Authentication Token` is the **unmatched-route** error,
not an auth-gate: a certainly-absent UUID returns **byte-identical output** to the published
root, `404` is never emitted at all (zero 404s in 90 requests), and all 44 of the 403s carry
the same 42-byte body. A usage-plan denial would read `{"message":"Forbidden"}` and never
appeared; a dummy `X-Api-Key` header changed nothing, so **no usage-plan key is required**.
The one working discriminator runs the other way: **on dialog-lite,
`500 InternalServerErrorException` ⇒ the path is matched and routed** (`GET /prodous/` → 403
but `GET /prodous/<uuid>` → 500). Which reveals the structural finding:

> **Both dialog-lite deployments are a single stage-wide `ANY /{proxy+}` catch-all over the
> whole stage, with a Lambda proxy integration that raises on every invocation** — on GET and
> on OPTIONS, with and without `X-Api-Key`, across 22 distinct request shapes and two
> independent regions. `dialog-lite/v1` in the published URL is therefore **not an API
> Gateway resource**; it is opaque path data handed to the Lambda, and the service has no
> route table to enumerate. **No `Access-Control-*` header appears on any of the 90
> responses**, including five explicit preflights — so a service published in the
> patient-facing public config **cannot be called from a browser at all**.

`patient-timeline` is the mirror image: `GET /prod/<uuid>` → 403 proves there is **no
`{proxy+}` at the stage root**, so no GET or OPTIONS request reached any backend on any of
the three gateways. Three readings are consistent with the evidence and cannot be separated
with GET-only probing: no routes are deployed in the `prod` stage; routes exist only for
other verbs; or the live stage is not `prod`. The complete observed response header set is
six keys and nothing else (`date`, `content-type`, `content-length` 36/42,
`x-amzn-errortype`, `x-amzn-requestid`, `x-amz-apigw-id`) — **nothing in any response
reveals stage, region, mapping template or backend service name**, and latency is the only
region-correlated signal in the whole dataset (EU ~73–93 ms, US ~256–402 ms) [source:
findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md].

## The biggest blind spot

**Prod `commoncore.medtronic.{eu,com}` has never been archived in any crawl** — only its
`dev`/`stage1`/`preprod1` twins exist. The reports backend behind repo issue #76 is the
**single largest unarchived surface in the project**; report bodies need a token [source:
findings-log/probe-2026-10-08/AUTH-TENANT-FINDINGS.md].

## Traps

| trap | detail |
|---|---|
| Portal 200-for-everything | `carelinkhp.minimed.eu` returns **200 + `text/html` + exactly 5518 bytes** for every unknown path. Discriminate on `Content-Type`, never on status code — filtering on status alone would have stored 225 copies of `index.html` and reported a clean chunk sweep |
| `*.carelink.{eu,com}`, `*.clcloud.eu` | **wildcard parking DNS**: a random string resolves and all 302 to a parked page. 49 collected names are false positives; never report one as a vendor asset |
| Internal hostnames in CT logs | recorded and redacted to `<service>.<internal>.minimed.<tld>` — the finding that CT logs leak internal infrastructure names survives, the names do not |