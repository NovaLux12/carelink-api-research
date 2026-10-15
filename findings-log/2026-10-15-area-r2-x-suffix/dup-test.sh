#!/bin/bash
# dup-test.sh — the grep-first duplicate test, re-runnable, for the three successors
# of docs/11 successor 2 (issue #132).  CONTRIBUTING-research.md:196 requires it.
#
# 0 requests. Reads the working tree only.
#
# WHY THIS IS A SCRIPT AND NOT A TRANSCRIPT OF COUNTS.
#   Round 1 recorded bare counts ("7 hits for 45559 in docs/11"). Round 2 of
#   verification found all three of those counts had gone stale in the very commit
#   that invalidated them: this pass edited docs/11 in six hunks and did not re-run
#   or re-state them. Re-running and pasting new numbers would fix one instance of a
#   bug that fires every time this file is edited — and four lanes in this pool edit
#   docs/11 simultaneously, so the numbers move under this pass whether or not it
#   touches them. So every count below is printed together with the commit it was
#   taken on, and re-deriving the count on a different tree is expected to differ.
#   THE VERDICTS ARE THE FINDING; THE COUNTS ARE A PROPERTY OF A NAMED TREE.
#
#   A count that names the tree it was taken on is re-derivable. A count that says
#   "this branch's head" is a promise about a moving object (AGENTS.md section 1).
#
# TWO TABLES ANSWER "the Closed table" — NAMED EXPLICITLY HERE, because round 2 found
# that the bare placeholder <Closed table> is ambiguous and the two disagree:
#     T1  docs/10-open-questions.md  section 2, "Searched and closed — do not re-run"
#     T2  docs/11-suggested-research-areas.md, section "Closed areas" (the row table)
#   For 45559 / BLE_X / false-positive / Samsung these read 0/0/0/0 and 1/1/1/0. Both
#   are tested; neither is assumed.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
# NOT a ../../../.. guess. This file sits under findings-log/, but the checkout may
# be the primary worktree or a pool worktree nested several levels down, and a wrong
# root here produced ALL ZEROS SILENTLY in the first run of this script — the exact
# failure mode AGENTS.md section 6 item 3 names, reached by a different road. Ask git.
REPO="$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null)" || REPO=""
[ -n "$REPO" ] || { echo "FATAL: cannot resolve the repository root from $HERE" >&2; exit 2; }
cd "$REPO" || exit 2

# A missing or empty subject must be LOUD. `grep -c` on an unreadable file prints 0,
# and a column of zeros is indistinguishable from a real result.
for f in docs/10-open-questions.md docs/11-suggested-research-areas.md \
         docs/05-devices-and-vocabulary.md docs/09-methodology-and-oracles.md; do
  [ -r "$f" ] || { echo "FATAL: subject not readable: $f (root $REPO)" >&2; exit 2; }
done

echo "=============================================================================="
echo "DUP-TEST — counted at a NAMED COMMIT, not at a moving head"
echo "=============================================================================="
echo "  repo          : $REPO"
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  SHA="$(git rev-parse HEAD)"
  BR="$(git rev-parse --abbrev-ref HEAD)"
  echo "  HEAD          : $SHA   (branch $BR)"
  echo "  tree counted  : the working tree as of the line above."
  echo "  NOTE          : any later commit touching docs/10 or docs/11 — INCLUDING"
  echo "                  this pass's own hunks, and including any other lane's, since"
  echo "                  four lanes edit docs/11 in this pool — CAN move these counts:"
  echo "                  a count is evidence only at the SHA printed above. (Measured,"
  echo "                  not assumed: merging all four pool lanes moved none of them —"
  echo "                  see FINDINGS.md section 10's merge-order note. That is a"
  echo "                  result for these four passes, not a guarantee for the next"
  echo "                  edit.) Re-run this script and cite the new SHA; do not carry"
  echo "                  a count forward un-pinned."
else
  echo "  HEAD          : (no git — counts below are unpinned and should not be cited)"
fi
echo "  requests      : 0"
echo

t1=$(awk '/^## 2\. Searched and closed/,/^## 3\./' docs/10-open-questions.md)
t2=$(awk '/^## Closed areas/,0' docs/11-suggested-research-areas.md)

probe() { # probe <label> <needle> <table-text> <table-name>
  local n; n=$(printf '%s' "$3" | grep -c -- "$2")
  printf '  %-46s %-16s : %s\n' "$1" "$2" "$n"
}

echo "  ---- (a) the patient lazy corpus, for module 45559 and _X reads ----"
probe "docs/10 section 1 (open questions)"   "45559" "$(sed -n '/^## 1\./,/^## 2\./p' docs/10-open-questions.md)" "docs10s1"
probe "docs/10 section 1 (open questions)"   "BLE_X" "$(sed -n '/^## 1\./,/^## 2\./p' docs/10-open-questions.md)" "docs10s1"
probe "T1 docs/10 section 2 (Searched/closed)" "45559" "$t1" "t1"
probe "T1 docs/10 section 2 (Searched/closed)" "BLE_X" "$t1" "t1"
probe "T2 docs/11 Closed areas"             "45559" "$t2" "t2"
probe "T2 docs/11 Closed areas"             "BLE_X" "$t2" "t2"
probe "docs/11 whole page"                  "45559" "$(cat docs/11-suggested-research-areas.md)" "d11"
echo
echo "  ---- (b) the false-positive class, as offsets ----"
probe "docs/10 whole file"                  "false-positive" "$(cat docs/10-open-questions.md)" "d10"
probe "docs/10 whole file"                  "false positive" "$(cat docs/10-open-questions.md)" "d10"
probe "T2 docs/11 Closed areas"             "false-positive" "$t2" "t2"
probe "docs/11 whole page"                  "false-positive" "$(cat docs/11-suggested-research-areas.md)" "d11"
probe "docs/09 section 4 (THE TRAP LIST — the register successor (b) names)" \
      "BLE" "$(awk '/^## 4\. The trap list/,/^## 5\./' docs/09-methodology-and-oracles.md)" "d09s4"
echo
echo "  ---- (c) the NGP figure that does not reproduce ----"
probe "docs/09 whole file"                  "Samsung" "$(cat docs/09-methodology-and-oracles.md)" "d09"
probe "docs/05 whole file"                  "Samsung" "$(cat docs/05-devices-and-vocabulary.md)" "d05"
probe "docs/10 whole file"                  "Samsung" "$(cat docs/10-open-questions.md)" "d10"
probe "T1 docs/10 section 2 (Searched/closed)" "Samsung" "$t1" "t1"
probe "T2 docs/11 Closed areas"             "Samsung" "$t2" "t2"
probe "docs/11 whole page"                  "Samsung" "$(cat docs/11-suggested-research-areas.md)" "d11"
echo
echo "  ---- docs/09 section 5 item 2 — does the register already cite this token? ----"
S5="$(awk '/^## 5\. Verification discipline/,/^## 6\./' docs/09-methodology-and-oracles.md)"
if printf '%s' "$S5" | grep -q 'Samsung'; then
  printf '  YES. docs/09 section 5 already carries the NGP/Samsung claim under the\n'
  printf '       "a grep that hit without proving" class:\n'
  printf '%s' "$S5" | grep -o "Samsung[^\"]\{0,90\}" | head -2 | sed 's/^/         /'
else
  echo "  NO — docs/09 section 5 does not mention Samsung. The register may be"
  echo "  elsewhere; do not read this line as the token being absent from the repo."
fi
echo
echo "REMINDER: counts are evidence of WHERE to look; the per-hit verdicts in"
echo "FINDINGS.md section 10 are the finding, and those were confirmed in"
echo "verification round 2 and are unaffected by a count moving."
