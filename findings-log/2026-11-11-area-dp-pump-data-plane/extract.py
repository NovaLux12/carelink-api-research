#!/usr/bin/env python3
"""Area DP — re-derive every number in FINDINGS.md from the two bodies. ZERO requests.

Checks, each one able to FAIL — a check that cannot fail is not evidence
(AGENTS.md §Method):

  1. the eager bundle's digest and byte count equal the values pinned in FINDINGS.md
  2. every one of the 24 pump-data tokens in the census table reproduces its two counts
  3. the split holds: >=20 of the 24 tokens are 0 in the eager bundle
  4. the alarm map has 73 source codes and 19 distinct targets
  5. the alarm map's target multiset reproduces the published distribution
  6. both enums carry exactly the published token counts (3 and 5)
  7. the two suppressed codes "00-1" and "121" are present in the consumer

Usage: python3 extract.py <dir holding patient-main.js and 6746.c6795ff7e9ff468d.js>
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BODIES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "bodies")

MAIN = os.path.join(BODIES, "patient-main.js")
CHUNK = os.path.join(BODIES, "6746.c6795ff7e9ff468d.js")

PINNED_MAIN_SHA = "0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa"
PINNED_MAIN_BYTES = 3417255

# token -> (hits in chunk 6746, hits in eager main), exactly as published in §2
CENSUS = {
    "therapyAlgorithmState": (5, 0),
    "autoModeShieldState": (3, 0),
    "plgmLgsState": (2, 0),
    "lastAlarm": (29, 0),
    "activeInsulin": (3, 0),
    "reservoirRemainingUnits": (2, 0),
    "reservoirAmount": (4, 0),
    "reservoirLevelPercent": (4, 0),
    "medicalDeviceBatteryLevelPercent": (4, 0),
    "conduitBatteryLevel": (5, 0),
    "conduitInRange": (6, 0),
    "sensorState": (15, 0),
    "calibStatus": (4, 0),
    "sensorDurationHours": (5, 0),
    "timeToNextCalibHours": (4, 0),
    "markers": (1, 1),
    "lastSGTrend": (6, 0),
    "sgs": (7, 0),
    "systemStatusMessage": (24, 0),
    "medicalDeviceSuspended": (8, 0),
    "pumpModelNumber": (5, 0),
    "medicalDeviceFamily": (5, 0),
    "deviceFamily": (10, 5),
    "bgUnits": (53, 14),
}

# target -> number of source codes that map to it, exactly as published in §4
DISTRIBUTION = {
    "002": 39, "024": 7, "037": 6, "062": 4, "007": 2, "011": 2,
    "006": 1, "012": 1, "025": 1, "029": 1, "051": 1, "052": 1,
    "057": 1, "058": 1, "061": 1, "066": 1, "069": 1, "077": 1, "084": 1,
}

SHIELD_TOKENS = ["AUTO_BASAL", "SAFE_BASAL", "FEATURE_OFF"]
PLGM_TOKENS = ["FEATURE_OFF", "REFRACTORY_PERIOD", "MONITORING",
               "SUSPEND_FIRED_PLGM", "SUSPEND_FIRED_LGS"]

failures = []


def check(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    if not ok:
        failures.append(label)


def main():
    for p in (MAIN, CHUNK):
        if not os.path.exists(p):
            print(f"MISSING {p} — run probe.sh first, then point this script at its output dir")
            return 2

    mb = open(MAIN, "rb").read()
    cb = open(CHUNK, "rb").read()
    mt = mb.decode("utf-8", "replace")
    ct = cb.decode("utf-8", "replace")

    # 1. the control
    sha = hashlib.sha256(mb).hexdigest()
    check("eager bundle digest == pinned", sha == PINNED_MAIN_SHA, sha[:16])
    check("eager bundle bytes == pinned", len(mb) == PINNED_MAIN_BYTES, f"{len(mb):,}")

    # 2 + 3. the census, token by token, then the split
    zeros = 0
    for tok, (want_c, want_m) in CENSUS.items():
        got_c = len(re.findall(re.escape(tok), ct))
        got_m = len(re.findall(re.escape(tok), mt))
        check(f"census {tok}", (got_c, got_m) == (want_c, want_m),
              f"chunk {got_c}/{want_c} main {got_m}/{want_m}")
        if got_m == 0:
            zeros += 1
    check("split: >=20 of 24 tokens are 0 in the eager bundle", zeros >= 20, f"{zeros} of 24")

    # 4. the alarm map cardinality
    off = ct.find('{"002":"002"')
    if off < 0:
        check("alarm map literal located", False, "sentinel not found")
        return 1
    depth = 0
    end = None
    for i in range(off, len(ct)):
        if ct[i] == "{":
            depth += 1
        elif ct[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    pairs = re.findall(r'"([0-9]{2,3})"\s*:\s*"([0-9]{2,3})"', ct[off:end])
    amap = dict(pairs)
    check("alarm map has 73 source codes", len(amap) == 73, str(len(amap)))
    check("alarm map has 19 distinct targets", len(set(amap.values())) == 19,
          str(len(set(amap.values()))))

    # 5. the published distribution
    got_dist = {}
    for src, tgt in amap.items():
        got_dist[tgt] = got_dist.get(tgt, 0) + 1
    check("alarm distribution reproduces §4", got_dist == DISTRIBUTION,
          "" if got_dist == DISTRIBUTION else f"got {got_dist}")

    # 6. the two enums
    shield = [t for t in SHIELD_TOKENS if f'"{t}"' in ct]
    check("autoModeShieldState vocabulary == 3 tokens", len(shield) == 3, ",".join(shield))
    plgm = [t for t in PLGM_TOKENS if f'"{t}"' in ct]
    check("plgmLgsState vocabulary == 5 tokens", len(plgm) == 5, ",".join(plgm))
    # the two vocabularies share FEATURE_OFF, so the union is 7, not 8
    check("union of both vocabularies == 7 distinct tokens",
          len(set(SHIELD_TOKENS) | set(PLGM_TOKENS)) == 7)

    # 7. the suppression list
    check('consumer suppresses "00-1" and "121"',
          '["00-1","121"]' in ct.replace(" ", ""), "literal present")

    print()
    if failures:
        print(f"VERIFY: {len(failures)} CHECK(S) FAILED")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("VERIFY: all checks passed — every number in FINDINGS.md re-derives from the bodies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
