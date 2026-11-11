#!/usr/bin/env bash
# Area DP — two GETs. Everything after this is offline reading of the bodies it leaves.
#
# WHY ONLY TWO. The pump-data parser is entirely in one lazy chunk (§2 of FINDINGS.md):
# 22 of 24 pump-data tokens are ZERO in the eager bundle. So the eager bundle is fetched
# only as the control that proves that split, and the chunk is fetched because it is the
# one body that carries the parser.
#
# SPACING. Both requests are on carelink.minimed.eu, 10.0 s apart, inside the >=2.5 s
# floor. t_sent is recorded per request from `date +%s.%N` taken BEFORE the curl.
# Only two gaps exist, so NO spacing statistic is claimed — two points cannot establish
# a floor. The verifier should recompute the gap from results.jsonl rather than trust
# this comment.
#
# CONTROLS. Request 1 is itself the control: its sha256 must reproduce area K's pinned
# 0fb4fbd483b5f5d2… (3,417,255 B). If it does not, the app has been rebuilt and NO byte
# offset in FINDINGS.md applies — abort rather than reading a moved artefact.

set -uo pipefail

HOST="carelink.minimed.eu"
OUT="${DP_OUT:-./bodies}"
PINNED_MAIN="0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa"
PINNED_MAIN_BYTES=3417255

mkdir -p "$OUT"

fetch () {  # $1=seq $2=url $3=filename
  local seq="$1" url="$2" fn="$3"
  local t0 t1 code
  t0=$(date +%s.%N)
  code=$(curl -sS -o "$OUT/$fn" -w "%{http_code}" --max-time 90 "$url")
  t1=$(date +%s.%N)
  local bytes sha
  bytes=$(stat -c%s "$OUT/$fn" 2>/dev/null || echo 0)
  sha=$(sha256sum "$OUT/$fn" | cut -d' ' -f1)
  printf '{"seq":%s,"method":"GET","url":"%s","status":%s,"bytes":%s,"sha256":"%s","t_sent":%s,"t_done":%s}\n' \
    "$seq" "$url" "$code" "$bytes" "$sha" "$t0" "$t1" >> "$OUT/results.jsonl"
  printf '%s -> %s %s B %s\n' "$seq" "$code" "$bytes" "${sha:0:16}"
}

# --- request 1: the control. Must reproduce the pinned digest. ---
fetch 1 "https://$HOST/main.6595daf83bd6d4b1.js" "patient-main.js"

GOT_SHA=$(sha256sum "$OUT/patient-main.js" | cut -d' ' -f1)
GOT_BYTES=$(stat -c%s "$OUT/patient-main.js")
if [ "$GOT_SHA" != "$PINNED_MAIN" ] || [ "$GOT_BYTES" != "$PINNED_MAIN_BYTES" ]; then
  echo "CONTROL FAILED: eager bundle moved (got $GOT_BYTES B $GOT_SHA)."
  echo "Every byte offset in FINDINGS.md is now void. ABORT."
  exit 1
fi
echo "CONTROL OK: eager bundle reproduces $PINNED_MAIN"

# --- request 2: the chunk that carries the pump-data parser. ---
sleep 3
fetch 2 "https://$HOST/6746.c6795ff7e9ff468d.js" "6746.c6795ff7e9ff468d.js"

echo
echo "Read the bodies offline:"
echo "  python3 extract.py $OUT"
