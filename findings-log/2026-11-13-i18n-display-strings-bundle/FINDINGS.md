# The NGP alarm display strings are an unauthenticated, digest-stable public asset (2026-11-13)

**Evidence class: OBSERVED.** Fifteen unauthenticated requests — fourteen `GET`, one
`HEAD` — across three hosts, plus offline reading of the bodies they left on disk.

**Requests issued by this pass: 15 of a 20 cap** — 13 on `carelink.minimed.eu`,
1 on `carelink.minimed.com`, 1 on `carelink-support.minimed.eu`. Statuses: **7 × `200`,
8 × `404`** — every 404 is one of §1's absence controls, not a failure. **Delay:** ≥2 s between requests, measured from
one-second-granularity `t_sent` stamps: 14 gaps, floor **2.0 s**, no sub-floor reading.
**Method:** `GET` and one `HEAD`; no `POST`, no `OPTIONS`. **No credential of any kind
was sent, and none is needed for anything below.**

---

## 0. Why this area exists

Two live pages record the same thing as blocked on a token:

- `docs/11-suggested-research-areas.md` line 22, the *Already blocked on a token* table:
  **"NGP alarm-code vocabulary | an authenticated `application` config"**.
- `docs/10-open-questions.md:38`, open §1: **"Not published on any unauthenticated
  surface"**.

Neither is true, and neither has been true for some time. Area DP
(`findings-log/2026-11-11-area-dp-pump-data-plane/`) got as far as establishing *that a
message bundle exists*: it recovered 73 source codes collapsing onto 19 i18n name keys
and stated, correctly for what it fetched, that

> **The alarm-code → human text mapping is not recovered.** The 19 targets are i18n key
> suffixes (`connect.ble.062` etc.); the display strings live in translation bundles not
> fetched here.

It then inherited the repo's standing assumption — that those bundles need a token. They
do not. They are static files on the same host, served to any unauthenticated `GET`, and
the path to them is published in the patient configuration document this repo has been
quoting since 2026-10-08.

**This is the fourth instance of one class**, and the class is the point: *the vendor's
own published client bytes describe the wire vocabulary.* Treatments and markers (area
DP), the pump-data schema (DP), the alias table (area S5), and now the display strings.
Every one of them was filed as token-gated first.

## 1. Method, and the controls that make the negatives mean something

Fifteen requests, ledger in `results.jsonl`, script in `probe.sh`. The four that carry
the finding:

| # | asset | status | bytes | sha256 |
|---|---|---|---|---|
| 1 | `carelink.minimed.eu/crm/ocl/15.5/i18n/ui/app/en.json` | 200 | 137,123 | `a6b8180b87c022d65ae48700d240f5a2a80db3ad9db6b3c8fff3a5c707cd7f9f` |
| 2 | `carelink.minimed.com/crm/ocl/15.5/i18n/ui/app/en.json` | 200 | 137,123 | **same digest** |
| 11 | `carelink-support.minimed.eu/crm/ocl/15.5/i18n/ui/app/en.json` | 200 | 137,123 | **same digest** |
| 10 | `carelink.minimed.eu/patient/v2/configuration/public` | 200 | 6,546 | `9f6cb919bb9abd22d74a66d7bccc555439619b8ab728262b02b12dff9a78f8cd` |

`application/json` on all four. The three i18n bodies are **byte-identical across three
hosts and two TLDs** — `cmp` clean, not merely equal in size.

**Absence controls, all four passing identically.** Every one of these returns
`404`, **196 bytes**, `text/html; charset=iso-8859-1`:

| # | control | purpose |
|---|---|---|
| 5 | `…/ocl/15.4/i18n/ui/app/en.json` | version segment is load-bearing |
| 6 | `…/ocl/15.6/i18n/ui/app/en.json` | …and not a wildcard: 15.6 does **not** answer |
| 7 | `…/ocl/15.5/i18n/ui/app/zz.json` | locale segment is validated, not ignored |
| 8, 9, 12–14 | absent path / absent file / `app.json` / `index.json` / `locales.json` | no directory index, no manifest |

All seven 404 bodies hash to one digest, `80c3fe2ae1062abf…` — the stock Apache
not-found document. **A 404 here is a true absence, not a soft error**, which is what
lets §2's "no manifest exists" be a claim rather than a shrug.

`last-modified: Wed, 26 Aug 2026 13:33:23 GMT`, `etag: "217a3-659f34366cec0"`,
`cache-control: no-cache, no-store, must-revalidate`, `access-control-allow-origin: *`,
`x-cache: Miss from cloudfront`. **The one honest oddity:** request 4 was `HEAD` sent as
`curl -X HEAD`, which makes curl expect a body and log
`end of response with 137123 bytes missing`. The status is a real `200`; the error is a
client-side artefact of `-X` over `-I`. Recorded rather than silently re-run.

## 2. The path is derivable, so `15.5` is not hardcoded

`docs/04` already publishes the pointer. Request 10 re-fetched it:

```json
"personal.crm.settings": { "base.uri": "https://carelink.minimed.eu/crm",
                           "product": "ocl", "version": "15.5" }
"csr.crm.settings":      { "base.uri": "https://carelink-support.minimed.eu/crm",
                           "product": "ocl", "version": "15.5" }
```

So the URL is a **composition of four published values**, not a guessed constant:

```
{personal.crm.settings.base.uri}/ocl/{personal.crm.settings.version}/i18n/ui/app/{locale}.json
```

`product` supplies the `ocl` segment, `version` the `15.5`. A version bump moves the
document without any guess here, and — per controls 5 and 6 — a stale version segment
fails cleanly at `404` rather than serving a different vocabulary. **`15.5` appears
nowhere in this entry as a pinned truth; it is an observed value of a published field on
2026-11-13.**

**There is no manifest.** `i18n/ui/app.json`, `i18n/ui/index.json` and
`i18n/locales.json` all 404. The locale list must be enumerated out of band; that it is
not discoverable *here* is a bounded negative, not a claim that no list exists elsewhere.

## 3. The numeric vocabulary — 63 codes, and no `811`

The full key path is `connect.ble.<code>`, matching the runtime template area S5 found
in the client (`this.translateService.instant(\`connect.ble.${code}\`)`). **63 keys**,
every one a three-character zero-padded string, enumerated in
`alarm-display-strings.tsv`:

```
002 006 007 011 012 024 025 029 037 051 052 057 058 061 062 066 069 073 077 084
100 103 104 105 107 109 110 113 117 130 140
775 776 777 779 780 784 794 795 796 797 801 802 803 805 807 809 810 812 814 815
816 817 819 821 822 823 827 829 832 833 869 870
```

Two structural facts, each checked explicitly because a plausible reading gets them
wrong:

- **There is no `connect.ble.811`.** `810` exists; `811` does not. A gap in an otherwise
  dense 801–823 band. **Do not record `811` as a code** — it is absent, and the nearest
  neighbours make its absence invisible to anyone reading a range rather than the list.
- **Neither `00-1` nor `121` has a key.** Both are area DP's two suppressed codes; the
  absence here is the display-side confirmation of that suppression, and it means
  DP's suppression list and this bundle agree on the exclusions.

### 3a. Ten codes say "Delivery Stopped", not eleven

The `delivery_stopped` column of the TSV flags the literal phrase, which is a string
test, **not** a semantic classification. **10 of 63 codes carry it:**

```
002 007 012 029 037 061 077 130 809 810
```

⚠ **`024` is not one of them**, and a summary of this finding that lists it is wrong.
`024` reads:

```
024  Critical Pump Error. Stop Pump Use. Use Other Treatment
```

That is a *stop-using-the-pump* instruction, which is a different and arguably more
urgent message than a delivery stop, but the phrase is not present and the count is
**10, not 11**. The remaining 52 codes without the phrase are battery, pairing,
notification, sensor and settings lifecycle messages — `006 "Pump Battery Out Limit"`,
`057 "Pump Battery Not Compatible"`, `062 "New notification received from CareLink"`,
`776 "Calibration Error"`, `779 "Recharge Transmitter Now"`.

**Why the count is stated as a string test and not as a severity class:** `docs/05`
already warns that relaying alarms to Nightscout without operator gating is unsafe, and
that argument rests on what a code *means*. "Carries the phrase" is reproducible from
the digest; "means delivery stopped" is an interpretation this pass did not make — and
`024`, which instructs the operator to stop using the pump and seek other treatment, is
the exact case where the phrase and the meaning come apart.

## 4. What it closes — and the cross-check that was worth running

The point of the asset is not 63 strings. It is that **the alias table and the display
bundle were recovered by different passes from different artefacts and they agree**.

Checked against `findings-log/2026-10-14-area-s5-ngp-alarm-vocabulary-static/alarm-code-map.tsv`
(137 raw → 62 canonical):

| check | result |
|---|---|
| s5's 62 canonical codes all have a display key | **62 of 62** |
| s5 canonical set + `073` == this bundle's 63 | **exact set equality** |
| alias pairs where both endpoints have a key | **63 pairs, 63 text-identical** |
| `073` (in the bundle, folded to `011` by s5's table) resolves | `011` and `073` both read *"Replace Pump Battery Now"* |

Checked against area DP's `alarm-code-map.json` (73 raw → 19 canonical):

| check | result |
|---|---|
| DP's 19 canonical name keys all have a display key | **19 of 19** |
| DP alias pairs whose raw key has its own display string | **20 of 20, text-identical** |
| this bundle's codes that DP's table never mentions | **43 of 63** |

**That last row is the finding nobody had.** Area DP's 137-code alias table covers only
**20** of the 63 codes this bundle renders. The other **43** — the whole `100`–`140`
band, the whole `775`–`870` band — are absent from DP's table entirely, so a client
following DP's normalisation table alone resolves 20 of 63 alarm strings and falls
through on the remaining 43. DP's own §4a suppression list names several of them
(`786 787 788 799 806 825 828`, `108 114`) as codes that force
`lastAlarmNameKey = null`, which is consistent with the table being narrower than the
bundle rather than the bundle having grown.

**Classification, stated carefully:** the set relationship is **OBSERVED** — both sides
are digest-pinned files. That the 43 unlisted codes *actually arrive on the wire* is
**INFERRED**, unobserved in both directions, exactly as DP §3 says of its own fields.
What is settled is that the vocabulary is published; what a real 780G sends is still a
token question (successor BD, item 1).

## 5. Two more vocabularies in the same body

The bundle is not only alarm codes, and the two siblings are worth recording because
neither appears anywhere in this repo:

- **`cp-notifications.alarm.<NAME>` — 117 symbolic names**, full list in
  `symbolic-alarm-names.tsv`. `INSULIN_DELIVERY_STOPPED`, `SUSPEND_ON_LOW`,
  `CRITICAL_PUMP_ERROR`, `AUTO_SUSPEND_LIMIT_REACHED`, `INSTINCT_APP_CLOSED`,
  `LOST_PUMP_COMMUNICATION`, `SMARTGUARD_DELIVERY_TIMEOUT`, `UNRESPONSIVE_USER`.
  This is a **semantic** vocabulary where `connect.ble.*` is a **numeric** one, and the
  two are not a mapping: 117 symbolic names against 63 numeric codes.
- **`cp-notifications.alarmGroup.<NAME>` — 11 groups**: `LOW_ALERTS`, `HIGH_ALERTS`,
  `INSULIN_DELIVERY_STOPPED`, `INSULIN_ALERTS`, `SENSOR_ERRORS`, `DEVICE_STATUS`,
  `AUTO_MODE`, `SMARTGUARD`, `REMINDERS`, `REMINDERS_ALERTS`, `ADVANCED_ALERTS`
  (`ADVANCED_ALERTS` displays as *"Status Messages"*, not as its name). Full list in
  `alarm-groups.tsv`.
- **140 bare top-level tokens, keyed by the token itself** — `SENSOR_OFF="Sensor off"`,
  `WARM_UP="Warm up..."`, `CHECK_CONN="Sensor disconnected"`,
  `MEDICAL_DEVICE_BAD="Pump weak signal"`, `SG_BELOW_40_MGDL="Below 40 mg/dL"`,
  `SG_ABOVE_400_MGDL="Above 400 mg/dL"`, `BELOW_40_MMOL="Below 2.2 mmol/L"`. These are
  the `systemStatusMessage` / sensor-state display strings; **no `systemStatus`-prefixed
  family exists** (0 keys), so a search for the wire field name finds none of them —
  the same mistake, one level down, that made the alarm vocabulary look absent.

**12 display texts are shared between a numeric code and a symbolic name**
(`051`/`BOLUS_STOPPED` = "Bolus Stopped"; `103`/`CHECK_BG` = "BG Check Reminder";
`775`/`CALIBRATE_NOW`; `777`/`CHANGE_SENSOR`; `780`/`LOST_SENSOR_SIGNAL`;
`797`/`SENSOR_CONNECTED`; `802`/`LOW_SENSOR`+`LOW_SG_ALERT` = "Low Sensor Glucose";
`816`/`HIGH_SENSOR`+`HIGH_SG_ALERT`; `869`/`CALIBRATION_REMINDER`; `107`;
`109`; `117`). Recorded as OBSERVED. **No claim is made that these are the same code by
another name** — string equality is not identity, and two vocabularies converging on one
English phrase is exactly what a translation bundle does.

## 6. Localisation: the code set is invariant, the key set is not

`fr.json` (141,577 B, `63ec83ed30f03e31…`) and `de.json` (130,541 B, `718af45f978af24d…`):

| | keys | `connect.ble.*` | code set |
|---|---|---|---|
| `en.json` | **1,876** | 63 | baseline |
| `fr.json` | 1,603 | 63 | **identical** |
| `de.json` | 1,603 | 63 | **identical** |

**All three agree on the 63 codes, name for name.** The 273 keys present in `en` and
absent from `fr`/`de` are UI strings, not alarm codes — the alarm vocabulary is fully
translated in all three. Sample: `024` = *"Erreur de pompe critique. Arrêter d'utiliser
la pompe. Utiliser un autre traitement"* (fr), *"Kritischer Pumpenfehler. Verwendung der
Pumpe einstellen. Andere Behandlung verwenden"* (de).

**This is what makes the asset a *display* source rather than a code list**: a client
needs the locale bundle for the operator's language, and the code set it indexes is
stable across locales, so one fetch per locale fully covers the vocabulary. **The 63 is
a property of the message catalogue, not of English.**

## 7. Corrections this pass owes to the record

### 7.1 `docs/10-open-questions.md:38` — the NGP alarm-code vocabulary (open §1)

Its class is `OBSERVED negative` and its claim is *"Not published on any unauthenticated
surface"*. **Refuted.** The vocabulary, its 63 display strings and two further
vocabularies are one unauthenticated `GET` away. The row's *evidence* was sound — 28
route-shaped key names did 404 — but the answer was never a route, which is the same
diagnosis area DP already recorded for the same row.

A dated Correction is added in the cell; the original wording is **kept**, per this
repo's rule for claims that were true when made.

### 7.2 `docs/10-open-questions.md:80` — the same question in §2 "Searched and closed"

> **Firm negative** — 28 key names across both rounds, all 404, under case-sensitivity
> and 401-vs-404 controls; negative in the patient config, the clinic bundle, all 225
> lazy chunks (body-verified 2026-10-13), and the patient bundle

Every clause of the measurement is still true — the vocabulary is genuinely absent from
all 225 chunks, which is *why* area S5 searched for a definition and found none. What is
false is **"firm negative" as a verdict on publication.** A corpus that excludes the
i18n bundles cannot settle whether the i18n bundles define the keys. Dated correction
added; the measurement stands.

### 7.3 `docs/11-suggested-research-areas.md:22` — the *blocked on a token* table

Row **"NGP alarm-code vocabulary | an authenticated `application` config"** is removed
from that table and moved into the body's closed/answered narrative, with a dated note
saying why: it is not blocked on a token, it was never blocked on a token, and the
table's own premise ("these need an authenticated response on a real account") is false
for it.

### 7.4 `docs/11` area BD, item 2 — "the display text"

BD was minted by area DP with three items and called item 2 *"The display text"*,
closing on *(b) the translation bundles are fetched at zero token cost*. **Item 2 is now
answered, by route (b), at one request.** BD's remaining item 1 (population) is untouched
and stays a token question.

## 8. What is not claimed

- **That a 780G sends any of these codes.** No live payload exists for this. The
  vocabulary is published; its population on the wire is unobserved in both directions.
- **That `delivery_stopped` is a severity classification.** It is a substring test over
  63 strings, and §3a exists because the tree makes it easy to miscount.
- **A cause for the absence of `811`.** Only that no `connect.ble.811` key exists in a
  1,876-key body whose neighbours 810 and 812 both do.
- **That these are the *only* CareLink i18n bundles.** Three hosts and one product were
  checked. The `cua`/`pow` split `docs/04` records for the clinic portal implies sibling
  bundles under other products; none was probed, and the derivation in §2 names only the
  patient pointer.
- **A locale list.** No manifest answered (§2), so "en, fr, de exist" is what was
  fetched, not an enumeration of what ships.
- **That the bundle is version-stable.** `last-modified` is 2026-08-26 and the digest is
  pinned here, but a version bump changes the path, not the digest — §2's derivation is
  the durable part, and the digest is the tripwire for 15.5 specifically.

## 9. The general lesson, and it is the fourth time

The repo's most expensive recurring error is not a wrong measurement. It is **a negative
scoped to a corpus, quoted later as a fact about the vendor.** "Not published on any
unauthenticated surface" was true of 28 probed route names, then of 225 lazy chunks,
then of 211 more — and false of a static file on a host this repo fetches every week.

The tell is grammatical. A negative that names its corpus (`0 in the 225 chunks`) is a
measurement and survives. A negative that names **the world** (`not published on any
unauthenticated surface`) is an inference wearing an observation's clothes, and it is
the sentence that costs four months — as area DP wrote about `blocked on a real 780G
account`, which was wrong on the same principle.

**And the cheap check that was never run:** the pointer was already in `docs/04`. The
URL was four published values concatenated. The whole area cost 15 requests, 4 of which
carry the finding.
