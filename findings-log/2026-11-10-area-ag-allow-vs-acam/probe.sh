#!/usr/bin/env bash
# Area AG — does `Allow` agree with `access-control-allow-methods` on the same route?
# Claim: NovaLux12/carelink-api-research#179. Cap 24, >=2.5 s per host, INSIDE the flock.
#
# THE SINGLE SOURCE OF THE CAP. One assignment, here; `cap_guard` reads it, and
# FINDINGS.md's "N of a 24 cap" line must equal `wc -l results.jsonl`.
#
#   CAP=24  ==  3 portal hosts  x 4 cells = 12
#            +  3 cumulus hosts x 4 cells = 12
#                                          --
#                                          24
#
# THE FOUR CELLS, and why each one is here. The question is whether the two headers
# are ever emitted on ONE response. Two crossings would break the separation seen in
# the committed corpus (portal: 27 Allow / 0 ACAM; cumulus: 0 Allow / 56 ACAM):
#
#   (1) control-live    — a route known to answer. Proves the host is answering at all,
#                         and that this pass is not reading a CDN error page as a result.
#   (2) control-absent  — a certainly-absent path. Proves the status code discriminates.
#   (3) the primary     — portal: GET a 405 route (does ACAM ever ride along?).
#                         cumulus: GET a POST-only route (does a 405+Allow ever appear?).
#   (4) the crossing    — portal: OPTIONS the same 405 route WITH an `Origin` header.
#                         If Apache is CORS-configured for that route it would emit
#                         ACAM here; that is the one plausible way ACAM reaches a portal
#                         response. cumulus: OPTIONS the POST-only route WITH `Origin`,
#                         the mirror test for Allow.
#
# GET only, plus empty-body OPTIONS. No POST, no token, no cookie, no auth, no wordlist.
# OPTIONS is not a POST: it carries no body and no credentials, and areas Z and AB both
# sent it under AGENTS.md §8.
#
# Usage: probe.sh all
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/ag-scratch"
mkdir -p "$SCRATCH"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=24
ORIGIN="https://example.invalid"

PORTAL="carelink.medtronic.com carelink.medtronic.eu carelink-support.medtronic.com"
CUMULUS="clcloud.minimed.com clcloud-trials.minimed.com clcloud.minimed.eu"

# Portal: the three direct routes recorded POST-only, answering GET 405 + Allow.
P_405=/hcp/configuration/application
P_LIVE=/hcp/configuration/access/config
P_ABSENT=/hcp/configuration/zz-ag-absent-8713

# Cumulus: the two routes recorded live and POST-only (areas C/N), carrying ACAM.
C_POSTONLY=/connect/csr/v2/display/message
C_LIVE=/connect/carepartner/v13/display/message
C_ABSENT=/connect/csr/v2/zz-ag-absent-8713

[ -f "$LEDGER" ] || : > "$LEDGER"
[ -f "$RUNLOG" ] || : > "$RUNLOG"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$*" >> "$RUNLOG"; }
ledger_len() { awk 'NF' "$LEDGER" 2>/dev/null | wc -l | tr -d ' '; }

cap_guard() {
  local n; n=$(ledger_len)
  if [ "$n" -ge "$CAP" ]; then
    log "CAP STOP at $n of $CAP"; echo "CAP STOP: $n of $CAP" >&2; return 1
  fi
  return 0
}

# req <host> <method> <path> <role> <tag> [extra-header]
req() {
  local host="$1" method="$2" path="$3" role="$4" tag="$5" extra="${6:-}"
  cap_guard || return 1

  local key; key=$(printf '%s' "$host" | tr '.' '_')
  local lock="$REPO/.loop/host-$key.lock"

  # The sleep is INSIDE the flock: spacing must hold across concurrent workers, and a
  # sleep taken outside the lock is a sleep that two workers can serve simultaneously.
  (
    flock -w 120 9 || { log "LOCK TIMEOUT $host"; exit 1; }
    sleep "$DELAY"
    local out="$SCRATCH/$(printf '%s' "$tag" | tr '/:' '__').hdr"
    local body="$SCRATCH/$(printf '%s' "$tag" | tr '/:' '__').body"
    local args=(-sS --http2 -X "$method" -D "$out" -o "$body"
                --max-time 25 -A "$UA" -H "Accept: */*")
    [ -n "$extra" ] && args+=(-H "$extra")

    local t_sent t_done code rc
    t_sent=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
    curl "${args[@]}" "https://$host$path" 2>>"$RUNLOG"; rc=$?
    t_done=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

    code=$(awk 'NR==1{print $2}' "$out" 2>/dev/null)
    local allow acam acao acah ctype bytes sha
    allow=$(grep -i '^allow:' "$out" 2>/dev/null | head -1 | sed 's/^[Aa]llow:[[:space:]]*//' | tr -d '\r')
    acam=$(grep -i '^access-control-allow-methods:' "$out" 2>/dev/null | head -1 | sed 's/^[Aa]ccess-[Cc]ontrol-[Aa]llow-[Mm]ethods:[[:space:]]*//' | tr -d '\r')
    acao=$(grep -i '^access-control-allow-origin:' "$out" 2>/dev/null | head -1 | sed 's/^[Aa]ccess-[Cc]ontrol-[Aa]llow-[Oo]rigin:[[:space:]]*//' | tr -d '\r')
    acah=$(grep -i '^access-control-allow-headers:' "$out" 2>/dev/null | head -1 | sed 's/^[Aa]ccess-[Cc]ontrol-[Aa]llow-[Hh]eaders:[[:space:]]*//' | tr -d '\r')
    ctype=$(grep -i '^content-type:' "$out" 2>/dev/null | head -1 | sed 's/^[Cc]ontent-[Tt]ype:[[:space:]]*//' | tr -d '\r')
    bytes=$(wc -c < "$body" 2>/dev/null | tr -d ' ')
    sha=$(sha256sum "$body" 2>/dev/null | cut -d' ' -f1)

    python3 - "$LEDGER" "$host" "$method" "$path" "$role" "$tag" "$code" "$rc" \
      "$bytes" "$sha" "$ctype" "$allow" "$acam" "$acao" "$acah" "$t_sent" "$t_done" "$out" <<'PY'
import json,sys,os
(L,host,method,path,role,tag,code,rc,bytes_,sha,ctype,allow,acam,acao,acah,ts,td,hdr)=sys.argv[1:]
def nz(v): return v if v else "(none)"
rec={"seq":sum(1 for l in open(L) if l.strip())+1,"host":host,"method":method,"path":path,
     "role":role,"tag":tag,"http_status":code or "(none)","curl_exit":int(rc),
     "body_bytes":int(bytes_ or 0),"body_sha256":sha,
     "content_type":nz(ctype),"allow":nz(allow),"acam":nz(acam),"acao":nz(acao),
     "acah":nz(acah),"sent_origin":nz(os.environ.get("SENT_ORIGIN","")),
     "t_sent":ts,"t_done":td,"header_file":os.path.basename(hdr)}
with open(L,"a") as f: f.write(json.dumps(rec)+"\n")
PY
    log "$method $host$path -> ${code:-FAIL} allow=${allow:-none} acam=${acam:-none} acao=${acao:-none} ${bytes}B"
  ) 9>"$lock"
}

echo "=== area AG sweep, cap $CAP ==="
log "=== AG sweep start, cap $CAP ==="

for h in $PORTAL; do
  echo "--- $h (portal) ---"
  req "$h" GET "$P_LIVE"   "control-live: recorded 401 route"        "p-$h-control-live"
  req "$h" GET "$P_ABSENT" "control-absent: certainly-absent path"    "p-$h-control-absent"
  req "$h" GET "$P_405"    "primary: GET a 405 route — does ACAM ride along?" "p-$h-get405"
  SENT_ORIGIN="$ORIGIN" req "$h" OPTIONS "$P_405" "crossing: OPTIONS 405-route WITH Origin — does Apache add ACAM?" "p-$h-options-origin" "Origin: $ORIGIN"
done

for h in $CUMULUS; do
  echo "--- $h (cumulus) ---"
  req "$h" GET "$C_LIVE"   "control-live: recorded 401 route"        "c-$h-control-live"
  req "$h" GET "$C_ABSENT" "control-absent: certainly-absent path"    "c-$h-control-absent"
  req "$h" GET "$C_POSTONLY" "primary: GET a POST-only route — does a 405+Allow appear?" "c-$h-get-postonly"
  SENT_ORIGIN="$ORIGIN" req "$h" OPTIONS "$C_POSTONLY" "crossing: OPTIONS POST-only route WITH Origin — does Allow appear?" "c-$h-options-origin" "Origin: $ORIGIN"
done

echo
echo "ledger rows: $(ledger_len) of $CAP"
log "=== AG sweep end: $(ledger_len) of $CAP ==="
