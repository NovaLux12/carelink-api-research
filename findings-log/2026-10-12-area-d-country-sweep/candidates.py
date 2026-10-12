#!/usr/bin/env python3
"""candidates.py — derive the area D candidate list OFFLINE, from documents
already on disk. Issues ZERO requests.

COUNTING RULE (stated so the number 118 can be re-derived and cannot drift
silently — docs/09 §4, "a count the gate's regex cannot see"):

  A country code is any string of exactly two characters, A-Z, that appears
  INSIDE the value of a top-level key whose name contains "countr"
  (case-insensitively), in any of these three positions:
     (a) as an element of an array,
     (b) as an object key,
     (c) as the value of an object member named "country".
  The three vendor-published public-config documents captured 2026-10-12
  (carelink.minimed.eu / .com / carelink-trials.minimed.com) are the only
  inputs. The result is the UNION over the three documents.

Source documents (gitignored captures, deliberately not committed — the
published-pointers pass found credential-shaped values in the config document;
see that pass's .gitignore):
  findings-log/2026-10-12-published-pointers/docs/config-eu.json
  findings-log/2026-10-12-published-pointers/docs/config-com.json
  findings-log/2026-10-12-published-pointers/docs/config-trials.json

Reads those three paths under --repo and writes:
  candidates.txt        one code per line, sorted, with provenance comments
  reference-keys.json   the reader's key vocabulary (union of top-level key
                        names across the three country documents also captured
                        by that pass)
"""

import argparse
import json
import os
import sys

CAP = 'findings-log/2026-10-12-published-pointers/docs'
CONFIGS = ['config-eu.json', 'config-com.json', 'config-trials.json']
COUNTRY_DOCS = ['countries-eu.json', 'countries-com.json', 'countries-trials.json']


def is_code(s):
    return isinstance(s, str) and len(s) == 2 and s.isalpha() and s.isupper()


def codes_in(value, out):
    if isinstance(value, list):
        for v in value:
            if is_code(v):
                out.add(v)
            else:
                codes_in(v, out)
    elif isinstance(value, dict):
        for k, v in value.items():
            if is_code(k):
                out.add(k)
            if k.lower() == 'country' and is_code(v):
                out.add(v)
            codes_in(v, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True, help='a clean clone or worktree')
    ap.add_argument('--out', required=True, help='output directory')
    a = ap.parse_args()
    base = os.path.join(a.repo, CAP)

    prov = {}
    for f in CONFIGS:
        path = os.path.join(base, f)
        if not os.path.exists(path):
            print(f'MISSING {path} — the published-pointers captures are '
                  f'gitignored; re-derive with that pass\'s probe.sh', file=sys.stderr)
            return 2
        with open(path, encoding='utf-8') as fh:
            doc = json.load(fh)
        found = set()
        for k, v in doc.items():
            if 'countr' in k.lower():
                codes_in(v, found)
        tag = f[len('config-'):-len('.json')]
        for c in sorted(found):
            prov.setdefault(c, []).append(tag)

    ref = set()
    for f in COUNTRY_DOCS:
        path = os.path.join(base, f)
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as fh:
            doc = json.load(fh)
        if isinstance(doc, dict):
            ref.update(doc)

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, 'candidates.txt'), 'w', encoding='utf-8') as fh:
        fh.write('# Area D candidate list — derived offline, zero requests.\n')
        fh.write('# Derivation and counting rule: candidates.py (same directory).\n')
        fh.write('# Provenance per code = which published config document(s) '
                 'list it.\n')
        fh.write(f'# Union size: {len(prov)}\n')
        for c in sorted(prov):
            fh.write(f'{c}\t{",".join(prov[c])}\n')
    with open(os.path.join(a.out, 'reference-keys.json'), 'w', encoding='utf-8') as fh:
        json.dump(sorted(ref), fh, indent=1)
        fh.write('\n')
    print(f'{len(prov)} candidate country codes; reader vocabulary {len(ref)} keys')
    return 0


if __name__ == '__main__':
    sys.exit(main())