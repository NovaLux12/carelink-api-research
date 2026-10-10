# Devices and vocabulary

> **Navigation** — the map: [`00-summary-the-map.md`](00-summary-the-map.md) · ← prev: [`04-configuration.md`](04-configuration.md) · → next: [`06-patient-api-surface.md`](06-patient-api-surface.md)

Dated 2026-10-10. Sources: `findings-log/probe-2026-10-08/recov/PATIENT-APP-VOCABULARY.md`,
`PUBLIC-CONFIG-FINDINGS.md`, `AUTH-TENANT-FINDINGS.md`, `recon/HCP-CONFIG-SCHEMA.md`,
`recon/JS-API-SURFACE.md`, `CHUNK-CORPUS-FINDINGS.md`.

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = vendor document served
without a login · **INFERRED** = reasoned, not seen.

> **Provenance rule.** `recov/PATIENT-APP-VOCABULARY.md` is the **only patient-app-side**
> artefact in this project. `JS-API-SURFACE.md` and `CHUNK-CORPUS-FINDINGS.md` are
> clinic-side. Do not cite them for patient-path questions; cite them for the clinic
> portal's model tables only [source:
> findings-log/probe-2026-10-08/recov/PATIENT-APP-VOCABULARY.md].

## The published vocabulary — 16 families

`personal.device.family.to.model.mapping` in `/patient/v2/configuration/public` —
**PUBLISHED** in vendor config, the endpoint itself **OBSERVED** live:

```
GM  BLE700  BLE720  BLE740  BLE770  BLE780  GST  SIMPLERA
SIMPLERACC  SIMPLERACCOLID  NMX7  CC840  CC880  NMX8  INSTINCT  EAGLE
```

| family | models (verbatim rows) |
|---|---|
| `BLE780` | MMT-1884/1885/1886 + XCU/XCE/XCF/XCY clinical variants |
| `CC880` | MMT-8062, 8063, 8082, 8083, 8084, 8085, 8162XCF, 8172XCF, 8163XCF, 8173XCF, 8173XCC |
| `CC840` | MMT-8021, 8022, 8023 |
| `NMX7` / `NMX8` | MMT-1906-1909 / MMT-8162, 8163 |
| `EAGLE` | MMT-9015, 9017, 9115, 9117 |
| `SIMPLERACC` | MMT-8600, 8601, MMT5100, MMT-5100JC1/2/4, MMT-5101W1/2/4, MMT-5100JD4, MMT-5101P/M |
| `SIMPLERACCOLID` | MMT-8602 |
| `INSTINCT` | SKU-78893-01 … SKU-78968-01 (plus unprefixed duplicates) |

A second, independent key corroborates the marketing name:

```json
"system.settings.transfer.feature.config": { "device.mapping": { "BLE780": "780G", "CC880": "MiniMed™ Flex" } }
```

**So `CC880` *is* the Minimed Flex family** — six model prefixes, MMT-8062/8063/8082-8085,
all appearing under `CC880`. Note it contains **no** `BLE` and **no** `FLEX` token, which
is exactly why a matcher that greps for those two strings misses the device entirely
[source: findings-log/probe-2026-10-08/PUBLIC-CONFIG-FINDINGS.md].

> **⚠ Correction — preserved.** An earlier note read `MMT-8600`/`MMT-8601` as *missing
> from Medtronic's tables*. They are not: the JS-bundle agent found them absent from the
> **portal bundle's** device table, and they are present here under `SIMPLERACC`. Two
> different tables, both partial. Nobody should conclude the portal table is
> authoritative [source: findings-log/probe-2026-10-08/PUBLIC-CONFIG-FINDINGS.md].

## Why family matching is unreliable

The patient portal's main bundle is served at the **domain root** of
`carelink.minimed.eu` (3.4 MB) and is a *different* bundle from the clinician portal's
`main.fb5f8cb7eb60c4d5.js`. Its matcher module `45559` is:

```js
{ BLE: "BLE", BLE_X: "BLE_X", SIMPLERA: "SIMPLERA", SIMPLERA_X: "SIMPLERA_X", GUARDIAN: "GUARDIAN" }
```

consumed as `deviceFamily.startsWith(…)` — **five tokens**. `CC880` is not among them, and
nor is anything containing `FLEX` [source:
findings-log/probe-2026-10-08/recov/PATIENT-APP-VOCABULARY.md].

Two readings, and no source can currently separate them:

| reading | claim |
|---|---|
| (a) | CC880 is the Flex family, and **Medtronic's own patient app is out of date** — it would also fail to detect a Flex. Possible; odd for a device already shipping |
| (b) | There is **a further family value nobody has found**, one that *does* start with one of those five tokens, and the Flex reports that. The published `CC880 → "MiniMed™ Flex"` would then be a *display* name, not a wire family |

Reading (b) is the one that keeps the wire-shape question open: the published config tells
us Medtronic's internal label for the Flex, not what the patient API emits. The
five-token `startsWith` matcher is direct evidence that whatever the Flex sends must be
matched by code that looks nothing like a `CC880` comparison.

**Consequence for third-party clients:** matching `CC880` exactly *and* keeping a
model-prefix fallback is not belt-and-braces, it is necessary. A family-only matcher —
even one containing all sixteen published families — is a guess about which of the two
readings is right. **The model-prefix path is the one that works under either reading**,
because the six Flex model numbers are consistent across every source held.

## Three model tables, all partial

| table | where | coverage | what it misses |
|---|---|---|---|
| patient config | `personal.device.family.to.model.mapping` | 16 families | `MMT-8200`, `MMT-8201`, `MMT-8400`, `MMT-8401` — present in the HCP report config, **absent here** |
| clinic bundle device table | `hp-main.js` module `68462`, byte range 2999400–3007200; PUMP / SENSOR / StandaloneCGM / InsulinDelivery | **80 distinct `MMT-*`, 9 distinct `SKU-*`** | `MMT-8600`, `MMT-8601` — absent from the table *in the same file* |
| HCP report config | `/hcp/configuration/public/pow.common.core.report.generation` → `reportFileNamingSupportedPumpModels` (214 entries) | includes MMT-8600/8601 and MMT-8200/8201/8400/8401 | **a third, partial table** — no single table is authoritative |

`MMT-8600`/`MMT-8601` appear elsewhere in the clinic bundle, module `90991`:

```js
const S = ["MMT-8600","MMT-8601"];
…  S.includes(Ce.dM) ? Ce.sM : Ce.dM
```

For these two codes the portal **ignores `deviceModel` and displays `sensorModel`
instead** — neither is a key in the device table, so the lookup can only succeed via the
sensor branch. Anyone mapping `deviceModel` → hardware from that table gets these two
wrong. Interpretation flagged, **not asserted**: the signature of a pump whose own model
code carries no clinician-facing meaning, i.e. hardware that pairs with a
separately-branded sensor. What it actually is **cannot be determined from the bundle**
and must not be guessed at [source:
findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md].

The HCP report config resolves that tension: MMT-8600/8601 are present in **both**
published configs — under `SIMPLERACC` in the patient map. **The bundle's table was the
incomplete one** [source:
findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md].

## Spelling traps

Medtronic is not internally consistent, so **family matching must be case-insensitive and
must handle the display-name spelling**:

| trap | detail |
|---|---|
| enum vs value | `SIMPLERA_SYSTEM` is the enum but `"Simplera™ system"` is the value; `COSMOS` is the enum but the wire `deviceType` value is `"Cosmos"` |
| mixed-case pairing | the bundle's pairing Map uses `deviceType:"CC"` against `deviceType:"Cosmos"` in the same structure |
| trailing whitespace | the `SIMPLERA` model list is **padded** — `"MMT-5100       "`, `"MMT-5100J      "`, `"MMT-5100CLXP   "`. An exact-match parser silently misses them; uppercase + strip non-alphanumerics handles it, a naive `===` does not |
| unhyphenated aliases | `MMT5100`/`MMT5101` in SENSOR, `CSS7200`/`CSS7201` in StandaloneCGM are bare aliases of the hyphenated codes |
| clinical suffixes | `MMT-1884XCU`, `MMT-1885XCE`, `MMT-1886XCE`, `MMT-1886XCF` are distinct keys, not string variants |

Sources: [findings-log/probe-2026-10-08/PUBLIC-CONFIG-FINDINGS.md],
[findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md],
[findings-log/probe-2026-10-08/AUTH-TENANT-FINDINGS.md].

## What the clinic portal actually knows

Device **types**, not families: `CC`, `COSMOS`, `COSMOS_WHITELISTED`, `DEVICE`. The
pairing map encodes **nine ordered dual-system pairings** (pump-side and sensor-side
types for the same period, `lastPeriod` marking which was active at the end);
`COSMOS_CC`, `CC_COSMOS`, `CC_DEVICE`, `DEVICE_CC` are all distinct rows, so the pairing
is **ordered, not commutative**. The report rules are CGM-only
(`deviceType` ∈ {`CC`, `Cosmos`}) — the portal's report layer knows nothing about pump
alarms [source: findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md].

Decisive negatives in that bundle for the patient-side `deviceFamily` question:

| token | case-sensitive hits | verdict |
|---|---:|---|
| `medicalDeviceFamily` | **0** | absent |
| `GUARDIAN` | **0** as a token | the rest are display names (`Guardian™ Sensor 3`, …) and zxcvbn dictionary words |
| `BLE` | **0** as a token | case-insensitive hits are `TABLE`, `ENABLED`, … |
| `SIMPLERA` | 2 | only the enum key `SIMPLERA_SYSTEM` |
| `deviceFamily` | 2 | only a localStorage patient-filter object — **not an API field** |

So the clinic bundle's vocabulary is model codes and `deviceType`; it **cannot** answer
what `deviceFamily` looks like on the wire. The one overlap is the token `CC`, which the
bundle confirms as a first-class device type. The mobile payload's family vocabulary is
recorded elsewhere as `GUARDIAN`/`NGP`/`CGM`/`CC` — **INFERRED**, carried forward from an
earlier round and not re-derived here [source:
findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md].

## NGP alarm codes — absent from every artefact held

Not in the patient bundle (its three apparent matches are Samsung user-agent strings), not
in the clinic bundle, not in the clinic's 224 lazy chunks, not in the public config, not
in any `hcp/configuration/public/*` key. The accumulating negative is complete
[source: findings-log/probe-2026-10-08/recov/PATIENT-APP-VOCABULARY.md].

## The field name is settled; the value is not

`deviceFamily` appears as an HTTP **call-site field name** in the lazy-chunk corpus —
independent corroboration of the field *name*, not its *value*. What that field's value
looks like on the wire still needs a token [source:
findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md].

## Guidance

1. **Match on model prefixes** (`MMT-…`, `SKU-…`), not on family. This is the only path
   that works under both readings of the Flex problem.
2. If you must match family: case-insensitive, handle the display-name spelling, and treat
   the sixteen published families as **open** — reading (b) above implies an unrecorded
   value exists.
3. Normalise before comparing: uppercase and strip non-alphanumerics. This absorbs the
   trailing-whitespace padding and the hyphenated/unhyphenated alias split.
4. Do not map `deviceModel` → hardware from the clinic bundle's table alone; it is missing
   MMT-8600/8601, and the patient config map is missing MMT-8200/8201/8400/8401.
