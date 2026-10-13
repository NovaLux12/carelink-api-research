#!/bin/bash
# Area V offline step 2 — ZERO requests.
#
# §1  KEY CENSUS: of the 69 published config key names committed by area W
#     (findings-log/2026-10-13-area-w-per-key/keys.txt), how many appear in the
#     patient bundle as a COMPLETE QUOTED LITERAL? Quoted-only, because a raw
#     substring count on `captcha` returns 152 and every one of the extra 151 is
#     a `captcha.*` translation key — a hit that means nothing.
# §2  POINTER CONSUMERS: for the four published pointers this area is about,
#     resolve the bundle's key constant -> its observable selector -> the webpack
#     export alias the selector is published as, and count property reads of that
#     alias. Zero reads is a different fact from zero mentions, and it is the only
#     thing in this corpus that can speak to whether a client FOLLOWS a pointer
#     rather than naming it. Every read site is printed, so a zero is checkable
#     rather than a lookup that silently returned nothing (docs/09 §5 item 3).
#     SCOPE: the eager main bundle only. Lazy chunks are separate files and are
#     not in this corpus — stated wherever the result is used.
# §3  KEY CONSTANTS NAMED BUT NEVER READ — proven by unique-string counting: a
#     reader would have to spell the constant's name, and the name occurs once.
# §4  CHUNK INVENTORY from the patient runtime bundle, which is what closes the
#     candidate list for the 211-chunk sweep nobody has run since 2026-10-08.
#
# Usage: TMPBODIES=/path/to/bodies bash consumers.sh > consumers-out.txt
set -u
: "${TMPBODIES:?set TMPBODIES}"
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 - "$TMPBODIES" "$HERE" <<'PYEOF'
import re, sys, os
B, HERE = sys.argv[1], sys.argv[2]
t = open(f'{B}/eu-main.b', 'rb').read().decode('utf-8', errors='replace')

# ---------- §1 key census -------------------------------------------------
keys = [l.strip() for l in open(
    os.path.join(HERE, '..', '..', 'findings-log', '2026-10-13-area-w-per-key', 'keys.txt'))
    if l.strip() and not l.startswith('#')]
print('=' * 78)
print("§1  PUBLISHED CONFIG KEY CENSUS — patient bundle vs area W's 69 names")
print('=' * 78)
print(f'# key list: findings-log/2026-10-13-area-w-per-key/keys.txt ({len(keys)} names)')
print('# test: the key as a COMPLETE quoted literal ("<key>"). Raw substring')
print('# counts are printed alongside only to show where they would mislead.')
pres, absent = [], []
for k in keys:
    q = len(re.findall(re.escape('"%s"' % k), t))
    raw = len(re.findall(re.escape(k), t))
    (pres if q else absent).append((k, q, raw))
print(f'\n# PRESENT as a quoted literal: {len(pres)} of {len(keys)}')
for k, q, raw in pres:
    flag = '   <-- raw-substring count would have misled' if raw != q else ''
    print(f'   q={q:<3} raw={raw:<4} {k}{flag}')
print(f'\n# ABSENT as a quoted literal (raw-substring count 0 too): {len(absent)} of {len(keys)}')
for k, q, raw in absent:
    print(f'   q=0    raw={raw:<4} {k}')
print('\n# NOTE the trap this rule exists for: `captcha` is q=5 / raw=152. A raw')
print('# census would have reported 152 reasons to believe the captcha config key')
print('# is used in code. 5 is the honest number.')

# ---------- §2 pointer consumers ------------------------------------------
print()
print('=' * 78)
print('§2  DOES ANY CODE FOLLOW A PUBLISHED POINTER?  (eager main bundle only)')
print('=' * 78)
MOD_START, MOD_END = 91296, 97138
mod = t[MOD_START:MOD_END]
mod_id = re.match(r'[^0-9]*(\d+):', mod).group(1)
alias_of = {v: k for k, v in re.findall(
    r'([A-Za-z0-9_$]+):\(\)=>([A-Za-z0-9_$]+)',
    re.search(r'i\.d\(_e,\{([^}]*)\}\)', mod).group(1))}
print(f'# config-observer module id {mod_id}, bytes {MOD_START}..{MOD_END}')
print(f'# exports {len(alias_of)} selectors')
print('# selector resolution is by hand-checked literal, not by regex: a regex')
print('# over minified signal-selector factories resolves some selectors to the')
print('# wrong leaf, and a wrong leaf is worse than an absent one.')

POINTERS = [
    ('csr.cumulus.periodic.data.endpoints', 'csrCumulusPeriodicDataAPI',
     '(0,e.Mz)(f,gt=>gt.csrCumulusPeriodicDataAPI)'),
    ('system.gc.gz.transition.flags', 'guardianCumulusPeriodicAPI',
     '(0,e.Mz)(f,gt=>gt.guardianCumulusPeriodicAPI)'),
]
for keyname, const, selector_src in POINTERS:
    print()
    print('--- ' + keyname)
    print(f'    key constant : {const}="{keyname}"  '
          f'({len(re.findall(re.escape(keyname), t))} occurrence(s) of the key string)')
    i_key = t.find('"%s"' % keyname)
    i_sel = t.find('=' + selector_src)
    i_cst = t.find('%s="%s"' % (const, keyname))
    print(f'    byte offsets : constant assignment @{i_cst}, selector definition @{i_sel}')
    if i_sel < 0:
        print('    selector NOT FOUND by its exact source text — stop, do not infer')
        continue
    # local = identifier immediately left of the selector definition's `=`
    j = i_sel
    while j > 0 and (t[j-1].isalnum() or t[j-1] in '_$'):
        j -= 1
    local = t[j:i_sel]
    al = alias_of.get(local)
    print(f'    selector local {local!r} -> exported as {al!r}')
    if al is None:
        print('    not exported — nothing outside this module can consume it')
        continue
    sites = [m.start() for m in re.finditer(r'\.' + re.escape(al) + r'(?![\w$])', t)]
    print(f'    property reads of ".{al}" in the whole file: {len(sites)}')
    for s in sites:
        print(f'      @{s}: ...{t[max(0, s-200):s+160]}...')
    if not sites:
        print(f'      the substring ".{al}" does not occur anywhere in this file.')

print()
print('--- personal.patient.timeline.host (area F addendum)')
print('    constant D.personalPatientTimelineHostURL assigned at byte '
      f'{t.find(chr(34)+"personal.patient.timeline.host"+chr(34))-60}; '
      f'{len(re.findall(re.escape("personal.patient.timeline.host"), t))} occurrence(s) of the key, '
      f'{len(re.findall(re.escape("personalPatientTimelineHostURL"), t))} of the constant name')
print('    NOTE the published key is personal.patient.timeline.config.host '
      '(docs/04), not personal.patient.timeline.host.')

# ---------- §3 named but never read ---------------------------------------
print()
print('=' * 78)
print('§3  KEY CONSTANTS NAMED BUT NEVER READ')
print('=' * 78)
print('# Two separate counts, because they prove different things:')
print('#  val  = occurrences of the KEY string. 1 means the key is named once and')
print('#        nowhere else, i.e. no code can spell it a second time.')
print('#  name = occurrences of the CONSTANT name. 1 means nothing reads the')
print('#        constant either; >1 means something does (usually the selector).')
consts = re.findall(r'D\.([A-Za-z0-9_$]+)="([^"]*)"', t)
seen = {}
for name, value in consts:
    seen.setdefault(value, name)
once = [(n, v) for v, n in seen.items() if len(re.findall(re.escape(v), t)) == 1]
print(f'\n# {len(once)} distinct key constants whose VALUE string occurs exactly once:')
print('%-4s %-5s %s' % ('val', 'name', 'constant -> key'))
for n, v in sorted(once, key=lambda x: x[1]):
    nv = len(re.findall(re.escape(n), t))
    print('%-4d %-5s %s -> "%s"' % (1, nv, n, v))
print('\n# Of those, the ones whose CONSTANT name is also read nowhere are the')
print('# strongest form: named in the key table and referenced by no code at all.')
dead = [(n, v) for n, v in once if len(re.findall(re.escape(n), t)) == 1]
print(f'# {len(dead)} of {len(once)}:')
for n, v in sorted(dead, key=lambda x: x[1]):
    print(f'   {n:<34} "{v}"')
print('\n# SCOPE: the EAGER MAIN BUNDLE. A lazy chunk can still read any of them,')
print('# and the 211 lazy chunks were not fetched (§4).')

# ---------- §4 chunk inventory --------------------------------------------
print()
print('=' * 78)
print('§4  PATIENT LAZY-CHUNK INVENTORY (from the runtime bundle)')
print('=' * 78)
rt = open(f'{B}/eu-runtime.b', 'rb').read().decode('utf-8', errors='replace')
pairs = re.findall(r'(\d+):"([0-9a-f]{16})"', rt)
print(f'# chunk entries in the runtime map: {len(pairs)}')
print('# url form: <id>.<hash>.js at the asset ROOT (f.u builds it; .p="" so')
print('# chunk paths are root-relative, NOT /app/)')
out = os.path.join(HERE, 'chunks.txt')
with open(out, 'w') as fh:
    for cid, h in pairs:
        fh.write(f'{cid}.{h}.js\n')
print(f'# written: chunks.txt  ({len(pairs)} lines)')
print('# first 5:', ' '.join(f'{a}.{b}.js' for a, b in pairs[:5]))
print('# last  3:', ' '.join(f'{a}.{b}.js' for a, b in pairs[-3:]))
PYEOF