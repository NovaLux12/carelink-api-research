#!/usr/bin/env bash
# Area A, batch 3 — one request.
#
# Batch 2 answered: carelink.medtronic.eu serves an entry document byte-identical to
# carelinkhp.minimed.eu's (md5 6aedf6c4004fbb29a298bc62128480be). That makes
# docs/01:69's verdict "does NOT serve that bundle" testable in one request: if the
# build that document names (main.fb5f8cb7eb60c4d5.js) is served there, the host DOES
# serve the bundle and the "false positive" reading was an artefact of only ever
# measuring the document, which is the catch-all.
#
# Batch 2 probed main.759cddab23085086.js on this host and correctly got the 5518 B
# fallback — but that is the OTHER build's asset name, so that row proves nothing
# about this host. This batch asks the right question. GET only.
set -uo pipefail

# Derived, never hardcoded: HERE is <main-clone>/.loop/worktrees/<w>/findings-log/<dir>,
# so five levels up is the main clone, and the per-host locks must live THERE rather
# than in this worktree -- four pool workers share one .loop (BRIEF 5).
REPO="$(cd "$HERE/../../../../.." && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
HDR="$HERE/headers"
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/areaA-XXXXXX")"
trap 'rm -rf "$SCRATCH"' EXIT

host="carelink.medtronic.eu"
tag="carelink-medtronic-eu-asset-fb5f8cb7"
out="$SCRATCH/$tag"
touch "$REPO/.loop/host-$host.lock" 2>/dev/null || true
code=$(flock "$REPO/.loop/host-$host.lock" -c "
  sleep 2.5
  curl -s --compressed --max-time 90 -A 'carelink-bridge-research/1.0' \
    -D '$out.h' -o '$out.b' -w '%{http_code}' 'https://$host/main.fb5f8cb7eb60c4d5.js'
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
 "path":"/main.fb5f8cb7eb60c4d5.js",
 "role":"CANDIDATE-main.fb5f8cb7eb60c4d5.js on carelink.medtronic.eu - the build its OWN entry document names; tests docs/01:69's 'does not serve that bundle' verdict",
 "sent_headers":"(none)","http_status":code,"curl_exit":int(exit_),"content_type":ctype,
 "content_length_hdr":"(not recorded)","content_encoding":"(not recorded)","vary":"(not recorded)",
 "x_amz_cf_pop":"(not recorded)","server":"(not recorded)","via":"(not recorded)","last_modified":"(not recorded)",
 "body_bytes":int(nbytes),"body_sha256_prefix16":digest,"body_md5":md5,"ctype_full":fullhdr}
open(L,"a").write(json.dumps(row)+"\n")
PY

printf '%s seq=%s host_seq=%s host=%s tag=%s status=%s ctype=%s bytes=%s sha256_16=%s md5=%s\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$SEQ" "$hseq" "$host" "$tag" "$code" "$ctype" "$nbytes" "$digest" "$md5" >> "$RUNLOG"
echo "SEQ=$SEQ CAP=20 status=$code bytes=$nbytes sha256_16=$digest md5=$md5 ctype=$ctype"