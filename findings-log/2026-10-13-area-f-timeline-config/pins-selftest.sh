#!/usr/bin/env bash
# pins-selftest.sh — prove the six AREA F assertions in
# regression/hurl/05-public-config.check.sh CAN FAIL, offline.
#
# WHY THIS FILE EXISTS
# --------------------
# That suite's AREA F block makes two claims that only mean something if they are
# demonstrably falsifiable:
#
#   "Pinned as the EXACT sorted member list, not has(\"featureEnabled\") ... The
#    jq expression was checked against a synthetic document carrying a third
#    member, and returns the other string, so this can fail."
#   "Anchored on ^$ so it cannot be satisfied by a longer name that merely
#    contains this one; the same expression returns 1 against a document that
#    does carry the key."
#
# A check that cannot fail is worse than no check (docs/09 section 5 item 1: a
# check that *looks* like it ran converts a gap into a green tick). Both claims
# were asserted in prose with the evidence living only in the author's shell, and
# verification on 2026-10-13 correctly called that out. This file is the evidence.
#
# ZERO vendor requests. jq only, against synthetic documents built from the
# committed 69-name key list (findings-log/2026-10-13-area-w-per-key/keys.txt) —
# the names are area W's committed artefact, not hand-typed, so a fixture that
# drifts from the real vocabulary would show up here.
#
# Exits 0 only if every pin discriminates. A pin that cannot fail is a defect.
set -uo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
KEYS="$DIR/../2026-10-13-area-w-per-key/keys.txt"
TMPD=$(mktemp -d)
trap 'rm -rf "$TMPD"' EXIT

FAIL=0
note() { printf '  %s\n' "$1"; }
bad()  { printf '  FAIL %s\n' "$1"; FAIL=$((FAIL + 1)); }
ok()   { printf '  ok   %s\n' "$1"; }

# --- build the fixture: the 69 published names, values irrelevant -----------
build() { # build <outfile>
  jq -Rn '[inputs]' "$KEYS" | jq '. as $names
    | reduce $names[] as $n ({}; .[$n] = "fixture")' > "$1"
}
# the real observed shape for the one member row that matters
with_config() { # with_config <in> <out>
  jq '. + {"personal.patient.timeline.config":
             {"featureEnabled": true, "host": "https://example.invalid/x"}}' "$1" > "$2"
}

build "$TMPD/base.json"
with_config "$TMPD/base.json" "$TMPD/good.json"

# The two filters, copied from the AREA F block of the suite. Step 0 below PROVES
# the copies are still equal, so "copy, don't import" is not merely a discipline note:
# an import would let a change to one silently escape the other, while a stale copy
# would make every result below a proof about the wrong string.
F_MEMBER='.["personal.patient.timeline.config"] | keys | sort | join(",")'
F_NOHOST='[keys[] | select(test("^personal[.]patient[.]timeline[.]host$"))] | length'
SUITE="$DIR/../../regression/hurl/05-public-config.check.sh"
SUITE_MEMBERS=3   # one check per deployment
SUITE_NOHOST=3

echo "--- pins-selftest: can the AREA F assertions fail? ---"

echo "0. the copies must still equal the suite's filters"
if [ ! -f "$SUITE" ]; then
  bad "suite not found at the expected path — cannot prove the copies are equal"
else
  n=$(grep -cF -- "$F_MEMBER" "$SUITE")
  if [ "$n" -eq "$SUITE_MEMBERS" ]; then
    ok "F_MEMBER appears verbatim $n/$SUITE_MEMBERS times in the suite"
  else
    bad "F_MEMBER appears $n times in the suite, expected $SUITE_MEMBERS — the copy has drifted and every result below is about the wrong string"
  fi
  n=$(grep -cF -- "$F_NOHOST" "$SUITE")
  if [ "$n" -eq "$SUITE_NOHOST" ]; then
    ok "F_NOHOST appears verbatim $n/$SUITE_NOHOST times in the suite"
  else
    bad "F_NOHOST appears $n times in the suite, expected $SUITE_NOHOST — the copy has drifted"
  fi
fi

echo "1. the real shape satisfies both pins"
got_member=$(jq -r "$F_MEMBER" "$TMPD/good.json")
got_nohost=$(jq -r "$F_NOHOST" "$TMPD/good.json")
[ "$got_member" = "featureEnabled,host" ] \
  && ok "member-set pin satisfied by the real shape ($got_member)" \
  || bad "member-set pin NOT satisfied by the real shape (got '$got_member')"
[ "$got_nohost" = "0" ] \
  && ok "absent-key pin satisfied by the real shape ($got_nohost)" \
  || bad "absent-key pin NOT satisfied by the real shape (got '$got_nohost')"

echo "2. a THIRD member must break the member-set pin"
jq '.["personal.patient.timeline.config"] += {"refreshIntervalSeconds": 30}' \
  "$TMPD/good.json" > "$TMPD/extra.json"
got=$(jq -r "$F_MEMBER" "$TMPD/extra.json")
if [ "$got" != "featureEnabled,host" ] && [ "$got" = "featureEnabled,host,refreshIntervalSeconds" ]; then
  ok "member-set pin FAILS on a third member, as claimed -> '$got'"
else
  bad "member-set pin did NOT fail on a third member (got '$got') — it cannot see this"
fi

echo "3. the bundle's stale key, if published, must break the absent-key pin"
jq '. + {"personal.patient.timeline.host": {"x": 1}}' \
  "$TMPD/good.json" > "$TMPD/withhost.json"
got=$(jq -r "$F_NOHOST" "$TMPD/withhost.json")
[ "$got" = "1" ] \
  && ok "absent-key pin FAILS when the key is present, as claimed -> $got" \
  || bad "absent-key pin did NOT fail when the key was present (got '$got')"

echo "4. the ^\$ anchor must NOT fire on a longer name that merely contains it"
jq '. + {"personal.patient.timeline.hostXYZ": 1, "xpersonal.patient.timeline.host": 2}' \
  "$TMPD/good.json" > "$TMPD/longer.json"
got=$(jq -r "$F_NOHOST" "$TMPD/longer.json")
[ "$got" = "0" ] \
  && ok "anchor holds: neither superstring nor prefix matched ($got)" \
  || bad "anchor is not \$-anchored: longer names matched (got '$got')"

echo
if [ "$FAIL" -eq 0 ]; then
  echo "PINS CAN FAIL — all checks passed (0 vendor requests)."
  exit 0
fi
echo "$FAIL check(s) FAILED — a pin here cannot fail, or a copy has drifted. Either is a defect."
exit 1