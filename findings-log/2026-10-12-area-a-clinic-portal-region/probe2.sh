#!/usr/bin/env bash
# Area A, batch 2 — settle the .eu/.com attribution of build main.759cddab23085086.js.
#
# Why this batch exists (found in batch 1, not planned in advance):
# batch 1 measured carelink-support.medtronic.COM serving the 5518 B document whose
# sha256 begins f637c8d0 — the same prefix docs/08 attributes to carelink-support.medtronic.EU's
# main.759cddab23085086.js. One host cannot be the other. This batch reads the two .eu
# hosts so the repo's ".eu" claim is tested rather than overwritten by inference.
#
# GET only. Same lock/sleep discipline as probe.sh. Appends to the same ledger.
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
ABSENT="/a-control-this-path-cannot-exist-2026-10-12"   # same string as batch 1, on purpose
ASSET="/main.759cddab23085086.js"                        # the build docs/08 names on .eu
SEQ=$(awk -F'"seq":' 'NF>1{split($2,a,","); print a[1]}' "$LEDGER" | tail -1)
SEQ=${SEQ:-0}

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$RUNLOG"; }

req() { # req <host> <path> <role> <tag>
  local host="$1" path="$2" role="$3" tag="$4"
  SEQ=$((SEQ+1))
  local hseq out code exit=0
  out="$SCRATCH/$tag"
  hseq=$(grep -c "\"host\": \"$host\"" "$LEDGER" 2>/dev/null | head -1)
  case "$hseq" in ''|*[!0-9]*) hseq=0 ;; esac
  hseq=$((hseq+1))
  touch "$REPO/.loop/host-$host.lock" 2>/dev/null || true
  code=$(flock "$REPO/.loop/host-$host.lock" -c "
    sleep 2.5
    curl -s --compressed --max-time 90 -A '$UA' -D '$out.h' -o '$out.b' -w '%{http_code}' 'https://$host$path'
  " 2>>"$RUNLOG") || exit=$?
  cp "$out.h" "$HDR/$tag.h" 2>/dev/null || true
  if [ -f "$out.b" ]; then
    local sz; sz=$(stat -c%s "$out.b")
    [ "$sz" -le 100000 ] && cp "$out.b" "$HDR/$tag.b"
  fi
  emit "$SEQ" "$hseq" "$host" "$tag" "$path" "$role" "(none)" "$code" "$exit" "$out"
}

emit() {
  local seq="$1" hseq="$2" host="$3" tag="$4" path="$5" role="$6" sent="$7" code="$8" exit="$9" out="${10}"
  local hf="$out.h" bf="$out.b"
  local ctype="(none)" clen="(none)" cenc="(none)" vary="(none)" xpid="(none)" server="(none)" via="(none)"
  local lastmod="(none)" nbytes=0 digest="" md5="(none)"
  hdrval() { grep -i "^$1:" "$hf" 2>/dev/null | tail -1 | sed 's/^[^:]*:[[:space:]]*//' | tr -d '\r'; }
  [ -f "$hf" ] && { v=$(hdrval 'content-type');   [ -n "$v" ] && ctype="$v"; }
  [ -f "$hf" ] && { v=$(hdrval 'content-length'); [ -n "$v" ] && clen="$v"; }
  [ -f "$hf" ] && { v=$(hdrval 'content-encoding');[ -n "$v" ] && cenc="$v"; }
  [ -f "$hf" ] && { v=$(hdrval 'vary');           [ -n "$v" ] && vary="$v"; }
  [ -f "$hf" ] && { v=$(hdrval 'x-amz-cf-pop');   [ -n "$v" ] && xpid="$v"; }
  [ -f "$hf" ] && { v=$(hdrval 'server');         [ -n "$v" ] && server="$v"; }
  [ -f "$hf" ] && { v=$(hdrval 'via');            [ -n "$v" ] && via="$v"; }
  [ -f "$hf" ] && { v=$(hdrval 'last-modified');  [ -n "$v" ] && lastmod="$v"; }
  if [ -f "$bf" ]; then
    nbytes=$(stat -c%s "$bf"); digest=$(sha256sum "$bf" | cut -c1-16); md5=$(md5sum "$bf" | cut -c1-32)
  fi
  fullhdr=""; [ -f "$hf" ] && fullhdr=$(grep -v '^$' "$hf" | tr -d '\r' | paste -sd'|' -)
  python3 - "$LEDGER" "$seq" "$hseq" "$host" "$tag" "$path" "$role" "$sent" "$code" "$exit" "$ctype" "$clen" "$cenc" "$vary" "$xpid" "$server" "$via" "$lastmod" "$nbytes" "$digest" "$md5" "$fullhdr" <<'PY'
import json,sys
(L,seq,hseq,host,tag,path,role,sent,code,exit_,ctype,clen,cenc,vary,xpid,server,via,lastmod,nbytes,digest,md5,fullhdr)=sys.argv[1:23]
row={"seq":int(seq),"host_seq":int(hseq),"host":host,"host_tag":tag,"method":"GET","path":path,"role":role,
 "sent_headers":sent,"http_status":code,"curl_exit":int(exit_),"content_type":ctype,"content_length_hdr":clen,
 "content_encoding":cenc,"vary":vary,"x_amz_cf_pop":xpid,"server":server,"via":via,"last_modified":lastmod,
 "body_bytes":int(nbytes),"body_sha256_prefix16":digest,"body_md5":md5,"ctype_full":fullhdr}
open(L,"a").write(json.dumps(row)+"\n")
PY
  log "seq=$seq host_seq=$hseq host=$host tag=$tag role=$role status=$code bytes=$nbytes sha256_16=$digest md5=$md5 path=$path"
}

for host in carelink-support.medtronic.eu carelink.medtronic.eu; do
  t=$(echo "$host" | tr '.' '-')
  req "$host" "$ABSENT" "CONTROL-certainly-absent path - same string as batch 1, so the .eu fallback is byte-comparable to the .com one" "$t-ctl-absent"
  req "$host" "/"       "CANDIDATE-portal entry document on the .eu host - tests docs/08's claim that .eu serves build main.759cddab23085086.js" "$t-root"
  req "$host" "$ASSET"  "CANDIDATE-main.759cddab23085086.js - the build docs/08 names on carelink-support.medtronic.eu; a 5518 B answer here means this host does not serve that build" "$t-asset"
done

log "TOTAL_HTTP_REQUESTS_BATCH2_END=$SEQ CAP=20"
echo "SEQ_END=$SEQ CAP=20"