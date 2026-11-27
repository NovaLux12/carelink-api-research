# `display/message` field semantics: three traps on a real 780G + Instinct account

**Evidence class: OBSERVED.** 2026-11-27, against a live GB account with a paired
Medtronic 780G (MMT-1885) and an Abbott Instinct sensor, on its first day of
operation. Responses read from the authenticated `display/message` data leg and
from the same payload as stored by a Nightscout `devicestatus` row.

**Requests: 0 of a 0 cap.** This pass issued no vendor request of any method — it
is analysis of payloads the operator's own bridge had **already fetched and
stored** before this pass began. No `GET`, `POST` or `OPTIONS` was sent by this
work. Everything below is read out of those stored responses.

### Delay between requests

**None was needed, because no request was made.** The repository's `≥2 s` floor
between requests to the same host is **vacuous** for this pass — there is no
request to space from. The floor is stated here so the accounting is complete
rather than because it applied.

**Where the payload came from:** the operator's bridge captured the response
server-side. It is the operator's own account and the operator confirmed the
response was theirs to see.

---

## 1. `sensorDurationHours` / `sensorDurationMinutes` are REMAINING, not elapsed

The field names carry no direction. Both readings below are from the same day:

| Observation | Value | Implied insertion |
|---|---|---|
| `sensorDurationMinutes` | `21163` (= 352.7 h) | — |
| `sensorDurationHours` | `352` | — |
| Operator's own record of fitting the sensor | "11am ish" | — |
| Payload timestamp | ~18:30 local | ~7.5 h elapsed |

352.7 h of **elapsed** wear is impossible ~7.5 h after insertion. Read as
**remaining** against Abbott's 15-day (360 h) Instinct wear it is exact:

```
360 h − 352.7 h remaining = 7.3 h elapsed   →  insertion ≈ 11:13 that morning
```

which matches the operator's own account to the minute. **OBSERVED: the pair is
time remaining, not time elapsed.**

Secondary observations from the same payloads:

- **The pump omits the field entirely when it loses the sensor.** A later payload
  from the same account carried no `sensorDurationHours`, no
  `sensorDurationMinutes`, and no `timeToNextCalibHours`, while
  `conduitSensorInRange` was `false` and `sensorState` was still
  `NO_ERROR_MESSAGE`. **`sensorState` describes the hardware, not the link**, so a
  healthy `sensorState` beside a missing duration figure means the pump cannot see
  the sensor — not that the sensor is fine.
- **`timeToNextCalibHours` was `65535` and `timeToNextCalibrationMinutes` was
  `65535`** on the payloads that carried them. `65535` is `0xFFFF`, a
  not-applicable sentinel; it is not 7.5 years of calibration time. On the payloads
  where the pump had lost the sensor the fields were absent rather than sentinel,
  so the sentinel appears on a *connected* sensor with no calibration due rather
  than as an error marker. (INFERRED from the two observed states; only the value
  `65535` itself is OBSERVED.)

**Why this matters downstream:** any client that renders `sensorDurationHours` as
"age" puts a sensor-expiry alarm on a sensor fitted that morning, which is a false
clinical alarm. The bridge's own source comments currently say "sensor age" — see
`docs/instinct-data-path-brief.md` §Open question 8, which asks whether 15-day wear
produces an anomalous pair. It does not; the pair is remaining-hours either way,
and the 15-day figure is only needed to turn it into a percentage.

## 2. `bgUnits: "MMOL_L"` can be present on a payload whose values are mg/dL

**OBSERVED on this account:** a payload declaring `"bgUnits":"MMOL_L"` carried
`sgBelowLimit: 50`, `limits[].lowLimit: 68`, and `sgs[].sg` values of 160, 148,
145 — all mg/dL magnitudes.

The unit labels are not self-consistent, and the payload refutes itself:

| Field | Value | As mg/dL | As mmol/L |
|---|---|---|---|
| `limits[].lowLimit` | `68` | **3.78 mmol/L** — exactly the pump's configured low alert | an impossible blood glucose |
| `sgBelowLimit` | `50` | 2.78 mmol/L, a plausible hard floor | impossible |

`sgBelowLimit` and `limits[].lowLimit` share the unit of `sg`, so a low limit of 68
is a valid mg/dL figure and not a survivable mmol/L one. **The declared unit is
wrong when the payload's own limits contradict it.** (INFERRED: that the declaration
is wrong rather than the limits. The values are OBSERVED; the conclusion follows
from what a configurable alert limit can sensibly be.)

This is a sharper statement than `docs/04-configuration.md` currently makes. That
page already warns that **country-settings** `bgUnits` is a per-country display
preference and not the account's unit (`MMOL_L` for GB/IE/AU/NL/NZ but `MG_DL` for
DE/FR despite both being mmol/L countries). What is new here is that the **data
payload's own** `bgUnits` can disagree with its values on a mmol/L-country account,
so reading `data.bgunits ?? data.bgUnits` is not sufficient either.

**A plausibility guard is the only reliable test:** if a payload declares mmol/L
but carries any glucose value, limit, or threshold above ~40, the declaration is
mg/dL wearing the wrong label.

## 3. The `display/message` window is a fixed ring buffer and ignores window parameters

The BLE/data-leg response is a fixed **288-slot** array (288 × 5 min = 24 h). On
first successful poll after the sensor came online:

- 89 slots carried data, the rest were empty placeholders;
- the oldest available reading was when the sensor warmed up that morning — there
  was **no earlier reading to fetch**;
- sending `hours`, `hoursBack`, `startDate`/`endDate` or `count` as query
  parameters changed nothing: the same array came back each time.

**OBSERVED**: the parameters are ignored and the window is fixed. **INFERRED, not
verified:** that the 288 length is a hard constant rather than a maximum the server
chose for this account on this day. The parameter-ignoring is observed directly;
the number 288 is observed once and should be re-checked on a second account or a
second day before being treated as a vendor constant.

**Why this matters downstream:** "does the bridge backfill missed readings?" is
bounded by this ring buffer, not by the bridge. A client can only re-send what the
vendor still holds, and the vendor holds ~24 h. No amount of client-side work
recovers a reading older than the buffer. On this account the gaps that did exist
were one to two polling intervals wide — consistent with a genuine sensor dropout
rather than a bridge failure, because a re-sent window with deterministic ids
backfills a down-bridge gap on the next successful poll.

---

## Closes an open question in the consumer

The bridge repo's `docs/instinct-data-path-brief.md` §Open question 8 asks whether
"the 15-day wear cycle produces a distinct `sensorState` / `sensorDurationHours`
pair". Finding 1 answers it: the pair is **remaining** time, so 15-day wear produces
no distinct shape — it produces the same shape with a longer initial remainder. The
question can be closed with that wording rather than left open. The question lives
in the bridge repo, so closing it there is a downstream change, not an edit to this
record.

---

## What this pass did not establish

- Whether the 288-slot length is a constant across accounts (**not** verified).
- Whether `65535` appears on a payload where calibration is genuinely due
  (the only observed instances were "not applicable").
- Anything about a Guardian 4 sensor. This account is Instinct; the corpus's
  earlier Guardian 4 material does not apply to it.

[source: findings-log/2026-11-27-display-message-field-semantics/FINDINGS.md]
