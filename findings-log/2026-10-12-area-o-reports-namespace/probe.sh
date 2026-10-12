#!/usr/bin/env bash
# ############################################################################
# # READ THIS BEFORE TRUSTING THE TIMESTAMPS IN run.log                    #
# #                                                                         #
# # THE RUN THAT PRODUCED results.jsonl / run.log / headers/ DID NOT SLEEP. #
# #                                                                         #
# # `DELAY=2.5` was declared and the lock section was commented "sleep +   #
# # curl", but the `sleep` call was never emitted into req(). So all 24    #
# # requests went out with the host-to-host gap dictated only by curl's     #
# # round trip: 21 same-host gaps, and NOT ONE of them reaching the         #
# # repository's >=2 s floor (AGENTS.md section 8).                         #
# #                                                                         #
# # CORRECTED MEASUREMENT: run.log's `t0` is unreliable on two rows (seq 9 #
# # and seq 20), so the first report of "min -0.538 s" was an artefact of  #
# # two corrupt `date` reads, not concurrent requests. Measured from the    #
# # body-file mtimes curl wrote, the true figures are min +0.092 s, max      #
# # +0.387 s, ZERO negative gaps and NO overlap. This file's own pass      #
# # therefore UNDERSTATED how badly it breached the floor. See mtime.py and #
# # FINDINGS.md section 1a.                                                #
# #                                                                         #
# # This is a breach of the probing rule, not a rounding artefact, and it   #
# # is disclosed as such in FINDINGS.md section 1b. The run was NOT redone: #
# # a clean re-run is 24 more requests on top of the 24 already sent, which #
# # would blow the 30-request cap committed in issue #24 — fixing one       #
# # committed limit by breaking another is not a repair.                   #
# #                                                                         #
# # The sleep below is the POST-RUN FIX, so this file is re-runnable with   #
# # correct pacing. It is a one-line addition in req(); it touches no       #
# # request-issuing logic, no URL, no header and no candidate list. The     #
# # executed artefacts are preserved byte-for-byte and are NOT regenerated. #
# # FINDINGS.md section 1b carries the exact diff.                          #
# #                                                                         #
# # A comment asserting a discipline is not the discipline. This file is the #
# # proof of that: for one run, the comment was there and the call was not. #
# ############################################################################
#
# Area O harness — is /patient/reports/* on carelink.* the reports surface for
# every region?
#
# Claim issue: https://github.com/NovaLux12/carelink-api-research/issues/24
#
# WHAT THIS SENDS, AND NOTHING ELSE
#   GET only. No -X, no -d, no --data*, no Authorization, no Cookie, no
#   x-api-key, no token exchange, no authentication. The only header sent that
#   a default curl does not send is the User-Agent, set to the SAME UA the
#   repo's own 05-public-config.check.sh uses, so these rows are comparable
#   with the existing corpus.
#
#   A 405 means the route is POST-only and live. It is EVIDENCE. It is never
#   sent. See AGENTS.md section 8.
#
# ORDER IS LOAD-BEARING
#   carelink.minimed.eu runs FIRST, entirely. It is the live control for the
#   two sibling verdicts (the recorded .eu rows are three days old and were
#   captured by a different harness). If it does not reproduce, the sibling
#   comparison has no baseline and the pass stops there rather than reporting
#   two verdicts against a baseline that is itself in question.
#
#   Per host: CONTROL-absent, CONTROL-known-live, then the seven candidates.
#   Both controls precede every candidate on every host.
#
# CAP
#   CAP=30 guard below exits 9 before issuing a request past the cap.
#   Expected 24 (3 hosts x 8). Up to 3 further requests are permitted ONLY by
#   the adaptive branch: if a host's CONTROL-known-live returns 404, one
#   request to /patient/v2/configuration/public on that same host separates
#   "this host is not serving the patient surface" from "this host is serving
#   it but /patient/reports/* is not routed here". Without it a 404 on the
#   controls is ambiguous and the pass could not tell a host down from a
#   namespace absent. That branch is capped at one request per host and can
#   therefore fire at most three times.
#
# LOCKING
#   Per-host lock at $REPO/.loop/host-<hostname>.lock, taken around each
#   single request with the sleep INSIDE the lock. Three other pool workers
#   share this machine. Nothing but sleep+curl runs while the lock is held.
#
# RUN ONCE
#   Refuses to run if results.jsonl or run.log already exists, so the request
#   count cannot silently double.

set -uo pipefail
cd "$(dirname "$0")"

# Lock files live in the MAIN clone's .loop/ directory, NOT in this worktree --
# that directory is shared with the other three pool workers on this machine.
# Portable form; override with CARELINK_LOOP_ROOT if the checkout lives
# elsewhere. See FINDINGS.md section 1b for the post-run edit that introduced it.
REPO="${CARELINK_LOOP_ROOT:-$HOME/.openclaw/workspace/projects/novas-github/carelink-api-research}"
CAP=30
UA="carelink-bridge-research/1.0"
DELAY=2.5
LEDGER="results.jsonl"
RUNLOG="run.log"

if [ -e "$LEDGER" ] || [ -e "$RUNLOG" ]; then
  echo "REFUSING TO RUN: results.jsonl or run.log already exists." >&2
  echo "This pass is one-shot by design; the request count must not double." >&2
  exit 2
fi
mkdir -p headers
: > "$LEDGER"
: > "$RUNLOG"

# The certainly-absent control carries a run-unique suffix so it can never have
# been served before by anything, including a parked wildcard front door.
NONCE="this-does-not-exist-ocl-probe-$(date -u +%Y%m%dT%H%M%SZ)"
echo "absent-path suffix: $NONCE" >> "$RUNLOG"

SEQ=0
declare -A HSEQ

emit() { # emit <key> <value>  -> "(none)" when empty
  if [ -z "${2:-}" ] || [ "$2" = "(null)" ]; then printf '(none)'; else printf '%s' "$2"; fi
}

# Takes the LAST occurrence: with a proxy in the path curl -D records more than
# one header block and the final response is the one that answers the question.
# The value is cut from the RAW record with sub(), not by reading $2 -- because
# under FS=": *" awk assigns $1="" makes it rebuild $0 with OFS and re-introduce
# a leading space (" application/json"), which would then reach the ledger.
# FS=": *" is load-bearing for the other half: it is what makes $1 the header
# NAME, which is what is compared against k.
hdrval() { # hdrval <headerfile> <lowercase-name>
  awk -v k="$(printf '%s' "$2" | tr 'A-Z' 'a-z')" '
    BEGIN{FS=": *"}
    { l=tolower($1); sub(/\r$/,"",l)
      if (l==k) { v=$0; sub(/^[^:]*:[ \t]*/,"",v); sub(/\r$/,"",v)
                  if (v!="") last=v } }
    END{ print (last=="" ? "" : last) }' "$1"
}

ctype_full() { # whole response header block, "k: v|k: v"
  awk 'BEGIN{n=0}
       /^\r?$/ {next}
       { sub(/\r$/,""); if ($0 !~ /^[A-Za-z0-9-]+:/) next; n++; s[n]=$0 }
       END{ for(i=1;i<=n;i++) printf "%s%s", (i>1?"|":""), s[i] }' "$1"
}

req() { # req <host> <path> <role> <tag>
  local host="$1" path="$2" role="$3" tag="$4"
  local url="https://$host$path"
  local lock="$REPO/.loop/host-$host.lock"
  touch "$lock" 2>/dev/null || true

  if [ "$SEQ" -ge "$CAP" ]; then
    echo "CAP=$CAP reached; refusing to issue $url" >&2
    exit 9
  fi

  SEQ=$((SEQ + 1))
  HSEQ[$host]=$(( ${HSEQ[$host]:-0} + 1 ))
  local hseq="${HSEQ[$host]}"

  local t0 code exit_code
  t0=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

  # ---- the only vendor-touching section; lock held across sleep + curl ----
  exec {LOCKFD}>"$lock"
  flock "$LOCKFD"
  sleep "$DELAY"
  code=$(curl -s --compressed \
      --max-time 30 \
      -A "$UA" \
      -D "headers/$tag.h" -o "headers/$tag.b" \
      -w '%{http_code}' "$url")
  exit_code=$?
  flock -u "$LOCKFD"
  exec {LOCKFD}>&-
  # -----------------------------------------------------------------------

  local h="headers/$tag.h" b="headers/$tag.b"
  local bytes sha ct amznerr caca cors cenc server allow ctype
  bytes=$(wc -c < "$b" 2>/dev/null | tr -d ' '); bytes="${bytes:-0}"
  sha=$(sha256sum "$b" 2>/dev/null | cut -d' ' -f1); sha="${sha:-}"
  ct=$(hdrval "$h" content-type)
  amznerr=$(hdrval "$h" x-amzn-errortype)
  caca=$(hdrval "$h" x-ca-err)
  cors=$(hdrval "$h" access-control-allow-origin)
  cenc=$(hdrval "$h" content-encoding)
  server=$(hdrval "$h" server)
  allow=$(hdrval "$h" allow)

  jq -nc \
    --argjson seq "$SEQ" \
    --argjson host_seq "$hseq" \
    --arg host "$host" \
    --arg host_tag "$tag" \
    --arg method "GET" \
    --arg path "$path" \
    --arg role "$role" \
    --arg sent_headers "User-Agent: $UA" \
    --arg http_status "$code" \
    --arg curl_exit "$exit_code" \
    --arg content_type "$(emit x "$ct")" \
    --arg x_amzn_errortype "$(emit x "$amznerr")" \
    --arg x_ca_err "$(emit x "$caca")" \
    --arg access_control_allow_origin "$(emit x "$cors")" \
    --arg content_encoding "$(emit x "$cenc")" \
    --arg server "$(emit x "$server")" \
    --arg allow "$(emit x "$allow")" \
    --arg ctype_full "$(ctype_full "$h")" \
    --argjson body_bytes "${bytes:-0}" \
    --arg body_sha256 "$sha" \
    '{seq:$seq, host_seq:$host_seq, host:$host, host_tag:$host_tag,
      method:$method, path:$path, role:$role, sent_headers:$sent_headers,
      http_status:$http_status, curl_exit:$curl_exit, content_type:$content_type,
      x_amzn_errortype:$x_amzn_errortype, x_ca_err:$x_ca_err,
      access_control_allow_origin:$access_control_allow_origin,
      content_encoding:$content_encoding, server:$server, allow:$allow,
      ctype_full:$ctype_full, body_bytes:$body_bytes, body_sha256:$body_sha256}' \
    >> "$LEDGER"

  printf '%s seq=%-3s hseq=%-2s %-30s GET %-58s %-40s http=%-4s exit=%-3s bytes=%-7s sha=%s\n' \
    "$t0" "$SEQ" "$hseq" "$host" "$path" "$role" "${code:-000}" "$exit_code" \
    "$bytes" "${sha:0:12}" >> "$RUNLOG"

  printf 'seq=%-3s %-30s http=%-4s %s\n' "$SEQ" "$host" "${code:-000}" "$path"
}

# ---------------------------------------------------------------------------
# The seven candidate paths, verbatim from the corpus.
#   findings-log/probe-2026-10-08/recon/ARCHIVE-URLS.md:162
# The list is NOT re-derived per host and NOT guessed. The recorded verdicts
# there are ARCHIVE verdicts, first captured 2020-09-29, last 2021-03-31
# (ARCHIVE-URLS.md:329) -- see FINDINGS.md section 1a.
# ---------------------------------------------------------------------------
CANDIDATES=(
  "supported:401"
  "snapshotTimelinesRange:401"
  "generateReport:405"
  "favoriteReports:405"
  "snapshotTimelinesForCalendar:405"
  "reportStatus:400"
  "report:404"
)

HOSTS=(
  "carelink.minimed.eu"
  "carelink.minimed.com"
  "carelink-trials.minimed.com"
)

for host in "${HOSTS[@]}"; do
  short=$(printf '%s' "$host" | tr '.' '-')

  # CONTROL 1 — certainly absent, same prefix. Establishes what DEAD looks like
  # on THIS host, so a later 404 is a real absence and not a uniform front-door
  # response. Sends nothing but a path that cannot exist.
  req "$host" "/patient/reports/$NONCE" "CONTROL-certainly-absent-same-prefix" "${short}--c1-absent"

  # CONTROL 2 — known-live recorded path, and candidate 1 of the seven in one
  # request. On .eu this is what decides whether the sibling comparison has a
  # baseline at all.
  req "$host" "/patient/reports/supported" "CONTROL-known-live-and-CANDIDATE-1-of-7" "${short}--c2-live-supported"

  for entry in "${CANDIDATES[@]:1}"; do
    name="${entry%%:*}"
    req "$host" "/patient/reports/$name" "CANDIDATE-$name" "${short}--k-${name}"
  done

  # ADAPTIVE BRANCH (capped at one per host, only if CONTROL 2 came back 404):
  # a 404 on the live control is ambiguous on its own -- "host not serving the
  # patient surface" and "namespace not routed here" look identical. This one
  # request separates them. /patient/v2/configuration/public is known-live and
  # unauthenticated: it is the URL regression/hurl/05-public-config.check.sh
  # fetches (its CFG variable) and the one every gate run proves live today.
  live_row=$(grep -F "\"host_tag\":\"${short}--c2-live-supported\"" "$LEDGER" | tail -1)
  if [ -n "$live_row" ] && [ "$(printf '%s' "$live_row" | jq -r '.http_status')" = "404" ]; then
    req "$host" "/patient/v2/configuration/public" \
        "CONTROL-host-alive-ambiguity-breaker-for-a-404-live-control" "${short}--c3-hostalive"
  fi
done

echo "DONE n=$SEQ cap=$CAP"