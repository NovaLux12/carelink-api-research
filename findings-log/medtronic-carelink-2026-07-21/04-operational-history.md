# Operational history: CareLink maintenance, outages, community reports, and release timelines (2024-2026)

Scope note: github.com HTML pages were the primary source (api.github.com REST endpoints returned HTTP 403 and were not used). x.com pages were read via Nitter mirrors (nitter.tiekoetter.com). The CareLink outage index pages are branding stubs with no live banner.

## 2024-03-03 (Sun) — CarePartner-based authentication introduced to xDrip CareLink Follower

- benceszasz releases xDripCareLinkFollower v0.1.15-beta. The data source moves from the old recaptcha + username/password flow to authentication that mimics the CareLink Connect (CarePartner) mobile app, based on work by palmarci. Same release merged into official xDrip nightly 5 Dec 2023.
- New logins valid for ~1 week; automatic refresh in the background.
- Maintainer note: "a different dedicated follower account must be used for every app, otherwise the previous authentication token (login) will be revoked."
- Source: https://github.com/benceszasz/xDripCareLinkFollower/releases/tag/v0.1.15-beta
- Evidence strength: high.
- Reliability implication: "one account, one app" rule is a long-standing Medtronic single-session constraint and the most common reason 3rd-party clients lose their session token in later incidents.

## 2024-03-06 (Wed) — EU CareLink v6/v11 endpoint change breaks EU 7xxG pump followers

- Community report in xDrip discussion #3855: in Austria (EU), xDrip 2024.09.17 stopped connecting to the Medtronic server on 6 March 2024 with "Error refreshing CpApp token." Investigation finds the BLE data endpoint URL embedded in the country settings (v6, `…/connect/carepartner/v6/discover/android/3.2`) is no longer stable; new v11 endpoint must be used. 7xxG pump users are affected. JSON response shape also changes (new keys: `lastConduitUpdateServerDateTime`, etc.).
- Source: https://github.com/NightscoutFoundation/xDrip/discussions/3855
- Evidence strength: high.
- Reliability implication: data-endpoint discovery is version-coupled. Hard-coding v6 will silently start returning empty or stale data when Medtronic rotates the country settings file.

## 2024-03-23 (Sat) — CareLink server maintenance; tokens expire on 3rd-party clients

- Discussion #3405: "On March 23rd the Carelink servers went down for maintenance for a few hours. Since then I have not been able to log back in through xDrip." System Status page shows "token has expired." Resolved by upgrading to the nightly from 27 March.
- Source: https://github.com/NightscoutFoundation/xDrip/discussions/3405
- Evidence strength: medium.

## 2024-04-06 (Sat) — EU CareLink planned maintenance; notifications stop

- Discussion #3431 reports CareLink notifications not appearing since the announced EU maintenance on 6 April 2024 around 5pm CET. EventLog shows "CarelinkFollowDL … SocketTimeoutException" and "CareLink download error! Response code: 200." Author fixed by updating to xDrip 2024.03.27.
- Source: https://github.com/NightscoutFoundation/xDrip/discussions/3431
- Evidence strength: medium.
- Reliability implication: notifications appear to be a separate code path from the data fetch; can break silently after EU maintenance even when data fetches succeed.

## 2024-10-12 (Sat) → 2024-10-18 (Fri) — Multi-day CareLink outage spanning US/EU/UK

- updownradar.com user reports:
  - 2024-10-12: "Suddenly on 10/12/2024 US Carelink is not connecting to computer."
  - 2024-10-15: "Had no carelink to our daughters pump since 8.30am on 15/10/24 — West Midlands, England."
  - 2024-10-16: "Hasn't uploaded data to hospital since 12/10/24. Rang helpline and it says they are working to fix problem."
  - 2024-10-18: "CareLink app is not working for 24h … 8 year old child must take care of his own blood sugar while in school — Serbia."
- Official follow-up: Medtronic's "CareLink Personal Connectivity" page describes a "recent CareLink software and network outage" and instructs users to re-enter credentials in MiniMed Mobile and CareLink Connect.
- Sources: https://updownradar.com/status/Carelink.com; https://www.minimed.com/en-us/support/product-support/carelink-software/connectivity
- Evidence strength: medium for 24h outage; high for "Medtronic confirmed an outage occurred."
- Reliability implication: most severe 2024 incident. Real impact: continuous monitoring broken 6+ days for some patients; hospital uploads failed. Community apps cannot self-heal.

## 2024-11-17 (Sun) → 2024-11-20 (Wed) — Two xDrip CareLink fixes + CareLink Connect app update

- 2024-11-17: xDrip nightly "CareLink fix" (release notes).
- 2024-11-20: @MDT_Diabetes tweet: "A new version of the CareLink Connect app is available! You will need to log back into the app following the update."
- Sources: https://navid200.github.io/xDrip/docs/ReleaseNotes.html; https://nitter.tiekoetter.com/MDT_Diabetes/status/1859290437200081233
- Evidence strength: high for release note; medium for the app version.
- Reliability implication: app-version bumps that force a re-login also break long-lived 3rd-party refresh tokens. Expect 1-7 day token-rotation gaps when CareLink Connect ships a new version.

## 2025-01-14 (Tue) — xDrip community flags post-maintenance breakage

- xDrip discussion #3855 opened by EarthDevour: "It seems after latest medtronic maintenance xdrip is unable to use carelink follower as source." 26 comments / 69 replies across January. Maintainer benceszasz posts the eventual v11-endpoint fix on 14 Feb 2025.
- Source: https://github.com/NightscoutFoundation/xDrip/discussions/3855
- Evidence strength: high.
- Reliability implication: confirms that even after the Dec-2023 auth migration, post-maintenance service flaps remain the dominant failure mode for community clients in 2024-2025.

## 2025-02-13 (Thu) — xDrip v11 EU endpoint fix lands

- benceszasz's first working v11 implementation, commit 2baa087 on master ("CareFollow - v11 endpoint - First working version"). Replaces EU endpoint with v11; new JSON structures (ActiveInsulin, ActiveNotification, Alarm, ClearedNotification, DisplayMessage, DisplayMessageMetadata, Limit, Marker, MarkerData, MarkerDataValues, Notification, RecentData, SensorGlucose, plus CareLinkJsonAdapter).
- Source: https://github.com/NightscoutFoundation/xDrip/commit/2baa087d2d05ad50dd3cffd0750798941428a6c2
- Evidence strength: high.
- Reliability implication: this is the load-bearing fix for EU 7xxG pump followers.

## 2025-02-14 (Fri) — xDrip 2025.02.14 release ships EU v11 + US v11 support

- PR #3888 ("CareLinkFollower - v11 endpoint for US also") merged 14 Feb 2025 by jamorham, closes the US gap and merges benceszasz's EU work. Release notes: "2025.02.14 — CareLink fix."
- Sources: https://github.com/NightscoutFoundation/xDrip/pull/3888; https://navid200.github.io/xDrip/docs/ReleaseNotes.html
- Evidence strength: high.
- Reliability implication: US and EU now share a single v11 path. Some 2024.x.x users remain broken until they update.

## 2025-03-12 (Wed) — xDrip "CareLink fix"

- Release notes: "2025.03.12 — CareLink fix - Edit alert decimal separator fix." No public discussion thread.
- Source: https://navid200.github.io/xDrip/docs/ReleaseNotes.html
- Evidence strength: low.

## 2025-08-28 (Thu) → 2025-09-04 (Thu) — CareLink Personal planned 7pm-PT outage

- @MDT_Diabetes posted 28 Aug 2025: "CareLink Personal will be offline for a planned software update on September 4, starting at 7 p.m. PT. CareLink Personal software, mobile app, and care partner connectivity will be unavailable during this time. Following this, you may need to log back in to CareLink Personal."
- Source: https://nitter.tiekoetter.com/MDT_Diabetes/status/1961071537571897855
- Evidence strength: high (direct Medtronic Diabetes post).
- Reliability implication: a 1-week-or-1-hour token that doesn't refresh by 4 Sept 19:00 PT is at risk. Schedule refresh-token rotation to fire well before the window.

## 2025-09-05 (Fri) → 2025-12-31 (Wed) — quiet period

- xDrip nightly releases 2025.09.05, 2025.09.26, 2025.10.04, 2025.10.15, 14x nightly releases 2025-11-05 through 2025-12-31, 2025.12.29. None tagged "CareLink fix" with public incident discussion.
- Source: https://navid200.github.io/xDrip/docs/ReleaseNotes.html
- Evidence strength: low (absence of evidence, not evidence of absence).

## 2026-01-02 (Fri) — Medtronic rolls out new Auth0 authentication on production servers

- xDrip discussion #4318 opened by jaky1977. m0rt4l1n investigates: legacy OAuth token endpoint at `https://mdtlogin-ocl.medtronic.com:443/mmcl/auth/oauth/v2/token` returns RST on TLS ClientHello. New auth hosts: `clcloud.minimed.eu`, `carelink.minimed.eu`, `carelink-connect.minimed.eu`, `carelink-login.minimed.eu`. Discovery now reports the new `Auth0SSOConfiguration` key. The new APK has discovery URL: `https://clcloud.minimed.com/connect/carepartner/v13/discover/android/3.6`. m0rt4l1n reverse-engineers the Auth0 Universal Login flow and posts a working proof-of-concept by the same day, using `https://carelink-login.minimed.eu/oauth/device/code` and Auth0 callback parsing.
- ondrej1024/carelink-python-client issue #34 (Kucharskov): all bridges using the old flow lose connectivity with `Connection reset by peer` from `mdtlogin-ocl.medtronic.com`.
- Affected: xDrip CareLink follower, domien-f/carelink-bridge, ondrej1024/carelink-python-client, yo-han/Home-Assistant-Carelink, CareLinkJavaClient, xDripCareLinkFollower variants — every CarePartner-imitation client.
- Sources: https://github.com/NightscoutFoundation/xDrip/discussions/4318; https://github.com/ondrej1024/carelink-python-client/issues/34; PR #35 on ondrej1024/carelink-python-client
- Evidence strength: very high.
- Reliability implication: hard authentication cut-over. The legacy `mdtlogin-ocl.medtronic.com` host still resolves but terminates TLS. The new path uses Auth0 as a SaaS OIDC provider; existing client-side certificates (CSR flow) are no longer honored. Expect 100% of unofficial clients to fail simultaneously.

## 2026-01-02 (Fri) → 2026-01-03 (Sat) — reverse-engineering the new Auth0 flow

- m0rt4l1n's 3 Jan 2026 02:49 comment shows the Auth0 OAuth flow working on the carelink-python-client. Draft PR #4320 to xDrip opened. Navid200 ships a test APK on 3 Jan for community testing. melwaraki: "I was able to get my iOS app working thanks to your PR."
- Source: https://github.com/ondrej1024/carelink-python-client/pull/35 (commits 4510bf5, f23979b, c18d157)
- Evidence strength: high.
- Reliability implication: new auth model is essentially standard Auth0 with PKCE S256, but the configured OAuth client does not accept the device-code grant. Bridging requires a real Auth0 Universal Login → callback capture → token exchange.

## 2026-01-04 (Sun) → 2026-01-07 (Wed) — bridge fixes cascade

- ondrej1024/carelink-python-client PR #35 merged 4 Jan 2026 into main. Test build by Navid200 distributed in xDrip discussion #4318 for Android users on 3-4 Jan. Testers report it works on EU + US (Ajut on EU 780G + G4 sensor; meluvalli on US after upgrading Firefox 145 → 146.0.1).
- xDrip release notes row: "2026.01.03 b — CareLink fix" and "2026.01.04 — CareLink - Dex - Pebble maintenance improvements."
- cmeissl cross-references this work in yo-han/Home-Assistant-Carelink PR #122 (Update to api version v13) for Home Assistant users.
- Sources: https://github.com/ondrej1024/carelink-python-client/pull/35; https://navid200.github.io/xDrip/docs/ReleaseNotes.html
- Evidence strength: high.
- Reliability implication: 2-day turnaround from public cut-over to community fix is unusually fast; the maintainers had been monitoring Medtronic's auth changes for some time. The new fix path does not yet handle every edge case (see "Access token expires every 3 hours" reports below).

## 2026-01-08 (Thu) → 2026-02-13 (Fri) — stability period for the v13/Auth0 path

- xDrip release notes 2026.01.09, 2026.01.18, 2026.01.25, 2026.01.30, 2026.02.11, 2026.02.13 — no CareLink-tagged entries.
- nightfever77 and meluvalli both reported `Sign In` button disabled in Firefox 145; resolved by Firefox 146.0.1. Firefox/reCAPTCHA side-effect, not a Medtronic regression.
- Source: https://navid200.github.io/xDrip/docs/ReleaseNotes.html
- Evidence strength: low (absence of public incident reports, not absence of impact).

## 2026-02-13 (Fri) — ondrej1024/carelink-python-client version 1.3 (commit c553063) — discovery URL bumped to 3.3

- `CARELINK_CONFIG_URL` updated from `v11/discover/android/3.2` to `v11/discover/android/3.3`. Comment: "# 11/02/2025 - Update CARELINK_CONFIG_URL to ver 3.3." Also normalizes the SSO config key access: `sso_config["system_endpoints"]["token_endpoint_path"]` (older had `sso_config["oauth"]["system_endpoints"]["token_endpoint_path"]`).
- Source: https://github.com/ondrej1024/carelink-python-client/commit/c5530633c145ff7c8d10405443826ce35a42c398
- Evidence strength: high.
- Reliability implication: Medtronic rolled a new minor version of the discovery JSON. App-version string (android/3.3) is load-bearing; bumping to 3.4 or 4.0 may silently drop onto a config with no Auth0 SSO URL.

## 2026-03-25 (Wed) — follow-up reachability incident

- xDrip discussion #4473 opened by martonlipcsik: "CareLink download error! Response code:204" and "SocketTimeoutException" after updating to 2026.03.01. Login attempts fail with "Error communicating with CareLink server." Investigation reveals `mdtlogin-ocl.medtronic.com:443` is unreachable from some networks. Then on 2026-03-26 14:29 CET, the user reports: "It's working now. That was probably a medtronic side issue or maintenance. … I have not changed anything."
- Source: https://github.com/NightscoutFoundation/xDrip/discussions/4473
- Evidence strength: high.
- Reliability implication: Medtronic still actively serving some clients through the legacy `mdtlogin-ocl.medtronic.com` host even after the Jan 2026 cut-over — meaning two parallel auth paths exist in production. Recommended: keep the new v13/Auth0 path primary but be ready to fall back when Medtronic's older host intermittently accepts.

## 2026-03-25 (Wed) → 2026-07-19 (Sun) — maintenance period

- xDrip release notes 2026.04.01, 04.05b, 04.22, 04.29, 05.06, 05.27, 06.02, 06.13, 06.17, 06.24, 07.01, 07.08, 07.12, 07.15, 07.19. Several are tagged "Maintenance improvements." No CareLink-tagged release in this window.
- 2026.07.19 carelink-bridge CHANGELOG entry: "The discovery app-version string (android/3.6) is now a documented, named constant in src/login.ts. Live probing showed Medtronic's discovery endpoint returns a different config per version — only 3.6/3.7 carry the Auth0 SSO config this flow needs, while 3.4 and 4.0 return no-Auth0 tracks — so a well-meaning 'bump to a newer number' would silently break login."
- Source: https://navid200.github.io/xDrip/docs/ReleaseNotes.html; project CHANGELOG.md
- Evidence strength: high.
- Reliability implication: the community has hard-coded `android/3.6` as the safe discovery version. Treat 3.6 as a pinned dependency.

## 2026-07-07 (Tue) — carelink-python-client v1.4 (PR #35 fix) merged into main

- PR #35 "fix: update to new Medtronic auth0 workflow" merged into ondrej1024/carelink-python-client:main. Final state includes a reworked `_get_config` (UseSSOConfiguration selector + trailing-slash strip), a reworked `_do_refresh` (client_secret optional), and a `wip: dont set mag identifier if not existing in token data` adjustment.
- Source: https://github.com/ondrej1024/carelink-python-client/pull/35
- Evidence strength: high.
- Reliability implication: this is the long-term fix. `_do_refresh` is now defensive about `client_secret` not always being present in the Auth0 response (the legacy oauth flow had it; authorization_code PKCE flow does not). Any client that still assumes `client_secret` always exists in token data will throw `KeyError` on the new path.

## Cross-cutting observations

- The Auth0 migration (Jan 2026) is the biggest 2024-2026 change. It removed `client_secret` from token responses, removed the `device_code` grant, and split the discovery payload into `Layer7SSOConfiguration` and `Auth0SSOConfiguration` with a `UseSSOConfiguration` selector. All four major community clients were affected on the same day. Fixes landed within 2-6 days.
- Two distinct endpoint-version events in 2024-2025: v6→v11 in March 2024, and v11→v13 + Auth0 in Jan 2026. Both times, hard-coded version strings broke community clients.
- Same-account single-session is the constant: Medtronic's CarePartner endpoint revokes prior session tokens when the same account logs in elsewhere. The only robust workaround is to use a dedicated Care Partner account (no MFA) per app. All public outage and incident reports are dominated by token-revocation failures, not infrastructure failures. The Oct 2024 outage was the major counter-example.
- Access token lifetime drift: pre-Auth0 (CarePartner CPApp) "valid for 1 week." Post-Auth0: tokens appear to be 10,800 seconds (3 hours) per a community capture in PR #35. The `refresh_token` is the long-lived artifact; some 3rd-party code that only re-uses `access_token` will fail every 3 hours. carelink-bridge already tracks this: a 401/403 from the data endpoint forces a token refresh on the next retry (CHANGELOG entry 0.1.5 → 0.1.6).
- Discovery endpoint URL map (as of 2026-07-21):
  - US: `https://clcloud.minimed.com/connect/carepartner/v13/discover/android/3.6`
  - EU: `https://clcloud.minimed.eu/connect/carepartner/v13/discover/android/3.6`
  - Token host (US): `https://carelink-login.minimed.com`
  - Token host (EU): `https://carelink-login.minimed.eu`
  - UserInfo endpoint: `https://carelink-login.minimed.eu/userinfo`
  - Legacy token endpoint (still partially up, flaky): `https://mdtlogin-ocl.medtronic.com/mmcl/auth/oauth/v2/token`
  - Legacy data endpoints: `https://clcloud.minimed.{eu,com}/connect/carepartner/v{6,11,13}/display/message`

## Recommended tests to add (load-bearing reliability tests)

1. Token invalidation after same-account login elsewhere. Add an integration test that logs in twice with the same Care Partner account on two simulated apps, verifies the first session's `refresh_token` returns 401 within one polling cycle, and verifies the bridge retries the Auth0 login flow and recovers.
2. Discovery version pinning. Add a unit test that asserts the discovery URL string contains `android/3.6` (or whichever version your project has currently pinned) and that the response contains an `Auth0SSOConfiguration` key.
3. Data endpoint fallback chain. For each region, assert that fetch falls through v13 → v11 → v6 and returns a 200 within the configured timeout.
4. Auth0 access token refresh at 3h boundary. Run a long-running test that allows the access_token to expire past `expires_in` and asserts the bridge calls the refresh endpoint using the `refresh_token`. Verify the bridge does NOT re-prompt the user for credentials in this path.
5. Maintenance-window probe. A scheduled test that calls the discovery endpoint every 5 minutes and records HTTP 200/4xx/5xx plus latency. Tag any 5xx windows as incidents.
6. Defensive refresh body. Assert that `_do_refresh` does not include `client_secret` when the token store does not have one (the post-Auth0 path). This would have failed pre-PR-35 builds.
7. No-SSO-URL detection. Probe the discovery response for the literal `Auth0SSOConfiguration` key. If absent, raise the same named error the new CHANGELOG entry references, so on-call can recognise it in production.
8. CareLink Personal outage tweet feed. A small fetcher that polls the @MDT_Diabetes / @minimed account for "offline" / "maintenance" keywords and records the planned maintenance timestamps. The Sept 2025 announcement was made 7 days in advance; the Oct 2024 outage was not pre-announced.

## Sources that did NOT return useful content (do not cite as evidence)

- api.github.com REST endpoints (discussions/comments/commits/releases) — HTTP 403
- x.com pages directly — JS-shell only, tweet text not in initial HTML
- carelink.medtronic.eu/outage/maintenance/index.html and carelink.minimed.com/outage/maintenance/index.html — branding stubs
- mycarelink-monitor/troubleshooting.html — relevant to MyCareLink Monitor (cardiac), not CareLink Personal/Connect (diabetes)
