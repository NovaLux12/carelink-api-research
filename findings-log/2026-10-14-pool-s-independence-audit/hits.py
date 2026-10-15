#!/usr/bin/env python3
"""hits.py — the population table for the area S independence audit.

Zero network requests. Reads only committed text in this repository.

Re-derives the occurrence list from the same eleven phrases AGENTS.md 2.1
names, left-to-right, longest-alternative-first, and prints one row per hit
with its file, line, the phrase matched and a short excerpt.

Usage:  python3 hits.py            # the table
        python3 hits.py --words    # just the phrase tallies
"""
import os
import re
import subprocess
import sys

# Longest first: the alternation is first-match-wins, so this order is what
# makes `corroborated independently` one hit and not two.  AGENTS.md 2.1.
PHRASES = [
    'double-sourced',
    'verifies independently',
    'corroborated independently',
    'confirms independently',
    'not contradicted by',
    'consistent with',
    'agrees with',
    'independently',
    'corroborated',
    'confirms',
    'supports',
]
# Correction (2026-10-14): the first version had no left word boundary, and
# `agrees with` matched inside `disagrees with` - the OPPOSITE word - in three
# places. A grep that hits without proving is AGENTS.md section 6 item 2, and
# this pass's own counting rule committed it. `\\b` before every alternative
# fixes exactly those 3 and nothing else; `uncorroborated` and `inconsistent with`
# do not occur here, but the boundary is what stops them.
PAT = re.compile(r'\b(?:' + '|'.join(re.escape(p) for p in PHRASES) + ')', re.I)

TOP = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                     capture_output=True, text=True).stdout.strip()
os.chdir(TOP)                      # so the script runs from any directory
IN_SCOPE = subprocess.run(['git', 'ls-files', 'docs', 'README.md'],
                          capture_output=True, text=True).stdout.split()
RULE_TEXT = ['AGENTS.md']          # reported separately, per FINDINGS.md 0-S


def hits(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        for n, line in enumerate(fh, 1):
            for m in PAT.finditer(line):
                yield n, m.group(0), line.rstrip('\n')


def main():
    rows = []
    for path in IN_SCOPE:
        for n, word, line in hits(path):
            rows.append((path, n, word.lower(), line))
    if '--words' in sys.argv:
        tally = {}
        for _, _, w, _ in rows:
            tally[w] = tally.get(w, 0) + 1
        for w, c in sorted(tally.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f'{c:4d}  {w}')
        print(f'{len(rows):4d}  TOTAL occurrences in scope')
        return
    prev = None
    for path, n, word, line in rows:
        if (path, n) != prev:
            loc = f'{path}:{n}'
            print(f'\n{loc}  [{word}]')
            prev = (path, n)
        else:
            print(f'{" " * (len(path) + len(str(n)) + 2)}[{word}]')
        print('    ' + line.strip()[:400])
    print(f'\n--- {len(rows)} occurrences across {len({(p, n) for p, n, _, _ in rows})} '
          f'matching lines in {len(IN_SCOPE)} in-scope files ---')


if __name__ == '__main__':
    main()
