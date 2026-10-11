# Medtronic CareLink — patient data API auth boundary
#
# Downstream consumer: https://github.com/NovaLux12/carelink-bridge — the bridge runs this suite before a release
# (`npm run drift:check` on the bridge side). A failure here is a bridge
# release checklist; see https://github.com/NovaLux12/carelink-bridge/blob/main/docs/vendor-api/README.md
#
# The bridge's own endpoint table lives in
# https://github.com/NovaLux12/carelink-bridge/blob/main/src/carelink/urls.ts
# and covers the bare /patient/* namespace. This suite pins the
# *unauthenticated* behaviour of every one of those paths, plus two namespaces
# the discovery doc advertises.
#
# 401 + {"error":{"type":"InvalidToken","group":"AUTH"}} is the expected
# "endpoint exists, needs a token" signature. 404 would mean the path moved.
# 200 on an endpoint that should require auth would be a finding.
#
# Verified live 2026-10-08. These are GET-only and carry no credentials.

# --- src/carelink/urls.ts: me ---
GET https://carelink.minimed.eu/patient/users/me
HTTP 401
[Asserts]
jsonpath "$.error.type" == "InvalidToken"
jsonpath "$.error.group" == "AUTH"

GET https://carelink.minimed.com/patient/users/me
HTTP 401
[Asserts]
jsonpath "$.error.type" == "InvalidToken"

# --- src/carelink/urls.ts: m2m links/patients ---
GET https://carelink.minimed.eu/patient/m2m/links/patients
HTTP 401
[Asserts]
jsonpath "$.error.type" == "InvalidToken"

# --- src/carelink/urls.ts: monitor/data (POST in the bridge; GET is also allowed) ---
GET https://carelink.minimed.eu/patient/monitor/data
HTTP 401
[Asserts]
jsonpath "$.error.type" == "InvalidToken"

# --- src/carelink/urls.ts: connect/data (POST in the bridge) ---
GET https://carelink.minimed.eu/patient/connect/data?cpSerialNumber=NONE&msgType=last24hours&requestTime=1
HTTP 401
[Asserts]
jsonpath "$.error.type" == "InvalidToken"

# --- Second attested namespace: discovery's baseUrlCareLink (/api/carepartner/v2) ---
GET https://carelink.minimed.eu/api/carepartner/v2/users/me
HTTP 401
[Asserts]
jsonpath "$.error.type" == "InvalidToken"

GET https://carelink.minimed.eu/api/carepartner/v2/links/patients
HTTP 401
[Asserts]
jsonpath "$.error.type" == "InvalidToken"

# --- Third surface: cumulus v13 on clcloud (different auth boundary/body shape) ---
GET https://clcloud.minimed.eu/connect/carepartner/v13/monitor/data
HTTP 401
[Asserts]
jsonpath "$.message" == "Authentication failure"

# --- Public, unauthenticated, 200-expected ---
GET https://carelink.minimed.eu/patient/countries/settings?countryCode=GB&language=en
HTTP 200
[Asserts]
jsonpath "$.name" == "United Kingdom"

# NEW 2026-10-08: unauthenticated feature-flag readout
GET https://carelink.minimed.eu/patient/configuration/system/personal.cp.m2m.enabled
HTTP 200
[Asserts]
jsonpath "$.value" == "true"

# --- The hybrid v2+patient shape must keep 404ing (asserts it never becomes valid) ---
GET https://carelink.minimed.eu/api/carepartner/v2/patient/users/me
HTTP 404
