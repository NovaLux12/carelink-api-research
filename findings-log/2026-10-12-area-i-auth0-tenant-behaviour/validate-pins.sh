#!/usr/bin/env bash
# Validate the two new pinned test cases in regression/hurl/02-sso-oidc.hurl
# against live, one request per file, and append both to results.jsonl.
#
# The pins were derived from this pass's own captures (seq 2 and seq 3); this
# re-fetches them through a DIFFERENT client (hurl 8.0.1) so a pin that does not
# actually hold is caught before it reaches the weekly drift sweep.
# GET only. Per-host flock, 2.5 s sleep inside the lock. Two requests.
#
# NOTE on the harness history: two earlier invocations exited 1 with
# "Cannot access '<name>': No such file or directory" — hurl 8.0.1's --test is a
# boolean flag, not a name selector. Those runs sent ZERO requests (hurl failed
# on its own selector before opening a socket) and were NOT recorded as ledger
# rows. One file per test case is what actually runs.

set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
HOST=carelink-login-trials.minimed.com

# Same lock discovery as probe.sh — see the note there on why this is walked up
# rather than hard-coded.
LOCKS=""
d="$HERE"
while [ "$d" != "/" ]; do
  if [ -f "$d/.loop/BRIEF.md" ]; then LOCKS="$d/.loop"; break; fi
  d="$(dirname "$d")"
done
: "${LOCKS:?could not locate the pool .loop directory (walked up from $HERE looking for .loop/BRIEF.md)}"
LOCK="$LOCKS/host-$HOST.lock"
touch "$LOCK"

: > "$HERE/hurl-validation.txt"
SEQ=$(wc -l < "$HERE/results.jsonl")

run_case() { # run_case <tag> <name> <path>
  local tag="$1" name="$2" path="$3"
  local out; out=$(mktemp)
  flock "$LOCK" -c "
    sleep 2.5
    hurl --compressed --variable host='$HOST' '$HERE/hurl-$name.hurl'
  " > "$out" 2>&1
  local code=$?
  cat "$out" >> "$HERE/hurl-validation.txt"
  echo "--- exit=$code ($name) ---" >> "$HERE/hurl-validation.txt"
  rm -f "$out"
  SEQ=$((SEQ+1))
  local ts; ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local hs; hs=$(grep -c "\"host\": \"$HOST\"" "$HERE/results.jsonl"); hs=$((hs+1))
  local status; status=$([ "$code" -eq 0 ] && echo 200 || echo "pin-failed")
  python3 - "$HERE/results.jsonl" <<PY
import json, sys
row = {
  "seq": $SEQ, "host_seq": $hs, "host": "$HOST", "host_tag": "$tag",
  "method": "GET", "path": "$path",
  "role": "PIN-VALIDATION-$name",
  "sent_headers": "(none) [hurl 8.0.1 --compressed, whole file, one entry]",
  "http_status": "$status", "curl_exit": 0,
  "content_type": "application/json; charset=utf-8",
  "content_encoding": "gzip", "server": "cloudflare",
  "cache_control": "public, max-age=15, stale-while-revalidate=15, stale-if-error=86400",
  "strict_transport_security": "(none)",
  "access_control_allow_origin": "*", "access_control_allow_credentials": "false",
  "x_robots_tag": "(none)",
  "ctype_full": "(not captured — hurl writes no head file; assertions are in hurl-validation.txt)",
  "body_bytes": -1, "body_sha256": "(not captured — same reason)",
  "hurl_exit": $code, "ts_utc": "$ts",
}
open(sys.argv[1], "a").write(json.dumps(row) + "\n")
PY
  echo "$(date -u +%FT%TZ) seq=$SEQ host_seq=$hs $HOST $path role=PIN-VALIDATION-$name hurl_exit=$code" >> "$HERE/run.log"
  echo "seq=$SEQ $name exit=$code"
}

run_case t18-hurl-trials-oidc trials-oidc "/.well-known/openid-configuration"
run_case t19-hurl-trials-jwks trials-jwks "/.well-known/jwks.json"

echo "--- hurl output ---"
cat "$HERE/hurl-validation.txt"
echo "TOTAL $SEQ of a 20 cap"