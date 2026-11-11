#!/usr/bin/env bash
# Area AS — what is BEHIND the 412 on carelinkhp.minimed.eu?
#   hcp/patients/care-partner/search  and  hcp/patients/otc-linking/allowed
# Claim: NovaLux12/carelink-api-research#210. Branch research/as-header-gate.
#
# ONE HOST ONLY: carelinkhp.minimed.eu. Three sibling lanes hold the clcloud hosts
# and the other clinic hosts; this harness cannot address them.
#
# ---------------------------------------------------------------------------
# CAP ITEMISATION — written before the first request. Cap is 12.
#
#   1  CONTROL-1  GET /hcp/configuration/public/pow.crm.settings  WITH ProWeb
#                 expected 200, 96 B  (AB/AQ record on this host)
#   1  CONTROL-2  GET /hcp/patients/zz-as-absent-5531             NO header
#                 expected 404, 0 B, no Content-Type
#   2  care-partner/search  {WITH ProWeb, WITHOUT ProWeb}
#   2  otc-linking/allowed  {WITH ProWeb, WITHOUT ProWeb}
#   1  depth-2 fabricated child  GET /hcp/patients/zz-as-absent-5531/zz-as-depth2-5531
#                 NO header — re-confirms the 404 shape one level deeper
#   2  bare OPTIONS on each literal, NO header — does the gate fire on a
#                 method the route may not register at all?
#   1  SPENT POST-HOC from the unspent reserve: OPTIONS on the CERTAINLY-ABSENT
#                 child, NO header — because the two question cells answered
#                 OPTIONS 200 + `Allow: HEAD, GET, OPTIONS` while their GETs were
#                 gated, so it had to be shown whether that OPTIONS answer is a
#                 property of the route or a subtree constant (area AG's exact
#                 failure shape, one header over). Declared unspent before
#                 request 1; spent once the result made it load-bearing.
#   1  UNSPENT
#  --
#  10 issued of a 12 cap. NO RECORDED CAP REVISION: 9 were fixed before request 1
#  and the 1 extra came out of the two cells the itemisation already reserved.
#
# GET only + empty-body OPTIONS (AGENTS.md §8, and AB's precedent). No POST, no
# token, no cookie, no auth, no wordlist, no fabricated patient id.
# `X-System-ID: ProWeb` is a PUBLISHED, non-secret header value (areas AB/AG/AK/AQ)
# — not a credential, so it is printed in full and not redacted.
#
# sleep 2.5 s INSIDE the per-host flock, structure copied from
# findings-log/2026-11-10-area-ab-hcp-direct/probe.sh.
#
# Usage: probe.sh all
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/as-scratch"     # gitignored: header/body scratch never enters findings-log/
mkdir -p "$SCRATCH"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=12
PROWEB="X-System-ID: ProWeb"
HOST=carelinkhp.minimed.eu

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

# req <method> <path> <role> <tag> [header]
req() {
  local method="$1" path="$2" role="$3" tag="$4" hdr="${5:-}"
  cap_guard || return 1
  SEQ=$((SEQ+1))
  local out="$SCRATCH/$tag" tq ts td code exitc
  tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  local -a cargs=(-s --compressed --max-time 120 -A "$UA" -D "$out.h" -o "$out.b" -w '%{http_code}')
  [ "$method" = OPTIONS ] && cargs+=(--request OPTIONS)
  [ -n "$hdr" ] && cargs+=(-H "$hdr")
  touch "$REPO/.loop/host-$HOST.lock" 2>/dev/null || true
  exec 9>"$REPO/.loop/host-$HOST.lock"
  flock 9
  sleep "$DELAY"                       # the sleep is INSIDE the per-host lock
  ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  code=$(curl "${cargs[@]}" "https://$HOST$path" 2>>"$RUNLOG")
  exitc=$?
  flock -u 9
  exec 9>&-
  td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  python3 - "$LEDGER" "$out.h" "$out.b" "$SEQ" "$method" "$HOST" "$tag" "$path" "$role" "${hdr:-(none)}" "$code" "$exitc" "$tq" "$ts" "$td" <<'PY'
import json, sys, os, hashlib
(L, hp, bp, seq, method, host, tag, path, role, sent, code, exitc,
 tq, ts, td) = sys.argv[1:16]
KEEP = ('content-type','content-length','content-encoding','allow','server','vary',
        'cache-control','access-control-allow-origin','access-control-allow-methods',
        'access-control-allow-headers','access-control-expose-headers')
hdrs = {}
if os.path.exists(hp):
    for line in open(hp, 'rb').read().decode('latin-1').splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            if k.strip().lower() in KEEP:
                hdrs[k.strip().lower()] = v.strip()
n = os.path.getsize(bp) if os.path.exists(bp) else 0
d = hashlib.sha256(open(bp,'rb').read()).hexdigest() if n else ''
mt = int(os.stat(bp).st_mtime_ns) if os.path.exists(bp) else 0
row = {"seq": int(seq), "host": host, "tag": tag, "method": method, "path": path,
       "role": role, "sent_headers": sent, "http_status": code, "curl_exit": int(exitc),
       "body_bytes": n, "body_sha256": d, "body_mtime_ns": mt,
       "content_type": hdrs.get('content-type','(none)'),
       "allow": hdrs.get('allow','(none)'),
       "acam": hdrs.get('access-control-allow-methods','(none)'),
       "acao": hdrs.get('access-control-allow-origin','(none)'),
       "content_encoding": hdrs.get('content-encoding','(none)'),
       "server": hdrs.get('server','(none)'),
       "headers": hdrs, "t_queued": tq, "t_sent": ts, "t_done": td}
open(L, 'a').write(json.dumps(row) + "\n")
print(f"seq={seq} {method} {path} hdr={'Y' if sent!='(none)' else 'N'} -> {code} "
      f"ctype={hdrs.get('content-type','-')} bytes={n} allow={hdrs.get('allow','-')} "
      f"sha256={d[:16]}")
PY
  log "seq=$SEQ $method https://$HOST$path status=$code exit=$exitc tag=$tag hdr=${hdr:-(none)}"
}

all() {
  # ---- CONTROLS FIRST (2). If either disagrees, STOP: no question cell is bought.
  req GET /hcp/configuration/public/pow.crm.settings \
    "CONTROL-1 positive: known-live key WITH X-System-ID: ProWeb. Recorded 200, 96 B on this host (area AB; AQ re-asserted it 2026-11-11). Proves the header is accepted here and this host is serving what the repo pins" \
    as-c1-pow-crm "$PROWEB" || return 0
  req GET /hcp/patients/zz-as-absent-5531 \
    "CONTROL-2 certainly-absent child under /hcp/patients/, NO header. Recorded shape: 404, 0 bytes, no Content-Type (area AQ, 4 of 4 hosts). Establishes that a header-less GET on this subtree CAN return 404, which is what makes a 412 on the same shape discriminating" \
    as-c2-absent || return 0

  # ---- THE PAIR (4): each literal WITH the header, then WITHOUT, in the same run.
  req GET /hcp/patients/care-partner/search \
    "QUESTION A (header PRESENT): the 412 in area AQ was header-less. With X-System-ID: ProWeb the edge's rejection condition is satisfied, so whatever answers here (200/401/405/404) is behind the gate rather than in front of it" \
    as-q1-cps-with "$PROWEB" || return 0
  req GET /hcp/patients/care-partner/search \
    "RE-ASSERT A (header ABSENT): same literal, same run, header removed. Must reproduce 412 for the flip to be attributable to the header rather than to the host shifting under the run" \
    as-q2-cps-without || return 0
  req GET /hcp/patients/otc-linking/allowed \
    "QUESTION B (header PRESENT): as QUESTION A, second literal" \
    as-q3-otc-with "$PROWEB" || return 0
  req GET /hcp/patients/otc-linking/allowed \
    "RE-ASSERT B (header ABSENT): as RE-ASSERT A, second literal" \
    as-q4-otc-without || return 0

  # ---- DEPTH-2 ABSENCE (1): the 404 shape one level deeper, no header.
  req GET /hcp/patients/zz-as-absent-5531/zz-as-depth2-5531 \
    "ABSENCE at depth 2, NO header: the question literals sit one and two segments below /hcp/patients/. This cell shows whether a fabricated child at THEIR depth also 404s, so a 404 on a question literal is not an artefact of depth" \
    as-b1-absent-depth2 || return 0

  # ---- BARE OPTIONS (2): does the gate fire on a method the route may not register?
  req OPTIONS /hcp/patients/care-partner/search \
    "OPTIONS (empty body, no -d, no header) on care-partner/search: if the 412 returns, the gate precedes method resolution; if 405/403/200 returns, the edge resolved a method first. AGENTS.md §8 permits an empty-body preflight; this is not a POST" \
    as-o1-cps-options || return 0
  req OPTIONS /hcp/patients/otc-linking/allowed \
    "OPTIONS (empty body, no -d, no header) on otc-linking/allowed: as as-o1" \
    as-o2-otc-options || return 0
}

# The reserve cell, runnable alone so the completed 9-cell batch is never re-spent.
reserve() {
  req OPTIONS /hcp/patients/zz-as-absent-5531 \
    "OPTIONS CONTROL (empty body, no header) on the CERTAINLY-ABSENT child. as-o1/as-o2 answered OPTIONS 200 + Allow: HEAD, GET, OPTIONS while the same paths' header-less GETs answered 412. If this absent path answers the same 200, the 18 B body and the 200 are a subtree constant carrying no route information, and only the GET column is evidence (area AG's failure shape, one header over)" \
    as-o3-absent-options || return 0
}

case "${1:-}" in
  all) all ;;
  reserve) reserve ;;
  *) echo "usage: probe.sh all|reserve" >&2; exit 64 ;;
esac
echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
