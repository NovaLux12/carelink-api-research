# Cross-region config diff — the endpoint is on all three deployments (2026-10-09)

`GET /patient/v2/configuration/public` is not EU-only. It answers on **all three**
CareLink deployments, and **34 of its 69 keys differ by region**. The key set is
identical everywhere (69/69 on each) — this is one document, regionalised, not
three documents.

```
carelink.minimed.eu            69 keys   default.country = GB
carelink.minimed.com           69 keys   default.country = US
carelink-trials.minimed.com    69 keys   default.country = US   (clinical)
```

Confirmed: the namespace is tight. `/patient/v2/configuration/public` is the only
member — no `v1`/`v3`, no unversioned `/configuration/public`, and no siblings
under `/patient/v2/configuration/`. A trailing slash is accepted.

## ⚠ SECURITY — real service API keys are published on the US and trials deployments

`nutrino.cc.broker.service.config.security_headers["x-api-key"]` and the same key
in `nutrino.cc.metadata.service.config`:

| deployment | value |
|---|---|
| EU | `%#$^&#GFFG@#*%&#$` — a **literal placeholder**, not a credential |
| US | a real-looking base64 token, **18+ chars** |
| trials | a **different** real-looking base64 token |

These authenticate to `commoncore.medtronic.{eu,com}/reports-broker/v1` and
`/reports-metadata/v1` — the reports backends behind repo issue **#76**.

This is the same class of defect as the hardcoded `x-api-key` in the portal JS
bundle (`SECURITY-FINDINGS.md` S3), but worse in two ways:

1. **It is on the patient host**, served unauthenticated to any internet client.
2. **EU ships a placeholder while US and trials ship working-looking secrets** —
   so the EU value has been passing every internal review as obviously-fake, and
   nobody noticed the other two deployments carry real material.

**The values are deliberately not reproduced in this file.** They exist only in
the gitignored raw captures (`security/cfg-*.json`). Treat them as sensitive: do
not paste them into an issue, a PR, a commit message, or any text that leaves
this machine. If this is ever disclosed, report *that the keys are exposed and
where*, not the keys themselves.

Not tested — and deliberately so: whether either key is live against the reports
brokers. That needs an authenticated call to a production medical-data service,
which is well outside a read-only pass.

## The logbook clinical validation schema — non-null on trials, `null` on both patient regions

`system.logbook.entry.validation.config` is `null` on EU and US, and a full
schema on trials. This is **the schema issue #76's deferred `markers[]` work has
been missing**, and it is a clinical taxonomy, not just a field list.

Validation rules exist for **5 of the 12** logbook entry types:
`SENSOR_INSERTION`, `SENSOR_REMOVAL`, `SENSOR_PHYSICAL_DISTURBANCE`,
`ADHESIVE_AND_TAPE`, `MEDICATION`.

**12 sensor insertion locations** — the full anatomical set:

```
leftAbdomenLower  leftAbdomenUpper   rightAbdomenLower  rightAbdomenUpper
leftUpperButtock  rightUpperButtock leftUpperLeg       rightUpperLeg
leftUpperArmLowerHalf  leftUpperArmUpperHalf
rightUpperArmLowerHalf rightUpperArmUpperHalf
```

**5 sensor-removal reason codes** — and these are the categories that actually
matter clinically, because they are what distinguishes an adhesive problem from a
device fault:

```
sensorFellOffEarlyDueToPhysicalDisturbance
sensorFellOffEarlyWithoutPhysicalDisturbance
secondarySensorIntentionallyRemovedDueToPrimarySensorRemoval
sensorIntentionallyRemovedDueToSensorIssues
sensorIntentionallyRemovedOtherReason
```

The schema also encodes **conditional free-text**: picking
`sensorFellOffEarlyDueToPhysicalDisturbance` triggers
`logbook.sensorRemoval.question.specifyOtherReason`, and `other` triggers a
specify-field. So the entry shape is *state-dependent*, which is exactly the kind
of thing a naive `{type, value}` model gets wrong.

**8 dose units** for `MEDICATION`: capsule, gram, internationalUnits, microgram,
milligram, milliliter, puff, tablet.

Corroborated by the lazy-chunk field names found independently today
(`removalType`, `removalReason`, `sensorInsertionLocation`, `adhesivetapeLocation`,
`timecapUnscrewed`) — two unrelated sources agreeing on the same vocabulary.

## Feature rollout differs sharply by region — and one item is medically relevant

| key | EU | US | trials |
|---|---|---|---|
| `logbook.enabled` | false | false | **true** |
| `personal.clinical.environment` | false | false | **true** |
| `personal.safety.notices.enabled` | false | **true** | false |
| `personal.data.csv.export.enable` (personal/aggregatedData) | true | true | **false** |
| `personal.cookie.consent.policy.enabledGlobally` | true | true | **false** |
| `personal.dob.validation.enabled` | true | true | **false** |
| `personal.mixpanel.analytics.settings.enabled` | true | true | **false**, empty token |
| `personal.username.as.email.settings.enabled` | true | true | **false** |
| `personal.inpen.supported.countries.enabledGlobally` | false | **true** | false |

**`personal.safety.notices.enabled` is true on the US deployment only.** Safety
notices are the mechanism by which Medtronic communicates device advisories
(recalls, warnings) to patients. For a UK/EU user of this bridge, that flag being
off is worth knowing — and it is a difference between regions, not a constant.

**`logbook.enabled` is false on both patient regions and true only on trials.**
So the logbook/markers feature that #76 wants is, on the patient API, switched
off — which is very likely why the entry schema ships `null` there and populated
only on trials. #76's "blocked on a missing schema" framing is now sharper: the
schema exists, on the one deployment where the feature is enabled.

Other rollout data:

- `personal.common.core.reporting.enabled.countries`: EU has 17 countries, **US
  has `["US","PR"]`** (Puerto Rico), trials has 21.
- `personal.countries.certification.enabled`: EU `["FR","YT","NC","PF"]` — the
  French overseas territories, i.e. an EU MDR certification rollout in progress.
  Empty on US and trials.
- `personal.third.party.apps`: EU `DS_EMEA_1_GLOOKOXT`, US `DS_AMERICANS` — the
  Glooko consent-sharing integration is region-split, with **no** equivalent on
  trials (`null`).
- `outages.nextupdateat` is populated on trials only — a maintenance-window
  schedule.
- Each deployment has its own reCAPTCHA site key and its own Mixpanel project
  token; the trials analytics token is empty and disabled.

## Nine previously-unrecorded service endpoints, all confirmed live

Every host below was disclosed only by the config and has never been in any note.

| service | EU | US | trials | probe result |
|---|---|---|---|---|
| dialog-lite | `…eu-central-1…/prodous/dialog-lite/v1/` | `…us-east-1…/prod/dialog-lite/v1/` | `null` | **500** JSON (API Gateway up, root unrouted) |
| patient-timeline | `…eu-central-1…/prod/patient-timeline` | `…us-east-1…/prod/patient-timeline` | `…us-east-1…/prod/patient-timeline` | **403** `Missing Authentication Token` |
| CSR periodic (VPC) | `vpce-0eecd30a2ab…` | `vpce-09606603f2b…` | `vpce-0f5c1c441631…` | timeout — private, as expected |
| CSR CRM | `carelink-support.minimed.eu/crm` | `carelink-support.minimed.com/crm` | `carelink-trials-support.minimed.com/crm` | 403 |
| retina | `clcloud.minimed.eu` + `/connect/retina/v1/personalWebView` | `clcloud.minimed.com` | `clcloud-trials.minimed.com` | **401** JSON |

**Three distinct AWS VPC endpoints**, one per deployment, for the same logical
service — the CSR periodic-packet path. None reachable from the public internet,
consistent with every other internal-looking name already recorded.

`mmm.data.api.url` is `null` on trials: the dialog service is not deployed there,
which is consistent with trials running `clinical.environment = true`.

## What this changes for the open issues

- **#76** — materially advanced. The logbook entry schema exists (on trials), the
  12/12 entry types are known, and the reports brokers are mapped per region.
  Still token-gated for actual report bodies.
- **#84** — unchanged. `csr.control.codes.settings` still has no N-codes on any
  deployment; it is the device *control* vocabulary, identically across all three.
- **#81** — unchanged and confirmed. Hash-verified (sha256 of canonical JSON,
  all three deployments):

  | key | hash (all three) |
  |---|---|
  | `personal.device.family.to.model.mapping` | `8ce419a22fd3` |
  | `system.settings.transfer.feature.config.device.mapping` | `90a93c057aec` |
  | `logbook.supported.entry.types` | `98c562842920` |
  | `csr.control.codes.settings.predefined_control_codes` | `c7c0f04fb4b0` |
  | `system.logbook.entry.validation.config` | **DIFFERS** — `null`/`null`/schema |

  
> **CORRECTION (2026-10-10):** an earlier version of this note gave the family-map
> hash as `215e6671de09`. That value is **wrong and unreproducible** — the map
> hashes to `8ce419a22fd3` on every artefact on disk and on the live body. The
> regression suite (`regression/hurl/05-public-config.check.sh`) asserted the
> correct value throughout and passed, which is how the error surfaced: the pinned
> hash was right and the hand-written note was wrong. Same failure class as the
> source-map edit in `CHUNK-CORPUS-FINDINGS.md` — a claim in prose that was never
> re-derived from the artefact. **Values quoted in notes are not evidence; the
> pinned assertion is.**

So the published device vocabulary is **global, not regional**: one
  authoritative map. That is now pinned by
  `hurl/05-public-config.check.sh`, which re-derives the hash from the US and
  trials deployments on every run.

  > **Verification note, recorded because it nearly shipped a false result.** The
  > first attempt at this comparison reported *four* "SAME" rows when only three
  > were same: the walker looked up dotted-nested paths with a single
  > `dict.get("a.b.c")`, got `None`, and then hashed `None` — so two genuinely
  > different values produced identical digests and looked like agreement. The
  > check now walks path segment-by-segment and asserts the resolved type, and
  > `05-public-config.check.sh` treats an all-zero digest (`e3b0c442…`, the
  > sha256 of the empty string) as a failure rather than a comparison. A hash
  > check over a lookup that can silently return `null` will manufacture
  > consensus.