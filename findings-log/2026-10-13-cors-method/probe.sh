#!/usr/bin/env bash
# probe.sh — is ACAO on the commoncore* hosts method-conditional?
#
# Correction issue #61, method half. See FINDINGS.md in this directory.
#
# Accounting, declared before the first request:
#   CAP      8 HTTP requests. GET and empty-body OPTIONS only. No POST.
#   DELAY    2.5 s, slept INSIDE the per-host flock lock.
#   HOSTS    commoncore-trials.medtronic.com, commoncore.medtronic.com.
#   CELLS    per host, controls first:
#              A  GET    /reports-broker/v1/ocl                 positive control (recorded path)
#              B  GET    /reports-broker/v1/ocl-probe-absent   certainly-absent control
#              C  OPTIONS /reports-broker/v1/ocl-probe-absent   the cell the question turns on
#              D  OPTIONS /reports-broker/v1/ocl                completes the path x method matrix
#
# The OPTIONS requests carry an EMPTY body: no -d, no --data, no data on stdin.
# No Origin header is sent in any cell — the six captures this pass follows carry none,
# and matching that is part of the point.
#
# The two candidate paths are the ones already on disk in the 2026-10-13 commoncore-trials
# pass. No new candidates were invented and nothing was fuzzed.
#
# Ledger: one results.jsonl row per invocation, three timestamps each (t_queued, t_sent,
# t_done) at millisecond UTC ISO-8601, plus the kernel body mtime as the independent
# spacing series (docs/09 section 4: the harness `date` series is the suspect in five passes).
# The ledger is APPENDED to, never truncated: a failed invocation is a row too, because the
# ledger rule is one row per request whatever issued it.
#
# Usage:  LOOP=<shared .loop dir> [ATTEMPT=<n>] bash probe.sh
# The gate scans .sh files, so no absolute machine path appears here; LOOP comes from
# the environment.
#
# ---------------------------------------------------------------------------
# CORRECTION (2026-10-13) — attempts 1 and 2 sent nothing, and this harness is why.
#
# Attempt 1 called `out` with six arguments while `out` takes five, so the values were
# shifted by one and the method word landed in the URL: curl was handed
# `https://commoncore-trials.medtronic.comGET` and `...comOPTIONS`, a real vendor name
# with a method word glued to it. Every invocation returned `curl_exit 6` ("could not
# resolve host") and `http_status 000`, and wrote 0-byte header, sent-header and body
# captures. Name resolution failed, so no TCP or TLS handshake was attempted and no HTTP
# request reached any vendor host; `attempt1-exit6-demo.txt` reproduces that failure path
# offline against a reserved `.invalid` name, where the absence of a `Trying <ip>:443...`
# line is visible. Attempt 2 repeated the defect and cost the same, because the fix had
# been applied to the function's parameter list and not to the eight call sites. **16
# invocations, 16 resolver queries for four non-existent names, 0 vendor HTTP requests** —
# so the declared 8-request cap was never reached. All 16 rows are kept in `results.jsonl`
# with the shift visible in their own `method`, `path` and `url` fields; they are evidence
# of the defect, not of the vendor.
#
# Three changes make the same class of defect unable to reach the network or the ledger:
#   1. `out` refuses any method that is not GET or OPTIONS, and any path that does not
#      begin with `/`. Either aborts before the first request.
#   2. The capture filename carries the cell label, so an argument shift shows up in the
#      filenames rather than in a malformed URL.
#   3. `curl_error_line` and `curl_connected_line` are recorded fields, and every ledger row
#      is assembled with `json.dumps` and then **read back and parsed before it is written**.
#      Attempts 1 and 2 each shipped rows that were not valid JSON — a duplicated `seq` key,
#      then an unquoted one — and nothing read the file back, so nothing noticed. That is
#      the same shape as docs/09's "a check that looks like it ran is worse than no check".
#
# CORRECTION (2026-10-13, verification round of PR #65) "positive control" was
# never a control.
#
# Cell A was labelled CONTROL-A-positive-recorded-path. It is not a positive control: it
# returns the same status, the same headers and the same body digest as the absence control,
# so it cannot discriminate from its own negative and it is a repeat of the negative rather
# than a control over it. The reasoning that made it look like one was circular -- it proved
# the 8 cells byte-identical to each other, then cited that identity as the control passing.
# The role string above is now RECORDED-PATH-not-a-control. **results.jsonl is deliberately
# NOT rewritten**: it is the record of what was sent and recorded, and the retraction history
# is the evidence. Its seq 17 and seq 21 rows still read CONTROL-A-positive-recorded-path and
# that is intentional -- FINDINGS.md 2.1 and 3.2 carry the correction.
#
# The same round retracted a second claim this harness encoded in its shape: that a
# full path x method square per host was worth 4 requests per host. That part still holds,
# but the justification attached to it (mandatory controls) did not, and FINDINGS.md 5.2 now
# records it as a trade rather than a rule.
#
# The harness was validated end-to-end before attempt 3 with `DRYRUN=1` against names under
# the reserved `.invalid` TLD: zero vendor traffic, and it is what caught defect 3.
# ---------------------------------------------------------------------------
set -euo pipefail

LOG="$(cd "$(dirname "$0")" && pwd)"
: "${LOOP:?set LOOP to the shared .loop directory}"
DELAY=2.5
UA='carelink-bridge-research/1.0'
CAP=8
ATTEMPT="${ATTEMPT:-1}"
SEQ=0
[ -f "$LOG/results.jsonl" ] && SEQ="$(wc -l < "$LOG/results.jsonl" | tr -d ' ')"

REC="$PWD/records"          # scratch, never committed, removed on exit
mkdir -p "$LOG/headers" "$LOG/bodies" "$REC"
V="$(mktemp "${TMPDIR:-/tmp}/corsmethod.XXXXXX")"
trap 'rm -f "$V"; rm -rf "$REC"' EXIT

now() { date -u +%FT%T.%3NZ; }
kv()  { printf '%s\t%s\n' "$1" "$2" >> "$REC/$KVS"; }   # TAB-separated: json.dumps escapes it

# out HOST CELL METHOD PATH ROLE
#
# CELL is the cell's own label (A-ocl-GET …) and names the capture files.
out() {
  local host="$1" cell="$2" method="$3" path="$4" role="$5"

  case "$method" in
    GET|OPTIONS) ;;
    *) echo "ABORT: method '$method' is not GET or OPTIONS — refusing to send" >&2; exit 2 ;;
  esac
  case "$path" in
    /*) ;;
    *) echo "ABORT: path '$path' does not begin with / — refusing to send" >&2; exit 2 ;;
  esac

  SEQ=$((SEQ + 1))
  local n; n="$(printf '%02d' "$SEQ")"
  local tag; tag="$(printf '%s' "$host" | cut -d. -f1)-$(printf '%s' "$cell" | tr 'A-Z' 'a-z')"
  local h="$LOG/headers/$n-$tag.h" b="$LOG/bodies/$n-$tag.b"
  local s="$LOG/headers/$n-$tag.sent.h" r="$REC/$n-$tag"
  KVS="$n-$tag.kv"; : > "$REC/$KVS"
  : > "$h"; : > "$b"; : > "$s"    # curl creates none of these on a connect/TLS failure

  local tq ts td code cexit upload sent_hdrs errline connected
  tq="$(now)"
  (
    set +e                      # a curl failure must still write its own row
    flock -x 9
    sleep "$DELAY"
    now > "$r.t_sent"
    if [ "$method" = OPTIONS ]; then
      # empty body: -X only. No -d, no --data, no data on stdin.
      curl -sS --compressed -v -X OPTIONS -A "$UA" \
        --connect-timeout 10 --max-time 40 \
        -o "$b" -D "$h" -w '%{http_code}' \
        "https://$host$path" > "$r.status" 2>"$r.v"
    else
      curl -sS --compressed -v -A "$UA" \
        --connect-timeout 10 --max-time 40 \
        -o "$b" -D "$h" -w '%{http_code}' \
        "https://$host$path" > "$r.status" 2>"$r.v"
    fi
    echo $? > "$r.exit"
    now > "$r.t_done"
  ) 9>"$LOOP/host-$host.lock"

  cexit="$(cat "$r.exit")"; code="$(cat "$r.status")"
  ts="$(cat "$r.t_sent")";    td="$(cat "$r.t_done")"

  # The request as sent, verbatim: curl's own "> " verbose block. Only those lines are
  # kept — the verbose stream also carries the local socket address, which has no business
  # in a research log.
  sed -n 's/^> //p' "$r.v" > "$s"
  errline="$(grep -m1 '^curl: ' "$r.v" || true)"
  upload="$(grep -m1 -e '^\* no upload' -e '^\* upload' "$r.v" || true)"
  connected="$(grep -c 'Connected to' "$r.v" || true)"
  sent_hdrs="$(grep -iv '^user-agent:' "$s" | paste -sd'; ' - || true)"
  sent_hdrs="User-Agent: $UA${sent_hdrs:+; ${sent_hdrs}}"

  kv seq "$SEQ"
  kv attempt "$ATTEMPT"
  kv host "$host"
  kv host_tag "$tag"
  kv cell "$cell"
  kv method "$method"
  kv path "$path"
  kv role "$role"
  kv url "https://$host$path"
  kv sent_headers "$sent_hdrs"
  kv sent_request_line "$(head -1 "$s")"
  kv sent_origin_header "$(grep -ic '^origin:' "$s" || true) line(s) in the sent request"
  kv sent_body "EMPTY on OPTIONS (-X only, no -d, no data); no body on GET"
  kv curl_upload_line "${upload:-<none emitted>}"
  kv curl_connected_line "${connected} verbose line(s) reading 'Connected to'"
  kv curl_error_line "${errline:-<none>}"
  kv delay_declared_s "$DELAY"
  kv t_queued "$tq"
  kv t_sent "$ts"
  kv t_sent_note "recorded immediately before curl was invoked; the true departure lies between t_sent and t_done"
  kv t_done "$td"
  kv http_status "${code:-000}"
  kv curl_exit "$cexit"
  kv content_type "$(grep -im1 '^content-type:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv x_amzn_errortype "$(grep -im1 '^x-amzn-errortype:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv x_ca_err "$(grep -im1 '^x-ca-err:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv access_control_allow_origin "$(grep -im1 '^access-control-allow-origin:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv access_control_allow_methods "$(grep -im1 '^access-control-allow-methods:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv access_control_allow_headers "$(grep -im1 '^access-control-allow-headers:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv access_control_allow_credentials "$(grep -im1 '^access-control-allow-credentials:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv allow "$(grep -im1 '^allow:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv vary "$(grep -im1 '^vary:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv content_encoding "$(grep -im1 '^content-encoding:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv server "$(grep -im1 '^server:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv x_cache "$(grep -im1 '^x-cache:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv via "$(grep -im1 '^via:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv response_cors_header_count "$(grep -ic '^access-control-' "$h" || true)"
  kv body_bytes "$(wc -c < "$b" | tr -d ' ')"
  kv body_sha256 "$(sha256sum "$b" | cut -d' ' -f1)"
  kv body_mtime_epoch "$(stat -c %Y "$b")"
  kv body_mtime_iso "$(date -u -d "@$(stat -c %Y "$b")" +%FT%T.%3NZ)"
  kv body_head256 "$(head -c 256 "$b" | tr -d '\0' | tr '\n' ' ' | cut -c1-256)"

  python3 - "$REC/$KVS" "$LOG/results.jsonl" <<'PY'
import json, sys
kvf, dest = sys.argv[1], sys.argv[2]
d, order = {}, []
for line in open(kvf):
    line = line.rstrip("\n")
    if "\t" in line:
        k, v = line.split("\t", 1)
        if k not in d:
            order.append(k)
        d[k] = v
row = json.dumps({k: d[k] for k in order})
json.loads(row)          # read-back: a row that cannot be parsed never reaches the ledger
with open(dest, "a") as f:
    f.write(row + "\n")
PY

  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$SEQ" "$host" "$method" "$path" "$tq" "$ts" "$td" >> "$LOG/run.log"
  printf '[%s] %-7s %-5s %-30s -> %s\n' "$host" "$method" "$code" "$path" "$ts"
}

echo "cap $CAP HTTP requests · delay ${DELAY}s · GET and empty-body OPTIONS only · no Origin · attempt $ATTEMPT"

# H1/H2 may be overridden ONLY for a dry run, and only with DRYRUN=1. A dry run costs zero
# vendor traffic: it exercises the guards, the capture naming, the ledger assembly and the
# read-back against a name under .invalid (RFC 2606, reserved, cannot resolve).
H1="${H1:-commoncore-trials.medtronic.com}"
H2="${H2:-commoncore.medtronic.com}"
if [ "$H1" != commoncore-trials.medtronic.com ] || [ "$H2" != commoncore.medtronic.com ]; then
  [ "${DRYRUN:-}" = 1 ] || { echo "ABORT: host override requires DRYRUN=1" >&2; exit 2; }
  echo "DRY RUN — hosts overridden, zero vendor traffic expected: $H1 $H2"
fi

# ---- host 1: commoncore-trials.medtronic.com --------------------------------
out "$H1" A-ocl-GET        GET     /reports-broker/v1/ocl               RECORDED-PATH-not-a-control
out "$H1" B-absent-GET     GET     /reports-broker/v1/ocl-probe-absent CONTROL-B-certainly-absent
out "$H1" C-absent-OPTIONS OPTIONS /reports-broker/v1/ocl-probe-absent CONTROL-C-the-deciding-cell
out "$H1" D-ocl-OPTIONS    OPTIONS /reports-broker/v1/ocl               MATCHED-PAIR-completes-the-matrix

# ---- host 2: commoncore.medtronic.com --------------------------------------
out "$H2" A-ocl-GET        GET     /reports-broker/v1/ocl               RECORDED-PATH-not-a-control
out "$H2" B-absent-GET     GET     /reports-broker/v1/ocl-probe-absent CONTROL-B-certainly-absent
out "$H2" C-absent-OPTIONS OPTIONS /reports-broker/v1/ocl-probe-absent CONTROL-C-the-deciding-cell
out "$H2" D-ocl-OPTIONS    OPTIONS /reports-broker/v1/ocl               MATCHED-PAIR-completes-the-matrix

echo "8 invocations · vendor HTTP requests sent in attempt $ATTEMPT: 8 · cap $CAP"