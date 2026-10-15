#!/bin/sh
# dup-test.sh — the NON-DUPLICATE test `CONTRIBUTING-research.md:199` requires for
# every successor, run for real, with the commands and their results recorded.
#
#     sh dup-test.sh            # report; exit 0 unless the POSITION check fails
#     sh dup-test.sh --advisory # report only, exit 0 even on a position hit
#
# The bar it enforces: "it is already in `docs/10` section 1, already in the
# Closed table, or already on the page — grep both first". A successor that
# cannot be shown to be non-duplicate fails the bar, and an absence that the bar
# asks to be recorded is itself the finding when it is not recorded.
#
# SCOPE NOTE: this tests whether a successor's SUBJECT is already recorded
# somewhere. It cannot prove novelty — docs/10 section 2 ("Searched and closed")
# is a surface the grep below deliberately does not claim to cover, and a
# re-derivation is welcome per CONTRIBUTING-research.md:212. Where a hit is a
# PARTIAL overlap rather than a duplicate, the table says so.
#
# ══ THE POSITION CHECK — the class, not the spelling ══════════════════════════
#
# Four review rounds found the same defect at a new coordinate: `:2189` ->
# `docs/11:2170` -> `docs/11:2218` -> `:2232` -> `:2236` -> `:2253`. Every fix
# added lines, which moved what the log measured, which required the next fix.
# That is not bookkeeping. It is a write-up shape that cannot converge, because
# prose in this directory cites positions into a file this PR edits.
#
# So: FINDINGS.md publishes NO POSITION into a file this PR edits. A position is a
# number a reader is invited to look up, and this PR moves those numbers. What
# prose cites instead is a grep, or `locate.sh` bound to a commit.
#
# WHAT IS ENFORCED, EXACTLY. Round 6 found this check claiming "the CLASS, not the
# spelling" while catching only the colon form, so after round 6 the claim IS this
# list and nothing wider:
#
#   A   <edited-file>:NUMBER           `docs/11:2236`
#   A'  <edited-file>:NUMBER-NUMBER    `docs/11:2236-2253`
#   A"  <edited-file>:  NUMBER         `docs/11: 2236`
#   E   <edited-file>#L NUMBER         `docs/11#L2236`
#   B   "line"/"lines" + NUMBER        when an edited-file subject is on the line
#   C   a positional verb + NUMBER     "the table begins at 2236", subject on the line
#
# WHAT IS NOT ENFORCED, named so the residual cannot be mistaken for coverage:
# a bare number with no positional context (deliberately — this file is full of
# legitimate `200`s, `1024`s and `193`s); a position whose SUBJECT follows the
# number ("absorbed from 2236 in docs/11"); and **a position split across two
# lines**, the subject at the end of one and the number at the start of the next.
# That last one was live in section 6 of this file and is fixed in the FILE, not in
# this check: a line-based scan cannot see it, and a two-line join produced more
# false positives than catches. See section 8a-6, rows 3 and 4.
#
# THE CHECK BELOW MATCHES THE SPELLINGS THE CLASS ACTUALLY TAKES — and after
# verifier round 5 it does so for the colon form. An earlier revision tested each
# punctuation-delimited TOKEN for a trailing `:NNNN`, but the tokeniser split on
# `:`, so `docs/11:NNNN` was torn into `docs/11` + `NNNN` and the test could
# never fire: it reported "0 positions" on a file that carried them. That is
# `AGENTS.md` section 6 item 2 aimed at this repo's own check — a test that
# catches only the spelling it was written for. The tokeniser now keeps `:`
# inside a token, and the subject is matched by path PREFIX (see B/C below).
#
# THE EXEMPTION IS A KIND, NOT A POSITION. It exempts SECTIONS whose heading
# matches the ONE pattern in CORR_RE below and runs to the next `^## ` heading.
# Two earlier revisions were wrong here: one used `awk '/^## 8a/ {skip=1}'`,
# which skipped from that line to EOF so every later section inherited a free
# pass forever; the next matched `^## 8a` alone, so any heading beginning `## 8a`
# opened the exemption, correction or not. CORR_RE is now specific, and a heading
# that mentions "correction" but does NOT match CORR_RE is reported as FAKE.
#
# WHY THE EXEMPTION EXISTS AT ALL: `AGENTS.md` section 5 requires corrections to
# be PRESERVED, not smoothed over. A correction record must be able to quote the
# wrong number it withdrew, or the retraction history stops being evidence.

set -u
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE/../.." || exit 1
LOG="$HERE/FINDINGS.md"
ADVISORY=0
[ "${1:-}" = "--advisory" ] && ADVISORY=1

D10=docs/10-open-questions.md
D11=docs/11-suggested-research-areas.md
# The single canonical test for a Correction SECTION heading. Used by the
# exemption, the FAKE check and the listing below, so they cannot diverge.
CORR_RE='^## 8a(-[0-9]+)?[.] Correction([^A-Za-z]|$)'

# FAIL CLOSED, AND FAIL EARLY. `git diff origin/main...HEAD` is the only source of
# the edited-file list; with no `origin/main` (a shallow clone, a detached merge
# checkout) it returns nothing, every path is then unmatched, and the check below
# would report PASS on a file full of positions. So the guard runs BEFORE the
# first grep: no list, no verdict.
EDITED=$(git diff --name-only origin/main...HEAD 2>/dev/null | grep -v '^findings-log/' || true)
if [ -z "$EDITED" ]; then
  echo "  ** FAIL - the edited-file list is empty: 'git diff --name-only" >&2
  echo "     origin/main...HEAD' returned nothing (is origin/main present?). With no" >&2
  echo "     list every position is exempt and the check is VACUOUS, not clean." >&2
  echo "     Run this from a clone that has origin/main. **" >&2
  exit 1
fi
EDRE=$(printf '%s\n' "$EDITED" | paste -sd'|' -)

echo "dup-test.sh — the non-duplicate test, run against docs/10 section 1,"
echo "the docs/11 Closed table, and docs/11 itself."
echo
CLOSED=$(grep -n '^## Closed areas' "$D11" | cut -d: -f1)
S10_A=$(grep -n '^## 1\. Open questions' "$D10" | cut -d: -f1)
S10_B=$(grep -n '^## 2\. Searched and closed' "$D10" | cut -d: -f1)
echo "  docs/10 section 1 spans lines $S10_A .. $((S10_B - 1))"
echo "  docs/11 Closed table begins at line $CLOSED"
echo "  (both derived by grep above, never typed in — a typed one is the defect)"
echo

# grep_subject LABEL PATTERN -- greps three surfaces and reports each count.
grep_subject() {
  label="$1"; pat="$2"
  d10=$(awk -v a="$S10_A" -v b="$S10_B" 'NR>=a && NR<b' "$D10" | grep -ci -- "$pat" || true)
  d11=$(grep -ci -- "$pat" "$D11" || true)
  cl=$(awk -v a="$CLOSED" 'NR>=a' "$D11" | grep -ci -- "$pat" || true)
  printf '  %-11s %-26s docs/10 s1=%-3s docs/11=%-3s Closed=%-3s\n' "$label" "$pat" "${d10:-0}" "${d11:-0}" "${cl:-0}"
}

echo "-- S-L4a  the member tally's window basis (census-84.txt lists an out-of-window crawl)"
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
echo "-- S-L4e  account.py handed on broken; its successor is docs/10 section 1"
grep_subject S-L4e "account.py"
grep_subject S-L4e "t_sent"
echo
echo "  ⚠ THE COUNTS ABOVE ARE LIVE. They are printed, not transcribed: round 4"
echo "    found a recorded table that no longer matched the script producing it"
echo "    (floor recorded 31 / live 30, truncat recorded 3 / live 5). FINDINGS.md"
echo "    therefore does NOT carry a copy of this table — it carries the command."
echo

echo "═══ THE POSITION CHECK ═══"
echo "  FINDINGS.md must publish no position into a file this PR edits:"
echo "    docs/NN:NNNN | docs/NN:NNNN-NNNN | docs/NN: NNNN | docs/NN#LNNNN"
echo "    | 'line NNNN' | 'begins at NNNN'   (subject on the same line)"
echo "  NOT seen, and stated in the header rather than left to be discovered: a"
echo "  subject-after-number, and a position split across two lines."
echo "  Exempt: Correction SECTIONS, recognised by heading, which must be able to"
echo "  quote a withdrawn number (AGENTS.md section 5). Everything after them is"
echo "  checked — an earlier revision skipped to EOF and let later sections inherit"
echo "  the exemption."

# ── WHAT IS FLAGGED, AND WHY IT IS BOUNDED ─────────────────────────────────
# A position is a NUMBER THE READER IS INVITED TO LOOK UP IN A FILE.
#
# THE BOUND THAT MAKES IT A CHECK RATHER THAN A NUISANCE: only positions into a
# file THIS PR ITSELF EDITS. This PR's entire diff outside its own log directory
# is `docs/11-suggested-research-areas.md` — so a pointer into `docs/11` is
# invalidated by this PR landing, and a pointer into `census-84.txt`,
# `derive.py` or `account.py` is not, because this PR does not touch them. That
# is a property of the diff, so it is derived below rather than hardcoded, and it
# will stay true as this PR's scope changes.
#
#   A  <edited-file>:NUMBER        the colon form
#   B  "line"/"lines" + number     incl. a range, when the subject is an edited file
#   C  a positional verb + number  "begins at 2189" — the B3 spelling, no colon
#
# WHAT IS DELIBERATELY NOT FLAGGED: a bare number with no positional context. This
# file is full of legitimate ones — `200` and `502` as HTTP statuses, `1024` in a
# byte rule, `193` in a count, `2014-03-10` in a date. An earlier revision of this
# check flagged all of them and reported **115 positions on a file that had 3** —
# a check nobody runs, hiding the 3 it was built to find. That was `AGENTS.md`
# section 6 item 2 aimed at this repo's own check: a test that only catches what
# it was written to catch is not a test.
#
# A line is reported once, by first match.

# `ed` below is used ONLY literally — as an exact key and via index() — so it is
# NOT regex-escaped, and the join is `paste`. (An earlier revision escaped it for
# a regex use that does not exist, which made gawk print "escape sequence ..."
# warnings on stderr and made the no-write-to-stderr rule false.)

HITS=$(awk -v ed="$EDRE" -v cre="$CORR_RE" '
  BEGIN { split(ed, A, "[|]"); for (i in A) E[A[i]] = 1 }
  # A Correction section is a SECTION: it starts at a "^## " heading and ENDS at
  # the next one. That is what makes the exemption a kind, not a position.
  /^## / { insec = ($0 ~ cre) }
  insec  { next }
  {
    line = $0
    why = ""
    n = split(line, W, /[^A-Za-z0-9._/:+#-]+/)
    # A — a colon position into a file this PR edits (full path, or the
    # abbreviated `docs/11` form this pass actually writes)
    for (i = 1; i <= n; i++) {
      tok = W[i]; pre = ""
      if (tok ~ /^[A-Za-z0-9._/-]+:[0-9]+(-[0-9]+)?$/) {
        pre = tok; sub(/:[0-9]+(-[0-9]+)?$/, "", pre)          # rule A / A-prime
      } else if (tok ~ /^[A-Za-z0-9._/-]+:$/ && i < n && W[i+1] ~ /^[0-9]{3,4}$/) {
        pre = tok; sub(/:$/, "", pre)                          # rule A-doubleprime
      } else if (tok ~ /^[A-Za-z0-9._/-]+#L[0-9]+$/) {
        pre = tok; sub(/#L[0-9]+$/, "", pre)                   # rule E (github anchor)
      }
      if (pre != "" && (E[pre] || (length(pre) > 2 && index(ed, pre) == 1))) {
        why = "A file:NUMBER   "; break
      }
    }
    # B/C — a positional phrase whose SUBJECT is an edited file, named either by
    # its full path (`docs/11-suggested-research-areas.md`) or by any leading
    # directory of one (`docs/11`). Getting this direction wrong is how the
    # bare-`2189` defect survived one more round: an earlier revision tested
    # whether the WORD started with the full path, but this pass writes the
    # subject as `docs/11`, so the word is a PREFIX OF the path, not the reverse.
    subject = 0
    for (i = 1; i <= n; i++)
      if (W[i] != "" && length(W[i]) > 2 && index(ed, W[i]) == 1) { subject = 1; break }
    if (why == "" && subject && line ~ /(begins|starts|ends) +(at )?[0-9]{3,4}/)
      why = "C positional verb"
    if (why == "" && subject && line ~ /[Ll]ines? +[0-9]{3,4}/)
      why = "B line NUMBER   "
    if (why != "") print NR": " why"  " line
  }
' "$LOG")

# Headings that LOOK like Correction sections but are not one — so the exemption
# cannot be widened by renaming.
FAKE=$(awk -v cre="$CORR_RE" '/^## / && tolower($0) ~ /correction/ && $0 !~ cre { print NR": "$0 }' "$LOG")

N=$(printf '%s' "$HITS" | grep -c '' || true)
echo
if [ "$N" -eq 0 ] && [ -z "$FAKE" ]; then
  echo "  PASS — 0 positions published outside the Correction sections."
  POS=0
else
  POS=1
  printf '%s\n' "$HITS" | sed 's/^/  HIT: /'
  [ -n "$FAKE" ] && printf '%s\n' "$FAKE" | sed 's/^/  FAKE CORRECTION HEADING: /'
  echo "  ** $N position(s) outside Correction sections — every one expires on the"
  echo "     next commit that adds lines above its target. **"
fi
echo
echo "  Correction sections (exempt, by heading):"
awk -v cre="$CORR_RE" '/^## /{ if ($0 ~ cre) print "    " NR": "$0 }' "$LOG"
echo
echo "  Sections AFTER the last Correction section, which the exemption does NOT reach:"
awk -v last="$(grep -nE "$CORR_RE" "$LOG" | tail -1 | cut -d: -f1)" '
  /^## / && NR > last { print "    " NR": "$0 }
' "$LOG"
echo
echo "  Stale pointers from earlier rounds — what each number reads NOW. A citation"
echo "  pointing at a passage that does not contain the claim is AGENTS.md section 6 item 6:"
for ln in 2170 2218 2232 2236 2253; do
  printf '     :%s -> %s\n' "$ln" "$(sed -n "${ln}p" "$D11" | cut -c1-62)"
done
echo
echo "  The positions are NOT cited anywhere; they are printed here so a reader can"
echo "  confirm for themselves that a pointer would have been wrong. locate.sh"
echo "  resolves every landmark this prose refers to, by content, bound to a commit."

if [ "$POS" -eq 1 ] && [ "$ADVISORY" -eq 0 ]; then
  echo
  echo "dup-test.sh: FAILED — $N position(s) outside the Correction sections."
  exit 1
fi
if [ "$POS" -eq 1 ]; then
  echo
  echo "dup-test.sh: ADVISORY ONLY (--advisory) — $N position(s), not enforced."
  exit 0
fi
echo
echo "dup-test.sh: PASS (non-duplicate table printed; 0 positions outside Corrections)"
exit 0