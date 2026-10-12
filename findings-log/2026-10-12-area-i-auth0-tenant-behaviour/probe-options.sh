#!/usr/bin/env bash
# Area I SUPPLEMENTARY — OPTIONS liveness oracle for /oidc/register.
#
# WHY THIS EXISTS. The original pass recorded /oidc/register as 404 on all five
# tenants and reported the endpoint "absent". A verifier refuted that: the route
# is live and POST-only. The GET-only method cannot see it. This is the repo's
# own standing method for exactly this question — PULL_REQUEST_TEMPLATE.md:15
# ("GET only, except OPTIONS with an empty body to find POST-only routes") and
# docs/09:64-71 (GET 403 + OPTIONS 200 -> live, POST-only) — and PROBE-FINDINGS
# §5 is titled "Endpoints that are POST-only (a GET-only probe reads them as
# dead)". The original pass ran the wrong method, not merely a wrong reading.
#
# BUDGET: named supplementary budget of 14, authorised by the owner to complete
# a claim a verifier refuted. Planned use is 10 = 5 tenants x (plausible +
# certainly-absent control). 4 spare, deliberately unspent: this budget exists
# to settle one question, and spending it on anything else would blur the
# accounting. Recorded in FINDINGS.md as a separate budget from the original
# 20-cap; total traffic for the area is 19 + <=14.
#
# OPTIONS ONLY, EMPTY BODY. No POST is sent to any host, no token exchange, no
# authentication. A preflight carries Origin + Access-Control-Request-Method,
# which is what proves the route exists without invoking it.
#
# CONTROLS ARE PER TENANT, NOT PER PASS. An absent-path 404 on one host says
# nothing about the next host's front door (the original pass already argued
# this at FINDINGS.md §7 C3). So every tenant gets its own control, one
# character off the path under test.
#
# Per-host serialisation: sleep INSIDE the flock, same as probe.sh:57-62.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE"
CAP=14
SEQ=0

LOCKS=""
d="$HERE"
while [ "$d" != "/" ]; do
  if [ -f "$d/.loop/BRIEF.md" ]; then LOCKS="$d/.loop"; break; fi
  d="$(dirname "$d")"
done
: "${LOCKS:?could not locate the pool .loop directory}"

# Origin is a fixed, non-routable placeholder: the preflight must carry an
# Origin to elicit CORS headers, but it must not look like a real referrer.
ORIGIN="https://probe.invalid"

req() { # req <host> <path> <role> <tag>
  local host="$1" path="$2" role="$3" tag="$4"
  SEQ=$((SEQ+1))
  if [ "$SEQ" -gt "$CAP" ]; then
    log "seq=$SEQ ABORTED supplementary cap $CAP reached before $host$path"
    return 1
  fi
  mkdir -p "$LOCKS"
  touch "$LOCKS/host-$host.lock"
  local url="https://$host$path"
  local code
  code=$(flock "$LOCKS/host-$host.lock" -c "
    sleep 2.5
    curl -sS --compressed -X OPTIONS \
      -H 'Origin: $ORIGIN' \
      -H 'Access-Control-Request-Method: POST' \
      -H 'Access-Control-Request-Headers: content-type' \
      -D '$OUT/headers/$tag.h' -o '$OUT/bodies/$tag.b' \
      -w '%{http_code}' '$url'
  " 2>"$OUT/headers/$tag.err")
  local exit=$?
  local ts; ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local nbytes=0 sha=""
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
  local status="${code:-000}"
  python3 - "$OUT/results.jsonl" "$SEQ" "$host" "$tag" "$role" "$path" "$status" \
            "$exit" "$nbytes" "$sha" "$ts" "$cf" <<'PY'
import json, sys
(_, out, seq, host, tag, role, path, status, exit_, nbytes, sha, ts, cf) = sys.argv
row = {
  "seq": int(seq), "host": host, "host_tag": tag, "method": "OPTIONS",
  "path": path, "role": role,
  "sent_headers": "Origin: https://probe.invalid | Access-Control-Request-Method: POST | "
                  "Access-Control-Request-Headers: content-type (empty body)",
  "http_status": status, "curl_exit": int(exit_),
  "body_bytes": int(nbytes), "body_sha256": sha,
  "ctype_full": cf, "ts_utc": ts,
  "budget": "SUPPLEMENTARY-14 (owner-authorised: complete a refuted claim)",
}
open(out, "a").write(json.dumps(row) + "\n")
PY
  log "$(date -u +%FT%TZ) seq=$SEQ $host $path method=OPTIONS role=$role status=$status bytes=$nbytes sha=$sha"
  echo "seq=$SEQ $host $path -> $status ${nbytes}B"
}

log() { printf '%s\n' "$*" >> "$OUT/run-options.log"; }

log "=== area I SUPPLEMENTARY OPTIONS run, $(date -u +%FT%TZ) ==="
log "supplementary cap=$CAP (planned 10, 4 spare) OPTIONS-only empty-body preflight"
log "origin=$ORIGIN  ACRM=POST  ACRH=content-type"
log "$(date -u +%FT%TZ) START"

for h in carelink-login-trials.minimed.com carelink-login.minimed.eu \
         carelink-login.minimed.com carelink-login.medtronic.eu \
         carelink-login.medtronic.com; do
  t=$(echo "$h" | sed 's/carelink-login//; s/\./-/g')
  # Control FIRST on every host, for the reason in FINDINGS.md §7 C3.
  req "$h" /oidc/registerx "CONTROL-absent-options-$t" "o01-c-$t"
  req "$h" /oidc/register  "CANDIDATE-liveness-options-$t" "o02-r-$t"
done

log "$(date -u +%FT%TZ) END supplementary total=$SEQ of a $CAP cap"
echo "SUPPLEMENTARY TOTAL $SEQ of a $CAP cap"