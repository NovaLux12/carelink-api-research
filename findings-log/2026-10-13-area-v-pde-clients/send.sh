#!/bin/bash
# Area V single-request sender — the exact string exec'd under the per-host flock.
# Split out of probe.sh so that no shell quoting can move the timestamp.
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
# GET only: no -X, no -d, no --data, no -H auth, no cookie, no token.
curl -s --compressed -D "$HDR" -o "$BODY" -w 'HTTP_STATUS %{http_code}\n' \
  --max-time 120 "$URL"
echo "CURL_EXIT $?"