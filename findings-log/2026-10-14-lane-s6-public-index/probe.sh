#!/usr/bin/env bash
# S6 — Common Crawl public host/path inventory, and the completeness question
# that docs/10 line 64 leaves open.
#
# AREA / SCOPE
# ------------
# Two hosts, both non-vendor, and nothing else:
#     index.commoncrawl.org    the CDX index API
#     data.commoncrawl.org     the bulk path (unused by this pass)
# req() refuses any host not on that list, so there is no vendor request, no
# vendor DNS, no vendor TLS. That is what makes this pass safe to run beside
# other workers. GET only, forever.
#
# WHAT THIS PASS IS TRYING TO SETTLE
# ---------------------------------
# docs/10 carries a CLOSED negative -- "Common Crawl covers essentially none of
# the API surface" -- plus an OPEN completeness question left by area L: an
# un-limited `matchType=domain` record query was never shown to be complete,
# only corroborated at small sizes (<= ~2000 records). The reasoning was that
# the absent `limit` is what makes a set complete "rather than their being
# small". That is INFERRED and it is untested at scale.
#
# The test here is a byte-cap detector. `fl=` selects WHICH FIELDS each record
# carries. It cannot change WHICH RECORDS match. So for one fixed (crawl, url)
# pair, issue the same query three times at three field widths:
#
#     narrow  fl=url                                            ~ 40 B/record
#     medium  fl=url,timestamp,status,mimetype                  ~160 B/record
#     wide    fl=url,timestamp,status,mimetype,digest,filename,
#             offset,length                                    ~330 B/record
#
# If the API truncates its response at a byte ceiling, the three counts MUST
# come back different -- wide < medium < narrow -- and the shortfall is
# invisible in any single response. If all three agree, no byte ceiling bit,
# and the set is complete. The 2022-40/medtronic.com response already on disk
# is EXACTLY 32768 bytes, which is 2^15 and smells like exactly this cap, so
# that cell gets the full triple plus the count and pagination oracles.
#
# CONTROLS GO FIRST
# -----------------
# The whole finding is a claim about counts, so no count is read until the
# instrument has returned a known-positive and a known-zero:
#   1 collinfo.json      the host is reachable and publishes what it claims to
#   2 CONTROL-A example.com    a host CC certainly covers -> records
#   3 CONTROL-B <fabricated>    a TRUE zero, not a syntax artefact
# Nothing else is sent until all three have been read.
#
# LEDGER INTEGRITY (why this file differs from the one it replaces)
# ---------------------------------------------------------------
# The previous pass left 76 rows, five of which record t_done BEFORE t_sent --
# impossible under the sleep/date/curl/date order the script documents, so those
# five rows' timing columns cannot be trusted. The likely cause is not
# established. This version removes the two properties that would let it recur:
#
#   * The JSONL row is written INSIDE the flock. Previously the row was
#     assembled after the lock was released, by re-reading ts/*.sent and
#     ts/*.done off disk -- so any writer that touched those files between
#     unlock and re-read could put another request's timestamps in this row.
#   * Tags are asserted unique against the existing ledger before a request is
#     sent, and a duplicate aborts rather than silently overwriting.
#
# Body mtimes remain the independent spacing oracle (docs/09 section 4): curl
# writes the body file, so its kernel mtime is not something the harness can
# assert about itself.
#
# PUBLISH RULE (AGENTS.md section 7)
# ---------------------------------
# CC captures carry jsessionid_* values in URL paths and pre-Auth0 authorize
# URLs whose sessionData is a base64 JWS. No response body is committed. Each
# one is reduced, in code, to bytes + sha256 + record count + the distinct
# HOSTNAMES it mentions. A hostname is the leftmost label of a URL and cannot
# carry a path, a query string or a session parameter.
#
# PER-HOST LOCK
# -------------
# sleep 2.5 INSIDE the flock. A sleep outside the lock lets other workers queue
# up and fire together inside one window, which is worse than no lock.
#
# USAGE: ./probe.sh <queries-file>

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE"
# Response bodies and timestamp scratch do NOT live under findings-log/.
# AGENTS.md section 3 makes that tree append-only evidence, and the gate's
# hygiene check globs it for anything over 1 MiB -- two genuine CC responses in
# this pass are 1.86 MB and 1.2 MB, so keeping them here fails the gate on the
# strength of files that are never meant to be committed. They live outside the
# repository instead, and only their host-only projections are recorded.
SCRATCH="${S6_SCRATCH:-${TMPDIR:-/tmp}/carelink-s6-lane-scratch}"
CAP=400
# Minimum per-host spacing is 2.5 s and the sleep runs INSIDE the lock. The
# default can be raised from the environment without editing this file, which
# matters because this API answers 502/504 under load and a retry storm makes
# that worse: 9 of the 15 requests in the first completeness round came back
# 502/504 at 2.5 s, and 9 of the next 11 at 8 s. Raising the delay is the honest fix; retrying faster is
# the one that gets an account throttled.
DELAY="${S6_DELAY:-2.5}"
QFILE="${1:?usage: probe.sh <queries-file>}"

LOCKS=""
d="$HERE"
while [ "$d" != "/" ]; do
  if [ -f "$d/.loop/BRIEF.md" ]; then LOCKS="$d/.loop"; break; fi
  d="$(dirname "$d")"
done
: "${LOCKS:?could not locate the pool .loop directory}"

ALLOWED="index.commoncrawl.org data.commoncrawl.org"

mkdir -p "$OUT/headers" "$SCRATCH/bodies" "$SCRATCH/ts"
export S6_SCRATCH="$SCRATCH"

log() { echo "$*" >> "$OUT/run.log"; }

SEQ=0
if [ -f "$OUT/results.jsonl" ]; then
  SEQ=$(grep -c . "$OUT/results.jsonl" 2>/dev/null || true)
  SEQ=${SEQ:-0}
fi
log "=== invocation $(date -u +%FT%T.%3NZ) qfile=$(basename "$QFILE") resume_seq=$SEQ cap=$CAP delay=$DELAY"

req() { # req <tag> <role> <host> <path-and-query> [extra curl args]
  local tag="$1" role="$2" host="$3" path="$4" extra="${5:-}"
  case " $ALLOWED " in
    *" $host "*) : ;;
    *) log "seq=$SEQ REFUSED host $host is not in the allowlist"; return 1 ;;
  esac
  # A reused tag would let one request's body/timing files stand in for
  # another's. Refuse rather than overwrite.
  if grep -q "\"host_tag\": \"$tag\"" "$OUT/results.jsonl" 2>/dev/null; then
    log "seq=$SEQ REFUSED duplicate tag $tag already present in the ledger"
    echo "ABORTED: tag $tag already in the ledger; a duplicate would make the files ambiguous."
    return 1
  fi
  SEQ=$((SEQ+1))
  if [ "$SEQ" -gt "$CAP" ]; then
    log "seq=$SEQ ABORTED cap $CAP reached before $host$path"
    echo "ABORTED at seq=$SEQ — cap $CAP reached. Stopping; write up what exists."
    return 1
  fi
  touch "$LOCKS/host-$host.lock"
  local url="https://$host$path"

  # host_seq is how many ledger rows already name this host, so per-host
  # spacing can be audited without re-reading the file per request.
  local host_seq
  host_seq=$(python3 -c "
import json
n=0
try:
    for line in open('$OUT/results.jsonl'):
        try:
            if json.loads(line).get('host')=='$host': n+=1
        except ValueError: pass
except FileNotFoundError: pass
print(n+1)")

  # ---- the locked region: sleep, send, measure, and COMMIT THE ROW ----
  # Nothing about this request is read back off disk afterwards. t_queued is
  # captured before the lock so the queue wait stays visible; t_sent and t_done
  # are written by this same critical section, in this order, and the ledger row
  # is appended before the lock is released.
  #
  # The row writer is a separate file (record.py) rather than a heredoc inside
  # this string: the first attempt inlined it and a single unescaped `"` in the
  # Python made the whole critical section exit 127. Quoting Python through two
  # layers of shell to save one file is a bad trade.
  local t_queued; t_queued=$(date -u +%FT%T.%3NZ)
  # shellcheck disable=SC2086
  flock "$LOCKS/host-$host.lock" -c "
    set -u
    sleep $DELAY
    date -u +%FT%T.%3NZ > '$SCRATCH/ts/$tag.sent'
    curl -sS --compressed $extra \
      -D '$OUT/headers/$tag.h' -o '$SCRATCH/bodies/$tag.b' \
      -w '%{http_code}' '$url' > '$SCRATCH/ts/$tag.code' 2>'$OUT/headers/$tag.err'
    # curl's REAL exit status. Captured here because record.py used to hardcode 0,
    # which made every row's curl_exit 0 by construction instead of by measurement --
    # a check that cannot fail. The ledger's own stderr proved it: seq 88 carries
    # `curl: (18) transfer closed with outstanding read data remaining`.
    curl_exit=\$?
    date -u +%FT%T.%3NZ > '$SCRATCH/ts/$tag.done'
    code=\$(cat '$SCRATCH/ts/$tag.code' 2>/dev/null || echo 000)
    [ -n \"\$code\" ] || code=000
    nbytes=0; sha='(none)'
    if [ -f '$SCRATCH/bodies/$tag.b' ]; then
      nbytes=\$(wc -c < '$SCRATCH/bodies/$tag.b' | tr -d ' ')
      sha=\$(sha256sum '$SCRATCH/bodies/$tag.b' | cut -d' ' -f1)
    fi
    python3 '$OUT/derive.py' '$SCRATCH/bodies/$tag.b' > '$SCRATCH/ts/$tag.facts' 2>/dev/null \
      || echo '{\"record_count\":0,\"distinct_hosts\":[],\"distinct_host_count\":0,\"shape\":\"none\"}' \
         > '$SCRATCH/ts/$tag.facts'
    # Discriminating headers only -- the set this repo compares on
    # (docs/09 section 4). Status is never the discriminator here: on this API a
    # 404 is 'no such crawl' AND 'no captures for this host', and only the body
    # tells them apart.
    tr -d '\r' < '$OUT/headers/$tag.h' 2>/dev/null \
      | awk 'BEGIN{IGNORECASE=1} /^: /{next} \
        {i=index(\$0,\": \"); if(i==0) next; k=tolower(substr(\$0,1,i-1)); v=substr(\$0,i+2); \
         if(k==\"content-type\"||k==\"x-amzn-errortype\"||k==\"x-ca-err\"||k==\"x-cache\"|| \
            k==\"access-control-allow-origin\"||k==\"content-range\"||k==\"content-encoding\"|| \
            k==\"retry-after\"||k==\"location\") \
            {if(k in a) a[k]=a[k]\", \" v; else a[k]=v}} \
        END{for(k in a) printf \"%s: %s|\", k, a[k]}' | sed 's/|\$//' \
      > '$SCRATCH/ts/$tag.cf' || : > '$SCRATCH/ts/$tag.cf'
    python3 '$OUT/record.py' '$OUT/results.jsonl' '$SEQ' '$host_seq' '$host' '$tag' \
             '$role' '$path' \"\$code\" \"\$nbytes\" \"\$sha\" '$t_queued' \
             \"\$(cat '$SCRATCH/ts/$tag.sent')\" \"\$(cat '$SCRATCH/ts/$tag.done')\" \
             \"\$curl_exit\"
  "
  local flock_exit=$?
  if [ "$flock_exit" -ne 0 ]; then
    log "seq=$SEQ FAILED flock_exit=$flock_exit $host $path"
    echo "seq=$SEQ $host $path -> LOCK FAILURE (exit $flock_exit)"
    return 1
  fi

  local code nbytes sha t_sent t_done
  code=$(cat "$SCRATCH/ts/$tag.code" 2>/dev/null || echo 000)
  nbytes=$(wc -c < "$SCRATCH/bodies/$tag.b" 2>/dev/null | tr -d ' ' || echo 0)
  sha=$(sha256sum "$SCRATCH/bodies/$tag.b" 2>/dev/null | cut -d' ' -f1 || echo "(none)")
  t_sent=$(cat "$SCRATCH/ts/$tag.sent" 2>/dev/null || echo "(none)")
  t_done=$(cat "$SCRATCH/ts/$tag.done" 2>/dev/null || echo "(none)")
  local nrec
  nrec=$(python3 -c "
import json
try: print(json.load(open('$SCRATCH/ts/$tag.facts')).get('record_count'))
except Exception: print('?')")

  log "t_queued=$t_queued t_sent=$t_sent t_done=$t_done seq=$SEQ host_seq=$host_seq $host $path method=GET role=$role status=$code records=$nrec bytes=$nbytes sha=$sha"
  echo "seq=$SEQ $host $path -> $code rec=$nrec ${nbytes}B $tag"
  return 0
}

# A bare `read` loop drops a final line that has no trailing newline: `read`
# returns non-zero at EOF-without-newline, so the loop exits before dispatching
# it. Four of the previous pass's query files were affected and four queries
# were never sent. The guard counts the unterminated last line.
if [ "$(tail -c 1 "$QFILE" | wc -l)" -eq 0 ]; then
  log "WARN $(basename "$QFILE") has no trailing newline; a bare read loop would drop its last line"
fi

while IFS='|' read -r tag role host path extra || [ -n "${tag}${role}${host}${path}" ]; do
  case "$tag" in ''|\#*) continue ;; esac
  req "$tag" "$role" "$host" "$path" "$extra" || break
done < "$QFILE"

echo "done: $SEQ of a $CAP cap"