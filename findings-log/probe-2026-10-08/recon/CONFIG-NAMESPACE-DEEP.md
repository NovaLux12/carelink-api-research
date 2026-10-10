# Config-namespace deep extension — 2026-10-10

Read-only, unauthenticated, GET-only follow-up to
`PUBLIC-CONFIG-FINDINGS.md` / `CROSS-REGION-CONFIG-FINDINGS.md` and
`recon/CONFIG-NAMESPACE.md`. All five targets probed.

**Request cap: 80. Used: 80/80. `deep-addendum.sh` stopped at the cap by design.**
≥2 s between consecutive requests to the same host (enforced per-host in
`deep-probe.sh`; the addendum process sleeps 3 s first so the gap survives the
process boundary). 6 hosts touched, 7 hosts attempted.

| | count |
|---|---|
| requests sent | **80** |
| 200 `application/json` | 45 |
| 404 | 17 |
| 401 (token-gated) | 2 |
| 400 (validation) | 4 |
| 403 / 405 / 502 / 503 | 4 |
| TCP connect failed | 2 |
| served gzip by the host | 29 |

Machine log: `deep-matrix.jsonl` (80 rows, one JSON object per request).
Raw bodies: `deep-bodies/` (`*.body` + the matching `*.hdr`).
Scripts: `deep-probe.sh` (rate limiter + cap + scrubber), `deep-run.sh`,
`deep-addendum.sh`.

---

## HEADLINE — the namespace IS enumerable per-key, on the *v1* path

The highest-value hypothesis in the brief was right, but the grammar is not the
one predicted. The patient host's per-key form is **`/patient/configuration/system/<flat.name>`** —
the *v1* path — not anything under `/patient/v2/`.

```
GET https://carelink.minimed.eu/patient/configuration/system/logbook.supported.entry.types
→ 200 application/json, 281 B (3470 B for the device map)
```

Every response is a Java-style config envelope:

```json
{ "value" : "<the config value, as a STRING>" }
```

For scalars the value is the scalar; **booleans arrive as the strings `"true"` /
`"false"`**, and objects/arrays arrive as a JSON document *serialised into the
string* — so a naive `resp.value === false` check silently fails on
`logbook.enabled`. Unwrap, then `JSON.parse` again:

```
mmm.data.api.url     → {"value": "https://0ptoikank6.../dialog-lite/v1/"}
logbook.enabled      → {"value": "false"}
csr.control.codes... → {"value": "{\n  \"predefined_control_codes\":[\n ..."}
```

**21 of 21 probed non-null keys returned a value byte-identical to the
corresponding subtree of the 69-key document.** This is a projection, not a
second source: `/patient/configuration/system/X` is the same data as
`X` inside `/patient/v2/configuration/public`, so there is no divergence to
reconcile — but there *is* now a 69-request enumeration path for the namespace,
which is what makes it enumerable at all.

`personal.device.family.to.model.mapping` also answers on
`carelink.minimed.com` (n=42) and is **identical to the EU body** — the device
vocabulary is global, as `05-public-config.check.sh` already pins.

### Which keys do NOT answer under the per-key form (24 probed, 3 absent)

| key | per-key result | why |
|---|---|---|
| `system.logbook.entry.validation.config` | **404** | value is `null` on EU — 2/2 null-valued keys 404 |
| `personal.retina.endpoint.config` | **404** | value is `null` on EU |
| `captcha` | **404** | served at a **dedicated route** instead |
| `default.country` | **404** | served at a **dedicated route** instead |

The null rule is confirmed twice (n=77, n=78 — both `null` in the document, both
404), so **`/patient/configuration/system/X` 404s for a null-valued key** rather
than returning `{"value": null}`. A per-key consumer must treat 404 as
"absent-or-null", not "key does not exist".

The two dedicated routes are real and both answer with the same envelope:

```
GET /patient/configuration/defaultCountry   → 200  {"value": "GB"}          (== default.country)
GET /patient/configuration/recaptcha/key    → 200  {"value": "6LfUbuor…"}    (== captcha.key)
```

`/patient/configuration/messages/en` also exists → `{"messages": []}` (n=41),
an i18n namespace that is live but empty.

**Control:** `/patient/configuration/system/zzz.not.a.real.key.zzz` → 404 with
`content-type: text/vnd.a`, so 404 is a genuine "absent", not a catch-all. Note
the odd content-type on the 404 — do not discriminate on it.

### Rejected grammars

| URL | result |
|---|---|
| `/patient/v2/configuration/public/<real.key>` (3 real keys) | **404** — no per-key form under v2 |
| `/patient/configuration/public/personal.crm.settings` | **404** — the HCP grammar does not exist on the patient host |
| `/patient/configuration/system/personal.crm.settings?countryCode=GB` | 200, **byte-identical to the no-param response** |

So the per-key namespace is addressable but **not country-parameterised**.

---

## TARGET 1 — `/patient/v2/` is wider than "configuration only"

`/patient/v2/configuration/` has exactly one member, `/public`, as
`CROSS-REGION-CONFIG-FINDINGS.md` already concluded — 6 further candidate
siblings all 404 (`system`, `defaultCountry`, `version`, `messages/en`,
`recaptcha/key`, plus `public/<key>`).

But **`/patient/v2/` itself is not configuration-only** — two previously
unrecorded members exist:

| URL | status | verdict |
|---|---|---|
| `/patient/v2/users/me` | **401** `{"error":{"type":"InvalidToken","group":"AUTH"}}` | **EXISTS**, token-gated |
| `/patient/v2/monitor/data` | **405** | **EXISTS**, POST-only |
| `/patient/v2/countries/settings` | 404 | absent |
| `/patient/v2/languages` | 404 | absent |

`/patient/v2/monitor/data` answering 405 rather than 404 is the same
"exists, POST-only" signature the HCP round used to prove existence without a
token, and it means the **v2 tree has a data plane**, not just a config plane.
Not previously recorded. Worth a token-gated follow-up in November.

---

## TARGET 3 — the country axis: `countryCode` is IGNORED by the config

`/patient/v2/configuration/public?countryCode=X` (GB/US/DE/FR):

- **69 keys in, 70 keys out.** The parameter is accepted and **echoed verbatim as
  a new top-level `"countryCode"` key** — and **nothing else changes**.
- `default.country` stays `GB` even when `countryCode=US` is sent to the EU host.
  So the document is **region-parameterised by host, not by parameter**.

Two consequences:

1. **`hurl/05-public-config.check.sh`'s `check "config key count (was 69)"` will
   FAIL if anyone ever runs it with a `countryCode` param** — it would see 70.
   The assertion is correct as written (bare URL); worth a comment so a future
   run does not "fix" a non-bug.
2. Anyone assuming the 69-key doc is the per-country source is wrong. **The
   per-country source is `/patient/countries/settings?countryCode=…`** — which is
   what the rest of this section maps.

### The per-country document — 18 countries, 35 keys

`GET /patient/countries/settings?countryCode=XX` → 200 `application/json`,
gzip. No param → **400** with a JSR-303 body
(`"field":"getCountryConfiguration.arg0","message":"must not be null"`).
Bogus `ZZ` → **400** `"Error! Country:ZZ Not Supported"`. Both are clean,
distinct error shapes — the country code is genuinely validated.

Country set drawn from the config's own lists
(`personal.common.core.reporting.enabled.countries`,
`personal.countries.certification.enabled`, `personal.inpen.supported.countries`,
`connect.countriesWithConnect`) plus US/RU/CL/ZA for contrast:

GB US DE FR IT ES NL SE NO DK FI CH AT BE IE ZA CL RU

#### Medically-interesting variation

| key | varies | detail |
|---|---|---|
| **`mfa.status`** | **YES** | **`NO` = `REQUIRED`; all 17 others `OPTIONAL`** |
| `mfa.gracePeriod` | YES | NL **0**, NO **0**, DE/DK/ES/FI **2**, GB/IE/IT/CL/RU/SE/US/ZA **5**, AT/BE/CH **7**, FR **7** |
| `mfa.maxAttempts` / `rememberPeriod` | YES | NO **5 / 10**; every other country **3 / 3** |
| **`bgUnits`** | **YES** | MMOL_L: GB IE NL NO SE DK FI ZA RU · MG_DL: US DE FR IT ES AT BE CH CL |
| **`glucoseUnitsDefault`** | **YES** | MMOL_L: BE CH DK FI GB IE NL NO RU SE ZA · MG_DL: AT CL DE ES FR IT US |
| **`INSULIN_ASSESSMENT` report** | **YES** | **absent in FR, RU, US**; present in the other 15 |
| `dateOfBirthRequired` | YES | **`false` only for RU**; `true` everywhere else |
| `stateCodes` | YES | US only (state enumeration); `null` for all 17 others |
| `techHours` | YES | **24/7: GB, RU, CL only** · US `7:00 am - 7:00 pm CST` · the rest weekday business hours |
| `techSupport` / `techDays` | YES | 18 different phone numbers; 24/7 days only GB/RU/CL, `Su-Sa` CL |
| `carbDefaultUnit` / `carbohydrateUnitsDefault` | YES | `EXCHANGES` for AT/ES/RU, `GRAMS` elsewhere |
| `defaultLanguage` / `languages` / `defaultCountryName` | YES | 11 / 13 / 18 distinct values |
| `region` / `mediaHost` | YES | **US → `US` + `carelink.minimed.com`; all 17 others → `OUS` + `carelink.minimed.eu`** |
| `pathDocs` | YES | FR-only `ddms.certificationPdf`; US-only `marketingAuthTerms`, `privacyPractices`, `privacyStatement`, `termsOfUse` |

**Constant across all 18 countries** (no variation at all):
`uploaderAllowed` = `true`, `smsSendingAllowed` = `true`,
`defaultDevice` = `"GM"`, `firstDayOfWeek` = `"Monday"`, `legalAge` = `18`,
`blePereodicDataEndpoint` = `https://clcloud.minimed.eu/connect/carepartner/v6/display/message`.
`cpMobileAppAvailable` is `false` for 16 countries and **`null` for GB and IE
only** — the one country-dependent oddity in an otherwise flat field.

**The EU host will happily serve US market config.** With `countryCode=US` the
reply carries `region:"US"`, `mediaHost:https://carelink.minimed.com`, US state
codes and US legal-document paths — all from `carelink.minimed.eu`. The host is
not the region boundary; the parameter selects the market, the host only
supplies the default.

**Report availability matrix** (10-11 reports per country):

| cc | ADHER | ASSESS | BOLUS_W | DAILY | DASH | DEV_SET | EPISODE | LOGBOOK | OVERVIEW | WEEKLY | INSULIN_ASSESS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FR | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | **–** |
| RU | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | **–** |
| US | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | **–** |
| *other 15* | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y |

Full vocabulary: `ADHERENCE, ASSESSMENT_AND_PROGRESS,
BOLUS_WIZARD_FOOD_BOLUS, DAILY_DETAILS, DASHBOARD, DEVICE_SETTINGS,
EPISODE_SUMMARY, LOGBOOK, OVERVIEW, WEEKLY_REVIEW, INSULIN_ASSESSMENT`.

This closes the loop on the earlier `personal.data.csv.export.enable` region
finding: **CSV export is enabled per-region, but the *report types* available
inside it are per-country.**

---

## TARGET 4 — `mfa`, `tech*` and `support` keys

- **`/patient/countries/mfaStatusForCountry?countryCode=GB` → 200, 8 B, a bare
  JSON string**: `OPTIONAL`. A second, unauthenticated per-country MFA oracle,
  independent of the country-settings blob. Never previously probed.
- **`/patient/countries/mfaGracePeriod?countryCode=GB` → 401
  `{"error":{"type":"InvalidToken","group":"AUTH"}}`.** So the MFA *status* is
  public but the MFA *grace period* is token-gated — and yet the grace period is
  published anyway inside the public `/patient/countries/settings` document
  (matrix above). A gated endpoint whose value is obtainable unauthenticated from
  a sibling is a finding about the gate, not about the value.
- `/patient/countries/account/types?countryCode=GB` → 400
  `"field":"getSupportedAccountTypes.arg0","message":"must not be null"`. The
  endpoint exists but wants a *different* argument name — the repo's
  `extraFields=stateCodes` note is the same shape of discovery.
- `/patient/countries/mfaStatusForCountry` (bare) → 400, `arg0 must not be null`.

The `tech*`/`support` keys are all inside the country document and are fully
mapped in the table above. The operationally interesting row for a UK/EU user of
this bridge: **GB is one of only three countries with 24/7 phone support** (with
RU and CL) — the other 15 are weekday business hours, and NL's `techHours` is
written `8.30 - 17.00` (dots, not colons) so a strict `HH:mm` parser breaks on it.

---

## TARGET 5 — no fourth deployment found

Six hosts already named in existing findings, probed with the same path:

| host | status | content-type | verdict |
|---|---|---|---|
| `carelink-trials-next.minimed.com` | 503 | text/html | maintenance page — not a config host |
| `carelink-temptrials.minimed.com` | **000** | — | TCP connect failed |
| `clcloud-trials.minimed.com` | 403 | application/json | `{"message":"Missing Authentication Token"}` — API GW, route absent |
| `commoncore-trials.minimed.com` | 502 | text/html | backend down |
| `carelink.medtronic.eu` | **200** | **text/html** | **the 5518-byte SPA — identical md5 to the `carelinkhp` trap page** |
| `carelinkhp-trials.minimed.com` | **000** | — | TCP connect failed |

**No `.eu` counterpart to `carelink-trials` exists in any recorded enumeration.**
Every `*trials*` host in `names-all.txt`, `names-eu.txt`, `names-com.txt`,
`prod-names.txt`, `scope-prod.txt` and the crt.sh/disc corpora is a `.com` host —
16 of them, all `.com`, zero `.eu`. So the answer to "is there a `.eu` trials
deployment" is a recorded-evidence **no**, obtained with zero DNS and zero
requests, which is the honest form of that answer given the no-DNS-sweep rule.

**The 5518-byte SPA trap is wider than recorded.** `carelink.medtronic.eu`
returns a body whose md5 (`6aedf6c4004fbb29a298bc62128480be`) is identical to
`recon/cl-mdt-com.html` and `security/hp-index.html`. So the `.medtronic.eu`
shadow deployment is the same SPA as `carelinkhp.minimed.eu`, and **any
"does host X serve the config" test that keys on status 200 will report a false
positive on it** — discriminate on content-type or on the exact 5518-byte size,
as before. Note this host serves it gzipped (2125 B on the wire), so the
byte-size check must be made after decompression.

---

## NEW / previously unrecorded items

1. **The per-key namespace `/patient/configuration/system/<flat.name>`** — 21/21
   values verified identical to the document, plus the envelope shape, the
   boolean-as-string trap, the null→404 rule, and the two dedicated alias routes
   (`/patient/configuration/defaultCountry`, `/patient/configuration/recaptcha/key`).
2. **`/patient/v2/users/me` (401) and `/patient/v2/monitor/data` (405)** — the v2
   tree has a token-gated data plane, not just the config document.
3. **`?countryCode=` on the public config echoes a 70th key and is otherwise
   ignored** — and it breaks the pinned "69 keys" assertion if used.
4. **`/patient/countries/mfaStatusForCountry`** — an unauthenticated,
   bare-scalar per-country MFA oracle.
5. **`/patient/countries/mfaGracePeriod` is 401-gated** while its value ships
   publicly inside `/patient/countries/settings`.
6. **`INSULIN_ASSESSMENT` is unavailable in FR, RU and US**; `dateOfBirthRequired`
   is false only in RU; `stateCodes` is US-only; FR-only `certification.pdf`.
7. **`bgUnits`/`glucoseUnitsDefault` split MG_DL vs MMOL_L by country** — and they
   do not agree with each other. **BE and CH report `MG_DL` for `bgUnits` but
   `MMOL_L` for `glucoseUnitsDefault`.** Two keys, same country, different units.
   Any bridge that reads one and not the other will mis-scale.
8. **Live drift in the country lists (2026-10-09 → 2026-10-10):**
   `personal.common.core.reporting.enabled.countries` grew from **17 to 26
   countries** (added AU, HR, CZ, EG, GE, IL, PL, RO, RS, SK, SI, AE) and
   `personal.inpen.supported.countries` grew in step (AE, AU, CZ, EG added).
   A rollout is in progress *right now*.
9. **The document is growing:** 20420 B compact on 10-09 → 20586 B compact on
   10-10 (6359 B on the wire). Same 69-key set.
10. **`/patient/configuration/messages/en`** is live and returns
    `{"messages": []}`.
11. **The 5518-byte SPA trap generalises to `carelink.medtronic.eu`** (identical
    md5, served gzipped).

### Measurement artifact — do not cite it

The `deep-matrix.jsonl` field `"x-api-key":"len=10"` on the six config responses
is the length of the literal string `[REDACTED]`, **not** of a key. The scrubber
runs before the length probe in `deep-probe.sh`, so this pass measured its own
placeholder. The authoritative EU figure is length 17, pinned as a placeholder by
`hurl/05-public-config.check.sh`. Further scrubbing is in place so a re-run
cannot repeat the mistake; the length column should simply be ignored.

Also: `/patient/configuration/system/nutrino.cc.{broker,metadata}.service.config`
appear as "CHANGED" against the 10-09 capture if you diff naively — that is this
pass's own redaction, and **ignoring `security_headers` they are identical**. No
vendor drift there.

---

## Gzip / RFC 9110 — recorded precisely

29 of 80 responses came back with `Content-Encoding: gzip`. This pass used
`curl --compressed`, which *does* advertise `Accept-Encoding`, so **it does not
re-verify the unconditional-gzip behaviour** pinned by `hurl/05` (which tested
`identity`, `gzip` and `deflate` explicitly). What this pass adds is that gzip is
applied broadly — to the config document, to the five large per-key bodies, to
all 18 country documents and to the `carelink.medtronic.eu` SPA — and that
**`carelink.medtronic.eu` serves its 5518-byte SPA gzipped**, so the byte-size
discriminator has to be applied post-decompression.

---

## Negatives, stated plainly

- **`/patient/v2/configuration/` has no siblings.** Six derived candidates 404,
  including a real flat key under `/public/`. The namespace is closed there.
- **`countryCode` does not parameterise the 69-key document.** Four countries
  tested; only the echoed key changed.
- **No fourth deployment.** Two hosts refused TCP, one is a 503 page, one a 502,
  one a 403 JSON API-GW error, one is the SPA trap.
- **No per-key form exists under `/patient/v2/`**, and the HCP-style
  `/patient/configuration/public/<key>` grammar does not exist on the patient host.
- 3 of 24 per-key keys 404, all explained (2 null-valued, 2 on dedicated routes).
- `account/types` was not resolved — it exists but wants an argument this pass
  did not guess, and guessing argument names is out of scope.

## Credential hygiene

**No credential was written to any file by this pass.** Every `x-api-key`
occurrence in every saved body — both the flat form inside the 69-key document
and the escaped form inside the per-key `{"value": "…"}` envelopes — was replaced
with `[REDACTED]` before the body was written. Verified after the fact: zero
occurrences of any key value remain anywhere under `deep-bodies/`
(`grep -rl GFFG deep-bodies/` → no files; every remaining `x-api-key` occurrence
reads `[REDACTED]`). The escaped-envelope form initially defeated a plain `sed`
and was caught and fixed mid-pass; `deep-probe.sh`'s `scrub()` now handles both
shapes and asserts on failure. Key *material* appears nowhere in this document.

The only long token left in the saved bodies is the reCAPTCHA **site** key, which
is public by design and already recorded as such in `PUBLIC-CONFIG-FINDINGS.md`.

No git repo or worktree was read for writing or touched by this pass; everything
was written under `research/probe-2026-10-08/recon/`, which is gitignored.


> **CORRECTION (2026-10-11, verified by set arithmetic on the source table).**
> An earlier version of this note named **BE, ES and IT** as the countries where
> `bgUnits` and `glucoseUnitsDefault` disagree. That is wrong. Reading the two
> rows above:
>
> | key | MG_DL | MMOL_L |
> |---|---|---|
> | `bgUnits` | AT BE CH CL DE ES FR IT US | DK FI GB IE NL NO RU SE ZA |
> | `glucoseUnitsDefault` | AT CL DE ES FR IT US | **BE CH** DK FI GB IE NL NO RU SE ZA |
>
> `ES` and `IT` are `MG_DL` in **both** keys — they agree. The only
> disagreements are **BE and CH**, and **CH was missing from the original claim
> entirely** while two agreeing countries were named.
>
> The prose in this file carried the same error as its own table, so this was
> faithfully propagated into five pages of the public repo. Corrected everywhere.
> The magnitude is not cosmetic: `MG_DL` vs `MMOL_L` is roughly 18×.
