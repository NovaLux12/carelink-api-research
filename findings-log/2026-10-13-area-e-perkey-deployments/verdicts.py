#!/usr/bin/env python3
"""Area E verdict pass — offline, zero requests.

Reads the transient body dir (argv[1]) + results.jsonl (argv[2]) + the committed
69-name candidate list (argv[3]) and emits, per host, per key:

    ABSENT-404 | NULL-404 | DEDICATED-ROUTE-404 | VALUED-match | VALUED-quirk |
    VALUED-mismatch | VALUED-NOT-IN-BULK | OTHER-<code>, plus SUBKEY-<code>
    for the four captcha flat-name subkeys, which are not bulk key names and
    so get their own verdict prefix.

Every comparison is made against the SAME host's own bulk subtree — never
string-compared against another deployment's envelope. Normalisation applied is
recorded per row in the `norm` column:

    exact          json.loads(envelope.value) deep-equals the bulk subtree
    sb             the value string parsed to "true"/"false" and coerced to a
                   bool before comparing (the per-key string-boolean trap)
    strip1bracket  json.loads failed; exactly one trailing ']' stripped and
                   retried (area W section 4, the reporting-countries quirk)

Type discipline (AGENTS.md section 6 item 3): the bulk lookup is asserted to
RESOLVE (key present) before any comparison, and values are compared through
canonical JSON so a bool can never equal an int. No value is printed anywhere —
only types, null-ness, lengths and digests.
"""

import json
import os
import sys

BODYDIR, RESULTS, KEYS = sys.argv[1], sys.argv[2], sys.argv[3]
OUT_TSV = os.path.join(os.path.dirname(os.path.abspath(RESULTS)), 'verdicts.tsv')
OUT_KEYSET = os.path.join(os.path.dirname(os.path.abspath(RESULTS)), 'keyset.tsv')

# Recorded 2026-10-08 (probe-2026-10-08) and re-confirmed by area W on EU: these
# two bulk keys have NO per-key form and are served at dedicated routes instead.
DEDICATED = {'captcha': '/patient/configuration/recaptcha/key',
             'default.country': '/patient/configuration/defaultCountry'}


def canon(v):
    """Canonical JSON so True != 1 and dict key order cannot decide a match."""
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


def parse_value(s):
    """Defensive unwrap->parse. Returns an ORDERED list of (norm, value)
    candidate readings of the envelope's value string, most-specific first.

    The per-key envelope is `String.valueOf(configValue)` (docs/04), so there
    are exactly three defensible readings and the pass tries all three rather
    than guessing one:

      exact         json.loads(s), with "true"/"false" coerced to a bool when
                    that is what it parsed to (the string-boolean trap)
      strip1bracket json.loads failed AND s ends with ']' -> drop EXACTLY one
                    trailing ']' and retry (area W section 4)
      rawstr        both of the above failed -> s is a bare string value (a
                    URL, a regex) that was never JSON, so read it literally
    """
    cands = []
    try:
        v = json.loads(s)
        if isinstance(v, str) and v in ('true', 'false'):
            v = (v == 'true')
            cands.append(('sb', v))
        else:
            cands.append(('exact', v))
    except Exception:
        if s.endswith(']'):
            try:
                cands.append(('strip1bracket', json.loads(s[:-1])))
            except Exception:
                pass
        cands.append(('rawstr', s))
    return cands


rows = [json.loads(l) for l in open(RESULTS, encoding='utf-8') if l.strip()]
misses = []
by_host = {}
for r in rows:
    by_host.setdefault(r['host'], []).append(r)

keys = [k for k in open(KEYS, encoding='utf-8').read().split('\n') if k]
assert len(keys) == 69, f'candidate list is not 69 names: {len(keys)}'

report = open(OUT_TSV, 'w', encoding='utf-8')
report.write('host\tkey\tseq\tcode\tbytes\tcontent_type\tbulk_resolved\tbulk_type\t'
             'bulk_is_null\tbulk_len\tverdict\tnorm\n')

ks_rows = []
summary = {}

for host, hrows in by_host.items():
    bulk_row = next(r for r in hrows if r['tag'] == '003-bulk-public')
    with open(os.path.join(BODYDIR, str(bulk_row['seq']), 'b'), encoding='utf-8') as fh:
        bulk = json.load(fh)
    bulk_keys = sorted(bulk)
    nulls = sorted(k for k in bulk_keys if bulk[k] is None)
    extra = [k for k in bulk_keys if k not in keys]
    missing = [k for k in keys if k not in bulk_keys]
    ks_rows.append((host, len(bulk_keys), bulk_row['bytes'], bulk_row['sha256'][:12],
                    ','.join(nulls), ';'.join(extra) or '-', ';'.join(missing) or '-'))
    summary[host] = dict(bulk=bulk, n=len(bulk_keys), nulls=nulls, extra=extra,
                         missing=missing)

    for k in keys:
        row = next((r for r in hrows if r['tag'].endswith(f'-{k}')), None)
        if row is None:
            raise SystemExit(f'no ledger row for {host} {k}')
        bpath = os.path.join(BODYDIR, str(row['seq']), 'b')
        resolved = 'yes' if k in bulk else 'NO'
        btype = type(bulk.get(k)).__name__ if k in bulk else '-'
        bnull = 'null' if k in bulk and bulk[k] is None else '-'
        blen = ''
        if k in bulk and bulk[k] is not None and hasattr(bulk[k], '__len__'):
            blen = len(bulk[k])
        with open(bpath, encoding='utf-8') as fh:
            raw = fh.read()
        if row['code'] == 404:
            if k in bulk and bulk[k] is None:
                verdict = 'NULL-404'
            elif k in DEDICATED:
                verdict = 'DEDICATED-ROUTE-404'
            else:
                verdict = 'ABSENT-404'
            norm = '-'
        elif row['code'] == 200:
            if k not in bulk:
                verdict, norm = 'VALUED-NOT-IN-BULK', '-'
            else:
                env = json.loads(raw)
                cands = parse_value(env['value'])
                hit = next(((n, v) for n, v in cands if canon(v) == canon(bulk[k])), None)
                if hit:
                    verdict, norm = 'VALUED-match', hit[0]
                elif any(n == 'strip1bracket' for n, _ in cands):
                    verdict, norm = 'VALUED-quirk', 'strip1bracket'
                else:
                    verdict, norm = 'VALUED-mismatch', '|'.join(n for n, _ in cands)
                    misses.append(f'{host}\t{k}\tseq={row["seq"]}\t'
                                  f'bulk={type(bulk[k]).__name__}/{len(bulk[k]) if hasattr(bulk[k], "__len__") else "-"}'
                                  f'\treadings={[(n, type(v).__name__) for n, v in cands]}')
        else:
            verdict, norm = f'OTHER-{row["code"]}', '-'
        report.write(f'{host}\t{k}\t{row["seq"]}\t{row["code"]}\t{row["bytes"]}\t'
                     f'{row["content_type"]}\t{resolved}\t{btype}\t{bnull}\t{blen}\t'
                     f'{verdict}\t{norm}\n')

    # the four captcha flat-name subkeys
    for s in ('enabled', 'key', 'type', 'testKey'):
        r = [x for x in hrows if x['tag'].endswith(f'captcha.{s}')]
        if not r:
            continue
        r = r[0]
        report.write(f'{host}\tcaptcha.{s}\t{r["seq"]}\t{r["code"]}\t{r["bytes"]}\t'
                     f'{r["content_type"]}\t-\t-\t-\t-\tSUBKEY-{r["code"]}\t-\n')
report.close()

with open(OUT_KEYSET, 'w', encoding='utf-8') as fh:
    fh.write('host\ttop_level_keys\tbulk_bytes\tbulk_sha256_12\tnull_valued_keys'
             '\tkeys_not_in_eu_69\tkeys_missing_from_this_bulk\n')
    for host, n, nb, sha, nulls, extra, missing in ks_rows:
        fh.write(f'{host}\t{n}\t{nb}\t{sha}\t{nulls}\t{extra}\t{missing}\n')

# ---- cross-deployment, offline, zero requests -------------------------------
print('=== bulk key set, per host ===')
for host, s in summary.items():
    print(f'  {host}: {s["n"]} top-level keys; {len(s["nulls"])} null-valued; '
          f'{len(s["extra"])} outside the EU 69; {len(s["missing"])} of the EU 69 missing')
    print(f'    null-valued: {", ".join(s["nulls"])}')
    if s['extra']:
        print(f'    EXTRA: {s["extra"]}')
    if s['missing']:
        print(f'    MISSING: {s["missing"]}')

hosts = list(summary)
if len(hosts) == 2:
    a, b = summary[hosts[0]], summary[hosts[1]]
    sa, sb = set(a['nulls']), set(b['nulls'])
    print('=== null set differs between the two hosts ===')
    print(f'  only {hosts[0]}: {sorted(sa - sb)}')
    print(f'  only {hosts[1]}: {sorted(sb - sa)}')
    print(f'  shared: {len(sa & sb)}')

print('=== verdict tallies ===')
tally = {}
for line in open(OUT_TSV, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) < 11 or p[0] == 'host':
        continue
    tally.setdefault(p[0], {})
    tally[p[0]][p[10]] = tally[p[0]].get(p[10], 0) + 1
for host, t in tally.items():
    print(f'  {host}: {t}')

print('=== cross-deployment verdict divergence ===')
grid = {}
for line in open(OUT_TSV, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) < 11 or p[0] == 'host':
        continue
    grid.setdefault(p[1], {})[p[0]] = p[10]
div = {k: v for k, v in grid.items() if len(set(v.values())) > 1}
print(f'  keys with differing verdicts across the two hosts: {len(div)}')
for k, v in sorted(div.items()):
    print(f'    {k}: {v}')
print(f'wrote {OUT_TSV} and {OUT_KEYSET}')
print('=== values that matched no reading (types only, no values printed) ===')
if not misses:
    print('  none')
for m in misses:
    print(f'  {m}')