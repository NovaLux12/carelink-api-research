# `/patient/v2/configuration/public` — the authoritative public config (2026-10-09)

**This is the single most valuable endpoint found in the whole research pass.**
Discovered by the Wayback agent as an archived URL, then verified live.

## The endpoint

```
GET https://carelink.minimed.eu/patient/v2/configuration/public
→ 200, application/json, gzip (6295 B compressed / 26692 B raw), UNAUTHENTICATED
```

Same host the bridge already talks to. No auth, no api-key. The bridge never
requests it.

**Parse gotcha:** the body is gzip and served without the client asking. A plain
`curl -o file` writes raw gzip bytes and every later `jq` call fails with
`utf-8 codec can't decode byte 0x8b`. Use `curl --compressed`, or
`gzip.decompress()` locally — don't re-request to work around it.

69 top-level keys. Archived captures run 2026-02-04 (18834 B) → 2026-09-26, so
the content grows; today is the largest seen.

## What it settles

### #81 — the `deviceFamily` vocabulary, authoritatively

`personal.device.family.to.model.mapping` is the complete map. **The complete
family list is:**

```
GM  BLE700  BLE720  BLE740  BLE770  BLE780  GST  SIMPLERA
SIMPLERACC  SIMPLERACCOLID  NMX7  CC840  CC880  NMX8  INSTINCT  EAGLE
```

And a second, independent key corroborates the marketing name:

```json
"system.settings.transfer.feature.config": {
  "device.mapping": { "BLE780": "780G", "CC880": "MiniMed™ Flex" }
}
```

**So `CC880` *is* the Minimed Flex family.** This validates the six model
prefixes added in PR #93 (MMT-8062/8063/8082-8085 all appear under `CC880`) and
simultaneously shows the `FLEX` family-substring test added alongside them is
guessing at a token the vendor does not appear to use.

Selected rows verbatim:

| family | models |
|---|---|
| `BLE780` | MMT-1884/1885/1886 + XCU/XCE/XCF/XCY clinical variants |
| `CC880` | MMT-8062, 8063, 8082, 8083, 8084, 8085, 8162XCF, 8172XCF, 8163XCF, 8173XCF, 8173XCC |
| `CC840` | MMT-8021, 8022, 8023 |
| `NMX7` / `NMX8` | MMT-1906-1909 / MMT-8162, 8163 |
| `EAGLE` | MMT-9015, 9017, 9115, 9117 |
| `SIMPLERACC` | MMT-8600, 8601, MMT5100, MMT-5100JC1/2/4, MMT-5101W1/2/4, MMT-5100JD4, MMT-5101P/M |
| `SIMPLERACCOLID` | MMT-8602 |
| `INSTINCT` | SKU-78893-01 … SKU-78968-01 (plus unprefixed duplicates) |

**`MMT-8600`/`MMT-8601` are NOT missing from Medtronic's tables** — the JS
bundle agent found them absent from the *portal bundle's* table, and they are
here under `SIMPLERACC`. Two different tables, both partial. Worth recording so
nobody concludes the portal table is authoritative.

**Trailing-whitespace trap:** several `SIMPLERA` entries are padded —
`"MMT-5100       "`, `"MMT-5100J      "`, `"MMT-5100CLXP   "`. Any exact-match
parser over this map breaks on them. The bridge's `normalise()` (uppercase +
strip non-alphanumerics) handles it; a naive `===` would not.

### #76 — logbook entry types (the ROADMAP's deferred `markers[]`)

`logbook.supported.entry.types` — 12 entries:

```
BLOOD_KETONES  SENSOR_INSERTION  SENSOR_REMOVAL  SENSOR_PHYSICAL_DISTURBANCE
ADHESIVE_AND_TAPE  MEDICATION  URINE_KETONES  CARBS  EXERCISE  HBA1C
INFUSION_SET_CHANGE  OTHER
```

Note `logbook.enabled = false` for the EU default and `logbook.entries.page.size = 30`.

### Also newly resolved

- **The retina service the JS-bundle agent could only see in pieces.**
  `retina.endpoints.config.personal.target_url` = `https://clcloud.minimed.eu`
  with `dashboard.base_uri = /connect/retina/v1/personalWebView`.
- **`csr.cumulus.periodic.data.endpoints`** — the CSR Cumulus namespace the
  archives also found, now with live values, including an AWS VPC-endpoint URL.
- **`csr.control.codes.settings`** — the device *control*-code vocabulary
  (`dpml`, `tup`, `lhpro`, `lghpro`, `vex`, `ssd`, `tcc`, `gstpro`, `gstrc`) with
  ranges. **This is NOT the NGP alarm-code set** — no N-codes. #84 stays open.
- **`mmm.data.api.url`** — a separate `dialog-lite/v1` service, never recorded.
- **`personal.patient.timeline.config.host`** — another undisclosed AWS service.

### Config-integrity notes (no credentials found)

- `nutrino.cc.*.security_headers."x-api-key"` is the literal placeholder
  `%#$^&#GFFG@#*%&#$` in both broker and metadata configs — **not a real key.**
  Distinct from the hardcoded bundle key in `SECURITY-FINDINGS.md`.
- `captcha.key` is a Google reCAPTCHA **site** key, which is public by design.
- `personal.mixpanel.analytics.settings.token` is a Mixpanel project token,
  also low-sensitivity but worth not republishing.
- `personal.third.party.apps` lists consent apps (GlookoXT, …).
- **`personal.session.timeout = 30`** — refresh-token lifetime is worth a look
  in November.

### Internal hostnames leaked in a public config

Two, both previously unrecorded:

- `praas.uri.path.reports.ping` = `https://iis.<internal-host>.corp:443/api/report/v2/ping`
- the CSR periodic-packet AWS VPC endpoint (`*.execute-api.eu-central-1.vpce.amazonaws.com`)

Neither is publicly reachable, per the recon notes. Recorded for completeness;
no probing done and none warranted.

### Redirect-scheme whitelist — relevant to the login SPOF

`personal.integrations.redirect.scheme.whitelist` = `about`, `minimed`,
`com.medtronic.wecare`, `be.aertsbert.wecaredev`, `emea.oscoe.wecaredev`,
`com.medtronic.diabetes.wecare.eu`, … and `system.auth0.url.whitelist` =
`minimed.com`, `minimed.eu`, `medtronic.com`, `medtronic.eu`.

Note `com.medtronic.carepartner:/sso` (the redirect the bridge relies on) is
**not** in the integrations whitelist — that whitelist governs deep links, not
the OAuth callback, so this is context rather than a contradiction. It does
independently corroborate that the bridge authenticates as the *Android app*
rather than as itself.

## What this does NOT answer

Still token-gated: the real shape of a `monitor/data` payload, whether
`deviceFamily` is spelled exactly as above on the wire, the NGP alarm codes
(#84), and which namespace returns real EU data (#74).