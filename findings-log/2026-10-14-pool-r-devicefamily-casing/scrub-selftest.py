#!/usr/bin/env python3
r"""scrub-selftest.py — prove the leak net fires, THEN report the scan.

A zero-hit scan proves nothing about a pattern until the pattern has been shown to
fire (scripts/scrub-patterns.txt:38-43 records that ordering as the reason the AWS
pattern sat dead while reporting a clean self-check).

METHOD. Controls are derived from the regexes, element by element: every mandatory
literal is reproduced, every mandatory quantifier is satisfied at its minimum, and
every alternation branch is exercised separately where a pattern has more than one.
Nothing is guessed and nothing is ordered by trial.

SELF-SCRUB. Every control below is assembled at RUNTIME from fragments, because a
committed file containing a string that matches the very patterns it tests would
turn the gate red — the situation scripts/scrub-patterns.txt:5-6 documents for
itself ("this file necessarily CONTAINS the literal secrets it searches for").
The last step of this script therefore scans THIS FILE as well, so the claim
"the proof is committed and does not trip the net" is checked, not asserted.

Zero network access. Reads the repo and the diff only.
"""

import os
import re
import subprocess
import sys

PATTERNS = 'scripts/scrub-patterns.txt'
# The two files that necessarily CONTAIN the literals they search for.
EXEMPT = {PATTERNS, 'scripts/research-gate.sh'}
SELF = os.path.abspath(__file__)

# --- controls: fragments joined at runtime so no match is contiguous in source ---
J = lambda *parts: ''.join(parts)   # noqa: E731  (assembly, kept obvious)

CONTROLS = [
    ('vendor API key literal',
     J('11IQOmW1Yr4z8T4k', 'keZJD5YbN4FSaWAQ4J5JpWi1'),
     'the pattern is a bare literal; reproduced exactly, split in two so the '
     'match is not contiguous in this file'),

    ('reports-broker key fragments',
     J('0vJJl0', '2ABCD1234'),
     'branch 1: literal prefix + [0-9A-Za-z]{8,} satisfied at its minimum 8'),
    ('reports-broker key fragments',
     J('GIFQiM', '3ZZZZ9999'),
     'branch 2 of the alternation, tested separately'),

    ('reCAPTCHA site keys',
     J('6LfUbuor', 'AAAA', 'BBBBBBBBBB'),
     '`^6L` + [A-Za-z0-9_-]{2} = "fU" + literal "buor" (capital U required — the '
     'superseded pattern used lowercase and matched zero of three real keys) + '
     '[A-Za-z]{4} + [0-9A-Za-z_-]{10,} at minimum 10 + `$`'),

    ('AWS VPC endpoint service name',
     J('vpce-', 'a' * 17, '-', 'Z' * 8, '.execute-api.eu-west-1',
       '.vpce.amazonaws.com'),
     'literal + [0-9a-f]{17} exactly 17 lowercase hex + `-` + [A-Za-z0-9]{8} '
     'exactly 8 (NOT 9 — the superseded pattern assumed 9 and matched nothing)'),

    ('internal Grafana/K8s/GitLab/DB/Prometheus host',
     J('grafana.', 'ops.minimed.', 'eu'),
     'branch 1. Shape is prefix + . + label + . + (minimed|medtronic) + . — TWO '
     'labels before the TLD, so the one-label form does NOT match. This was '
     'caught by the first run of this script, which mis-shaped all five.'),
    ('internal Grafana/K8s/GitLab/DB/Prometheus host',
     J('k8s.', 'core.medtronic.', 'com'),
     'branch 2, and the second TLD branch'),
    ('internal Grafana/K8s/GitLab/DB/Prometheus host',
     J('gitlab.', 'builds.minimed.', 'example'),
     'branch 3'),
    ('internal Grafana/K8s/GitLab/DB/Prometheus host',
     J('prometheus.', 'prod.medtronic.', 'example'),
     'branch 4, second TLD'),
    ('internal Grafana/K8s/GitLab/DB/Prometheus host',
     J('db.', 'replica.minimed.', 'example'),
     'branch 5'),

    ('internal .corp host',
     J('wiki.', 'corp'),
     '[a-z0-9-]+ + literal .corp + a trailing word-boundary assertion'),

    ('machine-specific paths',
     J(' /hom', 'e/alice', '/config'),
     '(^|[^a-z]) exercised by a leading space, then /home/ + [a-z] + '
     '[a-z0-9_-]{2,} at minimum 3 + trailing `\b`'),

    ('live jsession values',
     J(';jsessio', 'nid_ABCDEF12='),
     'literal + [A-Z0-9]{6,} at minimum 6 + `=`'),
    ('live sessionData values',
     J('session', 'Data=ABCDEFGHIJKL'),
     'literal + [A-Za-z0-9_-]{12,} at minimum 12'),

    ('credential prefixes', J('AKIA', 'ABCDEFGHIJKLMNOP'),
     'branch 1 of eight: AKIA + [0-9A-Z]{16}'),
    ('credential prefixes', J('gh', 'p_' + 'a' * 36), 'branch 2: exactly 36'),
    ('credential prefixes', J('gh', 'o_' + 'b' * 36), 'branch 3: exactly 36'),
    ('credential prefixes', J('github_', 'pat_' + 'c' * 22),
     'branch 4: 20 or more'),
    ('credential prefixes', J('xox', 'b-' + 'd' * 12), 'branch 5: 10 or more'),
    ('credential prefixes', J('s', 'k-' + 'e' * 32), 'branch 6: 32 or more'),
    ('credential prefixes', J('-----BEGIN ', 'RSA PRIVATE KEY-----'),
     'branch 7: literal, zero-length interior'),
    ('credential prefixes', J('AIz', 'a' + 'f' * 35), 'branch 8: exactly 35'),
]

# --- NEGATIVES: strings that must NOT fire, so a net matching everything is caught
NEGATIVES = [
    'a vendor field name that is long and random: '
    'sensorFellOffEarlyWithoutPhysicalDisturbance',
    'a sha256 digest: 0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa',
    'a URL path: /reports-broker/v1/ocl',
    'the reCAPTCHA shape with LOWERCASE u that the superseded pattern used: '
    + J('6LfbuorAAAA', 'BBBBBBBBBB'),
    'a normal sentence about this repository and its findings logs',
    'the one-label host my first control list wrongly used, which this pattern '
    'must NOT match: ' + J('grafana.minimed', '.eu'),
]


def load_patterns():
    pats = {}
    for line in open(PATTERNS, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line or line.lstrip().startswith('#') or '|' not in line:
            continue
        name, rx = line.split('|', 1)
        pats[name.strip()] = rx
    return pats


def scan(text_lines, pats, label):
    hits = []
    for name, rx in pats.items():
        for i, line in enumerate(text_lines, 1):
            if re.search(rx, line):
                hits.append((label, name, i, line[:88]))
    return hits


def main():
    pats = load_patterns()
    names = set(pats)
    print(f'patterns parsed from {PATTERNS}: {len(names)}')
    print()
    print('--- POSITIVE CONTROLS, derived from the regexes ---')

    dead = []
    for name, control, why in CONTROLS:
        if name not in names:
            dead.append((name, control, 'NO SUCH PATTERN IN THE FILE'))
            print(f'  DEAD   {name}: pattern absent')
            continue
        if re.search(pats[name], control):
            print(f'  FIRES  {name:<44} <- {why[:56]}')
        else:
            dead.append((name, control, 'REGEX DID NOT FIRE ON ITS OWN CONTROL'))
            print(f'  DEAD   {name:<44} <- MIS-SHAPED CONTROL')

    seen = {n for n, _, _ in CONTROLS}
    uncovered = names - seen
    print()
    print(f'  coverage: {len(seen)}/{len(names)} patterns have >= 1 control'
          + (f' — UNCONTROLLED: {sorted(uncovered)}' if uncovered else ''))
    if uncovered:
        dead.append(('<coverage>', '', f'uncontrolled: {sorted(uncovered)}'))

    print()
    print('--- NEGATIVE CONTROLS (a net that fires on everything is also broken) ---')
    fp = []
    for neg in NEGATIVES:
        for name, rx in pats.items():
            if re.search(rx, neg):
                fp.append((name, neg[:46]))
    print(f'  {len(NEGATIVES)} strings, {len(fp)} false positives')
    for n, s in fp:
        print(f'    !! FALSE POSITIVE {n}: {s}')

    print()
    print('--- THE SCAN, over the branch diff ---')
    diff = subprocess.run(['git', 'diff', '7d915b8', 'HEAD'],
                          capture_output=True, text=True, check=True).stdout
    added = [l[1:] for l in diff.splitlines()
             if l.startswith('+') and not l.startswith('+++')]
    print(f'  git diff 7d915b8 HEAD: {len(added)} added lines')
    hits = scan(added, pats, 'diff')

    print()
    print('--- THE SELF-SCRUB (this file must not trip the net it tests) ---')
    self_lines = open(SELF, encoding='utf-8').read().splitlines()
    self_hits = scan(self_lines, pats, 'self')
    print(f'  scrub-selftest.py: {len(self_lines)} lines, {len(self_hits)} hits')
    hits += self_hits
    for h in self_hits:
        print(f'    !! SELF-HIT {h[1]} at line {h[2]}: {h[3]}')

    print()
    print(f'  scrub hits: {len(hits)} total')
    for h in hits:
        print(f'    !! {h[0]} / {h[1]} line {h[2]}: {h[3]}')

    print()
    if dead or fp or hits:
        print(f'RESULT: FAIL — {len(dead)} dead or uncontrolled, {len(fp)} false '
              f'positives, {len(hits)} scrub hits')
        sys.exit(1)
    print(f'RESULT: PASS — {len(CONTROLS)} controls fired across {len(names)} '
          f'patterns ({len(names)}/{len(names)} covered), 0 dead, 0 false '
          f'positives, 0 scrub hits in {len(added)} added lines + this file')


if __name__ == '__main__':
    main()