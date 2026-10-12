# Area Z — single-cell validation harness for the assertions added to
# regression/hurl/04-deep-surface.hurl on 2026-10-12 by area Z.
#
# This file exists to EXECUTE the new assertions before they are committed,
# because this repo records shipping an unexecuted assertion as a defect. It
# is a copy of the request lines plus the new predicates, and nothing else.
#
# It costs exactly NINE vendor requests — 6 for the two-origin discriminating
# test (3 hosts x 2 distinct Origin values) and 3 for v6's preflight presence.
# The two EXACT allow-methods pins added to the pre-existing `csr/v2` and bare
# `v2` blocks are NOT re-run here: they are attached to request blocks that
# already existed, so the weekly drift sweep exercises them at no extra cost.
# They were validated in the area Z harness itself — see
# ../FINDINGS.md section 5, 9 of 9 cells per route.
#
# The assertions that actually ship live in regression/hurl/04-deep-surface.hurl.
# Capture and output: ../hurl-validation.txt

# --- The two-origin discriminating test: constant `*`, not an echo. ---
OPTIONS https://clcloud.minimed.eu/connect/carepartner/v13/display/message
Origin: https://example.invalid
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" == "OPTIONS"

OPTIONS https://clcloud.minimed.eu/connect/carepartner/v13/display/message
Origin: https://probe-two.invalid
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" == "OPTIONS"

OPTIONS https://clcloud.minimed.com/connect/carepartner/v13/display/message
Origin: https://example.invalid
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" == "OPTIONS"

OPTIONS https://clcloud.minimed.com/connect/carepartner/v13/display/message
Origin: https://probe-two.invalid
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" == "OPTIONS"

OPTIONS https://clcloud-trials.minimed.com/connect/carepartner/v13/display/message
Origin: https://example.invalid
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" == "OPTIONS"

OPTIONS https://clcloud-trials.minimed.com/connect/carepartner/v13/display/message
Origin: https://probe-two.invalid
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" == "OPTIONS"

# --- v6: the vendor's own published blePereodicDataEndpoint. ---
OPTIONS https://clcloud.minimed.eu/connect/carepartner/v6/display/message
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" == "OPTIONS"

OPTIONS https://clcloud.minimed.com/connect/carepartner/v6/display/message
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" == "OPTIONS"

OPTIONS https://clcloud-trials.minimed.com/connect/carepartner/v6/display/message
HTTP 200
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" == "OPTIONS"