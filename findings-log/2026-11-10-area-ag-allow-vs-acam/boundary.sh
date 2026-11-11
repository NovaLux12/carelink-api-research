#!/usr/bin/env bash
# Area AG — batch 2: WHERE does the 405 come from?
# Claim: NovaLux12/carelink-api-research#179.
#
# THE RECORDED CAP REVISION (one, per the lane rule):
#   cap 24 -> 28. Reason: the certainly-absent control `zz-ag-absent-8713` returned
#   **405 + `Allow: POST, OPTIONS`**, byte-identical to the real POST-only route
#   `/hcp/configuration/application`, so it is not a control and the primary cell
#   cannot be interpreted without knowing how far the 405 reaches. Four cells
#   establish the boundary: two paths on each of two portal hosts.
#
# If `/zz-ag-absent-8713` (root) answers 404 and `/hcp/configuration/zz-ag-absent-8713`
# answers 405, the 405 is emitted by a handler mounted on the `/hcp/configuration/`
# subtree — which means `Allow` there is a **subtree constant**, not a register of a
# route's methods, and AG's INFERRED assumption is refuted.
#
# GET only. No POST, no token, no cookie, no auth, no wordlist.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/ag-scratch"
mkdir -p "$SCRATCH"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=28

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$*" >> "$RUNLOG"; }
ledger_len() { awk 'NF' "$LEDGER" 2>/dev/null | wc -l | tr -d ' '; }

cap_guard() {
  local n; n=$(ledger_len)
  if [ "$n" -ge "$CAP" ]; then
    log "CAP STOP at $n of $CAP"; echo "CAP STOP: $n of $CAP" >&2; return 1
  fi
  return 0
}

req() {
  local host="$1" method="$2" path="$3" role="$4" tag="$5" extra="${6:-}"
  cap_guard || return 1
  local key; key=$(printf '%s' "$host" | tr '.' '_')
  local lock="$REPO/.loop/host-$key.lock"
  (
    flock -w 120 9 || { log "LOCK TIMEOUT $host"; exit 1; }
    sleep "$DELAY"
    local out="$SCRATCH/$(printf '%s' "$tag" | tr '/:' '__').hdr"
    local body="$SCRATCH/$(printf '%s' "$tag" | tr '/:' '__').body"
    local args=(-sS --http2 -X "$method" -D "$out" -o "$body" --max-time 25 -A "$UA" -H "Accept: */*")
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
    log "$method $host$path -> ${code:-FAIL} allow=${allow:-none} acam=${acam:-none} ${bytes}B"
  ) 9>"$lock"
}

echo "=== AG batch 2: the 405 boundary (cap $CAP) ==="
log "=== AG batch 2 start, cap $CAP (revision 24->28) ==="

for h in carelink.medtronic.com carelink.medtronic.eu; do
  echo "--- $h ---"
  req "$h" GET /zz-ag-absent-8713                    "boundary: absent at ROOT"          "b2-$h-root-absent"
  req "$h" GET /hcp/zz-ag-absent-8713                "boundary: absent under /hcp/"      "b2-$h-hcp-absent"
done

echo
echo "ledger rows: $(ledger_len) of $CAP"
log "=== AG batch 2 end: $(ledger_len) of $CAP ==="
