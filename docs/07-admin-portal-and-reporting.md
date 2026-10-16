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

**The bundle is deployed on more than one host — and there are two builds, not one.**
`carelink.medtronic.com` serves a **byte-identical** copy of the clinic bundle
(3,397,615 B, sha256 `2a7fa8e7af519c2b`, `cmp` identical to `carelinkhp.minimed.eu`), as
does `carelink.medtronic.eu`. So the hardcoded-key and build-config findings below span
**three hosts**; a remediation conversation naming only `carelinkhp` would fix a third of
it [source: findings-log/probe-2026-10-08/SECURITY-FINDINGS.md].

> ⚠ **Corrected 2026-10-12 (area A).** This paragraph previously ended *"`and
> `carelink-support.medtronic.com` serves the same document."* **It does not.**
> `carelink-support.medtronic.com` serves a **different build** —
> `main.759cddab23085086.js` (3,410,666 B, sha256 `a054555a0f22176e…`), the same build
> `carelink-support.medtronic.eu` serves, and *not* the clinic bundle: asking that host
> for `main.fb5f8cb7eb60c4d5.js` returns the 5518 B catch-all. The two builds differ by
> **product role (clinic `pow` vs support `cua`), not by region** — every `.eu`/`.com`
> pair measured serves the same build. Identity is by sha256, per host:
> [source: findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md §1–§2].

| Build | Entry document (5518 B) sha256 | Main asset | Hosts |
|---|---|---|---|
| **A — clinic** | `0f2c5f6257a6fc6a…` | `main.fb5f8cb7eb60c4d5.js` | `carelinkhp.minimed.eu`, `carelink.medtronic.com`, `carelink.medtronic.eu` |
| **B — support** | `f637c8d0cd4ec6bc…` | `main.759cddab23085086.js` | `carelink-support.medtronic.eu`, `carelink-support.medtronic.com` |

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
| `pow.crm.settings` · `cua.crm.settings` | `{"base.uri":"https://carelink.medtronic.eu/crm","product":"pow","version":"4.5"}` and the same shape with `base.uri` = `carelink-support.medtronic.eu/crm` — the **CUA (support) vs POW (clinic) CRM split**, confirmed on the wire. **Superseded in its reading 2026-10-17:** the split is **not deployment-dependent** — `cua.crm.settings` answers on the clinic deployments too and carries `"product": "pow"` on all three hosts probed, so a `cua.` prefix does not mean "support deployment". See *Deployment portability of the 15 verdicts* below |
| `hcp.banner.notifications` · `pow.follow.up.settings` · `pow.country.media.groups` · `pow.invite.to.personal.uri` | a disclosed **maintenance window** (`2026-08-20T16:00Z`→`16:45Z`) with `timezone:"PT"` hardcoded on an EU portal; email rate limits, a URL regex, a 3-domain allowlist; 37 + 51 country codes; a bare `https://carelink.minimed.eu` |
| `pow.nutrino.cc.{broker,metadata}.service.config` | the `commoncore` report hosts and sub-paths — see below |

Three divergences between the HCP `cua.*` and patient `csr.*` control-code documents matter
to any client written against one and pointed at the other: the `predefined_control_codes`
array is **absent** on HCP; `lhpro`/`lghpro` max is `4294967295` on HCP but `4292967295` on
the patient side (**almost certainly a typo** — `4294967295` is 2³²−1, and the same value
appears twice more in the same object); and the `expiration_period_settings` default key is
`"DEFAULT"` vs `"default"`.

### ⚠ The one sibling that answers with no header at all

**Per-host reading, 2026-10-12 (area A).** `pow.crm.settings` is the only cell in that
table this pass measured on more than one host, and the three answers are **not**
byte-identical — which is itself the evidence that these are two deployments rather
than one mirror (OBSERVED, [source: findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md
§5]):

| Host | body bytes | `base.uri` |
|---|---|---|
| `carelinkhp.minimed.eu` | 96 | `https://carelink.medtronic.eu/crm` |
| `carelink.medtronic.com` | 97 | `https://carelink.medtronic.com/crm` |
| `carelink-support.medtronic.com` | 97 | `https://carelink.medtronic.com/crm` |

The single byte is `.eu` → `.com`. All three answered `200` with `X-System-ID: ProWeb`,
so the "no header at all" property below is confirmed on the `.com` hosts too.
`cua.crm.settings` was **not** probed, so the CUA-vs-POW split recorded above stands as
recorded and this table neither confirms nor refutes it. What the table adds is that the
`.com` **support** host publishes the **clinic** CRM base in `pow.crm.settings` —
INFERRED reading: the base tracks the **deployment** (TLD) rather than the product. One
key, three hosts, no `cua.*` reading; offered as a reading, not a finding.

> ⚠ **That reading is now measured — 15 keys × 3 hosts, 2026-10-17** — and the inference
> stands, with the reading replaced by a result and one caveat added
> [source: findings-log/2026-10-17-hcp-config-deployments/FINDINGS.md].
> `carelink.medtronic.com` and `carelink-support.medtronic.com` are **byte-identical on all
> 15** route literals while serving **two different JavaScript builds**
> (`2a7fa8e7af519c2b…` 3 397 615 B against `a054555a0f22176e…` 3 410 666 B, both digests
> re-asserted this pass), and in **6** of the 15 the only difference anywhere is
> `carelink.medtronic.eu` against both `.com` hosts. The axis that moves content is the
> **TLD**; the product role does not move it. Area A's caveat, restated rather than
> inherited: `carelink-support.medtronic.eu` was **not** swept, so its verdicts are
> **INFERRED** from the digest pair and are excluded from every figure below.

### Deployment portability of the 15 verdicts — **15 of 15**, and the POW/CUA split is not there

The single-deployment reading above is now three deployments wider. Each host's build was
re-fetched by its **content-hashed asset name** and its recorded digest asserted before any
key list taken from it was used (OBSERVED, **4 of 4** reproduce), and each host's candidate
list was extracted offline from **that host's own route table** — never from this page.
**87 of a 90 cap** — the one bounded revision the claim allows, taken because the pinned suite the gate runs on every push was not in the claim's arithmetic; **no row was deleted to absorb it**, `GET` only, ≥2.5 s same-host inside a shared per-host lock, measured
`t_sent` floor **2.276 s** over 57 gaps with 1 sub-floor reading and **no cause asserted**
[source: findings-log/2026-10-17-hcp-config-deployments/FINDINGS.md].

**The verdicts are deployment-portable: 15 of 15 keys carry the same status verdict on
`carelink.medtronic.com`, `carelink.medtronic.eu` and `carelink-support.medtronic.com` —
the same 15 that `HCP-CONFIG-SCHEMA.md` §10 records for `carelinkhp.minimed.eu`.** All four
controls passed on all three hosts, which is what makes the two 404s per host trustworthy:
the certainly-absent path returned **404 with 0 bytes and no `content-type`** on all three
(not the `carelinkhp` 5518 B HTML trap), `CSU.CONTROL.CODES.SETTINGS` → **404** against
`cua.control.codes.settings` → **200** re-derives the case-sensitivity half on each host, and
`logbook.supported.entry.types` with **no header** returned **412** on all three.

**The POW/CUA split is not visible on this surface — that is the answer, and it supersedes
the reading above.** `cua.*` answers on the clinic deployments and `pow.*` answers on the
support deployment; **both namespaces answer everywhere**, and the payloads say so
themselves: **`cua.crm.settings` carries `"product": "pow"` on all three hosts** (OBSERVED).
`docs/07`'s earlier sentence describing the split stands as a record of what one key on one
host showed, and the following sentence is now settled: **`cua.crm.settings` was probed on
all three hosts** — 200 · 105 B / 104 B / 105 B, `base.uri` the **support** CRM while
`product` reads `pow`. A `cua.` prefix does not mean "support deployment"; a client must read
`base.uri`, never the prefix. The split is real, but it lives in the bundle's runtime
product selection (`JS-API-SURFACE.md` §7.15) and nowhere on this config surface.

**Same verdict, different body — and the two axes are different.** **9 of 15** keys are
byte-identical across all three hosts; the **6** that differ are `cua.crm.settings`,
`pow.crm.settings`, `pow.invite.to.personal.uri`, `hcp.banner.notifications`,
`pow.nutrino.cc.broker.service.config` and `pow.nutrino.cc.metadata.service.config` — in
every one the `.eu` host is the odd one out and the two `.com` hosts match.

Three deployment-level facts this pass adds, none of which `docs/07` recorded:

- **`carelink-support.medtronic.com` serves no `content-security-policy`, no
  `strict-transport-security` and no `x-content-type-options`** — **0 of 19** responses each,
  against **19 of 19** on both clinic hosts — and advertises
  `access-control-allow-headers: X-System-ID` where both clinic hosts advertise
  `X-System-ID, Content-Type, authorization` (20 of 20 responses each). **Severity: low** —
  a hardening gap, not an access control, and **no cause is asserted**. Recorded as an
  observation; it belongs beside `docs/08`'s F2, which records the *key* replicating across
  deployments while the *hardening* does not.
- **A credential-shaped `x-api-key` is reachable through this surface.** `docs/08` F2 records
  the key material inside the public bundle; it is also served **unauthenticated** by
  `pow.nutrino.cc.{broker,metadata}.service.config` on the `.com` deployments, where
  `carelink.medtronic.eu` serves the **placeholder** the pinned suite asserts. Value
  **redacted** per `SECURITY.md`; `findings-log/2026-10-17-hcp-config-deployments/REDACTIONS.md`
  records the substitution. Already known — **not a new disclosure**.
- **`application/octet-stream` on 11 of the 13 answering keys**, on all three hosts — a far
  wider version of the settled note below. **Whether that is per-host or a loose 2026-10-08
  record is NOT determined**: `carelinkhp`'s config surface was not re-probed, its own §10
  saying do not re-run it.

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

> [!IMPORTANT]
> ⚠ **Two corrections, 2026-10-13 (the `commoncore-trials` pass, #58).** Both readings are retained above.
>
> **(1) The `403` is not evidence these six endpoints exist.** This section read the
> uniform `403` as "live, auth-gated". Under [Oracle A](09-methodology-and-oracles.md)
> these hosts are AWS API Gateway behind CloudFront, where
> `MissingAuthenticationTokenException` **is** the unmatched-route error and a
> certainly-absent control is byte-identical to the published root. A fabricated path
> (`/reports-broker/v1/ocl-probe-absent`) on `commoncore.medtronic.com` returns the
> **same status, the same error type and the same body digest** (`f249b63c…`, 42 B) as
> the real one (OBSERVED). **The six paths above remain the vendor's own config values
> — that is unchanged — but the status code is not what establishes that they are
> served**, and this section used it that way.
>
> **Two limits on that correction, so it is not over-read in the other direction:**
> **(a)** it is **adjudicated on `.com` only** — the absent-path control exists on
> `commoncore.medtronic.com` (seq 4 vs 5), **not** on `.eu`, so the
> `commoncore.medtronic.{eu,com}` brace above is **not** one adjudicated pair and the
> EU cell is corroboration. **(b)** the "**`404` is never emitted**" half of Oracle A
> is **INFERRED by analogy from `clcloud.*`**, whose scope `docs/09` states as
> `clcloud.*` plus the five `execute-api` gateways; `AWS-GATEWAYS.md` names no
> `commoncore` host, and this pass **observed no `404` in either direction**. The
> correction rests on the byte-identical control, which needs neither clause.
> [findings-log/2026-10-13-commoncore-trials/FINDINGS.md §2b, §5]
>
> **(2) The `commoncore.medtronic.{eu,com}` brace was missing a case.** The trials
> deployment has its own pair: its *config* sets `nutrino.cc.broker.service.config.host`
> to `https://commoncore-trials.minimed.com/reports-broker/v1`, while its *CSP* allows
> **`commoncore-trials.medtronic.com`** — which is a **real host** (CNAME to
> CloudFront, host-specific DigiCert SAN match). Both answer `403`. Whether that split
> is deliberate or a stale config entry is **INFERRED and unresolved**
> [findings-log/2026-10-13-commoncore-trials/FINDINGS.md §2b, §3b].

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

### ⚠ Re-measured 2026-10-14 (area F, #123): the BLOCK-7 cells ran, and the caller question has a negative answer

Two separate questions are now closed, and one is explicitly **not**. 17 requests of a
40 cap, GET only, ≥2.5 s same-host, **controls first on every host** [source:
findings-log/2026-10-14-pool-f-timeline-caller/FINDINGS.md].

**1. The `BLOCK 7` cells that had never run are negative.** [AWS-GATEWAYS.md](../../findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md):240-242 records
that they never happened — an accidental re-run ate the last four budget slots. They ran
here: `GET /prod/patient-timeline/v1/events` on all three `patient-timeline` deployments,
and `GET /prod/patient-timeline/logbook` on the EU one, plus the `v1` prefix root.

**All 11 of 11 `patient-timeline` cells** now answer `403`,
`MissingAuthenticationTokenException`, 42 B, and the certainly-absent control is
**byte-identical to every plausible path on every deployment** — one body digest across
all eleven, `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16`, which
reproduces the 12-character digest this page already published **in full** for the first
time (OBSERVED). Under Oracle A that is **no matching GET route** under
`/prod/patient-timeline` on any of the three deployments. **Zero 404s in 17 requests** on
both gateway families, which removes the `clcloud.*` analogy from the "404 is never
emitted" clause and observes it on this family directly.

**2. `dialog-lite` still 500s, and the control says what that means.** All four cells,
both regions, published root *and* certainly-absent control, answer `500` with one body
digest (`660f19c0…`, 36 B — **new**; the 2026-10-10 pass recorded the size but published
no digest). Because the control is byte-identical to the root, the `500` **cannot
discriminate the path**: it is the stage-wide catch-all's signature, not evidence that any
particular route exists. What reproduces is that both deployments route anything with at
least one path segment below the stage root and the integration raises on every
invocation. **Zero of 15** gateway responses carry any `Access-Control-*` header and the
header set is still exactly the six keys listed above — so this section's
"structurally not browser-callable" premise is re-observed, not re-derived.

**3. Who calls these: a negative, and a structurally grounded one.** Both portal builds
were re-fetched on their **content-hashed asset names** and both reproduce their pinned
anchors in full (`2a7fa8e7…`, 3 397 615 B; `a054555a0f22176e…`, 3 410 666 B), so the
corpus is the corpus. In **both** bodies, every one of these scores **zero**:
`patient-timeline`, `dialog-lite`, `app-patient-timeline`, `patientTimeline`, both
`personal.patient.timeline.*` spellings, `execute-api`, `prodous`, `/patient/`, `clcloud`,
`carelink.minimed` — **and each of the five 10-character gateway ids**.

The reason is larger than the absence, and it is why no server-side proxy can exist in
these builds either: **`personal.` occurs 4 times and none of the four is a key of the
69-name patient document**, `/patient/` is 0, and the API surface these builds name is the
clinician namespace (`hcp/patients` 42 hits, `hcp/configuration/public/` 15 hits). **They
do not read the patient configuration document at all**, so the pointer
`personal.patient.timeline.config.host` is unreachable from this code — which is a
statement about the code, not about the service (OBSERVED for the two build facts;
INFERRED for the "no proxy" consequence).

**And the false-hit class, quantified, because a bare grep would have reported an
integration that is not there:** `timeline` scores **196** (66 + 126 + 4 across 74
signatures) against `patient-timeline`'s **0**, and every one of the 196 is GSAP
animation-library internals, Pusher SDK internals, Medtronic's own snapshot-timelines
**report** service (`hcp/reports/getSnapshotTimelinesRange`, `TIMELINE_RANGE`), two
leaked-password dictionary words, or one analytics label. `grep-out.txt` counts
**per build**, so: `m2m` — the call pattern the area's own text proposed — is **1
hit in each build** (2 across both), and it falls in the **middle** of `cum2me`
inside a leaked-password list; `baseUrl` is **2 hits in each build** (4 across both), and
every one of them is inside an embedded Pusher SDK, not a CareLink base (OBSERVED).

**4. What is NOT closed.** Which of the three readings explains the `403`s — no routes
deployed / routes for other verbs only / the live stage is not `prod` — is **unchanged and
still blocked**: separating them needs an authentication attempt, which `AGENTS.md` §8 and
§11 exclude. Four more cells went into that same dead end and did not move it. See
[`docs/10`](10-open-questions.md) §1. Also unchanged: *why* `dialog-lite` raises, and
whether the raw `…timeline.config.host` value is publishable — the latter is a disclosure
judgement for a maintainer holding the value, and is **not** pre-committed here.

**One scope limit that belongs with the negative.** Three builds exist and only one has
ever contained the timeline at all: the **patient** build carries
`patient-timeline` 5 times, every hit an Angular component selector, with the config
pointer read and its gateway-host sibling named but read by nothing (area V, 2026-10-13;
that host is outside the host set #123 authorises, so that record is **cited, not
reproduced**). So the honest scope of the negative is *no web caller in any of the three
builds this repo has read* — not *no caller exists*. **INFERRED**, and it is a claim
about the corpus, not about every client the vendor ships.

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