#!/bin/sh
# dup-test.sh — the NON-DUPLICATE test `CONTRIBUTING-research.md:199` requires for
# every successor, run for real, with the commands and their results recorded.
#
#     sh dup-test.sh          # exit 0 always; read the table
#
# The bar it enforces: "it is already in `docs/10` section 1, already in the
# Closed table, or already on the page — grep both first". A successor that
# cannot be shown to be non-duplicate fails the bar, and an absence that the bar
# asks to be recorded is itself the finding when it is not recorded.
#
# SCOPE NOTE: this tests whether a successor's SUBJECT is already recorded
# somewhere. It cannot prove novelty — docs/10 section 2 ("Searched and closed")
# is a second surface the grep below deliberately does not claim to cover, and a
# re-derivation is welcome per CONTRIBUTING-research.md:212. Where a hit is a
# PARTIAL overlap rather than a duplicate, the table says so.

set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE/../.." || exit 1

# Where the Closed table starts, derived rather than remembered — a hardcoded
# line number here is exactly the defect this file exists to catch.
CLOSED=$(grep -n '^## Closed areas' docs/11-suggested-research-areas.md | cut -d: -f1)
S10_S1_START=$(grep -n '^## 1\. Open questions' docs/10-open-questions.md | cut -d: -f1)
S10_S2_START=$(grep -n '^## 2\. Searched and closed' docs/10-open-questions.md | cut -d: -f1)

echo "dup-test.sh — the non-duplicate test, run against docs/10 section 1,"
echo "the docs/11 Closed table, and docs/11 itself."
echo
echo "  docs/10 section 1 spans   lines $S10_S1_START .. $((S10_S2_START - 1))"
echo "  docs/11 Closed table      begins at line $CLOSED"
echo "  (both derived by grep above, never typed in)"
echo

# grep_subject LABEL PATTERN -- greps three surfaces and reports each count.
grep_subject() {
  label="$1"; pat="$2"
  d10=$(awk -v a="$S10_S1_START" -v b="$S10_S2_START" 'NR>=a && NR<b' docs/10-open-questions.md | grep -ci "$pat" || true)
  d11=$(grep -ci "$pat" docs/11-suggested-research-areas.md || true)
  cl=$(awk -v a="$CLOSED" 'NR>=a' docs/11-suggested-research-areas.md | grep -ci "$pat" || true)
  printf '  %-11s %-26s docs/10 s1=%-3s docs/11=%-3s Closed=%-3s\n' "$label" "$pat" "${d10:-0}" "${d11:-0}" "${cl:-0}"
}

echo "-- S-L4a  the member tally's window basis (census-84.txt:168 lists an out-of-window crawl)"
grep_subject S-L4a "window basis"
grep_subject S-L4a "CC-MAIN-2022-27"
echo
echo "-- S-L4b  member counts as floors / truncation / 'computed, found none'"
grep_subject S-L4b "members_computed"
grep_subject S-L4b "floor"
grep_subject S-L4b "truncat"
echo
echo "-- S-L4c  one reader for the other committed ledgers"
grep_subject S-L4c "one reader"
grep_subject S-L4c "schema"
echo
echo "-- S-L4d  'absent from 65 of the 84' reconciling with neither reading"
grep_subject S-L4d "65 of the 84"
grep_subject S-L4d "absent from"
echo
echo "-- The exact line pointers this pass cites, verified by grep FIRST."
echo "   (round 2 of the verifier found docs/11:2170 pointed at an unrelated"
echo "    area-F passage; the real second instance is the Closed-table row L)"
echo "   Every docs/11 line number below is re-derived by grep, never typed in."
echo "   Files carrying the sentence, with their line numbers:"
grep -rn 'absent from 65 of the 84' docs/ | cut -d: -f1,2 | while IFS=: read -r f ln; do
  printf '     %-40s :%s\n' "$f" "$ln"
done
echo "   (docs/11 hits: $(grep -n 'absent from 65 of the 84' docs/11-suggested-research-areas.md | cut -d: -f1 | tr '\n' ' '))"
echo "   (docs/10 hits: $(grep -n 'absent from 65 of the 84' docs/10-open-questions.md | cut -d: -f1 | tr '\n' ' '))"
echo
echo "   Verifying each one actually contains the sentence:"
for spec in docs/10-open-questions.md docs/11-suggested-research-areas.md; do
  for ln in $(grep -n 'absent from 65 of the 84' "$spec" | cut -d: -f1); do
    printf '     %-40s :%-5s %s\n' "$spec" "$ln" "$(sed -n "${ln}p" "$spec" | grep -o 'absent from 65 of the 84' | head -1)"
  done
done
echo
echo "   docs/11 Closed table begins at line $CLOSED; Closed row L is at"
echo "   $(grep -n '^| L — recovery of the retired' docs/11-suggested-research-areas.md | cut -d: -f1)"
echo
echo "   Stale-pointer check. Round 1 cited line 2170 for the Closed-table instance;"
echo "   round 2 published 2218; round 3 found 2218 stale and this pass publishes NO"
echo "   docs/NN:NNNN pointer at all. Here is what each earlier number actually reads"
echo "   at THIS commit — the check that would have caught the bad citation:"
for ln in 2170 2218 2232 2236; do
  printf '     :%s -> %s\n' "$ln" "$(sed -n "${ln}p" docs/11-suggested-research-areas.md | cut -c1-66)"
done
echo
echo "   FINDINGS.md must publish no docs/NN:NNNN pointer into docs/10 or docs/11"
echo "   OUTSIDE its two '## Correction' sections, which quote them as history —"
echo "   AGENTS.md §5 requires corrections preserved, and a record that deleted the wrong"
echo "   number would destroy the evidence it records. So the check excludes those:"
LOG="$HERE/FINDINGS.md"
HITS=$(awk '/^## 8a/ {skip=1} !skip {print NR": "$0}' "$LOG" \
       | grep -E 'docs/(10|11)[^ ]*:[0-9]+')
if [ -z "$HITS" ]; then
  echo "     none outside the Correction sections — pass"
else
  echo "$HITS" | sed 's/^/     STALE: /'
fi
echo "     (the Correction sections this excludes begin at: $(grep -n '^## 8a' "$LOG" | cut -d: -f1 | tr '\n' ' '))"
echo
echo "exit 0 — this script reports; the reading of it is the reviewer's."