#!/usr/bin/env bash
# probe.sh — pool L, area L (claim #126): ipro/hcp census over Common Crawl.
#
# Host scope: index.commoncrawl.org ONLY. Zero requests to any Medtronic host.
# Method: GET only. No POST, no authentication, no token exchange.
# Delay: >= 3.5 s between requests to the same host, held INSIDE flock.
# Cap: 200 (continuation of area L; the area total is 240). Every attempt is a request and every attempt gets a ledger row,
#       retries included (this API fails 28-41% of its queries).
#
# Usage: ./probe.sh <queue-file>
# Queue line: <role><TAB><host_tag><TAB><path><TAB><outname>
#
# Bodies are written OUTSIDE the repository (AGENTS.md §7: >=1 MiB fails the
# hygiene check; raw archive captures are never published). Headers and the
# ledger stay in the tree.

set -u
cd "$(dirname "$0")"

HOST=index.commoncrawl.org
# Two absolute paths, taken from the environment and never written here: the
# host lock lives in the pool's `.loop/` directory, which is OUTSIDE this
# worktree, and bodies must live outside the repository (AGENTS.md section 7).
# No literal home path may be committed, so both are required inputs.
: "${L_LOCK:?set L_LOCK to the absolute host-lock path, e.g. <pool-root>/.loop/host-<host>.lock}"
: "${L_BODIES:?set L_BODIES to an absolute scratch directory outside the repository}"
LOCK=$L_LOCK
CAP=200
DELAY=3.5
MAXRETRY=2
BODIES=$L_BODIES
LEDGER=results.jsonl
RUNLOG=run.log
HD=headers
ROWPY=project-row.py

mkdir -p "$HD" "$BODIES"
[ -s "$LEDGER" ] || : > "$LEDGER"
[ -s "$RUNLOG" ] || printf 'seq\trole\thost_tag\tpath\thttp\tbytes\trecords\tipro\tminimed_hosts\tt_queued\tt_sent\tt_done\n' > "$RUNLOG"

now() { date -u +%FT%T.%3NZ; }
sent_rows() { wc -l < "$LEDGER" | tr -d ' '; }

# A 502/504/503/400 is a FAILURE on this API, never an absence (docs/09 §4).
is_failure() {
  case "$1" in
    200|301|302|404|"") return 1 ;;
    *) return 0 ;;
  esac
}

QF="$1"
while IFS=$'\t' read -r role host_tag path outname; do
  [ -z "${role:-}" ] && continue
  case "$role" in \#*) continue ;; esac

  attempt=0
  while :; do
    used=$(sent_rows)
    if [ "$used" -ge "$CAP" ]; then
      printf 'CAP REACHED at %s of %s — queue abandoned.\n' "$used" "$CAP" >> "$RUNLOG.capped"
      exit 0
    fi
    seq=$((used + 1))
    sfx=""; [ "$attempt" -gt 0 ] && sfx="-r$attempt"
    tag="$outname$sfx"
    h="$HD/$seq-$tag.h"
    b="$BODIES/$seq-$tag.body"
    tq=$(now)

    # The sleep lives INSIDE the lock: two passes on the same host must not
    # both sleep and then send together.
    flock "$LOCK" -c "sleep $DELAY; curl -sS --max-time 60 -D '$h' -o '$b' -w '%{http_code}' 'https://$HOST$path' > '$BODIES/$seq-$tag.code' 2> '$BODIES/$seq-$tag.err'"
    ts=$(now)
    code=$(tr -d '\r\n' < "$BODIES/$seq-$tag.code" 2>/dev/null)
    [ -z "$code" ] && code="000"
    td=$(now)

    python3 "$ROWPY" "$LEDGER" "$RUNLOG" "$seq" "$role" "$host_tag" "$path" "$tag" "$h" "$b" "$code" "$tq" "$ts" "$td"

    if is_failure "$code" && [ "$attempt" -lt "$MAXRETRY" ]; then
      attempt=$((attempt + 1))
      continue
    fi
    break
  done
done < "$QF"
printf 'DONE — %s requests of a %s cap.\n' "$(sent_rows)" "$CAP" >> "$RUNLOG.capped"