# Configuration — the unauthenticated public config

Dated 2026-10-10. Sources: `findings-log/probe-2026-10-08/PUBLIC-CONFIG-FINDINGS.md`,
`CROSS-REGION-CONFIG-FINDINGS.md`, `recon/CONFIG-NAMESPACE-DEEP.md`, `recon/CONFIG-NAMESPACE.md`.

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = vendor document served
without a login · **INFERRED** = reasoned, not seen.

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

35 of the 69 key names are recorded in the findings logs. The other 34 are
**Unknown** — not enumerated in any source.

| group | keys | notes |
|---|---|---|
| device vocabulary | `personal.device.family.to.model.mapping`, `system.settings.transfer.feature.config.device.mapping` | 16 families; `{"BLE780":"780G","CC880":"MiniMed™ Flex"}` — see `05-devices-and-vocabulary.md` |
| logbook | `logbook.supported.entry.types` (12 types), `logbook.enabled`, `logbook.entries.page.size` (= 30), `system.logbook.entry.validation.config` | validation config is `null` on both patient regions, full schema on trials |
| device control codes | `csr.control.codes.settings` | `dpml`/`tup`/`lhpro`/`lghpro`/`vex`/`ssd`/`tcc`/`gstpro`/`gstrc` with ranges. **Not** the NGP alarm set — no N-codes |
| disclosed service hosts | `retina.endpoints.config.personal.target_url` (+ `dashboard.base_uri`), `csr.cumulus.periodic.data.endpoints`, `mmm.data.api.url`, `personal.patient.timeline.config.host`, `praas.uri.path.reports.ping`, `nutrino.cc.{broker,metadata}.service.config` | five live service URLs, two never previously recorded; `praas` and the CSR AWS VPC endpoint are internal and not publicly reachable — recorded, not probed |
| regional feature flags | `personal.clinical.environment`, `personal.safety.notices.enabled`, `personal.data.csv.export.enable`, `personal.cookie.consent.policy.enabledGlobally`, `personal.dob.validation.enabled`, `personal.mixpanel.analytics.settings.{enabled,token}`, `personal.username.as.email.settings.enabled`, `personal.inpen.supported.countries.enabledGlobally` | see the regional table below |
| country lists | `personal.common.core.reporting.enabled.countries`, `personal.countries.certification.enabled`, `personal.inpen.supported.countries` | grow over time — see the drift note |
| auth / redirect | `personal.integrations.redirect.scheme.whitelist`, `system.auth0.url.whitelist`, `captcha.key`, `personal.session.timeout` (= 30) | the bridge's `com.medtronic.carepartner:/sso` redirect is **not** in the integrations whitelist — that whitelist governs deep links, not the OAuth callback, so this is context, not a contradiction |
| misc / operational | `personal.third.party.apps`, `outages.nextupdateat`, `default.country`, `personal.crm.settings`, `personal.retina.endpoint.config` | `captcha.key` is a reCAPTCHA **site** key, public by design |

Two `nutrino.cc.*` keys carry a `security_headers["x-api-key"]`. **EU ships a literal
placeholder; US and trials ship real-looking tokens.** Values are redacted everywhere in
this repo — existence and shape only, never the value. Detail in
`07-admin-portal-and-reporting.md` [source:
findings-log/probe-2026-10-08/CROSS-REGION-CONFIG-FINDINGS.md].

### Global vs regional — hash-verified

sha256 of canonical JSON, identical on all three deployments:

| key | digest |
|---|---|
| `personal.device.family.to.model.mapping` | `215e6671de09` |
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

## The 34 regional keys

Ten differing keys are documented. The other 24 are **Unknown** — not itemised in any
source.

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
| `personal.common.core.reporting.enabled.countries` | 17 countries | `["US","PR"]` | 21 |

`personal.safety.notices.enabled` is the medically relevant one: it is **true on the US
deployment only**, and safety notices are how Medtronic communicates device advisories to
patients. It is a regional difference, not a constant.
`logbook.enabled` is false on both patient regions, which is why the entry-validation
schema ships `null` there and populated only on trials.

Also regional: `personal.countries.certification.enabled` is `["FR","YT","NC","PF"]` on EU
(an EU MDR certification rollout in progress) and empty elsewhere;
`personal.third.party.apps` is `DS_EMEA_1_GLOOKOXT` on EU and `DS_AMERICANS` on US, with
no equivalent on trials; `outages.nextupdateat` is populated on trials only; each
deployment has its own reCAPTCHA site key and Mixpanel token.

**Live drift, recorded 2026-10-09 → 2026-10-10:**
`personal.common.core.reporting.enabled.countries` grew **17 → 26** (AU, HR, CZ, EG, GE,
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
- **21 of 21 probed non-null keys returned a value byte-identical to the corresponding
  subtree of the 69-key document.** This is a projection, not a second source — but it is
  a 69-request enumeration path for the namespace.
- **Null-valued keys 404.** `system.logbook.entry.validation.config` and
  `personal.retina.endpoint.config` are both `null` on EU and both 404. A per-key
  consumer must treat 404 as "absent-or-null", not "key does not exist".
- Dedicated alias routes: `/patient/configuration/defaultCountry` → `{"value":"GB"}`,
  `/patient/configuration/recaptcha/key` → `{"value":"6LfUbuor…"}`.
  `/patient/configuration/messages/en` is live and returns `{"messages":[]}`.
- Control: `/patient/configuration/system/zzz.not.a.real.key.zzz` → 404 with
  `content-type: text/vnd.a`, so 404 is a genuine "absent", not a catch-all. Do not
  discriminate on that odd content-type.
- `personal.device.family.to.model.mapping` also answers on `carelink.minimed.com` and is
  **identical to the EU body** — the vocabulary is global.
- Rejected grammars: no per-key form under `/patient/v2/`; no
  `/patient/configuration/public/<key>` on the patient host; `?countryCode=GB` on the
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
- **The EU host will happily serve US market config.** With `countryCode=US` the reply
  carries `region:"US"`, `mediaHost:https://carelink.minimed.com`, US state codes and US
  legal-document paths — all from `carelink.minimed.eu`. The host is not the region
  boundary; the parameter selects the market, the host only supplies the default.

### ⚠ `bgUnits` and `glucoseUnitsDefault` disagree in BE, ES and IT

| key | MMOL_L | MG_DL |
|---|---|---|
| `bgUnits` | GB IE NL NO SE DK FI ZA RU | US DE FR IT ES AT BE CH CL |
| `glucoseUnitsDefault` | BE CH DK FI GB IE NL NO RU SE ZA | AT CL DE ES FR IT US |

**BE, ES and IT report `MG_DL` for `bgUnits` but `MMOL_L` for
`glucoseUnitsDefault`.** Two keys, same country, different units. Reading one and not the
other mis-scales every value [source:
findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md].

### Other country-dependent keys

| key | varies |
|---|---|
| `mfa.status` | **`NO` = `REQUIRED`**; all 17 others `OPTIONAL` |
| `mfa.gracePeriod` | NL/NO 0 · DE/DK/ES/FI 2 · GB/IE/IT/CL/RU/SE/US/ZA 5 · AT/BE/CH/FR 7 |
| `mfa.maxAttempts` / `rememberPeriod` | NO 5 / 10; every other country 3 / 3 |
| `INSULIN_ASSESSMENT` report | **absent in FR, RU, US**; present in the other 15 |
| `dateOfBirthRequired` | **`false` only for RU**; `true` everywhere else |
| `stateCodes` | US only (state enumeration); `null` for all 17 others |
| `techHours` | 24/7 in GB, RU, CL only · US `7:00 am - 7:00 pm CST` · the rest weekday business hours |
| `carbDefaultUnit` / `carbohydrateUnitsDefault` | `EXCHANGES` for AT/ES/RU, `GRAMS` elsewhere |
| `defaultLanguage` / `languages` / `defaultCountryName` | 11 / 13 / 18 distinct values |
| `region` / `mediaHost` | **US → `US` + `carelink.minimed.com`; all 17 others → `OUS` + `carelink.minimed.eu`** |
| `pathDocs` | FR-only `ddms.certificationPdf`; US-only `marketingAuthTerms`, `privacyPractices`, `privacyStatement`, `termsOfUse` |

Constant across all 18 countries: `uploaderAllowed` = `true`, `smsSendingAllowed` = `true`,
`defaultDevice` = `"GM"`, `firstDayOfWeek` = `"Monday"`, `legalAge` = `18`,
`blePereodicDataEndpoint` = `https://clcloud.minimed.eu/connect/carepartner/v6/display/message`.
`cpMobileAppAvailable` is `false` for 16 countries and **`null` for GB and IE only**.

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
