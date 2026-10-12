# Medtronic CareLink — patient data API auth boundary
#
# Downstream consumer: https://github.com/NovaLux12/carelink-bridge — the bridge runs this suite before a release
# (`npm run drift:check` on the bridge side). A failure here reaches their
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

# ============================================================
# Area O (2026-10-12): /patient/reports/* is on ALL THREE patient
# deployments, not just the EU one.
# Source: findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md
#
# The claim this replaces said "live, gated 401/405" on
# carelink.minimed.eu, sourced to a 2026-10-10 sweep. That sweep's
# committed artefact disclaims itself: DRIFT-AND-NEW-2026-10-10.md:9
# calls it "a reconstruction from the agent's report", with the
# command-level evidence "not reproduced" and the instruction "re-verify
# before treating any row as OBSERVED". The bundle inventory it produced
# carries none of the camelCase names, and the only committed file
# naming `snapshotTimelinesRange`
# was ARCHIVE-URLS.md:162 — whose own header (line 302) says the codes
# are "as archived, NOT as measured live today", window 2020-09-29 to
# 2021-03-31. So there was no live probe behind the claim. These are
# the live rows: all seven recorded codes reproduce exactly, 21/21
# cells, and the responses are byte-identical across hosts.
#
# Five of the twenty-one cells are pinned, chosen as the separating
# ones rather than all of them: AGENTS.md section 11 gives the drift
# sweep a request budget, and 21 new requests per sweep is a tax, not
# a guard.
# ============================================================

# The load-bearing new cell: the US deployment positively carries the
# namespace. Before area O no sibling host had ever been asked.
GET https://carelink.minimed.com/patient/reports/supported
HTTP 401
[Asserts]
jsonpath "$.error.type" == "InvalidToken"
jsonpath "$.error.group" == "AUTH"

# Same, for the third (trials/clinical) deployment.
GET https://carelink-trials.minimed.com/patient/reports/supported
HTTP 401
[Asserts]
jsonpath "$.error.type" == "InvalidToken"

# The POST-only arm, asserted on a sibling. `Allow` is asserted because
# it is present here and IS method authority: docs/09 section 4 records
# that not one of the 42 captured clcloud.* responses carried `Allow`,
# so on that family the GET probe was the only authority available.
# On the carelink.* patient plane the header exists and agrees with the
# 405. The 405 is recorded as evidence the route is POST-only; this
# suite never sends a POST to it.
GET https://carelink.minimed.com/patient/reports/generateReport
HTTP 405
[Asserts]
header "Allow" == "POST, OPTIONS"

# The least-covered status (400 = argument-gated, the route reached
# application code), on the least-covered host.
GET https://carelink-trials.minimed.com/patient/reports/reportStatus
HTTP 400
[Asserts]
jsonpath "$.validationErrors[0].field" == "getReportStatus.arg0"

# THE NEGATIVE ARM. `/patient/reports/report` is 404 on all three hosts
# and its body is byte-identical to a certainly-absent path (0 bytes,
# sha256 e3b0c442... — the digest of the empty string). If this ever
# becomes a 401 or a 405 the route became real, which is a finding, and
# this is the assertion that would catch it. Pinning the negative
# matters as much as pinning the positive: without it the in-corpus
# negative could quietly flip.
GET https://carelink.minimed.com/patient/reports/report
HTTP 404
