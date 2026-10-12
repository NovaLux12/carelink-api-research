#!/usr/bin/env bash
# Area I — Auth0 tenant behavioural differences. Claim issue #23.
# Cap 20 requests, GET only, 2.5 s apart per host, controls first on every host.
#
# Per-host serialisation: the sleep happens INSIDE the flock, so four pool
# workers queue on the same host lock instead of firing simultaneously.
# Lock files live in the MAIN clone's .loop/ (BRIEF §5). Never holds the gate
# lock, never holds two host locks.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE"
CAP=20
SEQ=0

# Lock directory: the MAIN clone's .loop/, found by walking up for
# .loop/BRIEF.md rather than hard-coded. A literal /home/<user> path is a leak
# the gate fails (research-gate.sh, "machine-specific paths"), and the pass runs
# from a worktree nested inside that same .loop/ tree.
LOCKS=""
d="$HERE"
while [ "$d" != "/" ]; do
  if [ -f "$d/.loop/BRIEF.md" ]; then LOCKS="$d/.loop"; break; fi
  d="$(dirname "$d")"
done
: "${LOCKS:?could not locate the pool .loop directory (walked up from $HERE looking for .loop/BRIEF.md)}"

declare -A HOSTSEQ=()

log() { printf '%s\n' "$*" >> "$OUT/run.log"; }

# Full response header block, lowercased keys, duplicates joined, "k: v|k: v".
# Header ORDER is deliberately dropped: HTTP/2 reorders and it is not evidence.
hdr_of() {
  awk 'NR>1' "$1" | tr -d '\r' | awk '
    /: / {
      i = index($0, ": "); k = tolower(substr($0, 1, i-1)); v = substr($0, i+2)
      if (k in agg) agg[k] = agg[k] ", " v; else agg[k] = v
    }
    END { for (k in agg) printf "%s: %s|", k, agg[k] }'
}

req() { # req <host> <path> <role> <tag>
  local host="$1" path="$2" role="$3" tag="$4"
  SEQ=$((SEQ+1))
  HOSTSEQ[$host]=$(( ${HOSTSEQ[$host]:-0} + 1 ))
  local hs="${HOSTSEQ[$host]}"
  if [ "$SEQ" -gt "$CAP" ]; then
    log "seq=$SEQ ABORTED cap $CAP reached before $host$path"
    return 1
  fi
  mkdir -p "$LOCKS"
  touch "$LOCKS/host-$host.lock"
  local url="https://$host$path"
  local code
  code=$(flock "$LOCKS/host-$host.lock" -c "
    sleep 2.5
    curl -sS --compressed \
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
  local ctype cf
  if [ -f "$OUT/headers/$tag.h" ]; then
    ctype=$(awk 'BEGIN{IGNORECASE=1}/^content-type:/{print substr($0,index($0,": ")+2)}' \
            "$OUT/headers/$tag.h" | tr -d '\r' | tail -1)
    cf=$(hdr_of "$OUT/headers/$tag.h" | sed 's/|$//')
  else
    ctype="(none)"; cf="(none)"
  fi
  [ -n "$ctype" ] || ctype="(none)"
  local status="${code:-000}"
  # Emit one ledger row. Content negotiation/oracle headers kept explicit.
  python3 - "$OUT/results.jsonl" <<PY
import json, sys
row = {
  "seq": $SEQ, "host_seq": $hs, "host": "$host", "host_tag": "$tag",
  "method": "GET", "path": "$path", "role": "$role",
  "sent_headers": "(none)",
  "http_status": "$status", "curl_exit": $exit,
  "content_type": """$ctype""".strip() or "(none)",
  "content_encoding": None, "server": None, "cache_control": None,
  "strict_transport_security": None, "access_control_allow_origin": None,
  "access_control_allow_credentials": None, "x_robots_tag": None,
  "ctype_full": """$cf""",
  "body_bytes": $nbytes, "body_sha256": """$sha""",
  "ts_utc": "$ts",
}
p = "$OUT/headers/$tag.h"
if not None:
    import re
    txt = open(p, errors="replace").read().replace("\r", "")
    for line in txt.split("\n")[1:]:
        if ": " not in line: continue
        k, v = line.split(": ", 1)
        k = k.lower(); v = v.strip()
        if k == "content-encoding": row["content_encoding"] = v
        elif k == "server": row["server"] = v
        elif k == "cache-control": row["cache_control"] = v
        elif k == "strict-transport-security": row["strict_transport_security"] = v
        elif k == "access-control-allow-origin": row["access_control_allow_origin"] = v
        elif k == "access-control-allow-credentials": row["access_control_allow_credentials"] = v
        elif k == "x-robots-tag": row["x_robots_tag"] = v
for k in ("content_encoding","server","cache_control","strict_transport_security",
          "access_control_allow_origin","access_control_allow_credentials","x_robots_tag"):
    if row[k] is None: row[k] = "(none)"
open(sys.argv[1], "a").write(json.dumps(row) + "\n")
PY
  log "$(date -u +%FT%TZ) seq=$SEQ host_seq=$hs $host $path role=$role status=$status ctype=$ctype bytes=$nbytes sha=$sha"
  echo "seq=$SEQ host_seq=$hs $host$path -> $status $ctype ${nbytes}B"
}

: > "$OUT/results.jsonl"
log "=== area I probe run, $(date -u +%FT%TZ) ==="
log "cap=$CAP delay=2.5s GET-only controls-first-per-host"
log "$(date -u +%FT%TZ) START"

# ---- Tenant set: five carelink-login.* hosts, every one named in the corpus ----
#  trials.minimed.com   AUTH-TENANT-FINDINGS §1 row 3; PROBE-FINDINGS §8 line 93
#  minimed.eu           AUTH-TENANT-FINDINGS §1 row 1
#  minimed.com          PROBE-FINDINGS §8 lines 403-406
#  medtronic.eu         AUTH-TENANT-FINDINGS §1 row 2
#  medtronic.com        PROBE-FINDINGS §8; RECON-SUBDOMAINS §4.1
#
# --- Trials tenant FIRST (claim issue: it is the least-compared, and §1's
#     "no separate auth handling" conclusion leans on it) ---

# CONTROL 1 — certainly-absent well-known path on the trials tenant. Proves
# what a MISSING document looks like on carelink-login.*: without it, "this
# field is absent" cannot be told from "this document is a fallback page".
req carelink-login-trials.minimed.com /.well-known/openid-configurationx \
    CONTROL-absent-wellknown-trials t01-trials-absent
# CONTROL 2 — the known-live document on the same host, immediately after.
req carelink-login-trials.minimed.com /.well-known/openid-configuration \
    CONTROL-live-oidc-trials t02-trials-oidc
# First data cells on the never-compared tenant.
req carelink-login-trials.minimed.com /.well-known/jwks.json \
    CANDIDATE-jwks-trials t03-trials-jwks
req carelink-login-trials.minimed.com /oidc/register \
    CANDIDATE-registration-reachability-trials t04-trials-register

req carelink-login.minimed.eu /.well-known/openid-configuration \
    CANDIDATE-oidc-minimed-eu t05-eu-oidc
req carelink-login.minimed.eu /.well-known/jwks.json \
    CANDIDATE-jwks-minimed-eu t06-eu-jwks
req carelink-login.minimed.eu /oidc/register \
    CANDIDATE-registration-reachability-minimed-eu t07-eu-register

req carelink-login.minimed.com /.well-known/openid-configuration \
    CANDIDATE-oidc-minimed-com t08-us-oidc
req carelink-login.minimed.com /.well-known/jwks.json \
    CANDIDATE-jwks-minimed-com t09-us-jwks
req carelink-login.minimed.com /oidc/register \
    CANDIDATE-registration-reachability-minimed-com t10-us-register

req carelink-login.medtronic.eu /.well-known/openid-configuration \
    CANDIDATE-oidc-medtronic-eu t11-meu-oidc
req carelink-login.medtronic.eu /.well-known/jwks.json \
    CANDIDATE-jwks-medtronic-eu t12-meu-jwks
req carelink-login.medtronic.eu /oidc/register \
    CANDIDATE-registration-reachability-medtronic-eu t13-meu-register

# CONTROL 1b — the absent-path control repeated on a second, differently
# configured host (a shadow tenant), before that host's candidates. One host's
# 404 proves nothing about the next host's front door.
req carelink-login.medtronic.com /.well-known/openid-configurationx \
    CONTROL-absent-wellknown-medtronic-com t14-mcom-absent
req carelink-login.medtronic.com /.well-known/openid-configuration \
    CANDIDATE-oidc-medtronic-com t15-mcom-oidc
req carelink-login.medtronic.com /.well-known/jwks.json \
    CANDIDATE-jwks-medtronic-com t16-mcom-jwks
req carelink-login.medtronic.com /oidc/register \
    CANDIDATE-registration-reachability-medtronic-com t17-mcom-register

log "$(date -u +%FT%TZ) END total=$SEQ"
echo "TOTAL $SEQ of a $CAP cap"