#!/bin/bash
# Area G offline extraction — re-derives the per-build device tables from re-fetched bodies.
# Zero requests. Bodies live in $TMPBODIES (see probe.sh); they are never committed (area A precedent).
# Usage: TMPBODIES=/path/to/bodies bash findings-log/2026-10-13-area-g-device-tables/extract.sh
set -u
: "${TMPBODIES:?set TMPBODIES to the directory holding hp-main.b and sup-main.b}"
B=$TMPBODIES
python3 - "$B" <<'EOF'
import re, sys, hashlib
B = sys.argv[1]
def load(tag):
    return open(f'{B}/{tag}.b', 'rb').read().decode('utf-8', errors='replace')
for tag in ['hp-main', 'sup-main']:
    t = load(tag)
    print(f'===== {tag} ({len(t.encode())} B) =====')
    # Case-sensitivity controls (docs/09 section 5 false-hit class): every hit needs offset + context
    for tok in ['medicalDeviceFamily', 'deviceFamily', 'sourceMappingURL', 'GUARDIAN', 'SIMPLERA', '"BLE"', 'NGP']:
        offs = [m.start() for m in re.finditer(re.escape(tok), t)]
        print(f'{tok}: {len(offs)} hit(s) at {offs[:6]}')
    print('--- device-table window (last 68462 occurrence, 90KB) ---')
    idxs = [m.start() for m in re.finditer('68462', t)]
    seg = t[idxs[-1]:idxs[-1] + 90000]
    codes = sorted(set(re.findall(r'MMT-?[0-9]{2,5}[A-Za-z0-9]*', seg)))
    sku = sorted(set(re.findall(r'SKU-[0-9A-Za-z-]+', seg)))
    print(f'MMT n={len(codes)}: {" ".join(codes)}')
    print(f'SKU n={len(sku)}: {" ".join(sku)}')
    # quoted name-pairs + unquoted bare aliases
    pairs = sorted(set(re.findall(r'"(MMT-?[0-9A-Za-z]+)":\{name:"(.*?)",shortName:"(.*?)"', t)))
    uq = sorted(set(re.findall(r'[,{](MMT5100|MMT5101):\{name:"(.*?)",shortName:"(.*?)"', t)))
    print(f'quoted name-pairs n={len(pairs)}, unquoted bare-alias pairs n={len(uq)}: {uq}')
    # module 90991 sensor-branch array
    for m in re.finditer(r'const S=\["MMT-8600","MMT-8601"\]', t):
        print(f'90991 S-array at byte {m.start()}')
    # spot checks against patient-map rows on disk (PUBLIC-CONFIG-FINDINGS.md)
    whole = set(re.findall(r'MMT-?[0-9]{2,5}[A-Za-z0-9]*', t))
    print(f'whole-file distinct MMT n={len(whole)}')
    for c in ['MMT-8021', 'MMT-1909', 'MMT-8602', 'MMT-9015', 'MMT-8162XCF', 'MMT-1886XCY', 'MMT-5100JC1']:
        print(f'  {c}: {"present" if c in whole else "absent"}')
EOF
