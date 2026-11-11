#!/usr/bin/env bash
# Area AK — is the 5518 B `text/html` fallback prefix-scoped on the portal hosts,
# and is it byte-identical to the documented `carelinkhp.minimed.eu` one?
# Claim: NovaLux12/carelink-api-research#183. Cap 20, >=2.5 s per host, INSIDE the flock.
#
# THE SINGLE SOURCE OF THE CAP. One assignment, here; `cap_guard` reads it, and
# FINDINGS.md's "N of a 20 cap" line must equal `wc -l results.jsonl`.
#
#   CAP=20  ==  4 hosts x (1 live control + 4 prefix cells)
#            =  4 x 5
#            =  20
#
# THE DESIGN, and why depth/prefix rather than hostname is the variable. AG found
# `200 + 5518 B` at ROOT on the two portal hosts while `/hcp/` there answered a real
# 404 and `/hcp/configuration/` answered 405. So on the portal hosts the fallback is
# NOT host-wide and the interesting axis is the PREFIX. The four cells are chosen to
# separate "depth" from "prefix":
#
#   (a) `/zz-ak-absent-4713`                       root — AG's cell, re-measured
#   (b) `/hcp/zz-ak-absent-4713`                   depth 1, under the real API prefix
#   (c) `/hcp/configuration/zz-ak-absent-4713`     depth 2, under the deployment subtree
#   (d) `/app/zz-ak-absent-4713`                   depth 1, under the SPA prefix that
#                                                  area AC measured as a catch-all on
#                                                  `carelink.minimed.eu` (196 B 404s at
#                                                  the apex there, 1833 B under `/app/`)
#
# `carelinkhp.minimed.eu` is in the matrix as the DOCUMENTED BASELINE, so byte-identity
# is measured against the known case rather than assumed. Its four cells also test the
# documented word "every": if `/hcp/` 200s there too, §7's "every path" is literally
# true on that host and the portal hosts are the narrower ones.
#
# The fabricated name is `zz-ak-absent-4713`. It is verified absent from the tree by
# FINDINGS.md's `git grep` line (0 hits at the base commit), so it is a name this
# surface has never been asked for.
#
# GET only. No POST, no OPTIONS, no token, no cookie, no auth. The one header sent is
# `X-System-ID: ProWeb` on the known-live portal control, because that is what makes it
# a 200 rather than a 412 (AB, 2026-11-10: 412 without it). No wordlist: four cells and
# one control per host, named above.
#
# Usage: probe.sh all
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/ak-scratch"
mkdir -p "$SCRATCH"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=20
PROWEB="X-System-ID: ProWeb"

HOSTS="carelink.medtronic.com carelink.medtronic.eu carelink-support.medtronic.com carelinkhp.minimed.eu"
BASE_LIVE=/hcp/configuration/public/pow.crm.settings   # portal known-live (AB: 200)
HP_LIVE=/                                              # baseline known-live (area G: 200, 5518 B)
ABS=zz-ak-absent-4713

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
        'cache-control','etag','last-modified',
        'access-control-allow-headers','access-control-allow-methods')
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
       "content_encoding": hdrs.get('content-encoding','(none)'),
       "server": hdrs.get('server','(none)'),
       "etag": hdrs.get('etag','(none)'),
       "last_modified": hdrs.get('last-modified','(none)'),
       "headers": hdrs, "t_queued": tq, "t_sent": ts, "t_done": td}
open(L, 'a').write(json.dumps(row) + "\n")
print(f"seq={seq} GET {host}{path} -> {code} ctype={hdrs.get('content-type','-')} "
      f"bytes={n} sha256={d[:16]}")
PY
  log "seq=$SEQ GET https://$host$path status=$code exit=$exitc tag=$tag role=[$role]"
}

sweep() {
  local h
  for h in $HOSTS; do
    # ---- control FIRST, per host -------------------------------------------
    if [ "$h" = "carelinkhp.minimed.eu" ]; then
      req "$h" "$HP_LIVE" \
        "CONTROL live: the baseline entry document. Area G recorded 200 text/html 5518 B sha256 0f2c5f6257a6fc6a… at this exact path. A non-200 here is a FAILURE of the pass, not an absence." \
        "ctl-$h" "" || return 0
    else
      req "$h" "$BASE_LIVE" \
        "CONTROL live: known-live config key, WITH X-System-ID: ProWeb. AB recorded 200 here on 2026-11-10 (97 B on .com and support, 96 B on .eu). Proves this host is answering and the 200s below are not a CDN error page." \
        "ctl-$h" "$PROWEB" || return 0
    fi
    # ---- four prefix cells, same four on every host ------------------------
    req "$h" "/$ABS" \
      "CELL root: fabricated name at the apex. AG recorded 200 + 5518 B here on .com and .eu; this re-measures it and measures it on support and on the documented baseline host." \
      "root-$h" "" || return 0
    req "$h" "/hcp/$ABS" \
      "CELL /hcp/ depth 1: fabricated name one level under the real API prefix. AG recorded a real 404 on .com and .eu. Discriminates 'depth' from 'prefix'." \
      "hcp-$h" "" || return 0
    req "$h" "/hcp/configuration/$ABS" \
      "CELL /hcp/configuration/ depth 2: fabricated name two levels under. AG recorded 405 + Allow: POST, OPTIONS on .com and .eu. The third verdict shape on the same page." \
      "hcpcfg-$h" "" || return 0
    req "$h" "/app/$ABS" \
      "CELL /app/ depth 1: fabricated name under the SPA prefix area AC measured as a catch-all on carelink.minimed.eu (1833 B shell there, a different family). Tests whether these hosts serve a shell at /app/ too." \
      "app-$h" "" || return 0
  done
}

case "${1:-}" in
  all) sweep ;;
  *) echo "usage: probe.sh all" >&2; exit 64 ;;
esac
echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
echo "DONE — $(ledger_len) of $CAP" >> "$RUNLOG"
