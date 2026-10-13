#!/usr/bin/env bash
# Area Q — the appVersion BODY gate: a second version axis.
#
# SCOPE (claim issue #43). This is a STATIC pass over third-party source
# repositories, not a probe of Medtronic's surface.
#
#   ZERO requests to any Medtronic / MiniMed / Abbott host, by design. The only
#   way to settle a body-field gate is a POST carrying an appVersion body, which
#   AGENTS.md section 11 forbids outside the two already-pinned public-client_id
#   requests; no automation may extend that exception. A GET cannot reach a body
#   field. So the boundary values are NOT obtainable here by construction, and
#   the area's second close condition ("recorded as community-reported-and-
#   unverifiable, with the reason") applies.
#
# HOSTS: api.github.com (18 requests planned) and raw.githubusercontent.com (1).
# raw.githubusercontent is used ONCE, as an independent byte-level cross-check on
# one api.github.com contents response, so that a silent empty or truncated
# payload cannot be mistaken for agreement.
#
# SUBJECTS (all named in findings-log/2026-10-11-third-party-client-sources/
# FINDINGS.md, which is what produced this area's claim):
#   NightscoutFoundation/xDrip            @ 366c97a8 (source pass, 2026-10-10)
#   CarlosJPV/carelink-cumulus-bridge     @ 0180b89 (source pass, 2026-08-26)
#
# METHOD: GET only. No POST, no token exchange, no authentication. The
# api.github.com calls are UNAUTHENTICATED on purpose (no Authorization header,
# no gh token) so no credential is in the request path at all; 17 requests is
# well inside the 60/hour unauthenticated limit.
#
# CONTROLS, and why each exists:
#   C1  Certainly-absent REF at a plausible path. Establishes that a 404 on
#       this host family means "did not resolve" and is not a universal success.
#   C2  Certainly-absent PATH at a valid ref. Distinguishes bad-ref from
#       bad-path, which a bare status code cannot.
#   C3  Every subject file is fetched TWICE: at its PINNED COMMIT and at BRANCH
#       HEAD. The git blob `sha` the API returns is the oracle — equal blob SHAs
#       mean byte-identical content, so a cited file:line either resolves at both
#       or it has drifted. No eyeballing.
#   C4  raw.githubusercontent.com re-fetch of one file, sha256-compared against
#       the base64 the contents API returned. A payload that silently resolved
#       to null has been what made two different values hash identically here
#       before (docs/09 section 5 item 3).
#
# TIMESTAMPS are millisecond ISO-8601 UTC (date -u +%FT%T.%3NZ), three per row:
# t_queued (before the host lock), t_sent (inside the lock, after the sleep,
# immediately before curl) and t_done (after curl). The spacing rule is a rule
# about SENDS, so it is measured from t_sent.
#
# SPACING ORACLE: curl -o bodies/NN.b makes the KERNEL set each body's mtime at
# write time. That series is independent of this harness's clock, which docs/09
# section 4 records as the suspect instrument (four passes recorded impossible
# negative durations). Both series are recorded; spacing.txt computes from the
# mtimes and validates the series by comparing its span against the harness span.
#
# Per-host serialisation: sleep 2.5 s INSIDE the per-host flock. Three other pool
# workers share this machine; a sleep outside the lock would let queued workers
# fire simultaneously and make the spacing claim merely intended.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE"
CAP=20
DELAY=2.5
SEQ=0

# Locate the pool .loop directory (shared per-host lock files) by walking up to
# the copy of BRIEF.md rather than hard-coding it. A literal machine path in this
# file is a leak (area I's gate finding).
LOCKS=""
d="$HERE"
while [ "$d" != "/" ]; do
  if [ -f "$d/.loop/BRIEF.md" ]; then LOCKS="$d/.loop"; break; fi
  d="$(dirname "$d")"
done
: "${LOCKS:?could not locate the pool .loop directory}"

mkdir -p "$OUT/headers" "$OUT/bodies" "$OUT/ts"

XD_CARE="app/src/main/java/com/eveningoutpost/dexdrip/cgm/carelinkfollow/CareLinkClient.java"
CJ_CUMULUS="src/carelink/cumulus.ts"
CJ_PROBE="src/probe-appversion.ts"
CJ_README="README.md"
CJ_GITIGNORE=".gitignore"
XD_PIN="366c97a8"
CJ_PIN="0180b89"

log() { echo "$*" >> "$OUT/run.log"; }

req() { # req <host> <path> <role> <tag>
  local host="$1" path="$2" role="$3" tag="$4"
  SEQ=$((SEQ+1))
  if [ "$SEQ" -gt "$CAP" ]; then
    log "seq=$SEQ ABORTED cap $CAP reached before $host$path"
    return 1
  fi
  touch "$LOCKS/host-$host.lock"
  local url="https://$host$path"
  local t_queued; t_queued=$(date -u +%FT%T.%3NZ)
  flock "$LOCKS/host-$host.lock" -c "
    sleep $DELAY
    date -u +%FT%T.%3NZ > '$OUT/ts/$tag.sent'
    curl -sS --compressed \
      -H 'Accept: application/vnd.github+json' \
      -H 'User-Agent: carelink-api-research-static-audit' \
      -D '$OUT/headers/$tag.h' -o '$OUT/bodies/$tag.b' \
      -w '%{http_code}' '$url' > '$OUT/ts/$tag.code' 2>'$OUT/headers/$tag.err'
    date -u +%FT%T.%3NZ > '$OUT/ts/$tag.done'
  "
  local flock_exit=$?
  local t_sent t_done code
  t_sent=$(cat "$OUT/ts/$tag.sent" 2>/dev/null || echo "(none)")
  t_done=$(cat "$OUT/ts/$tag.done" 2>/dev/null || echo "(none)")
  code=$(cat "$OUT/ts/$tag.code" 2>/dev/null || echo "000")
  local nbytes=0 sha="(none)"
  if [ -f "$OUT/bodies/$tag.b" ]; then
    nbytes=$(wc -c < "$OUT/bodies/$tag.b" | tr -d ' ')
    sha=$(sha256sum "$OUT/bodies/$tag.b" | cut -d' ' -f1)
  fi
  local cf
  cf=$(awk 'NR>1' "$OUT/headers/$tag.h" 2>/dev/null \
        | tr -d '\r' | awk '/: /{i=index($0,": ");k=tolower(substr($0,1,i-1));v=substr($0,i+2);
          if(k in a)a[k]=a[k]", "v;else a[k]=v} END{for(k in a)printf "%s: %s|",k,a[k]}' \
        | sed 's/|$//')
  [ -n "$cf" ] || cf="(none)"
  # ctype_full travels via a file, not shell interpolation: header values
  # contain double quotes, which broke an earlier revision in this repo that
  # interpolated the header string into a Python literal (area J).
  printf '%s' "$cf" > "$OUT/ts/$tag.cf"
  local status="${code:-000}"
  local curl_exit=0
  [ "$flock_exit" -eq 0 ] || curl_exit=$flock_exit
  local host_seq; host_seq=$(python3 -c "
import json
n = 0
try:
    for line in open('$OUT/results.jsonl'):
        try:
            if json.loads(line).get('host') == '$host': n += 1
        except ValueError: pass
except FileNotFoundError: pass
print(n + 1)")
  # body head: 200 chars, for the human reading the ledger. Never a credential;
  # these are public repository files.
  local head=""; head=$(head -c 200 "$OUT/bodies/$tag.b" 2>/dev/null | tr -d '\n\r')
  printf '%s' "$head" > "$OUT/ts/$tag.head"
  python3 - "$OUT/results.jsonl" "$SEQ" "$host_seq" "$host" "$tag" "$role" "$path" "$status" "$curl_exit" "$nbytes" "$sha" "$t_queued" "$t_sent" "$t_done" "$OUT/ts/$tag.cf" "$OUT/ts/$tag.head" <<'PY'
import json, sys
(_, out, seq, host_seq, host, tag, role, path, status, exit_, nbytes, sha,
 t_queued, t_sent, t_done, cf_file, head_file) = sys.argv
cf = open(cf_file, encoding="utf-8").read() or "(none)"
head = open(head_file, encoding="utf-8").read()
row = {
  "seq": int(seq), "host_seq": int(host_seq), "host": host, "host_tag": tag,
  "method": "GET", "path": path, "role": role,
  "sent_headers": "Accept: application/vnd.github+json | User-Agent: carelink-api-research-static-audit (UNAUTHENTICATED — no Authorization header)",
  "http_status": status, "curl_exit": int(exit_),
  "body_bytes": int(nbytes), "body_sha256": sha,
  "ctype_full": cf, "body_head_200": head,
  "t_queued": t_queued, "t_sent": t_sent, "t_done": t_done,
}
open(out, "a").write(json.dumps(row) + "\n")
PY
  log "t_queued=$t_queued t_sent=$t_sent t_done=$t_done seq=$SEQ host_seq=$host_seq $host $path method=GET role=$role status=$status bytes=$nbytes sha=$sha"
  echo "seq=$SEQ host_seq=$host_seq $host $path status=$status bytes=$nbytes sha=${sha:0:12}"
}

echo "probe start: $(date -u +%FT%T.%3NZ)" > "$OUT/run.log"

# ---------------------------------------------------------------- step 1
# Resolve the default branch of the CarlosJPV repo from the API rather than
# assuming main-vs-master: a wrong guess costs a wasted request and produces a
# bogus "404 = file gone at head" drift verdict.
req "api.github.com" "/repos/CarlosJPV/carelink-cumulus-bridge" \
    "STEP-resolve-default-branch" "01-repo-meta" || exit 1
CJ_HEAD=$(python3 -c "
import json,sys
d=json.load(open('$OUT/bodies/01-repo-meta.b'))
print(d.get('default_branch') or 'MISSING')" 2>/dev/null)
if [ "$CJ_HEAD" = "MISSING" ] || [ -z "$CJ_HEAD" ]; then
  log "ABORT: could not resolve default_branch from seq=1"
  echo "ABORT: default_branch unresolved" >&2; exit 1
fi
echo "CarlosJPV default_branch = $CJ_HEAD"

# xDrip's default branch is recorded as master in the source pass; the same
# resolution is unnecessary for a repo whose branch name that pass read
# directly, and one request is better spent on a control.

# ---------------------------------------------------------------- controls
# C1: certainly-absent REF, at the most plausible path we intend to read.
req "api.github.com" "/repos/NightscoutFoundation/xDrip/contents/$XD_CARE?ref=deadbeefdeadbeefdeadbeefdeadbeefdeadbeef" \
    "CONTROL-neg-ref" "02-ctl-necref" || exit 1
# C2: certainly-absent PATH, at a real ref.
req "api.github.com" "/repos/CarlosJPV/carelink-cumulus-bridge/contents/src/zzz-no-such-path-area-q.ts?ref=$CJ_PIN" \
    "CONTROL-neg-path" "03-ctl-negpath" || exit 1

# ---------------------------------------------------------------- step 2
# Assert the pinned commits resolve, and record their dates. An abbreviated SHA
# that silently resolved to something else would invalidate every cite below.
req "api.github.com" "/repos/NightscoutFoundation/xDrip/commits/$XD_PIN" \
    "RESOLVE-pinned-sha" "04-xd-pin" || exit 1
req "api.github.com" "/repos/CarlosJPV/carelink-cumulus-bridge/commits/$CJ_PIN" \
    "RESOLVE-pinned-sha" "05-cj-pin" || exit 1

# ---------------------------------------------------------------- step 3
# Each subject file: PINNED COMMIT and BRANCH HEAD. The git blob sha in the
# response is the drift oracle.
req "api.github.com" "/repos/NightscoutFoundation/xDrip/contents/$XD_CARE?ref=$XD_PIN" \
    "SUBJ-xdrip-carelinkclient-PINNED" "06-xd-care-pin" || exit 1
req "api.github.com" "/repos/NightscoutFoundation/xDrip/contents/$XD_CARE?ref=master" \
    "SUBJ-xdrip-carelinkclient-HEAD" "07-xd-care-head" || exit 1
req "api.github.com" "/repos/CarlosJPV/carelink-cumulus-bridge/contents/$CJ_CUMULUS?ref=$CJ_PIN" \
    "SUBJ-cumulus-ts-PINNED" "08-cj-cumulus-pin" || exit 1
req "api.github.com" "/repos/CarlosJPV/carelink-cumulus-bridge/contents/$CJ_CUMULUS?ref=$CJ_HEAD" \
    "SUBJ-cumulus-ts-HEAD" "09-cj-cumulus-head" || exit 1
req "api.github.com" "/repos/CarlosJPV/carelink-cumulus-bridge/contents/$CJ_README?ref=$CJ_PIN" \
    "SUBJ-readme-PINNED" "10-cj-readme-pin" || exit 1
req "api.github.com" "/repos/CarlosJPV/carelink-cumulus-bridge/contents/$CJ_README?ref=$CJ_HEAD" \
    "SUBJ-readme-HEAD" "11-cj-readme-head" || exit 1
req "api.github.com" "/repos/CarlosJPV/carelink-cumulus-bridge/contents/$CJ_PROBE?ref=$CJ_PIN" \
    "SUBJ-probe-appversion-ts-PINNED" "12-cj-probe-pin" || exit 1
req "api.github.com" "/repos/CarlosJPV/carelink-cumulus-bridge/contents/$CJ_PROBE?ref=$CJ_HEAD" \
    "SUBJ-probe-appversion-ts-HEAD" "13-cj-probe-head" || exit 1
req "api.github.com" "/repos/CarlosJPV/carelink-cumulus-bridge/contents/$CJ_GITIGNORE?ref=$CJ_PIN" \
    "SUBJ-gitignore-PINNED" "14-cj-gitignore-pin" || exit 1
req "api.github.com" "/repos/CarlosJPV/carelink-cumulus-bridge/contents/$CJ_GITIGNORE?ref=$CJ_HEAD" \
    "SUBJ-gitignore-HEAD" "15-cj-gitignore-head" || exit 1

# ---------------------------------------------------------------- step 4
# The author-reported boundary table. The source pass says it is a README table
# AND a comment on xDrip PR #4711; fetch both and give both, per AGENTS.md section 2.
req "api.github.com" "/repos/NightscoutFoundation/xDrip/pulls/4711" \
    "SUBJ-xdrip-pr-4711" "16-xd-pr4711" || exit 1
req "api.github.com" "/repos/NightscoutFoundation/xDrip/issues/4711/comments" \
    "SUBJ-xdrip-pr-4711-comments" "17-xd-pr4711-comments" || exit 1

# ---------------------------------------------------------------- step 5
# C4: independent byte-level cross-check on one contents response, from a
# different host and a different code path, so a silently-empty payload cannot
# be mistaken for agreement (docs/09 section 5 item 3).
req "raw.githubusercontent.com" "/NightscoutFoundation/xDrip/$XD_PIN/$XD_CARE" \
    "CONTROL-crosshost-raw-vs-api" "18-raw-xd-care" || exit 1

echo "done: $SEQ of a $CAP cap" | tee -a "$OUT/run.log"