#!/usr/bin/env bash
set -uo pipefail
HOST="clcloud.minimed.eu"
OUT="findings-log/2026-10-11-pde-csr-oracle/results.jsonl"
HDRDIR="findings-log/2026-10-11-pde-csr-oracle/headers"
mkdir -p "$HDRDIR"
: > "$OUT"
n=0
req() {
  local method="$1" path="$2"
  n=$((n+1))
  local url="https://${HOST}/${path}"
  local hdrfile="$HDRDIR/$(printf '%02d' $n)-${method}-$(echo "$path" | tr '/.' '__').hdr"
  local bodyfile="$HDRDIR/$(printf '%02d' $n)-${method}-$(echo "$path" | tr '/.' '__').body"
  echo "[$n] $method $url"
  # -s silent, -D dump headers, -o body, --compressed (harmless), no auth, empty body
  curl -s -X "$method" --compressed -D "$hdrfile" -o "$bodyfile" --max-time 20 "$url"
  local status=$(head -1 "$hdrfile" | tr -d '\r')
  local ctype=$(grep -i '^content-type:' "$hdrfile" | tr -d '\r' || echo "content-type: (none)")
  local errtype=$(grep -i '^x-amzn-errortype:' "$hdrfile" | tr -d '\r' || echo "x-amzn-errortype: (none)")
  local caerr=$(grep -i '^x-ca-err:' "$hdrfile" | tr -d '\r' || echo "x-ca-err: (none)")
  local cors_origin=$(grep -i '^access-control-allow-origin:' "$hdrfile" | tr -d '\r' || echo "acao: (none)")
  local cors_methods=$(grep -i '^access-control-allow-methods:' "$hdrfile" | tr -d '\r' || echo "acam: (none)")
  local bytes=$(wc -c < "$bodyfile" | tr -d ' ')
  local bodyhead=$(head -c 200 "$bodyfile" | tr -d '\r\n')
  printf '{"n":%d,"method":"%s","path":"%s","status":%s,"ctype":%s,"bytes":%d,"body_head":%s}\n' \
    "$n" "$method" "$path" \
    "$(printf '%s' "$status" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" \
    "$(printf '%s' "$ctype $errtype $caerr $cors_origin $cors_methods" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" \
    "$bytes" \
    "$(printf '%s' "$bodyhead" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" >> "$OUT"
  echo "  $status | $ctype | $errtype | $caerr | $cors_origin | ${bytes}B"
  sleep 2.5
}
# 1-4 controls
req GET "connect/carepartner/v13/display/message"
req GET "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c"
req OPTIONS "connect/carepartner/v13/display/message"
req OPTIONS "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c"
# PDE
req GET "connect/pde/v1/display/message"
req OPTIONS "connect/pde/v1/display/message"
req GET "connect/pde/v2/display/message"
req OPTIONS "connect/pde/v2/display/message"
req GET "connect/pde/v3/display/message"
req OPTIONS "connect/pde/v3/display/message"
req GET "connect/pde/v3/discover/android/3.6"
req OPTIONS "connect/pde/v3/discover/android/3.6"
# CSR
req GET "connect/csr/v1/display/message"
req OPTIONS "connect/csr/v1/display/message"
req GET "connect/csr/v2/display/message"
req OPTIONS "connect/csr/v2/display/message"
req GET "connect/csr/v3/display/message"
req OPTIONS "connect/csr/v3/display/message"
# bare carepartner
req GET "connect/carepartner/"
req OPTIONS "connect/carepartner/"
req GET "connect/carepartner/v13"
req OPTIONS "connect/carepartner/v13"
req GET "connect/carepartner/v13/discover"
req OPTIONS "connect/carepartner/v13/discover"
# bare v2
req GET "connect/v2/display/message"
req OPTIONS "connect/v2/display/message"
echo "DONE n=$n (cap 30)"
