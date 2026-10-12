#!/usr/bin/env python3
"""measure-assertions.py — the ONE counting rule for this repo's assertion counts.

Usage:
  python3 scripts/measure-assertions.py            # prints "<static> <runtime>"
  python3 scripts/measure-assertions.py --json     # the counts.json the badge reads

THE COUNTING RULE
-----------------
This repo's badge, the gate's numbers check and the drift sweep's badge job
all read the number from here, because a number maintained in three places is
a number that will disagree with two of them. It already has: 93 was right
once and then silently wrong after two rounds of suite growth, a 195 appeared
from counting request lines, and a 95 from miscounting the loop's check site.
The rule is written down so the next person to add a pin changes the rule, the
number, and nothing else.

  static  = jsonpath/header predicates inside [Asserts] blocks across the four
            .hurl suites
          + `check "` sites in 05-public-config.check.sh
            (the site inside the 16-family loop counts ONCE — it is one site;
            it executes 16 times. That distinction is the trap.)

  runtime = hurl part + 2 x `HTTP` lines
              (hurl counts each status line as two asserts: version + code)
          + 05's executed assertions: non-loop check sites + the loop site x16
            + the 5 inline PASS branches
            (the live suite prints this as "<n> passed"; pass --observed-05
             with that number to use the measured value instead of the rule's)
"""

import argparse
import datetime
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HURL_DIR = os.path.join(ROOT, 'regression/hurl')
CONFIG_SUITE = os.path.join(HURL_DIR, '05-public-config.check.sh')

# The inline assertion families in 05 that are not a `check "` call: the shadow
# grep, the two sibling 412 checks, the two family-map hash comparisons, and the
# two portal-build markers added by area A on 2026-10-12 (05-public-config.check.sh
# — see its own PASS/FAIL branches). Count the EXECUTED total, not the site
# count: the family-map and build-marker loops each run twice.
INLINE_05 = 7
LOOP_FAMILY_SITES = 16


def _read(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        return fh.read()


def measure(root=ROOT, observed_05=None):
    """Return a dict of measured counts. `observed_05` is the "<n> passed"
    line from a live 05 run; when given it replaces the derived rule for 05."""
    predicates = http_lines = 0
    per_suite = {}
    for f in sorted(glob.glob(os.path.join(root, 'regression/hurl/*.hurl'))):
        in_asserts = False
        p = h = 0
        for line in _read(f).splitlines():
            s = line.strip()
            if re.match(r'^\[[A-Za-z]+\]$', s):
                in_asserts = (s == '[Asserts]')
                continue
            if in_asserts and (s.startswith('jsonpath ') or s.startswith('header ')):
                p += 1
            if s.startswith('HTTP '):
                h += 1
        per_suite[os.path.basename(f).replace('.hurl', '')] = p
        predicates += p
        http_lines += h

    sites = loop_sites = 0
    for line in _read(os.path.join(root, 'regression/hurl/05-public-config.check.sh')).splitlines():
        if re.match(r'^\s*check\s+"', line):
            sites += 1
            if line[0] in ' \t':
                loop_sites += 1
    per_suite['05-public-config'] = sites

    derived_05 = (sites - loop_sites) + LOOP_FAMILY_SITES * loop_sites + INLINE_05
    executed_05 = observed_05 if observed_05 is not None else derived_05
    static = predicates + sites
    runtime = (predicates + 2 * http_lines) + executed_05
    return {
        'static': static,
        'runtime': runtime,
        'predicates': predicates,
        'http_lines': http_lines,
        'check_sites': sites,
        'loop_sites': loop_sites,
        'executed_05': executed_05,
        'executed_05_derived': derived_05,
        'suites': per_suite,
    }


def counts_json(m, run_url='', commit=''):
    return {
        'generated_utc': datetime.datetime.now(datetime.timezone.utc)
                                .strftime('%Y-%m-%dT%H:%M:%SZ'),
        'run_url': run_url,
        'commit': commit,
        'assertions': {'static': m['static'], 'runtime': m['runtime']},
        'detail': {
            'predicates': m['predicates'],
            'http_lines': m['http_lines'],
            'check_sites': m['check_sites'],
            'loop_sites': m['loop_sites'],
            'executed_05': m['executed_05'],
            'suites': m['suites'],
        },
        'rule': ('static = predicates inside [Asserts] + check sites '
                 '(family-loop site counted once); runtime = predicates + 2xHTTP '
                 '+ 05 executed. See scripts/measure-assertions.py.'),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true',
                    help='print the counts.json the badge reads')
    ap.add_argument('--observed-05', type=int, default=None,
                    help="the '<n> passed' count from a live 05 run, if you have it")
    args = ap.parse_args()
    m = measure(observed_05=args.observed_05)
    if args.json:
        print(json.dumps(counts_json(
            m,
            run_url=os.environ.get('RUN_URL', ''),
            commit=os.environ.get('GITHUB_SHA', '')[:12]), indent=2))
    else:
        print(m['static'], m['runtime'])


if __name__ == '__main__':
    main()