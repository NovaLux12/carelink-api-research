#!/usr/bin/env bash
# Area B — the v11/v12/v13 routing picture under /connect/carepartner.
#
# Method-identical to the Area U harness (2026-10-12-pde-csr-cross-host/probe.sh)
# and the Area C harness (2026-10-11-pde-csr-oracle/probe.sh):
#   - GET and OPTIONS with an EMPTY body. No POST, no token exchange, no auth.
#   - NO auth-ish headers at all: no Authorization, no Cookie, no x-api-key, not
#     even a dummy. curl sends none by default and this script adds none.
#   - >=2.5 s between requests to the SAME host (enforced by `sleep` in req()).
#   - Controls run FIRST on each host, before any data, so the oracle verdict is
#     not contaminated by the data it is being used to judge.
#   - Discriminator is x-amzn-errortype (+ CORS on OPTIONS), NEVER the status
#     code: on clcloud.* 403 is the no-matching-route error and a 404 is never
#     emitted at all (docs/09-methodology-and-oracles.md section 2).
#   - Every path is already recorded on disk by an earlier pass. No wordlist, no
#     invented version neighbours, no new hosts, no dev/stage hosts.
#
# Cap: 24 requests. The plan below uses 17. See run.log for the count actually
# used; the harness refuses to run twice so the count cannot silently double.
#
# This pass also differs from Area U in one respect worth naming: it records
# `curl_exit` per request, which the Area U harness did not capture, and the
# sha256 of every body, so a transport failure can never be mistaken for a
# vendor answer.

set -uo pipefail
DIR="findings-log/2026-10-12-area-b-v12-routing"
OUT="$DIR/results.jsonl"
LOG="$DIR/run.log"
HDRDIR="$DIR/headers"

if [ -e "$OUT" ] || [ -e "$LOG" ]; then
  echo "REFUSING TO RUN: $OUT or $LOG already exists."
  echo "This directory is append-only. Move the previous run aside first;"
  echo "a silent second run would double the request count against the vendor."
  exit 1
fi

mkdir -p "$HDRDIR"
: > "$OUT"
: > "$LOG"

CAP=24
HOST=""
HOSTSUFFIX=""
n=0
per_host=0

# case-insensitive header fetch -> raw value after the first colon, CR stripped.
hdrval() { grep -i "^$2:" "$1" 2>/dev/null | tr -d '\r' | head -1 | sed "s/^[^:]*: *//"; }

req() {
  local method="$1" path="$2" note="$3"
  per_host=$((per_host+1))
  n=$((n+1))
  if [ "$n" -gt "$CAP" ]; then
    echo "CAP BREACH: refusing request $n (cap $CAP). STOP." | tee -a "$LOG" >&2
    exit 9
  fi
  local url="https://${HOST}/${path}"
  local slug; slug="$(echo "$path" | tr '/' '_')"
  local tag; tag="$(printf '%s-%02d' "$HOSTSUFFIX" "$per_host")"
  local hdrfile="$HDRDIR/${tag}-${method}-${slug}.hdr"
  local bodyfile="$HDRDIR/${tag}-${method}-${slug}.body"

  local ts; ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

  # -s silent, -D dump headers, -o body, --compressed, no auth header, empty body
  curl -s -X "$method" --compressed -D "$hdrfile" -o "$bodyfile" --max-time 20 "$url"
  local ec=$?

  # A non-zero curl exit means we may have no response head and no body at all.
  # That must read as a transport failure, never as a vendor answer, so the
  # files are materialised empty and the exit code is carried into results.jsonl.
  [ -f "$hdrfile" ] || : > "$hdrfile"
  [ -f "$bodyfile" ] || : > "$bodyfile"

  local status; status="$(head -1 "$hdrfile" 2>/dev/null | tr -d '\r')"
  [ -n "$status" ] || status="(no response head -- transport failure, curl_exit=$ec)"

  local http_status; http_status="$(echo "$status" | awk '{print $2}')"
  local ctype;  ctype="$(hdrval "$hdrfile" 'content-type')"
  local et_raw;  et_raw="$(hdrval "$hdrfile" 'x-amzn-errortype')"
  local caerr;   caerr="$(hdrval "$hdrfile" 'x-ca-err')"
  local acao;    acao="$(hdrval "$hdrfile" 'access-control-allow-origin')"
  local acam;    acam="$(hdrval "$hdrfile" 'access-control-allow-methods')"
  local acah;    acah="$(hdrval "$hdrfile" 'access-control-allow-headers')"
  local acac;    acac="$(hdrval "$hdrfile" 'access-control-allow-credentials')"
  local bytes;   bytes="$(wc -c < "$bodyfile" 2>/dev/null | tr -d ' ')"
  [ -n "$bytes" ] || bytes=0
  # AWS API Gateway sometimes appends ":http://internal.amazon.com/coral/..."
  # to x-amzn-errortype. Keep BOTH the raw value and the type token before it.
  local et_tok;  et_tok="${et_raw%%:*}"
  local sha;     sha="$(sha256sum "$bodyfile" 2>/dev/null | awk '{print $1}')"
  [ -n "$sha" ] || sha="(no body file -- transport failure)"

  echo "[$ts] [$n] ${tag} ${method} ${url}"
  echo "    status=${http_status} curl_exit=${ec} | content-type=${ctype:- (none)}"
  echo "    x-amzn-errortype=${et_raw:- (none)} | x-ca-err=${caerr:- (none)}"
  echo "    acao=${acao:- (none)} | acam=${acam:- (none)} | acah=${acah:- (none)}"
  echo "    bytes=${bytes} sha256=${sha}"

  # One human line per request, appended to run.log, timestamped. This is the
  # durable per-request record; the block above is the console echo.
  echo "[$ts] [$n] ${tag} ${method} https://${HOST}/${path} -> ${http_status} curl_exit=${ec}${et_raw:+ | $et_raw}${caerr:+ | $caerr}${acao:+ | acao=$acao}${acam:+ | acam=$acam} | ${bytes}B | ${note}" >> "$LOG"

  python3 - "$n" "$per_host" "$HOST" "$HOSTSUFFIX" "$method" "$path" "$http_status" "$ec" \
    "$ctype" "$et_raw" "$et_tok" "$caerr" "$acao" "$acam" "$acah" "$acac" "$bytes" "$sha" "$note" \
    >> "$OUT" <<'PY'
import json, sys
(n, hseq, host, tag, method, path, status, ec, ctype, et_raw, et_tok,
 caerr, acao, acam, acah, acac, nbytes, sha, note) = sys.argv[1:]
NONE = "(none)"
rec = {
    "seq": int(n),
    "host_seq": int(hseq),
    "host": host,
    "host_tag": tag,
    "method": method,
    "path": path,
    "role": note,
    "http_status": status,
    "curl_exit": int(ec),
    "content_type": ctype or NONE,
    "x_amzn_errortype": et_raw or NONE,
    "x_amzn_errortype_token": et_tok or NONE,
    "x_ca_err": caerr or NONE,
    "access_control_allow_origin": acao or NONE,
    "access_control_allow_methods": acam or NONE,
    "access_control_allow_headers": acah or NONE,
    "access_control_allow_credentials": acac or NONE,
    "body_bytes": int(nbytes),
    "body_sha256": sha,
}
print(json.dumps(rec))
PY

  sleep 2.5
}

# ---------------------------------------------------------------- Block 1
HOST="clcloud.minimed.eu"; HOSTSUFFIX="eu"
echo "=== $HOST (cap $CAP) ===" | tee -a "$LOG"
# controls FIRST, before any data
req GET    "connect/carepartner/v13/display/message" "CONTROL-live"
req GET    "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c" "CONTROL-dead-fabricated-uuid"
req OPTIONS "connect/carepartner/v13/display/message" "CONTROL-live-preflight"
req OPTIONS "connect/carepartner/v99/display/message" "CONTROL-dead-preflight-fabricated-version"
# data
req GET     "connect/carepartner/v11/display/message" "data-v11-GET"
req GET     "connect/carepartner/v12/display/message" "data-v12-GET"
req OPTIONS "connect/carepartner/v11/display/message" "data-v11-OPTIONS"
req OPTIONS "connect/carepartner/v12/display/message" "data-v12-OPTIONS"
req OPTIONS "connect/carepartner/v13/discover/android/3.6" "data-v13-discover-OPTIONS"
req OPTIONS "connect/carepartner/v11/discover/android/3.6" "data-v11-discover-OPTIONS"
req OPTIONS "connect/carepartner/v12/discover/android/3.6" "data-v12-discover-OPTIONS"

# ---------------------------------------------------------------- Block 2
HOST="clcloud.minimed.com"; HOSTSUFFIX="com"
echo "=== $HOST (cap $CAP) ===" | tee -a "$LOG"
req GET     "connect/carepartner/v13/display/message" "CONTROL-live"
req GET     "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c" "CONTROL-dead-fabricated-uuid"
req GET     "connect/carepartner/v12/display/message" "data-v12-GET"

# ---------------------------------------------------------------- Block 3
HOST="clcloud-trials.minimed.com"; HOSTSUFFIX="trials"
echo "=== $HOST (cap $CAP) ===" | tee -a "$LOG"
req GET     "connect/carepartner/v13/display/message" "CONTROL-live"
req GET     "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c" "CONTROL-dead-fabricated-uuid"
req GET     "connect/carepartner/v12/display/message" "data-v12-GET"

echo "DONE n=$n (cap $CAP)"
