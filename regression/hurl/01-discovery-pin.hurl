# Medtronic CareLink — discovery endpoint pin regression suite
#
# Downstream consumer: https://github.com/NovaLux12/carelink-bridge — the bridge runs this suite before a release
# (`npm run drift:check` on the bridge side). A failure here reaches their
# release checklist; see https://github.com/NovaLux12/carelink-bridge/blob/main/docs/vendor-api/README.md
#
# Run:  hurl --test --delay 1200 hurl/*.hurl
#
# The load-bearing check from https://github.com/NovaLux12/carelink-bridge/blob/main/docs/adr/0002-discovery-app-version-pin.md.
# Asserts the pinned
# DISCOVERY_APP_VERSION (android/3.6) still returns:
#   1. HTTP 200
#   2. UseSSOConfiguration == Auth0SSOConfiguration  (the key src/login.ts reads)
#   3. baseUrlCumulus == .../v13  (cumulus track the bridge's data calls need)
#   4. A non-empty Auth0SSOConfiguration URL per region
#
# NOTE (verified 2026-10-08): clcloud.minimed.{eu,com} and
# clcloud-trials.minimed.com all return a BYTE-IDENTICAL document
# (same sha256). The hostname does not select the region — the document is
# global and carries all three CP entries; src/login.ts picks the entry whose
# .region matches. So the eu/com split in buildDiscoveryUrl() is cosmetic.
#
# CP[] order is US, EU, CLINICAL — index 0 is US, not EU.

GET https://clcloud.minimed.eu/connect/carepartner/v13/discover/android/3.6
HTTP 200
[Asserts]
jsonpath "$.config" == "android,3.6"
# three regions present, in this order
jsonpath "$.CP[0].region" == "US"
jsonpath "$.CP[1].region" == "EU"
jsonpath "$.CP[2].region" == "CLINICAL"
# every region must be on the Auth0 track
jsonpath "$.CP[0].UseSSOConfiguration" == "Auth0SSOConfiguration"
jsonpath "$.CP[1].UseSSOConfiguration" == "Auth0SSOConfiguration"
jsonpath "$.CP[2].UseSSOConfiguration" == "Auth0SSOConfiguration"
# ...and on cumulus v13
jsonpath "$.CP[0].baseUrlCumulus" endsWith "/connect/carepartner/v13"
jsonpath "$.CP[1].baseUrlCumulus" endsWith "/connect/carepartner/v13"
jsonpath "$.CP[2].baseUrlCumulus" endsWith "/connect/carepartner/v13"
# the SSO config URLs each region will be sent to
jsonpath "$.CP[0].Auth0SSOConfiguration" startsWith "https://carelink.minimed.com/configs/v1/carepartner_auth0_us_sso_config_v1.json"
jsonpath "$.CP[1].Auth0SSOConfiguration" startsWith "https://carelink.minimed.eu/configs/v1/carepartner_auth0_ous_sso_config_v1.json"
jsonpath "$.CP[2].Auth0SSOConfiguration" startsWith "https://carelink-trials.minimed.com/configs/v1/carepartner_auth0_cl_sso_config_v1.json"
# base URLs the app (not this bridge) uses
jsonpath "$.CP[1].baseUrlCareLink" == "https://carelink.minimed.eu/api/carepartner/v2"
jsonpath "$.CP[1].baseUrlPde" == "https://clcloud.minimed.eu/connect/pde/v3"
jsonpath "$.supportedCountries" count > 100
jsonpath "$.certificates" count == 8

# --- the published PDE base URL, on ALL THREE regions (area T, 2026-10-12) ---
# Why this matters more than a base-URL pin usually does: baseUrlPde resolves to
# /connect/pde/v3, and that namespace has NO ROUTE on any tested method on any of
# the three cumulus hosts (area C on .eu; area U on .com and -trials — see
# regression/hurl/04-deep-surface.hurl). So the vendor publishes a base URL that
# cannot answer, on every region of the document.
#
# The route side is pinned in 04; this side pins the promise. If Medtronic retires
# PDE properly this fires, and the note gets rewritten instead of a dead base URL
# staying published and load-bearing-looking forever.
# Source: findings-log/2026-10-12-published-pointers/FINDINGS.md §2b
jsonpath "$.CP[0].baseUrlPde" == "https://clcloud.minimed.com/connect/pde/v3"
jsonpath "$.CP[2].baseUrlPde" == "https://clcloud-trials.minimed.com/connect/pde/v3"

# NEGATIVE pin: the discovery document publishes NO CSR base URL. The csr/v2 route
# is nevertheless addressable — via the public config's csrDisplayMessageUrl, not
# via discovery. So if Medtronic ever adds baseUrlCsr here, the "config, not
# discovery" story changes and this assertion fires.
# Source: findings-log/2026-10-12-published-pointers/FINDINGS.md §1, §4
jsonpath "$.CP[0].baseUrlCsr" not exists
jsonpath "$.CP[1].baseUrlCsr" not exists
jsonpath "$.CP[2].baseUrlCsr" not exists

# The .com host must serve the same global document (not a US-only one).
# If this ever changes, buildDiscoveryUrl(isUS) stops being cosmetic.
GET https://clcloud.minimed.com/connect/carepartner/v13/discover/android/3.6
HTTP 200
[Asserts]
jsonpath "$.CP[1].region" == "EU"
jsonpath "$.CP[1].Auth0SSOConfiguration" startsWith "https://carelink.minimed.eu/configs/v1/carepartner_auth0_ous_sso_config_v1.json"

# The CLINICAL tenant is served by clcloud-trials over the same path.
GET https://clcloud-trials.minimed.com/connect/carepartner/v13/discover/android/3.6
HTTP 200
[Asserts]
jsonpath "$.CP[2].region" == "CLINICAL"
jsonpath "$.CP[2].Auth0SSOConfiguration" startsWith "https://carelink-trials.minimed.com/configs/v1/carepartner_auth0_cl_sso_config_v1.json"
