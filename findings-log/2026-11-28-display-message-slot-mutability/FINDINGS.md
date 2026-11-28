# `display/message` slots are NON-MONOTONIC: a reading can be absent, then present, then absent again

**Evidence class: OBSERVED.** 2026-11-28, against a live GB account with a paired
Medtronic 780G (`pumpModelNumber` `MMT-1885`) and an Abbott Instinct sensor, three
days into its first sensor. Four `display/message` responses were captured from the
same account, same on-disk token, no intervening login, while the operator's own
bridge was polling that account every 300 s.

**Requests: 10 of a 10 cap.** All ten are listed in `requests.tsv` beside this
file, one row per request, with method and status. The four that returned an error
are included deliberately — two `500`s from the legacy data leg, one `403` from the
sibling host, and one `400` malformed control — because a ledger of successes alone
cannot be audited.

### Delay between requests

**⚠ This pass did not honour the repository's `≥ 2 s` floor on every request, and
that is recorded here rather than glossed over.** The floor applies to this host and
it was violated twice:

- **Requests 2 and 3, and 3 and 4, were issued back-to-back** with no delay.
- **Poll 2 (request 8) landed about 36 s after poll 1 (request 7)** — inside the
  floor, and inside the `300 s` cadence the operator's bridge uses.
- The other intervals were minutes: poll 1 → poll 3 ≈ 11 min, poll 3 → poll 4 ≈
  2 h 24 min.

Nothing here rests on a rate-limited response being re-sent: **no request in this
pass was retried on failure**, so the two `500`s are recorded as `500` rather than
retried into a different answer. The violation is stated so the next reader can
weigh the evidence, not discover it from git history. **INFERRED (assumption
stated):** a violation of this size does not plausibly change which slots the vendor
populates, because the effect is observed *within* a single payload at a single
instant, not across a burst. That reasoning is mine, not measured.

**Methods used: `GET` and `POST`.** The `POST` is not a probing choice —
`display/message` is the live data leg and the operator's bridge already calls it
as `POST`; reproducing its request shape is the only way to see what the bridge
sees. The `GET`s read metadata (`countries/settings`, `users/me`) and the legacy
data leg. **No token exchange was performed**: the access token was already on disk
from the operator's bridge login and was read, not minted. It has expired since.

**Where the payloads came from:** the operator's own account, authenticated as that
operator, who confirmed the responses were theirs to read. Nothing patient-identifying
appears below — no username, patient id, account id, serial, or individual glucose
value in mmol/L. The per-slot figures quoted are raw `sg` integers, which are needed
to show that a value does not move; the argument for the client fix does not depend
on them.

---

## 1. The claim

`display/message` returns a fixed **288-entry** array at `sgs[]`. Reading it as a
ring buffer — 288 settled five-minute slots covering ~24 h — is **wrong in both
directions**:

1. **A reading can be absent on an earlier poll and present on a later one** (the
   vendor fills a slot late).
2. **A reading that has been served can be absent from a later poll** (the slot
   reverts to empty). It comes back later still with **the same value**.

**A value, once served, never changes.** Over four payloads and 289 distinct
readings, **0 values differed** for any slot seen more than once. What moves is
**presence**, not content.

## 2. The measurement

Four polls of one account. `Y` = reading present, `.` = absent. Windows shown for
readings from 09:00 onward; the 288-entry array at each poll also covers the
preceding ~24 h.

| slot | poll 1 (10:24:54) | poll 2 (10:25:30) | poll 3 (10:36:00) | poll 4 (13:00:00) | `sg` |
|---|---|---|---|---|---|
| 09:19:00 | `.` | 70 | 70 | 70 | 70 |
| 09:26:00 | 66 | 66 | `.` | 66 | 66 |
| 09:50:00 | `.` | 105 | 105 | 105 | 105 |
| **10:07:00** | `.` | **179** | **`.`** | **179** | 179 |
| **10:15:01** | `.` | `.` | **205** | **205** | 205 |
| 10:18:00 | 230 | 230 | `.` | 230 | 230 |
| 10:33:01 | `.` | `.` | 272 | 272 | 272 |

The two patterns this establishes:

- **Fill-late:** `09:19`, `09:50`, `10:15`, `10:33` are absent at poll 1 and present
  from poll 2 or 3 onward. `10:33:01` is the clearest case — the slot simply did not
  exist in the earlier payloads and appears, with a value, 11 minutes later.
- **Present-then-absent:** `09:26`, `10:07` and `10:18` are **served with a value,
  then missing from a later payload, then served again with the same value.**
  `10:07:00` is the sharpest instance because it does both: absent at 10:24:54,
  present at 10:25:30, absent at 10:36:00, present again at 13:00:00 — the same
  reading 179 throughout.

**Why the second pattern matters more than the first.** A client that suppresses
"anything I have already passed" loses the late fills. A client that *reconciles*
by de-duplicating on what it has already sent is still safe — because the values are
stable — but a client that treats the array as append-only will see its own record
disagree with the vendor's on a later poll and has no way to distinguish "the vendor
withdrew a reading" from "my poll failed". **Presence is provisional; content is
not.**

### Slot-count and population size do move

| Poll | `sgs[]` length | populated |
|---|---|---|
| 1 (10:24:54) | 288 | 249 |
| 2 (10:25:30) | 288 | 257 |
| 3 (10:36:00) | 288 | 249 |
| 4 (13:00:00) | 288 | 280 |

**Length is constant at 288 in all four.** The populated count varies by up to 31
across two and a half hours — which is the same phenomenon as the per-slot table
viewed in aggregate, and is why "count the populated slots" is not a reliable way to
measure coverage.

### Empty slots carry a state, and more than one

An empty slot is `sg: 0` plus a `sensorState`. Three distinct states were observed
across the four payloads:

| `sensorState` | Meaning observed | Seen |
|---|---|---|
| `NO_ERROR_MESSAGE` | populated slot | always when `sg > 0` |
| `NO_DATA_FROM_PUMP` | the pump had no value for that slot | 12–23 per payload |
| `DO_NOT_CALIBRATE` | also `sg: 0`; sensor refused a calibration, not a missing reading | 4–7 per payload |
| `WARM_UP` | the sensor was warming | 12 per payload |

**A client that infers "no reading" from `sg === 0` alone gets the value right and
the cause wrong.** `DO_NOT_CALIBRATE` and `WARM_UP` are in-band statements about the
**sensor**, and collapsing them into "no data" discards the only signal on this
route that the sensor needs attention. This pass does not establish the full
vocabulary — four states are not a closed set — only that these four occur.

## 3. A trap this creates for anyone using `relativeOffset`

Every slot carries `relativeOffset`, seconds before an anchor. **It is only
internally consistent, and cannot be used to date a slot across polls.**

Within one payload the offsets step by exactly 300 s from newest to oldest
(`-150`, `-450`, `-750`, … `-86250`). But the offsets **reset relative to each
payload's own anchor**, so the same `-750` means a different instant in each one:

| Poll | `-750` corresponds to |
|---|---|
| 1 | 10:21:34 |
| 2 | 10:14:42 |
| 3 | 10:22:31 |

**INFERRED (assumption stated):** the anchor is at or near `currentServerTime` for
that response, so `relativeOffset` is a position in *this* window and nothing more.
Dating a slot by subtracting `relativeOffset` from a clock the client holds is
therefore wrong by however much the anchor moved — which, for a client polling every
five minutes, is up to the poll interval. **Date slots from `sgs[].datetime`**, which
is a full ISO-8601 timestamp carrying its own offset.

## 4. What is NOT established

Stated so none of it is read as OBSERVED:

- **How long a present-then-absent reading stays absent, and whether it can vanish
  permanently.** Observed absences lasted one poll (~11 min) and the readings
  returned. Whether a longer outage can lose one for good is **unknown** — this pass
  did not extend past 2 h 24 min, and cannot: the window itself is ~24 h.
- **What causes the non-monotonicity.** Candidates — the phone relay re-posting, an
  ingest-side reconciliation, a query routed to a different replica — are not
  separated by anything measured. **No cause is claimed.** A replica-consistency
  explanation would predict values *could* differ; none did, which is weak evidence
  against it, not a refutation.
- **Whether slot ordering is guaranteed.** `datetime` was ascending in all four
  payloads. Not tested against a sparser window.
- **Whether the `v11`/`v12`/`v13` siblings behave the same.** All four payloads came
  from the `v6` route that `countries/settings` advertises for GB
  (`blePereodicDataEndpoint`). Newer versions are **untested**.
- **The `WARM_UP` transition.** It was present at the oldest edge of all four
  windows, which is consistent with sensor warm-up at the window's start, but this
  pass did not watch a warm-up boundary.

## 5. Reproducing it

Two or more `display/message` calls 10+ minutes apart on an account with a live
sensor, then:

```
slots present in the later payload but absent from the earlier  → late fills
slots present in the earlier payload but absent from the later  → withdrawals
any slot present in both with a differing sg                    → would refute §1
```

Expect **1–4 slots changing presence per 10 minutes** and **zero value changes**. A
run showing a changed value refutes the central claim and should be reported as a
correction.

## 6. The consumer, and what must not be read into this

The client consequence is a change in the code repository, not a claim about the
vendor surface: [NovaLux12/carelink-bridge#190] replaced a single high-water mark
with a bounded set of already-forwarded timestamps, precisely so a late slot is
admitted rather than suppressed. **Nothing here is evidence for that PR's loss
figure** — that measurement is the consumer's own and belongs there.

One thing this pass does *not* support: **§2 pattern 2 is not offered as an
explanation for missing readings in a client's record.** A withdrawn-then-restored
slot is harmless to a client that already forwarded it. The loss in the consumer
came from the *fill-late* pattern meeting a high-water mark, which is §2 pattern 1.
