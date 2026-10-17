#!/usr/bin/env python3
"""derive.py — derive the window decision and the queue IN CODE, then re-print it.

    python3 derive.py --write      # writes crawl-window-out.txt + q-01-outwindow.tsv
    python3 derive.py              # re-derives and re-prints every table in FINDINGS.md

Zero requests. Every figure this pass publishes is computed here or in budget.py;
nothing is typed by hand.

THE RULE, AND WHY IT IS WRITTEN THIS WAY
----------------------------------------
A crawl is IN the window 2013-05-17 -> 2022-05-13 when

    from <= 2022-05-13  AND  to >= 2013-05-17

with BOTH sides compared in the SAME string shape. Area L's first pass sliced
`from[:8]` -> `'2013-05-1'` and compared it against a **dashless** `'20220513'`.
`-` is 0x2D, `0` is 0x30 and `2` is 0x32, so the separator sorts below both
digits: every 2013 crawl dropped out of the window AND every post-window 2022
crawl entered it. 84 - 2 + 5 = 87 where the answer is 84 (AGENTS.md section 6
item 3 -- a comparison over a lookup that silently returns the wrong value).

Two things are therefore non-negotiable here, and this file does both:

  1. THE RESOLVED TYPE IS ASSERTED BEFORE ANY COMPARISON. `collinfo.json` is
     parsed and every row's `id`/`from`/`to` is asserted to be a `str` before a
     single `<` or `>=` runs. A row that is not a str aborts the derivation; it
     does not compare and it does not get a verdict.
  2. THE BOUND IS BUILT FROM THE SAME SHAPE AS THE DATA. The comparison runs on
     `YYYY-MM-DD` (both sides), and the full ISO-8601 form is computed as well;
     `--write` refuses to write a queue if the two disagree, which is the check
     that would have caught area L's error.

The buggy variant is printed too, on purpose: it is the negative control, and a
derivation with no known-failing variant is a derivation whose rule has never been
tested.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INVENTORY = os.path.join(HERE, 'crawl-window-out.txt')
QUEUE = os.path.join(HERE, 'q-01-outwindow.tsv')

# The window, from ARCHIVE-URLS.md section 3 as recorded in docs/09/docs/10 and
# carried by area L. Both dates are DAY-precision and inclusive at both ends.
WIN_LO = '2013-05-17'
WIN_HI = '2022-05-13'

# The control host. ONE host, named before the sweep rather than alternated per
# crawl: pool-L measured `commoncrawl.org` first-attempt-failing on 4 of 7 crawls
# while `google.com` covered all four (findings-log/2026-10-14-pool-l-crawlcontrol).
# A single control host is one variable; area L's per-crawl alternation was
# described as "alternating" and was not (its round-1 correction C8).
CONTROL_HOST = 'google.com'
# The probe: area L's two-cell shape, unchanged. `matchType=domain`, `output=json`,
# and NO `limit` -- `limit` truncates from the tail (docs/10 section 1).
PROBE_HOST = 'minimed.eu'
ABSENT_SIBLING = 'zz-sl2-absent-20261017.minimed.eu'

# Out-of-window crawls some earlier pass in this repo already issued a query
# against. Recorded so the census says "unread" about a *crawl*, not about the
# repo, and every one is re-read by this pass anyway.
PRIOR_TOUCHED = {
    'CC-MAIN-2022-21': 'findings-log/2026-10-13-area-l-ipro-hcp seqs 18/21/24/26',
    'CC-MAIN-2022-27': 'findings-log/2026-10-14-pool-l-ipro-hcp-census seqs 34-39',
    'CC-MAIN-2022-40': 'findings-log/2026-10-13-area-m-commoncrawl-cdx + 2026-10-14-lane-s6-public-index',
    'CC-MAIN-2024-42': 'findings-log/2026-10-13-area-m-commoncrawl-cdx + 2026-10-14-lane-s6-public-index',
    'CC-MAIN-2025-30': 'findings-log/2026-10-13-area-m-commoncrawl-cdx + 2026-10-14-lane-s6-public-index',
    'CC-MAIN-2026-39': 'findings-log/2026-10-13-area-l-ipro-hcp + area-m + 2026-10-14-lane-s6-public-index',
}


def load_collinfo(path):
    """Parse /collinfo.json. ASSERT every field's type before returning."""
    with open(path, 'rb') as fh:
        raw = fh.read()
    crawls = json.loads(raw.decode('utf-8', 'replace'))
    if not isinstance(crawls, list):
        raise SystemExit('derive.py: collinfo.json did not resolve to a list (%s)'
                         % type(crawls).__name__)
    for c in crawls:
        for k in ('id', 'from', 'to'):
            if not isinstance(c.get(k), str):
                raise SystemExit('derive.py: crawl row %r field %r is %s, not str — '
                                 'refusing to compare an unasserted type'
                                 % (c.get('id'), k, type(c.get(k)).__name__))
        if not re.match(r'^CC-MAIN-[0-9]{4}(?:-[0-9]+)?$', c['id']):
            raise SystemExit('derive.py: id %r is not the crawl-id shape the queue '
                             'paths assume' % c['id'])
        for k in ('from', 'to'):
            if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', c[k]):
                raise SystemExit('derive.py: crawl %s field %s = %r is not the '
                                 'ISO-8601 shape the comparison assumes'
                                 % (c['id'], k, c[k]))
    return crawls, len(raw)


def in_window(c, n):
    """n = slice width. 10 -> YYYY-MM-DD; 19 -> full ISO-8601. Same shape BOTH sides."""
    return c['from'][:n] <= WIN_HI[:n] and c['to'][:n] >= WIN_LO[:n]


def in_window_BUGGY(c):
    """The variant that printed 87. Reproduced as a NEGATIVE CONTROL, never used."""
    return c['from'][:8] <= '20220513' and c['to'][:8] >= '20130517'


def side(c):
    """after / before / in -- which side of the window the crawl's whole span sits on."""
    if in_window(c, 10):
        return 'in'
    return 'after' if c['from'][:10] > WIN_HI else 'before'


def build(crawls):
    rows, seen = [], set()
    for c in sorted(crawls, key=lambda x: x['id']):
        if c['id'] in seen:
            raise SystemExit('derive.py: duplicate crawl id %s in the inventory'
                             % c['id'])
        seen.add(c['id'])
        s = side(c)
        rows.append({'id': c['id'], 'from': c['from'], 'to': c['to'], 'side': s,
                     'prior': PRIOR_TOUCHED.get(c['id'], '')})
    return rows


def census():
    """The per-crawl classification table, derived from the committed ledger alone.

    THE COUNTING RULE (area L's, unchanged):
      RECORD         the probe answered 200
      ABSENCE        the probe answered 404 AND some row for that crawl answered 200
      INDETERMINATE  a 404 with no 200 on any row for that crawl -- carries NO
                     absence weight in either direction
      FAILURE        the probe reached neither 200 nor 404 (502/504/503/400/000)

    And this pass's added distinction, which is the whole point of it:

      UNSERVABLE-CANDIDATE
                     a crawl where NO row of any kind answered 200 within the full
                     retry budget. The cell is INDETERMINATE, never an absence, and
                     the crawl is named as the one S-L1's `cluster.idx` check exists
                     to settle. This pass does NOT settle it: S-L1 is not this
                     lane's claim and is not closed here.
    """
    lp = os.path.join(HERE, 'results.jsonl')
    if not os.path.exists(lp):
        print('census: no ledger yet')
        return
    rows = [json.loads(l) for l in open(lp) if l.strip()]
    by = {}
    for r in rows:
        if r.get('crawl'):
            by.setdefault(r['crawl'], []).append(r)
    print('THE OUT-OF-WINDOW CRAWLS -- every cell classified from results.jsonl')
    print()
    print('%-20s %-36s %-24s %-8s %-6s %s'
          % ('crawl', 'control (seq-status-recs)', 'probe (seq-status-recs)',
             'members', 'floor', 'verdict'))
    tally = {}
    for cid in sorted(by):
        rs = sorted(by[cid], key=lambda r: r['seq'])
        ctl = [r for r in rs if r['role'] == 'control']
        prb = [r for r in rs if r['role'] == 'probe']
        any200 = any(r['http_status'] == '200' for r in rs)
        last_p = prb[-1] if prb else None
        desc_c = ' · '.join('%s·%s·%s' % (r['seq'], r['http_status'], r['records'])
                            for r in ctl) or '-'
        desc_p = ' · '.join('%s·%s·%s' % (r['seq'], r['http_status'], r['records'])
                            for r in prb) or '-'
        mem = sum(r.get('ipro_count', 0) for r in prb if r['http_status'] == '200')
        floor = any(r.get('truncation_boundary') for r in prb if r['http_status'] == '200')
        st = last_p['http_status'] if last_p else 'none'
        if last_p and st == '200':
            v = 'RECORD'
        elif last_p and st == '404' and any200:
            v = 'ABSENCE'
        elif last_p and st == '404':
            v = 'INDETERMINATE (404, no 200 on this crawl)'
        elif not any200:
            v = 'INDETERMINATE / UNSERVABLE-CANDIDATE (no row answered 200)'
        else:
            v = 'FAILURE (probe %s)' % st
        tally[v] = tally.get(v, 0) + 1
        print('%-20s %-36s %-24s %-8s %-6s %s'
              % (cid, desc_c, desc_p, mem, 'FLOOR' if floor else '-', v))
    print()
    for v, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print('%-48s %d' % (v, n))
    print('%-48s %d' % ('crawls carrying at least one row', len(by)))
    print()
    print('MEMBERS -- every /ipro/hcp/* record this pass observed, with its crawl.')
    found = [(r['crawl'], r['seq'], m) for r in rows
             for m in r.get('ipro_hcp', []) if r['http_status'] == '200']
    if not found:
        print('  none.')
    for cid, seq, m in sorted(found):
        print('  %-20s seq %-4s %s' % (cid, seq, m))
    print()
    nsess = sum(r.get('jsessionid_redacted', 0) for r in rows)
    print('jsessionid_ values found, redacted in code: %d, across %d row(s)'
          % (nsess, sum(1 for r in rows if r.get('jsessionid_redacted'))))
    fails = [r for r in rows if r.get('is_failure')]
    print('FAILURES (never read as absences): %d of %d rows' % (len(fails), len(rows)))
    if fails:
        shp = {}
        for r in fails:
            shp[r['http_status']] = shp.get(r['http_status'], 0) + 1
        print('  shapes: %s' % '  '.join('%s x%d' % (k, v) for k, v in sorted(shp.items())))
        print('  of those, retries (attempt > 0): %d' % sum(1 for r in fails if r['attempt']))
    print()
    print('TRUNCATION DETECTOR (lane S6): a 200 response whose byte count is an exact')
    print('multiple of 1024 was cut short, so that cell record count is a FLOOR.')
    for r in rows:
        if r['http_status'] == '200' and r.get('truncation_boundary'):
            print('  seq %s  %s  %d B  %d records  <- FLOOR'
                  % (r['seq'], r['crawl'], r['body_bytes'], r['records']))


def main():
    write = '--write' in sys.argv
    if '--census' in sys.argv:
        return census()
    if '--budget' in sys.argv:
        os.execvp('python3', ['python3', os.path.join(HERE, 'budget.py'),
                              '--population', 's-l2-out'])
    body = None
    if os.environ.get('L_BODIES'):
        p = os.path.join(os.environ['L_BODIES'], '1-inventory.body')
        if os.path.exists(p):
            body = p
    if body is None:
        print('derive.py: no collinfo body available; re-deriving from the committed '
              'inventory %s' % os.path.basename(INVENTORY))
        rows = []
        if os.path.exists(INVENTORY):
            for line in open(INVENTORY):
                line = line.rstrip('\n')
                if not line or line.startswith('#') or line.startswith('published'):
                    continue
                f = line.split('\t')
                if len(f) < 4:
                    continue
                rows.append({'id': f[0], 'from': f[1], 'to': f[2],
                             'side': f[3], 'prior': f[4] if len(f) > 4 else ''})
    else:
        crawls, nbytes = load_collinfo(body)
        rows = build(crawls)
        n_day = sum(1 for c in crawls if in_window(c, 10))
        n_full = sum(1 for c in crawls if in_window(c, 19))
        n_bug = sum(1 for c in crawls if in_window_BUGGY(c))
        print('collinfo.json: %d bytes, %d indexes, every id/from/to asserted str '
              'and ISO-8601' % (nbytes, len(crawls)))
        print()
        print('THE COMPARISON, THREE WAYS (all three printed; only the first is used):')
        print('  YYYY-MM-DD on BOTH sides            -> %3d in window   <- THE RULE' % n_day)
        print('  full ISO-8601 on BOTH sides          -> %3d in window   <- agrees' % n_full)
        print('  from[:8]/to[:8] vs a DASHLESS bound  -> %3d in window   <- THE BUG, '
              'negative control (drops 2 of 2013, wrongly adds 5 of 2022)' % n_bug)
        if n_day != n_full:
            print('REFUSING TO WRITE: the two correct variants disagree (%d vs %d).'
                  % (n_day, n_full))
            return 1
        print()
        n_in = sum(1 for r in rows if r['side'] == 'in')
        n_after = sum(1 for r in rows if r['side'] == 'after')
        n_before = sum(1 for r in rows if r['side'] == 'before')
        print('  published indexes %d  =  in %d  +  after %d  +  before %d'
              % (len(rows), n_in, n_after, n_before))
        print('  OUT OF WINDOW %d  (this pass\'s population)' % (n_after + n_before))
        print('  of those, already touched by an earlier pass in this repo: %d  [%s]'
              % (sum(1 for r in rows if r['side'] != 'in' and r['prior']),
                 ', '.join(r['id'] for r in rows if r['side'] != 'in' and r['prior'])))
        print()
        if write:
            with open(INVENTORY, 'w') as f:
                f.write('# crawl-window-out.txt — every published Common Crawl index and this '
                        'pass\'s window decision.\n')
                f.write('# Source: GET /collinfo.json, seq 1 of results.jsonl (200, 35226 B, '
                        'sha256 %s). Written by derive.py --write; the body stays outside the '
                        'tree by policy (AGENTS.md section 7), so this file is what makes the '
                        'counts re-derivable from a clean clone.\n' %
                        __import__('hashlib').sha256(open(body, 'rb').read()).hexdigest())
                f.write('#\n# COUNTING RULE: from <= %s AND to >= %s, compared as the SAME '
                        'shape on both sides (YYYY-MM-DD; the full ISO-8601 form gives the '
                        'same answer and derive.py refuses to write if they disagree). '
                        'A DASHLESS bound is wrong here — derive.py prints that variant as a '
                        'negative control and it reports 87.\n' % (WIN_HI, WIN_LO))
                f.write('#\n# id\tfrom\tto\tin_window\tside\tprior_touch\tverdict\tn_members'
                        '\tcontrol_200\n')
                for r in rows:
                    f.write('%s\t%s\t%s\t%s\t%s\t%s\t\t\t\n'
                            % (r['id'], r['from'], r['to'],
                               'yes' if r['side'] == 'in' else 'no', r['side'], r['prior']))
                f.write('\npublished indexes\t%d\n' % len(rows))
                f.write('in window\t%d\n' % n_in)
                f.write('out of window\t%d\n' % (n_after + n_before))
                f.write('out, entirely after the window\t%d\n' % n_after)
                f.write('out, entirely before the window\t%d\n' % n_before)
            print('wrote %s' % os.path.basename(INVENTORY))

            # The queue: one line per out-of-window crawl, oldest first, each group
            # control-then-probe. The certainly-absent sibling brackets the sweep --
            # first crawl and last crawl -- so the absence oracle is established in
            # this pass and not inherited.
            out = sorted([r for r in rows if r['side'] != 'in'], key=lambda r: r['from'])
            # NO header line: probe.sh reads every line as a cell, and a header
            # becomes a request. (It refused to send this one -- see run.log.refused --
            # but the queue does not carry the hazard in the first place.)
            with open(QUEUE, 'w') as f:
                for i, r in enumerate(out):
                    cid = r['id']
                    base = '/%s-index' % cid
                    f.write('control\t%s\t%s?url=%s&output=json&matchType=domain&limit=5\t%s-control\n'
                            % (cid, base, CONTROL_HOST, cid))
                    f.write('probe\t%s\t%s?url=%s&output=json&matchType=domain\t%s-probe\n'
                            % (cid, base, PROBE_HOST, cid))
                    if i == 0 or i == len(out) - 1:
                        f.write('absent-control\t%s\t%s?url=%s&output=json&matchType=host'
                                '\t%s-absent\n' % (cid, base, ABSENT_SIBLING, cid))
            print('wrote %s — %d crawls, %d queued cells'
                  % (os.path.basename(QUEUE), len(out), 2 * len(out) + 2))
            print('  control host   %s (one named host, chosen before the sweep; '
                  'pool-L measured it covering all four crawls where commoncrawl.org '
                  'first-attempt-failed on 4 of 7)' % CONTROL_HOST)
            print('  probe          %s matchType=domain output=json, NO limit' % PROBE_HOST)
            print('  certainly-absent sibling on the first and the last crawl')
    return 0


if __name__ == '__main__':
    sys.exit(main())