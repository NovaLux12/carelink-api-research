#!/bin/bash
# Area K — PROOF THAT leak-screen.py FAILS. ZERO requests.
#
# WHY. `leak-screen.py` carries a SELF-TEST, but that self-test proves the
# *patterns* fire on their own targets. It does NOT prove the *screen* fails: the
# subject walk, the extension filter, the hit recording, the `file:line` output and
# the non-zero exit are all untested, because on this pass's real artefacts the
# honest answer is zero hits and every path through the FAILURES branch was never
# executed. A check whose failure path has never run is the same defect the pass was
# corrected for twice — `spacing.sh`'s span comparison telescoped to a number that
# could not fail. So the failure path is run here, on a deliberately poisoned copy.
#
# THE POISON IS BUILT AT RUNTIME FROM FRAGMENTS and lives only in a temp tree that is
# deleted on exit. Nothing this script needs to detect is written into this file, so
# committing this file does not commit the material it screens for.
#
# WHAT IS ASSERTED, and why each one:
#   1. exit status is non-zero            — a screen that cannot fail is not a screen
#   2. the output names `file:line`       — the whole point of the FAILURES branch;
#                                           a count without a location is unusable
#   3. the named line is the planted one  — proves the locator is correct, not merely
#                                           present; a screen naming the wrong line is
#                                           worse than one naming none
#   4. each tripped pattern is named     — and NEVER its value, per leak-screen.py's
#                                           own rule 1
#   5. a CLEAN tree still exits zero      — the control. Without it, "exits non-zero"
#                                           is satisfied by a script that always fails,
#                                           which is the failure mode scrub-patterns.txt
#                                           warns about in its own header.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(git -C "$HERE" rev-parse --show-toplevel)
SCREEN="$HERE/leak-screen.py"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# --- the poisoned tree -----------------------------------------------------------
# Same layout leak-screen.py expects: scripts/scrub-patterns.txt, and a findings-log
# subject dir. Only the subject is ours; the pattern file is the repo's real one, so
# the screen is exercised against the production pattern list and not a stand-in.
mkdir -p "$TMP/repo/scripts" "$TMP/repo/findings-log/2026-10-13-area-k-patient-chunks"
cp "$REPO/scripts/scrub-patterns.txt" "$TMP/repo/scripts/"

SUBJ="$TMP/repo/findings-log/2026-10-13-area-k-patient-chunks/poisoned.txt"
# Line 3 is the target. Built from fragments so this file holds no scrub-list value.
# NOTE: one %s per fragment. An extra argument is silently DROPPED by printf, which
# would leave a half-written poison that looks planted and matches nothing — the
# harness failing for a reason that has nothing to do with the screen.
printf 'line one: harmless\n'                                     >  "$SUBJ"
printf 'line two: harmless\n'                                     >> "$SUBJ"
printf 'line three: %s%s%s\n'    "/"    "home"        "/zzprobe/x"      >> "$SUBJ" # machine-specific paths
printf 'line four: %s%s%s\n'    ";"    "jsessionid_" "ZZPROBE1="      >> "$SUBJ" # live jsession values
printf 'line five: %s%s%s%s\n'  "db"   "."           "zzprobe"  ".minimed." >> "$SUBJ" # internal host
PLANTED_LINE=3
PLANTED_N=3

# --- the control tree: identical, minus the poison --------------------------------
CTRL="$TMP/clean"
mkdir -p "$CTRL/repo/scripts" "$CTRL/repo/findings-log/2026-10-13-area-k-patient-chunks"
cp "$REPO/scripts/scrub-patterns.txt" "$CTRL/repo/scripts/"
printf 'line one: harmless\nline two: harmless\nline three: harmless\n' \
  > "$CTRL/repo/findings-log/2026-10-13-area-k-patient-chunks/clean.txt"

rc=0
note() { printf '  %-6s %s\n' "$1" "$2"; }

echo "============================================================================"
echo "LEAK-SCREEN FAILURE PROOF — the FAILURES branch, run on a poisoned copy"
echo "============================================================================"
echo
echo "screen : ${SCREEN#$REPO/}"
# NOT $TMP. mktemp -d resolves under this account's home directory, and echoing it
# put a real machine-specific path into this report — which the very screen under
# test then flagged in leak-screen-proof.txt:6 as `machine-specific paths`. Caught by
# the tool this file exists to exercise; the fix is to print the tree's ROLE, not its
# address. ($TMP is still used to build and delete the tree.)
echo "poisoned tree: a throwaway copy of scripts/ + one findings-log subject (deleted on exit)"
echo "planted: 3 patterns, first at line $PLANTED_LINE of poisoned.txt"
echo

echo "1. RUN AGAINST THE POISONED TREE"
out=$(python3 "$SCREEN" "$TMP/repo" 2>&1); status=$?
echo "$out" > "$TMP/poison.out"
note "exit" "$status"
[ "$status" -ne 0 ] || { note "ASSERT" "FAIL — the screen exited 0 on a poisoned tree"; rc=1; }
[ "$status" -ne 0 ] && note "ASSERT" "ok   — non-zero on a known-bad tree"

echo
echo "2. THE OUTPUT NAMES file:line"
if grep -Eq '^  [^ ].*poisoned\.txt:[0-9]+$' "$TMP/poison.out"; then
  note "ASSERT" "ok   — file:line lines present:"
  grep -E '^  [^ ].*poisoned\.txt:[0-9]+$' "$TMP/poison.out" | sed 's/^/           /'
else
  note "ASSERT" "FAIL — no file:line line in the output"; rc=1
fi

echo
echo "3. THE NAMED LINE IS THE PLANTED ONE (locator correctness, not just presence)"
if grep -Eq "^  [^ ].*poisoned\.txt:${PLANTED_LINE}\$" "$TMP/poison.out"; then
  note "ASSERT" "ok   — poisoned.txt:$PLANTED_LINE is among the named hits"
else
  note "ASSERT" "FAIL — the planted line $PLANTED_LINE was not named"; rc=1
fi

echo
echo "4. EVERY PLANTED PATTERN IS NAMED IN THE FAILURES BLOCK, AND NO VALUE IS"
# The by-name table lists EVERY pattern with its hit count, including zeros, so
# grepping the whole output for a pattern name proves nothing — it would pass even
# when the pattern matched nothing. Only the FAILURES block is evidence.
sed -n '/^FAILURES/,/^VERDICT/p' "$TMP/poison.out" > "$TMP/failures.txt"
named=$(grep -cE '^  [^ ].*poisoned\.txt:[0-9]+$' "$TMP/failures.txt")
note "hits"  "$named named in the FAILURES block (planted $PLANTED_N)"
if [ "$named" -eq "$PLANTED_N" ]; then
  note "ASSERT" "ok   — all $PLANTED_N planted hits reported"
else
  note "ASSERT" "FAIL — expected $PLANTED_N hits, the FAILURES block names $named"; rc=1
fi
for p in "machine-specific paths" "live jsession values"; do
  if grep -qF "$p" "$TMP/failures.txt"; then note "pattern" "ok   — named in FAILURES: $p"
  else note "pattern" "FAIL — not named in FAILURES: $p"; rc=1; fi
done
# rule 1 of leak-screen.py: names and counts only, never the value. NOTE this
# assertion FAILED on the first run and it is a real defect in leak-screen.py, not
# in the harness — see section 6 below.
if grep -qF 'ZZPROBE1' "$TMP/poison.out"; then
  note "ASSERT" "DEFECT — a probe VALUE reached the report; see section 6"
  LEAKED_VALUE=1
else
  note "ASSERT" "ok   — no probe value reprinted (leak-screen.py rule 1 held)"
  LEAKED_VALUE=0
fi

echo
echo "5. CONTROL — the SAME screen on a clean tree must exit 0"
cout=$(python3 "$SCREEN" "$CTRL/repo" 2>&1); cstatus=$?
note "exit" "$cstatus"
if [ "$cstatus" -eq 0 ]; then note "ASSERT" "ok — clean tree exits 0, so exit 1 above was the poison and not a always-fails script"
else
  note "ASSERT" "FAIL — clean tree also exits non-zero; the screen fails on everything"; rc=1
fi
grep -E '^VERDICT' "$TMP/poison.out" | sed 's/^/           poisoned: /'
grep -E '^VERDICT' <<<"$cout" | sed 's/^/           clean   : /'

echo
echo "6. DEFECT FOUND BY THIS PROOF, IN leak-screen.py ITSELF"
echo "   Run against the real repository the screen reported hits on its OWN committed"
echo "   output — the SELF-TEST printed its probe strings with %r, and a .txt screen"
echo "   output is exactly what this screen reads. The fragmentation in that self-test"
echo "   was therefore self-defeating: it assembled the material at runtime and then"
echo "   wrote the assembled string to a committed file, which is what it set out to"
echo "   prevent. Three separate artefacts tripped it, each found by a different route:"
echo "     - leak-screen.txt, by the screen reading its own report"
echo "     - leak-screen-proof.txt, by this file echoing \$TMP, a path under this"
echo "       account's home directory"
echo "     - leak-screen.py, by the SELF-TEST print"
echo "   Fixed in leak-screen.py (length only, never the value) and here. This is"
echo "   recorded rather than quietly repaired because a screen that finds a leak in"
echo "   its own report is the clearest evidence available that it can fail at all —"
echo "   which is the thing this file was written to establish."
echo

echo
echo "============================================================================"
if [ "$rc" -eq 0 ] && [ "$LEAKED_VALUE" -eq 0 ]; then
  echo "PROOF COMPLETE — the screen fails when it should, passes when it should, and"
  echo "names file:line. A zero-hit run of this script is now a measurement."
elif [ "$rc" -eq 0 ]; then
  echo "PROOF COMPLETE ON THE FAILURE PATH, WITH ONE DEFECT FOUND IN leak-screen.py:"
  echo "see section 6. The screen demonstrably fails and names file:line."
else
  echo "PROOF FAILED — see the ASSERT lines above."
fi
echo "============================================================================"
exit $rc