#!/usr/bin/env bash
# probe.sh — area R, pool run 2026-10-14. ZERO requests.
#
# There is no probe in this pass. `deviceFamily`'s wire casing is token-gated
# (VALIDATION-RUNBOOK Tier 1) and this pass does not attempt to observe it. The
# script below therefore performs NO network call of any kind: no DNS, no TCP,
# no TLS, no HTTP. It has no curl/wget/nc invocation and no host list, because a
# candidate list is what a probe has and this pass has none.
#
# What it does do is re-derive the candidate vocabulary from committed artefacts,
# so the denominator this pass publishes is checkable from a clean clone.
#
# Safe to run from ANY working directory: DIR is derived from this script's own
# location, and count-candidates.py resolves its paths against the repository
# root found by walking up from ITSELF. Verified from the repo root, from this
# directory, and from a clean `git archive` export.
#
# Method space: GET was the only method available to this project (AGENTS.md §8).
# It was NOT used — there is no request. The word appears here only because the
# accounting format requires the method to be named, as in the 2026-10-11
# third-party pass.
#
# Inter-request delay: the project floor is ≥2s between requests to the same
# host. It is vacuous at zero requests and is recorded rather than paraphrased
# away.
#
# Accounting: 0 rows in results.jsonl, matching "0 of a 0 cap" in FINDINGS.md.

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$DIR/results.jsonl"
LOG="$DIR/run.log"
METHOD="GET (not used — no request was made)"
DELAY=">=2s (vacuous at 0 requests)"
CAP=0

: > "$OUT"

# Build into a scratch file and move it into place ONLY on success. A child that
# fails must never leave a truncated ledger behind: a half-written run.log is
# indistinguishable from a short run, which is the defect this guard exists to
# stop (round 5: running this script from its own directory produced an 8-line
# run.log holding an error message).
TMP="$DIR/.run.log.tmp"
trap 'rm -f "$TMP"' EXIT

{
  echo "# run.log — area R, pool run 2026-10-14"
  echo "# host: none (no vendor host is contacted by this pass)"
  echo "# method: $METHOD"
  echo "# inter-request delay: $DELAY"
  echo "# cap: $CAP"
  echo "# started: $(date -u +%FT%TZ)"
  echo "# --- offline re-derivation begins (no network syscall is issued below) ---"
  python3 "$DIR/count-candidates.py"
  echo "# --- offline re-derivation ends ---"
} > "$TMP" 2>&1 || {
  echo "probe.sh: count-candidates.py failed; run.log left untouched" >&2
  cat "$TMP" >&2
  exit 1
}

mv "$TMP" "$LOG"
trap - EXIT

rows=$(grep -c . "$OUT" || true)
if [ "$rows" -ne 0 ]; then
  echo "probe.sh: results.jsonl has $rows rows; a zero-request pass must have 0" >&2
  exit 1
fi

echo "probe.sh: 0 requests of a $CAP cap; results.jsonl rows = $rows"
echo "probe.sh: run.log -> $LOG"