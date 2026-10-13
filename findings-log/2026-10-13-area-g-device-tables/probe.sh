#!/bin/bash
# Area G probe — per-build device-table assets with controls first per host.
# Claim issue #32. Cap 12, GET only, curl --compressed, 2.5 s sleep INSIDE per-host flock.
# Order per host: certainly-absent control, entry-document control, then main asset.
# Asset bodies (~3.4 MB) are written to $TMPBODIES, never committed (area A precedent).
set -u
# Derived, never hardcoded: probe.sh sits at <main>/.loop/worktrees/<w>/findings-log/<dir>/,
# so five levels up is the main clone, where the per-host locks live (pool brief §5).
HERE="$(cd "$(dirname "$0")" && pwd)"
MAIN="$(cd "$HERE/../../../../.." && pwd)"
LOGDIR=$HERE
OUT=$LOGDIR/headers
TMPBODIES=${TMPBODIES:-$(mktemp -d)}
mkdir -p "$OUT" "$TMPBODIES"
RUNLOG=$LOGDIR/run.log
JSONL=$LOGDIR/results.jsonl
: > "$RUNLOG"; : > "$JSONL"
echo "run start: $(date -u +%FT%T.%3NZ) tmpbodies=$TMPBODIES" | tee -a "$RUNLOG"
SEQ=0
req() { # req <host> <path> <role> <tag>
  local host="$1" path="$2" role="$3" tag="$4"
  SEQ=$((SEQ+1)); local seq=$SEQ
  local t_queued=$(date -u +%FT%T.%3NZ)
  local url="https://$host$path"
  local code
  code=$(flock "$MAIN/.loop/host-$host.lock" -c "sleep 2.5; curl -s --compressed -D '$OUT/$tag.h' -o '$TMPBODIES/$tag.b' -w '%{http_code}' --max-time 120 '$url'")
  local curl_exit=$?
  local t_sent t_done
  # t_sent approximated inside lock pre-curl is unobservable from outside;
  # record queued time and completion time; spacing floor derived from run.log + mtimes.
  t_done=$(date -u +%FT%T.%3NZ)
  # Re-read t_queued as t_sent basis: the sleep+curl happened inside the lock.
  t_sent="$t_queued"
  local ct="(none)"; local clen="(none)"
  ct=$(grep -i '^content-type:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[Cc]ontent-[Tt]ype: *//' || echo "(none)")
  [ -z "$ct" ] && ct="(none)"
  local bytes=0 sha="(none)"
  if [ -f "$TMPBODIES/$tag.b" ]; then bytes=$(stat -c%s "$TMPBODIES/$tag.b"); sha=$(sha256sum "$TMPBODIES/$tag.b" | cut -d' ' -f1); fi
  local ctype_full=$(tr '\r' ' ' < "$OUT/$tag.h" | tr '\n' '|' | sed 's/|$//')
  # host_seq: count of prior rows for this host + 1
  local host_seq=$(grep -c "\"host\":\"$host\"" "$JSONL" 2>/dev/null || true)
  host_seq=$((host_seq+1))
  printf '{"seq":%s,"host_seq":%s,"host":"%s","host_tag":"%s","method":"GET","path":"%s","role":"%s","sent_headers":"(none)","http_status":"%s","curl_exit":%s,"content_type":"%s","ctype_full":"%s","body_bytes":%s,"body_sha256":"%s","t_queued":"%s","t_sent":"%s","t_done":"%s"}\n' \
    "$seq" "$host_seq" "$host" "$tag" "$path" "$role" "$code" "$curl_exit" "$ct" "$ctype_full" "$bytes" "$sha" "$t_queued" "$t_sent" "$t_done" >> "$JSONL"
  echo "$t_queued $t_done seq=$seq host=$host tag=$tag code=$code ctype=$ct bytes=$bytes sha=$sha" >> "$RUNLOG"
  echo "seq=$seq host=$host path=$path code=$code ctype=$ct bytes=$bytes sha=$sha" >&2
}
# Host 1: clinic pow build
req carelinkhp.minimed.eu "/main.deadbeefdeadbeef.js" "CONTROL-absent-proves-fallback-live" "hp-absent"
req carelinkhp.minimed.eu "/" "CONTROL-entry-anchors-build-identity" "hp-root"
req carelinkhp.minimed.eu "/main.fb5f8cb7eb60c4d5.js" "CANDIDATE-clinic-pow-main-asset" "hp-main"
# Host 2: support cua build
req carelink-support.medtronic.eu "/main.deadbeefdeadbeef.js" "CONTROL-absent-proves-fallback-live" "sup-absent"
req carelink-support.medtronic.eu "/" "CONTROL-entry-anchors-build-identity" "sup-root"
req carelink-support.medtronic.eu "/main.759cddab23085086.js" "CANDIDATE-support-cua-main-asset" "sup-main"
echo "run end: $(date -u +%FT%T.%3NZ)" | tee -a "$RUNLOG"
# Mechanical re-encode: header blocks can contain raw double quotes (e.g. ETag
# W/"..."), which the printf above emits verbatim. Re-encode with identical
# fields so results.jsonl is valid JSON (found 2026-10-13: row 1 failed to parse).
python3 - "$JSONL" <<'EOF'
import re, json, sys
p = sys.argv[1]
out = []
for l in open(p).read().splitlines():
    m = re.match(r'^(.*"ctype_full":")(.*)(",\"body_bytes":.*)$', l)
    assert m, l[:120]
    head, ctype, tail = m.groups()
    o = json.loads(head + '"}')
    tm = re.match(r'^","body_bytes":(\d+),"body_sha256":"([0-9a-f]+)","t_queued":"([^"]+)","t_sent":"([^"]+)","t_done":"([^"]+)"\}$', tail)
    assert tm, tail[:200]
    o['ctype_full'] = ctype
    o['body_bytes'] = int(tm.group(1))
    o['body_sha256'] = tm.group(2)
    o['t_queued'] = tm.group(3)
    o['t_sent'] = tm.group(4)
    o['t_done'] = tm.group(5)
    out.append(o)
open(p, 'w').write('\n'.join(json.dumps(o) for o in out) + '\n')
print(f're-encoded {len(out)} rows', file=sys.stderr)
EOF
echo "TMPBODIES=$TMPBODIES"
