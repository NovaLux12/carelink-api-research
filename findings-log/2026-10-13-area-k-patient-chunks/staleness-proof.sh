#!/bin/bash
# Area K — PROOF THAT THE STALE-ARTEFACT GUARD FAILS, AND THAT
# resolve.py's SELF-TEST VERDICT IS WIRED TO THE EXIT STATUS. ZERO requests.
#
# WHY. Two of this pass's instruments had a verdict that could not fail, and neither
# had been shown to fail:
#
#   1. `resolve.txt` was committed STALE. `resolve.py` had been corrected to print a
#      SELF-TEST block and a three-line verdict; the committed capture had neither, and
#      had been shipped that way through a full review cycle. Nothing noticed, because
#      the only way to notice was to run a script whose corpus this repository does not
#      commit. The guard added beside it compares the script's own sha256 against the
#      one the artefact declares, and exits 3 on a mismatch.
#
#   2. `resolve.py`'s SELF-TEST printed `BAD` into a table and appended NOTHING. A
#      regression in `self_consistency()` would have printed `BAD` and the script
#      would still have exited 0 — the print-only verdict, inside the block written to
#      eliminate it, in the same pass that wrote `leak-screen-proof.sh` to eliminate it
#      in the sibling file. (`leak-screen.py`'s own SELF-TEST was never affected: it
#      sets `SELFTEST_OK = False` and `sys.exit(1 if (hits or not SELFTEST_OK) else 0)`
#      consumes it. The defect was in `resolve.py`.)
#
# `resolve.py --self-test-only` exists because of (2): the corpus is not committed, so
# before it, no part of this script could be exercised on a clean clone.
#
# WHAT IS ASSERTED, and why each one:
#   A. the control: the real script exits 0 on the self-test
#   B. a broken `self_consistency()` makes `--self-test-only` exit NON-ZERO and name
#      the rule — a verdict that cannot fail is not a verdict
#   C. a single mis-stated case expectation does the same (proves B is not just
#      "any edit fails")
#   D. the full run's consumer: the same count is appended to `failures`, and
#      `sys.exit(1 if failures else 0)` is what the script ends on
#   E. the stale-artefact guard: a deliberately wrong digest exits 3 and names both
#      digests
#   F. a missing digest line exits 3 rather than silently trusting the artefact
#   G. the control on the guard: the committed artefacts at their declared digests
#      PASS the guard, so G does not merely prove the guard can fail
#
# NOTHING HERE TRAVELS TO A VENDOR. Every step is local, on copies in a temp tree that
# is removed on exit.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(git -C "$HERE" rev-parse --show-toplevel)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fails=0
check() { # label expected got
  if [ "$2" = "$3" ]; then
    printf '  ok   %-58s expected %-4s got %s\n' "$1" "$2" "$3"
  else
    printf '  FAIL %-58s expected %-4s got %s\n' "$1" "$2" "$3"
    fails=$((fails + 1))
  fi
}
note() { printf '  ..   %s\n' "$1"; }

echo "STALENESS / VERDICT PROOF — resolve.py + patient-csr.py, zero requests"
echo

# --- A. control --------------------------------------------------------------------
echo "A. CONTROL — the committed artefacts pass the guard at their declared digests"
for pair in "resolve.py:resolve.txt" "patient-csr.py:patient-csr.txt"; do
  S="${pair%%:*}"; A="${pair##*:}"
  D=$(sha256sum "$HERE/$S" | cut -d' ' -f1)
  DECL=$(grep -E '^SCRIPT-SHA256-AS-OF-THIS-NOTE:' "$HERE/$A" | awk '{print $2}')
  check "$A declares sha256 of $S" "$D" "$DECL"
done
# And the guard genuinely runs rather than merely comparing strings in this report:
# with the digests correct, each script proceeds PAST the guard and fails on the
# corpus instead — a different exit code, from the next block of code.
( cd "$HERE" && python3 resolve.py headers results.jsonl >/dev/null 2>&1 )
check "resolve.py past the guard -> corpus error, not exit 3" "1" "$?"
( cd "$HERE" && python3 patient-csr.py headers results.jsonl chunks-swept.txt >/dev/null 2>&1 )
check "patient-csr.py past the guard -> corpus error, not exit 3" "2" "$?"
echo

# --- B. broken self_consistency() ---------------------------------------------------
echo "B. BROKEN self_consistency() — the verdict must be non-zero, not merely printed"
cp "$HERE/resolve.py" "$TMP/resolve.py"
python3 - "$TMP/resolve.py" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = "    problems = []\n    if printed and not recorded:"
assert old in s, "anchor not found — the file changed under this proof"
s = s.replace(old, "    return []   # POISONED: never reports a problem\n    problems = []\n    if printed and not recorded:", 1)
# Keep the guard satisfied so the proof tests the SELF-TEST, not the guard.
open(p, "w", encoding="utf-8").write(s)
PY
D=$(sha256sum "$TMP/resolve.py" | cut -d' ' -f1)
printf 'SCRIPT-SHA256-AS-OF-THIS-NOTE: %s\n' "$D" > "$TMP/resolve.txt"
python3 "$TMP/resolve.py" --self-test-only > "$TMP/b.out" 2>&1
check "poisoned copy: --self-test-only exit" "1" "$?"
check "poisoned copy: BAD rows printed" "4" "$(grep -c '^  BAD' "$TMP/b.out")"
check "poisoned copy: verdict says SELF-TEST FAILED" "1" \
  "$(grep -c 'VERDICT: SELF-TEST FAILED' "$TMP/b.out")"
check "poisoned copy: verdict names self_consistency()" "1" \
  "$(grep -c 'self_consistency() is broken' "$TMP/b.out")"
note "the four firing cases are exactly the four that expect fire — a rule that never"
note "fires is quiet on all seven, which is why this poison is the right one."
echo

# --- C. one mis-stated expectation --------------------------------------------------
echo "C. ONE MIS-STATED EXPECTATION — proves B is not 'any edit fails'"
cp "$HERE/resolve.py" "$TMP/resolve2.py"
python3 - "$TMP/resolve2.py" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = '    (2, 1, True,  "TWO printed FAILs, ONE entry — the case the old code called consistent"),'
assert old in s, "anchor not found — the file changed under this proof"
s = s.replace(old, '    (2, 1, False, "POISONED: expectation flipped to quiet"),', 1)
open(p, "w", encoding="utf-8").write(s)
PY
D=$(sha256sum "$TMP/resolve2.py" | cut -d' ' -f1)
printf 'SCRIPT-SHA256-AS-OF-THIS-NOTE: %s\n' "$D" > "$TMP/resolve.txt"
python3 "$TMP/resolve2.py" --self-test-only > "$TMP/c.out" 2>&1
check "flipped expectation: exit" "1" "$?"
check "flipped expectation: exactly one BAD row" "1" "$(grep -c '^  BAD' "$TMP/c.out")"
echo

# --- D. the full run's consumer -----------------------------------------------------
echo "D. FULL RUN — the same count reaches failures, and failures reaches the exit"
rm -f "$TMP/resolve.txt"          # let the guard no-op; we are not testing it here
note "D1: self_test() returns the count, and the consumer appends it to 'failures'"
check "self_test() -> failures.append(...) present" "1" \
  "$(grep -c 'failures.append("SELF-TEST: %d of %d synthetic case(s)' "$HERE/resolve.py")"
check "the script's exit status is a function of failures" "1" \
  "$(grep -c '^sys.exit(1 if failures else 0)$' "$HERE/resolve.py")"
check "self_test()'s return value is the count, not a string" "1" \
  "$(grep -c 'return lines, bad' "$HERE/resolve.py")"
note "D2: the self-test mode exits on the same value, end to end — proof C above IS"
note "that exit, and it is the value self_test() returns."
note "NOT PROVEN HERE: a poisoned FULL run, end to end. That needs the corpus, which is"
note "not committed. Proven is the wiring in D1 and the exit in C; NOT proven is the two"
note "composed. Stated rather than implied."
echo

# --- E. wrong digest ----------------------------------------------------------------
echo "E. STALE ARTEFACT — a wrong declared digest must exit 3 and name both digests"
cp "$HERE/resolve.py" "$TMP/resolve3.py"
printf 'SCRIPT-SHA256-AS-OF-THIS-NOTE: %s\n' \
  "0000000000000000000000000000000000000000000000000000000000000000" > "$TMP/resolve.txt"
python3 "$TMP/resolve3.py" headers results.jsonl > "$TMP/e.out" 2>&1
check "wrong digest: exit" "3" "$?"
check "wrong digest: says STALE" "1" "$(grep -c 'is STALE' "$TMP/e.out")"
check "wrong digest: names the declared one" "1" \
  "$(grep -c '0000000000000000000000000000000000000000000000000000000000000000' "$TMP/e.out")"
check "wrong digest: names the script's own" "1" \
  "$(grep -c "$(sha256sum "$TMP/resolve3.py" | cut -d' ' -f1)" "$TMP/e.out")"
check "wrong digest: fires BEFORE the corpus is read" "0" \
  "$(grep -c 'FileNotFoundError' "$TMP/e.out")"
echo

# --- F. no digest line --------------------------------------------------------------
echo "F. UNDECLARED ARTEFACT — no digest line must exit 3, not be trusted silently"
grep -v '^SCRIPT-SHA256-AS-OF-THIS-NOTE:' "$HERE/patient-csr.txt" > "$TMP/patient-csr.txt"
cp "$HERE/patient-csr.py" "$TMP/patient-csr.py"
rm -f "$TMP/resolve.py" "$TMP/resolve2.py" "$TMP/resolve3.py"
python3 "$TMP/patient-csr.py" headers "$HERE/results.jsonl" "$HERE/chunks-swept.txt" \
  > "$TMP/f.out" 2>&1
check "no digest line: exit" "3" "$?"
check "no digest line: says what is missing" "1" \
  "$(grep -c 'carries no' "$TMP/f.out")"
check "no digest line: names the line it wants" "1" \
  "$(grep -c 'SCRIPT-SHA256-AS-OF-THIS-NOTE: <sha256>' "$TMP/f.out")"
check "no digest line: prints the sha to use" "1" \
  "$(grep -c "$(sha256sum "$HERE/patient-csr.py" | cut -d' ' -f1)" "$TMP/f.out")"
echo

echo "SELF-CHECK"
echo "  checks that FAILED: $fails"
if [ "$fails" -ne 0 ]; then
  echo "  INCONSISTENT — a check below did not hold"
  exit 1
fi
echo "  consistent"