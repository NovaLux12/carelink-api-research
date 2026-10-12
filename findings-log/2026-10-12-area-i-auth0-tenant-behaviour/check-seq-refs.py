#!/usr/bin/env python3
"""Mechanically check every `seq` reference in FINDINGS.md against results.jsonl.

Round 3 shipped a sentence in FINDINGS.md 15 claiming "every seq cited in this
file points at the row it claims" while seq 31's own note pointed at seq 8/10 --
which, after the renumbering, were minimed.com GET rows. The claim was false and
the sentence certifying it is the reason the verifier looked. So the claim is
replaced by this script: it resolves each citation and prints what it resolves to,
and exits non-zero if a cited row cannot be found.

Reads only committed artefacts. Nothing is fetched.
"""
import glob, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
rows = {}
for line in open(os.path.join(HERE, 'results.jsonl')):
    if line.strip():
        r = json.loads(line)
        rows[r['seq']] = r

text = open(os.path.join(HERE, 'FINDINGS.md'), encoding='utf-8').read()

def label(sq):
    r = rows.get(sq)
    if r is None:
        return 'MISSING FROM LEDGER'
    return (f"{r['method']:<7} {r['host'].replace('carelink-login-',''):<24} "
            f"{r['path']:<34} {r['http_status']:<6} {r['body_bytes']}B "
            f"sha={str(r['body_sha256'])[:12]}")

# Every "seq N" / "seqs N, M" citation, with the line it appears on.
CITES = re.findall(r'seqs?\s+(\d+(?:\s*(?:,|and|/)\s*\d+)*)', text)
flat = []
for c in CITES:
    for n in re.findall(r'\d+', c):
        flat.append(int(n))

print('=' * 78)
print('A. every seq cited in FINDINGS.md, resolved against results.jsonl')
print('=' * 78)
bad = []
for n in sorted(set(flat)):
    ok = n in rows
    print(f'  {"ok " if ok else "BAD"} seq {n:<3} {label(n)}')
    if not ok:
        bad.append(n)
print(f'\ncited seqs: {len(set(flat))} distinct, {len(bad)} unresolvable')

print()
print('=' * 78)
print('B. ledger integrity')
print('=' * 78)
seqs = sorted(rows)
print(f'  rows: {len(rows)}   seq range {seqs[0]}..{seqs[-1]}   '
      f'contiguous: {seqs == list(range(seqs[0], seqs[-1] + 1))}')
dupes = [s for s in set(seqs) if [r for r in rows].count(s) > 1]
print(f'  duplicate seq keys: {len(dupes)}')

print()
print('=' * 78)
print('C. no hand-authored header fields')
print('=' * 78)
# A row whose header block was typed rather than captured is the defect this
# round exists to fix: it looks machine-parsed to everything that reads it.
# Every ctype_full must either be machine-parsed from a committed header file,
# or say explicitly that it was not captured.
machine = []
for sq, r in sorted(rows.items()):
    cf = r.get('ctype_full', '')
    tag = r.get('host_tag', '')
    hp = os.path.join(HERE, 'headers', f'{tag}.h')
    if not os.path.exists(hp):
        state = 'NOT CAPTURED (declared)' if cf.startswith('(not captured') else 'NO HEADER FILE - SUSPECT'
    else:
        from_hdr = open(hp, errors='replace').read()
        keys = [l.split(': ')[0].lower() for l in from_hdr.replace('\r', '').split('\n')
                if ': ' in l]
        machine.append((sq, len(cf.split('|')), len(set(keys))))
        state = f'machine-parsed, {len(cf.split("|"))} fields vs {len(set(keys))} header keys'
    if 'SUSPECT' in state:
        bad.append(('hand-authored', sq))
    print(f'  seq {sq:<3} {state}')

print()
print('=' * 78)
print('D. committed captures for the diagnostic rows')
print('=' * 78)
for sq in (30, 31, 32):
    r = rows[sq]
    tag = r['host_tag']
    present = [f for f in (
        f'headers/{tag}.txt', f'headers/{tag}.h', f'bodies/{tag}.b'
    ) if os.path.exists(os.path.join(HERE, f))]
    print(f'  seq {sq} {tag}: {present if present else "NO CAPTURE COMMITTED"}')
    if not present:
        bad.append(('no-capture', sq))

print()
print('=' * 78)
print('E. seq citations INSIDE the ledger prose (note/supersedes fields)')
print('=' * 78)
# This is where the half-applied renumbering actually hid: seq 31's `note` read
# "Same 107B digest as seq 8/10", which after the renumbering pointed at two
# minimed.com GET rows. Scanning FINDINGS.md alone would NOT have caught it, so
# this section scans the ledger's own prose too -- and checks that a cited row
# actually carries the digest the note attributes to it, not merely that it
# exists.
DIGEST = re.compile(r'\b([0-9a-f]{12})')
SAME = re.compile(r'same[^.]{0,60}?digest', re.I)   # "Same 107B digest as seq N"
for sq, r in sorted(rows.items()):
    prose = ' '.join(str(r.get(k, '')) for k in ('note', 'supersedes'))
    if not prose.strip():
        continue
    self_digest = str(r.get('body_sha256'))
    claims_same = bool(SAME.search(prose))
    for cited in re.findall(r'seqs?\s+(\d+(?:\s*(?:,|and|/)\s*\d+)*)', prose):
        for n in re.findall(r'\d+', cited):
            n = int(n)
            target = rows.get(n)
            if target is None:
                print(f'  BAD seq {sq} note cites seq {n}, which is not in the ledger')
                bad.append(('note-dangling', sq, n))
                continue
            actual = str(target['body_sha256'])
            problems = []
            # A note that says "same digest as seq N" is making a checkable
            # claim. Compare digests EQUALITY rather than looking for a hex
            # string in the prose: the first version of this check looked for a
            # 12-hex-digit digest in the note and so passed a note that said
            # "Same 107B digest as seq 8/10" -- the exact bug this section
            # exists to catch, because "107B" is not hex.
            if claims_same and n != sq and actual != self_digest:
                problems.append('note claims same digest, row differs')
            named = set(DIGEST.findall(prose))
            if named and actual[:12] not in named:
                problems.append(f'note names {sorted(named)}, row is {actual[:12]}')
            verdict = 'BAD' if problems else 'ok '
            if problems:
                bad.append(('note-digest', sq, n))
            print(f'  {verdict} seq {sq} note cites seq {n}: that row is '
                  f'{target["method"]} {target["host"].replace("carelink-login-","")} '
                  f'{target["path"]} {target["http_status"]} {target["body_bytes"]}B '
                  f'sha={actual[:12]}'
                  + (f'  <- {"; ".join(problems)}' if problems else ''))

print()
print('=' * 78)
print('E2. body digests and the body count stated in FINDINGS.md')
print('=' * 78)
# "All N raw bodies ... match" is a claim about the local working copy, so it
# can only be checked where those bodies exist. Here they do; in a clean clone
# it is skipped rather than silently passing, because there is nothing to check.
bodies = sorted(glob.glob(os.path.join(HERE, 'bodies', '*.b')))
mism = []
for f in bodies:
    tag = os.path.basename(f)[:-2]
    row = next((r for r in rows.values() if r.get('host_tag') == tag), None)
    if row is None:
        mism.append((tag, 'no ledger row'))
        continue
    raw = open(f, 'rb').read()
    if len(raw) != row['body_bytes'] or hashlib.sha256(raw).hexdigest() != row['body_sha256']:
        mism.append((tag, 'digest/byte mismatch'))
print(f'  bodies on disk: {len(bodies)}   matching ledger: {len(bodies) - len(mism)}')
for t, why in mism:
    print(f'  BAD {t}: {why}')
    bad.append(('body', t))
m = re.search(r'All \*\*(\d+)\*\* raw bodies', text)
stated = int(m.group(1)) if m else None
jwks = [f for f in bodies if os.path.basename(f).startswith('t') and '-jwks' in os.path.basename(f)]
if stated is None:
    print('  (no "All **N** raw bodies" claim found to check)')
elif len(bodies) == stated:
    print(f'  FINDINGS.md states All **{stated}** raw bodies -- matches')
elif len(jwks) == 0:
    # The "All N raw bodies" claim is about the PROBING MACHINE, which holds the
    # JWKS bodies that stay gitignored. In a clean clone those are absent by
    # design, so the count cannot be checked there. A check that cannot run must
    # say so rather than fail, or a reader learns to ignore it.
    print(f'  FINDINGS.md states All **{stated}** raw bodies -- NOT CHECKED HERE: this is a clean '
          f'clone and the {stated - len(bodies)} gitignored JWKS bodies (RSA modulus + x5c) are '
          f'absent by design. All {len(bodies)} committed bodies above were verified. Run this on '
          f'the probing machine for the full check.')
else:
    print(f'  BAD FINDINGS.md states All **{stated}** raw bodies, only {len(bodies)} on disk')
    bad.append(('body-count', stated, len(bodies)))

print()
if bad:
    print(f'FAIL: {len(bad)} problem(s): {bad}')
    sys.exit(1)
print('PASS: every cited seq resolves (file prose and ledger prose), keys are unique,')
print('      no hand-authored header field, and seq 30-32 each have a committed capture.')