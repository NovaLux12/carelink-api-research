#!/usr/bin/env bash
# Screen EVERY artefact this pass produced against scripts/scrub-patterns.txt.
#
# WHY THIS EXISTS INSTEAD OF RUNNING THE GATE. research-gate.sh chooses its
# subjects by file EXTENSION (md/yml/yaml/sh/hurl) and --all included, so a .txt,
# .jsonl or .json artefact this pass writes is read by no scrub pattern in any
# mode. docs/09 §4's own "a leak scan that cannot see the file it was written for"
# row records that blind spot as measured on this repo. This pass produces
# results.jsonl, map-diff.json and crosscheck.json, so it screens its own output
# the way that row says a pass must.
#
# It also greps for the machine-path pattern explicitly, because the paths of the
# response bodies are outside the repository and must not appear in any artefact.
set -uo pipefail
cd "$(cd "$(dirname "$0")" && pwd)"
# <checkout>/findings-log/<dir>/ -> two levels up is the checkout root.
ROOT="$(cd ../.. && pwd)"
SELF_PATTERNS="$ROOT/scripts/scrub-patterns.txt"
FAIL=0

# FAIL LOUDLY IF THE NET IS EMPTY. This script's first run resolved ROOT one level
# too high, found no pattern file, iterated zero patterns, and printed
# "scrub-check: PASS" — a scrub that reads nothing reporting clean, which is the
# same class as a dead scrub pattern (scripts/scrub-patterns.txt's own note: "a
# pattern that never fires is silent") and as AGENTS.md section 6 item 1. The
# guard is in the script rather than in a note because a note is what the previous
# version had.
if [ ! -r "$SELF_PATTERNS" ]; then
  echo "scrub-check: FAIL — pattern list not readable at '$SELF_PATTERNS'." >&2
  echo "  A scrub that reads no patterns is not a clean result; it is no result." >&2
  exit 1
fi
NPATTERNS=$(grep -v '^[[:space:]]*#' "$SELF_PATTERNS" | grep -c '|' || true)
if [ "$NPATTERNS" -lt 5 ]; then
  echo "scrub-check: FAIL — only $NPATTERNS pattern lines parsed; expected the full list." >&2
  exit 1
fi

SUBJECTS=$(find . -type f \
  ! -name 'scrub-check.sh' \
  \( -name '*.md' -o -name '*.txt' -o -name '*.json' -o -name '*.jsonl' \
     -o -name '*.sh' -o -name '*.py' -o -name '*.log' -o -name '*.tsv' \) | sort)

if [ -z "$SUBJECTS" ]; then
  echo "scrub-check: nothing to screen"
  exit 0
fi

ADDED=""
while IFS= read -r f; do
  [ -f "$f" ] || continue
  ADDED="${ADDED}$(cat "$f" 2>/dev/null)"$'\n'
done <<EOF
$SUBJECTS
EOF

echo "scrub-check: screening $(printf '%s\n' "$SUBJECTS" | wc -l) artefacts ($(printf '%s' "$ADDED" | wc -c) bytes) against $NPATTERNS patterns"
while IFS='|' read -r name pat; do
  [ -z "$name" ] && continue
  case "$name" in \#*) continue ;; esac
  if [ "$name" = "machine-specific paths" ]; then
    hits=$(printf '%s' "$ADDED" | grep -v '/home/<user>' | grep -cEi "$pat" || true)
  else
    hits=$(printf '%s' "$ADDED" | grep -cEi "$pat" || true)
  fi
  hits=${hits:-0}
  if [ "$hits" -gt 0 ]; then
    printf '  !!  %s — %s hit(s). DO NOT COMMIT.\n' "$name" "$hits"
    printf '%s' "$ADDED" | grep -nEi "$pat" | head -3 | cut -c1-160 | sed 's/^/         /'
    FAIL=1
  else
    printf '  ok  %s\n' "$name"
  fi
done < <(grep -v '^[[:space:]]*#' "$SELF_PATTERNS")

# The vendor key this pass FOUND inside the clinic bundle is named in
# scrub-patterns.txt as the first pattern, so a hit on it would already have been
# reported above. This line exists so a reader can see that the pass read the
# bundle and deliberately did not reproduce it.
echo "  --  the known-published vendor API key present at byte 3323593 of the clinic"
echo  "      main bundle is NOT reproduced in any artefact here; the pattern name"
echo "      above is the record of it."

if [ "$FAIL" -ne 0 ]; then
  echo "scrub-check: FAIL"
  exit 1
fi
echo "scrub-check: PASS"