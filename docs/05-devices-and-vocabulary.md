# Devices and vocabulary

> **Navigation** — the map: [`00-summary-the-map.md`](00-summary-the-map.md) · ← prev: [`04-configuration.md`](04-configuration.md) · → next: [`06-patient-api-surface.md`](06-patient-api-surface.md)

Dated 2026-10-10. Sources: `findings-log/probe-2026-10-08/recov/PATIENT-APP-VOCABULARY.md`,
`PUBLIC-CONFIG-FINDINGS.md`, `AUTH-TENANT-FINDINGS.md`, `recon/HCP-CONFIG-SCHEMA.md`,
`recon/JS-API-SURFACE.md`, `CHUNK-CORPUS-FINDINGS.md`.

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = vendor document served
without a login · **INFERRED** = reasoned, not seen.

> **Consumer note.** How much of this page is *load-bearing* for a client depends
> entirely on its matcher, so read the matcher's shape before assuming.
> [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge) matches
> on `isBleDevice()` in `src/carelink/client.ts`, and it is deliberately
> narrow: a `BLE`/`SIMPLERA` family **prefix**, plus exactly **one** published
> family token (`CC880`, the family the vendor's own config maps to "MiniMed™
> Flex"), plus a loose `FLEX` substring fallback, plus model prefix. The other
> published families — CC840, EAGLE, GST, NMX7, NMX8, GM, INSTINCT — are
> **deliberately not matched**, because routing a non-BLE device down the BLE
> endpoint is its own silent failure.
>
> So most of the 16-family vocabulary on this page carries no routing consequence
> for that client, and a wrong token here is *not* automatically a bridge bug.
> The consequential inputs are `CC880`, the `BLE`/`SIMPLERA` prefixes, and the
> model-prefix list.
>
> **Note on that consumer's own docs.** Its `docs/vendor-api/README.md`
> described matching on model prefix "rather than family token" — stale, since
> the `CC880` family-token match in `src/carelink/client.ts` postdates it. Read
> the code, not prose: `BLE_FAMILY_TOKENS` is the authority on what is matched.

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
| patient config | `personal.device.family.to.model.mapping` | 16 families | `MMT-8200`, `MMT-8201`, `MMT-8400`, `MMT-8401` — present in the HCP report config **and in both portal builds**, **absent here** |
| clinic bundle device table (both builds — see per-build note below) | `hp-main.js` module `68462`, byte range 2999400–3007200; PUMP / SENSOR / StandaloneCGM / InsulinDelivery | **80 distinct `MMT-*`, 9 distinct `SKU-*`** | `MMT-8600`, `MMT-8601` — absent from the table *in the same file* |
| HCP report config | `/hcp/configuration/public/pow.common.core.report.generation` → `reportFileNamingSupportedPumpModels` (214 entries) | includes MMT-8600/8601 and MMT-8200/8201/8400/8401 | **a third, partial table** — no single table is authoritative |

> **Per-build note — 2026-10-13 (area G).** "The clinic bundle's device table"
> above is now confirmed to be **one table in two builds, not two tables**: the
> clinic `pow` asset (`main.fb5f8cb7eb60c4d5.js`, 3,397,615 B) and the support
> `cua` asset (`main.759cddab23085086.js`, 3,410,666 B) were fetched separately
> (6 of a 12 cap, GET only, controls first per host) and extracted separately,
> offline. Result: identical code sets (78 table codes + 9 `SKU-*`), identical
> display-name pairs (76 quoted + 2 unquoted `MMT5100`/`MMT5101` aliases + 9
> `SKU-*`), identical whole-file census (80 `MMT-*`, same set), identical
> module-`90991` `["MMT-8600","MMT-8601"]` array, identical answers on 23
> patient-map spot checks — in both builds [source:
> findings-log/2026-10-13-area-g-device-tables/FINDINGS.md]. The segments differ
> at the byte level (minified renaming, shifted offsets), so byte-identity was
> never claimed; code-set and name-pair identity is, and both hold. **A negative
> closes the area**: G's premise is unchanged and the reconciliation stays
> three-way.
>
> One positive side-finding: `MMT-8200`/`8201` ("Guardian™ 4 system") and
> `MMT-8400`/`8401` ("Simplera™ system") are **present in both builds' tables
> with display names** [source:
> findings-log/2026-10-13-area-g-device-tables/FINDINGS.md]. The patient map is
> now the *only* compared source that lacks them. Against the patient map's
> recorded rows, both builds agree: present are the six base `CC880` Flex codes,
> `NMX8` `8162`/`8163`, `BLE780` base + XCU/XCE/XCF, base `MMT-5100`/`5101`;
> absent (whole-file, case-exact) are `CC840` `8021`–`8023`, `MMT-1909`,
> `MMT-8602`, all four `EAGLE` codes, all five `CC880` XCF/XCC variants,
> `MMT-1886XCY`, and the `SIMPLERACC` JC/JD/P/M suffixes [source:
> findings-log/2026-10-13-area-g-device-tables/FINDINGS.md]. Limits: the HCP
> 214-entry list is compared only through its recorded count and named deltas
> (the full list is not on disk), and the patient map only through its 8
> recorded family rows.

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

> ### ⚠ Correction — 2026-10-13 — the 214-entry list is not HCP-only
>
> The row above (and `docs/11` area H) located `reportFileNamingSupportedPumpModels`
> in the HCP namespace only. The **patient** public config carries the same list:
> `personal.common.core.report.generation.reportFileNamingSupportedPumpModels`,
> **214 strings**, re-derived live 2026-10-13 (`GET
> /patient/v2/configuration/public` → 200, 69 keys, body digest
> `d68b6b5…f1cb2d`) — the count above is now measured, not repeated
> [source: findings-log/2026-10-13-area-h-report-naming/FINDINGS.md §3;
> `list-verbatim.txt`].
>
> Every entry classified in code: **wire code 129 · display name 71 · bare
> number 10 · placeholder 4**. Against the 16-family value set
> (`family-map-verbatim.txt` — the first commit of all sixteen rows, prose
> previously quoted 8): **82 wire codes matched by family, 47 unmatched**;
> placeholders 4/4 matched (all are INSTINCT values); bare numbers 0/10;
> display names 0/71. Normalization (uppercase + strip non-alphanumerics)
> changes nothing — exact and normalized unmatched sets are identical, so no
> residue entry is a mere spelling variant. Full partition in
> [FINDINGS.md §5](findings-log/2026-10-13-area-h-report-naming/FINDINGS.md).
>
> Anomalies: `MMT-9015` ×2 and `Precision Xtra® / Xceed™` ×2; one trailing-space
> entry (`MMT-5100J      `) that matches the map's own padded `SIMPLERA` entry
> exactly, so the padding is vendor-side; ten `MMT-`+bare pairs (`MMT-515` +
> `515`, …); display names in three sub-shapes (lowercase vendor slugs,
> `®`/`™` meter names, `CSS-7200`/`CSS7200` hyphenated/bare pairs — the alias
> split §Spelling traps already records). The 47 unmatched wire codes group by
> prefix (`105*`, `151*`, `171*`, `178*`, legacy `5xx`/`7xx`, `5101`, `5420`,
> `6500/6501`, `77xx/78xx/79xx`, `8200/8201/8400/8401`) — structural grouping
> only, **INFERRED** as older generations on the stated assumption that the
> family map covers the current lineup; no response demonstrates what any of
> these codes is.
>
> Consequence for the table above: `MMT-8200/8201/8400/8401` are in **both**
> report lists (patient and HCP) and in **neither** family table — the
> "present in the HCP report config, absent here" cell stays true of the
> *map* and is now wrong if read of the *config*. Guidance item 4 below is
> read the same way: the patient **map** is missing those four codes; the
> patient **config** is not.

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
| ~~`deviceFamily`~~ | ~~2~~ | ⚠ **that verdict was wrong — correction below** |

> ### ⚠ Correction — 2026-10-11 — `deviceFamily` **is** an API field
>
> The row above originally read: *"`deviceFamily` — 2 hits — only a localStorage
> patient-filter object — **not an API field**"*.
>
> **That inference is refuted.** Three independent client implementations, each
> written against the live API and each read at a named commit, agree on a two-field
> split that the vendor's bundles do not contain:
>
> | Payload | Field | Cite |
> |---|---|---|
> | `/patient/monitor/data` | **`deviceFamily`** — the routing discriminator | `nightscout-connect` `index.js:587`; xDrip `message/MonitorData.java:5`; `CarlosJPV` `src/types/carelink.ts:29-34` |
> | Cumulus / ble data payload | **`medicalDeviceFamily`** — the reported family | `nightscout-connect` `index.js:179,194`; xDrip `message/RecentData.java:102`; `CarlosJPV` `src/types/carelink.ts:33` |
>
> **Why the original claim was wrong.** The corpus scan was correct *about the
> bundles* — `deviceFamily` really does appear twice in the patient portal's own
> JavaScript, and really does not appear as a wire field there. What it could not
> see is a field the vendor's own client **does not send**, because the field lives
> in a response the portal never renders. A corpus scan of a frontend is evidence
> about the frontend, not about the API.
>
> **Still open:** no client reports a `deviceFamily` *value* — every value observed
> by any of the three is a `medicalDeviceFamily` value. The casing of the routing
> field on the wire remains unobserved, so `docs/10` #81 stays open with a much
> narrower question than it started with.
>
> [source: findings-log/2026-10-11-third-party-client-sources/FINDINGS.md §1, §5.1]

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

**Correction (2026-10-14, lane S5).** The *server/config* negative above still holds:
no vendor surface names an alarm code. But one reproducible *client* artefact does carry
an NGP-specific mapping — the connect monitor component in lazy chunk
`k-6746-c6795ff7e9ff468d-js.b` (101,594 B) canonicalises 137 raw `lastAlarm.code`
strings to 62 canonical codes, with two excluded (`"00-1"`, `"121"`) and a pump-model
gate (`MMT-1809/1810/1818`). That is an alias table, not a definition table: the
human-readable names come from i18n keys `connect.ble.<code>` and no such key exists
in the 215-chunk corpus. See
[findings-log/2026-10-14-area-s5-ngp-alarm-vocabulary-static/FINDINGS.md].

## The field name is settled; the value is not

`deviceFamily` appears as an HTTP **call-site field name** in the lazy-chunk corpus —
independent corroboration of the field *name*, not its *value*. What that field's value
looks like on the wire still needs a token [source:
findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md].

## Correction — 2026-10-14 — `deviceFamily` and `medicalDeviceFamily` are one axis

The two field names have been tracked here as separate discriminators with partly
overlapping vocabularies. **They are not separate on the wire.** The patient client
assigns one from the other, in `parseJsonData` (lazy chunk
`k-6746-c6795ff7e9ff468d-js.b`, definition at byte 74,236):

```js
parseJsonData(i, v) { const n = {};
  n.deviceFamily = i.medicalDeviceFamily,
  n.isGuardian = "GUARDIAN" === n.deviceFamily,
  …
```

So `deviceFamily` is the **reported family under a second name**, not an independent
discriminator (OBSERVED, client source; the same chunk is hash-pinned in
[source: findings-log/2026-10-14-area-s4-lazy-chunk-control-flow/FINDINGS.md] §6).

Two consequences:

1. Any argument that "two independent sources agree on the casing" is over-counting: the
   client enum and the third-party clients are reading one value under two names, not
   corroborating two independent fields.
2. The token **`NGP`** is a `deviceFamily` value the vocabulary table above does not list
   — the client compares it directly at **four** sites in the same chunk: bytes 76,304
   (gates alarm-code formatting), 78,359 (gates last-bolus fields), 83,893 (compares
   `medicalDeviceFamily` directly — point 1's one-axis reading again, at a
   second call site in the same chunk) and 87,564
   (`this.isNGP="NGP"===K.deviceFamily`). **OBSERVED.** This is a *client-side* comparison
   value; the server's own NGP vocabulary remains token-gated (`docs/10` #38, #39).

> **⚠ Corrected 2026-10-14 (area S independence audit).** The parenthetical above
> read *"independently corroborating point 1"*. Both halves of that corroboration
> are **one author**: byte 83,893 and point 1 are two read sites in the **same
> client chunk**. `AGENTS.md` §2.1 counts the producer, not the artefact, so the
> independent count is **1** and the strength word is withdrawn. The corrected
> wording states the same fact — a second call site in the same chunk, which is
> repetition rather than corroboration, and is why point 1 says the two-field
> reading over-counts its own evidence.
> [source: findings-log/2026-10-14-pool-s-independence-audit/FINDINGS.md §3
> row 13].

The five-token enum above is still the client matcher set. `NGP` is compared by equality
rather than through `startsWith`, so it sits outside that matcher — which is consistent
with a Guardian-era device reaching that code by a different route.

**Also resolved:** the casing correction `timecapUnscrewed` → `timeCapUnscrewed` is real
but was mis-stated. Both forms exist, with different jobs: **`timecapUnscrewed`** (42
corpus occurrences) is a *form-control* name — `form.addControl("timecapUnscrewed", …)`,
`isShowControlError("timecapUnscrewed","required")` — and **`timeCapUnscrewed`** (5) is the
*wire* field, assigned `this.capUnscrewDateConversion()`. The lowercase form is not an
error; it was being read as a wire field when it is a control name. Same for
`sensorInsertionLocation` and `adhesivetapeLocation`, whose wire keys are
`sensorInsertionInfo.sensorLocation` and `adhesiveAndTapeInfo.sensorLocation` (OBSERVED,
lazy chunk `k-9799-ae484032a07c9d4f-js.b`: the serialiser is the `if(this.form.valid)`
statement at bytes 80,919–84,159, but the 42 control-name occurrences live at
30,424–98,733, so no single window holds both halves of the distinction).

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
