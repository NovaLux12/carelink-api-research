#!/bin/bash
# Area AU single-request sender — the exact string exec'd under the per-host flock.
# Split out so no shell quoting can move the timestamp.
#
#   send.sh <delay> <headers-out> <body-out> <url>
#
# The sleep is INSIDE the lock, and TS_SENT is emitted immediately before curl
# execs, so t_sent is the instant the request leaves this machine rather than the
# instant the lock was entered. Nothing follows curl except the curl exit code.
set -u
DELAY="$1"; HDR="$2"; BODY="$3"; URL="$4"
sleep "$DELAY"
date -u +'TS_SENT %FT%T.%3NZ'
# GET only: no -X, no -d, no --data, no -H auth, no cookie, no token.
# --compressed is mandatory on this host: it serves gzip unconditionally and
# ignores Accept-Encoding, so an uncompressed read parses 0x8b (docs/09).
curl -s --compressed -D "$HDR" -o "$BODY" -w 'HTTP_STATUS %{http_code}\n' \
  --max-time 120 "$URL"
echo "CURL_EXIT $?"
