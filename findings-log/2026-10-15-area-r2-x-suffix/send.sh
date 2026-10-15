#!/bin/bash
# send.sh <delay> <hdr-out> <body-out> <url>
#
# Takes the SHARED per-host lock, sleeps INSIDE the lock, emits TS_SENT on the
# line immediately before curl execs, and prints five fields for probe.sh:
#   <t_lock_acquired>\t<t_sent>\t<http_code>\t<curl_exit>\t<t_done>
#
# WHY THE SLEEP IS INSIDE THE LOCK: outside it, four pool workers queue and then
# fire together, which is worse than not serialising at all. The spacing claim
# is only true if the gap is enforced at the point of transmission.
#
# t_done is taken HERE, inside this process, not by the caller after flock
# returns. The first run of this pass took t_done in the caller and wrote a row
# whose t_sent was LATER than its own t_done — an impossible ordering, which
# made the ledger's t_sent unusable for recomputing a gap. All four stamps are
# now emitted by one process in one order, and probe.sh asserts the ordering
# before it writes a row.
#
# --compressed is mandatory: carelink.minimed.eu serves brotli unconditionally
# (observed 2026-10-13), ignoring Accept-Encoding, so without it every body
# starts 0x1f 0x8b and every parse fails (AGENTS.md section 7).
set -u
DELAY="$1"; HDR="$2"; BODY="$3"; URL="$4"
T_LOCK="$(date -u +%FT%T.%3NZ)"
sleep "$DELAY"
# shellcheck disable=SC2016
TS_SENT="$(date -u +%FT%T.%3NZ)"
CODE="$(curl -s --compressed -D "$HDR" -o "$BODY" -w '%{http_code}' "$URL")"
EXIT=$?
TS_DONE="$(date -u +%FT%T.%3NZ)"
printf '%s\t%s\t%s\t%s\t%s\n' "$T_LOCK" "$TS_SENT" "$CODE" "$EXIT" "$TS_DONE"