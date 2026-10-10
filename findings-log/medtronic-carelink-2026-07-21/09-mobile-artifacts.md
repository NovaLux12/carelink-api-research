# Mobile CareLink Connect metadata (observed 2026-07-21, store metadata only)

Methods: unauthenticated GETs to official Google Play and Apple iTunes lookup URLs, plus the third-party APKPure metadata mirror for version chronology. No APK was downloaded, installed, decompiled, or reverse-engineered.

## Package / region / current-version facts

- Google Play global: https://play.google.com/store/apps/details?id=com.medtronic.diabetes.carepartner&hl=en_US. Package `com.medtronic.diabetes.carepartner`; developer Medtronic, Inc.; title "CareLink™ Connect"; 100K+ downloads; page updated 2026-06-15. Release notes generic ("general bug fixes…"); semantic app version not rendered.
- Google Play US: https://play.google.com/store/apps/details?id=com.medtronic.diabetes.carepartner.us&hl=en_US. Package `com.medtronic.diabetes.carepartner.us`; 50K+ downloads; page updated 2026-06-22. Same generic release-note text and data-safety declarations.
- Apple iTunes lookup US: https://itunes.apple.com/lookup?id=1535972481&country=us. Bundle `com.medtronic.diabetes.carepartner.us`; version 3.8.1; current-version release 2026-06-22T20:09:23Z; iOS 14.0 minimum; 119,038,976 bytes; initial release 2020-11-05.
- Apple iTunes lookup global/GB: https://itunes.apple.com/lookup?id=1467892577&country=gb. Bundle `com.medtronic.diabetes.carepartner`; version 3.8.1; current-version release 2026-06-15T18:47:06Z; iOS 14 minimum; 119,034,880 bytes; initial release 2020-10-16.
- Apple regional checks: DE, CA confirm same global package/version with different regional initial-release dates (DE 2020-11-04, CA 2021-02-03).
- Third-party APKPure corroboration: global 3.8.1 build 9215, 71.1 MB, Android 11+ (dated 2026-06-17); US 3.8.1 build 9215, 74.4 MB, Android 11+ (dated 2026-06-26). Treated as medium-confidence; not official Medtronic provenance.

## Version history (APKPure metadata, corroboration only)

Global: 3.8.1 (9215, 2026-06-17), 3.8.0 (9210, 2026-05-17, 74.4 MB), 3.7.0 (9186, 2026-03-09, 71.4 MB), 3.6.0 (9172, 2025-10-09, 76.4 MB, Android 9+), 3.5.0 (9144, 2025-05-29), 3.4.0 (9115, 2025-01-20), 3.3.0 (9092, 2024-12-04), 3.2.2 (9047, 2024-04-24), 3.2.1 (9039, 2024-03-20), 3.2.0 (1284, 2023-10-17).

US: 3.8.1 (9215, 2026-06-26, 74.4 MB), 3.8.0 (9210, 2026-05-01, 74.4 MB), 3.7.0 (9186, 2026-03-03, 74.7 MB), 3.6.0 (9170, 2025-09-18, 76.4 MB, Android 9+), 3.5.0 (9144, 2025-05-26), 3.4.1 (9116, 2025-02-25), 3.3.1 (9093, 2024-11-20), 3.2.1 (9039, 2024-03-27), 3.1.0 (1248, 2023-08-25), 2.3.0 (1204, 2022-06-15, Android 7+).

## Functional facts

- CareLink Connect is for care partners, follows up to five people, views glucose/pump/CGM information, and sends selected alerts. Global: MiniMed 700-series and selected CGM. US: MiniMed 700-series + MiniMed Mobile + online CareLink sync. Both explicitly state it is a secondary display, not a replacement for the primary pump/CGM display, does not analyze/modify data, does not control the pump/CGM, does not receive data directly from the pump/CGM.

## Setup / compatibility

- Official setup guide: https://www.minimed.com/en-us/support/product-support/780g/setup-carelink-connect-app. Care-partner account differs from patient account; patient data reaches CareLink through MiniMed Mobile; both apps require Wi-Fi/mobile data; care partner and patient must reside in the same country; cross-country following is not supported; follow request expires after 24 hours; up to five people may be linked.
- Compatibility page: https://www.minimed.com/en-us/products/device-compatibility. Unsupported phones may refuse use, compatibility can lag new OS/device releases.

## Data safety (Play declarations)

- No data shared with third parties
- Possible collection: Personal info, Health and fitness, and 3 additional categories
- Data encrypted in transit
- Deletion request supported
- These are developer declarations and can vary by region/use; do not treat as an endpoint contract.

## Public discovery/config clues

- Public discovery URLs return 200 for US/EU android/3.6 and android/3.7. 3.6 and 3.7 return Auth0-selected Cumulus v13 configs; 3.4 returns legacy Cumulus v11/no-Auth0; 4.0 returns legacy v2/CareLink v1/no-Auth0.
- Public Auth0 structural clues: US auth domain `carelink-login.minimed.com`, client ID `0FGoNwY0SP8ZmESYSfEOgMw03c58c1hk`, audience `carepartner.patient.us`, scopes `profile openid offline_access`, redirect URI `com.medtronic.carepartner:/sso`. EU equivalent with `_ous` slug and client ID `PeAhkbhQWlQRxJiQxWfcFBiGus1lxfe9`. Public Auth0 paths: /authorize, /oauth/token, /oauth/revoke, /oidc/logout, /connect/session/status, /.well-known/openid-configuration, /userinfo.
- Public OIDC metadata at both Auth0 hosts advertises authorization_code + refresh_token (and other grants), PKCE S256 (and plain). Bridge should rely on S256/authorization-code semantics, not infer credentials.
- Legacy Android 3.4 discovery tails: legacy SSO configuration only, Cumulus /connect/carepartner/v11, CareLink /api/carepartner/v2, PDE /connect/pde/v2; no Auth0 SSO selector. Legacy endpoints under `mdtlogin.medtronic.com` (US) and `mdtlogin-ocl.medtronic.com` (EU), prefix `mmcl`, scope `profile openid roles country`.
- Android 4.0 discovery tails: CareLink /api/carepartner/v1, Cumulus /connect/carepartner/v2, PDE /connect/pde/v1, and legacy SSO config names. Confirms that a numerically newer discovery string is not necessarily compatible with the current Auth0 flow.

## Repo comparison

- `src/login.ts:15-24` defines `DISCOVERY_APP_VERSION = 'android/3.6'`. Local comments: 3.4 → cumulus v11/no Auth0, 3.6/3.7 → cumulus v13 Auth0, 4.0 → cumulus v2/CareLink v1 no Auth0. Public discovery GETs independently corroborate these structural differences.
- `src/doctor.ts:70-72` probes the same v13 Android 3.6 discovery URLs; this is a reachability check, not an app-version check.
- `src/carelink/client.ts:325-340` tries known data-endpoint versions [13, 11, 6, 5], preserving the country-settings URL first. The code comment says country settings were returning v6 while discovery advertised v13.
- Critical distinction: store semantic version 3.8.1 and discovery selector android/3.6 are different namespaces. The current public store version does not prove the app uses discovery selector android/3.8.1; public discovery proves 3.6/3.7 are Auth0-compatible tracks. Keep `android/3.6` unless a new public discovery track is verified to return the required Auth0 shape.

## Unknowns

- Official Android versionCode/build, exact Android manifest/minSdk/targetSdk/permissions, signing certificate, static endpoint/resource strings inside the app, regional Play artifact differences, whether 3.8.1 changed endpoint payloads, and whether public v13/v6 endpoint behavior is stable for all countries.
