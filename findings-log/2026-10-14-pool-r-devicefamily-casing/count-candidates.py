#!/usr/bin/env python3
"""count-candidates.py — the counting rule, implemented.

Every candidate string is EXTRACTED from a committed artefact of this repository
at a named file:line. Nothing is typed in by hand, so the denominator this pass
publishes is re-derivable from a clean clone. If an anchor stops resolving the
script exits non-zero rather than falling back to a default (AGENTS.md §6 item 2 —
a check that cannot fail is not evidence).

Zero network access. Reads only files tracked in this repository.

  python3 count-candidates.py

Safe to run from ANY working directory — the repo root, this file's own
directory, or a clean `git archive` export of the branch. Paths are resolved
against the repository root located by walking up from THIS FILE, never from
os.getcwd().

THE COUNTING RULE, stated before the count (AGENTS.md §6 item 7 — 44 became 93
because no rule was recorded):

  R-1 UNIT. One candidate VALUE STRING for the family/discriminator field: an
     exact, case-sensitive token. Not a model, not a device, not a display name.

  R-2 MEMBERSHIP. A string is a candidate iff a committed artefact records it as
     one of:
       (a) a KEY of `personal.device.family.to.model.mapping` (vendor config);
       (b) a member of the patient bundle's `deviceFamily` matcher enum;
       (c) a string the patient client compares that field against;
       (d) a value a named third-party client declares for `deviceFamily` /
           `medicalDeviceFamily`, WHERE that artefact carries a file:line AT A
           NAMED COMMIT.
     A set failing its own clause is NOT admitted, and is printed with the reason
     and with the count it would have produced. That conditional is the finding;
     the admitted union is the number.

  R-3 EXCLUSIONS, each with its reason, and each reported rather than dropped:
       - model codes (`MMT-*`, `SKU-*`) and display names are NOT members; they
         are the MATCH TABLE, counted separately (S-TABLE below). A wire value
         equal to a model code is a different finding from one equal to a family
         token, and mixing the two is how a union becomes a sum.
       - `deviceType` values (`CC`, `COSMOS`, `COSMOS_WHITELISTED`, `DEVICE`) are
         excluded AS `deviceType`. `CC` re-enters only on its own family citation.
       - a string whose only citation is not file:line-at-named-commit is NOT
         counted and its withdrawal is printed.

  R-4 DUPLICATES. A string in more than one admitted set is counted ONCE. The
     union is never the sum of the source counts; the sum is printed beside it
     precisely so the difference is visible.

  R-5 SCOPING. The union counts client/config-side strings. No member is OBSERVED
     on the wire. This script cannot promote anything.
"""

import os
import re
import sys

# Paths in this file are repository-root-relative. Anchor them on the SCRIPT'S
# OWN LOCATION, not on the working directory, so the documented invocation works
# from anywhere — including from this file's own directory, which is what
# AGENTS.md §10 means by "re-run your probe from what you wrote down". Verified
# from the repo root, from this directory, and from a clean `git archive` export.
HERE = os.path.dirname(os.path.abspath(__file__))


def repo_root():
    d = HERE
    for _ in range(8):
        if os.path.isdir(os.path.join(d, 'findings-log')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    sys.exit('PATH MISS: cannot locate the repository root from ' + HERE)


ROOT = repo_root()

# ---- anchors: (source id, file, 1-based first line, 1-based last line) --------
A = {
    'S-MAP': ('findings-log/2026-10-13-area-h-report-naming/'
              'family-map-verbatim.txt', 1, 16),
    'S-ENUM': ('findings-log/probe-2026-10-08/recov/'
               'PATIENT-APP-VOCABULARY.md', 18, 19),
    'S-CLIENT': ('findings-log/2026-10-14-area-s4-lazy-chunk-control-flow/'
                 'FINDINGS.md', 353, 354),
    'S-TABLE': ('findings-log/2026-10-13-area-g-device-tables/'
                'FINDINGS.md', 103, 115),
}

# Declared but NOT admitted: the set fails R-2(d), because the artefact that
# carries it names no file:line at a named commit for the third-party revision
# it was read from. Two cites, deliberately kept apart: :349 is the heading that
# carries the attribution PHRASE, :384-385 is where the token list is. An earlier
# version of this file attributed the phrase to :384-385, which does not contain
# it (correction in FINDINGS.md).
NOT_ADMITTED = ('S-CLIENT-DTO',
                'findings-log/probe-2026-10-08/APP-EMULATION-RESEARCH.md:349 '
                '(heading "from xDrip\'s message classes"); tokens at :384-385',
                'reads "from xDrip\'s message classes" with no file:line and no '
                'named commit for the xDrip revision; a bare PR number is not a '
                'commit. Fails R-2(d).')

# ---- R-3: named exclusions, with the reason they are excluded -----------------
EXCLUDED = [
    ('MINIMED', 'findings-log/2026-10-11-third-party-client-sources/FINDINGS.md:69',
     'cited only as "values seen by these clients"; no file:line, no per-client '
     'attribution anywhere in the repository'),
    ('PARADIGM', 'findings-log/2026-10-11-third-party-client-sources/FINDINGS.md:69',
     'same citation, same defect as MINIMED'),
    ('BLE_MINIMED', 'findings-log/probe-2026-10-08/APP-EMULATION-RESEARCH.md:390',
     'cited to "the upstream PR #2 tests" — a PR number is not file:line at a '
     'named commit (R-2(d))'),
    ('Ut.Ey.all', 'findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md:604',
     'a deviceFamily-FILTER key for a server-populated localStorage object, not a '
     'family value'),
    ('CC/COSMOS/COSMOS_WHITELISTED/DEVICE',
     'findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md:562',
     'deviceType values, not deviceFamily values; excluded as deviceType. `CC` '
     'would re-enter only through its own family citation, which fails R-2(d)'),
]

SETS = ('S-MAP', 'S-ENUM', 'S-CLIENT')


def load(sid):
    path, lo, hi = A[sid]
    try:
        lines = open(os.path.join(ROOT, path), encoding='utf-8').read().splitlines()
    except OSError:
        sys.exit(f'ANCHOR MISS: {sid} -> {path} does not exist')
    if len(lines) < hi:
        sys.exit(f'ANCHOR MISS: {sid} -> {path} has {len(lines)} lines, needs {hi}')
    return lines[lo - 1:hi], path


def uniq(seq):
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out


def parse(sid):
    body, path = load(sid)
    if sid == 'S-MAP':
        got = [l.split('|||')[0].strip() for l in body if '|||' in l]
        want = 16
    elif sid == 'S-ENUM':
        got = [k for l in body
               for k, v in re.findall(r'(\w+):\s*"(\w+)"', l) if k == v]
        want = 5
    elif sid == 'S-CLIENT':
        # the set is one comma-separated backtick span: `BLE, BLE_X, … NGP`
        spans = re.findall(r'`([^`]+)`', '\n'.join(body))
        got = [t.strip() for s in spans for t in s.split(',')
               if re.fullmatch(r'[A-Z][A-Z0-9_]*', t.strip())]
        want = 6
    else:
        sys.exit(f'no parser for {sid}')
    got = uniq(got)
    if len(got) != want:
        sys.exit(f'ANCHOR DRIFT: {sid} expected {want} tokens, '
                 f'parsed {len(got)}: {got}')
    return got


def union_of(sets):
    u, prov = [], {}
    for sid, toks in sets:
        for t in toks:
            if t not in u:
                u.append(t)
            prov.setdefault(t, []).append(sid)
    return u, prov


def main():
    members = {sid: parse(sid) for sid in SETS}

    print('COUNTING RULE R-1..R-5 — see the docstring of this script.')
    print()
    print('ADMITTED SOURCES (every string extracted from a committed artefact '
          'at a named file:line):')
    for sid in SETS:
        print(f'  {sid:<11} {len(members[sid]):>3}  {A[sid][0]}:'
              f'{A[sid][1]}-{A[sid][2]}')

    u, prov = union_of(members.items())
    print()
    print('UNION (R-4: each string once):')
    for tok in sorted(u):
        print(f'  {tok:<16} {",".join(prov[tok])}')
    total = sum(len(members[s]) for s in SETS)
    # Two DIFFERENT quantities, previously conflated under one label:
    #   duplicates      = occurrences beyond first appearance (total - union)
    #   shared_distinct = distinct strings appearing in two or more sources
    # They are 6 and 5 here, because SIMPLERA is in all three sources and so
    # contributes 2 occurrences while contributing 1 distinct string.
    duplicates = total - len(u)
    shared_distinct = sorted(t for t, srcs in prov.items() if len(srcs) > 1)
    print()
    print(f'UNION SIZE (the published number) = {len(u)}')
    print(f'sum of the admitted sources      = {total}  (NOT the answer)')
    print(f'  difference = {total} - {len(u)} = {duplicates} shared OCCURRENCE(s) '
          f'— appearances beyond first mention, NOT distinct strings')
    print(f'  distinct strings in >=2 sources = {len(shared_distinct)}: '
          f'{", ".join(shared_distinct)}')
    print()
    print('OVERLAPS:')
    for i, a in enumerate(SETS):
        for b in SETS[i + 1:]:
            shared = sorted(set(members[a]) & set(members[b]))
            print(f'  {a} & {b}: {shared if shared else "(none)"}')

    print()
    print(f'DECLARED BUT NOT ADMITTED — {NOT_ADMITTED[0]}:')
    print(f'  artefact : {NOT_ADMITTED[1]}')
    print(f'  reason   : {NOT_ADMITTED[2]}')
    u2, _ = union_of(list(members.items())
                     + [('S-CLIENT-DTO', ['GUARDIAN', 'NGP', 'CGM', 'CC'])])
    print(f'  if admitted, the union would be {len(u2)}, not {len(u)} '
          f'(+{len(u2) - len(u)}: CC, CGM)')

    print()
    print('MATCH TABLE (R-3: excluded from the union, counted separately):')
    body, _ = load('S-TABLE')
    toks = uniq(re.findall(r'\b(?:MMT|SKU)-?[A-Z0-9-]+', '\n'.join(body)))
    mmt = [t for t in toks if t.startswith('MMT')]
    sku = [t for t in toks if t.startswith('SKU')]
    print(f'  {A["S-TABLE"][0]}:{A["S-TABLE"][1]}-{A["S-TABLE"][2]}'
          f'  -> {len(mmt)} MMT-* + {len(sku)} SKU-* = {len(toks)} codes')
    print('  display-name pairs: 76 quoted + 2 unquoted aliases + 9 SKU-* = 87,'
          ' quoted from area G FINDINGS.md:118-119 and not re-derived here')

    print()
    print('EXCLUDED UNDER R-3 (named, with reason — never silently dropped):')
    for tok, cite, why in EXCLUDED:
        print(f'  {tok:<32} {cite}')
        print(f'  {"":<32} {why}')


if __name__ == '__main__':
    main()