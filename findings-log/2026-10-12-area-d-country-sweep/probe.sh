#!/usr/bin/env bash
# Area D — the country sweep, completed.
# Claim issue: https://github.com/NovaLux12/carelink-api-research/issues/22
#
# WHAT THIS SENDS, AND WHY EVERY ONE OF THEM IS JUSTIFIED
# ------------------------------------------------------
# Endpoint (recorded, not guessed):
#   GET https://carelink.minimed.eu/patient/countries/settings?countryCode=XX
#   -> 200 application/json, gzip, unauthenticated
#      (OBSERVED, docs/04-configuration.md:333)
#
# Candidate list: 118 country codes, derived OFFLINE from three vendor-published
# public-config documents by candidates.py in this directory — every 2-letter
# A-Z string appearing inside the value of a top-level key whose name contains
# "countr", unioned over carelink.minimed.eu / .com / carelink-trials.minimed.com.
# No code is guessed from a country name; ZZ is the one code NOT in that union
# and is sent only as the certainly-absent control. Full list, with provenance
# per code, in candidates.txt.
#
# Order is load-bearing: the four controls go FIRST, before any sweep.
#   1. GB  CONTROL-live        a country the repo records as served (docs/04:340)
#   2. BE  CONTROL-contradiction  the only internal contradiction the repo has
#   3. CH  CONTROL-contradiction  evidence for (docs/04:379). If these two come
#      back clean, the reader is wrong OR the drift was fixed, and either way
#      that has to be known at control time rather than after 114 requests.
#   4. ZZ  CONTROL-absent      the repo's recorded bogus code (docs/04:337) —
#      establishes what "not a supported country" looks like, so "key absent"
#      and "value null" can never be confused for one another.
#
# Constraints (claimed in #22, honoured here):
#   - GET only. No POST, no token exchange, no authentication, no api-key.
#     The only request header probe.sh adds is a User-Agent.
#   - >=2.5 s between requests to the same host, enforced by the per-host lock
#     with the SLEEP INSIDE THE LOCK (three other pool workers share this host
#     and this machine; outside the lock they would fire simultaneously).
#   - curl --compressed on every request: carelink.minimed.eu serves gzip
#     unconditionally, ignoring Accept-Encoding (AGENTS.md §7). Without it every
#     parse fails on 0x8b.
#   - CAP=130, enforced by counting before the request is issued. 119 are sent
#     (118 country codes + the ZZ control). The remaining 11 of the cap are the
#     hurl pin-validation requests named in #22; probe.sh refuses to use them.
#   - Refuses to run twice: results.jsonl / run.log already present -> exit 8.
#     The harness count cannot silently double.
#   - A response that fails to parse is NOT re-requested. Decompress locally.
#
# THREE TIMESTAMPS PER REQUEST, because three prior passes each recorded a
# same-host gap below the sleep their own harness declared (docs/09 §4):
#   t_queued  before the lock is taken   — comparable to prior passes' convention
#   t_sent    inside the lock, after the sleep, immediately before curl
#   t_done    immediately after curl returns
# Both gap series are measured in FINDINGS.md; neither is rounded away.

set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
BODY="$DIR/bodies"
HDR="$DIR/headers"
# The per-host lock lives in the MAIN clone, not in this worktree — all four
# pool workers take the same lock for this host, and the lock files are
# .gitignored beside the main checkout.
#
# This file is committed, so it must carry NO machine-specific absolute path
# (AGENTS.md §7; the gate greps for one and fails the PR). `git rev-parse
# --git-common-dir` is the one form that resolves correctly in BOTH layouts: in
# a plain clone it returns `.git` (relative, so the lock lands in ./.loop) and
# in a linked worktree it returns the MAIN clone's .git directory, whose parent
# is where the locks are. POOL_LOCK_DIR overrides both, for a re-run anywhere.
_gitdir="$(git -C "$DIR" rev-parse --git-common-dir 2>/dev/null)"
if [ -n "$_gitdir" ]; then
  POOL_LOCK_DIR="${POOL_LOCK_DIR:-$(dirname "$_gitdir")/.loop}"
else
  POOL_LOCK_DIR="${POOL_LOCK_DIR:-$DIR/../../../.loop}"
fi
LOCK="$POOL_LOCK_DIR/host-carelink.minimed.eu.lock"
CAP=130
UA="carelink-bridge-research/1.0 (area D, research)"
BASE="https://carelink.minimed.eu/patient/countries/settings"

if [ -s "$DIR/results.jsonl" ] || [ -s "$DIR/run.log" ]; then
  echo "REFUSING TO RE-RUN: results.jsonl or run.log already exists (exit 8)" >&2
  exit 8
fi
mkdir -p "$BODY" "$HDR"
: > "$DIR/run.log"
: > "$DIR/results.jsonl"
touch "$LOCK"

# run.log columns, so the spacing floor is re-derivable from the timestamps on
# disk without reading this script:
#   1 seq   2 cc   3 role   4 http_status   5 curl_exit
#   6 t_queued (before the lock)   7 t_sent (in-lock, after sleep, pre-curl)
#   8 t_done (curl returned)
# All timestamps ISO-8601 UTC with milliseconds.
printf '# seq\tcc\trole\thttp_status\tcurl_exit\tt_queued\tt_sent\tt_done\n' \
  > "$DIR/run.log"

n=0

req() { # req <cc> <role>
  local cc="$1" role="$2" tag="cc-$1"
  n=$((n + 1))
  if [ "$n" -gt "$CAP" ]; then
    echo "CAP $CAP REACHED at cc=$cc — exiting without issuing request $((n + 1))" >&2
    exit 9
  fi
  local queued url
  queued=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  url="$BASE?countryCode=$cc"
  flock "$LOCK" -c "
    sleep 2.5
    date -u +%Y-%m-%dT%H:%M:%S.%3NZ > '$HDR/$tag.sent'
    curl -s --compressed --max-time 30 -A '$UA' -D '$HDR/$tag.h' -o '$BODY/$tag.json' \
         -w '%{http_code}' '$url' > '$HDR/$tag.code' 2> '$HDR/$tag.err'
    echo \$? > '$HDR/$tag.cexit'
    date -u +%Y-%m-%dT%H:%M:%S.%3NZ > '$HDR/$tag.done'
  "
  local code cexit t_sent t_done
  code=$(cat "$HDR/$tag.code" 2>/dev/null || echo "(none)")
  cexit=$(cat "$HDR/$tag.cexit" 2>/dev/null || echo "(none)")
  t_sent=$(cat "$HDR/$tag.sent" 2>/dev/null || echo "(none)")
  t_done=$(cat "$HDR/$tag.done" 2>/dev/null || echo "(none)")
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$n" "$cc" "$role" "$code" "$cexit" "$queued" "$t_sent" "$t_done" >> "$DIR/run.log"
  printf '  %3d  %-3s %-26s %s (curl %s)\n' "$n" "$cc" "$role" "$code" "$cexit"
}

echo "--- area D: controls first ---"
req GB CONTROL-live
req BE CONTROL-contradiction
req CH CONTROL-contradiction
req ZZ CONTROL-absent

echo "--- area D: sweep ---"
# candidates.txt line 1-4 are comments; 5+ are CODE<TAB>provenance
while IFS=$'\t' read -r cc prov; do
  case "$cc" in \#*|"") continue ;; esac
  case "$cc" in GB|BE|CH) continue ;; esac   # already sent as controls
  req "$cc" "CANDIDATE($prov)"
done < "$DIR/candidates.txt"

echo "DONE n=$n (cap $CAP)" | tee -a "$DIR/run.log"