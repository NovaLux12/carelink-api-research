#!/usr/bin/env python3
"""Value-free structural report of the credential-SHAPED keys in the public config.

Prints, for every leaf whose key name looks credential-ish: its key path, JSON
type, character count, and a coarse character-class label. Nothing else.

WHAT IT WILL NOT DO
-------------------
It never prints, hashes, compares or otherwise derives anything from a value.
Two rules learned the hard way on 2026-10-12, both by getting them wrong first:

1. NO CHARACTER-CLASS PROJECTION. The first version of this script emitted a
   per-character "shape" (a-z -> x, A-Z -> X, everything else verbatim). That is
   a leak dressed as a redaction: for a 40-character alphanumeric value it
   printed 10 characters verbatim, and those positions revealed 3 of the 7 fixed
   characters of this repo's own published credential prefix. Length plus a
   coarse class label carries the same information for the purpose here.

2. NO LOCAL COPY OF A CREDENTIAL PATTERN. This script used to embed the
   reports-broker and reCAPTCHA patterns so it could label which credential class
   a value belonged to. That is a second copy of a credential pattern in a second
   file, twenty lines below this pass's own rule that a second copy is a leak.
   The patterns are read from `scripts/scrub-patterns.txt`, the one exempt home.

Matching a value against a known published credential literal is a
CLASSIFICATION ("is this the credential class we scrub?"), not a comparison
between two deployments' values. The cross-deployment comparison that
docs/04-configuration.md holds back for a disclosure decision stays held: this
script compares LENGTHS only, never values.
"""
import json
import os
import re
import sys

PATTERN_FILE = "scripts/scrub-patterns.txt"
SENSITIVE_KEY = re.compile(r"(api[-_]?key|secret|token|password|credential)", re.I)

# The pattern-file entries that identify a published credential CLASS. Their
# NAMES are listed here; the patterns themselves are read from the file, so no
# credential fragment is duplicated into this source.
CREDENTIAL_CLASSES = [
    "reports-broker key fragments",
    "reCAPTCHA site keys",
    "vendor API key literal",
]


def classify(s):
    """A coarse character-class label. Deliberately loses per-position detail."""
    if not s:
        return "empty"
    if s.isalnum():
        return "alphanumeric"
    if all(not c.isalnum() for c in s):
        return "punctuation-only"
    return "mixed alphanumeric and punctuation"


def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f"{p}.{k}" if p else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, f"{p}[{i}]")
    else:
        yield p, o


def credential_patterns():
    """(class name, compiled regex) for the published credential classes only."""
    out = []
    if not os.path.exists(PATTERN_FILE):
        sys.exit(f"{PATTERN_FILE} not found -- run from the repo root")
    with open(PATTERN_FILE, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "|" not in line:
                continue
            name, pat = line.split("|", 1)
            if name.strip() in CREDENTIAL_CLASSES:
                try:
                    out.append((name.strip(), re.compile(pat, re.I)))
                except re.error:
                    continue
    return out


def walk_configs():
    for name, label in [("config-eu", "carelink.minimed.eu          (EU/OUS)"),
                        ("config-com", "carelink.minimed.com         (US)"),
                        ("config-trials", "carelink-trials.minimed.com (trials)")]:
        path = f"findings-log/2026-10-12-published-pointers/docs/{name}.json"
        with open(path, encoding="utf-8") as f:
            yield name, label, json.load(f)


def main():
    classes = credential_patterns()
    rows = []
    for _, label, d in walk_configs():
        assert isinstance(d, dict), "config did not parse as an object"
        print(f"\n=== {label}  --  {len(d)} top-level keys ===")
        for key, val in walk(d):
            if not SENSITIVE_KEY.search(key):
                continue
            s = str(val)
            matched = [n for n, rx in classes if rx.search(s)]
            print(f"  {key}")
            print(f"      type={type(val).__name__}  length={len(s)}  class={classify(s)}")
            if matched:
                print(f"      belongs to a published credential class: {'; '.join(matched)}")
            rows.append((label.split()[0], key, len(s), bool(matched)))

    print("\n" + "=" * 72)
    print("CROSS-DEPLOYMENT SUMMARY -- key paths and lengths only, values never read")
    print("=" * 72)
    by_key = {}
    for dep, key, ln, matched in rows:
        by_key.setdefault(key, []).append((dep, ln, matched))
    for key, deps in sorted(by_key.items()):
        lens = {d: l for d, l, _ in deps}
        print(f"  {key}")
        for dep, ln, m in deps:
            tag = "   [matches a published credential class]" if m else ""
            print(f"      {dep:8} {ln:3d} chars{tag}")
        if len(set(lens.values())) > 1:
            print(f"      -> lengths DIFFER across deployments ({lens})")
        if any(m for _, _, m in deps):
            print("      -> a published credential class is present; the cross-deployment")
            print("         comparison is HELD for a disclosure decision (docs/04) and is")
            print("         deliberately not made here. This script compares LENGTHS only.")


if __name__ == "__main__":
    main()