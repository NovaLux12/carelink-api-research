#!/usr/bin/env python3
"""Area M — mutation-test `failclass.py --selftest`, and publish the exact
matrix of which mutants it kills and which it does not.

WHY
---
`failclass.py`'s docstring used to claim the self-test asserted that "a
`showNumPages` cell does not mark its own domain absent". Verifier round 2
showed that assertion was VACUOUS: two mutants passed with exit 0, so the
falsifiability claim overstated coverage by one. The honest repair is not to
keep asserting more than is true — it is to measure, publish the matrix, and
narrow the claim to what the fixtures actually kill.

A self-test that cannot fail is worse than no self-test, because it reads as
evidence. So: every claim about the self-test's strength in FINDINGS.md and in
failclass.py's docstring is checked by running this.

HOW
---
Each mutant is a single textual substitution in a COPY of failclass.py, applied
to a temp file; the copy's `--selftest` is run and its exit code recorded.
`KILLED` = the self-test fails, i.e. the fixture discriminates. `SURVIVED` = the
mutant passes, i.e. the self-test does NOT cover it and the claim must not say
it does.

Exit 0 when every mutant listed as expected-to-be-killed is killed AND the
output is in sync with MUTANTS below. Exit 1 otherwise.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "failclass.py")

# (id, anchor, replacement, expected killed?, why it matters)
MUTANTS = [
    ("A", 'record_form = p(path, "showNumPages") != "true"',
     'record_form = True',
     True,
     "ignores showNumPages, so a count cell is treated as a record query"),
    ("C", 'if r["http_status"] == "200" and record_form and r["distinct_hosts"]:',
     'if r["http_status"] == "200" and record_form:',
     False,
     "reads an EMPTY host set as 'no captures' and wipes the bucket — the exact "
     "bug the module docstring says it was born catching"),
    ("D", 'elif (crawl, registrable(host)) in complete and mt == "domain":',
     'elif crawl in {c for c, _d in complete} and mt == "domain":',
     True,
     "scopes the enumeration inference to the crawl instead of the registrable "
     "domain, so minimed.eu's enumeration would mark medtronic.eu absent"),
]


def sibling_inheritance(src: str) -> str:
    """Re-introduce the branch the rewrite removed: a host-level query inherits
    its state from any sibling under the same registrable domain."""
    anchor = "        elif (crawl, host) in absent:\n"
    assert anchor in src
    return src.replace(anchor,
                       "        elif any(registrable(h) == registrable(host) and h in covered.get(crawl, ())\n"
                       "                 for h in covered.get(crawl, ())):\n"
                       "            classes[r[\"seq\"]] = \"covered\"\n"
                       + anchor, 1)


def run(mutated_src: str) -> int:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     dir=HERE) as fh:
        fh.write(mutated_src)
        path = fh.name
    try:
        # the module resolves sibling fixtures relative to __file__, so run the
        # copy in place and delete it afterwards
        proc = subprocess.run([sys.executable, path, "--selftest"],
                              capture_output=True, text=True)
        return proc.returncode
    finally:
        os.unlink(path)


def main() -> int:
    src = open(SRC, encoding="utf-8").read()
    print("mutant  killed  expected  mutation")
    print("-" * 78)
    bad = 0
    for mid, anchor, repl, expect_killed, why in MUTANTS:
        assert anchor in src, f"mutant {mid}: anchor not found in failclass.py"
        rc = run(src.replace(anchor, repl, 1))
        killed = rc != 0
        mark = "yes " if killed else "NO  "
        exp = "killed" if expect_killed else "survives"
        ok = killed == expect_killed
        if not ok:
            bad += 1
        print(f"  {mid}     {mark}    {exp:<9} {why}")
        if not ok:
            print(f"        !! expectation violated — the matrix below is stale")

    rc = run(sibling_inheritance(src))
    killed = rc != 0
    if not killed:
        bad += 1
    print(f"  S     {'yes ' if killed else 'NO  '}    "
          f"{'killed' if killed else 'survives':<9} "
          f"re-introduces sibling inheritance: a host-level query takes its state "
          f"from any sibling under the same registrable domain")
    if not killed:
        print("        !! expected the fabricated-sibling fixture to kill this")

    print("\nHONEST READING:")
    print("  The self-test kills mutants A, D and S. It does NOT kill C, and")
    print("  `failclass.py`'s docstring no longer claims it does.")
    print("  C survives because `covered` is consulted before `absent`, so the")
    print("  damage a C-mutant does to the absent-set is never observable in a")
    print("  classification. That is a known, measured limit of the suite — not a")
    print("  claim that C is harmless: C would matter the moment check order")
    print("  changed, and nothing in the published 2/0/13/2 split depends on it.")
    print(f"\n{'OK' if bad == 0 else 'MISMATCH'}: {len(MUTANTS) + 1} mutants measured, "
          f"{bad} expectation(s) violated")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())