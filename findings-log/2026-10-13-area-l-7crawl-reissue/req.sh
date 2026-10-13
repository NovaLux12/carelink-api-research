#!/usr/bin/env bash
# req.sh <path> <tag> <role>   -- path is full CDX query path starting with /CC-MAIN-.../cdx-server/cdx?...
# Sends GET to index.commoncrawl.org only. Cap 60 requests (this pass's cap).
DELAY=3.5
HERE="$(cd "$(dirname "$0")" && pwd)"
WT="$(cd "$HERE/../.." && pwd)"
LOOP="$(cd "$WT/../.." && pwd)"
LOCK="$LOOP/host-index.commoncrawl.org.lock"
BODIES="${TMPDIR:-/tmp}/l79-bodies"
mkdir -p "$BODIES" "$HERE/headers" "$HERE/tmp"
if [ "$#" -lt 3 ]; then echo "usage: req.sh <path> <tag> <role>" >&2; exit 2; fi
path="$1"; tag="$2"; role="$3"
cd "$HERE"
SEQ=0
if [ -s results.jsonl ]; then SEQ="$(wc -l < results.jsonl | tr -d ' ')"; fi
SEQ=$((SEQ + 1))
if [ "$SEQ" -gt 60 ]; then echo "REFUSED: seq $SEQ > 60 (cap)" >&2; exit 9; fi
seqp="$(printf '%02d' "$SEQ")"
H="headers/${seqp}-${tag}.h"
E="headers/${seqp}-${tag}.err"
B="$BODIES/${seqp}.body"
R="tmp/${seqp}"
url="https://index.commoncrawl.org${path}"
now() { date -u +%FT%T.%3NZ; }
t_queued="$(now)"
{
  printf 'sleep %s\n' "$DELAY"
  printf 'date -u +%%FT%%T.%%3NZ > %q\n' "${R}.t0"
  printf 'curl -s --compressed -D %q -o %q -w %q %q > %q 2> %q\n' \
         "$H" "$B" '%{http_code}' "$url" "${R}.code" "$E"
  printf 'date -u +%%FT%%T.%%3NZ > %q\n' "${R}.t1"
} > "${R}.sh"
flock "$LOCK" sh "${R}.sh"
rc=$?
code="$(cat "${R}.code" 2>/dev/null || echo 000)"
t_sent="$(cat "${R}.t0" 2>/dev/null || echo '')"
t_done="$(cat "${R}.t1" 2>/dev/null || echo '')"
bytes="$(wc -c < "$B" 2>/dev/null || echo 0)"
sha="$(sha256sum "$B" 2>/dev/null | cut -d' ' -f1)"; [ -z "$sha" ] && sha=""
ct="$(grep -i '^content-type:' "$H" 2>/dev/null | head -1 | tr -d '\r' | sed 's/^[^:]*: *//')"
disc="content-type: ${ct}"
for h in x-amzn-errortype x-cache server; do
  v="$(grep -i "^${h}:" "$H" 2>/dev/null | head -1 | tr -d '\r' | sed 's/^[^:]*: *//')"
  [ -n "$v" ] && disc="${disc}|${h}: ${v}"
done
python3 - "$B" "${R}.proj" "$path" <<'PY'
import json,sys
body_path,proj_path,path=sys.argv[1:4]
recs=0; ipro=[]
minimed_hosts=set()
try:
    with open(body_path,'rb') as f: raw=f.read()
    txt=raw.decode('utf-8',errors='replace')
    for line in txt.splitlines():
        line=line.strip()
        if not line: continue
        try:
            o=json.loads(line)
            if isinstance(o,dict) and 'timestamp' in o and 'url' in o:
                recs+=1
            if isinstance(o,dict):
                u=o.get('url','')
                if 'ipro/hcp' in str(u):
                    ipro.append(u)
                if 'minimed.eu' in str(u):
                    # host extraction
                    m=None
                    import urllib.parse as up
                    # url like https://carelink.minimed.eu/...
                    host=u
                    if '://' in u:
                        host=up.urlsplit(u).hostname or u
                    minimed_hosts.add(host)
        except Exception:
            pass
except Exception:
    pass
open(proj_path,'w').write(json.dumps({'records':recs,'ipro_hcp_urls':ipro,'minimed_hosts':sorted(minimed_hosts)}))
PY
proj="$(cat "${R}.proj" 2>/dev/null || echo '{}')"
printf '%s  seq=%-3s %s  %s  %s\n' "$t_done" "$SEQ" "$code" "$path" >> run.log
python3 - "$SEQ" "$tag" "$role" "$code" "$rc" "$bytes" "$sha" "$disc" "$t_queued" "$t_sent" "$t_done" "$path" "$proj" >> results.jsonl <<'PY'
import json,sys
(seq,tag,role,code,rc,nbytes,sha,disc,tq,ts,td,path,proj)=sys.argv[1:14]
row={"seq":int(seq),"host":"index.commoncrawl.org","host_tag":tag,"method":"GET","path":path,
     "role":role,"http_status":code,"curl_exit":int(rc),"body_bytes":int(nbytes),
     "body_sha256":sha,"disc_headers":disc,"t_queued":tq,"t_sent":ts,"t_done":td}
row.update(json.loads(proj))
print(json.dumps(row))
PY
echo "seq ${SEQ}  ${code}  ${bytes}B  ${path}"
