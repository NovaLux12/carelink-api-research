#!/usr/bin/env bash
# Area AV offline extraction — re-derives module 68462's device table from the five
# re-fetched bodies. ZERO requests. Bodies live in the gitignored scratch dir and are
# NEVER committed (area A/G/V precedent); only the derived tables below are.
#
# Emits, into this directory:
#   instinct-table.tsv      every SKU-/Instinct/MMT-5420 named pair, per build, per host
#   census-7896x.tsv        the 17-code census (sku-prefixed pair form, SKU-string form,
#                           bare form) — offsets are reported by print-offsets below
#   build-table-summary.tsv one row per build host: digest, module window, pair counts
#
# Usage: bash extract.sh [scratch_dir]
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MAIN="$(cd "$HERE/../../../../.." && pwd)"
B="${1:-$MAIN/.loop/av-scratch}"

python3 - "$B" "$HERE" <<'EOF'
import re, sys, os, hashlib, csv

B, OUT = sys.argv[1], sys.argv[2]
TAGS  = ['a-hp-main', 'a-cmc-main', 'a-cme-main', 'a-sup-main', 'a-supc-main']
HOST  = {'a-hp-main': 'carelinkhp.minimed.eu',
         'a-cmc-main': 'carelink.medtronic.com',
         'a-cme-main': 'carelink.medtronic.eu',
         'a-sup-main': 'carelink-support.medtronic.eu',
         'a-supc-main': 'carelink-support.medtronic.com'}
BUILD = {'a-hp-main': 'A(pow)', 'a-cmc-main': 'A(pow)', 'a-cme-main': 'A(pow)',
         'a-sup-main': 'B(cua)', 'a-supc-main': 'B(cua)'}

CODES = ['78893', '78953', '78954', '78955', '78956', '78957', '78958', '78959',
         '78960', '78961', '78962', '78963', '78964', '78965', '78966', '78967',
         '78968']

inst_rows, census_rows, summary_rows, offset_lines = [], [], [], []

for tag in TAGS:
    p = f'{B}/{tag}.b'
    if not os.path.exists(p):
        print(f'{tag}: MISSING body — skipping (no claim made)', file=sys.stderr)
        continue
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8', errors='replace')
    sha = hashlib.sha256(raw).hexdigest()

    # Module 68462: webpack emits `68462:(ct,Z,r)=>{...}` as the module TABLE entry and
    # two `r(68462)` call sites. The table entry is the LAST occurrence, and it is the
    # only one followed by `:{name:` pairs. Assert that before reading it.
    ids = [m.start() for m in re.finditer('68462', t)]
    assert ids, f'{tag}: no module 68462'
    start = ids[-1]
    assert t[start:start+14] == '68462:(ct,Z,r)', \
        f'{tag}: last 68462 occurrence is not the module table entry: {t[start-1:start+30]!r}'
    m = re.search(r'\}\},\d+:\(ct,Z,r\)=>', t[start:])
    assert m, f'{tag}: could not find the end of module 68462'
    mod = t[start:start + m.start()]

    # Four sections in this table; assert all four so a section rename cannot hide codes.
    sect = [(mm.group(1), mm.start())
            for mm in re.finditer(r'[,{](PUMP|SENSOR|StandaloneCGM|InsulinDelivery):\{DEFAULT', mod)]
    assert [s for s, _ in sect] == ['PUMP', 'SENSOR', 'StandaloneCGM', 'InsulinDelivery'], \
        f'{tag}: unexpected section list {[s for s,_ in sect]}'

    pairs = []
    for i, (sec, pos) in enumerate(sect):
        end = sect[i+1][1] if i+1 < len(sect) else len(mod)
        for mm in re.finditer(r'(?:"([^"]+)"|([A-Za-z0-9_-]+)):\{name:"(.*?)",shortName:"(.*?)"',
                              mod[pos:end]):
            key = mm.group(1) or mm.group(2)
            pairs.append((sec, key, mm.group(3).replace('\\u2122', '\u2122')))

    n_sku  = sum(1 for s, k, _ in pairs if re.fullmatch(r'SKU-[0-9]{5}-01', k))
    n_inst = sum(1 for s, k, n in pairs if 'Instinct' in n)
    summary_rows.append([tag, HOST[tag], BUILD[tag], sha, len(raw), start, len(mod),
                         len(pairs), n_sku, n_inst])

    for sec, key, name in pairs:
        if 'SKU-' in key or 'Instinct' in name or key == 'MMT-5420':
            inst_rows.append([tag, HOST[tag], BUILD[tag], sha, len(raw), start, sec, key, name])

    for c in CODES:
        # Three forms, kept separate because two of them collide:
        #  1. the quoted named pair  "SKU-NNNNN-01":{name:   (what the table maps)
        #  2. the SKU- string anywhere   SKU-NNNNN-01       (a code, no name)
        #  3. a BARE NNNNN-01, i.e. not preceded by 'SKU-'  (the family map's other form)
        # A plain \bNNNNN\b count is NOT form 3: it hits inside `SKU-78960-01` and inside
        # zxcvbn password-list integers (1478963, 789654, 7896321). Both were produced by
        # the first version of this script and are the §7-bearing false-hit class.
        pair_hits = len(re.findall(r'"SKU-%s-01":\{name:' % c, t))
        sku_hits  = len(re.findall(r'SKU-%s-01' % c, t))
        bare_hits = len(re.findall(r'(?<!SKU-)(?<![0-9])%s-01' % c, t))
        loose_hits = len(re.findall(c, t))          # raw substring, zip-list noise included
        if '"SKU-%s-01"' % c in mod:
            near = 'table(module68462)'
        elif sku_hits or bare_hits:
            near = 'bundle-elsewhere'
        elif loose_hits:
            near = 'substring-only(zxcvbn)'
        else:
            near = 'absent-from-file'
        census_rows.append([tag, HOST[tag], BUILD[tag], sha[:16], c,
                            pair_hits, sku_hits, bare_hits, loose_hits, near])
        if pair_hits:
            off = start + mod.index('"SKU-%s-01"' % c)
            offset_lines.append(f'{tag}\tSKU-{c}-01\tbyte {off}')

with open(f'{OUT}/instinct-table.tsv', 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['tag', 'host', 'build', 'asset_sha256', 'asset_bytes',
                'module_start_byte', 'section', 'key', 'name'])
    w.writerows(inst_rows)

with open(f'{OUT}/census-7896x.tsv', 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['tag', 'host', 'build', 'asset_sha16', 'code',
                'named_pair_hits', 'sku_string_hits', 'bare_form_hits',
                'loose_substring_hits', 'where'])
    w.writerows(census_rows)

with open(f'{OUT}/build-table-summary.tsv', 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['tag', 'host', 'build', 'asset_sha256', 'asset_bytes',
                'module_start_byte', 'module_bytes', 'named_pairs',
                'sku_pairs', 'instinct_named_pairs'])
    w.writerows(summary_rows)

with open(f'{OUT}/sku-offsets.tsv', 'w') as f:
    f.write('tag\tkey\tbyte_offset\n' + '\n'.join(offset_lines) + '\n')

print(f'{len(inst_rows)} instinct/sku rows, {len(census_rows)} census rows, '
      f'{len(summary_rows)} build rows')
EOF
