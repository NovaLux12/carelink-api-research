# Area DP — the pump-data plane the bridge discards

**Minted** 2026-11-11 (issue #224) · **Requests** 2 of a 2 cap · **Revisions** 0
**Zero-request content:** everything below after the two fetches is offline reading of bodies
already on disk.

---

## 0. Why this area exists

The repository holds a gap memo dated 2026-07-21
(`findings-log/medtronic-carelink-2026-07-21/03-data-model-and-gaps.md`) that ranks what the
bridge throws away. Its top two items are:

- **P1.1** — *"treatments (markers) upload is the single largest 'available but unused' gap"*
- **P1.2** — *"Medtronic 780G auto-mode fields likely available but currently unmodeled"*

Both were marked **blocked on a real 780G account**, and both sat unmeasured for four months on
that basis. That blocker was wrong, and it was wrong in a way worth recording: **a client that
parses a response is a published description of that response.** The patient app ships its own
parser to every browser. Nothing about reading it needs a token.

This area buys the field set at two requests.

## 1. Method

Two `GET`s, both against `carelink.minimed.eu`:

| # | asset | status | bytes | sha256 | note |
|---|---|---|---|---|---|
| 1 | `/main.6595daf83bd6d4b1.js` | 200 | 3,417,255 | `0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa` | **digest reproduces the pinned value** — area K's positive control, unchanged since 2026-10-13 |
| 2 | `/6746.c6795ff7e9ff468d.js` | 200 | 101,594 | (see `results.jsonl`) | the lazy chunk area V identified as carrying the marker parser |

Both `200`, both `application/javascript`. `t_sent` recorded per request; the two are on the same
host and 10.0 s apart, inside the ≥2.5 s floor. **Spacing is a single clock and only two gaps
exist, so no spacing statistic is claimed** — two points cannot establish a floor.

The eager bundle was fetched rather than reused because the on-disk copy
(`.loop/aq-assets/main.js`, `2a7fa8e7…`) is the **clinic portal** build, not the patient app: it
carries `hcp/` 190 times and `carepartner/` zero times. Reading the portal build for patient
fields is the exact error area P made (see §5).

## 2. The structural result — the fields are not in the eager bundle at all

Every pump-data field was counted in both bodies:

| token | chunk `6746` | eager `main` | first offset |
|---|---|---|---|
| `therapyAlgorithmState` | **5** | **0** | 47,334 |
| `autoModeShieldState` | **3** | **0** | 47,446 |
| `plgmLgsState` | **2** | **0** | 47,485 |
| `lastAlarm` | **29** | **0** | 75,838 |
| `activeInsulin` | **3** | **0** | 78,004 |
| `reservoirRemainingUnits` | **2** | **0** | 76,999 |
| `reservoirAmount` | **4** | **0** | 76,980 |
| `reservoirLevelPercent` | **4** | **0** | 76,930 |
| `medicalDeviceBatteryLevelPercent` | **4** | **0** | 77,083 |
| `conduitBatteryLevel` | **5** | **0** | 77,206 |
| `conduitInRange` | **6** | **0** | 77,172 |
| `sensorState` | **15** | **0** | 45,353 |
| `calibStatus` | **4** | **0** | 76,871 |
| `sensorDurationHours` | **5** | **0** | 76,600 |
| `timeToNextCalibHours` | **4** | **0** | 76,532 |
| `markers` | **1** | 1 | 77,986 |
| `lastSGTrend` | **6** | **0** | 41,049 |
| `sgs` | **7** | **0** | 34,359 |
| `systemStatusMessage` | **24** | **0** | 45,578 |
| `medicalDeviceSuspended` | **8** | **0** | 47,380 |
| `pumpModelNumber` | **5** | **0** | 46,746 |
| `medicalDeviceFamily` | **5** | **0** | 74,282 |
| `deviceFamily` | 10 | 5 | 10,825 |
| `bgUnits` | 53 | 14 | 34,012 |

**21 of 24 tokens are zero in the eager bundle.** The three exceptions each appear in both bodies:
`markers` (1 hit in the eager bundle, and it is the SVG/charting sense rather than the wire field —
area S4 §5 already established that distinction), `deviceFamily` (5) and `bgUnits` (14). None of the
three is a pump-data field: the first two are routing/unit discriminators that the login and
transform paths need before any chunk loads.

**This is the finding that makes the rest actionable:** the pump-data parser is *entirely* in a
lazy chunk — 21 of the 24 tokens measured carry zero hits in the eager bundle. A static pass that reads only the eager bundle — which is what the repo's standing
"read the hash-pinned patient bundle" habit does — sees **none of it**. That is not a gap in
diligence; it is a structural property of how the app is split, and it explains four months of
"blocked on a real account" for something that was two requests away.

**Caveat, stated because the negative is broad:** this is measured against **two bodies**, not
against the 211-chunk corpus. `0` here means "absent from the eager bundle and present in 6746",
not "absent from every chunk". Area AU is sweeping the full 211 for the INSTINCT tail; a
pump-field sweep of all 211 is not done and is not claimed.

## 3. `therapyAlgorithmState` — SmartGuard's own state machine

Read at bytes 47,334 / 47,446 / 47,485 / 48,685 in two consumers,
`setStatusTherapyIcon(a)` and `setStatusTherapyColor(a,m)`. Both destructure the same object:

```js
setStatusTherapyIcon(a){
  const m = a.therapyAlgorithmState,
        f = a.pumpModelNumber,
        M = a.medicalDeviceSuspended,
        G = a.systemStatusMessage,
        U = null == m ? void 0 : m.autoModeShieldState,
        D = null == m ? void 0 : m.plgmLgsState;
  ...
}
```

Two nested fields, two disjoint vocabularies, **seven tokens total** (OBSERVED, verbatim string
literals in the same chunk):

| field | tokens | count |
|---|---|---|
| `therapyAlgorithmState.autoModeShieldState` | `AUTO_BASAL`, `SAFE_BASAL`, `FEATURE_OFF` | **3** |
| `therapyAlgorithmState.plgmLgsState` | `FEATURE_OFF`, `REFRACTORY_PERIOD`, `MONITORING`, `SUSPEND_FIRED_PLGM`, `SUSPEND_FIRED_LGS` | **5** |

`plgmLgsState` is the **Predictive Low Glucose Management / Low Glucose Suspend** state, which is
the safety-relevant half: `SUSPEND_FIRED_PLGM` and `SUSPEND_FIRED_LGS` mean the pump has stopped
insulin delivery. The client treats them as a blinking icon
(`Re = "SUSPEND_FIRED_PLGM" === D || "SUSPEND_FIRED_LGS" === D; ... Re && M && (this.autoModeImg = $e, this.blinking = !0)`).

**INFERRED, and the inference is bounded:** that these strings arrive as JSON string values on the
`connect/data` response rather than being client-side state labels. The evidence is that they are
read as properties of `a.therapyAlgorithmState`, where `a` is the response object also carrying
`sgs`, `lastAlarm`, `pumpModelNumber` and `bgUnits` — the same object, so the same origin. It is
**not** a captured payload; no live response in this repository shows either field. A token-holder
reading one `connect/data` body would settle it in one request, and that request is out of scope
here.

**P1.2 is therefore answered as a schema, not as a live observation.** The field names, the nesting
and both vocabularies are recovered; whether a given pump populates them is not.

## 4. The alarm-code normalisation table — 73 codes, 19 names

This is the item `docs/10` records as *"Not published on any unauthenticated surface"*, and the
item area P closed with `alarmCode` = **0 hits**.

The table is at byte **84,476** of chunk 6746, as a single object literal of 73 pairs, consumed at
byte **87,695** as `const ee = e[H]` where `H = K.sLastAlarmCode`. Its cardinality:

**73 source codes collapse to 19 distinct name keys.** Full table in `alarm-code-map.json`.

| target name key | source codes that map to it |
|---|---|
| `002` | 39 — `002 003 004 013 014 015 016 017 018 019 020 022 023 026 027 028 030 031 033 034 044 045 046 049 053 054 060 063 064 065 067 068 074 075 076 079 080 081 082` |
| `024` | 7 — `024 035 040 047 048 050 055` |
| `037` | 6 — `037 038 039 041 042 043` |
| `062` | 4 — `062 070 071 072` |
| `007` | 2 — `007 008` |
| `011` | 2 — `011 073` |
| the other 13 | one code each — `006 012 025 029 051 052 057 058 061 066 069 077 084` |

**Why the previous passes missed it, and this matters more than the table:**

1. **Area P searched for `alarmCode`.** That token occurs **0** times in this chunk. The wire
   property is `lastAlarm` (29 hits), and the code is read as `O.code` where `O` is the alarm
   object. `alarmCode` is the *portal's* name for the concept, not the patient wire field's.
2. **The map is keyed on the code's VALUE, not its name.** No search for an identifier finds a
   lookup table of string literals like `"024":"024"`.
3. **Area P read the portal bundles.** `therapyAlgorithmState` is 0 there and 5 here.

So `docs/10`'s negative is **correct about what it searched and wrong about what it implies**. It
says "not published on any unauthenticated surface" on the strength of 28 probed key *names*; the
vocabulary is published, in the client, as data rather than as a route. **That is a correction to
a standing negative, not a new row** — see §5.

### 4a. Two codes the client refuses to render

At byte 87,622 the consumer filters two codes out before lookup:

```js
if (this.isNGP) {
  if (["00-1", "121"].includes(H)) return;
  ...
```

`00-1` and `121` produce **no alarm name at all** — they are suppressed. `docs/05` §Close already
records these two as excluded from its 62-canonical-code count; this is the reason, at the source.

A second suppression list appears at byte 88,057 — codes `070 071 072 108 114 786 787 788 799 806
825 828` and `0` — which force `lastAlarmNameKey = null`. Note `070`/`071`/`072` map to `062` in
the table **and** are suppressed here, so the table entry is unreachable for them. Recorded as
OBSERVED; the reason is not claimed.

## 5. Corrections this area owes to the record

### 5.1 `docs/10` — the NGP alarm-code vocabulary row

The row's class is `OBSERVED negative` and its claim is *"Not published on any unauthenticated
surface"*. **The claim is refuted**: the vocabulary is published in the patient client, and its
normalisation table is recoverable at zero requests. The row's *evidence* was sound (28 key names
did 404) — it searched for route names, and the answer was never a route.

### 5.2 `findings-log/2026-10-13-area-p-static-schema-recovery/FINDINGS.md` §35 and §43

Two cells need narrowing rather than retraction:

- *"`therapyAlgorithmState` … OBSERVED negative on wire form"* — true of the **portal** bundles
  it read, false of the patient app, where it occurs 5 times.
- *"`alarmCode` = 0 in both bundles … Still needs an authenticated POST"* — the token is 0 and
  the conclusion does not follow: `lastAlarm.code` is the field, and its value-space is published.

`findings-log/` is append-only, so both are **superseded here rather than edited**. No edit was
made to either file.

### 5.3 `docs/05` — unaffected

Its 62-canonical-code count and its two exclusions (`00-1`, `121`) stand. This area supplies the
mechanism for the exclusions, not a change to the count.

## 6. What this means for the bridge's Nightscout mapping

Stated as a gap inventory, **not** as a change request — the bridge is a separate repository and
this one publishes findings.

The bridge posts two Nightscout documents per fetch: `entries` (SGVs) and `devicestatus`. The
fields in §2 that reach neither:

| wire field | would map to | status |
|---|---|---|
| `markers[]` | `/api/v1/treatments.json` | **P1.1** — the largest gap; the mapping is already written in `nightscout-connect` and could be ported |
| `therapyAlgorithmState.*` | `devicestatus.pump.annotations` | **P1.2** — schema now recovered (§3) |
| `lastAlarm` | `devicestatus.pump.annotations` | **P0.2** — schema now recovered (§4) |
| `reservoirLevelPercent` | `devicestatus.pump.reservoir` | **P2.1** — 5 snap-points, coarser than the units field |
| `sensorDurationHours`, `timeToNextCalibHours` | `devicestatus` sensor block | partially posted today |

**The safety caveat on alarms is unchanged and must stay:** several NGP codes mean *"Critical Pump
Error. Stop using pump"* or *"Insulin delivery stopped"*. Relaying those to Nightscout as
treatments without operator gating is unsafe. A devicestatus annotation plus a WARN log is the
safe shape; the 2026-07-21 memo's P0.2 says the same and that reasoning still holds.

## 7. What is not claimed

- **No live payload.** Neither field set is observed on the wire. Both are read from the client's
  own parser. Class is OBSERVED-of-source, not OBSERVED-of-response.
- **No token was used and none is needed for §2–§4.**
- **The 211-chunk corpus was not swept for pump fields** — only the eager bundle and chunk 6746.
  §2's zeros are scoped to those two bodies.
- **The alarm-code → human text mapping is not recovered.** The 19 targets are i18n key suffixes
  (`connect.ble.062` etc.); the display strings live in translation bundles not fetched here.
- **`safeBasalDuration` is 0 in this chunk** — the 2026-07-21 memo cited it from a third-party
  document, and it is not in this build. Not refuted, just not found here.
