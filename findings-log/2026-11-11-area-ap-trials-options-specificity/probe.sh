#!/usr/bin/env bash
# Area AP — is the `-trials` `OPTIONS 200` on `connect/carepartner/v2/display/message`
# path-specific, or does the `/connect/carepartner/v2/` subtree on this host answer
# OPTIONS with 200 for absent paths too?
#
# Claim: NovaLux12/carelink-api-research#197.  Host: clcloud-trials.minimed.com ONLY
# (four other lanes own the other hosts; a cross-host probe would contaminate their
# spacing figures).
#
# THE CELLS — itemised BEFORE the first request. 7 planned, CAP=8, 1 unspent reserve.
#
#   1  GET      connect/carepartner/v13/display/message       CONTROL-LIVE  must be 401,
#                                                             36 B, d551247201fc8fc2…
#   2  GET      connect/carepartner/v2/zz-ap-absent-4821      CONTROL-ABSENT must be 403,
#                                                             42 B, f249b63cb2fc…
#                                                             --- both are GATES: mismatch aborts
#   3  OPTIONS  connect/carepartner/v2/zz-ap-absent-4821      ***THE CELL*** fabricated name,
#                                                             same subtree, same depth
#   4  OPTIONS  connect/carepartner/v2/display/message        re-run AJ's positive (AJ seq 10)
#   5  OPTIONS  connect/carepartner/v2/zz-ap-absent-4821/zz   second fabricated name, +1 depth
#   6  OPTIONS  connect/carepartner/v2/discover/android/3.6   counter-cell — AJ's 403 (AJ seq 12)
#   7  GET      connect/carepartner/v2/display/message        the GET half of the seq-4 pair
#                                                             (AJ seq 9), so the verdict rule
#                                                             is read from one run
#
# Fabricated names `zz-ap-absent-4821` / `zz-ap-absent-4821/zz` are derived from the
# observed convention only in the sense that they sit at the same depths as the real
# leaves; their standing as "certainly absent" is established by cell 2 (GET → the
# no-route 403 at the published digest) and by `git grep` returning 0 hits repo-wide.
# No wordlist, no fuzzing: two names, three question cells.
#
# GET + empty-body OPTIONS only (`--request OPTIONS`, never `-X OPTIONS` with a body).
# No POST, no token, no cookie, no Authorization, no x-api-key, no X-System-ID.
#
# sleep 2.5 INSIDE the per-host flock on $REPO/.loop/host-clcloud-trials.minimed.com.lock.
#
# The kernel body mtime is captured per request and written to the ledger, so the
# second clock can be PROVEN to be a second clock (distinct mtimes, each inside its
# own request window) rather than assumed — three prior passes published a
# kernel-mtime cross-check that was dead because one checkout stamped every body.
#
# Usage: probe.sh            # controls, then the question cells
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/ap-scratch"
mkdir -p "$SCRATCH"

HOST="clcloud-trials.minimed.com"
UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=8

DIGEST_LIVE=d551247201fc8fc2
DIGEST_ABSENT=f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16

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
        'x-amzn-errortype','x-ca-err','x-amz-apigw-id','x-cache','x-amzn-requestid')
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
print(f"seq={seq} {method} {path} -> {code} errtype={hdrs.get('x-amzn-errortype','-')} "
      f"bytes={n} sha256={d[:16]} acao={hdrs.get('access-control-allow-origin','-')} "
      f"acam={hdrs.get('access-control-allow-methods','-')} mtime={mtime}")
PY
  log "seq=$SEQ $method https://$HOST$path status=$code exit=$exitc tag=$tag role=[$role]"
}

# read back cell <seq> as "status|bytes|digest"
cell() {
  python3 - "$LEDGER" "$1" <<'PY'
import json,sys
L,seq=sys.argv[1],int(sys.argv[2])
for line in open(L):
    if not line.strip(): continue
    r=json.loads(line)
    if r["seq"]==seq:
        print(f'{r["http_status"]}|{r["body_bytes"]}|{r["body_sha256"]}')
        break
PY
}

gate() {   # gate <seq> <want_status> <want_bytes> <want_digest_prefix> <name>
  local got st by dg
  got=$(cell "$1"); st=${got%%|*}; rest=${got#*|}; by=${rest%%|*}; dg=${rest#*|}
  if [ "$st" != "$2" ] || [ "$by" != "$3" ] || [ "${dg:0:${#4}}" != "$4" ]; then
    log "GATE FAIL $5: got $st/$by/${dg:0:16} want $2/$3/$4"
    echo "GATE FAIL $5: got $st/$by/${dg:0:16} want $2/$3/$4 — ABORT, oracle has moved" >&2
    return 9
  fi
  log "GATE OK $5: $st/$by/${dg:0:16}"
  echo "GATE OK $5: $st/$by/${dg:0:16}"
  return 0
}

# have_tag <tag> — a row for this tag is already in the ledger (a resumed run must not
# re-spend a request on a control it already bought).
have_tag() { awk 'NF' "$LEDGER" | grep -q "\"tag\": \"$1\""; }
seq_of_tag() { awk 'NF' "$LEDGER" | python3 -c 'import json,sys
t=sys.argv[1]
for l in sys.stdin:
    r=json.loads(l)
    if r["tag"]==t: print(r["seq"]); break' "$1"; }

# ---------------------------------------------------------------- controls FIRST
if have_tag c1-live-v13-message; then
  echo "seq 1 already in ledger — gating it, not re-requesting"
else
req GET "/connect/carepartner/v13/display/message" \
  "CONTROL-LIVE: recorded 401 UnauthorizedException + x-ca-err 990, 36 B, d551247201fc8fc2… on all three cumulus hosts (AJ §2; area AG). Proves the host still routes a carepartner display/message leaf and the authorizer answers" \
  c1-live-v13-message || exit 0
fi

if have_tag c2-absent-v2-fab; then
  echo "seq 2 already in ledger — gating it, not re-requesting"
else
req GET "/connect/carepartner/v2/zz-ap-absent-4821" \
  "CONTROL-ABSENT / GATE: fabricated name in the SAME subtree at the same depth as the question cell. Recorded no-route shape: 403 MissingAuthenticationTokenException, 42 B, f249b63cb2fcb66b… (docs/09 §2 Oracle A). This GET is what establishes 'certainly absent' for the OPTIONS in seq 3" \
  c2-absent-v2-fab || exit 0
fi

gate "$(seq_of_tag c1-live-v13-message)" 401 36 "$DIGEST_LIVE" "control-live"    || exit 9
gate "$(seq_of_tag c2-absent-v2-fab)"    403 42 "$DIGEST_ABSENT" "control-absent" || exit 9
echo "ORACLE RE-ESTABLISHED — question cells follow" | tee -a "$RUNLOG"

# ---------------------------------------------------------------- question cells
req OPTIONS "/connect/carepartner/v2/zz-ap-absent-4821" \
  "THE CELL: empty-body OPTIONS on the fabricated path in the /connect/carepartner/v2/ subtree. 403 at the no-route digest => AJ's 200 on 2/display/message is PATH-SPECIFIC and stands. 200 (+CORS) => the subtree answers OPTIONS 200 for absent paths and AJ's positive does NOT stand" \
  q3-options-v2-fab || exit 0

req OPTIONS "/connect/carepartner/v2/display/message" \
  "AJ's POSITIVE re-run (AJ seq 10): recorded 200, 0 B, ACAO *, ACAM OPTIONS on this host. Re-issuing it beside the control is what makes a one-off distinguishable from a stable door" \
  q4-options-v2-message || exit 0

req OPTIONS "/connect/carepartner/v2/zz-ap-absent-4821/zz" \
  "SECOND FABRICATED NAME, +1 depth: if OPTIONS 200 is keyed on the /v2/ prefix rather than a route, a deeper absent path should also answer 200. Distinguishes a subtree-wide catch-all from a depth-specific one" \
  q5-options-v2-fab-deep || exit 0

req OPTIONS "/connect/carepartner/v2/discover/android/3.6" \
  "COUNTER-CELL: AJ seq 12 — recorded 403 no-route on this host on a sibling leaf whose GET is 200. Reproduces AJ's own exclusion of a blanket-200 and is the 'a 403 is still available here' proof" \
  q6-options-discover || exit 0

req GET "/connect/carepartner/v2/display/message" \
  "GET half of the seq-4 pair (AJ seq 9): recorded 403 no-route. Read in the same run as seq 4, so GET 403 + OPTIONS <status> is one observation, not two hops" \
  q7-get-v2-message || exit 0

echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
log "DONE rows=$(ledger_len) cap=$CAP"
