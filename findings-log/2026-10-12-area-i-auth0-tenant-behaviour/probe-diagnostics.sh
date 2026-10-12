#!/usr/bin/env bash
# Area I — RE-ISSUE of diagnostic seq 30, the load-bearing wire capture.
#
# WHY THIS FILE EXISTS. The supplementary run recorded seq 30/31/32 with
# hand-written `ctype_full` values and no committed header or body files. seq 30
# — the `curl -v` capture that proves `Access-Control-Request-Method: POST` is
# actually on the wire — has no artefact on disk at all, because that
# invocation wrote its body to /dev/null and piped its verbose output to a
# terminal filter. A hand-authored field that looks machine-parsed is the most
# dangerous kind of artefact: everything downstream reads it as captured.
#
# So seq 30 is re-issued here, with the verbose REQUEST transcript, the response
# HEADERS and the response BODY all written to files a reviewer can open. This
# is the single request spent from the last of the supplementary budget
# (14 of 14). seq 31 and seq 32 did survive on disk and are committed from
# those originals; only this one had to be re-issued.
#
# OPTIONS, empty body. No POST. Per-host flock, sleep inside the lock.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE"
HOST=carelink-login.medtronic.eu
TAG="d11-mcom-acrm-verbose"

LOCKS=""
d="$HERE"
while [ "$d" != "/" ]; do
  if [ -f "$d/.loop/BRIEF.md" ]; then LOCKS="$d/.loop"; break; fi
  d="$(dirname "$d")"
done
: "${LOCKS:?could not locate the pool .loop directory}"

mkdir -p "$LOCKS"
touch "$LOCKS/host-$HOST.lock"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
flock "$LOCKS/host-$HOST.lock" -c "
  sleep 2.5
  curl -sS --compressed -X OPTIONS \
    -H 'Origin: https://probe.invalid' \
    -H 'Access-Control-Request-Method: POST' \
    -H 'Access-Control-Request-Headers: content-type' \
    -v \
    -D '$OUT/headers/$TAG.h' \
    -o '$OUT/bodies/$TAG.b' \
    'https://$HOST/oidc/register'
" > "$OUT/headers/$TAG.txt" 2>&1
CODE=$?

# The verbose transcript is the point: it contains BOTH the '>' request lines
# (proving the header was sent) and the '<' response lines (proving what came
# back). Assert that the request line for the header is actually present -- if
# curl ever stops sending it, this script fails rather than quietly recording a
# row that would not support the claim.
if ! grep -q '^> Access-Control-Request-Method: POST' "$OUT/headers/$TAG.txt"; then
  echo "FATAL: the ACRM request header is absent from the transcript; not recording a row" >&2
  exit 1
fi

BYTES=$(wc -c < "$OUT/bodies/$TAG.b" | tr -d ' ')
SHA=$(sha256sum "$OUT/bodies/$TAG.b" | cut -d' ' -f1)
CF=$(awk 'NR>1' "$OUT/headers/$TAG.h" | tr -d '\r' | awk '
  /: / { i = index($0, ": "); k = tolower(substr($0, 1, i-1)); v = substr($0, i+2)
         if (k in a) a[k] = a[k] ", " v; else a[k] = v }
  END { for (k in a) printf "%s: %s|", k, a[k] }' | sed 's/|$//')
STATUS=$(grep -oE '^HTTP/2 [0-9]+' "$OUT/headers/$TAG.h" | head -1 | grep -oE '[0-9]+$')

python3 - "$OUT/results.jsonl" "$STATUS" "$CODE" "$BYTES" "$SHA" "$CF" "$TS" "$TAG" "$HOST" <<'PY'
import json, sys
(_, rj, status, code, nbytes, sha, cf, ts, tag, host) = sys.argv
rows = [json.loads(l) for l in open(rj) if l.strip()]
new = {
  "seq": 30, "host": host, "host_tag": tag,
  "method": "OPTIONS", "path": "/oidc/register",
  "role": "DIAGNOSTIC-wire-presence-acrm-HEADER",
  "sent_headers": ("Origin: https://probe.invalid | "
                   "Access-Control-Request-Method: POST | "
                   "Access-Control-Request-Headers: content-type (empty body)"),
  "http_status": status, "curl_exit": int(code),
  "body_bytes": int(nbytes), "body_sha256": sha,
  "ctype_full": cf, "ts_utc": ts,
  "budget": "SUPPLEMENTARY-14 re-issue of a row whose capture was not retained",
  "note": ("RE-ISSUED. The original seq 30 row (ts 18:18:15Z) carried a hand-written "
           "ctype_full and no header, body or transcript file: that invocation wrote its "
           "body to /dev/null and piped -v output to a terminal filter, so nothing "
           "survived to commit. This row replaces it with a retained capture -- "
           "headers/" + tag + ".h, bodies/" + tag + ".b and headers/" + tag + ".txt, the "
           "full curl -v transcript carrying both the '>' request lines and the '<' "
           "response lines. probe-diagnostics.sh asserts '> Access-Control-Request-Method: "
           "POST' is present in the transcript BEFORE this row is written, so the row "
           "cannot exist unless the header was demonstrably on the wire."),
  "supersedes": ("the original seq 30 row, ts_utc 2026-10-12T18:18:15Z, which asserted "
                 "this digest with a hand-authored header field and no retained capture"),
}
out = [new if r['seq'] == 30 else r for r in rows]
out.sort(key=lambda r: r['seq'])
with open(rj, 'w') as f:
    for r in out:
        f.write(json.dumps(r) + '\n')
print('ledger: seq 30 replaced in place')
PY
echo "captured: status=$STATUS bytes=$BYTES sha=${SHA:0:12}"
echo "transcript lines: $(wc -l < "$OUT/headers/$TAG.txt")"
echo "ACRM on the wire: $(grep -c '^> Access-Control-Request-Method: POST' "$OUT/headers/$TAG.txt") occurrence(s)"