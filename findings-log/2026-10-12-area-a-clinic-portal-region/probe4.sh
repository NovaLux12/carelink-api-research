#!/usr/bin/env bash
# Area A, batch 4 — the last request of the cap.
#
# Batch 1 established that carelink-support.medtronic.COM's entry document names
# main.759cddab23085086.js. Naming an asset in HTML is not serving it (AGENTS.md §6.2 —
# "a hit proves the token exists, not that it means what you assumed"). This request asks
# the host for that chunk, so the "both TLDs serve build 2" claim rests on the asset's own
# digest rather than on a string inside a document. GET only.
set -uo pipefail

# Derived, never hardcoded: HERE is <main-clone>/.loop/worktrees/<w>/findings-log/<dir>,
# so five levels up is the main clone, and the per-host locks must live THERE rather
# than in this worktree -- four pool workers share one .loop (BRIEF 5).
REPO="$(cd "$HERE/../../../../.." && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
HDR="$HERE/headers"
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/areaA-XXXXXX")"
trap 'rm -rf "$SCRATCH"' EXIT

host="carelink-support.medtronic.com"
tag="carelink-support-medtronic-com-asset-759cddab"
out="$SCRATCH/$tag"
touch "$REPO/.loop/host-$host.lock" 2>/dev/null || true
code=$(flock "$REPO/.loop/host-$host.lock" -c "
  sleep 2.5
  curl -s --compressed --max-time 90 -A 'carelink-bridge-research/1.0' \
    -D '$out.h' -o '$out.b' -w '%{http_code}' 'https://$host/main.759cddab23085086.js'
") || exit=$?
cp "$out.h" "$HDR/$tag.h"

SEQ=$(awk -F'"seq":' 'NF>1{split($2,a,","); print a[1]}' "$HERE/results.jsonl" | tail -1); SEQ=${SEQ:-0}; SEQ=$((SEQ+1))
hseq=$(grep -c "\"host\": \"$host\"" "$HERE/results.jsonl" | head -1); hseq=$((hseq+1))
ctype=$(grep -i '^content-type:' "$out.h" | tail -1 | sed 's/^[^:]*:[[:space:]]*//' | tr -d '\r')
nbytes=$(stat -c%s "$out.b" 2>/dev/null || echo 0)
digest=$(sha256sum "$out.b" 2>/dev/null | cut -c1-16)
md5=$(md5sum "$out.b" 2>/dev/null | cut -c1-32)
fullhdr=$(grep -v '^$' "$out.h" | tr -d '\r' | paste -sd'|' -)

python3 - "$HERE/results.jsonl" "$SEQ" "$hseq" "$host" "$tag" "$code" "${exit:-0}" "$ctype" "$nbytes" "$digest" "$md5" "$fullhdr" <<'PY'
import json,sys
(L,seq,hseq,host,tag,code,exit_,ctype,nbytes,digest,md5,fullhdr)=sys.argv[1:13]
row={"seq":int(seq),"host_seq":int(hseq),"host":host,"host_tag":tag,"method":"GET",
 "path":"/main.759cddab23085086.js",
 "role":"CANDIDATE-main.759cddab23085086.js on carelink-support.medtronic.com - verifies the build its entry document NAMES is actually SERVED, rather than inferred from a string in HTML (AGENTS.md 6.2)",
 "sent_headers":"(none)","http_status":code,"curl_exit":int(exit_),"content_type":ctype,
 "content_length_hdr":"(not recorded)","content_encoding":"(not recorded)","vary":"(not recorded)",
 "x_amz_cf_pop":"(not recorded)","server":"(not recorded)","via":"(not recorded)","last_modified":"(not recorded)",
 "body_bytes":int(nbytes),"body_sha256_prefix16":digest,"body_md5":md5,"ctype_full":fullhdr}
open(L,"a").write(json.dumps(row)+"\n")
PY

printf '%s seq=%s host_seq=%s host=%s tag=%s status=%s ctype=%s bytes=%s sha256_16=%s md5=%s path=/main.759cddab23085086.js\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$SEQ" "$hseq" "$host" "$tag" "$code" "$ctype" "$nbytes" "$digest" "$md5" >> "$HERE/run.log"
echo "SEQ=$SEQ CAP=20 status=$code bytes=$nbytes sha256_16=$digest ctype=$ctype"