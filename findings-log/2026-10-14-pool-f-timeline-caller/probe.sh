#!/usr/bin/env bash
# probe.sh — area F ("what the timeline and dialog-lite gateways actually are"),
# pool run 2026-10-14, claim issue #123.
#
# WHAT THIS SENT, EXACTLY. The table below is the whole probe; nothing is
# generated, retried or re-ordered at run time.
#
#   GET only. No POST, no token exchange, no authentication, no dummy
#   api-key. 17 rows, a cap of 40. >=2.5 s between requests to the SAME host,
#   with the sleep INSIDE the host lock so two workers can never collide.
#
# CONTROLS FIRST PER HOST (claim #123): on every gateway, the published root
# is asked before any data cell, and the certainly-absent control UUID
# 9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6 (AWS-GATEWAYS.md:67-70) is asked
# immediately after it, so the "same envelope" reading is established in this
# ledger rather than cited from 2026-10-10.
#
# ORACLE (docs/09 §2, Oracle A), and it is NOT the same in both directions:
#   - x-amzn-errortype: MissingAuthenticationTokenException (403, 42 B) on
#     patient-timeline => NO MATCHING ROUTE. It can only ever confirm a
#     negative; it never confirms a route exists.
#   - x-amzn-errortype: InternalServerErrorException (500) on dialog-lite
#     => the path IS matched and the Lambda raised. It never means "exists"
#     in the ordinary sense and it is not a health signal.
# Status alone is never read as route evidence on either host.

set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1

LOGDIR="findings-log/2026-10-14-pool-f-timeline-caller"
# Bodies are transient (AGENTS.md section 7: no raw captures; and a 3.4 MB
# bundle would breach the 1 MiB per-file log limit), so they are written OUTSIDE
# the repository, to a scratch directory the caller chooses. No path is baked in
# here, because AGENTS.md section 7 forbids committing a machine-specific path.
SCRATCH="${SCRATCH:-$(mktemp -d)}"
mkdir -p "$SCRATCH"
printf 'scratch (bodies, transient, NOT committed): %s\n' "$SCRATCH" >&2
# The host locks live in the MAIN checkout's .loop/, because .loop/ does not
# exist inside a worktree. Derived from this script's own location rather than
# written out, for the same reason as above.
SELF_DIR="$(cd "$(dirname "$0")" && pwd -P)"
WORKTREE="$(cd "$SELF_DIR/../.." && pwd -P)"
case "$WORKTREE" in
  */.loop/worktrees/*) LOCKDIR="${WORKTREE%%/.loop/worktrees/*}/.loop" ;;
  *)                  LOCKDIR="$WORKTREE/.loop" ;;
esac
[ -d "$LOCKDIR" ] || { printf 'lock dir %s does not exist — refusing to send\n' "$LOCKDIR" >&2; exit 4; }
# .loop/ does not exist inside a worktree, so the locks are addressed
# absolutely, resolved from this script's own location (see LOCKDIR above).
LEDGER="$LOGDIR/results.jsonl"
RUNLOG="$LOGDIR/run.log"
CAP=40
LOCKD=2.5
UA="carelink-bridge-research/1.0"

mkdir -p "$LOGDIR/headers" "$SCRATCH"
: > "$LEDGER"
: > "$RUNLOG"

ts() { date -u +%FT%T.%3NZ; }

PT_EU="d4mwt26mmi.execute-api.eu-central-1.amazonaws.com"
PT_US="7r9xxd72kk.execute-api.us-east-1.amazonaws.com"
PT_TR="oflhmnvbe6.execute-api.us-east-1.amazonaws.com"
DL_EU="0ptoikank6.execute-api.eu-central-1.amazonaws.com"
DL_US="r5djbmetbb.execute-api.us-east-1.amazonaws.com"
ABS="9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6"   # certainly-absent control UUID

# tag  purpose  url
# shellcheck disable=SC2014
CELLS=(
  # A. the two portal bundles, anchored on the content-hashed asset name
  #    (not a document path: on this host family the catch-all IS the entry
  #    document -- area A, docs/00). The control is the sha256 anchor pair
  #    2a7fa8e7... / a054555a..., checked by grep.sh, not by this script.
  "bundle-clinic|corpus-clinic-bundle|https://carelink.medtronic.eu/main.fb5f8cb7eb60c4d5.js"
  "bundle-support|corpus-support-bundle|https://carelink-support.medtronic.com/main.759cddab23085086.js"
  # B. patient-timeline EU -- controls, then the BLOCK-7 cells that never ran
  #    (AWS-GATEWAYS.md:240-243).
  "pt-eu-root|control-plausible-root|https://$PT_EU/prod/patient-timeline/"
  "pt-eu-absent|control-certainly-absent-uuid|https://$PT_EU/prod/patient-timeline/$ABS"
  "pt-eu-v1root|block7-v1-prefix-root|https://$PT_EU/prod/patient-timeline/v1/"
  "pt-eu-v1events|block7-v1-events|https://$PT_EU/prod/patient-timeline/v1/events"
  "pt-eu-logbook|block7-logbook|https://$PT_EU/prod/patient-timeline/logbook"
  # C. patient-timeline US -- same two BLOCK-7 cells on the US deployment.
  "pt-us-root|control-plausible-root|https://$PT_US/prod/patient-timeline/"
  "pt-us-absent|control-certainly-absent-uuid|https://$PT_US/prod/patient-timeline/$ABS"
  "pt-us-v1events|block7-v1-events|https://$PT_US/prod/patient-timeline/v1/events"
  # D. patient-timeline trials -- same two BLOCK-7 cells on the trials deployment.
  "pt-tr-root|control-plausible-root|https://$PT_TR/prod/patient-timeline/"
  "pt-tr-absent|control-certainly-absent-uuid|https://$PT_TR/prod/patient-timeline/$ABS"
  "pt-tr-v1events|block7-v1-events|https://$PT_TR/prod/patient-timeline/v1/events"
  # E/F. dialog-lite, both deployments: the published root plus the paired
  #      certainly-absent control. 500-vs-403 on this family is the only
  #      POSITIVE route oracle in the whole area, and it is meaningless
  #      without the control sent in the same ledger.
  "dl-eu-root|control-plausible-root|https://$DL_EU/prodous/dialog-lite/v1/"
  "dl-eu-absent|control-certainly-absent-uuid|https://$DL_EU/prodous/$ABS"
  "dl-us-root|control-plausible-root|https://$DL_US/prod/dialog-lite/v1/"
  "dl-us-absent|control-certainly-absent-uuid|https://$DL_US/prod/$ABS"
)

SEQ=0
for cell in "${CELLS[@]}"; do
  tag="${cell%%|*}"; rest="${cell#*|}"; purpose="${rest%%|*}"; url="${rest#*|}"
  host="${url#*://}"; host="${host%%/*}"
  SEQ=$((SEQ + 1))
  if [ "$SEQ" -gt "$CAP" ]; then
    printf 'CAP REACHED at seq %s — refusing to send %s\n' "$SEQ" "$tag" >&2
    exit 3
  fi
  sn=$(printf '%03d' "$SEQ")
  hdr="$LOGDIR/headers/$sn-$tag.h"
  body="$SCRATCH/$sn-$tag.body"
  codef="$SCRATCH/$sn-$tag.code"
  tsf="$SCRATCH/$sn-$tag.ts"
  tq="$(ts)"
  # The sleep is INSIDE the lock, and t_sent is stamped immediately before
  # curl runs, so the >=2 s rule is checkable from the ledger alone.
  flock "$LOCKDIR/host-$host.lock" -c "
    sleep $LOCKD
    date -u +%FT%T.%3NZ > '$tsf'
    curl -sS --compressed --max-time 30 -A '$UA' -o '$body' -D '$hdr' -w '%{http_code}' '$url' > '$codef' 2>'$SCRATCH/$sn-$tag.err'
  "
  t_done="$(ts)"
  t_sent="$(cat "$tsf" 2>/dev/null)"
  code="$(tr -dc '0-9' < "$codef" 2>/dev/null)"
  bytes=0; [ -f "$body" ] && bytes=$(stat -c%s "$body")
  bsha="-"; [ -f "$body" ] && bsha=$(sha256sum "$body" | cut -c1-16)
  hval() { grep -i "^$1:" "$hdr" 2>/dev/null | head -1 | cut -d' ' -f2- | tr -d '\r'; }
  head_txt=""
  if [ -f "$body" ]; then head_txt="$(head -c 80 "$body" | tr -d '\r\n' | tr -c '[:print:]' '.')"; fi
  printf '%s\t%s\tGET\t%s\t%s\n' "$tq" "$t_sent" "$t_done" "$tag" >> "$RUNLOG"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$t_sent" "$t_done" "$host" "$url" "$code" "$(hval content-type)" \
    "$(hval x-amzn-errortype)" "$bytes" >> "$RUNLOG"
  # Plain assignments on their own statement, then the command. An assignment
  # PREFIX on a command is not visible to that command's own arguments under
  # `set -u`, so the two must not be the same simple command.
  SEQJ="$SEQ"; TAGJ="$tag"; PURPJ="$purpose"; HOSTJ="$host"; URLJ="$url"; CODEJ="$code"
  TQJ="$tq"; TSJ="$t_sent"; TDJ="$t_done"; BYTESJ="$bytes"; BSHAJ="$bsha"
  HEADJ="$head_txt"; HDRI="$hdr"
  CT="$(hval content-type)"; ET="$(hval x-amzn-errortype)"
  ACAO="$(hval access-control-allow-origin)"; ACAM="$(hval access-control-allow-methods)"
  ACAC="$(hval access-control-allow-credentials)"
  XCACHE="$(hval x-cache)"; ALLOW="$(hval allow)"; CLEN="$(hval content-length)"
  ENC="$(hval content-encoding)"; GWID="$(hval x-amz-apigw-id)"; REQID="$(hval x-amzn-requestid)"
  ERRJ="$(tr -d '\r\n' < "$SCRATCH/$sn-$tag.err" 2>/dev/null)"
  python3 - "$SEQJ" "$TAGJ" "$PURPJ" "$HOSTJ" "$URLJ" "$CODEJ" "$TQJ" "$TSJ" "$TDJ" \
      "$CT" "$ET" "$ACAO" "$ACAM" "$XCACHE" "$ALLOW" "$CLEN" "$ENC" "$GWID" "$REQID" \
      "$BYTESJ" "$BSHAJ" "$HEADJ" "$HDRI" "$ACAC" "$ERRJ" <<'PY' >> "$LEDGER"
import json, sys
(seq, tag, purpose, host, url, code, tq, ts, td, ct, et, acao, acam, xcache,
 allow, clen, enc, gwid, reqid, nbytes, bsha, bhead, hdr, acac, err) = sys.argv[1:26]
def d(s):
    return None if s in ('', 'None') else s
print(json.dumps({
    "seq": int(seq), "tag": tag, "purpose": purpose, "host": host,
    "url": url, "path": url.split('/', 3)[3] if url.count('/') > 2 else '/',
    "method": "GET", "status": d(code),
    "content_type": d(ct), "x_amzn_errortype": d(et),
    "access_control_allow_origin": d(acao),
    "access_control_allow_methods": d(acam),
    "access_control_allow_credentials": d(acac),
    "x_cache": d(xcache), "allow": d(allow),
    "content_length": d(clen), "content_encoding": d(enc),
    "x_amz_apigw_id": d(gwid), "x_amzn_requestid": d(reqid),
    "body_bytes": int(nbytes), "body_sha256_16": bsha, "body_head": bhead,
    "headers_file": hdr, "curl_stderr": d(err),
    "t_queued": tq, "t_sent": ts, "t_done": td,
}, sort_keys=False))
PY
  sleep 0.2
done

printf 'sent %s requests, cap %s\n' "$SEQ" "$CAP" >&2