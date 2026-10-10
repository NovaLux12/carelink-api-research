# Lazy-chunk corpus (224 files) — what it did and did not add (2026-10-09)

The previous round's top recommendation was "fetch the 225 lazy chunks, it is
one `curl` pass". Done. **It was the wrong recommendation**, and the reason is
structural enough to be worth recording.

## The fetch

`hp-runtime.js` holds a 225-entry webpack chunk map, `{12:"cfb28faf…", …}`, and
chunks resolve against the portal root (`.p=""`), so the filenames are
`<id>.<hash>.js`.

**224 fetched, 4.4 MB.** One entry returned the SPA fallback.

> **Gotcha, same shape as a trap already hit twice today:** this portal returns
> **HTTP 200 with `text/html` (5518 B) for *every* path**, including
> `<id>.deadbeefdeadbeef.js`. Real chunks are `application/javascript`. Filtering
> on status code alone would have stored 225 copies of `index.html` and reported
> a clean sweep. Always discriminate on **content-type** against this host.

## The negative — chunks do not extend the API surface

| measure | `hp-main.js` alone | all 224 chunks |
|---|---|---|
| distinct hosts | 13 | **3** (`www.w3.org`, `www.highcharts.com`, `github.com`) |
| Medtronic hosts | 1 | **0** |
| distinct API path literals | 183 (`hcp/*` etc.) | **3** |
| `MMT-*` model codes | 80 | **3** |
| `deviceFamily`-style tokens | many | **0** |
| NGP `N\d\d` alarm codes | 0 | **0** |

**All API definitions live in the eagerly-loaded main bundle; the lazy chunks
are view/component code.** So the `hcp/*` map already extracted (183 paths) is
effectively complete, and the four endpoints with "zero call sites" are called
from code paths that resolve at runtime rather than as literals.

Do not re-run this. The remaining marginal value is below.

## What the chunks DID add

### Three new endpoint literals

```
POST /hcp/sso/auth/otc/send        (found by jsrecon too)
GET  hcp/countries/dialCodes
     hcp/patients/checkPhoneNumber
GET  /connect/retina/searchfilter
POST /connect/retina/searchfilter/feedback
```

`hcp/countries/dialCodes` and `hcp/patients/checkPhoneNumber` are new; the
`otc/send` one corroborates the earlier `hcp/patients/*otc-linking*` finding.

### 89 distinct field names at HTTP call-sites — the real value

This is schema data that grepping `main.js` for paths would not surface, because
it lives in the *feature* modules. Grouped by what they tell us:

**Logbook / markers** — the read side of the ROADMAP's deferred `markers[]`, and
the concrete field list that item was missing:

```
removalType  removalReason  adhesivetapeLocation  sensorInsertionLocation
sensorRemovalLocation  sensorPdLocation  timecapUnscrewed
timecapUnscrewed_additionalTime  timecapUnscrewed_minutesTime  notes  entryTs
```

**Device identity** — `deviceFamily` appears as a call-site field name,
independent corroboration of the field name (not its value) that #95 relies on.

**Insulin / therapy:** `tdd` `longActingInsulin` `doseFrequency`
`doseTwoUnitsPerDose1` `doseTwoUnitsPerDose2` `medicationDoseUnit`
`currentPreset` `blindedStatus` `glucoseManagementIndicator` `gmi`
`ageGroups` `weight` `weightUnit`

**Meal bolus wizard:** `breakfast` `lunch` `dinner` `snack`

**Auth / MFA:** `captcha` `captchaValue` `mfaRemembrancePeriod`
`mfaVerificationCodeExpiration` `personalCredentials` `personalPassword`
`oldPassword` `expireAllActiveSessions`

**Account linking:** `ssoLink` `isSendLinkCode` `linkingMethod` `phoneDetails`
`sendCC` `personalUsername` `personalUsername` `updatePatientEmail`

**Consent / data-sharing:** `consent` `accessDataEnabled` `accessDataFilter`
`dataSharingDisabled` `patientDataColumns` `therapyDataColumns`
`reportDataRange` `triageSettings`

### Also: `deviceFamily` confirms the *name*, not the *value*

The single most relevant confirmation: the portal calls a field `deviceFamily`.
It does not tell us what that field's *value* looks like on the wire — that still
needs a token. So **#81 stays open on the wire-shape question** exactly as
recorded, while the vocabulary half is now settled from the published config.

## Tooling note — jsrecon

Installed `jsrecon` 0.2.0 (tree-sitter-based, resolves strings split across `+`,
emits an OpenAPI skeleton). It found 6 endpoints over the corpus — fewer than raw
regex, because this Angular app composes URLs from **server-supplied config**
(`retina.endpoints.config.personal.target_url` + `dashboard.base_uri`) rather than
from literals. It is the right tool for apps that build URLs in code and the
wrong one for config-driven apps. Worth keeping for the patient-side surfaces.

## OpenAPI / source maps — both negative, both now closed

- **Source maps:** no `.map` file exists for any of the three eager bundles, and
  neither `main.js` nor `runtime.js` contains a `sourceMappingURL` comment. The
  standard "just fetch `<bundle>.js.map`" shortcut does not apply here.
- **Published API spec:** probed the conventional discovery set
  (`/swagger.json`, `/openapi.json`, `/api-docs`, `/v2|v3/api-docs`,
  `/swagger/v1/swagger.json`, `/.well-known/openapi.json`, `/api/schema`,
  `/api/v1/schema`, `/graphql`, `/graphiql`) on `carelink.minimed.eu`,
  `clcloud.minimed.eu` and `carelinkhp.minimed.eu`.
  - `carelink.minimed.eu` → Apache **404** on all 11 (196 B error page).
  - `clcloud.minimed.eu` → **403 `{"message":"Missing Authentication Token"}`** on
    all 11 — same PDE/cumulus auth wall as `/connect/pde/v3/*`. Note this is
    identical for a real path and a non-existent one, so it proves nothing about
    existence either way; it does mean there is no *unauthenticated* spec.
  - `carelinkhp.minimed.eu` → SPA HTML fallback on all 11.

So there is no published OpenAPI/Swagger document to parse. That closes the
"spec-driven discovery" avenue as a source for #76/#84.