#!/usr/bin/env bash
# Area AJ — does the cumulus-v2 base carry a `display/message` route at all?
# Claim: NovaLux12/carelink-api-research#182. Cap 18, >=2.5 s per host, INSIDE the flock.
#
# THE SINGLE SOURCE OF THE CAP. One assignment, here; `cap_guard` reads it, and
# FINDINGS.md's "N of a 18 cap" line must equal `wc -l results.jsonl`.
#
#   CAP=18  ==  6 cells x 3 hosts
#
#   per host:
#     1 GET     connect/carepartner/v13/display/message   CONTROL-LIVE   (recorded 401 + x-ca-err 990)
#     2 GET     connect/carepartner/v2/zz-aj-absent-8713  CONTROL-ABSENT (must be the 42 B no-route digest)
#     3 GET     connect/carepartner/v2/display/message    THE QUESTION
#     4 OPTIONS connect/carepartner/v2/display/message    THE QUESTION, method axis
#     5 GET     connect/carepartner/v2/discover/android/3.6   NEARBY CELL (is the v2 base routed at all?)
#     6 OPTIONS connect/carepartner/v2/discover/android/3.6   NEARBY CELL, method axis
#
# Why both methods on both leaves: docs/09 Oracle A needs the pair. A leaf that is
# GET-403 + OPTIONS-403 is dead on every tested method; GET-403 + OPTIONS-200 is
# live-but-POST-only (that is how csr/v2 and bare connect/v2 were found). Reading a
# GET-403 as "does not exist" is exactly the error this area exists to avoid.
#
# Why cell 5 is worth two of the eighteen: on `clcloud-trials.minimed.com` the v2
# base path IS routed (GET v2/discover/android/3.6 -> 200, 10 053 B, digest
# 1aab9bb1e721..., findings-log/2026-10-17-discover-3host-matrix/FINDINGS.md:143).
# So a no-route verdict on v2/display/message at -trials cannot be explained away as
# "the whole v2 base is unrouted on this host" — that is what cell 5 rules out, per host.
#
# GET only, plus empty-body OPTIONS. No POST, no token, no cookie, no auth, no wordlist.
#
# Usage: probe.sh all      # the 18-cell sweep (controls first on every host)
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"        # findings-log/<dir> -> repo root (two levels)
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$HERE/headers"                  # small bodies only (<=10 KB); committed as evidence
mkdir -p "$SCRATCH" "$REPO/.loop"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=18

HOSTS="clcloud.minimed.com clcloud-trials.minimed.com clcloud.minimed.eu"

ABSENT="connect/carepartner/v2/zz-aj-absent-8713"
ABSENT_TAG_PREFIX="c2-"
NO_ROUTE_SHA="f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16"

[ -f "$LEDGER" ] || : > "$LEDGER"
SEQ=$(awk 'NF' "$LEDGER" 2>/dev/null | wc -l | tr -d ' '); SEQ=${SEQ:-0}
[ -f "$RUNLOG" ] || : > "$RUNLOG"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$*" >> "$RUNLOG"; }
ledger_len() { awk 'NF' "$LEDGER" 2>/dev/null | wc -l | tr -d ' '; }

cap_guard() {
  local n; n=$(ledger_len)
  if [ "$n" -ge "$CAP" ]; then log "CAP STOP at $n of $CAP"; echo "CAP STOP: $n of $CAP" >&2; return 1; fi
  return 0
}

# req <method> <host> <path> <role> <tag>
req() {
  local method="$1" host="$2" path="$3" role="$4" tag="$5"
  cap_guard || return 1
  SEQ=$((SEQ+1))
  local out="$SCRATCH/$tag" tq ts td code exitc
  tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  local -a cargs=(-s --compressed --max-time 120 -A "$UA" -D "$out.hdr" -o "$out.body" -w '%{http_code}')
  [ "$method" = OPTIONS ] && cargs+=(--request OPTIONS)
  touch "$REPO/.loop/host-$host.lock" 2>/dev/null || true
  exec 9>"$REPO/.loop/host-$host.lock"
  flock 9
  sleep "$DELAY"                       # the sleep is INSIDE the per-host lock
  ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  code=$(curl "${cargs[@]}" "https://$host/$path" 2>>"$RUNLOG")
  exitc=$?
  flock -u 9
  exec 9>&-
  td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  python3 - "$LEDGER" "$out.hdr" "$out.body" "$SEQ" "$method" "$host" "$tag" "$path" "$role" "$code" "$exitc" "$tq" "$ts" "$td" <<'PY'
import json, sys, os, hashlib
(L, hp, bp, seq, method, host, tag, path, role, code, exitc,
 tq, ts, td) = sys.argv[1:15]
# x-ca-err and x-amzn-errortype are the ORACLE on this family — they must be kept,
# or the ledger records a status code and no verdict.
KEEP = ('content-type','content-length','content-encoding','allow','server','vary',
        'cache-control','access-control-allow-origin','access-control-allow-methods',
        'access-control-allow-headers','x-amzn-errortype','x-ca-err','x-amzn-requestid',
        'x-cum-signature')
hdrs = {}
if os.path.exists(hp):
    for line in open(hp, 'rb').read().decode('latin-1').splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            if k.strip().lower() in KEEP:
                hdrs[k.strip().lower()] = v.strip()
n = os.path.getsize(bp) if os.path.exists(bp) else 0
d = hashlib.sha256(open(bp,'rb').read()).hexdigest() if n else ''
row = {"seq": int(seq), "host": host, "tag": tag, "method": method, "path": path,
       "role": role, "http_status": code, "curl_exit": int(exitc),
       "body_bytes": n, "body_sha256": d,
       "content_type": hdrs.get('content-type','(none)'),
       "x_amzn_errortype": hdrs.get('x-amzn-errortype','(none)'),
       "x_ca_err": hdrs.get('x-ca-err','(none)'),
       "allow": hdrs.get('allow','(none)'),
       "acam": hdrs.get('access-control-allow-methods','(none)'),
       "acao": hdrs.get('access-control-allow-origin','(none)'),
       "content_encoding": hdrs.get('content-encoding','(none)'),
       "server": hdrs.get('server','(none)'),
       "headers": hdrs, "t_queued": tq, "t_sent": ts, "t_done": td}
open(L, 'a').write(json.dumps(row) + "\n")
print(f"seq={seq} {method:7s} {host}{path} -> {code} errtype={hdrs.get('x-amzn-errortype','-')} "
      f"ca_err={hdrs.get('x-ca-err','-')} bytes={n} sha256={d[:16]} acam={hdrs.get('access-control-allow-methods','-')}")
PY
  log "seq=$SEQ $method https://$host/$path status=$code exit=$exitc tag=$tag role=[$role]"
}

sweep() {
  local h htag
  for h in $HOSTS; do
    htag=$(echo "$h" | tr . -)
    # ---- controls first, per host (2) --------------------------------------
    req GET "$h" "connect/carepartner/v13/display/message" \
      "CONTROL-LIVE: recorded 401 UnauthorizedException + x-ca-err 990 on all three hosts (findings-log/2026-10-12-csr-cross-host/FINDINGS.md rows 1,9; area C rows 1). Proves this host still routes a carepartner display/message leaf and that the Layer7 authorizer answers" \
      "c1-$htag-v13-display-message" || return 1
    local atag="c2-$htag-v2-absent"
    req GET "$h" "$ABSENT" \
      "CONTROL-ABSENT: fabricated leaf under the v2 base. Must answer 403 at the 42 B no-route digest f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16. If it does not, the oracle has moved and this run's verdicts are void" \
      "$atag" || return 1
    # The absent control is a GATE, not a datapoint: if the oracle has moved, every
    # verdict below is void. Digest AND size AND status are all checked, because a
    # body that hashes right at the wrong length is a different artefact.
    local d; d=$(python3 -c '
import json,sys
for line in open(sys.argv[1]):
    r=json.loads(line)
    if r["tag"]==sys.argv[2]:
        print(r["body_sha256"], r["body_bytes"], r["http_status"])
' "$LEDGER" "$atag")
    if [ "$d" != "$NO_ROUTE_SHA 42 403" ]; then
      log "ABSENT CONTROL FAILED on $h: got [$d], oracle requires [$NO_ROUTE_SHA 42 403] — SWEEP ABORTED"
      echo "ABSENT CONTROL FAILED on $h: got [$d] — oracle has moved; see run.log" >&2
      return 9
    fi
    log "absent control OK on $h: $d (oracle reproduces)"
    # ---- the question (2) --------------------------------------------------
    req GET "$h" "connect/carepartner/v2/display/message" \
      "QUESTION GET: the v2 track's own display/message leaf — named by the cumulus-v2 spike as GET {baseUrlCumulus}/display/message where baseUrlCumulus is /connect/carepartner/v2, and probed exactly once before (VERSION-AXIS.md row 42, .eu, GET only, 403). No OPTIONS on this leaf is recorded anywhere" \
      "q1-$htag-v2-display-message-GET" || return 1
    req OPTIONS "$h" "connect/carepartner/v2/display/message" \
      "QUESTION OPTIONS (empty body, no -d): the method axis. GET-403 + OPTIONS-403 = dead on every tested method; GET-403 + OPTIONS-200 = live, POST-only (the csr/v2 and bare connect/v2 signature)" \
      "q2-$htag-v2-display-message-OPTIONS" || return 1
    # ---- the nearby cell (2) ----------------------------------------------
    req GET "$h" "connect/carepartner/v2/discover/android/3.6" \
      "NEARBY GET: is the v2 base routed on this host at all? Recorded 200 / 10 053 B / sha256 1aab9bb1e721... on -trials only, no-route on .eu and .com (findings-log/2026-10-17-discover-3host-matrix/FINDINGS.md:143,347). Rules out 'the whole v2 base is unrouted' as an explanation for a negative on the question above" \
      "n1-$htag-v2-discover-3.6-GET" || return 1
    req OPTIONS "$h" "connect/carepartner/v2/discover/android/3.6" \
      "NEARBY OPTIONS (empty body, no -d): method axis for the same leaf, so the v2 base gets the same two-method treatment the question gets" \
      "n2-$htag-v2-discover-3.6-OPTIONS" || return 1
  done
}

case "${1:-}" in
  all) sweep ;;
  *) echo "usage: probe.sh all" >&2; exit 64 ;;
esac
echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
