#!/usr/bin/env python3
"""Reconcile the observed tenant set against every host and kid string already
recorded in the corpus. Eyeballing base64url identifiers is how this repo has
been wrong before (AGENTS.md §6 #2: a token that hit without proving what it
meant), so every comparison here is exact string equality against a named
file:line, and disagreements are printed rather than resolved.
"""
import json, os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

OBS = {}
for tag in ('t03-trials-jwks', 't06-eu-jwks', 't09-us-jwks',
            't12-meu-jwks', 't16-mcom-jwks'):
    OBS[tag] = json.load(open(os.path.join(HERE, 'bodies', tag + '.b')))
OBSKIDS = {t: [k['kid'] for k in d['keys']] for t, d in OBS.items()}

TAG2HOST = {'t03-trials-jwks': 'carelink-login-trials.minimed.com',
            't06-eu-jwks': 'carelink-login.minimed.eu',
            't09-us-jwks': 'carelink-login.minimed.com',
            't12-meu-jwks': 'carelink-login.medtronic.eu',
            't16-mcom-jwks': 'carelink-login.medtronic.com'}

# Every 20-char base64url-ish token that appears in the corpus next to a host
# name, with the file:line it came from.
KIDRE = re.compile(r'`([A-Za-z0-9_\-]{20,24})`')
corpus = subprocess.run(['git', 'ls-files'], capture_output=True, text=True,
                        cwd=ROOT).stdout.split()
hits = {}
for f in corpus:
    if not f.endswith('.md'):
        continue
    p = os.path.join(ROOT, f)
    try:
        lines = open(p, errors='replace').read().splitlines()
    except OSError:
        continue
    for i, line in enumerate(lines, 1):
        for tok in KIDRE.findall(line):
            hits.setdefault(tok, []).append(f"{f}:{i}")

allobserved = [k for v in OBSKIDS.values() for k in v]
print('=' * 78)
print('E. observed kids vs the corpus')
print('=' * 78)
for tag, ks in OBSKIDS.items():
    host = TAG2HOST[tag]
    print(f"\n{host}")
    for k in ks:
        where = hits.get(k)
        if where:
            print(f"  OBSERVED + IN CORPUS  {k}   at {', '.join(where[:4])}")
        else:
            print(f"  OBSERVED, NOT IN CORPUS  {k}   <-- new")
            # show corpus tokens that look like a near-miss for this host line
            for f in corpus:
                if not f.endswith('.md'): continue
                try:
                    txt = open(os.path.join(ROOT, f), errors='replace').read()
                except OSError:
                    continue
                for i, line in enumerate(txt.splitlines(), 1):
                    if host in line:
                        for tok in KIDRE.findall(line):
                            if tok in allobserved: continue
                            same = sum(a == b for a, b in zip(tok, k))
                            print(f"      corpus-only token {tok!r} at {f}:{i} "
                                  f"(len {len(tok)} vs {len(k)}, "
                                  f"{same}/{min(len(tok),len(k))} leading chars equal)")

print()
print('=' * 78)
print('F. host sets')
print('=' * 78)
HOSTRE = re.compile(r'carelink-login(?:-trials)?\.[a-z]+\.[a-z]+')
# Scope is TRACKED MARKDOWN ONLY (see the f.endswith('.md') filter below), not
# "the tracked corpus" as an earlier revision of this file's own summary claimed.
# Tightened 2026-10-12: a conclusion is only as strong as the scan behind it.
# No host name in this repo's conclusions is sourced from a non-.md file -- the
# tenant set comes from the captured discovery documents and JWKS bodies, which
# are ledger rows, not prose -- so the finding is unaffected.
SCAN_EXTS = ('.md',)
corpus_hosts = {}
for f in corpus:
    if not f.endswith(SCAN_EXTS): continue
    try:
        txt = open(os.path.join(ROOT, f), errors='replace').read()
    except OSError:
        continue
    for h in set(HOSTRE.findall(txt)):
        corpus_hosts.setdefault(h, set()).add(f)
mine = set(TAG2HOST.values())
print(f'hosts this pass compared ({len(mine)}):')
for h in sorted(mine):
    print(f'  {h}')
print(f'\ncorpus names {len(corpus_hosts)} distinct carelink-login.* hosts; '
      f'{len(mine & set(corpus_hosts))} of mine are in it')
print('\ncorpus hosts NOT in this pass:')
for h in sorted(set(corpus_hosts) - mine):
    print(f'  {h:<44} named in {len(corpus_hosts[h])} file(s): '
          f'{sorted(corpus_hosts[h])[:3]}')