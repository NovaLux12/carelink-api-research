#!/usr/bin/env bash
# Area M — Common Crawl via the CDX index API, not computed byte offsets.
# Claim issue #44. Cap 60 requests, raised to 64 by OWNER AUTHORISATION
# (dated addendum on #44, 2026-10-13) for the cdx-00101.gz overshoot re-read
# only. GET only. Zero vendor traffic.
#
# WHAT THIS IS FOR
# ----------------
# docs/10 §2 carries a CLOSED negative — "Does Common Crawl cover the API
# surface? Essentially zero" — that was produced by the data.commoncrawl.org
# bulk path (binary-searched cluster.idx -> ranged cdx-NNNNN.gz fetches) after
# index.commoncrawl.org was unreachable from the host that ran it. AGENTS.md §6
# item 1: a claim that cannot be sourced should be deleted, not inherited. So
# this pass re-derives the negative through the API the earlier pass could not
# reach, across a named set of crawls, with two controls sent FIRST.
#
# HOST POLICY
# -----------
# Exactly two hosts may be contacted, both non-vendor:
#     index.commoncrawl.org    the CDX index API
#     data.commoncrawl.org     the bulk path, used ONLY to re-derive and check
#                             the earlier pass's byte offsets (step 4 of the claim)
# The `req()` function refuses any other host. There is no vendor denylist
# because there is no vendor allowlist either: this pass makes no Medtronic
# request of any kind, which is what makes it safe to run beside three other
# workers.
#
# CONTROLS GO FIRST
# -----------------
# The whole finding is a claim about a ZERO, so a zero measured against a
# broken instrument is worthless. Queries 1-4 are, in order:
#   1  collinfo.json                  - is the host reachable AT ALL today
#   2  CONTROL-A  example.com         - a host CC is known to cover -> rows
#   3  CONTROL-B  medtronic.com       - the same API, same crawl, same query
#                                       shape, on the namespace under test
#   4  CONTROL-C  a fabricated host   - a TRUE zero, not a syntax artefact
# Nothing else is sent until all four have been read.
#
# PUBLISH RULE (AGENTS.md §7)
# ---------------------------
# No response body is committed. CC captures carry Java session identifiers in
# URL paths and pre-Auth0 authorize URLs whose sessionData is a plaintext-base64
# JWS, so a raw head is a raw capture. Bodies are written under bodies/ (which
# this directory's .gitignore excludes) and immediately reduced, in code, to
# bytes + sha256 + record count + the DISTINCT HOSTNAMES the response mentions.
# A hostname is the leftmost label of a URL and cannot carry a path, a query
# string or a session parameter, so that projection is safe. derive.py --selftest
# asserts the projection both fires on positives and stays quiet on controls.
#
# LEDGER
# ------
# One results.jsonl row per request, whatever issued it. seq continues across
# invocations from the file itself, so three invocations form one ledger.
# Every row carries t_queued / t_sent / t_done in millisecond UTC ISO-8601;
# t_sent is written INSIDE the per-host lock, immediately before curl, because
# the spacing rule is a rule about sends. Bodies are written by curl at
# bodies/<tag>.b, so their kernel mtimes are the independent spacing oracle
# (docs/09 §4): a harness `date` series that disagrees with them is the suspect,
# not the requests.
#
# PER-HOST LOCK
# -------------
# sleep 2.5 INSIDE the flock. A sleep outside the lock lets other workers queue
# up and then fire together inside one window, which is worse than no lock.
#
# USAGE: ./probe.sh queries-01-reachability-and-controls.txt

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE"
CAP=64
DELAY=2.5
QFILE="${1:?usage: probe.sh <queries-file>}"

LOCKS=""
d="$HERE"
while [ "$d" != "/" ]; do
  if [ -f "$d/.loop/BRIEF.md" ]; then LOCKS="$d/.loop"; break; fi
  d="$(dirname "$d")"
done
: "${LOCKS:?could not locate the pool .loop directory}"

ALLOWED="index.commoncrawl.org data.commoncrawl.org"

mkdir -p "$OUT/headers" "$OUT/bodies" "$OUT/ts"

log() { echo "$*" >> "$OUT/run.log"; }

SEQ=0
if [ -f "$OUT/results.jsonl" ]; then
  SEQ=$(grep -c . "$OUT/results.jsonl" 2>/dev/null || echo 0)
fi

req() { # req <tag> <role> <host> <path-and-query> [extra curl args]
  local tag="$1" role="$2" host="$3" path="$4" extra="${5:-}"
  SEQ=$((SEQ+1))
  if [ "$SEQ" -gt "$CAP" ]; then
    log "seq=$SEQ ABORTED cap $CAP reached before $host$path"
    echo "ABORTED at seq=$SEQ — cap $CAP reached. Stopping; write up what exists."
    return 1
  fi
  case " $ALLOWED " in
    *" $host "*) : ;;
    *) log "seq=$SEQ REFUSED host $host is not in the allowlist"; return 1 ;;
  esac
  touch "$LOCKS/host-$host.lock"
  local url="https://$host$path"
  local t_queued; t_queued=$(date -u +%FT%T.%3NZ)
  # shellcheck disable=SC2086
  flock "$LOCKS/host-$host.lock" -c "
    sleep $DELAY
    date -u +%FT%T.%3NZ > '$OUT/ts/$tag.sent'
    curl -sS --compressed $extra \
      -D '$OUT/headers/$tag.h' -o '$OUT/bodies/$tag.b' \
      -w '%{http_code}' '$url' > '$OUT/ts/$tag.code' 2>'$OUT/headers/$tag.err'
    date -u +%FT%T.%3NZ > '$OUT/ts/$tag.done'
  "
  local flock_exit=$?
  local t_sent t_done code
  t_sent=$(cat "$OUT/ts/$tag.sent" 2>/dev/null || echo "(none)")
  t_done=$(cat "$OUT/ts/$tag.done" 2>/dev/null || echo "(none)")
  code=$(cat "$OUT/ts/$tag.code" 2>/dev/null || echo "000")
  [ -n "$code" ] || code=000
  local nbytes=0 sha="(none)"
  if [ -f "$OUT/bodies/$tag.b" ]; then
    nbytes=$(wc -c < "$OUT/bodies/$tag.b" | tr -d ' ')
    sha=$(sha256sum "$OUT/bodies/$tag.b" | cut -d' ' -f1)
  fi
  # Discriminating headers only — the set this repo compares on
  # (docs/09 §4): content-type, the AWS error class, the CA error code,
  # CORS, and cache state. Status is never the discriminator.
  local cf
  cf=$(tr -d '\r' < "$OUT/headers/$tag.h" 2>/dev/null \
        | awk 'BEGIN{IGNORECASE=1} /^: /{next} \
          {i=index($0,": "); if(i==0) next; k=tolower(substr($0,1,i-1)); v=substr($0,i+2); \
           if(k=="content-type"||k=="x-amzn-errortype"||k=="x-ca-err"||k=="x-cache"|| \
              k=="access-control-allow-origin"||k=="content-range"||k=="content-encoding"|| \
              k=="retry-after"||k=="location") \
             {if(k in a) a[k]=a[k]", " v; else a[k]=v}} \
          END{for(k in a) printf "%s: %s|", k, a[k]}' | sed 's/|$//')
  [ -n "$cf" ] || cf="(none)"
  printf '%s' "$cf" > "$OUT/ts/$tag.cf"
  # Reduce the body to host-only facts in code (see header). Never store text.
  local facts
  facts=$(python3 "$OUT/derive.py" "$OUT/bodies/$tag.b" 2>/dev/null || echo '{"record_count":0,"distinct_hosts":[],"distinct_host_count":0,"shape":"none"}')
  printf '%s' "$facts" > "$OUT/ts/$tag.facts"
  local host_seq
  host_seq=$(python3 -c "
import json,sys
n=0
try:
    for line in open('$OUT/results.jsonl'):
        try:
            if json.loads(line).get('host')=='$host': n+=1
        except ValueError: pass
except FileNotFoundError: pass
print(n+1)")
  python3 - "$OUT/results.jsonl" "$SEQ" "$host_seq" "$host" "$tag" "$role" "$path" "$code" "$flock_exit" "$nbytes" "$sha" "$t_queued" "$t_sent" "$t_done" "$OUT/ts/$tag.cf" "$OUT/ts/$tag.facts" <<'PY'
import json, sys
(_, out, seq, host_seq, host, tag, role, path, status, exit_, nbytes, sha,
 t_queued, t_sent, t_done, cf_file, facts_file) = sys.argv
row = {
  "seq": int(seq), "host_seq": int(host_seq), "host": host, "host_tag": tag,
  "method": "GET", "path": path, "role": role,
  "http_status": status, "curl_exit": int(exit_),
  "body_bytes": int(nbytes), "body_sha256": sha,
  "disc_headers": open(cf_file, encoding="utf-8").read() or "(none)",
  # AGENTS.md §7: response text is never committed. This field is the record
  # that it was deliberately withheld, not a placeholder for a missing value.
  "body_head": "<withheld-by-policy: raw CDX/JSON text carries session material; see derive.py>",
  **json.load(open(facts_file, encoding="utf-8")),
  "t_queued": t_queued, "t_sent": t_sent, "t_done": t_done,
}
open(out, "a").write(json.dumps(row) + "\n")
PY
  log "t_queued=$t_queued t_sent=$t_sent t_done=$t_done seq=$SEQ host_seq=$host_seq $host $path method=GET role=$role status=$code bytes=$nbytes sha=$sha"
  echo "seq=$SEQ $host $path -> $code (${nbytes}B) $tag"
  return 0
}

# FIXED 2026-10-13 (verifier round 1, BLOCKING 2). This loop was
#   while IFS='|' read -r tag role host path extra; do ... done < "$QFILE"
# which SILENTLY DROPS THE LAST LINE whenever the file has no trailing newline:
# `read` returns non-zero at EOF-without-newline, so the loop exits before the
# final line is dispatched. Four of this pass's query files had no trailing
# newline, so four queries were never sent and three of them have no ledger row
# at all. The `|| [ -n ... ]` guard makes the last unterminated line count, and
# the check below says so out loud instead of only describing it in a comment.
if [ "$(tail -c 1 "$QFILE" | wc -l)" -eq 0 ]; then
  log "WARN $(basename "$QFILE") has no trailing newline; a bare read loop would drop its last line"
fi

while IFS='|' read -r tag role host path extra || [ -n "${tag}${role}${host}${path}" ]; do
  case "$tag" in ''|\#*) continue ;; esac
  req "$tag" "$role" "$host" "$path" "$extra" || break
done < "$QFILE"

echo "done: $SEQ of a $CAP cap"