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
#
# Correction (2026-10-15): the pattern below was still missing the left word
# boundary, so this script did NOT reproduce FINDINGS.md's denominator while
# hits.py did — probe.sh read 68 occurrences / 47 lines where hits.py read
# 63 / 44 on the same tree, and the 5-occurrence gap was `disagrees with`
# matching `agrees with`. The three commits on this branch (5bfdb6c, d85634b,
# 9e82ecf) all carried the un-boundaried string; 9e82ecf, titled "fix the
# population table to the corrected pattern, keep the error", edited
# FINDINGS.md and hits.txt and not this file. A fix that corrects the table and
# leaves the tool that prints it wrong is not a fix.
#
# Correction (2026-10-15, round 2): the first version of the note above blamed
# this on GNU grep rejecting `(?:...)` "silently dropping the rest". That
# explanation was fabricated, labelled "verified" on a transcript that did not
# support it, and it has been withdrawn — probe.sh never contained `(?:` at any
# commit. The boundary was never written. See the `## Correction (2026-10-15)`
# section, C7, in FINDINGS.md for the measurement and for what grep actually
# does.
#
# WHAT IT MEASURES: the CHECKED-OUT WORKING TREE, not origin/main. After this
# branch's own edits the in-scope total is 63 occurrences / 44 lines
# (FINDINGS.md section 1a). The section 1 table — 68 / 49, measured before the
# edits — is re-derived at origin/main with:
#     git worktree add /tmp/s-at-main origin/main && bash probe.sh
# or, without a second checkout:
#     git stash && bash probe.sh && git stash pop
# Both figures are printed by section A + B below.

set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

# ---------------------------------------------------------------- the phrases
# Taken verbatim from AGENTS.md section 2.1. The rule supplies the vocabulary;
# this pass does not get to widen it (AGENTS.md section 1: every claim must be
# traceable to a source, and the source for the word list is the rule itself).
# Longest-alternative-first: Perl alternation is first-match-wins, so the order
# is load-bearing, not cosmetic — it is what makes `corroborated independently`
# ONE occurrence instead of `corroborated` + `independently`.
#
# `\b` before EVERY alternative. It is what stops `agrees with` matching inside
# `disagrees with` — the opposite word — which the first pattern matched in three
# places (FINDINGS.md section 0-M). The boundary was NEVER written here: this
# file has carried an un-boundaried pattern at every commit it has existed
# (5bfdb6c, d85634b, 9e82ecf — verified 2026-10-15 with `git show <c>:<path>`,
# 0 hits for `(?:` in all three). That is the whole cause; see the correction
# below for what a `(?:...)` spelling would and would not have done under grep.
#
# The spelling is per-alternative rather than hits.py's `\b(?:...)` because
# GNU `grep -E` does not implement non-capturing groups. Measured 2026-10-15,
# not assumed:
#     $ printf 'alpha agrees with beta\n' > a.txt
#     $ grep -oiE '\b(?:agrees with)' a.txt
#     grep: warning: ? at start of expression
#     exit=1                      <- the alternative straight after `(?:` never matches
#     $ grep -oiE '\bagrees with' a.txt
#     agrees with ; exit=0
# It does not "silently drop the rest": the alternative immediately after `(?:`
# becomes unmatchable and alternatives 2..n still match. Run over docs/ + README
# with the full eleven-phrase list, the `(?:...)` spelling returns 60
# occurrences against this file's 63 — the 3 lost being `double-sourced`, which
# is the FIRST alternative. So the two spellings are NOT interchangeable and
# the counts above are what proves it.
#
# Repeating `\b` per alternative is the grep spelling of hits.py's pattern: the
# engine asserts a word boundary at the match start whichever alternative it
# then takes. Verified to give hits.py's figures exactly — 63 / 44 in scope at
# this branch's head, 68 / 49 at origin/main 7d915b8, `AGENTS.md` 14 / 7 both.
ALL='\bdouble-sourced|\bverifies independently|\bcorroborated independently|\bconfirms independently|\bnot contradicted by|\bconsistent with|\bagrees with|\bindependently|\bcorroborated|\bconfirms|\bsupports'

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
