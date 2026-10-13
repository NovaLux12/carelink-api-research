#!/usr/bin/env bash
# Area J — OPTIONS sweep of the three advertised Auth0 sibling endpoints.
#
# SCOPE (claim issue #34, addendum only): the three paths named inside each
# tenant's own committed discovery document
# (findings-log/2026-10-12-area-i-auth0-tenant-behaviour/openid/*-openid-configuration.json):
#   backchannel_authentication_endpoint -> /bc-authorize
#   mfa_challenge_endpoint              -> /mfa/challenge
#   global_token_revocation_endpoint    -> /oauth/global-token-revocation/connection/{connectionName}
# The {connectionName} template is concretised as "Auth0" because that is the
# value already recorded in this repo (docs/02-auth-tenants-and-flows.md:137 and
# the GET 404 pin in regression/hurl/04-deep-surface.hurl). No wordlist, no
# enumeration: 3 paths x 5 tenants + 1 certainly-absent control per host.
#
# METHOD: empty-body OPTIONS with a preflight header set, which
# PULL_REQUEST_TEMPLATE.md permits for exactly this purpose ("GET only, except
# OPTIONS with an empty body to find POST-only routes"). All three paths are
# POST-only by OAuth/OIDC specification, so a GET sweep would report "absent"
# five times and be wrong five times (area I's retracted error). NO POST is
# sent anywhere: Access-Control-Request-Method is a preflight *declaration*,
# not a request, and no body is attached.
#
# VERDICT RULE (headers, never status — Oracle C, docs/09):
#   access-control-allow-methods: POST (+ACAO) = routed-POST-only
#   404 application/json 107 B, no access-control-* = routed-but-CORS-refused
#   404 text/plain 10 B + x-auth0-not-found: 1 = unrouted
#
# BUDGET: 26 requests (claim #34). Planned use: 20 = 5 controls + 15
# candidates. Up to 6 spare for diagnostics/re-issues, deliberately unspent
# unless a row fails to capture.
#
# TIMESTAMPS are millisecond ISO-8601 (the docs/09 ledger-resolution trap:
# area I's 1-second ledger could not resolve its own 2.5 s sleep). Every row
# carries t_queued (before the host lock), t_sent (inside the lock, after the
# sleep, immediately before curl) and t_done (after curl). Spacing floor is
# measured from t_sent gaps per host and must be >= 2 s.
#
# Per-host serialisation: sleep 2.5 s INSIDE the per-host flock. Three other
# pool workers share this machine; a sleep outside the lock would let queued
# workers fire simultaneously.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE"
CAP=26
SEQ=0

LOCKS=""
d="$HERE"
while [ "$d" != "/" ]; do
  if [ -f "$d/.loop/BRIEF.md" ]; then LOCKS="$d/.loop"; break; fi
  d="$(dirname "$d")"
done
: "${LOCKS:?could not locate the pool .loop directory}"

# Fixed, non-routable placeholder Origin: the preflight must carry an Origin
# to elicit CORS headers, but it must not look like a real referrer.
ORIGIN="https://example.invalid"

mkdir -p "$OUT/headers" "$OUT/bodies" "$OUT/ts"

log() { echo "$*" >> "$OUT/run.log"; }

req() { # req <host> <path> <role> <tag>
  local host="$1" path="$2" role="$3" tag="$4"
  SEQ=$((SEQ+1))
  if [ "$SEQ" -gt "$CAP" ]; then
    log "seq=$SEQ ABORTED cap $CAP reached before $host$path"
    return 1
  fi
  touch "$LOCKS/host-$host.lock"
  local url="https://$host$path"
  local t_queued; t_queued=$(date -u +%FT%T.%3NZ)
  flock "$LOCKS/host-$host.lock" -c "
    sleep 2.5
    date -u +%FT%T.%3NZ > '$OUT/ts/$tag.sent'
    curl -sS --compressed -X OPTIONS \
      -H 'Origin: $ORIGIN' \
      -H 'Access-Control-Request-Method: POST' \
      -H 'Access-Control-Request-Headers: content-type' \
      -D '$OUT/headers/$tag.h' -o '$OUT/bodies/$tag.b' \
      -w '%{http_code}' '$url' > '$OUT/ts/$tag.code' 2>'$OUT/headers/$tag.err'
    date -u +%FT%T.%3NZ > '$OUT/ts/$tag.done'
  "
  local flock_exit=$?
  local t_sent t_done code
  t_sent=$(cat "$OUT/ts/$tag.sent" 2>/dev/null || echo "(none)")
  t_done=$(cat "$OUT/ts/$tag.done" 2>/dev/null || echo "(none)")
  code=$(cat "$OUT/ts/$tag.code" 2>/dev/null || echo "000")
  local nbytes=0 sha="(none)"
  if [ -f "$OUT/bodies/$tag.b" ]; then
    nbytes=$(wc -c < "$OUT/bodies/$tag.b" | tr -d ' ')
    sha=$(sha256sum "$OUT/bodies/$tag.b" | cut -d' ' -f1)
  fi
  local cf
  cf=$(awk 'NR>1' "$OUT/headers/$tag.h" 2>/dev/null \
        | tr -d '\r' | awk '/: /{i=index($0,": ");k=tolower(substr($0,1,i-1));v=substr($0,i+2);
          if(k in a)a[k]=a[k]", "v;else a[k]=v} END{for(k in a)printf "%s: %s|",k,a[k]}' \
        | sed 's/|$//')
  [ -n "$cf" ] || cf="(none)"
  # ctype_full travels via a file, not via shell interpolation: header values
  # contain double quotes (e.g. etag W/"..."), which broke an earlier revision
  # of this writer that interpolated $cf into a Python string literal and
  # wrote zero ledger rows for 20 captured responses (2026-10-13, area J).
  printf '%s' "$cf" > "$OUT/ts/$tag.cf"
  local status="${code:-000}"
  local curl_exit=0
  [ "$flock_exit" -eq 0 ] || curl_exit=$flock_exit
  # host_seq: 1-based counter within this host, derived from rows so far.
  local host_seq; host_seq=$(python3 -c "
import json
n = 0
try:
    for line in open('$OUT/results.jsonl'):
        try:
            if json.loads(line).get('host') == '$host': n += 1
        except ValueError: pass
except FileNotFoundError: pass
print(n + 1)")
  python3 - "$OUT/results.jsonl" "$SEQ" "$host_seq" "$host" "$tag" "$role" "$path" "$status" "$curl_exit" "$nbytes" "$sha" "$t_queued" "$t_sent" "$t_done" "$OUT/ts/$tag.cf" <<'PY'
import json, sys
(_, out, seq, host_seq, host, tag, role, path, status, exit_, nbytes, sha,
 t_queued, t_sent, t_done, cf_file) = sys.argv
cf = open(cf_file, encoding="utf-8").read() or "(none)"
row = {
  "seq": int(seq), "host_seq": int(host_seq), "host": host, "host_tag": tag,
  "method": "OPTIONS", "path": path, "role": role,
  "sent_headers": "Origin: https://example.invalid | Access-Control-Request-Method: POST | Access-Control-Request-Headers: content-type (empty body)",
  "http_status": status, "curl_exit": int(exit_),
  "body_bytes": int(nbytes), "body_sha256": sha,
  "ctype_full": cf,
  "t_queued": t_queued, "t_sent": t_sent, "t_done": t_done,
}
open(out, "a").write(json.dumps(row) + "\n")
PY
  log "t_queued=$t_queued t_sent=$t_sent t_done=$t_done seq=$SEQ host_seq=$host_seq $host $path method=OPTIONS role=$role status=$status bytes=$nbytes sha=$sha"
  echo "seq=$SEQ host_seq=$host_seq $host $path status=$status bytes=$nbytes sha=${sha:0:12}"
}

TENANTS="carelink-login-trials.minimed.com carelink-login.minimed.eu carelink-login.minimed.com carelink-login.medtronic.eu carelink-login.medtronic.com"

# Control per host FIRST, then that host's three candidates. The control is
# one character off the first candidate (/bc-authorize -> /bc-authorizex),
# same method, same headers: it proves the unrouted signature on that host,
# so a routed verdict is falsifiable per host rather than assumed.
for h in $TENANTS; do
  short=$(echo "$h" | sed 's/carelink-login-//;s/\./-/g')
  req "$h" "/bc-authorizex" "CONTROL-unrouted-per-host" "c-$short" || break
  req "$h" "/bc-authorize" "CANDIDATE-backchannel_authentication_endpoint" "bc-$short" || break
  req "$h" "/mfa/challenge" "CANDIDATE-mfa_challenge_endpoint" "mfa-$short" || break
  req "$h" "/oauth/global-token-revocation/connection/Auth0" "CANDIDATE-global_token_revocation_endpoint" "gtr-$short" || break
done

echo "done: $SEQ of a $CAP cap"
