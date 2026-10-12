#!/usr/bin/env bash
# Area N — cross-host check of the two POST-only routes (2026-10-12).
# Claim: issue #8. Mirrors findings-log/2026-10-11-pde-csr-oracle/probe.sh
# cell-for-cell on the control set, so each host's oracle is established before
# its own data cells are read.
#
# Read-only and unauthenticated: GET and OPTIONS with an empty body only.
# No POST, no token exchange, no Authorization / Cookie / x-api-key.
# 16 requests, hard cap. >=2.5 s between requests to the same host.
set -uo pipefail

DIR="findings-log/2026-10-12-csr-cross-host"
OUT="$DIR/results.jsonl"
HDRDIR="$DIR/headers"
LOG="$DIR/run.log"
mkdir -p "$HDRDIR"
: > "$OUT"
: > "$LOG"

n=0
HOST=""

req() {
  local method="$1" path="$2"
  n=$((n+1))
  local url="https://${HOST}/${path}"
  local stem="$(printf '%02d' $n)-${method}-$(echo "$path" | tr '/.' '__')"
  local hdrfile="$HDRDIR/${stem}.hdr"
  local bodyfile="$HDRDIR/${stem}.body"
  echo "[$n] $method $url" | tee -a "$LOG"
  # -s silent, -D dump headers, -o body, --compressed (harmless), no auth, empty body
  curl -s -X "$method" --compressed -D "$hdrfile" -o "$bodyfile" --max-time 20 "$url"
  local status=$(head -1 "$hdrfile" | tr -d '\r')
  local ctype=$(grep -i '^content-type:' "$hdrfile" | tr -d '\r' || echo "content-type: (none)")
  local errtype=$(grep -i '^x-amzn-errortype:' "$hdrfile" | tr -d '\r' || echo "x-amzn-errortype: (none)")
  local caerr=$(grep -i '^x-ca-err:' "$hdrfile" | tr -d '\r' || echo "x-ca-err: (none)")
  local cors_origin=$(grep -i '^access-control-allow-origin:' "$hdrfile" | tr -d '\r' || echo "acao: (none)")
  local cors_methods=$(grep -i '^access-control-allow-methods:' "$hdrfile" | tr -d '\r' || echo "acam: (none)")
  local xcache=$(grep -i '^x-cache:' "$hdrfile" | tr -d '\r' || echo "x-cache: (none)")
  local bytes=$(wc -c < "$bodyfile" | tr -d ' ')
  local bodyhead=$(head -c 200 "$bodyfile" | tr -d '\r\n')
  printf '{"n":%d,"host":%s,"method":"%s","path":"%s","status":%s,"ctype":%s,"bytes":%d,"body_head":%s}\n' \
    "$n" \
    "$(printf '%s' "$HOST" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" \
    "$method" "$path" \
    "$(printf '%s' "$status" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" \
    "$(printf '%s' "$ctype $errtype $caerr $cors_origin $cors_methods $xcache" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" \
    "$bytes" \
    "$(printf '%s' "$bodyhead" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" >> "$OUT"
  echo "  $status | $ctype | $errtype | $caerr | $cors_origin | $cors_methods | ${bytes}B" | tee -a "$LOG"
  sleep 2.5
}

# The area's two target paths, plus the two control paths. Both methods on each,
# because the verdict rule (docs/09 section 2) needs GET and OPTIONS together.
CELLS=(
  "connect/carepartner/v13/display/message"
  "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c"
  "connect/csr/v2/display/message"
  "connect/v2/display/message"
)

for HOST in clcloud.minimed.com clcloud-trials.minimed.com; do
  echo "=== $HOST ===" | tee -a "$LOG"
  # 1-2 controls (GET pair), 3-4 control (OPTIONS pair) run BEFORE the data
  # cells, so the oracle verdict is not contaminated by the data it judges.
  req GET    "connect/carepartner/v13/display/message"
  req GET    "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c"
  req OPTIONS "connect/carepartner/v13/display/message"
  req OPTIONS "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c"
  # 5-8 the area's own cells
  req GET    "connect/csr/v2/display/message"
  req OPTIONS "connect/csr/v2/display/message"
  req GET    "connect/v2/display/message"
  req OPTIONS "connect/v2/display/message"
done

echo "DONE n=$n (cap 16)" | tee -a "$LOG"