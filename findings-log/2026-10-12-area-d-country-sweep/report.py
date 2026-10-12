#!/usr/bin/env python3
"""report.py — render the sweep into the artefacts FINDINGS.md cites.

Issues ZERO requests. Reads bodies/ + run.log, runs the reader in-process, and
writes:

  verdicts.jsonl        one reader record per country (the raw verdict stream)
  matrix.tsv            country x 35-key state matrix: ABSENT / NULL / VALUED.
                        This is the "the sweep is complete" artefact — every
                        country the vendor config enumerates, every documented
                        key, three states. It is deliberately a STATE matrix,
                        not a value-difference table: cross-country differences
                        are area W's subject, not this one's.
  contradictions.tsv    the enumeration: country, tier, rule, both values.
  summary.txt           the counts FINDINGS.md quotes.
"""

import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import reader  # noqa: E402


def main():
    bodies = os.path.join(DIR, 'bodies')
    order = []
    with open(os.path.join(DIR, 'run.log'), encoding='utf-8') as fh:
        for line in fh:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.rstrip('\n').split('\t')
            if len(parts) >= 2:
                order.append(parts[1])

    recs = []
    for cc in order:
        p = os.path.join(bodies, f'cc-{cc}.json')
        if os.path.exists(p):
            recs.append(reader.analyse(cc, p))

    with open(os.path.join(DIR, 'verdicts.jsonl'), 'w', encoding='utf-8') as fh:
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True) + '\n')

    keys = reader.REF
    with open(os.path.join(DIR, 'matrix.tsv'), 'w', encoding='utf-8') as fh:
        fh.write('cc\t' + '\t'.join(keys) + '\tkey_count\n')
        for r in recs:
            if r.get('parse') != 'OK':
                fh.write(f"{r['cc']}\tPARSE-FAIL\t{r.get('parse')}\n")
                continue
            row = [r['key_states'][k] for k in keys]
            fh.write(f"{r['cc']}\t" + '\t'.join(row) + f"\t{r['key_count']}\n")

    with open(os.path.join(DIR, 'contradictions.tsv'), 'w', encoding='utf-8') as fh:
        fh.write('cc\ttier\tclass\trule\tkeys\tleft\tright\n')
        for r in recs:
            for h in r.get('contradictions', []):
                fh.write('\t'.join([
                    r['cc'], str(h.get('tier', '')), h['class'], h['rule'],
                    '|'.join(h['keys']), str(h['left']), str(h['right'])]) + '\n')
            for h in r.get('flags', []):
                fh.write('\t'.join([
                    r['cc'], '-', h['class'], h['rule'], '|'.join(h['keys']),
                    str(h['left']), str(h['right'])]) + '\n')

    ok = [r for r in recs if r.get('parse') == 'OK']
    notok = [r for r in recs if r.get('parse') != 'OK']
    # Each list collects the HITS, not the records. An earlier version of this
    # line bound `r` in the flags comprehension, so the list held records and
    # the Counter below raised KeyError: 'rule'. Caught by running it.
    t1 = [h for r in ok for h in r['contradictions'] if h.get('tier') == 1]
    t2 = [h for r in ok for h in r['contradictions'] if h.get('tier') == 2]
    flags = [h for r in ok for h in r['flags']]
    lines = [
        f'countries requested        {len(recs)}',
        f'parsed as a JSON object   {len(ok)}',
        f'not a JSON object         {len(notok)}  '
        + (','.join(r['cc'] for r in notok) or '(none)'),
        f'tier-1 contradictions     {len(t1)}',
        f'tier-2 disagreements      {len(t2)}',
        f'flag-inferred findings    {len(flags)}',
        '',
        'tier-1 by rule:',
    ]
    from collections import Counter
    for rule, n in sorted(Counter(h['rule'] for h in t1).items(), key=lambda kv: -kv[1]):
        lines.append(f'  {n:>4}  {rule}')
    lines.append('')
    lines.append('tier-2 by rule:')
    for rule, n in sorted(Counter(h['rule'] for h in t2).items(), key=lambda kv: -kv[1]):
        lines.append(f'  {n:>4}  {rule}')
    lines.append('')
    lines.append('flags by rule:')
    for rule, n in sorted(Counter(h['rule'] for h in flags).items(), key=lambda kv: -kv[1]):
        lines.append(f'  {n:>4}  {rule}')
    lines.append('')
    lines.append('key-count distribution:')
    for n, c in sorted(Counter(r['key_count'] for r in ok).items()):
        lines.append(f'  {n} keys: {c} countries')
    lines.append('')
    lines.append('keys ABSENT in at least one country (never null):')
    for k in keys:
        states = {r['key_states'][k] for r in ok}
        na = sum(1 for r in ok if r['key_states'][k] == 'ABSENT')
        nn = sum(1 for r in ok if r['key_states'][k] == 'NULL')
        nv = sum(1 for r in ok if r['key_states'][k] == 'VALUED')
        if na or nn:
            lines.append(f'  {k:<28} ABSENT {na:>4}  NULL {nn:>4}  VALUED {nv:>4}')
    lines.append('')
    lines.append('keys not in the reference vocabulary:')
    extra = sorted({k for r in ok for k in r['keys_not_in_reference']})
    lines.append('  ' + (', '.join(extra) if extra else '(none)'))
    lines.append('')
    lines.append('report-name vocabulary deltas:')
    deltas = sorted({r['cc'] for r in ok if r['report_vocabulary_delta']})
    lines.append('  ' + (', '.join(deltas) if deltas else '(none)'))

    out = '\n'.join(lines)
    with open(os.path.join(DIR, 'summary.txt'), 'w', encoding='utf-8') as fh:
        fh.write(out + '\n')
    print(out)
    return 0


if __name__ == '__main__':
    sys.exit(main())