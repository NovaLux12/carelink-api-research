#!/bin/bash
# Area K clinic control-flow pass — single-request sender.
# The exact string exec'd under the per-host flock, split out of probe.sh so that
# no shell quoting can move a timestamp (the 2026-10-13 patient pass's defect
# class: a timestamp emitted outside the lock measures the lock wait, not the send).
#
#   send.sh <delay> <headers-out> <body-out> <url>
#
# The sleep is INSIDE the lock (pool brief), and TS_SENT is emitted immediately
# before curl execs, so t_sent is the instant the request left this machine
# rather than the instant the lock was entered. Nothing follows curl except the
# curl exit code.
set -u
DELAY="$1"; HDR="$2"; BODY="$3"; URL="$4"
sleep "$DELAY"
date -u +'TS_SENT %FT%T.%3NZ'
# GET only: no -X, no -d, no --data, no --json, no -H auth, no cookie, no token.
curl -s --compressed -D "$HDR" -o "$BODY" -w 'HTTP_STATUS %{http_code}\n' \
  --max-time 120 "$URL"
echo "CURL_EXIT $?"