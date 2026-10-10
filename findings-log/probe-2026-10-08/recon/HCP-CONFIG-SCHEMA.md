# `carelinkhp.minimed.eu/hcp/configuration/*` — HCP config schema (2026-10-09)

**Target of this round:** the portal's own `/configuration/` family, which had
never been read, hunting specifically for the **NGP alarm-code vocabulary**
(issue #84) and logbook marker types (issue #76).

**Headline: the NGP vocabulary is not published here.** 28 distinct
alarm/notification/severity key names were probed; **all 404**, and the
methodology controls prove a 404 on this namespace is a *true absence* rather
than a spelling artifact. This is a real, defensible negative — see §6.

---

## 1. Method, cap and compliance

| Constraint | How it was honoured |
|---|---|
| **GET only** | Every request was `curl -sS -o … -D …`. No `-X`, no POST/PUT/DELETE, no body. |
| **No auth** | No `Authorization`, no `Cookie`, no api-key header. Unauthenticated throughout. |
| **Cap 60** | **42 requests used in this round** (R2), enforced in `recon/hcp2probe.sh`. R1 (a prior pass on the same host, same constraints) used 45. **Combined 87 requests**, 73 distinct paths. |
| **≥2s between requests to same host** | Enforced per-host in the harness (`last_hit[]` assoc array). Actual observed spacing ≥2s. |
| **Stay on `/configuration/`** | All 87 URLs are under `/hcp/configuration/`. Zero requests to `/patients/`, `/user/`, `/clinics/`, or any other namespace. Nothing that could return patient data was requested. |
| **No credential in any file** | See §9. The bundle's hardcoded `x-api-key` was never read into, copied to, or echoed by this pass. It does not appear in this file. The `security_headers` object in the nutrino configs is reproduced in §5 with its value redacted. |
| **No git / no worktree** | Wrote only under `research/probe-2026-10-08/recon/`. No git command was run against the repo, no branch/stash/worktree touched. |
| **Discriminate on content-type** | The host returns **HTTP 200 + `text/html` + exactly 5518 bytes** for every unknown path. Verdicts are content-type-derived; the 5518-byte signature is treated as a fallback, never a hit. |

### Files written by this pass (all in `recon/`, nothing else touched)

```
hcp2probe.sh     round-2 harness — global counter, ≥2s per-host sleep,
                 content-type verdicts, 401/404 existence oracle
phase-f.sh       controls: case-sensitivity, header-value whitelist, countryCode
phase-g.sh       #84 hunt — "notification" vocabulary (the word Medtronic uses)
phase-h.sh       severity mapping + #76 logbook depth + namespace-alias controls
phase-i.sh       countryCode mechanism control + generic vocabulary + 401 shapes
hcp2-matrix.jsonl  42 result records
hcp2bodies/        42 header+body pairs
```

---

## 2. Base URL and the header contract  ← answers targets 1 and 3

```
BASE = https://carelinkhp.minimed.eu
PREFIX = /hcp/configuration/public/<key>
```

The `hcp/` prefix is **not** guessed — it is the literal the bundle's constants
table binds (`hcp/configuration/public/…`, 15 keys; `JS-API-SURFACE.md` §2.1,
§7.15). All paths are relative to the portal origin; no separate API host.

### The one load-bearing header is `X-System-ID`, and its **value** is validated

| `X-System-ID` sent | Result on a known-good key |
|---|---|
| *(absent)* | **412**, 0 bytes |
| *(empty — `X-System-ID;`)* | **412**, 0 bytes |
| `NotARealClient` | **412**, 0 bytes |
| `proweb` (lower-case) | **200**, 778 B JSON |
| `ProWeb` | **200**, 778 B JSON |

Three things follow, and they are the useful output of this section:

1. **The header is mandatory.** Without it the request is rejected at the
   edge (`x-cache: Error from cloudfront`, `x-amz-cf-pop: LHR5-P7` — CloudFront
   in front of an API Gateway) with **412**, not 401 and not 404. The 412 is
   emitted before routing, which is why the brief's "412 on everything" is not
   seen — only the `public/` subtree is behind this check.
2. **The value is checked against a vendor whitelist.** An invented value is
   rejected exactly like a missing one. So this is a **client-identity
   selector the vendor enumerates**, not a routing hint. That is the honest
   characterisation: I established which header the real client sends, and did
   not attempt anything further.
3. **The value comparison is case-insensitive** (`proweb` works) even though
   the **key namespace is case-sensitive** (§4). Minor robustness note, not a
   vulnerability — no access control depends on it.

### `Accept` is not load-bearing

| Headers | Result |
|---|---|
| `X-System-ID` only, no `Accept` | **200**, 226 B — byte-identical to the full-header response |
| `Accept: application/json` only | **412** (header check fires first) |
| Full default set (`User-Agent`, `Accept: application/json, text/plain, */*`, `X-System-ID`) | **200** |

`Accept` changes nothing about status or body. It is not worth recording in a
client implementation; `X-System-ID: ProWeb` is the whole contract.

---

## 3. The existence oracle: 401 ≠ 404

This is what makes the negative in §6 trustworthy, and it is the most reusable
thing in this document.

| Response | Meaning on `…/configuration/public/<key>` |
|---|---|
| `200` + `application/json` | key exists, published unauthenticated |
| **`401` + `application/json` + `{"error":{"type":"InvalidToken","group":"AUTH"}}`** | **key exists but is token-gated** |
| **`404`, 0 bytes** | **key does not exist** |
| `412`, 0 bytes | header check failed (see §2) |
| `405` | key exists but is POST-only |
| `200` + `text/html` + 5518 B | **SPA fallback — means nothing about existence** |

Verified with a positive control: `…/public/personal/media/config/eu` → **401**
(key exists, gated) versus `…/public/personal/media/config` → **404** and
`…/public/zzz.this.does.not.exist.zzz` → **404**. So existence is resolvable
without authentication; **content** is not.

Applied to the non-public namespace: `application`, `productContext`, `user`
→ **405** (POST-only, exist); `appContext`, `access/config`, `whitelisted`
→ **401** (exist, gated). The routing is real on both subtrees — only the
bundle root falls back to HTML.

---

## 4. Methodology control: the namespace is **case-sensitive**

```
GET …/public/CSU.CONTROL.CODES.SETTINGS     (X-System-ID: ProWeb)
→ 404, 0 bytes
```

`cua.control.codes.settings` returns 200; its upper-case spelling 404s. **The API
is case-sensitive, so a 404 on a lower-case spelling is a true absence.**

Without this control the 404s would prove nothing — a wrongly-cased guess and a
genuinely absent key are indistinguishable. This is the single control that
converts §6 from a guess into a result. (Applied to `hp-main.js` the same rule
holds and is already documented in `JS-API-SURFACE.md` §8: `N\d\d`, `ALARM`,
`alarmCode`, `stop_using_pump`, `stopUsingPump` all score **0 case-sensitive**
hits, so the apparent `ngp`/`guardian` matches are zxcvbn dictionary noise.)

---

## 5. Full request table

All 87 requests, both rounds. R1 = prior pass on this host; R2 = this pass.

| Rnd | URL | Headers sent | Status | Content-type | Bytes | Verdict |
|---|---|---|---|---|---|---|
| R1 | `/` | — | 200 | text/html; charset=UTF-8 | 5518 | spa-fallback |
| R1 | `/hcp/configuration/public/system.logbook.entry.validation.config` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/cua.alarm.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/personal/media/config/` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/cua.control.codes.settings` | — | 412 | — | 0 | header rejected |
| R1 | `/hcp/configuration/public/pow.crm.settings` | X-System-ID: ProWeb | 200 | application/json | 96 | **JSON** |
| R1 | `/hcp/configuration/public/csr.alarm.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/personal/media/config/eu` | X-System-ID: ProWeb | 401 | application/json | 48 | EXISTS (token-gated) |
| R1 | `/hcp/configuration/public/logbook.supported.entry.types` | — | 412 | — | 0 | header rejected |
| R1 | `/hcp/configuration/public/cua.crm.settings` | X-System-ID: ProWeb | 200 | application/json | 104 | **JSON** |
| R1 | `/hcp/configuration/public/pow.alarm.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/csr.logbook.entry.validation.config` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/cua.control.codes.settings` | X-System-ID: ProWeb | 200 | application/json | 778 | **JSON** |
| R1 | `/hcp/configuration/public/hcp.banner.notifications` | X-System-ID: ProWeb | 200 | application/json | 219 | **JSON** |
| R1 | `/hcp/configuration/public/system.alarm.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/cua.logbook.entry.validation.config` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/logbook.supported.entry.types` | X-System-ID: ProWeb | 200 | application/json | 226 | **JSON** |
| R1 | `/hcp/configuration/public/pow.follow.up.settings` | X-System-ID: ProWeb | 200 | application/json | 612 | **JSON** |
| R1 | `/hcp/configuration/public/hcp.alarm.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/application` | X-System-ID: ProWeb | 405 | — | 0 | exists, POST-only |
| R1 | `/hcp/configuration/public/zzz.this.does.not.exist.zzz` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/pow.common.core.report.generation` | X-System-ID: ProWeb | 200 | application/json | 9863 | **JSON** |
| R1 | `/hcp/configuration/public/alarm.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/appContext` | X-System-ID: ProWeb | 401 | application/json | 48 | EXISTS (token-gated) |
| R1 | `/hcp/configuration/public/pow.country.media.groups` | X-System-ID: ProWeb | 200 | application/json | 768 | **JSON** |
| R1 | `/hcp/configuration/public/cua.error.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/productContext` | X-System-ID: ProWeb | 405 | — | 0 | exists, POST-only |
| R1 | `/hcp/configuration/public/pow.invite.to.personal.uri` | X-System-ID: ProWeb | 200 | application/json | 27 | **JSON** |
| R1 | `/hcp/configuration/public/cua.control.alarm.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/user` | X-System-ID: ProWeb | 405 | — | 0 | exists, POST-only |
| R1 | `/hcp/configuration/public/personal/media/config` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/system.pump.alarm.codes.config` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/access/config` | X-System-ID: ProWeb | 401 | application/json | 48 | EXISTS (token-gated) |
| R1 | `/hcp/configuration/public/cms-config.json` | X-System-ID: ProWeb | 200 | application/json | 2 | **JSON** |
| R1 | `/hcp/configuration/public/logbook.alarm.codes` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/whitelisted` | X-System-ID: ProWeb | 401 | application/json | 48 | EXISTS (token-gated) |
| R1 | `/hcp/configuration/public/pow.nutrino.cc.broker.service.config` | X-System-ID: ProWeb | 200 | application/json | 309 | **JSON** |
| R1 | `/hcp/configuration/public/ngp.alarm.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/logbook.supported.entry.types` | X-System-ID: | 412 | — | 0 | header rejected |
| R1 | `/hcp/configuration/public/pow.nutrino.cc.metadata.service.config` | X-System-ID: ProWeb | 200 | application/json | 288 | **JSON** |
| R1 | `/hcp/configuration/public/cua.ngp.alarm.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/logbook.supported.entry.types` | -H X-System-ID: ProWeb | 200 | application/json | 226 | **JSON** |
| R1 | `/hcp/configuration/public/user-identifier-settings?countryCode=EU` | X-System-ID: ProWeb | 200 | application/json | 423 | **JSON** |
| R1 | `/hcp/configuration/public/system.ngp.alarm.codes.config` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R1 | `/hcp/configuration/public/system.error.codes.config` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/CSU.CONTROL.CODES.SETTINGS` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.control.codes.settings` | X-System-ID: NotARealClient | 412 | — | 0 | header rejected |
| R2 | `/hcp/configuration/public/cua.control.codes.settings` | X-System-ID; | 412 | — | 0 | header rejected |
| R2 | `/hcp/configuration/public/cua.control.codes.settings` | X-System-ID: proweb | 200 | application/json | 778 | **JSON** |
| R2 | `/hcp/configuration/public/cua.control.codes.settings?countryCode=US` | X-System-ID: ProWeb | 200 | application/json | 778 | **JSON** |
| R2 | `/hcp/configuration/public/cua.control.codes.settings?countryCode=EU` | X-System-ID: ProWeb | 200 | application/json | 778 | **JSON** |
| R2 | `/hcp/configuration/public/cua.notification.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/notification.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/csr.notification.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/system.notification.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/personal.notification.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.notifications.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.alert.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/alert.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.alerts.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.status.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.notify.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.ngp.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/ngp.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.ngp.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.control.codes.severity.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.severity.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/ngp.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.ngp.control.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.control.codes.settings.severity` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.alarm.codes.severity.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/system.logbook.entry.validation.config?countryCode=EU` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/logbook.entry.validation.config` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.logbook.entry.validation.config?countryCode=EU` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/logbook.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.logbook.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/logbook.marker.types` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/hcp.control.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/hcp.logbook.supported.entry.types` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/csr.logbook.supported.entry.types` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/user-identifier-settings?countryCode=US` | X-System-ID: ProWeb | 200 | application/json | 381 | **JSON** |
| R2 | `/hcp/configuration/public/user-identifier-settings?countryCode=DE` | X-System-ID: ProWeb | 200 | application/json | 423 | **JSON** |
| R2 | `/hcp/configuration/public/codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/cua.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/control.codes.settings` | X-System-ID: ProWeb | 404 | — | 0 | absent |
| R2 | `/hcp/configuration/public/personal/media/config/en` | X-System-ID: ProWeb | 401 | application/json | 48 | EXISTS (token-gated) |
| R2 | `/hcp/configuration/public/personal/media/config` | X-System-ID: ProWeb | 404 | — | 0 | absent |

---

## 6. Verbatim JSON — everything that answered

23 of 87 requests returned real JSON across 13 distinct keys. Grouped by what
they settle.

### 6.1 `cua.control.codes.settings` — the HCP twin of `csr.control.codes.settings`

`GET …/public/cua.control.codes.settings` → 200, 778 B. **Identical for
`?countryCode=US`, `=EU`, and no param** (778 B each) — this key is global, not
market-varying.

```json
{
  "predefined_control_codes_regexp": "(dpml:[0-3])|(tcc:[1-7])|(tup:((?i)TUP|LTU|DTU|BGM|GST|NOGSTU|NONE))|(lhpro:\\d+)|(lghpro:\\d+)|(vex:\\d+)|(ssd:(t|f))",
  "custom_control_codes_regexp": "(gstpro:\\d+)|(gstrc:(t|f))",
  "expiration_period_settings": {
    "DEFAULT": { "min": 1, "max": 30, "value": 3 },
    "tcc":     { "min": 1, "max": 30, "value": 1 }
  },
  "ranges": {
    "dpml":   { "min": 0, "max": 3 },
    "tcc":    { "min": 1, "max": 7 },
    "lhpro":  { "min": 0, "max": 4294967295 },
    "lghpro": { "min": 0, "max": 4294967295 },
    "vex":    { "min": 0, "max": 100 },
    "gstpro": { "min": 0, "max": 9223372036854775807 }
  }
}
```

**No N-codes. No severity vocabulary. This is the device *control* vocabulary
(`dpml`, `tcc`, `tup`, `lhpro`, `lghpro`, `vex`, `ssd`, `gstpro`, `gstrc`) and it
is structurally the same vocabulary the patient config publishes as
`csr.control.codes.settings`.** It says nothing about alarms.

**New finding — the two surfaces are NOT schema-identical.** Diffing the HCP
body against the patient-side `csr.control.codes.settings` (already on disk at
`hcpbodies/C1_patient-config.json`) exposes three divergences that matter to any
client written against one and pointed at the other:

| Divergence | HCP (`cua.*`) | Patient (`csr.*`) |
|---|---|---|
| `predefined_control_codes` array | **absent** | present: `["dpml","tup","lhpro","lghpro","vex","ssd","tcc"]` |
| `lhpro`/`lghpro` max | `4294967295` | `4292967295` |
| `expiration_period_settings` default key | `"DEFAULT"` (upper-case) | `"default"` (lower-case) |

The second row is almost certainly a **typo in the patient config** —
`4292967295` is not a round number, `4294967295` is `2³²−1`, the correct uint32
max, and the same value appears twice more in the same object. Worth recording
so nobody pins a range check to the wrong constant. The first and third are
straightforward key-presence differences that will produce `undefined` /
`undefined` reads.

### 6.2 `logbook.supported.entry.types` → issue **#76**

`GET …/public/logbook.supported.entry.types` → 200, 226 B.

```json
[
  "BLOOD_KETONES",
  "SENSOR_INSERTION",
  "SENSOR_REMOVAL",
  "SENSOR_PHYSICAL_DISTURBANCE",
  "ADHESIVE_AND_TAPE",
  "MEDICATION",
  "URINE_KETONES",
  "CARBS",
  "EXERCISE",
  "HBA1C",
  "INFUSION_SET_CHANGE",
  "OTHER"
]
```

**This is byte-identical, list-for-list, to the patient-side
`logbook.supported.entry.types` in `/patient/v2/configuration/public`.** I
asserted equality programmatically (`hcp == patient → True`, 12 entries). That
is worth something for #76: the list is no longer attested by a *single* source.
It is now confirmed on **two independently-served, independently-versioned**
config surfaces — the clinician portal and the patient cloud — which is a
meaningfully stronger basis for shipping the ROADMAP's deferred `markers[]`
vocabulary than one endpoint's word for it.

Note this key is **unprefixed** yet served on both surfaces, i.e. unprefixed
means "shared", not "patient".

### 6.3 `user-identifier-settings?countryCode=…` — the countryCode mechanism works

The only `public/*` key known to take a query parameter, and it genuinely
varies by market — which proves `countryCode` is a live parameter and therefore
that the control-codes key's *ignoring* of it (§6.1) is a property of that key,
not a broken probe.

`?countryCode=EU` and `?countryCode=DE` → 423 B, identical:

```json
{
  "regex" : "^[\\p{L}\\d\\s\\+\\.,:;()/#'−-]{1,20}$",
  "fieldName" : "user.identifier.field.default",
  "userIdentifierEnable" : true,
  "isUserIdentifierEnable" : true,
  "maxSize" : 20,
  "error" : "user.identifier.field.error.default",
  "errorNotUnique" : "error.user.identifier.not.unique.ous",
  "validateSpecialChars" : true,
  "userIdentifierPlaceholder" : "clinic.users.new.user.confirm.uid.placeholder.ous"
}
```

`?countryCode=US` → 381 B, materially different — US identifiers are a bare
10-digit phone number, EU identifiers a 20-char general Unicode class:

```json
{
  "regex" : "^\\d{10}$",
  "fieldName" : "user.identifier.field.us",
  "userIdentifierEnable" : true,
  "isUserIdentifierEnable" : true,
  "maxSize" : 10,
  "error" : "user.identifier.field.error.us",
  "errorNotUnique" : "error.user.identifier.not.unique.us",
  "validateSpecialChars" : false,
  "userIdentifierPlaceholder" : "clinic.users.new.user.confirm.uid.placeholder.us"
}
```

### 6.4 The remaining JSON keys (all small, none bearing on #84/#76)

- **`pow.crm.settings`** → `{"base.uri":"https://carelink.medtronic.eu/crm","product":"pow","version":"4.5"}`
- **`cua.crm.settings`** → same shape, `"base.uri":"https://carelink-support.medtronic.eu/crm"`. This is the **CUA (support) vs POW (clinic) CRM split** the bundle switches between at runtime (`JS-API-SURFACE.md` §7.15) — now confirmed on the wire, and it discloses a second Medtronic host, `carelink-support.medtronic.eu`, not previously recorded on the HCP surface.
- **`hcp.banner.notifications`** → `bannerEnabled:false`, `shortTimeFormat:"h:mm A"`, `timezone:"PT"`, plus `displayStartDate` / `serversDownTime` / `serversUpTime`. **Operational status embedded in a public config**: it discloses a maintenance window (`2026-08-20T16:00Z`→`16:45Z`) to unauthenticated callers. Note the timezone is `PT` regardless of market — an EU portal serving US/Pacific banner config is a latent bug for anything time-sensitive.
- **`pow.follow.up.settings`** → rate limits (`limitEmailsPerHour:3`, clinic caps), a URL-validating `urlPattern` regex, a 3-domain `whitelistDomains`, and `charReplacements` for `<`/`>`/`:` — an HTML-sanitising follow-up-email template config.
- **`pow.country.media.groups`** → 37 + 51 country codes in two groups (EU/EEA/UK vs the rest). Useful as a shipped country-inventory.
- **`pow.invite.to.personal.uri`** → bare string `https://carelink.minimed.eu`.
- **`pow.nutrino.cc.broker.service.config`** / **`…metadata.service.config`** → host `https://commoncore.medtronic.eu/reports-broker/v1` and `/reports-metadata/v1`, the five report sub-paths, and a `security_headers` object containing an `x-api-key` placeholder. **Value redacted here by policy**; it is the inert placeholder already documented in `PUBLIC-CONFIG-FINDINGS.md`, *not* the live bundle credential in `SECURITY-FINDINGS.md`. The two must not be conflated.
- **`cms-config.json`** → literally `{}`. Endpoint exists, publishes nothing.

---

## 7. Verdict on **#84** (NGP alarm codes) — **advanced to a firm negative**

> **The NGP / Next Generation Platform alarm-code vocabulary is not published on
> any unauthenticated surface we can reach.**

What was actually done:

- **28 distinct key names** probed across both rounds and **all 404**, spanning
  every vocabulary Medtronic plausibly uses. Round 1 exhausted the **"alarm"**
  space (14 names: `{cua,csr,pow,system,hcp,}alarm.codes.settings`,
  `logbook.alarm.codes`, `system.pump.alarm.codes.config`,
  `system.error.codes.config`, …). Round 2 exhausted the **"notification"**
  space — which is the term Medtronic actually uses for the N-codes — plus
  alert/status/notify/ngp and every severity spelling (6 more, §5).
- **The 404s are trustworthy**, because of two controls that did not have to be
  assumed: the namespace is **case-sensitive** (§4), so a lower-case guess that
  misses is a real absence; and **401-vs-404 is a validated existence oracle**
  (§3) with a positive control, so the 404s are distinguishable from the
  gated keys we *can* see exist.
- **Cross-checked at zero request cost** in the two corpora already on disk: the
  69-key patient config contains **zero** `N\d\d` tokens and no alarm/severity
  key beyond `personal.notification.enabled`; `hp-main.js` scores **0**
  case-sensitive hits for `N24|N35|N40|N47|N48|N50|N55|N131`, `ALARM`,
  `alarmCode`, `stop_using_pump`, `stopUsingPump`; and the full 224-chunk lazy
  corpus was already recorded as containing none.
- The one HCP key that *sounds* right, `cua.control.codes.settings`, is the
  **control** vocabulary (§6.1) and contains **no N-codes**, matching the
  patient-side finding exactly. The two surfaces agree on this negative.

**A hypothesis I formed and then refuted — recorded because the refutation is
the finding.** I hypothesised that HCP prefixes mirror patient prefixes
(`personal.banner.notifications` ↔ `hcp.banner.notifications` is a real pair),
which would have let #84 be closed *by argument*: if an alarm vocabulary existed
on the patient side it would appear here under `hcp.`. **It does not hold.**
`hcp.control.codes.settings` → 404 (the key lives at `cua.`), `hcp.logbook.supported.entry.types`
→ 404 (the key lives unprefixed), `csr.logbook.supported.entry.types` → 404
(unprefixed). The `hcp.` namespace is just a third namespace, not an alias
family. So the 404 list stands as a list, not as a proof by mapping.

**Where this leaves #84.** The vocabulary is not obtainable unauthenticated.
The remaining candidates are all token-gated or POST-only: `hcp/configuration/application`,
`productContext`, `user` (405, POST-only) and `appContext`, `access/config`,
`whitelisted` (401). The most likely remaining home is
`POST hcp/configuration/application`, which the bundle shows returning a large
`appConfig` blob with per-clinic settings — that is a **clinician-token**
request and out of scope for this project. Recommend #84 be retitled from
"find the key" to "obtain an authenticated `application` config or a real
device/pump report, since the vocabulary is not published", and record the
negative above so nobody re-runs this enumeration.

---

## 8. Verdict on **#76** (logbook entry types / `markers[]`) — **advanced, modestly**

`logbook.supported.entry.types` is now confirmed on **two independent surfaces**
with byte-identical content (§6.2). The ROADMAP's deferred `markers[]`
vocabulary — 12 types — is corroborated by the clinician portal as well as the
patient cloud, which is the strongest form of confirmation available without a
token.

What #76 still needs, and did **not** get:

- **`system.logbook.entry.validation.config` returns `null` in the patient
  config** — the key is *published but empty*, which is different from absent
  and is worth recording so nobody re-chases it as a missing endpoint. On HCP
  the same name 404s (and 404s again with `?countryCode=EU`).
- The **per-entry field names** the ROADMAP actually lacks — `removalType`,
  `removalReason`, `adhesivetapeLocation`, `sensorInsertionLocation`,
  `timecapUnscrewed`, `notes`, `entryTs` — remain **token-gated**: they are
  call-site fields in the lazy chunks, not config. The portal serves them from
  `hcp/patients/{patientId}/logbook/entries`, which is patient-scoped, requires a
  token, and was **not requested** (out of scope by instruction and by the
  no-patient-data rule).
- `logbook.entry.validation.config`, `cua.logbook.settings`, `logbook.settings`,
  `logbook.marker.types`, `csr.`/`cua.logbook.entry.validation.config` → all 404.

**Bottom line for #76: the type vocabulary is settled and double-sourced; the
per-entry payload schema is not obtainable unauthenticated and is not in this
configuration family.** Recommend closing the *vocabulary* half of #76 and
splitting the payload half out as a token-dependent item.

---

## 9. Incidental findings worth recording

1. **Four pump model codes that appear nowhere else** — `MMT-8200`, `MMT-8201`,
   `MMT-8400`, `MMT-8401` are in
   `pow.common.core.report.generation → reportFileNamingSupportedPumpModels`
   (214 entries) but **absent** from the patient config's
   `personal.device.family.to.model.mapping`. These are not in the `CC880` /
   `SIMPLERACC` families published in `PUBLIC-CONFIG-FINDINGS.md`, so they are a
   **third, partial table** — reinforcing that note's warning that no single
   table is authoritative. Relevant to #81.
2. **MMT-8600 / MMT-8601 do appear in the portal bundle's config** here
   (`reportFileNamingSupportedPumpModels`), which resolves the `JS-API-SURFACE.md`
   §10 Q1 tension: they were missing from the *bundle's* table, and they are
   present in both published configs — under `SIMPLERACC` in the patient map.
   The bundle's table was the incomplete one.
3. **`carelink-support.medtronic.eu`** — a new Medtronic host, disclosed by
   `cua.crm.settings` as the support-CRM base URI. (Recorded, not probed.)
4. **`hcp.banner.notifications` discloses a maintenance window** to
   unauthenticated callers, and hardcodes `timezone: "PT"` on an EU portal.
5. **`pow.follow.up.settings.whitelistDomains` is a 3-domain allowlist**
   (`www.medtronic.com`, `www.medtronicdiabetes.com`,
   `www.medtronic-diabetes.com`) — note the hyphen/non-hyphen pair, which is
   the sort of thing that produces confusing report-link bugs.
6. **`X-System-ID` is a validated client-identity whitelist, case-insensitive.**
   This belongs in `SECURITY-FINDINGS.md` as a note on the vendor's own request
   contract (it is not an exposure and not a bypass), but it is recorded here so
   the claim is not duplicated or contradicted. The **credential** itself was
   never touched by this pass and appears in no file written today.
7. The `pow.common.core.report.generation` report rules are **CGM-only**
   (`deviceType` ∈ {`CC`, `Cosmos`}) — consistent with §7: this portal's report
   layer knows nothing about pump alarms.

---

## 10. Do not re-run

- The `hcp/configuration/public/*` namespace is **exhaustively mapped**: 13 keys
  return JSON, 1 is token-gated (`personal/media/config/<locale>`), 1 is an
  empty `{}` (`cms-config.json`), and every other bundle-known name is 404. All
  15 bundle-declared `public/*` keys and all 6 direct `hcp/configuration/*`
  endpoints have been resolved to an existence verdict.
- The NGP alarm-code search is closed as a negative (§7) **with controls**.
- The 401/404 oracle (§3) and the case-sensitivity control (§4) are the reusable
  parts; re-derive those before trusting any future 404 from this host.
- Not attempted, by instruction or by scope: `/patients/`, `/user/`, `/clinics/`
  (patient data or identity), and any POST/tokened endpoint.