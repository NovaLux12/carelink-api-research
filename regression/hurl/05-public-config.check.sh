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
# (`npm run drift:check` on the bridge side). A failure here reaches their
# release checklist; see https://github.com/NovaLux12/carelink-bridge/blob/main/docs/vendor-api/README.md

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

# =====================================================================
# AREA T (2026-10-12) — the published-pointer set.
# Source: findings-log/2026-10-12-published-pointers/FINDINGS.md
#
# Every check below runs against the $BODY already fetched at the top of this
# file, so the whole block costs ZERO additional vendor requests. That is the
# only reason it lives here rather than in a new suite: the weekly drift sweep
# has a request budget (AGENTS.md §11) and a config assertion that needs no
# request is worth more than a new suite that needs four.
# =====================================================================

# csr/v2 IS published, twice, by the public config. Area T was opened to test
# the opposite and the opposite is false — which matters because a route that no
# document names is unreachable by every config-driven client.
check "csrDisplayMessageUrl names csr/v2"   '.["system.gc.gz.transition.flags"]["displayMessage"].csrDisplayMessageUrl | endswith("/connect/csr/v2/display/message")' 'true'
check "csr periodic endpoints name csr/v2"  '.["csr.cumulus.periodic.data.endpoints"].display_message | endswith("/connect/csr/v2/display/message")' 'true'
# Both keys carry the SAME URL — the client is handed the same endpoint twice,
# from two unrelated config subtrees.
check "the two csr keys agree"              '.["system.gc.gz.transition.flags"]["displayMessage"].csrDisplayMessageUrl == .["csr.cumulus.periodic.data.endpoints"].display_message' 'true'
# NEGATIVE pin: no baseUrlCsr-shaped key anywhere in the 69. This is how the
# route stays addressable from the CONFIG rather than from DISCOVERY — the
# discovery document is asserted to carry no baseUrlCsr in 01-discovery-pin.hurl.
check "no baseUrlCsr-shaped key exists"     '[keys[] | select(test("baseUrlCsr"))] | length' '0'

# The three-way plane dispatch table, and the master switch already ON.
# useCumulusUrls=true means the vendor's own client is instructed to address the
# csr/v2 URL above on this deployment, today.
check "useCumulusUrls is true"              '.["system.gc.gz.transition.flags"]["displayMessage"].useCumulusUrls' 'true'
check "csr plane dispatch table present"    '.["system.gc.gz.transition.flags"]["displayMessage"] | has("personalDisplayMessageUrl") and has("csrDisplayMessageUrl") and has("carepartnerDisplayMessageUrl")' 'true'
check "sendPeriodicToCumulus is true"       '.["system.gc.gz.transition.flags"].sendPeriodicToCumulus' 'true'
check "sendDiagnosticLogsToCumulus is true" '.["system.gc.gz.transition.flags"].sendDiagnosticLogsToCumulus' 'true'
# csr carries a retina endpoint the personal plane does NOT: a path in no prior
# note (recorded, unprobed — retina's host is runtime-composed).
check "csr retina transfer_settings path"   '.["retina.endpoints.config"].csr.transfer_settings.base_uri' '/connect/retina/v1/settings/audit'
check "personal retina has no transfer_settings" '.["retina.endpoints.config"].personal | has("transfer_settings")' 'false'

# CORRECTION pinned (area T §3a): personal.data.csv.export.enable is an OBJECT
# keyed by plane, not a boolean. docs/04 recorded true/true/false — which matched
# personal.aggregatedData by coincidence and hid the csr plane entirely. A scalar
# reader misses trials csr.rawData=true, the one value in this key that differs
# from every personal value. Asserted on TYPE so the shape cannot silently revert.
check "csv export enable is an object"      '.["personal.data.csv.export.enable"] | type' 'object'
check "csv export enable is per-plane"      '.["personal.data.csv.export.enable"] | has("personal") and has("csr")' 'true'
check "csv export personal rawData is false" '.["personal.data.csv.export.enable"].personal.rawData' 'false'

# PARSING TRAP (area T §3b): 68 of the 69 keys are literal dotted names; exactly
# one — captcha — is a real nested object. A walker that splits every key on "."
# misses captcha entirely. Pinned so a future flattening is visible.
check "captcha is a nested object, not a dotted key" '.captcha | type' 'object'
check "the dotted key captcha.key does NOT exist at top level" 'has("captcha.key")' 'false'
check "captcha subkeys are the documented four" '.captcha | keys | sort | join(",")' 'enabled,key,testKey,type'
# testKey is PRESENT but EMPTY on every deployment: a client switching on
# "testKey is present" rather than "non-empty" would enable test mode.
#
# Pinned as has() AND == "", not as `| length == 0`. `length` returns 0 for an
# ABSENT key and for `null` as well as for "", so that assertion was satisfied by
# three different states and could not tell them apart -- the exact
# present-vs-absent confusion this repo keeps getting bitten by (docs/09 §4, the
# `//`-swallows-false trap). Assert the state that is actually claimed.
check "captcha.testKey is present and empty" '.captcha | has("testKey") and (.testKey == "")' 'true'

# --- AREA A (2026-10-12): which portal BUILD each host serves ----------------
# Source: findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md
#
# There are TWO builds of the clinician portal in production, and the split is
# PRODUCT ROLE, not region:
#   clinic  (pow) -> main.fb5f8cb7eb60c4d5.js   carelinkhp.minimed.eu,
#                                               carelink.medtronic.{eu,com}
#   support (cua) -> main.759cddab23085086.js   carelink-support.medtronic.{eu,com}
# Every .eu/.com pair measured serves the SAME build, so a client pinned to one
# region's host works against the other region's host -- and a client that only
# ever fetched the entry document could not tell the two builds apart at all,
# because both are 5518 B of text/html.
#
# WHY THIS FETCHES THE DOCUMENT AND NOT THE ASSET: the asset is 3.4 MB per host.
# The entry document is 5.5 KB and NAMES its own content-hashed chunk, so the
# build identity is readable for 0.2% of the bandwidth. The cost of this choice
# is that it asserts the document's claim about its chunk, not the chunk itself:
# the asset-level proof lives in the findings log (seq 4, 8, 15, 19, 20).
#
# Pinned at the CURRENT build on purpose, the same convention as the lhpro
# bounds above: if Medtronic ships a new build this fails and the note gets
# updated, rather than a host quietly changing build under a stale claim.
for spec in "carelinkhp.minimed.eu:main.fb5f8cb7eb60c4d5.js" \
            "carelink-support.medtronic.eu:main.759cddab23085086.js"; do
  hp_host="${spec%%:*}"
  hp_chunk="${spec##*:}"
  hp_body=$(curl -s --max-time 25 -A "$UA" "https://$hp_host/")
  if printf '%s' "$hp_body" | grep -q "$hp_chunk"; then
    PASS=$((PASS + 1)); printf '  ok   %s serves build %s\n' "$hp_host" "$hp_chunk"
  else
    FAIL=$((FAIL + 1)); printf '  FAIL %s no longer names %s (build changed?)\n' "$hp_host" "$hp_chunk"
  fi
  sleep 2
done

echo
echo "  ${PASS} passed, ${FAIL} failed"
[ "$FAIL" -eq 0 ]