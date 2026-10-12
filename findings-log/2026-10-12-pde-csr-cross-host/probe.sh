#!/usr/bin/env bash
# Area U — are the csr/v1, csr/v3 and PDE cells dead on .com and -trials too,
# or only on .eu?
#
# Method-identical to the Area C harness (2026-10-11-pde-csr-oracle/probe.sh):
#   - GET and OPTIONS with an EMPTY body. No POST, no token exchange, no auth.
#   - >=2.5 s between requests to the same host (enforced by `sleep` in req()).
#   - Controls run FIRST on each host, so the oracle verdict is not
#     contaminated by the data it judges.
#   - Discriminator is x-amzn-errortype (+ CORS on OPTIONS), NEVER the status
#     code: on clcloud.* 403 is the no-matching-route error and a 404 is never
#     emitted at all.
#   - Every candidate is a path already recorded on disk by the Area C pass.
#     No wordlist, no version neighbours added beyond the recorded set.
#
# Cap: 32 requests (16 per host). See run.log for the count actually used.

set -uo pipefail
DIR="findings-log/2026-10-12-pde-csr-cross-host"
OUT="$DIR/results.jsonl"
HDRDIR="$DIR/headers"
mkdir -p "$HDRDIR"
: > "$OUT"

HOST=""
n=0
per_host=0

req() {
  local method="$1" path="$2"
  per_host=$((per_host+1))
  n=$((n+1))
  local url="https://${HOST}/${path}"
  local slug="$(echo "$path" | tr '/.' '__')"
  local tag; tag="$(printf '%s-%02d' "$HOSTSUFFIX" "$per_host")"
  local hdrfile="$HDRDIR/${tag}-${method}-${slug}.hdr"
  local bodyfile="$HDRDIR/${tag}-${method}-${slug}.body"
  echo "[$n] $method https://${HOST}/${path}"
  # -s silent, -D dump headers, -o body, --compressed, no auth header, empty body
  curl -s -X "$method" --compressed -D "$hdrfile" -o "$bodyfile" --max-time 20 "$url"
  local status; status=$(head -1 "$hdrfile" | tr -d '\r')
  local ctype;     ctype=$(grep -i '^content-type:' "$hdrfile" | tr -d '\r' | head -1)
  local errtype;   errtype=$(grep -i '^x-amzn-errortype:' "$hdrfile" | tr -d '\r' | head -1)
  local caerr;     caerr=$(grep -i '^x-ca-err:' "$hdrfile" | tr -d '\r' | head -1)
  local acao;      acao=$(grep -i '^access-control-allow-origin:' "$hdrfile" | tr -d '\r' | head -1)
  local acam;      acam=$(grep -i '^access-control-allow-methods:' "$hdrfile" | tr -d '\r' | head -1)
  local bytes;     bytes=$(wc -c < "$bodyfile" | tr -d ' ')
  local bodyhead;  bodyhead=$(head -c 200 "$bodyfile" | tr -d '\r\n')
  python3 - "$n" "$HOST" "$method" "$path" "$status" "$ctype" "$errtype" "$caerr" "$acao" "$acam" "$bytes" "$bodyhead" >> "$OUT" <<'PY'
import json, sys
(n, host, method, path, status, ctype, errtype, caerr, acao, acam, bytes, bodyhead) = sys.argv[1:]
rec = {
    "n": int(n), "host": host, "method": method, "path": path,
    "status_line": status,
    "content_type": ctype or "(none)",
    "x_amzn_errortype": errtype or "(none)",
    "x_ca_err": caerr or "(none)",
    "acao": acao or "(none)",
    "acam": acam or "(none)",
    "bytes": int(bytes),
    "body_head": bodyhead,
}
print(json.dumps(rec))
PY
  echo "    $status | ${ctype:-content-type: (none)} | ${errtype:-x-amzn-errortype: (none)} | ${acao:-acao: (none)} | ${bytes}B"
  sleep 2.5
}

run_host() {
  HOST="$1"
  HOSTSUFFIX="$2"
  per_host=0
  echo "=== $HOST ==="
  # --- controls, FIRST: one certainly-live cell, one certainly-absent cell, both methods
  req GET    "connect/carepartner/v13/display/message"
  req GET    "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c"
  req OPTIONS "connect/carepartner/v13/display/message"
  req OPTIONS "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c"
  # --- the six recorded negative cells, GET + OPTIONS each (Area C rows 5-12, 13-14, 17-18)
  req GET     "connect/pde/v1/display/message"
  req OPTIONS "connect/pde/v1/display/message"
  req GET     "connect/pde/v2/display/message"
  req OPTIONS "connect/pde/v2/display/message"
  req GET     "connect/pde/v3/display/message"
  req OPTIONS "connect/pde/v3/display/message"
  req GET     "connect/pde/v3/discover/android/3.6"
  req OPTIONS "connect/pde/v3/discover/android/3.6"
  req GET     "connect/csr/v1/display/message"
  req OPTIONS "connect/csr/v1/display/message"
  req GET     "connect/csr/v3/display/message"
  req OPTIONS "connect/csr/v3/display/message"
}

run_host "clcloud.minimed.com"        "com"
run_host "clcloud-trials.minimed.com" "trials"

echo "DONE n=$n (cap 32)"