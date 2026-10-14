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
#
# Correction (2026-10-14, recorded rather than smoothed over): the first
# version of this script died at section C with exit 1. `set -euo pipefail`
# plus `grep -oiE "$PATTERN" file | wc -l` returns 1 whenever a file has no
# match — which is most of them — and pipefail propagates that into the script.
# Section A had `|| true` and survived; C did not, so the run printed a
# denominator and stopped, which is exactly the shape of a check that looks
# like it ran. Same family as the gate's own "an `ok` printed below its own
# `!!`" row in docs/09 section 4. Fixed by making the no-match case explicit.

set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

# ---------------------------------------------------------------- the phrases
# Taken verbatim from AGENTS.md section 2.1. The rule supplies the vocabulary;
# this pass does not get to widen it (AGENTS.md section 1: every claim must be
# traceable to a source, and the source for the word list is the rule itself).
# Longest-alternative-first: Perl alternation is first-match-wins, so the order
# is load-bearing, not cosmetic — it is what makes `corroborated independently`
# ONE occurrence instead of `corroborated` + `independently`.
ALL='double-sourced|verifies independently|corroborated independently|confirms independently|not contradicted by|consistent with|agrees with|independently|corroborated|confirms|supports'

# `grep -c` counts LINES; `grep -o | wc -l` counts OCCURRENCES. Both are
# printed because they are not the same number and quoting only one of them is
# how a denominator stops being re-derivable. grep exits 1 on "no match", which
# under -e aborts the script; `|| :` is the fix, not `|| true` on the whole run.
lines_in()   { grep -oiEc  "$ALL" "$1" 2>/dev/null || :; }
occurs_in()   { grep -oiE   "$ALL" "$1" 2>/dev/null | grep -c '' || :; }

echo '=== A. D1 — matching LINES per in-scope file (docs/*.md + README.md) ==='
for f in docs/*.md README.md; do printf '%s\t%s\n' "$f" "$(lines_in "$f")"; done

echo
echo '=== B. D2 — matching OCCURRENCES per in-scope file ==='
for f in docs/*.md README.md; do printf '%s\t%s\n' "$f" "$(occurs_in "$f")"; done

echo
echo '=== C. AGENTS.md — rule text, NOT claims. Reported separately. ==='
printf 'AGENTS.md\t%s lines\t%s occurrences\n' "$(lines_in AGENTS.md)" "$(occurs_in AGENTS.md)"

echo
echo '=== D. every hit, with location ==='
grep -oinE "$ALL" docs/*.md README.md AGENTS.md 2>/dev/null || :
grep -inE "$ALL" docs/*.md README.md 2>/dev/null || :

echo
echo '=== E. ledger accounting ==='
printf 'results.jsonl rows: %s\n' "$(grep -c '' findings-log/2026-10-14-pool-s-independence-audit/results.jsonl 2>/dev/null || :)"
echo 'requests issued: 0 of a 0 cap'
