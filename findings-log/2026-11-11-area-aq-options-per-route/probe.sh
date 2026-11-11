#!/usr/bin/env bash
# Area AQ — does `OPTIONS` resolve PER ROUTE, or subtree-wide, under the three bases whose
# "live, POST-only" verdicts rest on an unvalidated `OPTIONS 200`?
#
# Claim: NovaLux12/carelink-api-research#209.  Branch: research/aq-options-per-route.
#
# HOSTS (this lane owns these three and NO others — the clinic hosts and carelinkhp belong
# to sibling lanes, and touching them would contaminate their spacing figures):
#   clcloud.minimed.com
#   clcloud.minimed.eu
#   clcloud-trials.minimed.com
#
# ---------------------------------------------------------------------------------------
# THE PLAN — every cell itemised BEFORE the first request.  24 planned, CAP=24, 0 reserve.
#
# Per host, in this order (controls are GATES: a mismatch exits 9 and no question cell for
# that host is issued):
#
#   1  GET      connect/carepartner/v13/display/message     CONTROL-LIVE   must be 401,
#                                                           36 B, d551247201fc8fc2…
#   2  GET      connect/carepartner/v2/zz-aq2-absent-7241   CONTROL-ABSENT must be 403,
#                                                           42 B, f249b63cb2fcb6… (the
#                                                           published no-route digest).
#                                                           This GET is what establishes
#                                                           "certainly absent" for the
#                                                           OPTIONS on the same literal.
#   3  OPTIONS  connect/csr/v2/zz-aq2-absent-7241           ***DECIDING CELL*** fabricated
#                                                           sibling of csr/v2/display/message
#   4  OPTIONS  connect/csr/v2/display/message              the real leaf, same run (area C
#                                                           seq 16 recorded 200 + ACAO *)
#   5  OPTIONS  connect/v2/zz-aq2-absent-7241               ***DECIDING CELL*** bare v2
#   6  OPTIONS  connect/v2/display/message                  the real leaf, same run (area C
#                                                           seq 26 recorded 200 + ACAO *)
#   7  OPTIONS  connect/carepartner/v6/zz-aq2-absent-7241   ***DECIDING CELL*** v6
#   8  OPTIONS  connect/carepartner/v6/display/message      the real leaf, same run (area Z
#                                                           recorded 200 + ACAO * ×3)
#
# 8 cells × 3 hosts = 24 = CAP.  Zero reserve: a 000/5xx/timeout is recorded as a FAILURE
# and NOT retried.  (Zero reserve is deliberate — the two controls are gates, so the only
# thing a reserve could buy is a retry of a cell whose value is already uninformative when
# it fails.)
#
# ---------------------------------------------------------------------------------------
# WHY ONE FABRICATED NAME SERVES ALL THREE SUBTREES
#
# `zz-aq2-absent-7241` is nonsense, sits at the SAME depth as each subtree's
# `display/message` leaf (two segments below the base), and has zero hits repo-wide at this
# head (`git grep -c 'zz-aq2-absent-7241' -- .` → only this file).  Its standing as absent
# is MEASURED, not asserted, on every host by cell 2's GET answering the published 42 B
# no-route body — but cell 2 measures it under `carepartner/v2`, not under `csr/v2` or `v6`.
#
# The CSS/scoring logic does NOT depend on that measurement, and the asymmetry is the point:
#   fabricated OPTIONS → 200 (+ CORS)  => the base answers preflight for paths it has no
#                                          route for => SUBTREE-WIDE => the verdict's
#                                          OPTIONS half FALLS.  Definitive in one cell.
#   fabricated OPTIONS → 403 at the no-route digest => no route matched that path for that
#                                          method.  A 403 is the gateway's unmatched-route
#                                          answer on this family (docs/09 §2 Oracle A), so
#                                          this falsifies a blanket-200 in the subtree
#                                          whether or not the literal is otherwise unused.
# So a 200 is a decisive negative for the verdicts; a 403 is the per-route reading, and its
# strength is that it reproduces the control's digest rather than any argument about the name.
#
# ---------------------------------------------------------------------------------------
# METHOD DISCIPLINE
#   GET + empty-body OPTIONS only (`--request OPTIONS`, never `-X OPTIONS` with a body).
#   No POST, no token, no cookie, no Authorization, no x-api-key, no X-System-ID, no
#   wordlist, no DNS, no port scan, no dev/stage host.
#   sleep 2.5 INSIDE the per-host flock on $REPO/.loop/host-<host>.lock.
#   Kernel body mtime captured per request into the ledger, so the second spacing clock can
#   be PROVEN to be a second clock (distinct mtimes, each inside its own request window)
#   rather than assumed.
#
# Usage: probe.sh            # all three hosts, controls first on each
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/aq2-scratch"
mkdir -p "$SCRATCH"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=24

DIGEST_LIVE=d551247201fc8fc27dee1ae62538455ea04258855f1880443176930399875a7a
DIGEST_ABSENT=f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16

HOSTS=(clcloud.minimed.com clcloud.minimed.eu clcloud-trials.minimed.com)
FAB=zz-aq2-absent-7241

[ -f "$LEDGER" ] || : > "$LEDGER"
[ -f "$RUNLOG" ] || : > "$RUNLOG"
SEQ=$(awk 'NF' "$LEDGER" | wc -l | tr -d ' '); SEQ=${SEQ:-0}

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$*" >> "$RUNLOG"; }
ledger_len() { awk 'NF' "$LEDGER" | wc -l | tr -d ' '; }

cap_guard() {
  local n; n=$(ledger_len)
  if [ "$n" -ge "$CAP" ]; then log "CAP STOP at $n of $CAP"; echo "CAP STOP: $n of $CAP" >&2; return 1; fi
  return 0
}

# req <method> <path> <role> <tag>
req() {
  local method="$1" path="$2" role="$3" tag="$4"
  cap_guard || return 1
  SEQ=$((SEQ+1))
  local out="$SCRATCH/$tag" tq ts td code exitc mtime
  rm -f "$out.h" "$out.b"                 # so a stale body cannot be read as this request's
  tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  local -a cargs=(-s --compressed --max-time 120 -A "$UA" -D "$out.h" -o "$out.b" -w '%{http_code}')
  [ "$method" = OPTIONS ] && cargs+=(--request OPTIONS)
  touch "$REPO/.loop/host-$HOST.lock" 2>/dev/null || true
  exec 9>"$REPO/.loop/host-$HOST.lock"
  flock 9
  sleep "$DELAY"                          # the sleep is INSIDE the per-host lock
  ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  code=$(curl "${cargs[@]}" "https://$HOST$path" 2>>"$RUNLOG")
  exitc=$?
  # kernel mtime of the response body, set at write time — the second clock
  if [ -f "$out.b" ]; then mtime=$(stat -c %.9Y "$out.b"); else mtime=0; fi
  flock -u 9
  exec 9>&-
  td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  python3 - "$LEDGER" "$out.h" "$out.b" "$SEQ" "$method" "$HOST" "$tag" "$path" "$role" "$code" "$exitc" "$tq" "$ts" "$td" "$mtime" <<'PY'
import json, sys, os, hashlib
(L, hp, bp, seq, method, host, tag, path, role, code, exitc,
 tq, ts, td, mtime) = sys.argv[1:16]
KEEP = ('content-type','content-length','content-encoding','allow','server','vary',
        'cache-control','access-control-allow-origin','access-control-allow-methods',
        'access-control-allow-headers','access-control-expose-headers',
        'x-amzn-errortype','x-ca-err','x-amz-apigw-id','x-cache','x-amzn-requestid',
        'x-amz-cf-id','via')
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
       "errortype": hdrs.get('x-amzn-errortype','(none)'),
       "ca_err": hdrs.get('x-ca-err','(none)'),
       "allow": hdrs.get('allow','(none)'),
       "acam": hdrs.get('access-control-allow-methods','(none)'),
       "acao": hdrs.get('access-control-allow-origin','(none)'),
       "acah": hdrs.get('access-control-allow-headers','(none)'),
       "x_cache": hdrs.get('x-cache','(none)'),
       "content_encoding": hdrs.get('content-encoding','(none)'),
       "headers": hdrs, "t_queued": tq, "t_sent": ts, "t_done": td,
       "body_mtime": mtime}
open(L, 'a').write(json.dumps(row) + "\n")
print(f"seq={seq} {host} {method} {path} -> {code} errtype={hdrs.get('x-amzn-errortype','-')} "
      f"bytes={n} sha256={d[:16]} acao={hdrs.get('access-control-allow-origin','-')} "
      f"acam={hdrs.get('access-control-allow-methods','-')} mtime={mtime}")
PY
  log "seq=$SEQ host=$HOST $method https://$HOST$path status=$code exit=$exitc tag=$tag role=[$role]"
}

# cell <seq> -> "host|status|bytes|digest"
cell() {
  python3 - "$LEDGER" "$1" <<'PY'
import json,sys
L,seq=sys.argv[1],int(sys.argv[2])
for line in open(L):
    if not line.strip(): continue
    r=json.loads(line)
    if r["seq"]==seq:
        print(f'{r["host"]}|{r["http_status"]}|{r["body_bytes"]}|{r["body_sha256"]}')
        break
PY
}

# gate <seq> <want_host> <want_status> <want_bytes> <want_digest_prefix> <name>
gate() {
  local got h st by dg
  got=$(cell "$1"); h=${got%%|*}; rest=${got#*|}; st=${rest%%|*}; rest=${rest#*|}
  by=${rest%%|*}; dg=${rest#*|}
  if [ "$h" != "$2" ] || [ "$st" != "$3" ] || [ "$by" != "$4" ] || [ "${dg:0:${#5}}" != "$5" ]; then
    log "GATE FAIL $6: got $h/$st/$by/${dg:0:16} want $2/$3/$4/$5"
    echo "GATE FAIL $6: got $h/$st/$by/${dg:0:16} want $2/$3/$4/${5} — ABORT, oracle has moved" >&2
    return 9
  fi
  log "GATE OK $6: $h $st/$by/${dg:0:16}"
  echo "GATE OK $6: $h $st/$by/${dg:0:16}"
  return 0
}

# have_tag <tag> — a row for this tag is already in the ledger (a resumed run must not
# re-spend a request on a cell it already bought).
have_tag() { awk 'NF' "$LEDGER" | grep -q "\"tag\": \"$1\""; }
seq_of_tag() { awk 'NF' "$LEDGER" | python3 -c 'import json,sys
t=sys.argv[1]
for l in sys.stdin:
    r=json.loads(l)
    if r["tag"]==t: print(r["seq"]); break' "$1"; }

# req_once <tag> <method> <path> <role>
req_once() {
  local tag="$1"
  if have_tag "$tag"; then echo "tag $tag already in ledger — not re-requesting"; return 0; fi
  req "$2" "$3" "$4" "$tag" || return 1
}

log "=== START area AQ  plan=24 cap=$CAP hosts=${HOSTS[*]}"

for H in "${HOSTS[@]}"; do
  HOST="$H"
  slug=$(printf '%s' "$H" | tr '.' '-')
  echo "-------- $HOST (controls first) --------"
  log "HOST $HOST begin"

  req_once "c1-$slug-live-v13" GET "/connect/carepartner/v13/display/message" \
    "CONTROL-LIVE: recorded 401 UnauthorizedException + x-ca-err 990, 36 B, d5512472… on all three cumulus hosts (area AP §2; area AG). Proves the host still routes a carepartner display/message leaf and the authorizer answers" \
    || exit 0
  req_once "c2-$slug-absent-v2" GET "/connect/carepartner/v2/$FAB" \
    "CONTROL-ABSENT / GATE: fabricated name in the carepartner/v2 subtree at the same depth as every question leaf. Recorded no-route shape: 403 MissingAuthenticationTokenException, 42 B, f249b63c… (docs/09 §2 Oracle A). Establishes the literal as certainly absent for the OPTIONS cells" \
    || exit 0

  gate "$(seq_of_tag "c1-$slug-live-v13")"   "$HOST" 401 36 "$DIGEST_LIVE"   "control-live $HOST"   || exit 9
  gate "$(seq_of_tag "c2-$slug-absent-v2")"  "$HOST" 403 42 "$DIGEST_ABSENT" "control-absent $HOST" || exit 9
  echo "ORACLE RE-ESTABLISHED on $HOST — question cells follow" | tee -a "$RUNLOG"

  req_once "q-$slug-csr-fab" OPTIONS "/connect/csr/v2/$FAB" \
    "THE CELL (csr/v2): empty-body OPTIONS to a fabricated name in the same subtree as csr/v2/display/message. 403 at the no-route digest => the base resolves OPTIONS per route and the csr verdict's OPTIONS half stands. 200 + CORS => subtree-wide preflight and the verdict FALLS to 'no GET route'" \
    || exit 0
  req_once "q-$slug-csr-leaf" OPTIONS "/connect/csr/v2/display/message" \
    "Real leaf, same run (area C seq 16 / area N seq 6,14: 200, 0 B, ACAO *). Pairing it with the fabricated sibling in ONE run is what makes a one-off distinguishable from a stable door" \
    || exit 0

  req_once "q-$slug-v2-fab" OPTIONS "/connect/v2/$FAB" \
    "THE CELL (bare v2): fabricated sibling of connect/v2/display/message. Same reading rule as above" \
    || exit 0
  req_once "q-$slug-v2-leaf" OPTIONS "/connect/v2/display/message" \
    "Real leaf, same run (area C seq 26 / area N seq 8,16: 200, 0 B, ACAO *)" \
    || exit 0

  req_once "q-$slug-v6-fab" OPTIONS "/connect/carepartner/v6/$FAB" \
    "THE CELL (v6): fabricated sibling of connect/carepartner/v6/display/message. Same reading rule as above" \
    || exit 0
  req_once "q-$slug-v6-leaf" OPTIONS "/connect/carepartner/v6/display/message" \
    "Real leaf, same run (area Z seq 15,32,49: 200, 0 B, ACAO *, ACAM OPTIONS)" \
    || exit 0

  log "HOST $HOST done"
done

echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
log "DONE rows=$(ledger_len) cap=$CAP"
