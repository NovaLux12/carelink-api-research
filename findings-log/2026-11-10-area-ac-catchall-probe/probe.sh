#!/usr/bin/env bash
# probe.sh — area AC (claim #168): the ONE bounded live question the census could not answer.
#
#   Does carelink.minimed.eu run a catch-all on non-existent paths?  If it does, every
#   archived 404-vs-200 reading in this area's crawl record is uninterpretable and
#   "is /ipro/hcp/ retired" is unanswerable from crawl data at all.
#
# Host scope: carelink.minimed.eu ONLY. Zero requests to any other vendor host.
# Method: GET only. No POST, no OPTIONS, no token, no cookie, no wordlist.
# Delay: >= 2.5 s between same-host requests, slept INSIDE the per-host flock.
CAP=20
#   CAP=20, itemised before the first request:
#     1  control  /zz-ac-absent-20261110-probe.html          (fabricated apex path)
#     1  control  /robots.txt                                (recorded live 200, this family)
#     5  the five F10a shape paths (apex + four /app/assets nesting depths)
#     1  deepest-nesting duplicate (digest-stability check on a served path)
#     1  fabricated name at nested depth  (apex-vs-depth discriminator)
#     1  fabricated name at deepest nesting (depth-independence check)
#   = 10 planned rows; 10 held back for retries and the repository's own gate
#     traffic (~13 requests, which runs on every push).
#
# A failure (000, 5xx, 502/503/504/400) is a FAILURE, never an absence: it is
# re-issued, and every retry gets its own ledger row.
#
# Bodies are written OUTSIDE the repository (AGENTS.md section 7). Only status,
# content-type, bytes, sha256 and a short redacted body_head are committed.
#
# LITERAL GET: https://carelink.minimed.eu<path>   (curl --compressed, -D headers)

set -u
cd "$(dirname "$0")"

HOST=carelink.minimed.eu
: "${L_LOCK:?set L_LOCK to the absolute host-lock path}"
: "${L_BODIES:?set L_BODIES to an absolute scratch directory outside the repository}"
LOCK=$L_LOCK
BODIES=$L_BODIES
DELAY=2.5
MAXRETRY=1
LEDGER=results.jsonl
RUNLOG=run.log
HD=headers

mkdir -p "$HD" "$BODIES"
[ -s "$RUNLOG" ] || printf 'seq\trole\tpath\thttp\tcontent_type\tbytes\tsha256_16\tt_sent\tt_done\n' > "$RUNLOG"
now() { date -u +%FT%T.%3NZ; }

QF=${1:-queue.tsv}
while IFS=$'\t' read -r role path outname; do
  [ -z "${role:-}" ] && continue
  case "$role" in \#*) continue ;; esac
  case "${path:-}" in /*) : ;; *) printf 'REFUSED non-path line: %s\n' "$role" >> "$RUNLOG.refused"; continue ;; esac

  attempt=0
  while :; do
    used=$(wc -l < "$LEDGER" 2>/dev/null | tr -d ' '); used=${used:-0}
    if [ "$used" -ge "$CAP" ]; then
      printf 'CAP REACHED at %s of %s — queue abandoned.\n' "$used" "$CAP" >> "$RUNLOG.capped"; exit 0
    fi
    seq=$((used + 1))
    sfx=""; [ "$attempt" -gt 0 ] && sfx="-r$attempt"
    tag="$outname$sfx"
    h="$HD/$seq-$tag.h"; b="$BODIES/$seq-$tag.body"
    tq=$(now)
    flock "$LOCK" -c "sleep $DELAY; curl -sS --compressed --max-time 45 -D '$h' -o '$b' -w '%{http_code}' 'https://$HOST$path' > '$BODIES/$seq-$tag.code' 2> '$BODIES/$seq-$tag.err'"
    ts=$(now)
    code=$(tr -d '\r\n' < "$BODIES/$seq-$tag.code" 2>/dev/null); [ -z "$code" ] && code="000"
    td=$(now)
    python3 row.py "$seq" "$role" "$path" "$tag" "$h" "$b" "$code" "$tq" "$ts" "$td"
    case "$code" in
      200|301|302|403|404|410) : ;;
      *) if [ "$attempt" -lt "$MAXRETRY" ]; then attempt=$((attempt + 1)); continue; fi ;;
    esac
    break
  done
done < "$QF"
printf 'DONE — %s requests of a %s cap.\n' "$(wc -l < "$LEDGER" | tr -d ' ')" "$CAP" >> "$RUNLOG.capped"
