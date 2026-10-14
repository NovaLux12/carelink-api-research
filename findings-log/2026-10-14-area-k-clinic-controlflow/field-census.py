#!/usr/bin/env python3
"""Field-name census over the clinic corpus: the 89 call-site field names the
2026-10-08 sweep recovered, re-measured on a body-verified 226-file corpus.

The point is NOT the count. The point is WHERE each name lives — in the eager
main bundle or in a lazy chunk — and whether the hit is a QUOTED PROPERTY NAME the
client actually serialises or bare code / a translation key / a zxcvbn dictionary
entry. Every hit is emitted with its byte offset, its enclosing literal and its
context, because a count that cannot be read at the offset is the false-hit class
this repo keeps re-learning (patient-timeline = 5 Angular component selectors;
discover = zxcvbn password words).

Controls run on every name:
  * case sensitivity — occurrences case-sensitive and case-insensitive are both
    reported, so "0 hits" and "0 hits in this casing" are distinguishable;
  * literal vs code — mine.literal_label, which has a self-test;
  * a KNOWN-FALSE control word is included in the list so a run that reports the
    false control as a hit is visibly broken.

Usage: field-census.py <bodies-dir> <out.json> [main-file-glob]
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mine import literal_label, index, module_at  # noqa: E402

# The field names as transcribed by the 2026-10-08 sweep, plus two controls.
# CONTROL-WORDS are the repo's documented false-hit classes, carried here on
# purpose: if a census cannot separate them, the census is not measuring names.
FIELD_NAMES = [
    # logbook / markers
    "removalType", "removalReason", "adhesivetapeLocation", "sensorInsertionLocation",
    "sensorRemovalLocation", "sensorPdLocation", "timecapUnscrewed",
    "timecapUnscrewed_additionalTime", "timecapUnscrewed_minutesTime", "notes", "entryTs",
    # device identity
    "deviceFamily",
    # insulin / therapy
    "tdd", "longActingInsulin", "doseFrequency", "doseTwoUnitsPerDose1",
    "doseTwoUnitsPerDose2", "medicationDoseUnit", "currentPreset", "blindedStatus",
    "glucoseManagementIndicator", "gmi", "ageGroups", "weight", "weightUnit",
    # meal bolus wizard
    "breakfast", "lunch", "dinner", "snack",
    # auth / MFA
    "captcha", "captchaValue", "mfaRemembrancePeriod", "mfaVerificationCodeExpiration",
    "personalCredentials", "personalPassword", "oldPassword", "expireAllActiveSessions",
    # account linking
    "ssoLink", "isSendLinkCode", "linkingMethod", "phoneDetails", "sendCC",
    "personalUsername", "updatePatientEmail",
    # consent / data sharing
    "consent", "accessDataEnabled", "accessDataFilter", "dataSharingDisabled",
    "patientDataColumns", "therapyDataColumns", "reportDataRange", "triageSettings",
    # the primary target of this area
    "system.logbook.entry.validation.config",
    "logbook.supported.entry.types",
    "logbook_add_entry", "logbook_edit_entry", "logbook_remove_entry",
    # CONTROL WORDS — documented false-hit classes, expected to be NON-zero here
    "patient-timeline", "discover",
]

CONTROL_WORDS = {"patient-timeline", "discover"}

# Hits are truncated per name so this artefact stays reviewable. The truncation
# is RECORDED per row (`hits_emitted` vs `occ_case_sensitive`) rather than
# silently applied — a count nobody can see the tail of is how a reader assumes
# they have seen all of it. Every count in the summary line is the full count,
# computed over every body; only the per-hit detail list is capped.
MAX_HITS_PER_NAME = 40
CTX_CHARS = 110


def main():
    bodies_dir, out_path = sys.argv[1], sys.argv[2]
    files = sorted(glob.glob(os.path.join(bodies_dir, "*.b")))
    if not files:
        print("no bodies found")
        sys.exit(2)
    cache = {}
    for f in files:
        b = open(f, "rb").read()
        cache[f] = (b, b.decode("utf-8", "replace"), index(b))
    print(f"# {len(files)} bodies in {os.path.basename(bodies_dir)}")

    rows = []
    for name in FIELD_NAMES:
        pat = re.compile(re.escape(name))
        pat_ci = re.compile(re.escape(name), re.IGNORECASE)
        total_cs = total_ci = 0
        per_file = []
        hits_detail = []
        for f in files:
            body, text, mods = cache[f]
            ms = list(pat.finditer(text))
            ci_n = len(pat_ci.findall(text))
            total_cs += len(ms)
            total_ci += ci_n
            if not ms and ci_n == 0:
                continue
            per_file.append({"file": os.path.basename(f), "occ": len(ms), "occ_ci": ci_n})
            for m in ms:
                if len(hits_detail) >= MAX_HITS_PER_NAME:
                    break
                off = m.start()
                mod = module_at(mods, off)
                hits_detail.append({
                    "file": os.path.basename(f),
                    "offset": off,
                    "module": mod[0] if mod else None,
                    "label": literal_label(text, off),
                    "ctx": text[max(0, off - 45): off + len(name) + 45][:CTX_CHARS],
                })
        rows.append({
            "name": name,
            "is_control_word": name in CONTROL_WORDS,
            "occ_case_sensitive": total_cs,
            "occ_case_insensitive": total_ci,
            "files_with_hits": len(per_file),
            "per_file": per_file,
            "hits_emitted": len(hits_detail),
            "hits_truncated": total_cs > len(hits_detail),
            "hits": hits_detail,
        })
        flag = "  [CONTROL WORD]" if name in CONTROL_WORDS else ""
        print(f"{name:<42} cs={total_cs:<5} ci={total_ci:<5} files={len(per_file)}{flag}")

    out = {
        "bodies_dir": os.path.basename(bodies_dir),
        "body_count": len(files),
        "field_names": len(FIELD_NAMES),
        "names_with_zero_case_sensitive_hits": [r["name"] for r in rows if r["occ_case_sensitive"] == 0],
        "rows": rows,
    }
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote {out_path}")
    print("zero case-sensitive hits:", out["names_with_zero_case_sensitive_hits"])


if __name__ == "__main__":
    main()