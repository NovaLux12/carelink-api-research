#!/usr/bin/env bash
# Area AZ — is the per-route `OPTIONS` resolution STABLE across passes, and does a
# fabricated name at DEPTH 2 answer the same way as one at leaf depth?
#
# Claim: NovaLux12/carelink-api-research#221.  Branch: research/laz.
#
# HOSTS (this lane owns these three and NO others):
#   clcloud.minimed.com
#   clcloud.minimed.eu
#   clcloud-trials.minimed.com
#
# ---------------------------------------------------------------------------------------
# THE PLAN — every cell itemised BEFORE the first question request.  23 harnessed cells,
# CAP=24, and the 24th wire request is the pre-flight GET disclosed in FINDINGS.md §1a.
#
# Per host, in this order (the control is a GATE: a mismatch exits 9 and no question cell
# for that host is issued):
#
#   1  GET      connect/carepartner/v2/zz-aq2-absent-7241   CONTROL-ABSENT / GATE
#                                                           must be 403, 42 B,
#                                                           f249b63cb2fcb6… — the corpus
#                                                           no-route digest.
#   2  OPTIONS  connect/csr/v2/zz-aq2-absent-7241            REPRODUCTION of AY seq 3/11/19
#   3  OPTIONS  connect/csr/v2/display/message               REPRODUCTION of AY seq 4/12/20
#   4  OPTIONS  connect/v2/zz-aq2-absent-7241                REPRODUCTION of AY seq 5/13/21
#   5  OPTIONS  connect/v2/display/message                   REPRODUCTION of AY seq 6/14/22
#   6  OPTIONS  connect/carepartner/v6/zz-aq2-absent-7241    REPRODUCTION of AY seq 7/15/23
#   7  OPTIONS  connect/carepartner/v6/display/message       REPRODUCTION of AY seq 8/16/24
#
# Then, one DEPTH-2 fabricated name per subtree on two of the three hosts (the cap buys
# two, not three — the third is named as unspent in FINDINGS.md §6):
#
#   8  .com      OPTIONS  connect/csr/v2/zz-az2-absent-9917/deeper
#   8  .eu       OPTIONS  connect/carepartner/v6/zz-az2-absent-9917/deeper
#
# 7 cells x 3 hosts + 2 depth cells = 23 harnessed.  Zero reserve: a 000/5xx/timeout is
# recorded as a FAILURE and NOT retried.
#
# ---------------------------------------------------------------------------------------
# WHY THE SAME FABRICATED LITERAL AS AREA AY
#
# `zz-aq2-absent-7241` is the literal AY bought under all three subtrees, so re-using it is
# what makes this a REPRODUCTION rather than a new measurement — a different literal would
# leave "the name changed" as an alternative explanation for any cell that moved.  Its
# standing as absent is MEASURED on every host by cell 1's GET answering the published 42 B
# no-route body.  `zz-az2-absent-9917` is a second, new literal, used only at depth 2.
#
# ---------------------------------------------------------------------------------------
# METHOD DISCIPLINE
#   Empty-body OPTIONS + GET only (`--request OPTIONS`, never `-X OPTIONS` with a body).
#   No POST, no token, no cookie, no Authorization, no x-api-key, no X-System-ID, no
#   wordlist, no DNS, no port scan, no dev/stage host.
#   sleep 2.5 INSIDE the per-host flock on $REPO/.loop/host-<host>.lock.
#   Kernel body mtime captured per request into the ledger, so the second spacing clock is
#   measured per request rather than assumed.
#
# Usage: probe.sh            # all three hosts, control first on each
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/az-scratch"
mkdir -p "$SCRATCH"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=24

DIGEST_ABSENT=f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16

HOSTS=(clcloud.minimed.com clcloud.minimed.eu clcloud-trials.minimed.com)
FAB=zz-aq2-absent-7241
FAB2=zz-az2-absent-9917

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

log "=== START area AZ  plan=23 harnessed cells  cap=$CAP  hosts=${HOSTS[*]}"

for H in "${HOSTS[@]}"; do
  HOST="$H"
  slug=$(printf '%s' "$H" | tr '.' '-')
  echo "-------- $HOST (control first) --------"
  log "HOST $HOST begin"

  req_once "g-$slug-absent-v2" GET "/connect/carepartner/v2/$FAB" \
    "CONTROL-ABSENT / GATE: reproduces AY seq 2/10/18 — GET on the same fabricated literal in carepartner/v2. Must be 403, 42 B, f249b63c… (the corpus no-route digest). No question cell is issued on a host whose gate did not pass" \
    || exit 0

  gate "$(seq_of_tag "g-$slug-absent-v2")" "$HOST" 403 42 "$DIGEST_ABSENT" "control-absent $HOST" || exit 9
  echo "ORACLE RE-ESTABLISHED on $HOST — question cells follow" | tee -a "$RUNLOG"

  req_once "r-$slug-csr-fab" OPTIONS "/connect/csr/v2/$FAB" \
    "REPRODUCTION of AY seq 3/11/19 (csr/v2 fabricated). AY recorded 403 / 42 B / f249b63c… / no ACAO. Any other answer is a FLIP and is the finding" || exit 0
  req_once "r-$slug-csr-leaf" OPTIONS "/connect/csr/v2/display/message" \
    "REPRODUCTION of AY seq 4/12/20 (csr/v2 real leaf). AY recorded 200 / 0 B / ACAO * / ACAM OPTIONS,POST" || exit 0

  req_once "r-$slug-v2-fab" OPTIONS "/connect/v2/$FAB" \
    "REPRODUCTION of AY seq 5/13/21 (bare v2 fabricated). AY recorded 403 / 42 B / f249b63c… / no ACAO" || exit 0
  req_once "r-$slug-v2-leaf" OPTIONS "/connect/v2/display/message" \
    "REPRODUCTION of AY seq 6/14/22 (bare v2 real leaf). AY recorded 200 / 0 B / ACAO * / ACAM POST,OPTIONS" || exit 0

  req_once "r-$slug-v6-fab" OPTIONS "/connect/carepartner/v6/$FAB" \
    "REPRODUCTION of AY seq 7/15/23 (v6 fabricated). AY recorded 403 / 42 B / f249b63c… / no ACAO" || exit 0
  req_once "r-$slug-v6-leaf" OPTIONS "/connect/carepartner/v6/display/message" \
    "REPRODUCTION of AY seq 8/16/24 (v6 real leaf). AY recorded 200 / 0 B / ACAO * / ACAM OPTIONS" || exit 0

  # depth-2 cells: the cap buys two of the three subtrees, not three (§6)
  if [ "$HOST" = "clcloud.minimed.com" ]; then
    req_once "d2-$slug-csr" OPTIONS "/connect/csr/v2/$FAB2/deeper" \
      "DEPTH 2, csr/v2: a fabricated name one segment deeper than the leaf. 403 at the no-route digest => the depth-2 absent path is answered by the same unmatched-route path and AY's leaf-depth control was not a depth artefact. 200 + CORS => a catch-all one segment up and AY's reading is scoped to depth" || exit 0
  fi
  if [ "$HOST" = "clcloud.minimed.eu" ]; then
    req_once "d2-$slug-v6" OPTIONS "/connect/carepartner/v6/$FAB2/deeper" \
      "DEPTH 2, carepartner/v6: a fabricated name one segment deeper than the leaf. Same reading rule as the csr depth-2 cell" || exit 0
  fi

  log "HOST $HOST done"
done

echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
log "DONE rows=$(ledger_len) cap=$CAP"
