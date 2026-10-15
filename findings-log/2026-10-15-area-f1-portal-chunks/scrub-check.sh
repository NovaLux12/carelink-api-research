#!/usr/bin/env bash
# scrub-check.sh — screen THIS PASS's own artefacts against
# scripts/scrub-patterns.txt. Zero requests, no network.
#
# WHY THIS EXISTS AND WHY IT IS NOT OPTIONAL. docs/09 §4, trap row "A leak scan
# that cannot see the file it was written for": all three of the gate's leak
# scan modes choose their subjects by file extension (md/yml/yaml/sh/hurl), so
# the tracked .txt files — and, by the same mechanism, .jsonl / .tsv / .json —
# are read by no scrub pattern in ANY mode, --all included. A .txt artefact
# written this pass would be scanned by nothing.
#
# So this script does what the gate cannot: it takes every pattern from the ONE
# scrub list and applies it to every file this pass adds, whatever the
# extension. It is deliberately independent of the gate so that a green gate is
# never mistaken for a clean artefact.
#
# A pattern that fires on a file in this directory is a STOP, not a warning.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1

DIR="findings-log/2026-10-15-area-f1-portal-chunks"
PATS="scripts/scrub-patterns.txt"

# Patterns are "<name>|<regex>", one per line; comment lines start with '#'.
mapfile -t PATTERNS < <(grep -v '^#' "$PATS" | grep -v '^[[:space:]]*$' | while IFS='|' read -r name rx; do
  printf '%s\t%s\n' "$name" "$rx"
done)

# The one file allowed to contain the literals: the scrub list itself, and the
# gate script (both excluded by the gate for exactly this reason). Neither is
# in this directory, so nothing needs exempting here — and that is asserted
# rather than assumed.
if grep -ql 'scrub-patterns' "$DIR"/* 2>/dev/null && [ -e "$DIR/scrub-patterns.txt" ]; then
  printf 'FAIL: the scrub list has been copied into this pass log\n'; exit 1
fi

hits=0
files=0
for f in "$DIR"/*; do
  [ -f "$f" ] || continue
  files=$((files + 1))
  while IFS=$'\t' read -r name rx; do
    [ -z "$name" ] && continue
    # -a: treat binary as text. Bodies are not committed, but headers and the
    # ledger can hold bytes that are not printable.
    n=$(grep -a -c -E -e "$rx" "$f" 2>/dev/null || true)
    n=${n:-0}
    if [ "$n" -gt 0 ]; then
      printf 'HIT  %s  pattern "%s"  %s line(s)  in  %s\n' "$n" "$name" "$f"
      grep -a -n -E -e "$rx" "$f" | head -3 | cut -c1-160
      hits=$((hits + 1))
    fi
  done < <(printf '%s\n' "${PATTERNS[@]}")
done

# The scrub list also carries a live-value pattern for .corp hosts and home
# paths that the regex list covers; this pass adds one more shape the list does
# not: a body head or header value carrying a Set-Cookie. Not a pattern above,
# so it is checked by hand here and reported either way.
cookies=0
for f in "$DIR"/headers/* "$DIR"/results.jsonl; do
  [ -f "$f" ] || continue
  if grep -a -i -q '^set-cookie:' "$f" 2>/dev/null; then
    printf 'NOTE %s carries a Set-Cookie header — read it before publishing\n' "$f"
    cookies=$((cookies + 1))
  fi
done

printf '\nscreened %s files against %s patterns: %s hits, %s files with Set-Cookie\n' \
  "$files" "$(printf '%s\n' "${PATTERNS[@]}" | grep -c .)" "$hits" "$cookies"
[ "$hits" -eq 0 ] || { printf 'FAIL — do not push\n'; exit 1; }
printf 'PASS — no scrub pattern fires on any artefact in %s\n' "$DIR"