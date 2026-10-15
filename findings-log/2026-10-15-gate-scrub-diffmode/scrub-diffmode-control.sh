#!/usr/bin/env bash
# scrub-diffmode-control.sh — per-pattern liveness of the ten scrub nets behind
# the gate's diff-mode leading "+", with one control cell per pattern.
#
# ZERO REQUESTS. Every input is local: scripts/scrub-patterns.txt, the gate's own
# source, and a scratch git repo holding synthetic lines. No vendor host, no
# archive host, no network call at all, so AGENTS.md §8's probing rules have
# nothing to bite on.
#
# WHAT IS MEASURED. The gate's leak scan builds one text blob (ADDED) and counts,
# per pattern, how many of its lines match:
#     hits=$(printf '%s' "$ADDED" | grep -cEi "$pat" || true)      # gate :126
# Liveness is therefore a property of (pattern x subject text), and the subject
# text differs by mode:
#     all    -> cat "$f"                                                       (gate :106)
#     staged -> git diff --cached -U0 | grep '^+' | grep -v '^+++'              (gate :107)
#     diff   -> git diff -U0 "$BASE"     | grep '^+' | grep -v '^+++'           (gate :108)
# All three constructions, and the whole matching loop, are EVAL'D VERBATIM FROM
# scripts/research-gate.sh — never re-implemented. A re-implementation that
# drifted from the gate would measure the wrong thing and still print a tidy
# table. If the gate changes shape the extraction guards in self_test() fail and
# this harness exits non-zero rather than publishing stale verdicts.
#
# MODES
#   (no arg)     the measurement: cells x patterns x 3 modes, then the verdict
#   --self-test  the harness's own assertions, including a mutation test that
#               proves the measurement moves when the thing it measures moves
#   --screen     run the gate's leak-scan path (both subject modes) over THIS
#               repository's own diff vs origin/main — the static part of the
#               gate, so a committed artefact can be screened without running the
#               vendor suite. Run it from anywhere: the mode enters $REPO itself,
#               asserts it got there, and refuses to report a clean scan over an
#               empty subject list or a partial loop. It names the tree it read,
#               so a committed transcript of it is re-derivable.
#
# WHY NO COMMITTED FIXTURES. All ten nets are self-referential: an instance that
# matches pattern P is by construction text that pattern P matches, so committing
# an instance as a fixture makes the gate fire on its own control set. Instances
# are assembled at runtime from fragments and elided as <INST> in every committed
# artefact (AGENTS.md §7).

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"          # findings-log/<slug>/.. == repo root
GATE="$REPO/scripts/research-gate.sh"
PAT_REL="scripts/scrub-patterns.txt"
PAT_ABS="$REPO/$PAT_REL"          # absolute, so cwd changes cannot break a read
MODES="all staged diff"
RS=$'\x1f'                      # cell field separator; see build_corpus

FAILURES=0
note_fail() { printf 'FAIL  %s\n' "$*" >&2; FAILURES=$((FAILURES + 1)); }
note_ok()   { printf 'ok    %s\n' "$*"; }
block()     { sed -n "${1}p" "$GATE"; }

# ---------------------------------------------------------------- instances
# frag joins its arguments with nothing. Instances are split into fragments so no
# committed line ever contains a complete instance.
frag() { local IFS=; printf '%s' "$*"; }

# The one net whose only positive instance IS a published literal: the pattern is
# a literal string, so nothing else can match it. Read at runtime from the
# pattern file — the file the gate itself exempts at :67 — and written to no
# committed artefact.
LITERAL_VENDOR="$(grep '^vendor API key literal|' "$REPO/$PAT_REL" | head -1 | cut -d'|' -f2-)"

INST_VENDOR="$LITERAL_VENDOR"
INST_BROKER="$(frag 0vJJl02 abcdefgh)"
INST_RECAPTCHA="$(frag 6L Aa buor ABCD 0123456789)"
INST_VPCE="$(frag vpce- 0123456789abcdef0 - abcdefgh .execute-api. eu-west-1 .vpce.amazonaws.com)"
INST_HOST="$(frag grafana . zzz . minimed . eu)"
INST_CORP="$(frag build .corp)"
INST_HOMEPATH="$(frag /home/ jle)"
INST_JSESSION="$(frag ';jsessionid_' ABCDEF12 =)"
INST_SESSIONDATA="$(frag sessionData= abcdefghijkl)"
INST_AWSKEY="$(frag AKIA IOSFODNN7EXAMPLE)"

# Realistic embedding per pattern. A bare token is the easiest cell in the matrix
# and proves nothing about the line a real finding would arrive in.
WRAP_VENDOR="$(frag '"api_key": "' "$INST_VENDOR" '"')"
WRAP_BROKER="$(frag '?broker=' "$INST_BROKER" '&next=1')"
WRAP_RECAPTCHA="$(frag '"site_key": "' "$INST_RECAPTCHA" '"')"
WRAP_VPCE="$(frag '"service": "https://' "$INST_VPCE" '"')"
WRAP_HOST="$(frag '"url": "https://' "$INST_HOST" '/board"')"
WRAP_CORP="$(frag '"host": "' "$INST_CORP" '"')"
WRAP_HOMEPATH="$(frag 'cd ' "$INST_HOMEPATH" ' && ls')"
WRAP_JSESSION="$(frag 'GET /x?a=1' "$INST_JSESSION" ' HTTP/1.1')"
WRAP_SESSIONDATA="$(frag '"payload": "' "$INST_SESSIONDATA" '"')"
WRAP_AWSKEY="$(frag '"aws_access_key_id": "' "$INST_AWSKEY" '"')"

# Keyed by the pattern's own name, so a renamed pattern becomes an unresolved key
# and fails loudly instead of silently losing a cell.
inst_of() {
  case "$1" in
    'vendor API key literal')                    printf '%s' "$INST_VENDOR" ;;
    'reports-broker key fragments')              printf '%s' "$INST_BROKER" ;;
    'reCAPTCHA site keys')                       printf '%s' "$INST_RECAPTCHA" ;;
    'AWS VPC endpoint service name')             printf '%s' "$INST_VPCE" ;;
    'internal Grafana/K8s/GitLab/DB/Prometheus host') printf '%s' "$INST_HOST" ;;
    'internal .corp host')                       printf '%s' "$INST_CORP" ;;
    'machine-specific paths')                    printf '%s' "$INST_HOMEPATH" ;;
    'live jsession values')                      printf '%s' "$INST_JSESSION" ;;
    'live sessionData values')                   printf '%s' "$INST_SESSIONDATA" ;;
    'credential prefixes')                       printf '%s' "$INST_AWSKEY" ;;
    *)                                          return 1 ;;
  esac
}
wrap_of() {
  case "$1" in
    'vendor API key literal')                    printf '%s' "$WRAP_VENDOR" ;;
    'reports-broker key fragments')              printf '%s' "$WRAP_BROKER" ;;
    'reCAPTCHA site keys')                       printf '%s' "$WRAP_RECAPTCHA" ;;
    'AWS VPC endpoint service name')             printf '%s' "$WRAP_VPCE" ;;
    'internal Grafana/K8s/GitLab/DB/Prometheus host') printf '%s' "$WRAP_HOST" ;;
    'internal .corp host')                       printf '%s' "$WRAP_CORP" ;;
    'machine-specific paths')                    printf '%s' "$WRAP_HOMEPATH" ;;
    'live jsession values')                      printf '%s' "$WRAP_JSESSION" ;;
    'live sessionData values')                   printf '%s' "$WRAP_SESSIONDATA" ;;
    'credential prefixes')                       printf '%s' "$WRAP_AWSKEY" ;;
    *)                                          return 1 ;;
  esac
}

CLEAN="$(frag 'This line carries no instance of any scrub pattern.')"

# ---------------------------------------------------------------- the gate's own bytes
SELF=""; SELF_PATTERNS=""; MODE=""; ADDED=""; SUBJECT=""; f=""
name=""; pat=""; hits=""; FAIL=0; REC=""; BASE=""; SCRATCH=""
G_SELF='66,67'        # SELF / SELF_PATTERNS
G_SUBJ='84,94'        # subject-list selection, all three modes
G_FAILCLOSED='76,82'  # fail-closed override of MODE when origin/main is unresolvable
G_ADDED='105,109'     # ADDED construction, all three modes
G_LOOP='114,136'      # the matching loop: parse, carve-out, count, decide
BLOCK_SELF=""; BLOCK_SUBJ=""; BLOCK_FAILCLOSED=""; BLOCK_ADDED=""; BLOCK_LOOP=""

load_blocks() {
  BLOCK_SELF="$(block "$G_SELF")"
  BLOCK_SUBJ="$(block "$G_SUBJ")"
  BLOCK_FAILCLOSED="$(block "$G_FAILCLOSED")"
  BLOCK_ADDED="$(block "$G_ADDED")"
  BLOCK_LOOP="$(block "$G_LOOP")"
  eval "$BLOCK_SELF"
}

# The gate's note() formats prose for a human; the harness needs a machine
# reading. Everything that DECIDES a hit — the parse, the carve-out, the count,
# the -gt 0 test — is still the gate's own bytes, eval'd from $BLOCK_LOOP.
note() { REC="${REC}$1${RS}${2-}"$'\n'; }

build_subject() {                 # $1 = mode, $2 = base
  MODE="$1"; BASE="$2"
  SUBJECT=""
  eval "$BLOCK_SUBJ"
}

build_added() {                   # transcription of gate :101-112; the case block
  ADDED=""                        # inside it is eval'd verbatim
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    [ -f "$f" ] || continue
    eval "$BLOCK_ADDED"
  done <<EOF
$SUBJECT
EOF
}

# scan runs the gate's matching loop in THIS shell (not a subshell: command
# substitution and a pipe would both discard the loop's FAIL and REC — the shape
# of a check that cannot fail) with stdout to a temp file.
scan() {
  local tmp; tmp="$(mktemp)"
  FAIL=0; REC=""
  eval "$BLOCK_LOOP" >"$tmp" 2>&1
  LAST_LOOP_OUT="$(cat "$tmp")"
  rm -f "$tmp"
  SCAN_ROWS=""
  local st msg nm h
  while IFS="$RS" read -r st msg; do
    [ -n "$st" ] || continue
    nm="${msg%% — *}"
    if [ "$msg" = "$nm" ]; then h=0; else h="${msg#* — }"; h="${h%% *}"; fi
    SCAN_ROWS="${SCAN_ROWS}${nm}"$'\t'"${h}"$'\n'
  done <<EOF
$REC
EOF
}
LAST_LOOP_OUT=""; SCAN_ROWS=""

hits_for() {                      # $1 = pattern name
  local nm h
  while IFS=$'\t' read -r nm h; do
    [ "$nm" = "$1" ] && { printf '%s' "$h"; return 0; }
  done <<EOF
$SCAN_ROWS
EOF
  printf 'MISSING'
}

# Counts NON-EMPTY lines. The gate appends a newline after every file's captured
# text (:106-108), so a file whose capture came back empty still contributes one
# blank line — and `grep -c ''` would report that as "one line rendered", hiding
# exactly the case this column exists to expose: a line the gate's own
# construction dropped.
rendered_lines() { printf '%s' "$ADDED" | grep -c '[^[:space:]]' || true; }

# mode_vacuity_guard: every mode MUST produce at least one rendered subject line
# and at least one non-zero hit across the whole matrix. An all-zero matrix is
# what a harness whose git commands ran in the wrong directory prints, and it
# looks exactly like ten dead nets — the shape AGENTS.md §6 item 2 warns about.
# So it is an error here, not a result.
mode_vacuity_guard() {
  local cells_tsv="$1" mode rows rendered hits
  for mode in $MODES; do
    rows="$(awk -F'\t' -v m="$mode" '$1==m' "$cells_tsv" | grep -c '')"
    rendered="$(awk -F'\t' -v m="$mode" '$1==m && $5+0 > 0' "$cells_tsv" | grep -c '')"
    hits="$(awk -F'\t' -v m="$mode" '$1==m && $4+0 > 0' "$cells_tsv" | grep -c '')"
    if [ "$rows" -eq 0 ] || [ "$rendered" -eq 0 ] || [ "$hits" -eq 0 ]; then
      note_fail "mode=$mode produced $rows rows, $rendered rendered lines, $hits non-zero hits — the matrix is vacuous, not a result"
    else
      printf '  ok mode=%-7s rows=%-4s rendered_lines_rows=%-4s non_zero_hit_rows=%s\n' "$mode" "$rows" "$rendered" "$hits"
    fi
  done
}

# ---------------------------------------------------------------- corpus
# A cell record is three fields separated by US (0x1f), not TAB: a file line may
# legitimately contain a tab, and a TAB-separated table would then lose a column
# silently — the same shape as the null-lookup failure in AGENTS.md §6 item 3.
CELLS=""
add_cell() { CELLS="${CELLS}$1${RS}$2${RS}$3"$'\n'; }

build_corpus() {
  CELLS=""
  local nm
  while IFS= read -r nm; do
    add_cell "A[$nm]"  "$(inst_of "$nm")"  'token alone on the line (at line start)'
    add_cell "B[$nm]"  "$(frag zz ' ' "$(inst_of "$nm")" ' ' zz)" 'token mid-line, uniform wrapper'
    add_cell "B2[$nm]" "$(wrap_of "$nm")" 'token mid-line, realistic embedding'
    add_cell "C[$nm]"  "$(frag + "$(inst_of "$nm")")" 'token at line start behind a leading +'
  done < <(pattern_names)
  # Negatives: zero hits required under EVERY pattern, in EVERY mode. A scanner
  # that fires on a clean line is reported, not tolerated (AGENTS.md §6 item 2).
  add_cell 'NEG-bare'  "$CLEAN"                          'clean, at line start'
  add_cell 'NEG-mid'   "$(frag 'prefix ' "$CLEAN" ' suffix')" 'clean, mid-line'
  add_cell 'NEG-plus'  "$(frag + "$CLEAN")"              'clean, behind a leading +'
  # Structural cell: content beginning with ++ is dropped by the ^+++ filter, so
  # its zero hits are a dropped line and NOT a pattern verdict.
  add_cell 'DROP-plusplus' "$(frag ++ "$CLEAN")"         'clean, content begins with ++ (gate drops it)'
  # The gate's own documented carve-out (gate :123-124).
  add_cell 'CARVE-AGENTS' "$(frag /home/ '<user>')"      'the string AGENTS.md documents, carve-out line'
}

# pattern_names: the gate's own parse, with the gate's own comment skip.
pattern_names() {
  local n p
  while IFS='|' read -r n p; do
    [ -z "$n" ] && continue
    [ -z "$p" ] && continue
    printf '%s\n' "$n"
  done < <(grep -v '^[[:space:]]*#' "$PAT_ABS")
}
count_patterns() { pattern_names | wc -l | tr -d ' '; }

# pattern_pairs: name TAB pattern, same parse. TAB is safe as the separator here
# because a pattern body may contain '|' but never a TAB.
pattern_pairs() {
  local n p
  while IFS='|' read -r n p; do
    [ -z "$n" ] && continue
    [ -z "$p" ] && continue
    printf '%s\t%s\n' "$n" "$p"
  done < <(grep -v '^[[:space:]]*#' "$PAT_ABS")
}

# classification: the three TEXTUAL properties the verdict table carries, read off
# the pattern file rather than typed into prose. These are string properties
# (OBSERVED in the source); the liveness verdict is measured, and the two are
# reported side by side precisely because a string property is not a verdict.
#   anchored    — every alternative starts at ^
#   caret_alt   — a '^' exists but only as one branch of an alternation
#   neg_letter  — a negated-letter class [^a-z] is present, i.e. an alternative
#                 that accepts ANY non-letter, which is what lets a '+' in front
#                 of the token still match
classify() {
  local n p anchored caret_alt neg_letter
  while IFS=$'\t' read -r n p; do
    case "$p" in
      '^'*) anchored=yes; caret_alt=no ;;
      *'(^|'*|*'|^'*) anchored=no; caret_alt=yes ;;
      *)    anchored=no; caret_alt=no ;;
    esac
    case "$p" in *'[^a-z]'*) neg_letter=yes ;; *) neg_letter=no ;; esac
    printf '%s\t%s\t%s\t%s\n' "$n" "$anchored" "$caret_alt" "$neg_letter"
  done < <(pattern_pairs)
}

# carveout_effect: a SUPPLEMENTARY, single-pattern measurement, deliberately not
# the gate's loop. It exists to quantify what gate :123-124 costs — the carve-out
# that drops the machine-path example AGENTS.md documents. It reports the count
# the pattern would produce on that line with NO carve-out, beside the count the
# gate actually recorded.
carveout_effect() {
  local line; line="$(frag /home/ '<user>')"
  local n p raw
  while IFS=$'\t' read -r n p; do
    [ "$n" = 'machine-specific paths' ] || continue
    raw="$(printf '%s' "$line" | grep -cEi "$p" || true)"
    printf '  %-24s pattern-only hits on the documented example (no carve-out): %s\n' "$n" "$raw"
  done < <(pattern_pairs)
  printf '  %-24s hits the gate recorded on the same cell (gate :123-124 applied): %s\n' \
    'machine-specific paths' \
    "$(awk -F'\t' '$1=="diff" && $2=="CARVE-AGENTS" && $3=="machine-specific paths" {print $4}' "$SCRATCH/cells.tsv")"
}

# ---------------------------------------------------------------- measurement
measure() {                       # $1 = output tsv
  local out_tsv="$1" mode cid line desc nm h rendered
  : > "$out_tsv"
  for mode in $MODES; do
    while IFS="$RS" read -r cid line desc; do
      [ -n "$cid" ] || continue
      printf '%s\n' "$line" > "$SCRATCH/synthetic.md"
      ( cd "$SCRATCH" && git add synthetic.md >/dev/null 2>&1 )
      build_subject "$mode" "$BASE"
      build_added
      rendered="$(rendered_lines)"
      scan
      while IFS= read -r nm; do
        h="$(hits_for "$nm")"
        [ "$h" = MISSING ] && { note_fail "scan loop never reported pattern ${nm@Q}"; h=0; }
        printf '%s\t%s\t%s\t%s\t%s\n' "$mode" "$cid" "$nm" "$h" "$rendered" >> "$out_tsv"
      done < <(pattern_names)
    done <<EOF
$CELLS
EOF
  done
}

init_repo() {
  ( cd "$SCRATCH" \
    && git init -q . \
    && mkdir -p scripts \
    && cp "$REPO/$PAT_REL" scripts/scrub-patterns.txt \
    && cmp -s "$REPO/$PAT_REL" scripts/scrub-patterns.txt \
    && printf '%s\n' 'scratch base line — replaced by every control cell' > synthetic.md \
    && git add synthetic.md \
    && git -c user.email=control@localhost -c user.name=control \
         commit -q -m 'scratch base' ) \
    || { note_fail "scratch repo setup failed"; return 1; }
  # Assigned from OUTSIDE the subshell: a `BASE=` inside it would die with the
  # subshell and every diff would silently be an empty diff.
  BASE="$( cd "$SCRATCH" && git rev-parse --verify HEAD )"
  [ -n "$BASE" ] || { note_fail "scratch repo has no base commit"; return 1; }
}

# ---------------------------------------------------------------- self-test
self_test() {
  echo "--- self-test: this harness must be able to fail ---"
  [ -r "$GATE" ] || { note_fail "cannot read $GATE"; return 1; }

  local b n nm missing sig
  b="$(block "$G_SELF")"
  case "$b" in *'SELF="scripts/research-gate.sh"'*) : ;;
                 *) note_fail "SELF not at gate lines $G_SELF — the gate moved" ;; esac
  case "$b" in *'SELF_PATTERNS="scripts/scrub-patterns.txt"'*) : ;;
                 *) note_fail "SELF_PATTERNS not at gate lines $G_SELF" ;; esac

  b="$(block "$G_SUBJ")"
  case "$b" in *'case "$MODE" in'*'esac'*) : ;;
                 *) note_fail "subject block $G_SUBJ is not a whole case statement" ;; esac
  case "$b" in *"git ls-files '*.md'"*) : ;;
                 *) note_fail "subject block lost its all-mode ls-files pathspec" ;; esac
  case "$b" in *"grep -E '\.(md|yml|yaml|sh|hurl)\$'"*) : ;;
                 *) note_fail "subject block lost its diff/staged extension filter" ;; esac

  # The fail-closed block, and it must be RUN rather than read. Verifier round 1,
  # F5: --screen eval'd every other block but not this one, so a checkout where
  # origin/main does not resolve produced an empty subject list, zero hits for
  # every pattern, and exit 0 — a green that had checked nothing.
  b="$(block "$G_FAILCLOSED")"
  for sig in 'git rev-parse --verify origin/main' 'MODE="all"' 'BASE=HEAD'; do
    case "$b" in *"$sig"*) : ;;
                   *) note_fail "fail-closed block $G_FAILCLOSED lost ${sig@Q}" ;; esac
  done
  # Behaviour, both directions, in a throwaway repo so $SCRATCH is untouched.
  fc_probe() {   # $1 = dir -> prints "MODE BASE" after the block has run
    ( cd "$1" && MODE="diff"; BASE="origin/main"; eval "$BLOCK_FAILCLOSED" >/dev/null 2>&1
      printf '%s %s\n' "$MODE" "$BASE" )
  }
  local fc r
  fc="$(mktemp -d)"
  ( cd "$fc" && git init -q . && printf 'x\n' > f.txt && git add f.txt \
      && git -c user.email=c@localhost -c user.name=c commit -qm base ) >/dev/null 2>&1
  r="$(fc_probe "$fc")"
  if [ "$r" = "all HEAD" ]; then
    note_ok "fail-closed block fires where origin/main cannot resolve (mode diff -> $r)"
  else
    note_fail "fail-closed block did NOT fire with no origin/main: got [$r], expected [all HEAD]"
  fi
  ( cd "$fc" && git update-ref refs/remotes/origin/main HEAD ) >/dev/null 2>&1
  r="$(fc_probe "$fc")"
  # On the non-fire path the gate's block still runs its assignment, so BASE
  # becomes the RESOLVED sha rather than the literal string it was given. Assert
  # on that: what matters is that MODE stayed diff and BASE got resolved.
  case "$r" in
    "diff "*) [ "${r#diff }" != "origin/main" ] \
        && note_ok "fail-closed block leaves a resolvable origin/main alone (mode stays diff, BASE resolved to ${r#diff })" \
        || note_fail "fail-closed block resolved nothing: got [$r]" ;;
    *) note_fail "fail-closed block flipped MODE although origin/main resolves: got [$r], expected [diff <sha>]" ;;
  esac
  rm -rf "$fc"

  # The two facts the area's premise rests on, counted rather than read: the
  # ADDED block carries exactly two '+'-prefixed paths and exactly one cat path.
  b="$(block "$G_ADDED")"
  case "$b" in *'case "$MODE" in'*'esac'*) : ;;
                 *) note_fail "ADDED block $G_ADDED is not a whole case statement" ;; esac
  n="$(printf '%s\n' "$b" | grep -c -F "grep '^+' | grep -v '^+++'")"
  [ "$n" = 2 ] && note_ok "ADDED block carries exactly 2 '+'-prefixed paths (staged :107 + diff :108)" \
                || note_fail "ADDED block carries $n '+'-prefixed paths, expected 2"
  n="$(printf '%s\n' "$b" | grep -c 'cat "\$f"')"
  [ "$n" = 1 ] && note_ok "ADDED block carries exactly 1 cat path (all :106)" \
                || note_fail "ADDED block carries $n cat paths, expected 1"

  b="$(block "$G_LOOP")"
  for sig in "IFS='|' read -r name pat" \
             '[ -z "$name" ] && continue' \
             '[ -z "$pat" ] && continue' \
             'grep -cEi "$pat"' \
             '[ "$hits" -gt 0 ]' \
             "grep -v '/home/<user>'"; do
    case "$b" in *"$sig"*) : ;;
                   *) note_fail "scan loop lost the signature ${sig@Q}" ;; esac
  done
  note_ok "scan loop keeps all 6 signatures (parse, both skips, count, decide, carve-out)"

  # gate :101-112 is transcribed rather than eval'd; assert the two lines the
  # transcription depends on are still there.
  b="$(block '101,112')"
  case "$b" in *'[ -f "$f" ] || continue'*'done <<EOF'*) : ;;
                 *) note_fail "file-loop wrapper (101-112) changed — re-read it" ;; esac

  # Ten patterns, each with a non-empty name AND regex. A harness iterating zero
  # patterns prints PASS (area K's scrub-check.sh): the count is asserted.
  n="$(count_patterns)"
  [ "$n" = 10 ] && note_ok "parsed $n patterns with the gate's own IFS='|' read" \
                || note_fail "parsed $n patterns, expected 10 — the measurement would be vacuous"

  missing=0
  while IFS= read -r nm; do
    inst_of "$nm" >/dev/null || { note_fail "no instance for pattern ${nm@Q}"; missing=1; }
    wrap_of "$nm" >/dev/null || { note_fail "no realistic wrapper for ${nm@Q}"; missing=1; }
    case "$nm" in *' — '*) note_fail "pattern name contains the gate's hit separator: ${nm@Q}"; missing=1 ;; esac
  done < <(pattern_names)
  [ "$missing" = 0 ] && note_ok "every pattern resolves to an instance + wrapper, and no name holds the hit separator"

  # frag() quote parity.
  [ "$(frag 'ab' 'cd')" = 'abcd' ] || note_fail "frag() does not concatenate"
  [ "$(frag 'a b')" = 'a b' ]         || note_fail "frag() ate a space"
  [ "$(frag '' '' '')" = '' ]         || note_fail "frag() invented characters"
  note_ok "frag() concatenation is exact (3 cells)"

  # The construction this file measures must still prefix a "+". If it stops, the
  # diff/staged verdicts below are measuring nothing.
  init_repo || return 1
  local rendered
  printf '%s\n' "$(frag 'SENTINEL token here')" > "$SCRATCH/synthetic.md"
  ( cd "$SCRATCH" && git add synthetic.md >/dev/null 2>&1 )
  rendered="$( cd "$SCRATCH" && git diff -U0 "$BASE" -- synthetic.md 2>/dev/null | grep '^+' | grep -v '^+++' )"
  [ "$rendered" = '+SENTINEL token here' ] \
    && note_ok "diff construction still emits a leading '+' (rendered exactly +SENTINEL token here)" \
    || note_fail "diff construction rendered [$rendered], expected [+SENTINEL token here]"

  # The ^+++ filter is positional: an added line whose CONTENT starts with '+'
  # renders as '+++...', indistinguishable from the file header, and is dropped.
  # A content line starting with a SINGLE '+' renders as '++...' and survives.
  # That is a different effect from a pattern failing to match, so it is asserted
  # here rather than assumed.
  printf '%s\n%s\n' "$(frag ++ 'SENTINEL token here')" "$(frag 'SECOND line')" > "$SCRATCH/synthetic.md"
  ( cd "$SCRATCH" && git add synthetic.md >/dev/null 2>&1 )
  rendered="$( cd "$SCRATCH" && git diff -U0 "$BASE" -- synthetic.md 2>/dev/null | grep '^+' | grep -v '^+++' )"
  [ "$rendered" = '+SECOND line' ] \
    && note_ok "the ^+++ filter drops an added line whose content begins with '++' — positional, not a marker test" \
    || note_fail "^+++ filter behaved unexpectedly: [${rendered//$'\n'/ | }]"

  printf '%s\n%s\n' "$(frag '+SENTINEL token here')" "$(frag 'SECOND line')" > "$SCRATCH/synthetic.md"
  ( cd "$SCRATCH" && git add synthetic.md >/dev/null 2>&1 )
  rendered="$( cd "$SCRATCH" && git diff -U0 "$BASE" -- synthetic.md 2>/dev/null | grep '^+' | grep -v '^+++' )"
  case "$rendered" in
    '++SENTINEL token here'*) : ;;
    *) note_fail "an added line whose content begins with a single '+' did not survive as '++...': [${rendered//$'\n'/ | }]" ;;
  esac

  # F5 regression, at the entry point a reader actually uses. --screen invoked
  # from a directory that is NOT the repo root must still screen the repo. Before
  # the fix, gate :136's relative pattern path resolved to nothing there, the
  # subject list came back empty, and the run printed "no pattern fired" and
  # exited 0 — a green that had read no file at all.
  local sdir sout
  sdir="$(mktemp -d)"
  sout="$( cd "$sdir" && bash "$HERE/scrub-diffmode-control.sh" --screen 2>&1 )"
  case "$sout" in
    *"HEAD "*) : ;;
    *) note_fail "--screen from a foreign cwd did not report which tree it screened" ;;
  esac
  if printf '%s' "$sout" | grep -q 'subject files: 0'; then
    note_fail "--screen from a foreign cwd screened 0 subject files — the F5 defect is back"
  else
    note_ok "--screen is cwd-independent: from a foreign directory it still screens the repo root"
  fi
  rm -rf "$sdir"
}

# ---------------------------------------------------------------- mutation test
# Prove the measurement reacts to the thing it claims to measure: strip the ^ from
# the one anchored pattern in the scratch copy and assert the diff-mode verdict
# MOVES. A harness that cannot fail is not evidence.
mutation_test() {
  echo "--- mutation test: de-anchor the anchored net, expect the verdict to move ---"
  local before after
  printf '%s\n' "$(frag 'zz ' "$INST_RECAPTCHA" ' zz')" > "$SCRATCH/synthetic.md"
  ( cd "$SCRATCH" && git add synthetic.md >/dev/null 2>&1 )
  build_subject diff "$BASE"; build_added; scan
  before="$(hits_for 'reCAPTCHA site keys')"
  [ "$before" = 0 ] \
    || note_fail "baseline: the anchored net was expected to read 0 mid-line in diff mode, got $before"

  # Both anchors are stripped, not just ^: the pattern is ^…$ , so removing only the
  # leading anchor leaves the trailing one and the mutation would prove nothing.
  # Delimiter is @, not |: the pattern file's own separator is a pipe, and a
  # | -delimited s/// silently deletes the whole line instead of de-anchoring it.
  ( cd "$SCRATCH" \
    && sed -i 's@^reCAPTCHA site keys|\^\(.*\)\$$@reCAPTCHA site keys|\1@' scripts/scrub-patterns.txt )
  if cmp -s "$PAT_ABS" "$SCRATCH/scripts/scrub-patterns.txt"; then
    note_fail "the mutation did not change the scratch pattern file"
  fi
  grep -q '^reCAPTCHA site keys|[^^$]' "$SCRATCH/scripts/scrub-patterns.txt" \
    || note_fail "the mutant pattern still carries an anchor: $(grep '^reCAPTCHA site keys|' "$SCRATCH/scripts/scrub-patterns.txt")"
  scan
  after="$(hits_for 'reCAPTCHA site keys')"
  if [ "$after" -gt 0 ] 2>/dev/null; then
    note_ok "de-anchoring moved its diff-mode hits $before -> $after: the measurement reacts to the construct"
  else
    note_fail "de-anchoring did NOT move the diff-mode hits ($before -> ${after}): the harness cannot detect what it measures"
  fi
  cp "$REPO/$PAT_REL" "$SCRATCH/scripts/scrub-patterns.txt"
  scan
  [ "$(hits_for 'reCAPTCHA site keys')" = "$before" ] \
    || note_fail "restoring the pattern file did not restore the baseline"
  note_ok "baseline restored after the mutation"
}

# ---------------------------------------------------------------- verdicts
# liveness(P, mode) is decided over the instance cells that RENDER in that mode. A
# cell whose subject text came out empty was dropped by the gate's own
# construction, so its zero is not a pattern verdict and is not counted.
verdicts() {
  local cells_tsv="$1"
  printf 'pattern\tmode\tcells\trendered\tfiring\tverdict\n'
  local nm mode cid row h r fired rendered
  while IFS= read -r nm; do
    for mode in $MODES; do
      fired=0; rendered=0
      for cid in "A[$nm]" "B[$nm]" "B2[$nm]" "C[$nm]"; do
        # One row per (mode, cell, pattern) — and a cell id carries its pattern's
        # name, so all THREE keys are needed. Filtering on two returns 10 rows.
        row="$(awk -F'\t' -v m="$mode" -v c="$cid" -v n="$nm" \
               '$1==m && $2==c && $3==n {print $4"\t"$5}' "$cells_tsv")"
        [ -n "$row" ] || { note_fail "no cells.tsv row for $mode $cid / $nm"; continue; }
        case "$row" in *$'\n'*) note_fail "ambiguous cells.tsv rows for $mode $cid / $nm"; continue ;; esac
        h="${row%%$'\t'*}"; r="${row#*$'\t'}"
        [ "$r" -gt 0 ] 2>/dev/null && rendered=$((rendered + 1))
        [ "$h" -gt 0 ] 2>/dev/null && fired=$((fired + 1))
      done
      local v
      if [ "$rendered" -eq 0 ]; then v='no-cell-rendered'
      elif [ "$fired" -gt 0 ]; then v='live'
      else v='dead'; fi
      printf '%s\t%s\t4\t%d\t%d\t%s\n' "$nm" "$mode" "$rendered" "$fired" "$v"
    done
  done < <(pattern_names)
}

check_negatives() {
  local cells_tsv="$1" mode cid nm h r bad=0 rows=0
  while IFS=$'\t' read -r mode cid nm h r; do
    case "$cid" in NEG-*|DROP-*|CARVE-*) rows=$((rows + 1))
      if [ "$h" -ne 0 ] 2>/dev/null; then
        printf '  !! nonzero on a clean cell: mode=%s cell=%s pattern=%s hits=%s\n' "$mode" "$cid" "$nm" "$h"
        bad=$((bad + 1))
      fi ;;
    esac
  done < "$cells_tsv"
  if [ "$bad" -eq 0 ]; then
    printf '  ok all %d clean-cell rows read 0 under every pattern in every mode\n' "$rows"
  else
    note_fail "$bad clean-cell row(s) fired — the scanner is not trustworthy on clean input"
  fi
}

# ---------------------------------------------------------------- screen
# The gate's leak-scan path, verbatim, over this repository's own diff. Static
# only: the 05 vendor suite is NOT run (the pool serialises suites).
screen() {
  local rc=0 want tmp st msg f
  load_blocks
  # The gate's loop reads `scripts/scrub-patterns.txt` by RELATIVE path (:136) and
  # its subject block runs bare `git`, so the directory this mode runs in IS the
  # input. Enter the repo explicitly and assert it, rather than letting the
  # caller's cwd decide what gets scanned — run from anywhere else, :136 iterates
  # nothing, every pattern reads 0, and the screen exits 0 having checked no file
  # at all. That is the "check that cannot fail" shape this harness exists to
  # close, in the one mode a reader is told to re-run (verifier round 1, F5).
  cd "$REPO" || { echo "screen: cannot enter $REPO"; return 1; }
  # Name the tree being screened. A transcript that does not say which commit it
  # read cannot be re-derived, and its counts go stale the moment a doc line moves.
  # Only the BASENAME is printed: the first version of this line printed $REPO
  # whole, which put an absolute home path into a committed artefact, and the
  # gate's own machine-path net fired on the transcript of its own screen.
  echo "--- screen: repo $(basename "$REPO"), HEAD $(git rev-parse --verify HEAD 2>/dev/null || echo UNRESOLVED), dirty $(git status --porcelain 2>/dev/null | grep -c '') file(s) ---"
  # Pre-flight, before any count is printed: the path the gate's loop reads and
  # the absolute copy this harness parsed must be the same file.
  if [ ! -r scripts/scrub-patterns.txt ]; then
    echo "screen: !! gate :136 reads scripts/scrub-patterns.txt relative to the cwd, unreadable from $PWD"
    return 1
  fi
  local rel_abs; rel_abs="$(cd "$(dirname scripts/scrub-patterns.txt)" && pwd)/$(basename scripts/scrub-patterns.txt)"
  if [ "$rel_abs" != "$PAT_ABS" ]; then
    echo "screen: !! gate :136 would read $rel_abs but this harness parsed $PAT_ABS"
    return 1
  fi
  local np; np="$(count_patterns)"
  if [ "${np:-0}" -eq 0 ]; then
    echo "screen: !! parsed $np patterns — refusing to report a clean scan over zero patterns"
    return 1
  fi
  for want in diff all; do
    MODE="$want"; BASE="origin/main"
    eval "$BLOCK_FAILCLOSED"      # the gate's own override (:76-82) — without it a
    # missing origin/main yields an empty subject list and a silent pass, which is
    # the same defect as an unreadable pattern file.
    build_subject "$MODE" "$BASE"
    build_added
    echo "--- screen: gate leak scan over this branch's diff, mode=$MODE (requested $want), subject files: $(printf '%s' "$SUBJECT" | grep -c '') ---"
    if [ -z "$SUBJECT" ]; then
      echo "  !! no subject files for mode $MODE — a scan that reads nothing is not a clean scan"
      rc=1; continue
    fi
    tmp="$(mktemp)"
    FAIL=0; REC=""
    eval "$BLOCK_LOOP" >"$tmp" 2>&1
    echo "  gate loop FAIL flag: $FAIL, loop verdicts recorded: $(printf '%s' "$REC" | grep -c '')"
    if [ "$(printf '%s' "$REC" | grep -c '')" -ne "$np" ]; then
      echo "  !! the loop recorded $(printf '%s' "$REC" | grep -c '') verdicts for $np patterns — a partial loop is not a clean loop"
      rc=1
    fi
    while IFS="$RS" read -r st msg; do
      [ -n "$st" ] || continue
      if [ "$st" = '!!' ]; then echo "  !! $msg"; rc=1; fi
    done <<EOF
$REC
EOF
    rm -f "$tmp"
  done
  # Re-derivability key. A transcript that names only a commit cannot be checked
  # against a LATER commit, and this file is committed, so the commit it ships in
  # cannot be named inside itself (verifier round 1, F6 — the previous
  # self-screen.txt recorded a line count matching neither commit it could have
  # been taken at, and named neither). So print the digest of the exact subject
  # list and the exact line count it scanned: a reader who checks out any later
  # commit and re-runs gets the same pair if and only if nothing the gate reads
  # moved. That is the property a committed transcript needs.
  MODE="all"; BASE="origin/main"
  eval "$BLOCK_FAILCLOSED"
  build_subject "$MODE" "$BASE"
  build_added
  echo "--- re-derivable key: --all subject list sha256 $(printf '%s' "$SUBJECT" | sha256sum | cut -d' ' -f1), non-empty subject lines $(printf '%s' "$ADDED" | grep -c '[^[:space:]]') ---"
  # The machine-path carve-out (gate :123-124) is the loop's only per-pattern
  # special case. Quantify it over the REAL --all subject text, not a synthetic
  # cell, so the number describes the repo as it stands.
  echo '--- carve-out over the real --all subject text (supplementary; pattern applied directly) ---'
  MODE="all"; BASE="origin/main"
  eval "$BLOCK_FAILCLOSED"
  build_subject "$MODE" "$BASE"
  build_added
  if [ -z "$SUBJECT" ]; then
    echo '  !! no --all subject files — the carve-out would read nothing and 0 would mean nothing'
    rc=1
  fi
  local mp raw gated
  mp="$(pattern_pairs | awk -F'\t' '$1=="machine-specific paths"{print $2}')"
  raw="$(printf '%s' "$ADDED" | grep -cEi "$mp" || true)"
  gated="$(printf '%s' "$ADDED" | grep -v '/home/<user>' | grep -cEi "$mp" || true)"
  echo "  subject files: $(printf '%s' "$SUBJECT" | grep -c '')"
  echo "  subject lines in the --all text: $(printf '%s' "$ADDED" | grep -c '[^[:space:]]')"
  # What the carve-out actually removes. "Not load-bearing" is a claim about the
  # HIT COUNT; "excludes nothing" would be a claim about the TEXT, and the two are
  # not the same. Verifier round 1, F4: this pass said "excludes nothing" while
  # the filter was dropping real lines. Count both.
  echo "  lines the carve-out drops (grep -v '/home/<user>'): $(($(printf '%s' "$ADDED" | grep -c '') - $(printf '%s' "$ADDED" | grep -v '/home/<user>' | grep -c '')))"
  echo "  lines carrying the literal /home/<user>: $(printf '%s' "$ADDED" | grep -cF '/home/<user>' || true)"
  echo "  machine-specific paths, carve-out NOT applied: $raw"
  echo "  machine-specific paths, carve-out applied (gate :124): $gated"
  # Positive control, so "not load-bearing" is never read as "disabled": a REAL
  # machine path must fire, and must survive the carve-out. The instance is taken
  # from INST_HOMEPATH, which is itself assembled from fragments at runtime.
  # Writing the example path the gate documents into this script instead is what
  # makes it fail its own screen, for two reasons that are worth keeping apart:
  # this file is a .sh, so it IS in the --all and diff subject sets; and the
  # carve-out drops a WHOLE LINE that carries the documented example. Neither was
  # hypothetical — the first version of this control named both paths on one
  # comment line, and `--screen` went red on the harness itself. See FINDINGS.md
  # §3c for what that accidental commit measured.
  local pc
  pc="$(frag 'cd ' "$INST_HOMEPATH" '/projects')"
  echo "  control, a real machine path, carve-out NOT applied: $(printf '%s' "$pc" | grep -cEi "$mp" || true) (expect 1)"
  echo "  control, the same line, carve-out applied:           $(printf '%s' "$pc" | grep -v '/home/<user>' | grep -cEi "$mp" || true) (expect 1 — the carve-out must not blanket-disable the net)"
  # docs/09 §4: all three leak-scan modes choose subjects by EXTENSION, so the
  # .tsv / .jsonl / .log artefacts this pass commits are read by no pattern in
  # any mode. Screen this log directory by hand, through the same loop.
  echo "--- screen: the gate's loop over EVERY file in this log dir, all extensions ---"
  # Snapshot first. When this mode's own stdout is redirected into self-screen.txt
  # (the committed transcript), the loop would otherwise read that file while the
  # shell is still writing it, and the transcript would depend on stdout buffering.
  # A committed artefact has to be byte-reproducible, so the bytes under test are
  # taken once, up front, from a snapshot.
  local snap; snap="$(mktemp -d)"
  cp "$HERE"/* "$snap"/ 2>/dev/null
  for f in "$snap"/*; do
    [ -f "$f" ] || continue
    ADDED="$(cat "$f")"
    scan
    while IFS="$RS" read -r st msg; do
      [ -n "$st" ] || continue
      if [ "$st" = '!!' ]; then echo "  !! $(basename "$f"): $msg"; rc=1; fi
    done <<EOF
$REC
EOF
  done
  rm -rf "$snap"
  [ "$rc" -eq 0 ] && echo '  ok no pattern fired on any committed artefact in this log directory'
  return $rc
}

# ---------------------------------------------------------------- main
case "${1:-}" in
  --self-test)
    SCRATCH="$(mktemp -d)"; trap 'rm -rf "$SCRATCH"' EXIT
    # The measurement branches cd into the scratch repo and never cd back: the
    # gate's git commands are bare (`git diff --name-only ... "$BASE"`), so the
    # directory they run in IS the subject source. Running them in the real repo
    # yields an empty subject list and an all-zero matrix that reads like ten
    # dead nets.
    cd "$SCRATCH" || exit 1
    load_blocks
    self_test
    if [ "$FAILURES" -ne 0 ]; then
      echo "SELF-TEST FAILED — $FAILURES assertion(s). No verdict from this harness is admissible."
      exit 1
    fi
    echo 'SELF-TEST PASS'
    ;;
  --screen)
    screen
    exit $?
    ;;
  '')
    SCRATCH="$(mktemp -d)"; trap 'rm -rf "$SCRATCH"' EXIT
    cd "$SCRATCH" || exit 1          # see --self-test: cwd IS the subject source
    load_blocks
    echo 'scratch: <mktemp dir, removed on exit> — it holds the only un-elided copy of the rendered subject lines'
    self_test
    if [ "$FAILURES" -ne 0 ]; then
      echo "SELF-TEST FAILED — $FAILURES assertion(s); refusing to measure."
      exit 1
    fi
    build_corpus
    echo "--- measurement: $(printf '%s' "$CELLS" | grep -c '') cells x $(count_patterns) patterns x 3 modes, gate bytes eval'd ---"
    measure "$SCRATCH/cells.tsv"
    mutation_test
    echo '--- vacuity guard ---'
    mode_vacuity_guard "$SCRATCH/cells.tsv"
    echo '--- negatives ---'
    check_negatives "$SCRATCH/cells.tsv"
    echo '--- per-cell detail (a cell row, plus every cross-match) ---'
    awk -F'\t' '($2 ~ ("\\[" $3 "\\]$")) || $4+0 > 0 {printf "  %-7s %-52s %-46s hits=%-2s rendered_lines=%s\n", $1, $2, $3, $4, $5}' \
        "$SCRATCH/cells.tsv"
    echo '--- structural cells (rendered_lines 0 = the gate dropped the line before any pattern saw it) ---'
    for c in DROP-plusplus CARVE-AGENTS NEG-bare NEG-mid NEG-plus; do
      for mode in $MODES; do
        rendered="$(awk -F'\t' -v m="$mode" -v c="$c" '$1==m && $2==c {print $5; exit}' "$SCRATCH/cells.tsv")"
        nonzero="$(awk -F'\t' -v m="$mode" -v c="$c" '$1==m && $2==c && $4+0>0' "$SCRATCH/cells.tsv" | grep -c '')"
        printf '  %-7s %-16s rendered_lines=%-2s patterns_with_hits=%s/10\n' "$mode" "$c" "${rendered:-?}" "$nonzero"
      done
    done
    echo '--- classification (string properties of the pattern file; NOT the verdict) ---'
    printf '  %-46s %-8s %-9s %s\n' pattern anchored_at_^ caret_in_alt negated_letter_class
    classify | while IFS=$'\t' read -r n a ca nl; do
      printf '  %-46s %-8s %-9s %s\n' "$n" "$a" "$ca" "$nl"
    done
    echo '--- carve-out effect (supplementary: one pattern applied directly, NOT the gate loop) ---'
    carveout_effect
    echo '--- verdicts ---'
    verdicts "$SCRATCH/cells.tsv" | column -t -s$'\t'
    # The matrix carries pattern names and integers only — no instance text, so
    # both files are safe to commit (the raw rendered lines stay in the scratch).
    cp "$SCRATCH/cells.tsv" "$HERE/cells.tsv"
    verdicts "$SCRATCH/cells.tsv" > "$HERE/verdicts.tsv"
    if [ "$FAILURES" -ne 0 ]; then echo "HARNESS FAILURES: $FAILURES"; exit 1; fi
    echo
    echo "cells.tsv and verdicts.tsv written beside this script; they hold no instance text."
    ;;
  *)
    echo "usage: $0 [--self-test|--screen]" >&2
    exit 2
    ;;
esac