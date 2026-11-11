#!/usr/bin/env bash
# Area AR — is the `/hcp/configuration/` absent-path 405 a property of `configuration`,
# of a handler class, or of something the two already-measured subtrees share?
# Claim: NovaLux12/carelink-api-research#212. Cap 18, >2.5 s per host, INSIDE the flock.
#
# THE SINGLE SOURCE OF THE CAP. One assignment, here; `cap_guard` reads it, and
# FINDINGS.md's "N of an 18 cap" line must equal `wc -l results.jsonl`.
#
#   CAP=18  ==  3 controls  x 2 hosts                    =  6
#            +  3 derived subtrees x 2 depths x 2 hosts  = 12
#                                                         --
#                                                         18
#
# The three subtrees are NOT typed here — they are read from `candidates.txt`, which
# `derive.py` wrote from the shipped clinic build before this sweep ran. No wordlist,
# no invented name: AGENTS.md §8.
#
# The derivation itself cost ZERO requests: the clinic bundle was already in this run's
# asset cache (`.loop/aq-assets/main.js`, fetched by area AQ) and `derive.py` verifies
# its sha256 against the value area AB pinned before extracting anything.
#
# GET only. No POST, no OPTIONS, no token, no cookie, no auth beyond the one
# X-System-ID control header, no wordlist, no patient id. `--compressed` on every
# request (`carelink.minimed.eu` gzips unconditionally; §7 records it).
#
# Usage: probe.sh controls   # the 6 control cells only
#        probe.sh sweep      # controls then candidates (all 18)
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/ar-scratch"
mkdir -p "$SCRATCH"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=18
PROWEB="X-System-ID: ProWeb"
ABSENT=zz-ar-absent-6293
HOSTS="carelink.medtronic.eu carelink-support.medtronic.com"
DEPTHS="1 2"

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

# req <host> <path> <role> <tag> [header]
req() {
  local host="$1" path="$2" role="$3" tag="$4" hdr="${5:-}"
  cap_guard || return 1
  SEQ=$((SEQ+1))
  local out="$SCRATCH/$tag" tq ts td code exitc
  tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  local -a cargs=(-s --compressed --max-time 120 -A "$UA" -D "$out.h" -o "$out.b" -w '%{http_code}')
  [ -n "$hdr" ] && cargs+=(-H "$hdr")
  touch "$REPO/.loop/host-$host.lock" 2>/dev/null || true
  exec 9>"$REPO/.loop/host-$host.lock"
  flock 9
  sleep "$DELAY"                       # the sleep is INSIDE the per-host lock
  ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  code=$(curl "${cargs[@]}" "https://$host$path" 2>>"$RUNLOG")
  exitc=$?
  flock -u 9
  exec 9>&-
  td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  python3 - "$LEDGER" "$out.h" "$out.b" "$SEQ" "$host" "$tag" "$path" "$role" "${hdr:-(none)}" "$code" "$exitc" "$tq" "$ts" "$td" <<'PY'
import json, sys, os, hashlib
(L, hp, bp, seq, host, tag, path, role, sent, code, exitc,
 tq, ts, td) = sys.argv[1:15]
KEEP = ('content-type','content-length','content-encoding','allow','server','vary',
        'cache-control','access-control-allow-origin','access-control-allow-methods',
        'access-control-allow-headers','access-control-expose-headers','x-system-id')
hdrs = {}
if os.path.exists(hp):
    for line in open(hp, 'rb').read().decode('latin-1').splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            if k.strip().lower() in KEEP:
                hdrs[k.strip().lower()] = v.strip()
n = os.path.getsize(bp) if os.path.exists(bp) else 0
d = hashlib.sha256(open(bp,'rb').read()).hexdigest() if n else ''
row = {"seq": int(seq), "host": host, "tag": tag, "method": "GET", "path": path,
       "role": role, "sent_headers": sent, "http_status": code, "curl_exit": int(exitc),
       "body_bytes": n, "body_sha256": d,
       "content_type": hdrs.get('content-type','(none)'),
       "allow": hdrs.get('allow','(none)'),
       "acam": hdrs.get('access-control-allow-methods','(none)'),
       "acao": hdrs.get('access-control-allow-origin','(none)'),
       "content_encoding": hdrs.get('content-encoding','(none)'),
       "server": hdrs.get('server','(none)'),
       "headers": hdrs, "t_queued": tq, "t_sent": ts, "t_done": td}
open(L, 'a').write(json.dumps(row) + "\n")
print(f"seq={seq} GET {host}{path} -> {code} ctype={hdrs.get('content-type','-')} "
      f"bytes={n} allow={hdrs.get('allow','-')} sha256={d[:16]}")
PY
  log "seq=$SEQ GET https://$host$path status=$code exit=$exitc tag=$tag role=[$role]"
}

sweep() {
  local h seg d
  for h in $HOSTS; do
    controls_host_one "$h" || return 0
    while read -r seg; do
      [ -n "$seg" ] || continue
      for d in $DEPTHS; do
        if [ "$d" = 1 ]; then p="/hcp/$seg/$ABSENT"; else p="/hcp/$seg/$ABSENT/zz"; fi
        req "$h" "$p" \
          "CANDIDATE subtree '$seg' (derived: derive.py -> candidates.txt, $([ -f "$HERE/candidates.txt" ] && grep -c . "$HERE/candidates.txt") survivors ranked by distinct literal count), depth $d, header-less. A 404 here = discriminating subtree (the /hcp/ shape). A 405 + Allow here = the constant follows a handler class. Depth 2 separates a handler mounted on the subtree from one that answers every child path" \
          "k-$(echo "$h"|tr . -)-$seg-d$d" || return 0
      done
    done < "$HERE/candidates.txt"
  done
}

# Controls for one host, in one place, so `sweep` cannot start a candidate before
# that host's controls have all been read.
controls_host_one() {
  local h="$1"
  req "$h" "/hcp/configuration/public/pow.crm.settings" \
    "CONTROL-1 positive: known-live key WITH X-System-ID: ProWeb (96 B on .eu, 97 B on support). Proves the host answers and the header is accepted" \
    "c1-$(echo "$h"|tr . -)-pow-crm" "$PROWEB" || return 1
  req "$h" "/hcp/configuration/$ABSENT" \
    "CONTROL-2 absent child under configuration, header-less: recorded 405 + Allow: POST, OPTIONS on 4 of 4 clinic hosts — the subtree constant whose scope AR measures" \
    "c2-$(echo "$h"|tr . -)-config-absent" || return 1
  req "$h" "/hcp/$ABSENT" \
    "CONTROL-3 absent child under /hcp/, header-less: recorded 404, 0 B, no Content-Type on 4 of 4 — proves a 404 here is a true absence" \
    "c3-$(echo "$h"|tr . -)-hcp-absent" || return 1
}

case "${1:-}" in
  controls) for h in $HOSTS; do controls_host_one "$h" || break; done ;;
  sweep)    sweep ;;
  *) echo "usage: probe.sh controls|sweep" >&2; exit 64 ;;
esac
echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
