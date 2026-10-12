#!/usr/bin/env python3
"""Scrub a captured document before it is allowed near the repo.

WHY THIS EXISTS. The 69-key public config is unauthenticated and carries
credential-shaped values: a reCAPTCHA site key on all three deployments, and an
x-api-key under each of the two `nutrino.cc.*` service keys. On EU that key is a
17-character non-alphanumeric placeholder; on the other two deployments it is a
40-character alphanumeric value. docs/04-configuration.md holds the cross-deployment
comparison back for a disclosure decision, and this repo publishes none of the
values -- so the raw captures must never be committed.

WHAT THIS SCRIPT DELIBERATELY CANNOT DO. It redacts; it never compares. It has no
code path that can tell you whether two redacted values are equal, because
answering that question IS the held-back disclosure, and a scrubber that answered
it would be doing the thing the hold-back exists to prevent. Its output is the
enumeration with sensitive values replaced by typed placeholders, so the KEY LIST
that was searched stays auditable -- which is the whole point of a negative result
in this repo (#84).

PATTERNS ARE NOT LITERAL HERE, AND THERE ARE NO LOCAL EXTRAS
----------------------------------------------------------
Every pattern is read from `scripts/scrub-patterns.txt`, the single source of
truth. Two hard-won rules, both learned the hard way on 2026-10-12:

1. Copying a credential prefix into a second file puts a credential in the diff.
   That is the exact failure `scripts/research-gate.sh` exists to stop, and why
   that one file plus the gate are the only two paths excluded from the scan.

2. THE FIRST VERSION OF THIS SCRIPT HAD A LOCAL `EXTRA_RULES` LIST containing an
   AWS VPC-endpoint pattern that was simply WRONG -- it assumed a 16-hex /
   9-alphanumeric shape where the real identifiers are 17 / 8. It matched nothing,
   three live VPC endpoint identifiers sailed straight through into a committed
   findings log, and the script still printed a clean self-check. Why it looked
   clean: `gate_selfcheck()` scanned only the patterns read from
   `scripts/scrub-patterns.txt` and never checked the local extras.

So this version has no local extras at all (the pattern was promoted into
`scripts/scrub-patterns.txt`, where the gate and the drift sweep see it too), and
it adds two guards:

  * `selfcheck()` checks the output against EVERY pattern that was applied, not
    just the ones read from the pattern file.
  * `RESIDUE_TRIPWIRES` are literal markers that must not survive into the
    output. This is the guard that actually catches the wrong-shape case, and it
    took two attempts to get right. The first attempt guarded with "a rule whose
    pattern occurs in the source but matched nothing" -- which cannot detect a
    wrong-shaped pattern at all, because a pattern with a wrong shape does not
    match the source either, so it looks like a rule that simply had no work.
    The tripwire asks the only question that matters of the OUTPUT: is a marker
    of an internal identifier still sitting in it?
"""
import os
import re
import sys

PATTERN_FILE = "scripts/scrub-patterns.txt"

# Literal markers that must not survive into the output. These are the net that
# catches a pattern whose shape assumption is simply wrong, which no amount of
# self-checking the patterns themselves can detect. Plain substrings on purpose:
# this asks "does the OUTPUT still contain an internal identifier?", which is the
# question a reader of the committed file actually cares about.
RESIDUE_TRIPWIRES = [
    "vpce-",                 # AWS VPC-endpoint service name
    ".corp",                 # internal corporate hostname
    ".vpce.amazonaws.com",   # VPC endpoint, belt and braces
    "buor",                  # reCAPTCHA v2 site-key marker
]

# Placeholders keyed off the pattern file's NAME field, so adding a class there
# needs no edit here.
PLACEHOLDER = {
    "vendor API key literal": "<REDACTED:vendor-api-key>",
    "reports-broker key fragments": "<REDACTED:reports-broker-key>",
    "reCAPTCHA site keys": "<REDACTED:recaptcha-site-key>",
    "AWS VPC endpoint service name": "<REDACTED:aws-vpc-endpoint-id>",
    "internal .corp host": "<service>.<internal>",
    "internal Grafana/K8s/GitLab/DB/Prometheus host": "<internal-host>.<internal>",
    "machine-specific paths": "/<user-path>",
    "live jsession values": "<REDACTED:jsessionid>",
    "live sessionData values": "<REDACTED:sessionData>",
    "credential prefixes": "<REDACTED:credential-shaped>",
}


def gate_patterns():
    """(name, pattern) pairs, read from the single source of truth."""
    out = []
    if not os.path.exists(PATTERN_FILE):
        sys.exit(f"{PATTERN_FILE} not found -- run from the repo root")
    with open(PATTERN_FILE, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "|" not in line:
                continue
            name, pat = line.split("|", 1)
            out.append((name.strip(), pat))
    return out


def compile_rules():
    rules = []
    for name, pat in gate_patterns():
        try:
            rx = re.compile(pat, re.I)
        except re.error as e:
            print(f"  WARNING: pattern {name!r} does not compile ({e}); skipped")
            continue
        rules.append((name, rx, PLACEHOLDER.get(name, f"<REDACTED:{name}>")))
    return rules


def scrub(text, rules):
    applied = []
    for name, rx, repl in rules:
        text, n = rx.subn(repl, text)
        if n:
            applied.append((name, n))
    return text, applied


def selfcheck(text, rules):
    """Check the output against EVERY applied pattern, not a subset of them.

    This is the guard the first version lacked: it checked the pattern FILE but
    not the local extras, and so reported a clean result while three VPC endpoint
    identifiers sat unredacted in the committed output.
    """
    hits = []
    for name, rx, _ in rules:
        probe = text.replace("/home/<user>", "")
        for i, line in enumerate(probe.splitlines(), 1):
            if rx.search(line):
                hits.append(f"    line {i}: {name}")
    return hits


def dead_rules(source, applied, rules):
    """Rules whose pattern occurs in the source yet matched nothing.

    This catches the case where an EARLIER rule already redacted the text, so a
    later rule finds nothing and silently contributes nothing. It does NOT, and
    cannot, catch a wrong-shaped pattern: such a pattern does not match the
    source either, so it is indistinguishable from a rule with no work. That
    case is `RESIDUE_TRIPWIRES`' job, and conflating the two is what made the
    first attempt at this guard useless.
    """
    dead = []
    fired = {n for n, _ in applied}
    for name, rx, _ in rules:
        if name in fired:
            continue
        if rx.search(source):
            dead.append(name)
    return dead


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8", errors="replace") as fh:
        original = fh.read()

    rules = compile_rules()
    out, applied = scrub(original, rules)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(out)

    print(f"scrubbed {src} -> {dst}")
    print(f"  {len(original)} bytes -> {len(out)} bytes")
    print(f"  {len(rules)} rules loaded from {PATTERN_FILE}")
    for name, n in applied:
        print(f"  redacted {n:3d} x {name}")
    if not applied:
        print("  WARNING: no rule fired at all -- is the input the file you think it is?")

    failed = False
    hits = selfcheck(out, rules)
    if hits:
        print("\nSELF-CHECK FAILED -- the scrubbed text still matches a pattern it applied:")
        for h in hits[:20]:
            print(h)
        failed = True
    else:
        print("  self-check: 0 matches against every pattern applied")

    dead = dead_rules(original, applied, rules)
    if dead:
        print("\nINERT RULES -- these patterns occur in the source yet matched nothing, "
              "so an earlier rule already redacted their target. They contributed "
              "nothing this run:")
        for name in dead:
            print(f"    {name}")
        failed = True

    residue = [m for m in RESIDUE_TRIPWIRES if m in out]
    if residue:
        print("\nRESIDUE -- these internal-identifier markers SURVIVED into the output. "
              "Either the pattern covering them has the wrong shape, or no pattern "
              "covers them. This is the exact failure the first version of this "
              "script shipped:")
        for m in residue:
            print(f"    {m!r}")
        failed = True
    else:
        print(f"  residue tripwires: none of {len(RESIDUE_TRIPWIRES)} markers present")

    if failed:
        print("\nRefusing to report success. Fix the pattern in "
              f"{PATTERN_FILE}, then re-run.")
        sys.exit(1)

    print("  NOTE: this script redacts only. It never compares two credential values.")


if __name__ == "__main__":
    main()