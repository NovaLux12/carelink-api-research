#!/usr/bin/env bash
# Public-config regression assertions — 2026-10-09
#
# WHY THIS IS A SHELL SCRIPT AND NOT A .hurl FILE
# ------------------------------------------------
# GET /patient/v2/configuration/public returns `Content-Encoding: gzip`
# UNCONDITIONALLY. It was verified to do so for Accept-Encoding: identity,
# gzip AND deflate — the server ignores the header entirely:
#
#     magic=1f8b  content-encoding: gzip      <- Accept-Encoding: identity
#     magic=1f8b  content-encoding: gzip      <- Accept-Encoding: gzip
#     magic=1f8b  content-encoding: gzip      <- Accept-Encoding: deflate
#
# Sending a content-coding the client did not accept is an RFC 9110 §8.4
# violation, and it breaks any client that does not opt in — hurl's jsonpath
# filters all return `none` against this body, because hurl only decodes what
# it asked for. So these assertions decompress explicitly instead.
#
# That is recorded as a finding in PUBLIC-CONFIG-FINDINGS.md. Do not "fix" this
# file back to .hurl without also recording why.
#
# Exit 0 = every claim still holds. Exit 1 = drift; diff against the notes.
#
# Downstream consumer: https://github.com/NovaLux12/carelink-bridge — the bridge runs this suite before a release
# (`npm run drift:check` on the bridge side). A failure here is a bridge
# release blocker; see https://github.com/NovaLux12/carelink-bridge/blob/main/docs/vendor-api/README.md

set -uo pipefail
cd "$(dirname "$0")/.."
UA="carelink-bridge-research/1.0"
CFG="https://carelink.minimed.eu/patient/v2/configuration/public"

PASS=0
FAIL=0

check() { # check <label> <jq-filter> <expected>
  local label="$1" filter="$2" expected="$3" actual
  actual=$(jq -r "$filter" "$BODY" 2>/dev/null)
  if [ "$actual" = "$expected" ]; then
    PASS=$((PASS + 1))
    printf '  ok   %s\n' "$label"
  else
    FAIL=$((FAIL + 1))
    printf '  FAIL %s\n         expected: %s\n         actual:   %s\n' "$label" "$expected" "$actual"
  fi
}

echo "--- 05-public-config ---"
SCRATCH="$(mktemp -u /tmp/clb-cfg-XXXXXX.json)"
BODY="$SCRATCH"
curl -s --compressed --max-time 30 -A "$UA" "$CFG" -o "$BODY"
trap 'rm -f "$BODY"' EXIT
if [ ! -s "$BODY" ] || [ "$(head -c1 "$BODY")" != "{" ]; then
  echo "  FAIL could not read the public config as JSON"
  exit 1
fi

# --- The load-bearing claim behind repo issue #95 -------------------------
# CC880 is the Minimed Flex family, and it contains the six models #93 added.
check "CC880 family exists"                 '.["personal.device.family.to.model.mapping"] | has("CC880")' 'true'
check "CC880 contains MMT-8062 (Flex)"      '.["personal.device.family.to.model.mapping"].CC880 | index("MMT-8062") != null' 'true'
check "CC880 contains MMT-8085 (Flex)"      '.["personal.device.family.to.model.mapping"].CC880 | index("MMT-8085") != null' 'true'
check "CC880 is named 'MiniMed™ Flex'"      '.["system.settings.transfer.feature.config"]["device.mapping"].CC880' 'MiniMed™ Flex'
check "BLE780 is named '780G'"              '.["system.settings.transfer.feature.config"]["device.mapping"].BLE780' '780G'

# --- The published vocabulary is exactly sixteen families ------------------
check "family count is 16"                  '.["personal.device.family.to.model.mapping"] | length' '16'
for fam in GM BLE700 BLE720 BLE740 BLE770 BLE780 GST SIMPLERA \
           SIMPLERACC SIMPLERACCOLID NMX7 CC840 CC880 NMX8 INSTINCT EAGLE; do
  check "family $fam present"               ".[\"personal.device.family.to.model.mapping\"] | has(\"$fam\")" 'true'
done

# --- TRAP: trailing-whitespace padding in the vendor's model list ----------
# Several SIMPLERA entries are padded ("MMT-5100       "). The bridge's
# normalise() strips it; a naive exact-match parser would silently miss them.
check "SIMPLERA still padded (trap)"        '.["personal.device.family.to.model.mapping"].SIMPLERA | index("MMT-5100       ") != null' 'true'

# --- Logbook entry types (#76: markers read side) --------------------------
check "logbook has SENSOR_INSERTION"        '.["logbook.supported.entry.types"] | index("SENSOR_INSERTION") != null' 'true'
check "logbook has INFUSION_SET_CHANGE"     '.["logbook.supported.entry.types"] | index("INFUSION_SET_CHANGE") != null' 'true'
check "logbook has HBA1C"                   '.["logbook.supported.entry.types"] | index("HBA1C") != null' 'true'
check "logbook entry count is 12"           '.["logbook.supported.entry.types"] | length' '12'

# --- #84 marker: this is the CONTROL vocabulary, not the NGP alarm set -----
# If a future capture shows an N-code here, the assumption that NGP codes live
# somewhere else is wrong and #84's blocker changes.
check "csr control codes contain 'tup'"     '.["csr.control.codes.settings"].predefined_control_codes | index("tup") != null' 'true'
check "csr control codes have NO N24"       '.["csr.control.codes.settings"].predefined_control_codes | index("N24") != null' 'false'

# --- Config integrity: the nutrition key is a PLACEHOLDER, not a credential -
check "nutrition x-api-key is a placeholder" '.["nutrino.cc.broker.service.config"].security_headers["x-api-key"] | length' '17'
check "nutrition x-api-key starts with %#"  '.["nutrino.cc.broker.service.config"].security_headers["x-api-key"] | startswith("%#")' 'true'

# --- Shadow portal: the one header-gate that ISN'T -------------------------
# Nine siblings of this endpoint return 412 (precondition failed = missing the
# client header) with no credentials. This one returns 200. The finding is the
# inconsistency, not the content — a CRM base URI and a version, no PII.
SHADOW="https://carelink.medtronic.eu/hcp/configuration/public/pow.crm.settings"
BODY_SH=$(curl -s --max-time 25 -A "$UA" "$SHADOW")
if printf '%s' "$BODY_SH" | grep -q '"product"'; then
  PASS=$((PASS + 1)); printf '  ok   shadow pow.crm.settings still unauthenticated\n'
else
  FAIL=$((FAIL + 1)); printf '  FAIL shadow pow.crm.settings no longer open (may now be gated)\n'
fi
for sib in cms-config.json pow.udi.number; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 -A "$UA" \
         "https://carelink.medtronic.eu/hcp/configuration/public/$sib")
  if [ "$code" = "412" ]; then
    PASS=$((PASS + 1)); printf '  ok   sibling %s still gated (412)\n' "$sib"
  else
    FAIL=$((FAIL + 1)); printf '  FAIL sibling %s changed: expected 412, got %s\n' "$sib" "$code"
  fi
  sleep 2
done

# --- KNOWN VENDOR BUG, pinned at its CURRENT (wrong) value -------------------
# csr.control.codes.settings.ranges.lhpro.max and .lghpro.max both read
# 4292967295. The correct 32-bit maximum is 4294967295 — the published value is
# exactly 2,000,000 too low, and is wrong in BOTH ranges, so it is a consistent
# upstream typo rather than a per-field slip. The HCP-side config carries the
# correct 4294967295, which is how the two were compared.
# Consequence: any client validating a low-hypo / low-hypo-profile code against
# this bound rejects 2,000,000 legitimate values.
# Asserted at the CURRENT value on purpose: if Medtronic fixes it, this assertion
# fails and the note gets updated rather than the fact going stale.
check "lhpro.max (KNOWN BUG: 2^32-1 minus 2,000,000)" '.["csr.control.codes.settings"].ranges.lhpro.max' '4292967295'
check "lghpro.max (KNOWN BUG: same value)"            '.["csr.control.codes.settings"].ranges.lghpro.max' '4292967295'
check "vex.max (correct, control)"                    '.["csr.control.codes.settings"].ranges.vex.max' '100'
check "gstpro.max (correct, int64 max)"               '.["csr.control.codes.settings"].ranges.gstpro.max' '9223372036854775807'

# --- DRIFT GUARD: the reports-country rollout is a live, moving fence --------
# Observed drift, not a bug. On 2026-10-09 the key carried 17 countries; by
# 2026-10-10 it carried 29 (+AU HR CZ EG GE IL PL RO RS SK SI AE), growing in
# lockstep with personal.inpen.supported.countries. Pinned at the CURRENT value
# on purpose: a further rollout fails this check, which is the point. A silent
# rollout is how a bridge ends up believing a feature is unavailable.
check "reporting countries drifted 17 -> 29 (drift guard)" '.["personal.common.core.reporting.enabled.countries"] | length' '29'
check "inpen countries moved in lockstep" '.["personal.inpen.supported.countries"].enabledPerCountry | length' '29'
# The EU doc's reporting list must NOT contain US — that country lives in the
# .com deployment's own list. Asserting the invariant, not my earlier conflation
# of the two lists (which silently failed and was a wrong claim about the data).
check "eu reporting list excludes US (invariant)" '.["personal.common.core.reporting.enabled.countries"] | index("US") != null' 'false'

# --- Global, not regional: the device vocabulary is identical everywhere -----
# Verified across carelink.minimed.eu / .com / carelink-trials.minimed.com.
# If this ever differs by region, the CC880 mapping in #95 stops being a single
# authoritative answer and the test has to be re-derived.
# NOTE: $BODY is a FILE PATH, so jq takes it as an argument, never on stdin.
EUH=$(jq -S -c '.["personal.device.family.to.model.mapping"]' "$BODY" | sha256sum | cut -c1-12)
if [ -z "$EUH" ] || [ "$EUH" = "e3b0c44298fc" ]; then
  echo "  FAIL could not hash the EU family map (got '$EUH')"
  FAIL=$((FAIL + 1))
else
  for host in carelink.minimed.com carelink-trials.minimed.com; do
    other="$(mktemp -u /tmp/clb-cfg-XXXXXX.json)"
    curl -s --compressed --max-time 30 -A "$UA" "https://$host/patient/v2/configuration/public" -o "$other"
    OTH=$(jq -S -c '.["personal.device.family.to.model.mapping"]' "$other" 2>/dev/null | sha256sum | cut -c1-12)
    rm -f "$other"
    if [ "$EUH" = "$OTH" ]; then
      PASS=$((PASS + 1)); printf '  ok   family map identical on %s (%s)\n' "$host" "$EUH"
    else
      FAIL=$((FAIL + 1)); printf '  FAIL family map differs on %s (eu=%s %s=%s)\n' "$host" "$EUH" "$host" "$OTH"
    fi
    sleep 2
  done
fi

# --- Shape -----------------------------------------------------------------
check "config key count (was 69)"           'keys | length' '69'

echo
echo "  ${PASS} passed, ${FAIL} failed"
[ "$FAIL" -eq 0 ]