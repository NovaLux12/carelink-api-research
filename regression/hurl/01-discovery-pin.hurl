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
# NOTE, CORRECTED 2026-10-12 by area Y. This note previously read "clcloud.
# minimed.{eu,com} AND clcloud-trials.minimed.com all return a BYTE-IDENTICAL
# document (same sha256)". Only the FIRST TWO were ever hashed: the 2026-10-12
# sweep records v13/discover/android/3.6 for clcloud.minimed.eu and .com, both
# 20256 B / sha256 f84886265667, and its only -trials row is the LEGACY v6
# document (10053 B) — a different document at a different version. So the
# byte-identity claim is 2-host evidenced, not 3. See
# findings-log/2026-10-12-area-y-three-host-audit/FINDINGS.md section 4 Y-1.
#
# What IS 3-host evidenced, and is all this block needs: the -trials request
# below asserts CP[2].region == "CLINICAL", so every host serves a document
# carrying all three CP entries and the hostname does not select the region.
# The eu/com split in buildDiscoveryUrl() is therefore cosmetic. The trials
# BODY has simply never been hashed — do not read the absence of a digest here
# as evidence the document differs.
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

# NEGATIVE CORS pin, added 2026-10-12 by area X — this is the cell whose absence
# let a wrong claim through two review rounds. It costs ZERO extra requests: the
# GET above already fetches this exact URL, so these two assertions ride on a
# request the suite was making anyway.
#
# WHY IT MATTERS. The discovery document is one of the few things on clcloud.* that
# answers 200 unauthenticated. It answers 200 and carries NO Access-Control-* header
# at all. Until area X, 04-deep-surface.hurl pinned only the OPTIONS side (a 401
# carrying no CORS), which is the wrong method to catch this: a one-directional pin
# on the 401 still passes if Medtronic later adds CORS to the 200 GET. Asserting the
# ABSENCE on the 200 is what makes "a 200 on clcloud.* does not imply a preflight"
# falsifiable by drift.
#
# This is the assertion that makes docs/03 §6 and docs/06 checkable. Before it,
# "on clcloud.*, carries-a-preflight and answers-200 are the same observation in this
# corpus" was repeated across five pages and was FALSE: this very URL is the
# counterexample, and it was sitting in the suite unpinned the whole time.
#
# Still NOT established, and deliberately not asserted here: whether preflight
# presence is configured per route, or whether ACAO is only ever emitted on OPTIONS
# responses. Both readings fit every cell on disk, and no recorded clcloud.* route is
# both CORS-configured and GET-public, so the question cannot be settled from a GET
# at all. Successor area in docs/11, not a claim made here.
# Source: findings-log/2026-10-12-area-x-cors-separation/FINDINGS.md §4
header "access-control-allow-origin" not exists
header "access-control-allow-methods" not exists

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
