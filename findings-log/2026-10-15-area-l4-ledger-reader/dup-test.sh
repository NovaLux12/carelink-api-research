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
cd "$(dirname "$0")/../.." || exit 1

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
echo "   docs/11 Closed table begins at line $CLOSED; row L is at"
echo "   $(grep -n '^| L — recovery of the retired' docs/11-suggested-research-areas.md | cut -d: -f1)"
echo "   while 2170 (the line round 1 wrongly cited) reads:"
printf '     %s\n' "$(sed -n '2170p' docs/11-suggested-research-areas.md | cut -c1-64)"
echo
echo "exit 0 — this script reports; the reading of it is the reviewer's."