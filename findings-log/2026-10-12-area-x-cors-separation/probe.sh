#!/usr/bin/env bash
# Area X — why do the two clcloud.* route families differ in their CORS headers?
#
# HTTP discipline, method-identical to the Area B harness
# (2026-10-12-area-b-v12-routing/probe.sh), which in turn matches Area U and
# Area C:
#   - GET and OPTIONS with an EMPTY body. No POST, no token exchange, no auth.
#   - NO auth-ish headers at all: no Authorization, no Cookie, no x-api-key, not
#     even a dummy. curl sends none by default and this script adds none.
#   - >=2.5 s between requests to the SAME host (enforced by `sleep` in req()).
#   - Controls run FIRST on each host, before any data, so the oracle verdict is
#     not contaminated by the data it is being used to judge.
#   - Discriminator is x-amzn-errortype (+ the access-control-* header SET),
#     NEVER the status code: on clcloud.* 403 is the no-matching-route error and
#     a 404 is never emitted at all (docs/09-methodology-and-oracles.md §2).
#   - Every path is already recorded on disk by an earlier pass. No wordlist, no
#     invented version neighbours, no new hosts, no dev/stage hosts.
#
# WHAT THIS PASS ADDS. Two things Area B and every earlier pass did not do:
#
#   1. It asks the CORS question of a GET that ANSWERS 200. Area B's whole
#      confound was that "carries a preflight" and "answers 200" were the same
#      observation in the corpus. That is false on clcloud.*: four 200-status
#      heads on clcloud.* carry NO access-control-allow-origin
#      (2026-10-12-published-pointers/docs/disc-{eu-v13,com-v13,com-v11-legacy,
#      trials-v6-legacy}.hdr). So a 200 GET is a real CORS cell.
#
#      PROVENANCE WARNING -- those four heads are NOT in git.
#      2026-10-12-published-pointers/.gitignore lists docs/, because those bodies
#      carry credential-shaped values this repo deliberately does not publish. A
#      fresh clone holds 91 .hdr files, not 101, so the 24/14/10 split and the
#      4-of-10 finding CANNOT be re-derived from a clean checkout. What a clone
#      does hold is that pass's probe.sh:81-84, which carries the host
#      attribution -- the raw capture is not part of a walkable evidence chain.
#      Four heads across THREE hosts; clcloud.minimed.com carries two of them.
#
#   2. It sends an Origin header. NO capture in this repository ever
#      sent one (verified across every probe.sh / .hurl / .py harness), so the
#      archive cannot distinguish "this route has no preflight configured" from
#      "this gateway only emits ACAO when an Origin is present". That is the
#      one mechanism question this pass exists to answer, and it is capable of
#      REVERSING the offline conclusion.
#
# Origin is a request header, not a credential. The value is
# https://example.invalid — RFC 2606 reserved, guaranteed never to resolve, so
# no real third-party origin is involved. Access-Control-Request-Method is the
# other half of a browser preflight and is likewise not a credential.
#
# Cap: 26 requests. The plan below uses 24. See run.log for the count actually
# used; the harness refuses to run twice so the count cannot silently double.

set -uo pipefail
DIR="findings-log/2026-10-12-area-x-cors-separation"
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

CAP=26
ORIGIN_VALUE="https://example.invalid"
HOST=""
HOSTSUFFIX=""
n=0
per_host=0

# case-insensitive header fetch -> raw value after the first colon, CR stripped.
hdrval() { grep -i "^$2:" "$1" 2>/dev/null | tr -d '\r' | head -1 | sed "s/^[^:]*: *//"; }

# req <METHOD> <PATH> <NOTE> <ACRM>
#   ACRM is "" for a bare request, or "GET" / "POST" to send
#   Access-Control-Request-Method. Origin is sent iff $5 is non-empty, so the
#   two halves of a preflight travel together — a real preflight always has
#   both. Recorded per request in results.jsonl as `sent_headers`.
req() {
  local method="$1" path="$2" note="$3" acrm="$4"
  per_host=$((per_host+1))
  n=$((n+1))
  if [ "$n" -gt "$CAP" ]; then
    echo "CAP BREACH: refusing request $n (cap $CAP). STOP." | tee -a "$LOG" >&2
    exit 9
  fi
  local url="https://${HOST}/${path}"
  local slug; slug="$(echo "$path" | tr '/' '_')"
  local tag; tag="$(printf '%s-%02d' "$HOSTSUFFIX" "$per_host")"
  local mode="${acrm:-bare}"
  local hdrfile="$HDRDIR/${tag}-${method}-${slug}-${mode}.hdr"
  local bodyfile="$HDRDIR/${tag}-${method}-${slug}-${mode}.body"

  local -a extra=()
  local sent="(none)"
  if [ -n "$acrm" ]; then
    extra=( -H "Origin: ${ORIGIN_VALUE}" -H "Access-Control-Request-Method: ${acrm}" )
    sent="Origin:${ORIGIN_VALUE}|Access-Control-Request-Method:${acrm}"
  fi

  local ts; ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

  # -s silent, -D dump headers, -o body, --compressed, no auth header, empty body
  curl -s -X "$method" --compressed -D "$hdrfile" -o "$bodyfile" --max-time 20 \
       "${extra[@]}" "$url"
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
  local acamx;   acamx="$(hdrval "$hdrfile" 'access-control-max-age')"
  local vary;    vary="$(hdrval "$hdrfile" 'vary')"
  # Any CORS-family header at all, ANY case, unanchored. This is the §6-item-2
  # defence for the cells that report an ABSENCE: the discriminator is not a
  # tidy anchored grep for one header name, it is "did the gateway send
  # anything in this family on the wire".
  local acany;   acany="$(grep -ioE '^[[:space:]]*access-control-[a-z-]+' "$hdrfile" 2>/dev/null | tr -d '\r' | sed 's/^[[:space:]]*//' | sort -u | tr '\n' ',' | sed 's/,$//')"
  local bytes;   bytes="$(wc -c < "$bodyfile" 2>/dev/null | tr -d ' ')"
  [ -n "$bytes" ] || bytes=0
  # AWS API Gateway sometimes appends ":http://internal.amazon.com/coral/..."
  # to x-amzn-errortype. Keep BOTH the raw value and the type token before it.
  local et_tok;  et_tok="${et_raw%%:*}"
  local sha;     sha="$(sha256sum "$bodyfile" 2>/dev/null | awk '{print $1}')"
  [ -n "$sha" ] || sha="(no body file -- transport failure)"

  echo "[$ts] [$n] ${tag} ${method} ${url}"
  echo "    sent=${sent}"
  echo "    status=${http_status} curl_exit=${ec} | content-type=${ctype:- (none)}"
  echo "    x-amzn-errortype=${et_raw:- (none)} | x-ca-err=${caerr:- (none)}"
  echo "    acao=${acao:- (none)} | acam=${acam:- (none)} | acah=${acah:- (none)}"
  echo "    ac_family_seen=${acany:- (none)} | vary=${vary:- (none)}"
  echo "    bytes=${bytes} sha256=${sha}"

  # One human line per request, appended to run.log, timestamped.
  echo "[$ts] [$n] ${tag} ${method} https://${HOST}/${path} sent=${sent} -> ${http_status} curl_exit=${ec}${et_raw:+ | $et_raw}${caerr:+ | $caerr}${acao:+ | acao=$acao}${acam:+ | acam=$acam} | ${bytes}B | ${note}" >> "$LOG"

  python3 - "$n" "$per_host" "$HOST" "$HOSTSUFFIX" "$method" "$path" "$http_status" "$ec" \
    "$ctype" "$et_raw" "$et_tok" "$caerr" "$acao" "$acam" "$acah" "$acac" "$acamx" "$vary" "$acany" \
    "$bytes" "$sha" "$note" "$sent" \
    >> "$OUT" <<'PY'
import json, sys
(n, hseq, host, tag, method, path, status, ec, ctype, et_raw, et_tok,
 caerr, acao, acam, acah, acac, acamx, vary, acany, nbytes, sha, note, sent) = sys.argv[1:]
NONE = "(none)"
rec = {
    "seq": int(n),
    "host_seq": int(hseq),
    "host": host,
    "host_tag": tag,
    "method": method,
    "path": path,
    "role": note,
    "sent_headers": sent,
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
    "access_control_max_age": acamx or NONE,
    "vary": vary or NONE,
    "access_control_family_seen": acany or NONE,
    "body_bytes": int(nbytes),
    "body_sha256": sha,
}
print(json.dumps(rec))
PY

  sleep 2.5
}

# ---------------------------------------------------------------- Block 1
# clcloud.minimed.eu — the host area B's 3x2 was collected on, and the only host
# in the corpus with BOTH a public 200 GET (discover) and a 200+ACAO OPTIONS
# (display/message) recorded. Controls first.
HOST="clcloud.minimed.eu"; HOSTSUFFIX="eu"
echo "=== $HOST (cap $CAP) ===" | tee -a "$LOG"
req GET     "connect/carepartner/v13/display/message" "CONTROL-live-token-gated"  ""
req GET     "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c" "CONTROL-dead-fabricated-uuid" ""
req OPTIONS "connect/carepartner/v99/display/message" "CONTROL-dead-preflight-fabricated-version" ""
# --- the archive-unreachable cell: a 200 GET, asked for CORS, bare then with Origin
req GET     "connect/carepartner/v13/discover/android/3.6" "data-public-200-GET-bare"   ""
req GET     "connect/carepartner/v13/discover/android/3.6" "data-public-200-GET-with-origin" "GET"
req GET     "connect/carepartner/v13/discover/android/3.6" "data-public-200-GET-with-preflight-shape" "GET"
# --- the paired OPTIONS on the same route
req OPTIONS "connect/carepartner/v13/discover/android/3.6" "data-discover-OPTIONS-bare" ""
req OPTIONS "connect/carepartner/v13/discover/android/3.6" "data-discover-OPTIONS-with-preflight-shape" "GET"
# --- the contrast route: preflight present in the archive. Does it echo or widen?
req OPTIONS "connect/carepartner/v13/display/message" "data-display-OPTIONS-bare" ""
req OPTIONS "connect/carepartner/v13/display/message" "data-display-OPTIONS-preflight-GET" "GET"
req OPTIONS "connect/carepartner/v13/display/message" "data-display-OPTIONS-preflight-POST" "POST"
# --- does a token-gated 401 GET carry CORS when an Origin is present?
req GET     "connect/carepartner/v13/display/message" "data-token-gated-GET-with-origin" "GET"
# --- second public 200 route on .eu, so "a 200 GET lacks ACAO" rests on n=2 not n=1
req GET     "connect/carepartner/v11/discover/android/3.6" "data-public-200-GET-v11-bare" ""
req GET     "connect/carepartner/v11/discover/android/3.6" "data-public-200-GET-v11-with-origin" "GET"

# ---------------------------------------------------------------- Block 2
# Cross-host spot check on the .com sibling. Area X's own stated INFERRED
# assumption is that a .eu finding transfers to .com; this tests it rather than
# assuming it. Controls first — including the live control, because the likeliest
# outcome here is a negative and a 403 cannot be believed on a host whose own
# no-route signature has not been shown today.
HOST="clcloud.minimed.com"; HOSTSUFFIX="com"
echo "=== $HOST (cap $CAP) ===" | tee -a "$LOG"
req GET     "connect/carepartner/v13/display/message" "CONTROL-live-token-gated"  ""
req GET     "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c" "CONTROL-dead-fabricated-uuid" ""
req GET     "connect/carepartner/v13/discover/android/3.6" "data-public-200-GET-bare"   ""
req GET     "connect/carepartner/v13/discover/android/3.6" "data-public-200-GET-with-origin" "GET"
req OPTIONS "connect/carepartner/v13/discover/android/3.6" "data-discover-OPTIONS-bare" ""

# ---------------------------------------------------------------- Block 3
HOST="clcloud-trials.minimed.com"; HOSTSUFFIX="trials"
echo "=== $HOST (cap $CAP) ===" | tee -a "$LOG"
req GET     "connect/carepartner/v13/display/message" "CONTROL-live-token-gated"  ""
req GET     "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c" "CONTROL-dead-fabricated-uuid" ""
req GET     "connect/carepartner/v13/discover/android/3.6" "data-public-200-GET-bare"   ""
req GET     "connect/carepartner/v13/discover/android/3.6" "data-public-200-GET-with-origin" "GET"
req OPTIONS "connect/carepartner/v13/discover/android/3.6" "data-discover-OPTIONS-bare" ""

echo "DONE n=$n (cap $CAP)"