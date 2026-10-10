# Cumulus-v2 spike: Instinct/Simplera-era data path (2026-08-22)

Design notes for the newer "Cumulus" API. Trigger: US Instinct-sensor users report
login succeeds but data downloads fail — m0rt4l1n in xDrip discussion #4318 states
Instinct sensors use a new API ("Cumulus") not yet implemented by xDrip.
https://github.com/NightscoutFoundation/xDrip/discussions/4318 (Jan 2026, 17 comments).

## Background

- Current Auth0+cumulus-**v13** track (discovery `v13/discover/android/3.6`, our pin)
  serves the CareLink Connect / MiniMed Mobile 3.x app family and the 780G+Guardian
  path that ondrej1024 PR #35 / xDrip #4320 / HA PR #122 all implement.
- Discovery cells `android/{4.0,4.1,4.2,5.0}` return cumulus **v2** + CareLink API v1 +
  PDE v1 configs with NO Auth0 and no CLINICAL region. No shipped store app is ≥4.x
  (max: CareLink Connect US 3.8.1, Jun 2026), so these cells serve unreleased builds or
  legacy-compat config. [INFERENCE] The cumulus-v2 shape may be the transport the
  Instinct-era "Cumulus" API rides on.

## Known endpoints

| Family | Base | Evidence |
|---|---|---|
| Discovery | `clcloud.minimed.{com,eu}/connect/carepartner/v13/discover/android/{X.Y}` | live 200 2026-08-22 |
| Cumulus v13 | `clcloud.minimed.com/connect/carepartner/v13` (baseUrlCumulus) | discovery cell |
| Cumulus v2 | same host `/connect/carepartner/v2` (4.x cells) | discovery cell |
| PDE | `/connect/pde/v3` (v13 track) vs `/connect/pde/v1` (v2 track) | discovery cell |
| Display/messages | `GET {baseUrlCumulus}/display/message` | ondrej1024 carelink_client2.py:221; doc/carelink.md |
| cloudServer() calls in xDrip | `patient/connect/data`, `patient/m2m/connect/data/gc/patients/{username}` | CareLinkClient.java ~626,725 |

## Expected auth

- Same Auth0 token infrastructure is the only attested path: issuer
  `carelink-login.minimed.{eu,com}`, audiences `carepartner.patient.{ous,us}` REQUIRED,
  empty client_secret, scope `profile openid offline_access`, expires_in 10,800s.
  Sources: SSO config JSONs (live 2026-08-22); ondrej1024 PR #35 thread.
- [INFERENCE] Whether the Instinct Cumulus data plane accepts the same
  `carepartner.patient.*` audience token or mints a different one is UNKNOWN publicly;
  assume a distinct audience/scope until disproven on real hardware.
- device_code grant rejected for these client_ids; PKCE advertised (S256/plain).

## Message shapes known publicly

- Legacy display/message protocol documented in ondrej1024 doc/carelink.md
  (https://raw.githubusercontent.com/ondrej1024/carelink-python-client/main/doc/carelink.md).
- Everything else (Instinct sensor payload schema) is NOT public. No third-party client
  implements the Instinct Cumulus data path as of 2026-08-22 (checked: xDrip master,
  ondrej1024 client2, nightscout-connect minimedcarelink source).

## Gap list ranked by validation-day risk

1. **Data-plane unknown** — Instinct sensor payloads: zero public schema. Highest risk;
   needs real-device capture day one.
2. **Audience/token scope for the Cumulus data plane** — untested; probe with captured
   token before assuming parity with carepartner.patient.*.
3. **PDE v3 vs v1 semantics** — push-data endpoint differences undocumented.
4. **Region routing** — 4.x cells lack CLINICAL; irrelevant for personal use but signals
   config-axis divergence.

## Fork needs when maintenance resumes (Nov 2026)

1. Dynamic discovery resolution (stop trusting hardcoded cell beyond the pin assertion).
2. Pluggable baseUrlCumulus/baseUrlPde transports so v13/v2 backends are swappable.
3. Secret-less refresh already satisfied; keep asserting NO client_secret (test landed).
4. Treat 401 `{"error":{"type":"InvalidToken","group":"AUTH"}}` as refresh trigger
   (covered by reliability tests landed 2026-08-22).
