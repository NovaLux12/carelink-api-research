# Open-source ecosystem parity (observed 2026-07-21, public sources only)

## Current state of the local bridge

- Interactive browser OAuth + persisted `logindata.json`, then Bearer.
- Resolves EU/US to `carelink.minimed.eu` / `.com`.
- Hardcodes `/patient/users/me`, `/patient/monitor/data`, `/patient/connect/data?...msgType=last24hours`, `/patient/m2m/links/patients`. Obtains `blePereodicDataEndpoint` from country settings.
- Patient flow probes `monitor/data`, detects BLE from `deviceFamily || medicalDeviceFamily`, then posts to the discovered BLE endpoint; else accepts monitor data or falls back to legacy connect data.
- Care-partner flow selects first linked patient unless configured, probes monitor data, tries endpoint versions 13, 11, 6, 5.
- 3-attempt retry, deterministic 2/4-second waits (third never reached because attempt 3 throws first).
- No jitter. 401/403 forces refresh on next attempt.
- Transform exports SGV + pump or Guardian status. Drops everything when device-update age > 20 minutes.
- Does NOT transform markers, boluses, fingersticks, or notifications.
- Local retry only waits 2s and 4s; the comment's 8s is unreachable.

## Auth/endpoint parity vs active Python client (ondrej1024/carelink-python-client)

1. Python current executable constant: `CARELINK_CONFIG_URL = "https://clcloud.minimed.eu/connect/carepartner/v13/discover/android/3.6"`. Source changelog: 2023-12-28 initial, 2024-04-11 valid-data check, 2024-11-19 discovery bump, 2025-02-11 v3.3, 2026-01-03 fix for new Auth method (by m0rt4l1n), 2026-07-05 data format adaptation. Client library VERSION 1.4.
2. Python supports two discovery-selected login families. Auth0 path: authorization-code exchange. Non-Auth0 path: initialize device credentials, create PKCE state/challenge, browser social login, generate 2048-bit RSA key and CSR, register device, receive `id-token` + `mag-identifier`, exchange assertion, persist `client_secret` and `mag-identifier`. Every user/patient/data call and refresh conditionally sends `mag-identifier`; refresh also conditionally sends `client_secret`. Local `LoginData` and refresh request contain neither, and the request pipeline never sends `mag-identifier`. Accounts/regions whose discovery selects the non-Auth0 configuration will fail in this app. The 2026 change suggests this is an active compatibility boundary.
3. Endpoint architecture diverges. Python derives regional `baseUrlCareLink` and `baseUrlCumulus` from discovery, then calls `${baseUrlCareLink}/users/me`, `/links/patients`, and `${baseUrlCumulus}/display/message`. The source comment resolves these to the `/api/carepartner/v2/...` and `/connect/carepartner/v11...` families, while current constant is v13. Local hardcodes the older `/patient/*` web family and only discovers the BLE display endpoint through country settings. xDrip independently hardcodes `connect/carepartner/v13/display/message`, but also retains the old web-family endpoints.
4. Python token validity uses JWT expiry with a 10-minute margin and retries a 401/403 once after refresh. Local now matches both principles (10-minute margin and forced refresh on 401/403), an improvement over domien-f upstream. Python additionally propagates `client_secret` and `mag-identifier`; local does not.
5. MFA is unsupported: Python README says CareLink MFA is not supported. Local types expose `mfaRequired` / `mfaEnabled`, but no full MFA flow was observed.

## Device / BLE parity

- domien-f upstream PR #2 (2026-06-11) fixes empty patient data by checking `deviceFamily` as well as `medicalDeviceFamily`. Local includes and tests this fix and expands detection to strings containing `BLE` or `SIMPLERA`.
- xDrip has substantially richer device routing: BLE from recent uploads for patients, patient-list metadata for care partners, then monitor data; treats both BLE and CC device indicators as display-message candidates. Otherwise routes Guardian multi-follow through M2M and Guardian single-account through last-24-hours. Local relies mainly on monitor payload family strings and does not inspect recent-upload or linked-patient device metadata.

## Data schema parity

- Local and nightscout-connect share foundational schema: `sgs[]` entries with `sg`, `datetime`, `kind`; trend mapping; `activeInsulin.amount`; reservoir; pump/conduit battery; sensor calibration and range status. Local improves timestamps and supports `reservoirAmount` fallback.
- xDrip processes additional observed response families: `markers` for finger BG, meal/carbs and insulin; `notificationHistory.activeNotifications` and `.clearedNotifications`; `lastAlarm`; pump communication state; device-family predicates. It deduplicates glucose by timestamp tolerance, rejects future/zero timestamps and zero SG, and explicitly refuses NGP data when pump communication is down because time may be wrong.
- nightscout-connect already has conversion functions for markers into Nightscout treatments (meal bolus, correction bolus, fingerstick). Its README roadmap still describes Medtronic treatments/profiles/full device status as unfinished — its schema code is reference, not evidence of a complete supported contract.
- Local stale-data behaviour drops both SGV and device status after 20 minutes. xDrip filters individual invalid readings and refuses a specific unsafe pump-disconnected condition. Recommended: preserve a device-status/health signal while suppressing stale glucose, and add per-entry validation.

## Retry/resilience parity

- Local config still accepts `CARELINK_MAX_RETRY_DURATION`, but local client's `maxRetryDuration` is not used by `fetch`; it always makes three attempts.
- nightscout-connect uses an explicit state-machine architecture and a backoff helper with exponential slots; its helper defaults to deterministic maximum-slot timing unless random-slot mode is enabled. The merge order `{...config, ...defaults}` also means defaults overwrite caller values — pattern not worth copying without correction.
- Local refreshes stale JWTs and forces refresh after 401/403, but deletes the token file after any refresh exception. Recommended: classify permanent auth failures separately from transport/5xx failures; honour Retry-After, add jitter, use capped exponential delay, use status-aware retry.

## Breakages and recency

- nightscout/minimed-connect-to-nightscout: deprecated, says it would be archived 2026-03-31 in favor of nightscout-connect. Latest npm release 1.5.8 (~1.3k weekly downloads). Open issues document CareLink breakage categories: reCAPTCHA EU (#47, 2023-09-28), EU 504 (#44), care-partner 400 and v6→v5 hotfix (#39), MFA (#34), timezone errors (#30), US 770G compatibility (#11).
- ondrej1024/carelink-python-client: open issue #36 "No longer works" created 2026-07-07 with no comments. Same date as auth merge `29051ca`; chronology alone does not prove resolution. 2026-07-05 commit adapted "time until next reading" to a new data format in `carelink_client2_proxy`.
- domien-f upstream: only one open BLE PR (#2), opened 2026-06-11, still open. Upstream main retains default-on proxy rotation and has only one non-proxy fetch attempt; the local fork appropriately removed this sensitive default and added retries/auth recovery.

## Package / ecosystem

- npm `minimed-connect-to-nightscout` 1.5.8 is the relevant published cloud bridge; depends on old axios/request-era components, points to the deprecated Nightscout repo. No evidence the present local `carelink-bridge` is published to npm; its local package manifest is 0.1.6.
- PyPI `decocare` 0.0.31 is unrelated to modern CareLink Cloud: Python-2-era CareLink USB/ComLink2 pump protocol package, latest release metadata from 2015. Do not use it to guide cloud auth or endpoint design.
- `carelink-python-client` is a source repository rather than a published PyPI distribution; installation is from clone plus `requirements.txt`.
- Tidepool's `mmcsv-carelink-data` is deprecated historical CSV parsing, not current cloud-follow API evidence. Tidepool Uploader issue #586 states uploading via CareLink was no longer supported.
- Loop showed no direct, current CareLink cloud integration in consulted public material; it is not a useful implementation comparator for this bridge.

## Prioritized opportunities

- P0: Implement or explicitly diagnose the discovery-selected non-Auth0 MAG/device-registration flow; extend persisted token schema and refresh/API headers for optional `client_secret` and `mag-identifier`. Treat private key/token material as secrets and write atomically with restrictive permissions.
- P0: Make data/control base URLs discovery-driven while retaining separately validated legacy routes; log the selected auth/config family without secrets.
- P1: Expand device routing using xDrip's layered evidence (recent uploads, linked-patient metadata, monitor data) and distinguish BLE, CC, Guardian M2M, and legacy routes.
- P1: Replace fixed retries with status-aware capped exponential backoff plus jitter; honour or remove `CARELINK_MAX_RETRY_DURATION`; do not retry permanent 4xx except the one refresh cycle for 401/403.
- P1: Add schema-fixture coverage for the July 2026 "next reading" format change, markers, notifications, M2M, Simplera, and patient/care-partner variants. Fixtures should come from operator-sanitized data or public source models, never invented endpoint responses.
- P2: Optionally transform markers/notifications into Nightscout treatments/notes with strict dedupe and opt-in controls, borrowing xDrip's validation and nightscout-connect's mapping cautiously.
- P2: Separate stale-glucose suppression from bridge/device health reporting and retain raw response-family diagnostics that exclude medical data and identifiers.

## Open questions

- Which discovery records/regions currently select Auth0 versus MAG/non-Auth0? Public code establishes both paths, not rollout distribution.
- Does Medtronic still require PKCE for Auth0? Local uses it; current Python Auth0 source omits it. Only controlled testing or current public app artifacts can resolve this.
- Are `blePereodicDataEndpoint`, discovery `baseUrlCumulus`, and v13 display-message equivalent for every patient/care-partner/device combination? Evidence supports coexistence, not equivalence.
- What exact July 2026 response-field change required the Python proxy adjustment, and should the bridge surface "next reading" scheduling? Inspect commit `bd7064b` before implementation.
- Are multiple linked patients meant to be iterated or explicitly selected? Local silently selects the first; xDrip similarly exposes a default but supports named patients.
- Does the 20-minute global stale cutoff hide useful connection/alarm status?

No accounts, credentials, private data, authentication, POSTs to live services, or intrusive scans were used.
