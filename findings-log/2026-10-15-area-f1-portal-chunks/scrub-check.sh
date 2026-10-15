#!/usr/bin/env bash
# Screen EVERY artefact this pass produced against scripts/scrub-patterns.txt.
# Zero requests, no network.
#
# WHY THIS EXISTS AND WHY IT IS NOT OPTIONAL. docs/09 §4, trap row "A leak scan
# that cannot see the file it was written for": all three of the gate's leak
# scan modes choose their subjects by file extension (md/yml/yaml/sh/hurl), so
# every other extension — .txt, .jsonl, .tsv, .json, .log, .py, and the .h header
# captures this pass wrote — is read by no scrub pattern in ANY mode, --all
# included. This pass adds 271 files of which 252 are .h header captures, so
# this script is the only thing that reads them.
#
# It is deliberately independent of the gate so that a green gate is never
# mistaken for a clean artefact.
#
# A pattern that fires on a file in this directory is a STOP, not a warning.
#
# ⚠ TWO DEFECTS FIXED 2026-10-15 (verification round 1). The first version of
# this script was wrong twice, and both are recorded because the failure shape
# is the one docs/09 §4 warns about:
#
#   1. IT DID NOT RECURSE. Its loop was `for f in "$DIR"/*` with a `[ -f "$f" ]`
#      guard, so it screened the 19 top-level files and NONE of the 252 header
#      captures — 19 of 271 files, against a FINDINGS.md sentence that claimed
#      "every file here". The verifier screened headers/ by hand: 0 hits, so no
#      leak had escaped. The sentence was the defect, not the corpus; both are
#      fixed. Now `find -type f`, which cannot silently drop a directory.
#   2. IT PRINTED PASS HAVING SCREENED NOTHING. Run from a partial tree it
#      resolved the pattern file to nothing, iterated zero patterns, reported
#      "screened 19 files against 0 patterns: 0 hits" and then printed PASS — a
#      scrub that reads no patterns reporting clean (AGENTS.md §6 item 1). The
#      guards below are the fix, in the script rather than in a note, because a
#      note is what the first version had. Precedent: area K's scrub-check.sh.
set -uo pipefail
cd "$(cd "$(dirname "$0")" && pwd)"
# <checkout>/findings-log/<dir>/ -> two levels up is the checkout root.
ROOT="$(cd ../.. && pwd)"
PATS="$ROOT/scripts/scrub-patterns.txt"

# ---- FAIL LOUDLY IF THE NET IS EMPTY -------------------------------------
if [ ! -r "$PATS" ]; then
  printf 'scrub-check: FAIL — pattern list not readable at %s\n' "$PATS" >&2
  printf '  A scrub that reads no patterns is not a clean result; it is no result.\n' >&2
  exit 1
fi
NPATTERNS=$(grep -v '^[[:space:]]*#' "$PATS" | grep -c '|' || true)
if [ "$NPATTERNS" -lt 5 ]; then
  printf 'scrub-check: FAIL — only %s pattern lines parsed from %s; expected the full list.\n' \
    "$NPATTERNS" "$PATS" >&2
  exit 1
fi

# ---- SUBJECTS: recurse, every extension this pass actually wrote ----------
# .h is in this list because that is what the 252 header captures are called.
SUBJECTS=$(find . -type f \
  ! -name 'scrub-check.sh' \
  \( -name '*.md' -o -name '*.txt' -o -name '*.json' -o -name '*.jsonl' \
     -o -name '*.sh' -o -name '*.py' -o -name '*.log' -o -name '*.tsv' \
     -o -name '*.h' \) | sort)

NFILE=$(printf '%s\n' "$SUBJECTS" | grep -c . || true)
if [ "$NFILE" -eq 0 ]; then
  printf 'scrub-check: FAIL — no subjects found; the glob found nothing.\n' >&2
  exit 1
fi

# The one file allowed to contain the literals is the scrub list itself, and the
# gate script; neither is in this directory, so nothing needs exempting here.
if [ -e ./scrub-patterns.txt ]; then
  printf 'FAIL: the scrub list has been copied into this pass log\n'; exit 1
fi

hits=0
while IFS='|' read -r name rx; do
  [ -z "$name" ] && continue
  case "$name" in \#*) continue ;; esac
  [ -z "$rx" ] && continue
  if [ "$name" = "machine-specific paths" ]; then
    n=$(cat $SUBJECTS 2>/dev/null | grep -v '/home/<user>' | grep -a -c -E -e "$rx" || true)
  else
    n=$(cat $SUBJECTS 2>/dev/null | grep -a -c -E -e "$rx" || true)
  fi
  n=${n:-0}
  if [ "$n" -gt 0 ]; then
    printf 'HIT  %s  pattern "%s"  %s line(s)\n' "$n" "$name" "$rx"
    grep -a -n -E -e "$rx" $SUBJECTS 2>/dev/null | head -3 | cut -c1-160 | sed 's/^/       /'
    hits=$((hits + 1))
  fi
done < <(grep -v '^[[:space:]]*#' "$PATS")

# The scrub list carries no shape for a Set-Cookie in a header capture, and this
# pass writes 252 of them. Not a pattern above, so it is checked by hand and
# reported either way.
cookies=0
for f in ./headers/* ./results.jsonl; do
  [ -f "$f" ] || continue
  if grep -a -i -q '^set-cookie:' "$f" 2>/dev/null; then
    printf 'NOTE %s carries a Set-Cookie header — read it before publishing\n' "$f"
    cookies=$((cookies + 1))
  fi
done

# ---- REPORT WHAT WAS ACTUALLY COVERED ------------------------------------
nhead=$(printf '%s\n' "$SUBJECTS" | grep -c '/headers/.*\.h$' || true)
printf '\nscreened %s files (%s of them .h header captures) against %s patterns: %s hits, %s files with Set-Cookie\n' \
  "$NFILE" "$nhead" "$NPATTERNS" "$hits" "$cookies"
[ "$hits" -eq 0 ] || { printf 'FAIL — do not push\n'; exit 1; }
printf 'PASS — no scrub pattern fires on any of the %s artefacts this pass adds\n' "$NFILE"