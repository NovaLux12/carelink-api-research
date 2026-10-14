#!/usr/bin/env bash
# probe.sh — area S independence audit (2026-10-14 pool run, worker S).
#
# THIS SCRIPT MAKES NO NETWORK REQUEST. There is no curl, no hurl, no fetch, no
# DNS lookup and no HTTP client on any line below. It is a static reader over
# this repository's own committed text.
#
# Cap: 0 requests. Method: GET (policy statement; no GET was issued). Delay:
# >=2 s between requests to the same host — vacuous at 0 requests.
#
# It is kept in the log so a reader can re-derive every number in FINDINGS.md
# with one command, rather than taking the prose on trust.

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# ---------------------------------------------------------------- the phrases
# Taken verbatim from AGENTS.md section 2.1. The rule supplies the vocabulary;
# this pass does not get to widen it (AGENTS.md section 1: every claim must be
# traceable to a source, and the source for the word list is the rule itself).
STRENGTH='independently|corroborated|corroborated independently|confirms|confirms independently|verifies independently|double-sourced'
COHERENCE='consistent with|supports|agrees with|not contradicted by'
# Longest-alternative-first so `corroborated independently` is ONE occurrence
# and not `corroborated` + `independently`. Perl alternation is first-match-wins,
# so the order below is load-bearing, not cosmetic.
ALL="double-sourced|verifies independently|corroborated independently|confirms independently|not contradicted by|consistent with|agrees with|independently|corroborated|confirms|supports"

PATTERN="($ALL)"

echo '=== A. per-file line counts, in-scope files (docs/*.md + README.md) ==='
for f in docs/*.md README.md; do
  printf '%s\t%s\n' "$f" "$(grep -oiEc "$PATTERN" "$f" || true)"
done

echo
echo '=== B. per-file line counts, rule text excluded by construction ==='
echo 'AGENTS.md is reported separately: its section 2.1 hits are the rule,'
echo 'not claims. See FINDINGS.md "Two denominators".'
for f in AGENTS.md; do
  printf '%s\t%s\n' "$f" "$(grep -oiEc "$PATTERN" "$f" || true)"
done

echo
echo '=== C. occurrence counts (not line counts), in-scope files ==='
for f in docs/*.md README.md; do
  n=$(grep -oiE "$PATTERN" "$f" 2>/dev/null | wc -l | tr -d ' ')
  printf '%s\t%s\n' "$f" "$n"
done

echo
echo '=== D. every matching line, with its location, in-scope files ==='
grep -oinE "$PATTERN" docs/*.md README.md || true

echo
echo '=== E. ledger accounting ==='
printf 'results.jsonl rows: %s\n' "$(grep -c '' findings-log/2026-10-14-pool-s-independence-audit/results.jsonl || true)"
echo 'requests issued: 0 of a 0 cap'
