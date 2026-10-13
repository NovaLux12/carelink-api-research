#!/bin/bash
# Area K follow-up — ONE cell, the URL-form defect.
#
# WHY THIS CELL EXISTS. runtime-map.py re-derived the chunk filenames from the
# runtime bundle's own f.u and found that the committed list carries chunk 2076
# under its ID where the runtime emits the NAME `common`. The sweep therefore
# requested /2076.<hash>.js and will record a 404 that has nothing to do with the
# corpus — it is the list's filename, not the chunk, being wrong. Without this
# cell the sweep would close with "211 cells carry a verdict" while one of them
# carries a verdict about a file that does not exist.
#
# The cell is the file the runtime actually names, so the sweep's verdict for the
# corpus is about the corpus. Its ledger row is appended to the same
# results.jsonl in the same schema under the same per-host flock with the sleep
# inside the lock, because it is a request and every request gets a row
# (pool brief, the ledger is the binding rule).
#
# The schema duplication with probe.sh is deliberate and checked, not
# convenient: each harness is committed "as sent" and must stand alone, so the
# row is written from the environment here exactly as it is there. A self-check
# at the end asserts the key set of this row equals the key set of an existing
# row, so a drift between the two copies FAILS instead of quietly producing a
# second-shaped ledger.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
LOOP="$(cd "$HERE/../../../.." && pwd)"
OUT=$HERE/headers
DELAY=${DELAY:-2.5}
CAP=${CAP:-230}
HOST=carelink.minimed.eu
LOCK="$LOOP/host-$HOST.lock"
LEDGER=$HERE/results.jsonl
PATH_TO_FETCH=${1:?usage: probe-followup.sh <path>}
TMPBODIES=${TMPBODIES:?set TMPBODIES to the same directory the sweep wrote bodies to}
mkdir -p "$OUT"
[ -e "$LOCK" ] || : > "$LOCK"

SEQ=$(python3 -c '
import json,sys
m=0
for line in open(sys.argv[1]):
    line=line.strip()
    if line: m=max(m,int(json.loads(line)["seq"]))
print(m)' "$LEDGER")
echo "follow-up: ledger holds $SEQ rows; next seq $((SEQ+1))" >&2
if [ "$((SEQ+1))" -gt "$CAP" ]; then
  echo "CAP $CAP REACHED — refusing to send." >&2; exit 9
fi

tag="k-fu-$(printf '%s' "$PATH_TO_FETCH" | sed 's|/|_|g; s/\./-/g')"
url="https://$HOST$PATH_TO_FETCH"
t_queued=$(date -u +%FT%T.%3NZ)
out=$(flock "$LOCK" "$HERE/send.sh" "$DELAY" "$OUT/$tag.h" "$TMPBODIES/$tag.b" "$url" 2>&1)
t_done=$(date -u +%FT%T.%3NZ)
t_sent=$(printf '%s\n' "$out"  | sed -n 's/^TS_SENT //p'     | head -1)
code=$(printf '%s\n'    "$out"  | sed -n 's/^HTTP_STATUS //p' | head -1)
curl_exit=$(printf '%s\n' "$out" | sed -n 's/^CURL_EXIT //p'  | head -1)
[ -n "$t_sent" ] || t_sent="(unrecorded)"; [ -n "$code" ] || code="000"; [ -n "$curl_exit" ] || curl_exit="-1"
ct="(none)"; [ -f "$OUT/$tag.h" ] && ct=$(grep -i '^content-type:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$ct" ] || ct="(none)"
amz="(none)"; caerr="(none)"; xcache="(none)"; acao="(none)"; cenc="(none)"
if [ -f "$OUT/$tag.h" ]; then
  amz=$(grep -i '^x-amzn-errortype:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$amz" ] || amz="(none)"
  caerr=$(grep -i '^x-ca-err:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$caerr" ] || caerr="(none)"
  xcache=$(grep -i '^x-cache:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$xcache" ] || xcache="(none)"
  acao=$(grep -i '^access-control-allow-origin:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$acao" ] || acao="(none)"
  cenc=$(grep -i '^content-encoding:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$cenc" ] || cenc="(none)"
fi
ctype_full="(none)"; [ -f "$OUT/$tag.h" ] && ctype_full=$(tr '\r' ' ' < "$OUT/$tag.h" | tr '\n' '|' | sed 's/|$//'); [ -n "$ctype_full" ] || ctype_full="(none)"
bytes=0; sha="(none)"; mtns=""
if [ -f "$TMPBODIES/$tag.b" ]; then
  bytes=$(stat -c%s "$TMPBODIES/$tag.b"); sha=$(sha256sum "$TMPBODIES/$tag.b" | cut -d' ' -f1)
  mtns=$(python3 -c 'import os,sys;print(os.stat(sys.argv[1]).st_mtime_ns)' "$TMPBODIES/$tag.b")
fi
V_SEQ="$((SEQ+1))" V_HOST="$HOST" V_TAG="$tag" V_PATH="$PATH_TO_FETCH" \
V_ROLE="FOLLOWUP-the-file-the-runtime-actually-names-for-chunk-2076-the-committed-list-carries-the-id-instead" \
V_URL="$url" V_CODE="$code" V_EXIT="$curl_exit" V_CT="$ct" V_CFULL="$ctype_full" V_BYTES="$bytes" \
V_SHA="$sha" V_MTNS="$mtns" V_DELAY="$DELAY" V_TQ="$t_queued" V_TS="$t_sent" V_TD="$t_done" \
V_AMZ="$amz" V_CAERR="$caerr" V_XCACHE="$xcache" V_ACAO="$acao" V_CENC="$cenc" \
python3 -c '
import json, os, sys
e = os.environ
row = {
  "seq": int(e["V_SEQ"]), "host": e["V_HOST"], "host_tag": e["V_TAG"],
  "method": "GET", "path": e["V_PATH"], "role": e["V_ROLE"], "url": e["V_URL"],
  "http_status": e["V_CODE"], "curl_exit": int(e["V_EXIT"]),
  "content_type": e["V_CT"], "ctype_full": e["V_CFULL"],
  "content_encoding": e["V_CENC"],
  "x_amzn_errortype": e["V_AMZ"], "x_ca_err": e["V_CAERR"],
  "x_cache": e["V_XCACHE"], "access_control_allow_origin": e["V_ACAO"],
  "body_bytes": int(e["V_BYTES"]), "body_sha256": e["V_SHA"],
  "body_mtime_ns": e["V_MTNS"] or "(none)",
  "delay_declared_s": e["V_DELAY"],
  "t_queued": e["V_TQ"], "t_sent": e["V_TS"], "t_done": e["V_TD"],
}
open(sys.argv[1], "a").write(json.dumps(row) + "\n")
' "$LEDGER"
printf '%s seq=%s host=%s tag=%s code=%s ctype=%s bytes=%s sha=%s\n' \
  "$t_sent" "$((SEQ+1))" "$HOST" "$tag" "$code" "$ct" "$bytes" "$sha" >> "$HERE/run.log"
printf '%s\t%s\t%s\t%s\t%s\n' "$PATH_TO_FETCH" "$code" "$bytes" "$sha" \
  "$(LC_ALL=C grep -c -E 'baseUrlPde|baseUrlCumulus|baseUrlCms|baseUrlAem|baseUrlCareLink|baseUrl|discover/android|discover|clcloud|api/carepartner|pde|system\.gc\.gz\.transition\.flags|patient-timeline|dialog-lite' "$TMPBODIES/$tag.b" 2>/dev/null || echo 0)" >> "$HERE/verdicts.tsv"

# Self-check: this row's key set must equal an existing row's. A schema drift
# between the two harness copies FAILS here rather than producing a ledger with
# two shapes in it, which is exactly the defect area G's pass had to re-encode.
python3 - "$LEDGER" <<'EOF'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
assert len(rows) >= 2
a, b = set(rows[0].keys()), set(rows[-1].keys())
if a != b:
    print("SCHEMA DRIFT: only in first row:", sorted(a - b), file=sys.stderr)
    print("SCHEMA DRIFT: only in last  row:", sorted(b - a), file=sys.stderr)
    raise SystemExit(1)
print("schema self-check ok: %d rows, %d keys, identical key set" % (len(rows), len(a)))
EOF
echo "rows now: $(wc -l < "$LEDGER")" >&2