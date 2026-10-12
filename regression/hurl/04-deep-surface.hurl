# Medtronic CareLink — deep-surface assertions added 2026-10-08
#
# Covers the findings from the second, deeper pass. Run via ../run.sh.
#
# NOTE: two of these are *negative* assertions pinning endpoints that are
# advertised in Medtronic's own config/OIDC documents but do NOT resolve.
# If they ever start returning 200, the surface has moved.

# ============================================================
# Discovery: the ONLY Auth0+cumulus-v13 cells are 3.6/3.7/3.8
# ============================================================

# 3.5 selects Auth0 but is on cumulus v11 -> must NOT be used as a fallback
GET https://clcloud.minimed.eu/connect/carepartner/v13/discover/android/3.5
HTTP 200
[Asserts]
jsonpath "$.CP[1].UseSSOConfiguration" == "Auth0SSOConfiguration"
jsonpath "$.CP[1].baseUrlCumulus" endsWith "/connect/carepartner/v11"

# 3.9+ dropped to cumulus v2 with no SSO selector
GET https://clcloud.minimed.eu/connect/carepartner/v13/discover/android/3.9
HTTP 200
[Asserts]
jsonpath "$.CP[1].UseSSOConfiguration" not exists

# Base-path versions select the DEPLOYMENT, not an API revision.
# v13 = the patient API (what we use). v11 = a TRIALS deployment: every region,
# including US and EU, is served the trials tenant. Discovering this mattered
# because "v11" reads like "older API" but is actually a different tenant.
GET https://clcloud.minimed.eu/connect/carepartner/v11/discover/android/3.6
HTTP 200
[Asserts]
# all three regions point at the trials infrastructure, not the patient one
jsonpath "$.CP[0].baseUrlCumulus" endsWith "clcloud-trials.minimed.com/connect/carepartner/v13"
jsonpath "$.CP[1].baseUrlCumulus" endsWith "clcloud-trials.minimed.com/connect/carepartner/v13"
jsonpath "$.CP[2].baseUrlCumulus" endsWith "clcloud-trials.minimed.com/connect/carepartner/v13"
jsonpath "$.CP[0].baseUrlCareLink" endsWith "carelink-trials.minimed.com/api/carepartner/v2"

GET https://clcloud.minimed.eu/connect/carepartner/v12/discover/android/3.6
HTTP 401

GET https://clcloud.minimed.eu/connect/carepartner/v14/discover/android/3.6
HTTP 403

# ============================================================
# device_code is REJECTED for this client (verified 2026-10-08)
# ============================================================
# The OIDC doc advertises the grant, but the CareLink client_ids do not
# have it enabled. Community reported this untested; now confirmed.
# This POST is unauthenticated (public client, no secret) and is rejected
# server-side, so no device code is ever created.
POST https://carelink-login.minimed.eu/oauth/device/code
[FormParams]
client_id: PeAhkbhQWlQRxJiQxWfcFBiGus1lxfe9
scope: openid profile offline_access
audience: carepartner.patient.ous
HTTP 403
[Asserts]
jsonpath "$.error" == "unauthorized_client"
jsonpath "$.error_description" contains "not allowed for the client"

# ============================================================
# Advertised-but-absent endpoints (negative assertions)
# ============================================================
# The SSO config lists this path but it 404s on every method.
GET https://carelink-login.minimed.eu/connect/session/status
HTTP 404

# Advertised in the OIDC doc but not live at the documented path.
GET https://carelink-login.minimed.eu/oauth/global-token-revocation/connection/Auth0
HTTP 404

# ============================================================
# POST-only endpoints that a GET-only probe would misread as dead
# ============================================================
# /oauth/revoke: GET -> 404, POST -> 401 invalid_client. It IS live.
GET https://carelink-login.minimed.eu/oauth/revoke
HTTP 404

POST https://carelink-login.minimed.eu/oauth/revoke
HTTP 401
[Asserts]
jsonpath "$.error" == "invalid_client"

# /oidc/logout serves a page on both GET and POST
GET https://carelink-login.minimed.eu/oidc/logout
HTTP 200

# /userinfo is a live OAuth-protected endpoint
GET https://carelink-login.minimed.eu/userinfo
HTTP 401

# ============================================================
# Patient API: guardian-connect (m2m gc) data path is live
# ============================================================
GET https://carelink.minimed.eu/patient/m2m/connect/data/gc/patients/probe-user
HTTP 401
[Asserts]
jsonpath "$.error.type" == "InvalidToken"

# The `/last24hours` suffix on that path is NOT valid
GET https://carelink.minimed.eu/patient/m2m/connect/data/gc/patients/probe-user/last24hours
HTTP 404

# ============================================================
# Country settings: only AU has the care-partner mobile app flag.
# This is the pre-780G regional rollout watch item.
# ============================================================
GET https://carelink.minimed.eu/patient/countries/settings?countryCode=AU&language=en
HTTP 200
[Asserts]
jsonpath "$.cpMobileAppAvailable" == true

# GB does not even carry the flag — the key is absent, not false.
GET https://carelink.minimed.eu/patient/countries/settings?countryCode=GB&language=en
HTTP 200
[Asserts]
jsonpath "$.cpMobileAppAvailable" not exists

# US carries it explicitly false.
GET https://carelink.minimed.eu/patient/countries/settings?countryCode=US&language=en
HTTP 200
[Asserts]
jsonpath "$.cpMobileAppAvailable" == false

# ============================================================
# Area C (2026-10-11): PDE closed, CSR v2 + bare v2 are POST-only
# Source: findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md
# GET 403 + OPTIONS 403 = dead. GET 403 + OPTIONS 200 = live POST-only.
# If any of these flip, the vendor surface moved.
# ============================================================
# PDE has no route on any tested method (GET and OPTIONS both 403)
GET https://clcloud.minimed.eu/connect/pde/v3/display/message
HTTP 403

OPTIONS https://clcloud.minimed.eu/connect/pde/v3/display/message
HTTP 403

# CSR v2 is live but POST-only: GET is undefined, OPTIONS proves the resource
OPTIONS https://clcloud.minimed.eu/connect/csr/v2/display/message
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"

GET https://clcloud.minimed.eu/connect/csr/v2/display/message
HTTP 403

# Bare pre-carepartner v2 is live but POST-only (same signature as v6)
OPTIONS https://clcloud.minimed.eu/connect/v2/display/message
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"

GET https://clcloud.minimed.eu/connect/v2/display/message
HTTP 403

# CSR neighbours are dead on both methods (only v2 is live)
OPTIONS https://clcloud.minimed.eu/connect/csr/v1/display/message
HTTP 403

OPTIONS https://clcloud.minimed.eu/connect/csr/v3/display/message
HTTP 403

# The remaining negatives from the same pass, pinned here so the space stays
# closed: PDE v1/v2, the v3 discovery cell, and the bare carepartner prefixes
# (the router answers at leaves, not at prefix parents). All GET+OPTIONS 403
# with MissingAuthenticationTokenException and no CORS.
GET https://clcloud.minimed.eu/connect/pde/v1/display/message
HTTP 403

OPTIONS https://clcloud.minimed.eu/connect/pde/v1/display/message
HTTP 403

GET https://clcloud.minimed.eu/connect/pde/v2/display/message
HTTP 403

OPTIONS https://clcloud.minimed.eu/connect/pde/v2/display/message
HTTP 403

GET https://clcloud.minimed.eu/connect/pde/v3/discover/android/3.6
HTTP 403

OPTIONS https://clcloud.minimed.eu/connect/pde/v3/discover/android/3.6
HTTP 403

GET https://clcloud.minimed.eu/connect/carepartner/
HTTP 403

OPTIONS https://clcloud.minimed.eu/connect/carepartner/
HTTP 403

GET https://clcloud.minimed.eu/connect/carepartner/v13
HTTP 403

OPTIONS https://clcloud.minimed.eu/connect/carepartner/v13
HTTP 403

GET https://clcloud.minimed.eu/connect/carepartner/v13/discover
HTTP 403

OPTIONS https://clcloud.minimed.eu/connect/carepartner/v13/discover
HTTP 403

# ============================================================
# Area N (2026-10-12): both POST-only routes are NOT region-split —
# they are live on .com and -trials too, with byte-identical CORS config.
# Source: findings-log/2026-10-12-csr-cross-host/FINDINGS.md
#
# Method registration is read from the GET probe, never from
# access-control-allow-methods. The carepartner/v13 preflight advertises
# `allow-methods: OPTIONS` on a route that IS GET-capable (GET -> 401
# UnauthorizedException + x-ca-err: 990), so that header is not a register
# of the route's methods. `contains "POST"` below is corroboration that
# POST is advertised, not the proof that GET is absent — the GET 403 with
# MissingAuthenticationTokenException is that proof.
# ============================================================

# The GET half of the v13 contradiction, pinned on all three hosts.
# Without this the block above is one-directional: if Medtronic ever made
# v13 POST-only, `allow-methods` would very likely still read OPTIONS and
# nothing here would fail, while the claim the suite documents became
# false. `x-ca-err: 990` is what makes 401 mean "reached the Layer7
# authorizer" rather than "some other 401" (VERSION-AXIS section 6).
GET https://clcloud.minimed.eu/connect/carepartner/v13/display/message
HTTP 401
[Asserts]
header "x-ca-err" == "990"

OPTIONS https://clcloud.minimed.com/connect/carepartner/v13/display/message
HTTP 200
[Asserts]
header "access-control-allow-methods" == "OPTIONS"

GET https://clcloud.minimed.com/connect/carepartner/v13/display/message
HTTP 401
[Asserts]
header "x-ca-err" == "990"

OPTIONS https://clcloud-trials.minimed.com/connect/carepartner/v13/display/message
HTTP 200
[Asserts]
header "access-control-allow-methods" == "OPTIONS"

GET https://clcloud-trials.minimed.com/connect/carepartner/v13/display/message
HTTP 401
[Asserts]
header "x-ca-err" == "990"

OPTIONS https://clcloud.minimed.com/connect/csr/v2/display/message
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" contains "POST"

GET https://clcloud.minimed.com/connect/csr/v2/display/message
HTTP 403
[Asserts]
header "x-amzn-errortype" contains "MissingAuthenticationTokenException"

OPTIONS https://clcloud.minimed.com/connect/v2/display/message
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" contains "POST"

GET https://clcloud.minimed.com/connect/v2/display/message
HTTP 403
[Asserts]
header "x-amzn-errortype" contains "MissingAuthenticationTokenException"

OPTIONS https://clcloud-trials.minimed.com/connect/csr/v2/display/message
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" contains "POST"

GET https://clcloud-trials.minimed.com/connect/csr/v2/display/message
HTTP 403
[Asserts]
header "x-amzn-errortype" contains "MissingAuthenticationTokenException"

OPTIONS https://clcloud-trials.minimed.com/connect/v2/display/message
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" contains "POST"

GET https://clcloud-trials.minimed.com/connect/v2/display/message
HTTP 403
[Asserts]
header "x-amzn-errortype" contains "MissingAuthenticationTokenException"
