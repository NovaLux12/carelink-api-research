#!/usr/bin/env bash
# grep.sh — the offline half of the area F pass (corpus grep), zero requests.
#
# WHAT IT ANSWERS. Area F's letter question is "how does the portal call
# patient-timeline / dialog-lite?" (docs/11-suggested-research-areas.md:209).
# The only way to get that far from outside is to read the vendor's own portal
# builds. Area V did this for the PATIENT bundle on 2026-10-13; nobody had ever
# done it for the two PORTAL builds, which is the gap this pass closes.
#
# THE TWO GATES, IN THIS ORDER. A negative from a corpus that is not the corpus
# is worse than no answer, so:
#   1. ANCHOR GATE — the body must hash to the anchor this repo already pins
#      for that build (2a7fa8e7... clinic, a054555a... support). A body that
#      does not reproduce its anchor is NOT analysed, and the script exits 1.
#   2. METHOD GATE — at least one literal KNOWN to be present must be reported
#      present. A grep that finds nothing is indistinguishable from a broken
#      grep; this is the "a hit proves the token exists, not that it means what
#      you assumed" trap of AGENTS.md section 6 item 2, run in the other
#      direction: a MISS must be proven to be a miss.
#
# CANDIDATE LIST, AND WHY EACH TOKEN IS HERE. Bounded and justified; no
# wordlist. Every token is either (a) a name this repo already has on record,
# or (b) the literal spelling a caller would have to contain to reach the
# service at all.
#   patient-timeline                   the published path segment (docs/00)
#   dialog-lite                         the published path segment (docs/00)
#   app-patient-timeline                the Angular component selector the
#                                      PATIENT bundle carries 5 of (area V) --
#                                      included so the portal builds' 0 can be
#                                      compared against a known-positive
#   patientTimeline                     camelCase spelling of the service name
#   personal.patient.timeline.config    the PUBLISHED config key (docs/04)
#   personal.patient.timeline.host      the key the bundle names and the
#                                      document does NOT publish (area V)
#   execute-api                         the AWS API Gateway hostname pattern
#                                      every published host value uses
#   <five 10-char gateway ids>          the actual gateway ids, published in
#                                      findings-log/2026-10-12-published-pointers/
#                                      enumeration-scrubbed.txt lines 83/121/
#                                      155/187/245 -- a caller must name one
#   prodous                             the dialog-lite stage prefix
#   m2m                                 the call pattern area F's own text names
#                                      (docs/11:222) -- included PRECISELY
#                                      because it is expected to false-hit
#   baseUrl                             shape probe: does either build read a
#                                      CareLink API base from config at all?
#   hcp/configuration/public/           the namespace these builds DO read
#   hcp/patients                        the namespace these builds DO call
#   timeline                            the UNQUALIFIED form. Present so the
#                                      false-hit class is quantified, not
#                                      asserted: if `timeline` scores high and
#                                      `patient-timeline` scores 0, that is
#                                      the whole finding.
#   personal.                           the patient-document key prefix: 0 hits
#                                      means no patient config key is read
#
# USAGE. The bodies are NOT committed (AGENTS.md section 7: no raw captures,
# and a 3.4 MB bundle would also breach the 1 MiB per-file log limit). Re-fetch
# them with ./probe.sh --bundles-only is NOT supported; run the two bundle rows
# of probe.sh, then:
#     ./grep.sh <clinic.js> <support.js>
#
# Zero requests. No network access at all.

set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1

CLINIC_ANCHOR="2a7fa8e7af519c2b"
SUPPORT_ANCHOR="a054555a0f22176e"

TOKENS=(
  'patient-timeline'
  'dialog-lite'
  'app-patient-timeline'
  'patientTimeline'
  'personal.patient.timeline.config'
  'personal.patient.timeline.host'
  'execute-api'
  '0ptoikank6'
  'r5djbmetbb'
  'd4mwt26mmi'
  '7r9xxd72kk'
  'oflhmnvbe6'
  'prodous'
  'm2m'
  'baseUrl'
  'hcp/configuration/public/'
  'hcp/patients'
  '/patient/'
  'clcloud'
  'carelink.minimed'
  'timeline'
  'Timeline'
  'TIMELINE'
  'personal.'
)
# The literals this repo already KNOWS are in these two builds. The method gate
# requires each of them to be reported present, by name. A total count is not
# enough: a threshold can be met by false hits (two of the tokens above are
# false hits by construction -- `m2m` lands inside a password-dictionary word and
# `baseUrl` lands inside a vendored SDK), so a count-based gate can pass on a
# broken grep.
MUST_BE_PRESENT=(
  'hcp/configuration/public/'
  'hcp/patients'
  'timeline'
)

printf '=== corpus grep, area F, zero requests, %s\n' "$(date -u +%FT%T.%3NZ)"
for f in "$@"; do
  [ -f "$f" ] || { printf 'MISSING BODY: %s\n' "$(basename "$f")"; exit 2; }
done

for f in "$@"; do
  sha="$(sha256sum "$f" | cut -c1-16)"
  size="$(stat -c%s "$f")"
  # Identified by its sha256 anchor, not by its path: AGENTS.md section 7
  # forbids committing a machine-specific path, and the anchor is the thing
  # that has to be reproducible anyway.
  printf '\n## body %s (sha256_16=%s)\n' "$(basename "$f")" "$sha"
  printf 'bytes=%s sha256_16=%s\n' "$size" "$sha"
  case "$sha" in
    "$CLINIC_ANCHOR"*) printf 'ANCHOR GATE: PASS (clinic %s)\n' "$CLINIC_ANCHOR" ;;
    "$SUPPORT_ANCHOR"*) printf 'ANCHOR GATE: PASS (support %s)\n' "$SUPPORT_ANCHOR" ;;
    *) printf 'ANCHOR GATE: **FAIL** — sha %s matches no pinned anchor; NOT ANALYSED\n' "$sha"
       exit 1 ;;
  esac
  printf '\n%-38s %s\n' 'token' 'occurrences'
  present=0
  for t in "${TOKENS[@]}"; do
    n="$(grep -o -a -F -e "$t" "$f" | wc -l | tr -d ' ')"
    printf '%-38s %s\n' "$t" "$n"
    [ "$n" -gt 0 ] && present=$((present + 1))
  done
  if [ "$present" -lt 3 ]; then
    printf 'METHOD GATE: **FAIL** — only %s literals reported present; a grep that\n' "$present"
    printf 'finds almost nothing cannot distinguish "absent" from "broken". NOT ANALYSED.\n'
    exit 1
  fi
  gate_failed=0
  for t in "${MUST_BE_PRESENT[@]}"; do
    n="$(grep -o -a -F -e "$t" "$f" | wc -l | tr -d ' ')"
    if [ "$n" -gt 0 ]; then
      printf 'METHOD GATE: ok   known-present literal %-30s %s hits\n' "$t" "$n"
    else
      printf 'METHOD GATE: FAIL known-present literal %-30s 0 hits\n' "$t"
      gate_failed=1
    fi
  done
  [ "$gate_failed" -ne 0 ] && { printf 'NOT ANALYSED — the grep cannot see what is known to be there.\n'; exit 1; }
  printf 'METHOD GATE: PASS (%s literals present)\n' "$present"
  printf '\n-- every occurrence, with +-45 bytes of context, token marked --\n'
  for t in "${TOKENS[@]}"; do
    n="$(grep -o -a -F -e "$t" "$f" | wc -l | tr -d ' ')"
    [ "$n" -eq 0 ] && continue
    [ "$n" -gt 12 ] && printf '\n[%s] %s hits — first 12 only\n' "$t" "$n"
    grep -o -a -b -P ".{0,45}\Q$t\E.{0,45}" "$f" 2>/dev/null | head -12 \
      || grep -o -a -b -F -e "$t" "$f" | head -12 | cut -c1-120
  done
  # The classification evidence for the headline negative. `timeline` scores
  # high and `patient-timeline` scores 0, so the reader needs to see WHAT every
  # `timeline` occurrence actually is -- as distinct signatures, exhaustively,
  # rather than as a count they have to take on trust.
  #
  # COUNTING RULE for this census, so the total can be re-derived: each
  # occurrence contributes exactly one signature, formed from up to 18
  # word-characters of LEFT context plus the matched token and NO right
  # context. A right-context form was tried first and returns 189 rather than
  # 196, because greedy right context swallows a following token in the same
  # identifier -- so the 189 figure is a defect of that pattern, not a count of
  # anything. The census total must equal 66 + 126 + 4 = 196.
  printf '\n-- `timeline` signature census, EVERY occurrence classified by the\n'
  printf '   identifier characters to its LEFT. Counting rule: one signature per\n'
  # shellcheck disable=SC2016
  printf '   occurrence, <=18 left word-chars, no right context. Total must be 196.\n'
  grep -o -a -P '[A-Za-z0-9_.$-]{0,18}?(?:timeline|Timeline|TIMELINE)' "$f" \
    | sort | uniq -c | sort -rn
done
printf '\n=== done, zero requests\n'