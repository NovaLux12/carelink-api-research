#!/bin/sh
# locate.sh — resolve every landmark this pass's prose refers to, BY CONTENT,
# and print it bound to the commit it was measured at.
#
#     sh locate.sh            # the table
#     sh locate.sh --sha      # just the SHA the numbers below are valid for
#
# WHY THIS EXISTS. Four review rounds found the same defect class at a new
# coordinate each time: this prose published line positions into files that this
# PR ITSELF edits, so every commit invalidated its own citation. The sequence was
# :2189 -> docs/11:2170 -> docs/11:2218 -> :2232 -> :2236 -> :2253. Correcting
# the number each round was the wrong fix: it treated an instance of a class.
#
# THE RULE THIS ENCODES: prose in this directory does not publish positions. It
# publishes either
#   (a) a grep, runnable verbatim, that resolves the target — or
#   (b) this script's output, which is bound to a commit SHA printed with it.
# A position without its commit is a claim that expires on the next commit.
#
# EACH LANDMARK BELOW IS RESOLVED BY MATCHING CONTENT, NEVER BY A TYPED LINE
# NUMBER. That is the whole point: the `PATTERN` column is what stays true when
# the file moves, and the script recomputes the line number every run.
#
# EXIT: 0 if every landmark resolved; 1 if any failed. A landmark that cannot be
# found is a broken citation, and a script that prints a table while its targets
# are missing is the failure mode this repo keeps paying for.

set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE/../.." || exit 1
SHA=$(git rev-parse --verify HEAD 2>/dev/null || echo UNKNOWN)

[ "${1:-}" = "--sha" ] && { echo "$SHA"; exit 0; }

# NAME | FILE | FIXED-STRING OR E-RE | WHAT IT IS
resolve() {
  name=$1; file=$2; pat=$3; what=$4
  if [ ! -f "$file" ]; then
    printf '  %-26s %-38s UNRESOLVED (no such file: %s)\n' "$name" "$file" "$what"
    FAILED=$((FAILED + 1)); return
  fi
  # `grep -n --` is REQUIRED: several patterns below begin with a hyphen or
  # contain spaces and a leading dash, which grep otherwise reads as options.
  # An earlier revision of this script lost 10 of its 17 landmarks to exactly
  # that, and would have reported them UNRESOLVED — a false negative that looks
  # like a broken citation. The flag is the fix; so is the non-zero exit.
  # BOTH prefixes must be stripped. An earlier revision stripped `-E` but passed
  # `-F…` through to grep as part of the PATTERN, so every fixed-string landmark
  # searched for the literal text "-Fis absent from…" and reported UNRESOLVED —
  # nine false negatives, and a check that cries wolf is a check nobody runs.
  case "$pat" in
    -E*) line=$(grep -n -E -- "${pat#-E}" "$file" | head -1 | cut -d: -f1) ;;
    -F*) line=$(grep -n -F -- "${pat#-F}" "$file" | head -1 | cut -d: -f1) ;;
    *)   line=$(grep -n -F -- "$pat" "$file" | head -1 | cut -d: -f1) ;;
  esac
  PATBODY=${pat#-E}; PATBODY=${PATBODY#-F}
  # A landmark that resolved against the WRONG FILE is a broken citation too.
  # Checking it resolved is not enough — `grep -c` across the tree above shows
  # "is absent from 65 of the 84" hits BOTH docs/11 and docs/10, so a landmark
  # pointed at the wrong one resolves happily and says nothing.
  if [ -z "$line" ]; then
    printf '  %-26s %-30s ** UNRESOLVED ** %s\n' "$name" "$(basename "$file")" "$what"
    FAILED=$((FAILED + 1)); return
  fi
  # A landmark that resolved against the WRONG FILE is a broken citation too.
  # Resolving is not enough: "is absent from 65 of the 84" appears in BOTH
  # docs/11 and docs/10, so a landmark pointed at the wrong one resolves happily
  # and reports a line number that is true of the wrong file. Each landmark below
  # therefore names the file it must resolve IN, and the ambiguity is stated
  # rather than silently resolved by taking the first hit.
  if [ "$name" = "absent-sentence" ]; then
    hits=$(grep -l -F -- "$PATBODY" docs/*.md 2>/dev/null | wc -l)
    if [ "$hits" -gt 1 ]; then
      printf '  %-26s %s:%-6s appears in %s files — cite the grep, not a position\n' \
        "$name" "$(basename "$file")" "$line" "$hits"
    else
      printf '  %-26s %s:%-6s %s\n' "$name" "$(basename "$file")" "$line" "$what"
    fi
    return
  fi
  if [ "$name" = "absent-sentence-10" ]; then
    printf '  %-26s %s:%-6s %s\n' "$name" "$(basename "$file")" "$line" "$what"
    return
  fi
  if [ -z "$line" ]; then
    printf '  %-26s %-38s ** UNRESOLVED ** %s\n' "$name" "$file" "$what"
    FAILED=$((FAILED + 1)); return
  fi
  printf '  %-26s %s:%-6s %s\n' "$name" "$(basename "$file")" "$line" "$what"
}

FAILED=0
echo "locate.sh — landmarks resolved by CONTENT, measured at commit"
echo "  $SHA"
echo
echo "  These line numbers are valid ONLY for that commit. Cite the commit, or cite"
echo "  the grep. Do not copy the number into prose — that is the defect."
echo
D11=docs/11-suggested-research-areas.md
D10=docs/10-open-questions.md
C84=findings-log/2026-10-15-pool-l-ipro-census-cont/census-84.txt
DER=findings-log/2026-10-15-pool-l-ipro-census-cont/derive.py

echo "docs/11 — the surface this PR edits, so its positions expire on every commit"
resolve "closed-table-start"    "$D11" -E"^## Closed areas"            "the Closed table's first line"
resolve "closed-row-L"          "$D11" -E"^\| L — recovery of the ret" "Closed-table row L"
resolve "absent-sentence"       "$D11" -F"is absent from 65 of the 84" "the S-L4d defect sentence (area-L addendum)"
resolve "absent-sentence-10"    "$D10" -F"is absent from 65 of the 84" "the SAME sentence, in docs/10 section 1"
resolve "areaL-family-table"    "$D11" -F"| 2014-03-10 |"   "the family table row for 2014-10 (prior)"
resolve "S-L4-block"            "$D11" -F"S-L4 — one reader"            "the successor this pass closes"
resolve "S-L4-closed-marker"    "$D11" -F"CLOSED 2026-10-15 by"         "this pass's result block"
echo
echo "docs/10 — the surface S-L4b and S-L4e are measured against"
resolve "open-questions-1"      "$D10" -E"^## 1\. Open questions"       "section 1 (Open questions)"
resolve "floors-row"            "$D10" -F"*already-committed* Common Crawl record counts" "the floor question S-L4b overlaps"
resolve "truncation-row"        "$D10" -F"Can a **single** Common Crawl index query" "the truncation question"
resolve "account.py-named"      "$D10" -F"account.py"                    "the row that hands the broken tool on"
echo
echo "census-84.txt / derive.py — not edited by this PR, but cited often enough"
resolve "census-member-tally"   "$C84" -E"^crawls carrying"             "the 11-crawl member tally S-L4a corrects"
resolve "census-window-rule"    "$C84" -E"^# WINDOW RULE"                "the window rule"
resolve "census-verdict-rule"   "$C84" -E"^# VERDICT RULE"               "the verdict rule"
resolve "census-older-note"     "$C84" -F"VERDICT IS NOT A GAP IN THE CENSUS" "the older-schema note in its own header"
resolve "derive-bailout"        "$DER" -E"^ *AV\[c\] = 'older-schema'"   "the parser bail-out S-L4 closes"
resolve "derive-ledgers-glob"   "$DER" -E"^LEDGERS = sorted"             "the 6-ledger input list"
echo
echo "  Every row above was found by matching CONTENT. Zero of these numbers are"
echo "  typed into this script, and zero are typed into FINDINGS.md."
echo
if [ "$FAILED" -gt 0 ]; then
  echo "locate.sh: $FAILED landmark(s) UNRESOLVED — a citation is broken."
  exit 1
fi
echo "locate.sh: all landmarks resolved at $SHA"
exit 0