#!/usr/bin/env python3
"""kib-detector.py — the WHOLE-KiB truncation detector, run over area L, and the
member-source `limit=` cell, both under stated counting rules.

    python3 kib-detector.py            # both cells, human-readable
    python3 kib-detector.py --json     # machine-readable

WHY THIS IS A SCRIPT AND NOT A TABLE IN FINDINGS.md. Round 3 of the verifier found
that the §7b byte table (193 / 0) had **no committed artefact behind it** — no
`.py` or `.sh` in this directory performed the byte arithmetic, so the number was
reproducible only by hand. `AGENTS.md` §6 item 7: a count whose rule is not
shipped is a typed number wearing a script's name. And round 3 also found the
companion cell ("67 of 69 member-source rows carry no limit=") cited a numerator
and a denominator from **two different counting rules**. So both cells are
computed here, from the reader's OWN predicates, and both print their rule.

RULE 1 — WHOLE-KiB TRUNCATION DETECTOR
    Verbatim from `docs/10` §1, where the rule was first published:
      "a record response whose body_bytes is an exact multiple of 1024 was cut
       short, and one whose byte count is not, ran to completion."
    It is a CORRELATION over the rows observed, never a proven mechanism
    (`account.py`'s own docstring says so). Reported as such.

RULE 2 — "SUCCESSFUL 200"
    A row counts when `read-area-l.py`'s own `status_of()` resolves it to the int
    200. That predicate is deliberately NOT a raw comparison, because every
    `http_status` in this population is a JSON **string** (all 380 rows) and
    `pool-s7-l7crawl` writes the opaque form `"200 (curl)"`. Three obvious rules
    give three answers:

        raw == 200                    ->   0   (misses every row; all are strings)
        raw == "200"  (exact equality)-> 183   (misses the 10 opaque s7 rows)
        status_of(row) == 200         -> 193   <- the rule used here

    The gap between the last two is exactly the 10 `"200 (curl)"` rows. All three
    are printed by this script so the distinction is visible rather than assumed.
    ⚠ `docs/10` §1's own warning applies: "Clean for this test is not the same as
    complete" — a truncation not aligned to 1024 is invisible to it.

RULE 3 — MEMBER-SOURCE ROW
    A row is a member-source row when the reader's own predicates agree on all
    three: `query_of(row) in DATA_TARGETS` (it is a DATA cell), `status_of(row) ==
    200`, and `members_of(row) is not None` (it carries a member field). Three
    cells are reported because they are genuinely different populations and
    round 3's "69/67" mixed two of them:
      A  every such row in the population
      B  one per crawl — the LAST such row per crawl, which is what `derive()`
         actually uses as the count
      C  B restricted to in-window crawls
    For each: how many carry a `limit=`, how many carry none, how many reached
    their own limit (records >= limit), and how many carried a limit WITHOUT
    reaching it. That last figure is the one round 3 caught: carrying a limit and
    reaching it are different predicates, and only the second means the tail may
    have been cut.

WHY NOT JUST USE account.py
    `findings-log/2026-10-14-lane-s6-public-index/account.py` is the prior art and
    is left untouched — it is another lane's file and out of this lane. It also
    **crashes** on a member of this population: `2026-10-13-area-l-ipro-hcp`
    seqs 1-4 carry a null `t_sent`, and `account.py:109` calls
    `strptime(None)` (`TypeError`). That is recorded as successor **S-L4e** rather
    than fixed here. Rule 1 below is that file's rule, reimplemented in six lines
    so this pass does not have to route its own census through a tool that
    cannot read its own population.

OFFLINE. Reads only `findings-log/**/results.jsonl`. Sends nothing.
"""
import argparse
import collections
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
READER = os.path.join(HERE, 'read-area-l.py')

_spec = importlib.util.spec_from_file_location('read_area_l', READER)
rl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rl)

LIMIT_RE = re.compile(r'[?&]limit=([^&]*)')


def limit_of(raw):
    """The row's own `limit=` value, or None. Taken from `path`, which every
    committed schema carries — the same field the reader uses to decide the cell."""
    m = LIMIT_RE.search(raw.get('path', '') or '')
    return int(m.group(1)) if m else None


def records_of(raw):
    """The row's record count. `records` in the 2026-10-13/14 passes,
    `record_count` in pool-s7. None when the row carries neither, and then the
    row cannot be said to have reached its limit either way — counted as such
    rather than assumed to be under it."""
    v = raw.get('records', raw.get('record_count'))
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def member_source_rows():
    """Every row satisfying RULE 3, as (ledger, raw, crawl, limit, records)."""
    out = []
    for p in rl.population(git=True):
        with open(os.path.join(rl.REPO, p)) as fh:
            for line in fh:
                if not line.strip():
                    continue
                raw = json.loads(line)
                if rl.query_of(raw) not in rl.DATA_TARGETS:
                    continue
                if rl.status_of(raw) != 200:
                    continue
                if rl.members_of(raw) is None:
                    continue
                out.append((p, raw, rl.crawl_of(raw), limit_of(raw), records_of(raw)))
    return out


def one_per_crawl(rows):
    """The LAST such row per crawl, in first-seen crawl order — which is what
    `derive()` uses, because a later pass's row is the addendum."""
    by = collections.OrderedDict()
    for x in rows:
        by.setdefault(x[2], []).append(x)
    return [v[-1] for v in by.values()]


def cells(rows):
    n = len(rows)
    with_limit = [x for x in rows if x[3] is not None]
    at_limit = [x for x in with_limit if x[4] is not None and x[4] >= x[3]]
    carried_not_reached = [x for x in with_limit if x not in at_limit]
    return {
        'n': n,
        'carrying_limit': len(with_limit),
        'carrying_no_limit': n - len(with_limit),
        'at_own_limit': len(at_limit),
        'carried_but_not_reached': len(carried_not_reached),
        'unknown_records': sum(1 for x in with_limit if x[4] is None),
    }


def kib():
    """RULE 1 + RULE 2 over the population."""
    per = collections.OrderedDict()
    total200 = lit_int = lit_str = candidates = 0
    vals = []
    for p in rl.population(git=True):
        n200 = ncand = 0
        for line in open(os.path.join(rl.REPO, p)):
            if not line.strip():
                continue
            raw = json.loads(line)
            st = raw.get('http_status')
            if st == 200 and isinstance(st, int) and not isinstance(st, bool):
                lit_int += 1
            if st == '200':
                lit_str += 1
            if rl.status_of(raw) != 200:
                continue
            n200 += 1
            bb = raw.get('body_bytes')
            if isinstance(bb, int) and not isinstance(bb, bool):
                vals.append(bb)
                if bb % 1024 == 0:
                    ncand += 1
        per[p] = (n200, ncand)
        total200 += n200
        candidates += ncand
    return per, total200, candidates, lit_int, lit_str, vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    per, total200, cand, lit_int, lit_str, vals = kib()
    rows = member_source_rows()
    A = cells(rows)
    B = cells(one_per_crawl(rows))
    win = {c for c, f in rl.read_census_file().items() if f['in_window'] == 'yes'}
    C = cells([x for x in one_per_crawl(rows) if x[2] in win])

    if a.json:
        print(json.dumps({
            'rule_1': 'body_bytes an exact multiple of 1024 == truncated (docs/10 §1)',
            'rule_2': "status_of(row) == 200, the reader's predicate, NOT raw == '200'",
            'successful_200': total200,
            'whole_kib_candidates': cand,
            'literal_int_200': lit_int,
            'literal_str_200_prefix': lit_str,
            'per_ledger': {os.path.basename(os.path.dirname(k)): v for k, v in per.items()},
            'rule_3_cells': {'A_every_row': A, 'B_one_per_crawl': B, 'C_in_window_one_per_crawl': C},
        }, indent=2))
        return 0

    print('=' * 78)
    print('RULE 1 (verbatim from docs/10 section 1): a record response whose body_bytes')
    print('  is an exact multiple of 1024 was cut short; one whose byte count is not ran')
    print('  to completion. A CORRELATION over the rows observed, not a proven mechanism.')
    print('=' * 78)
    print()
    print('RULE 2 — "successful 200" is status_of(row) == 200, the reader\'s predicate.')
    print('  Every http_status in this population is a JSON STRING (380 of 380 rows), and')
    print('  pool-s7-l7crawl writes the opaque form "200 (curl)". Three obvious rules, three')
    print('  different answers — which is why the rule is stated rather than assumed:')
    print('    raw == 200      (int)                    : %3d   <- misses every row'
          % lit_int)
    print('    raw == "200"    (exact string equality)  : %3d   <- misses the opaque rows'
          % lit_str)
    print('    status_of(row) == 200  (USED HERE)        : %3d   <- resolves the prefix'
          % total200)
    print('  The gap between the last two is exactly the %d "200 (curl)" rows in'
          % (total200 - lit_str))
    print('  pool-s7-l7crawl. A reader picking either obvious rule gets a different number')
    print('  and no way to tell which is right — AGENTS.md section 6 item 3.')
    print()
    for p, (n200, nc) in per.items():
        print('  %-58s %3d x 200 | whole-KiB %d' % (p, n200, nc))
    print('  %-58s %3d x 200 | whole-KiB %d' % ('TOTAL', total200, cand))
    print()
    print('  body_bytes present on %d of %d successful rows; %d distinct values, %d .. %d B'
          % (len(vals), total200, len(set(vals)), min(vals), max(vals)))
    print('  whole-KiB candidates: %d' % cand)
    print('  ⚠ docs/10 §1: "Clean for this test is not the same as complete" — a')
    print('    truncation not aligned to 1024 is invisible to this detector.')
    print()
    print('=' * 78)
    print('RULE 3 — a MEMBER-SOURCE ROW is one where the reader\'s own predicates agree on')
    print('  all three: query_of(row) in DATA_TARGETS, status_of(row) == 200, and')
    print('  members_of(row) is not None. Three cells, because they are different')
    print('  populations and round 3 caught "67 of 69" mixing two of them.')
    print('=' * 78)
    print()
    print('  %-34s %5s %8s %8s %9s %10s' % ('cell', 'rows', 'w/limit', 'no limit',
                                           'AT limit', 'carried but'))
    print('  %-34s %5s %8s %8s %9s %10s' % ('', '', '', '', '', 'NOT reached'))
    for lbl, c in (('A  every such row', A), ('B  one per crawl (derive uses)', B),
                   ('C  B restricted to in-window', C)):
        print('  %-34s %5d %8d %8d %9d %10d'
              % (lbl, c['n'], c['carrying_limit'], c['carrying_no_limit'],
                 c['at_own_limit'], c['carried_but_not_reached']))
    print()
    print('  ONLY `AT limit` means the tail may have been cut. Carrying a limit WITHOUT')
    print('  reaching it is a different predicate, and a row carrying no limit at all was')
    print('  not truncated by this mechanism. Publishing "carries no limit" as though it')
    print('  meant "did not reach its limit" is the error round 3 caught at cell B.')
    print()
    print('  Rows AT their own limit (printed, not counted):')
    for p, raw, c, lim, rec in rows:
        if lim is not None and rec is not None and rec >= lim:
            print('    %-16s seq%-4s records=%-4s limit=%-5s %s'
                  % (c, raw['seq'], rec, lim, os.path.basename(os.path.dirname(p))))
    return 0


if __name__ == '__main__':
    sys.exit(main())