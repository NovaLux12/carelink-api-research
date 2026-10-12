#!/usr/bin/env bash
# Area Z — does any clcloud.* route REFLECT Origin, or is ACAO a fixed "*"?
#
# HTTP discipline, method-identical to the Area X harness (which matches B, U, N, C):
#   - OPTIONS with an EMPTY body for every data cell; GET (empty body) for controls.
#     No POST, no token exchange, no authentication, no port scan.
#   - NO auth-ish headers at all: no Authorization, no Cookie, no x-api-key, not
#     even a dummy. curl sends none by default and this script adds none.
#   - >=2.5 s between requests to the SAME host (enforced by `sleep` in req()).
#     The repository rule is >=2 s.
#   - Controls run FIRST on each host, before any data cell, so the oracle verdict
#     is not contaminated by the data it is being used to judge.
#   - Discriminator is x-amzn-errortype (+ the access-control-* header SET), NEVER
#     the status code: on clcloud.* 403 is the no-matching-route error and a 404 is
#     never emitted at all (docs/09-methodology-and-oracles.md §2).
#   - Every path is already recorded on disk by an earlier pass. No wordlist, no
#     invented version neighbours, no new hosts, no dev/stage hosts.
#
# WHAT THIS PASS ADDS. Area X sent ONE Origin (https://example.invalid) and could
# therefore not separate an ECHO from a CONSTANT: a fixed "*" and a reflected origin
# look identical under one value. Two distinct Origin values are the minimum that
# distinguishes them, and that is this pass's whole discriminating test.
#
# DELIBERATE DEPARTURE FROM AREA X. Area X always sent Origin and
# Access-Control-Request-Method together ("the two halves of a preflight travel
# together"). This pass sends Origin ALONE, so that Origin is the only variable.
# Coupling them here would confound area Z's question with area X's already-settled
# ACRM question. The cost, recorded rather than hidden: a real browser preflight
# always carries both, so every Origin cell here is synthetic, and the
# ACRM x Origin INTERACTION is not tested by this pass. See FINDINGS.md §Assumptions.
#
# LEDGER SCHEMA. This pass writes an explicit `host` key and an explicit key for
# every CORS header, with the literal "(none)" when absent, PLUS `ctype_full`
# (the raw head string). It does that because the existing corpus stores the same
# header four different ways across five ledgers, and a query written against one
# convention silently under-reports -- measured at 2 cells vs the true 12. See
# FINDINGS.md §6. Self-describing rows are the cheap half of fixing that.
#
# Cap: 60 requests. The plan below uses 51. See run.log for the count actually
# used; the harness refuses to run twice so the count cannot silently double.

set -uo pipefail
DIR="findings-log/2026-10-12-area-z-origin-reflection"
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

CAP=60
# Two RFC 2606 reserved names: guaranteed never to resolve, so no real third-party
# origin is involved. A is the literal Area X used, so the two passes are
# comparable; B exists only to be DIFFERENT from A, which is the whole test.
ORIGIN_A="https://example.invalid"
ORIGIN_B="https://probe-two.invalid"
HOST=""
HOSTSUFFIX=""
n=0
per_host=0

# case-insensitive header fetch -> raw value after the first colon, CR stripped.
hdrval() { grep -i "^$2:" "$1" 2>/dev/null | tr -d '\r' | head -1 | sed "s/^[^:]*: *//"; }

# req <METHOD> <PATH> <NOTE> <ORIGIN>
#   ORIGIN is "" for a bare request, or an origin literal to send as `Origin`.
req() {
  local method="$1" path="$2" note="$3" origin="$4"
  per_host=$((per_host+1))
  n=$((n+1))
  if [ "$n" -gt "$CAP" ]; then
    echo "CAP BREACH: refusing request $n (cap $CAP). STOP." | tee -a "$LOG" >&2
    exit 9
  fi
  local url="https://${HOST}/${path}"
  local slug; slug="$(echo "$path" | tr '/' '_')"
  local tag; tag="$(printf '%s-%02d' "$HOSTSUFFIX" "$per_host")"
  local mode="bare"
  [ -n "$origin" ] && mode="$(echo "$origin" | sed 's#https://##; s#[./]#-#g')"
  local hdrfile="$HDRDIR/${tag}-${method}-${slug}-${mode}.hdr"
  local bodyfile="$HDRDIR/${tag}-${method}-${slug}-${mode}.body"

  local -a extra=()
  local sent="(none)"
  if [ -n "$origin" ]; then
    extra=( -H "Origin: ${origin}" )
    sent="Origin:${origin}"
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
  # The raw head, newline->" | ". Kept so header ORDER and the full CORS family are
  # re-derivable without re-parsing a lossy summary.
  local chead;   chead="$(tr -d '\r' < "$hdrfile" | tail -n +2 | sed '/^[[:space:]]*$/d' | tr '\n' '|' | sed 's/|$//')"
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
    "$ctype" "$et_raw" "$et_tok" "$caerr" "$acao" "$acam" "$acah" "$acac" "$acamx" "$vary" "$acany" "$chead" \
    "$bytes" "$sha" "$note" "$sent" \
    >> "$OUT" <<'PY'
import json, sys
(n, hseq, host, tag, method, path, status, ec, ctype, et_raw, et_tok,
 caerr, acao, acam, acah, acac, acamx, vary, acany, chead, nbytes, sha, note, sent) = sys.argv[1:]
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
    "acao": acao or NONE,
    "acam": acam or NONE,
    "acah": acah or NONE,
    "acac": acac or NONE,
    "acamx": acamx or NONE,
    "vary": vary or NONE,
    "ac_family_seen": acany or NONE,
    "ctype_full": chead or NONE,
    "body_bytes": int(nbytes),
    "body_sha256": sha,
}
print(json.dumps(rec))
PY

  sleep 2.5
}

# ---------------------------------------------------------------------------
# The grid. 5 route families x 3 conditions (bare / Origin A / Origin B).
# Sent as bare, A, B in that order per route so a reader can read the block
# top-to-bottom and see the comparison without cross-referencing.
# ---------------------------------------------------------------------------
grid() {
  local path="$1" tag="$2"
  req OPTIONS "$path" "data-${tag}-bare"       ""
  req OPTIONS "$path" "data-${tag}-origin-A"   "$ORIGIN_A"
  req OPTIONS "$path" "data-${tag}-origin-B"   "$ORIGIN_B"
}

for HOST in "clcloud.minimed.eu|eu" "clcloud.minimed.com|com" "clcloud-trials.minimed.com|trials"; do
  HOST="${HOST%%|*}"; HOSTSUFFIX="${HOST##*|}"
  echo "=== $HOST (cap $CAP) ===" | tee -a "$LOG"

  # ---- Controls FIRST, bare, on every host. Not Origin-bearing: the oracle must
  # not be contaminated by the variable this pass is testing.
  # C1 proves the token-gated signature (route exists, authorizer reachable).
  # C2 proves the no-route signature -- the only thing that makes a 403 readable
  # as "dead" on a host where 404 is never emitted.
  req GET     "connect/carepartner/v13/display/message" "CONTROL-live-token-gated" ""
  req GET     "connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c" "CONTROL-dead-fabricated-uuid" ""

  # v13 -- the only route family with a recorded ACAO value on all three hosts.
  grid "connect/carepartner/v13/display/message" "v13-display-message"
  # csr/v2 -- recorded ACAM "OPTIONS,POST": already differs from the literal OPTIONS.
  grid "connect/csr/v2/display/message" "csr-v2-display-message"
  # bare v2 -- recorded ACAM "POST,OPTIONS": same method SET as csr/v2, different ORDER.
  grid "connect/v2/display/message" "bare-v2-display-message"
  # v12 -- Area B's version-axis evidence is .eu-only; the siblings are unrecorded.
  grid "connect/carepartner/v12/display/message" "v12-display-message"
  # v6 -- the vendor's OWN published blePereodicDataEndpoint, and the one route
  # with no ACAO value recorded anywhere in the repository.
  grid "connect/carepartner/v6/display/message" "v6-display-message"
done

echo "DONE n=$n (cap $CAP)"