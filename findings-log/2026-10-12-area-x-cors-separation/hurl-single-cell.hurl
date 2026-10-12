# Single-cell validation harness for the two assertions added to
# regression/hurl/01-discovery-pin.hurl on 2026-10-12 by area X.
#
# This file exists to EXECUTE the new assertions before they are committed, because
# this repo records shipping an unexecuted assertion as a defect. It is a copy of
# the request line plus the two new predicates, and nothing else -- running it
# costs exactly ONE vendor request, which is what keeps the pass inside its cap.
# The assertions that actually ship live in regression/hurl/01-discovery-pin.hurl.
GET https://clcloud.minimed.eu/connect/carepartner/v13/discover/android/3.6
HTTP 200
[Asserts]
header "access-control-allow-origin" not exists
header "access-control-allow-methods" not exists
