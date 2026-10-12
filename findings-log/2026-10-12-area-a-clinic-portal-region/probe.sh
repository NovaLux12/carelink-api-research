#!/usr/bin/env bash
# Area A — carelinkhp bundle identity across the region.
# Claim: NovaLux12/carelink-api-research#21. Cap 20 HTTP GETs, 2.5 s per host.
#
# GET only. No POST, no -X, no -d, no token, no auth, no port scan, no DNS brute force.
# The sleep goes INSIDE the per-host flock (BRIEF §5) — three other pool workers are
# probing the same machine; outside the lock they would queue and then fire together.
#
# Why the certainly-absent path is the SAME string on every host: the fallback body is
# the question, so the three fallback bodies have to be byte-comparable to each other
# and to each host's own root. A per-host nonce would make three incomparable rows.
set -uo pipefail

# Derived, never hardcoded: HERE is <main-clone>/.loop/worktrees/<w>/findings-log/<dir>,
# so five levels up is the main clone, and the per-host locks must live THERE rather
# than in this worktree -- four pool workers share one .loop (BRIEF 5).
REPO="$(cd "$HERE/../../../../.." && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
HDR="$HERE/headers"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/areaA-XXXXXX")"
mkdir -p "$HDR" "$SCRATCH"
trap 'rm -rf "$SCRATCH"' EXIT

UA="carelink-bridge-research/1.0"
ABSENT="/a-control-this-path-cannot-exist-2026-10-12"
ASSET="/main.fb5f8cb7eb60c4d5.js"   # recorded at AUTH-TENANT-FINDINGS.md:248
CFGKEY="/hcp/configuration/public/pow.crm.settings"  # pinned, 05-public-config.check.sh:98
SEQ=0

: > "$RUNLOG"
: > "$LEDGER"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$RUNLOG"; }

req() { # req <host> <path> <role> <tag> [extra-header]
  local host="$1" path="$2" role="$3" tag="$4" hdr="${5:-}"
  SEQ=$((SEQ+1))
  local hseq out
  out="$SCRATCH/$tag"
  # count the per-host request number before the sleep so host_seq is right
  # grep -c prints 0 AND exits 1, so `|| echo 0` would double it into "0\n0"
  hseq=$(grep -c "\"host\": \"$host\"" "$LEDGER" 2>/dev/null | head -1)
  case "$hseq" in ''|*[!0-9]*) hseq=0 ;; esac
  hseq=$((hseq+1))
  touch "$REPO/.loop/host-$host.lock" 2>/dev/null || true
  local code
  code=$(flock "$REPO/.loop/host-$host.lock" -c "
    sleep 2.5
    if [ -n '$hdr' ]; then
      curl -s --compressed --max-time 90 -A '$UA' -H '$hdr' -D '$out.h' -o '$out.b' -w '%{http_code}' 'https://$host$path'
    else
      curl -s --compressed --max-time 90 -A '$UA' -D '$out.h' -o '$out.b' -w '%{http_code}' 'https://$host$path'
    fi
  " 2>>"$RUNLOG")
  local exit=$?
  cp "$out.h" "$HDR/$tag.h" 2>/dev/null || true
  # keep small bodies as evidence; the 3.4 MB asset body is deliberately not committed
  if [ -f "$out.b" ]; then
    local sz; sz=$(stat -c%s "$out.b")
    if [ "$sz" -le 100000 ]; then cp "$out.b" "$HDR/$tag.b"; fi
  fi
  emit "$SEQ" "$hseq" "$host" "$tag" "GET" "$path" "$role" "${hdr:-(none)}" "$code" "$exit" "$out"
}

emit() { # emit seq hseq host tag method path role senthdr code exit out
  local seq="$1" hseq="$2" host="$3" tag="$4" method="$5" path="$6" role="$7" sent="$8" code="$9" exit="${10}" out="${11}"
  local hf="$out.h" bf="$out.b"
  local ctype="(none)" clen="(none)" cenc="(none)" vary="(none)" xpid="(none)" server="(none)" via="(none)"
  local nbytes=0 digest=""
  [ -f "$hf" ] && { grep -i '^content-type:' "$hf" | tail -1 | sed 's/^[Cc]ontent-[Tt]ype:[[:space:]]*//' | tr -d '\r' | { read -r v || true; [ -n "$v" ] && ctype="$v"; }; }
  [ -f "$hf" ] && { grep -i '^content-length:' "$hf" | tail -1 | sed 's/^[Cc]ontent-[Ll]ength:[[:space:]]*//' | tr -d '\r' | { read -r v || true; [ -n "$v" ] && clen="$v"; }; }
  [ -f "$hf" ] && { grep -i '^content-encoding:' "$hf" | tail -1 | sed 's/^[Cc]ontent-[Ee]ncoding:[[:space:]]*//' | tr -d '\r' | { read -r v || true; [ -n "$v" ] && cenc="$v"; }; }
  [ -f "$hf" ] && { grep -i '^vary:' "$hf" | tail -1 | sed 's/^[Vv]ary:[[:space:]]*//' | tr -d '\r' | { read -r v || true; [ -n "$v" ] && vary="$v"; }; }
  [ -f "$hf" ] && { grep -i '^x-amz-cf-pop:' "$hf" | tail -1 | sed 's/^[^:]*:[[:space:]]*//' | tr -d '\r' | { read -r v || true; [ -n "$v" ] && xpid="$v"; }; }
  [ -f "$hf" ] && { grep -i '^server:' "$hf" | tail -1 | sed 's/^[Ss]erver:[[:space:]]*//' | tr -d '\r' | { read -r v || true; [ -n "$v" ] && server="$v"; }; }
  [ -f "$hf" ] && { grep -i '^via:' "$hf" | tail -1 | sed 's/^[Vv]ia:[[:space:]]*//' | tr -d '\r' | { read -r v || true; [ -n "$v" ] && via="$v"; }; }
  if [ -f "$bf" ]; then
    nbytes=$(stat -c%s "$bf")
    digest=$(sha256sum "$bf" | cut -c1-16)
  fi
  local fullhdr=""
  [ -f "$hf" ] && fullhdr=$(grep -v '^$' "$hf" | tr -d '\r' | paste -sd'|' -)
  python3 - "$LEDGER" "$seq" "$hseq" "$host" "$tag" "$method" "$path" "$role" "$sent" "$code" "$exit" "$ctype" "$clen" "$cenc" "$vary" "$xpid" "$server" "$via" "$nbytes" "$digest" "$fullhdr" <<'PY'
import json,sys
(L,seq,hseq,host,tag,method,path,role,sent,code,exit_,ctype,clen,cenc,vary,xpid,server,via,nbytes,digest,fullhdr)=sys.argv[1:22]
row={"seq":int(seq),"host_seq":int(hseq),"host":host,"host_tag":tag,"method":method,"path":path,
 "role":role,"sent_headers":sent,"http_status":code,"curl_exit":int(exit_),"content_type":ctype,
 "content_length_hdr":clen,"content_encoding":cenc,"vary":vary,"x_amz_cf_pop":xpid,"server":server,"via":via,
 "body_bytes":int(nbytes),"body_sha256_prefix16":digest,"ctype_full":fullhdr}
open(L,"a").write(json.dumps(row)+"\n")
PY
  log "seq=$seq host_seq=$hseq host=$host tag=$tag role=$role status=$code ctype=$ctype bytes=$nbytes sha256_16=$digest path=$path"
}

# ---- DNS is not HTTP traffic; recorded in run.log and dns.jsonl, counted separately ----
: > "$HERE/dns.jsonl"
for h in carelinkhp.minimed.eu carelinkhp-prod.minimed.eu carelink.medtronic.com \
         carelink-support.medtronic.com carelinkhp.minimed.com carelinkhp-prod.minimed.com \
         carelinkhp-trials.minimed.com carelinkhp-test.minimed.eu; do
  st=$(dig +noall +comments "$h" A 2>/dev/null | grep -o 'status: [A-Z]*' | head -1 | awk '{print $2}')
  ans=$(dig +short "$h" A 2>/dev/null | grep -c '^[0-9]')
  [ -z "$st" ] && st="UNAVAILABLE"
  # carelinkhp-test.minimed.eu is a test host: DNS only, never a request (docs/09 §1)
  python3 -c "import json,sys;print(json.dumps({'host':sys.argv[1],'resolver_status':sys.argv[2],'a_records':int(sys.argv[3]),'probed':'no - test host, recorded only' if 'test' in sys.argv[1] else 'see results.jsonl'}))" "$h" "$st" "$ans" >> "$HERE/dns.jsonl"
  log "DNS host=$h status=$st a_records=$ans"
done

# ================= CONTROLS FIRST, PER HOST (BRIEF §4) =================
# control 1: certainly-absent path -> is the SPA-fallback oracle live on THIS host?
# control 2: the published, already-pinned public config key -> is this host a live portal
#            rather than a parked page? 200 here is what a parked page cannot fake.
# then the candidates: the entry document, then the content-addressed main bundle asset.
for host in carelinkhp.minimed.eu carelink.medtronic.com carelink-support.medtronic.com; do
  t=$(echo "$host" | tr '.' '-')
  req "$host" "$ABSENT"      "CONTROL-certainly-absent path - proves the SPA fallback oracle on this host; 5518 B = not a portal root" "$t-ctl-absent"
  req "$host" "$CFGKEY"      "CONTROL-known-live published config key (pow.crm.settings, pinned 05-public-config.check.sh:98) - proves a live portal, not a parked page" "$t-ctl-cfg" "X-System-ID: ProWeb"
  req "$host" "/"            "CANDIDATE-portal entry document (bundle root)" "$t-root"
  req "$host" "$ASSET"       "CANDIDATE-main.fb5f8cb7eb60c4d5.js - the content-addressed bundle asset, the digest that actually identifies the build" "$t-asset"
done

log "TOTAL_HTTP_REQUESTS=$SEQ CAP=20"
echo "TOTAL_HTTP_REQUESTS=$SEQ CAP=20"