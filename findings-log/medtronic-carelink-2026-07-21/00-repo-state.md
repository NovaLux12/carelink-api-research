# carelink-bridge current state (NovaLux12/carelink-bridge, observed 2026-07-21)

## File layout (key files only)

```
src/
  main.ts              - main loop, ensureLogin + requestLoop; uploads entries/devicestatus to Nightscout
  config.ts            - dotenv, requires CARELINK_USERNAME / PASSWORD / API_SECRET / NS
  filter.ts            - in-memory recency filter; restart loses watermark
  logger.ts            - verbose-gated text logger
  login.ts             - three-strategy Auth0 login (auto POST / puppeteer / terminal paste)
  carelink/
    client.ts          - fetch loop, role routing, BLE/legacy/carepartner, version fallback
    token.ts           - JWT decode + 600s expiry margin + refresh
    urls.ts            - EU/US server name + 5 patient URLs
  transform/
    index.ts           - 20-min stale threshold, 8-entry trend map, last-SG trend, pump-vs-Guardian
    pump-offset.ts     - 15-minute quantized offset guess
    trend-map.ts       - CareLink -> Nightscout trend strings
  nightscout/
    upload.ts          - POST entries + devicestatus, sha1(api-secret)
  types/
    carelink.ts        - 11 interfaces, blePereodicDataEndpoint misspelling intentional
    nightscout.ts      - 2 interfaces
  doctor.ts            - non-mutating pre-flight probe (env, JWT, CareLink discovery, Nightscout)

deploy/                - install.sh, systemd unit, Nightscout + cloudflared compose
```

## Key constants and tunables

- `DISCOVERY_APP_VERSION = 'android/3.6'` (`src/login.ts:24`)
- `BLE_API_VERSIONS = [13, 11, 6, 5]` (`src/carelink/client.ts:332`)
- 3-attempt retry, exp backoff 2/4/8s (third delay never reached because attempt 3 throws)
- `MAX_REQUESTS_PER_FETCH = 30`
- `isBleDevice` matches `BLE` or `SIMPLERA` substrings
- JWT margin: 600s (widened v0.1.4)
- `STALE_DATA_THRESHOLD_MINUTES = 20`
- 401/403 triggers force refresh on next retry (v0.1.4)
- server-reported username preferred in data POSTs (v0.1.5)
- pump-offset rounds to 15 minutes (v0.1.3)
- 5-min default poll; 30s between retries; max 5 restarts / 300s
- ReadWritePaths at directory level (v0.1.3)
- 4 runtime deps: axios, dotenv, qs, puppeteer-core; no proxy code; Node >=20

## Tests (10 vitest files, 55 cases after v0.1.6)

- transform (trend, stale-threshold, sgvLimit, activeInsulin -1 sentinel, uploader battery)
- pump-offset (whole/half/quarter-hour + ±7.5-min drift)
- filter recency
- BLE detection incl. PR #2 deviceFamily || medicalDeviceFamily fallback
- endpoint candidates (v6/v13/unknown-version/unversioned)
- username source (#25)
- force refresh on 401 (#22)
- doctor (config missing-vars, token validity/expiry/malformed, US/EU, status/verifyauth, secret hashing)
- No mocked-auth0 tests; login.ts itself untested

## What is modeled vs left on the floor

Modeled: sgs[], lastSGTrend, activeInsulin, lastAlarm, reservoir (amount/remaining), battery, sensor calibration/range, conduit/sensor in-range, BLE detection, device family, pump time, bgUnits (declared only), timeFormat (declared only)

Observed in public sources but NOT modeled (passes through `[key: string]: unknown`): `markers[]` (meal/insulin/bg readings), `limits[]` (BG-target schedule), `reservoirLevelPercent` (snap-pointed 0/25/50/75/100), `notificationHistory.activeNotifications/clearedNotifications`, `therapyAlgorithmState.autoModeShieldState/SAFE_BASAL`, `timeToNextCalibrationMinutes`

## Upstream / fork posture

- Upstream domien-f/carelink-bridge: only one open PR (#2 by @terminalcommand) since 2026-06-11
- Fork NovaLux12/carelink-bridge: v0.1.0-v0.1.6 shipped; v0.1.3 deploy artifacts; v0.1.4 force refresh; v0.1.5 server username; v0.1.6 doctor
- v0.2.0-v0.5.0 blocked on real-data validation (780G expected November 2026)
- Hardening deltas vs upstream: removed https-proxy-agent / socks-proxy-agent / https.txt; added SECURITY.md; Dependabot; CI Node 20+22; CODEOWNERS; branch protection enforce_admins; vitest 2→4; Node 18 dropped
- WebSocket / mobile push notifications: not implemented; bridge polls

## Open issues in repo

- #7: pre-pump operator checklist
- #8: v0.2.0 operability (doctor part shipped, healthz/stale alert/shutdown still open)
- #9: v0.3.0 reliability (backoff jitter, token refresh before expiry, circuit breaker, persistent state)
- #10: v0.4.0 observability (JSON logs, Prometheus, request counters)
- #11: v0.5.0 distribution (single binary, Docker, HA add-on)
- #12: Real-data discoveries tracker (parent for auth-flow research round-1/round-2)
- #13: low-priority repo hygiene

## Recap

Fork is materially ahead of domien-f upstream; three real gaps vs the active Python client: (1) no discovery-selected non-Auth0 MAG/device-registration flow + no `client_secret`/`mag-identifier` persistence, (2) hardcoded `/patient/*` instead of discovery-derived `baseUrlCareLink`/`baseUrlCumulus`, (3) `CARELINK_MAX_RETRY_DURATION=512` env still accepted but unused by fetch. Otherwise up to date for Auth0 v13/android/3.6 path.
