#!/usr/bin/env python3
"""read-area-l.py — ONE reader for every area-L ledger, and the census it derives.

    python3 read-area-l.py census          # population -> manifest -> census, vs census-84.txt
    python3 read-area-l.py population      # the population, counted, with the counting rule
    python3 read-area-l.py manifest        # write manifest.tsv (precedence order)
    python3 read-area-l.py self-test       # the controls, exercised rather than asserted

WHY THIS EXISTS. Three passes of area L wrote three row schemas. `derive.py` in
`findings-log/2026-10-15-pool-l-ipro-census-cont/` resolved a crawl by looking for
a row whose `role` was literally one of three strings, and called the rest
`older-schema` (that file's lines 182-185). A row's job in the census does not
depend on what its author called it: it depends on WHAT IT QUERIED. So this
reader never reads `role`. It reads `path`, which every schema in the tree
carries, and derives the cell from the query. That is the whole trick, and it is
why one code path covers all five committed schemas instead of three branches
and a mapping table.

WHAT THIS READER DELIBERATELY CANNOT DO. It normalises three member shapes into
one record. That is a claim the schemas carry the same facts — the area's
stated INFERRED assumption — and this reader does NOT settle it. What it does
instead is measure the gap: see `--equivalence` / census section 6, which prints
which fields survive normalisation and which do not. Treat that block as the
finding, not as a caveat attached to it.

OFFLINE. Reads only files under `findings-log/`. Sends nothing.
"""
import argparse
import collections
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOGROOT = os.path.dirname(HERE)
REPO = os.path.dirname(LOGROOT)
CENSUS = os.path.join(LOGROOT, '2026-10-15-pool-l-ipro-census-cont', 'census-84.txt')
MANIFEST = os.path.join(HERE, 'manifest.tsv')

# ---------------------------------------------------------------- the counting rule
#
# POPULATION RULE R1 (mechanical, recorded before any row is read — AGENTS.md §6
# item 7 is what makes this order load-bearing):
#
#   step 1  every committed ledger:  `git ls-files 'findings-log/**/results.jsonl'`
#   step 2  keep a ledger iff its <date>-<slug> slug contains one of the tokens
#           `area-l`, `pool-l`, `l7crawl` as a DASH-DELIMITED component.
#
# R2 is the check on R1: each surviving ledger's own `FINDINGS.md` names area L
# or an area-L successor in its `**Area:**` line. R1 and R2 agree, but they are
# both this pass's work, so the agreement is consistency, NOT corroboration
# (AGENTS.md §2.1 — one author, two rules).
#
# R1 deliberately does NOT require the slug to contain `area-l`: two of the eight
# are lane-lettered (`pool-l-`, `pool-s7-`) and their FINDINGS.md `**Area:**`
# lines are what put them in. A rule that only matched `area-l` would find six and
# would miss the two ledgers a later pass wrote for the same seven crawls.
AREA_L_TOKENS = ('area-l', 'pool-l', 'l7crawl')
CRAWL_RE = re.compile(r'/(CC-MAIN-[0-9]{4}-[0-9]{2})-index')
STATUS_RE = re.compile(r'^(\d{3})')

# ---------------------------------------------------------------- the cell rule
#
# CELL RULE (this is what replaces reading `role`): a row is part of the census's
# DATA CELL iff the `url=` it queried is a domain this area reads, and otherwise
# it is a CONTROL or OTHER. Derived from the query, so it is identical under
# every schema in the tree.
DATA_TARGETS = ('minimed.eu', 'carelink.minimed.eu')

# Member SHAPES are discovered by NAME PATTERN, not read from a hardcoded list.
# `ipro_hcp_count` matches the pattern but is excluded for a stated reason: it is
# a scalar count, and derive.py:122 sets it to len(members), so it carries nothing
# the member list does not. The exclusion is explicit so a future fourth shape is
# counted rather than silently missed.
SHAPE_RE = re.compile(r'^ipro_hcp')
EXCLUDED_FROM_K2 = {
    'ipro_hcp_count': 'a scalar COUNT, not a list shape; derive.py:122 sets it to '
                      'len(members), so it adds no information the list does not',
}
# `medtronic.eu` is a Medtronic domain but no area-L cell queries it; it is
# therefore OTHER, not DATA. Stated because getting it wrong would silently fold
# a 502 control into a data row.


class Unreadable(Exception):
    """A row no branch of this reader understands. Never swallowed."""


def slug_of(path):
    return os.path.basename(os.path.dirname(path))


AREA_L_RE = re.compile(r'(^|-)(area-l|pool-l|l7crawl)(-|$)')
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}-')


def slug_of(path):
    return os.path.basename(os.path.dirname(path))


def area_l_slug(slug):
    """True iff the <date>-<slug> slug, past its date, carries one of the three
    area-L lane tokens on a dash boundary. The date prefix is removed first so
    `2026-10-14-pool-s7-l7crawl` is judged on `pool-s7-l7crawl` and not on the
    `2026-10-14` in front of it."""
    return bool(AREA_L_RE.search(DATE_RE.sub('', slug)))


def population(git=False):
    """Return the area-L ledgers, repo-relative, sorted by (date, slug).

    Step 1 then step 2 of R1. Recorded before any row is read.
    """
    if git:
        out = subprocess.run(['git', 'ls-files', 'findings-log/**/results.jsonl'],
                             cwd=REPO, capture_output=True, text=True, check=True).stdout
        found = [os.path.join(REPO, l) for l in out.splitlines() if l.strip()]
    else:
        found = sorted(glob.glob(os.path.join(LOGROOT, '*', 'results.jsonl')))
    keep = [os.path.relpath(f, REPO) for f in found if area_l_slug(slug_of(f))]
    return sorted(keep, key=lambda p: (os.path.basename(os.path.dirname(p)), p))


# ---------------------------------------------------------------- field readers


def crawl_of(row):
    """The crawl, from the path first and from a `crawl` field second.

    `2026-10-14-pool-s7-l7crawl/results.jsonl` is the only committed schema with
    no `role` key, and it carries `crawl` instead — so the fallback is exercised
    by real data, not only by the synthetic fixture.
    """
    m = CRAWL_RE.search(row.get('path', '') or '')
    if m:
        return m.group(1)
    c = row.get('crawl')
    if c and CRAWL_RE.match('/%s-index' % c):
        return c
    return None


def status_of(row):
    """Resolve `http_status` to an INT and assert the type.

    `2026-10-14-pool-s7-l7crawl` writes `"200 (curl)"`, not `200`. A comparison
    against the string `'200'` is False for that row, which is AGENTS.md §6
    item 3 — a comparison that cannot fail looking like agreement — in its most
    literal form in this tree. Everything downstream sees an int or nothing.
    """
    m = STATUS_RE.match(str(row.get('http_status', '')))
    if not m:
        return None
    v = int(m.group(1))
    assert isinstance(v, int) and not isinstance(v, bool)
    return v


def query_of(row):
    m = re.search(r'[?&]url=([^&]*)', row.get('path', '') or '')
    return m.group(1) if m else None


def matchtype_of(row):
    m = re.search(r'[?&]matchType=([^&]*)', row.get('path', '') or '')
    return m.group(1) if m else None


TS14 = re.compile(r'(\d{14})')
MEMBER_ENTRY = re.compile(r'^(?P<url>\S+?)\s*@(?P<ts>\d{14})\s+status=(?P<code>\d{3})\s*$')


def members_of(row):
    """Normalise the three member shapes to [(path, host, ts, status)].

    Returns None when the row carries NO recognised member field — which is a
    statement about the row, not a zero. None is load-bearing: a ledger with no
    member field must not overwrite a member count from a ledger that has one.
    """
    if 'ipro_hcp' in row:
        v = row['ipro_hcp']
        if not isinstance(v, list):
            raise Unreadable('ipro_hcp is %s, not a list' % type(v).__name__)
        out = []
        for e in v:
            m = MEMBER_ENTRY.match(e)
            if not m:
                raise Unreadable('ipro_hcp entry does not match "url @ts status=nnn": %r' % (e,))
            out.append(normalise(m.group('url'), m.group('ts'), m.group('code')))
        return out
    if 'ipro_hcp_urls' in row:
        v = row['ipro_hcp_urls']
        if not isinstance(v, list):
            raise Unreadable('ipro_hcp_urls is %s, not a list' % type(v).__name__)
        # URL ONLY. No timestamp and no HTTP status exist in this shape; both live
        # in the 2026-10-13 pass's prose. This is the equivalence gap, measured.
        return [normalise(u, '', '') for u in v]
    if 'ipro_hcp_members' in row:
        v = row['ipro_hcp_members']
        if not isinstance(v, list):
            raise Unreadable('ipro_hcp_members is %s, not a list' % type(v).__name__)
        out = []
        for e in v:
            if not isinstance(e, dict) or 'ts' not in e or 'path' not in e:
                raise Unreadable('ipro_hcp_members entry is not {ts, path, ...}: %r' % (e,))
            out.append(normalise('https://%s%s' % (e.get('host', ''), e['path']),
                                 e['ts'], str(e.get('code', ''))))
        return out
    return None


def normalise(url, ts, code):
    host = re.match(r'https?://([^/]+)/?(.*)$', url)
    if not host:
        raise Unreadable('member url does not parse: %r' % (url,))
    d = TS14.search(ts or '')
    return (host.group(2) or '/', host.group(1), d.group(1)[:8] if d else '', str(code))


def read_row(row, src):
    """One ledger row -> one record. The only place a schema branch exists."""
    crawl = crawl_of(row)
    status = status_of(row)
    if crawl is None:
        # Not a crawl row (an inventory fetch, a `/collinfo.json` read). Carried
        # with crawl=None so the arithmetic control still counts it, and excluded
        # from every crawl cell by construction.
        return {'src': src, 'seq': row.get('seq'), 'crawl': None, 'status': status,
                'cell': 'NON-CRAWL', 'query': query_of(row), 'kind': None,
                'members': None, 'records': None}
    q = query_of(row)
    if q not in DATA_TARGETS:
        cell, kind = 'CONTROL/OTHER', None
    else:
        cell = 'DATA'
        kind = 'host' if matchtype_of(row) == 'host' else 'domain'
    m = members_of(row)
    if 'ipro_hcp_count' in row and m is not None:
        c = row['ipro_hcp_count']
        if not isinstance(c, int) or isinstance(c, bool):
            raise Unreadable('ipro_hcp_count is %r, not an int' % (c,))
        if c != len(m):
            raise Unreadable('ipro_hcp_count=%d disagrees with %d members' % (c, len(m)))
    recs = row.get('records', row.get('record_count'))
    return {'src': src, 'seq': row.get('seq'), 'crawl': crawl, 'status': status,
            'cell': cell, 'query': q, 'kind': kind, 'members': m, 'records': recs}


def read_ledger(path, unreadable_ok=False):
    """Return (records, unreadable). Never silently drops a row."""
    recs, bad = [], []
    with open(os.path.join(REPO, path)) as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                recs.append(read_row(json.loads(line), path))
            except (Unreadable, ValueError, AssertionError) as e:
                bad.append((path, n, '%s: %s' % (type(e).__name__, e)))
    if bad and not unreadable_ok:
        for p, n, why in bad:
            sys.stderr.write('UNREADABLE %s line %d — %s\n' % (p, n, why))
        raise SystemExit('reader refuses to emit a census over a row it cannot read '
                         '(pass --allow-unreadable to record it as UNREADABLE instead)')
    return recs, bad


# ---------------------------------------------------------------- the census


def verdict(cell_recs, all_recs):
    """census-84.txt's rule, lines 18-20, applied per crawl.

    RECORD if the last DATA row answered 200; ABSENCE if 404 and some row for
    that crawl answered 200; INDETERMINATE if 404 with no 200 anywhere;
    FAILURE otherwise. 502/504/503/400 is a FAILURE, never an absence.
    """
    data = [r for r in cell_recs if r['cell'] == 'DATA']
    if not data:
        return None, None, False
    probe = data[-1]
    any200 = any(r['status'] == 200 for r in all_recs)
    if probe['status'] == 200:
        v = 'RECORD'
    elif probe['status'] == 404:
        v = 'ABSENCE' if any200 else 'INDETERMINATE'
    else:
        v = 'FAILURE'
    return v, probe, any200


def derive(recs):
    """recs are in manifest (precedence) order, then seq. -> per-crawl records."""
    by = collections.OrderedDict()
    for r in recs:
        if r['crawl'] is None:
            continue
        by.setdefault(r['crawl'], []).append(r)
    out = collections.OrderedDict()
    for crawl, rows in by.items():
        v, probe, any200 = verdict(rows, rows)
        # Verdict precedence: the last DATA row in manifest order wins, because
        # the manifest is chronological and a later pass is an addendum.
        # Member precedence: the last DATA row that (a) answered 200 AND (b)
        # carries a member field wins. (a) is not decoration. An empty member
        # list on a 404 or a 502 says nothing — the query returned no records, so
        # there was nothing to find — and reading it as a zero would convert a
        # FAILURE into an absence, which census-84.txt's own rule forbids
        # ("502/504/503/400 is a FAILURE, never an absence"). CC-MAIN-2013-48 is
        # the cell this fixes: its only member-carrying DATA row is a 502.
        # The two can disagree, and the reader reports that rather than picking.
        mrows = [r for r in rows
                 if r['cell'] == 'DATA' and r['status'] == 200 and r['members'] is not None]
        if mrows:
            m = mrows[-1]
            members, msrc = m['members'], '%s seq %s' % (m['src'], m['seq'])
        else:
            members, msrc = None, None
        # Every DATA row that could NOT supply a count, printed rather than hidden.
        no_evidence = ['%s seq %s (%s)' % (r['src'], r['seq'], r['status'])
                       for r in rows if r['cell'] == 'DATA'
                       and not (r['status'] == 200 and r['members'] is not None)]
        out[crawl] = {
            'verdict': v,
            'probe': ('%s seq %s' % (probe['src'], probe['seq'])) if probe else None,
            'probe_status': probe['status'] if probe else None,
            'any200': any200,
            'members': members,
            'members_src': msrc,
            'n_members': len(members) if members is not None else None,
            'dates': sorted({d for d in (members or []) if d[2]}) if members is not None else None,
            'late_no_member_field': no_evidence,
            'rows': len(rows),
        }
    return out


def read_census_file():
    """census-84.txt -> {crawl: (verdict, members, dates, pass)}. Its rows are 8
    tab-separated fields; the tally lines below are 1-3. A filter of len==5 (what
    an earlier version of derive.py used) matches NOTHING and re-derives over an
    empty set — the silent-pass class this repo has already paid for."""
    rows = {}
    for line in open(CENSUS):
        if not line.startswith('CC-MAIN-'):
            continue
        f = line.rstrip('\n').split('\t')
        if len(f) >= 5:
            rows[f[0]] = {'verdict': f[4], 'members': f[5], 'dates': f[6],
                          'pass': f[7] if len(f) > 7 else '', 'in_window': f[3]}
    return rows


def rule(ch='='):
    print(ch * 78)


def cmd_population(a):
    print('POPULATION RULE R1, in the order it is applied:')
    print('  step 1  git ls-files \'findings-log/**/results.jsonl\'   (all committed ledgers)')
    print('  step 2  keep a ledger iff its <date>-<slug> slug has `area-l`, `pool-l` or')
    print('          `l7crawl` as a dash-delimited component')
    all_l = subprocess.run(['git', 'ls-files', 'findings-log/**/results.jsonl'],
                           cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
    pop = population(git=True)
    print()
    print('  step 1 population                %3d ledgers' % len(all_l))
    print('  step 2 population (the answer)   %3d ledgers' % len(pop))
    rule('-')
    total = 0
    for p in pop:
        n = sum(1 for l in open(os.path.join(REPO, p)) if l.strip())
        total += n
        print('  %-58s %4d rows' % (p, n))
    print('  %-58s %4d rows' % ('TOTAL', total))
    rule('-')
    print('  R2 check — each ledger\'s own FINDINGS.md `**Area:**` line:')
    for p in pop:
        area = ''
        try:
            for line in open(os.path.join(REPO, os.path.dirname(p), 'FINDINGS.md')):
                if line.startswith('**Area:**'):
                    area = line.split('**Area:**')[1].strip()[:90]
                    break
        except OSError:
            area = '(no Area: line)'
        print('    %-40s %s' % (slug_of(p), area or '(states its area in prose, see FINDINGS.md)'))
    return 0


def cmd_schemas(a):
    """SCHEMA CENSUS. The counting rule is printed before the number, because a
    count of "how many schemas" is only meaningful with the rule that produced it.

    COUNTING RULES, three separate questions, three separate answers:

      K1  distinct row key-SETS   = the number of distinct `frozenset(row.keys())`
                                    over every row of the population. Mechanical,
                                    no judgement.
      K2  distinct member FIELDS  = the number of distinct keys among
                                    {ipro_hcp, ipro_hcp_urls, ipro_hcp_members}
                                    present on any row. Mechanical.
      K3  ledgers that break a reader, counted per PROPERTY rather than by a
          single number: rows with no `role` key; rows whose raw `http_status`
          does not EQUAL its 3-digit prefix (so a `== '200'` test misses them);
          ledgers with no DATA cell.

    There is deliberately no "number of schemas" headline. An earlier draft of
    this pass published "five schemas, not three" and the number could not be
    re-derived from any of these rules — it mixed a row-schema property with a
    census-derivation property. Withdrawn; see the Correction section in
    FINDINGS.md.

    The DATA and CONTROL counts here come from `read_row()`, the SAME function
    the census uses. A second rule for the same question would be a second
    unverifiable claim.
    """
    pop = population(git=True)
    rule()
    print('SCHEMA CENSUS over the %d-ledger population (rules K1-K3 below)' % len(pop))
    rule('-')
    keysets = collections.Counter()
    per = collections.OrderedDict()
    for p in pop:
        rows = [json.loads(l) for l in open(os.path.join(REPO, p)) if l.strip()]
        parsed = [read_row(r, p) for r in rows]
        norole = sum(1 for r in rows if 'role' not in r)
        # The discriminator that matters: does a raw `== '200'` test find this row?
        # A plain "200" string is fine. A "200 (curl)" is not — that is the shape
        # that would silently read as "no status" to the comparison derive.py used.
        opaque = sum(1 for r in rows
                     if str(r.get('http_status', ''))[:3].isdigit()
                     and str(r.get('http_status', '')) != str(r.get('http_status', ''))[:3])
        ks = {frozenset(r.keys()) for r in rows}
        # This is the per-ledger COLUMN only. It deliberately does not exclude:
        # the column's job is to show what is on the rows, and hiding
        # `ipro_hcp_count` here would make K2's exclusion list look like it had
        # nothing to exclude. K2 prints the exclusion and its row count.
        flds = collections.Counter()
        for r in rows:
            for k in r:
                if SHAPE_RE.match(k):
                    flds[k] += 1
                    break
        for r in rows:
            keysets[frozenset(r.keys())] += 1
        data = sum(1 for r in parsed if r['cell'] == 'DATA')
        per[p] = {'rows': len(rows), 'keysets': len(ks), 'norole': norole,
                  'opaque': opaque, 'data': data, 'flds': flds}
        print('  %-58s rows %3d | key-sets %2d | no-role %2d | opaque status %2d | DATA %2d | %s'
              % (p, len(rows), len(ks), norole, opaque, data,
                 ','.join(sorted(flds)) or 'no member field'))

    rule('-')
    print('K1  distinct row key-sets over the population      %d' % len(keysets))
    for ks, n in keysets.most_common():
        print('      %4d rows  %s' % (n, ','.join(sorted(ks))[:150]))
    # K2 re-scans the population for member shapes by NAME PATTERN. Each ledger
    # is read ONCE more here rather than reusing `per[p]['flds']`, because K2's
    # answer must come from the same pattern scan that finds an UNEXPECTED fourth
    # shape — reusing the per-ledger summary would make the two agree by
    # construction and hide a shape that appeared on a row the summary skipped.
    shapes = {}
    excluded_seen = collections.Counter()
    for p in pop:
        with open(os.path.join(REPO, p)) as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                # Exclusions are counted over EVERY key, before the one-shape-per-row
                # break. Counting them inside the break would report 0 whenever an
                # excluded key co-occurs with an included one — which is exactly
                # what `ipro_hcp_count` does — and the exclusion list would then
                # look decorative.
                for k in row:
                    if k in EXCLUDED_FROM_K2:
                        excluded_seen[k] += 1
                for k in row:
                    if not SHAPE_RE.match(k) or k in EXCLUDED_FROM_K2:
                        continue
                    shapes.setdefault(k, []).append(row)
                    break
    allflds = sorted(shapes)
    print()
    print('K2  distinct member fields present                  %d  (%s)'
          % (len(allflds), ', '.join(allflds)))
    print('    found by the name pattern `^ipro_hcp` over every key on every row,')
    print('    NOT from a hardcoded list. Excluded by name, and why:')
    for k, why in sorted(EXCLUDED_FROM_K2.items()):
        n = excluded_seen.get(k, 0)
        print('      %-18s excluded on %4d rows — %s' % (k, n, why))
    total_ex = sum(excluded_seen.values())
    print('      (%d row(s) carried an excluded key; the rule was applied, not assumed)'
          % total_ex)
    print('K3  ledgers with rows carrying NO `role` key        %d  (%s)'
          % (len([p for p in per if per[p]['norole']]),
             ', '.join(os.path.basename(os.path.dirname(p)) for p in per if per[p]['norole'])))
    print('    ledgers with an OPAQUE status (raw != 3-digit prefix, so a `== "200"`'
          ' test misses it)')
    print('                                                     %d  (%s)'
          % (len([p for p in per if per[p]['opaque']]),
             ', '.join('%s: %d/%d rows' % (os.path.basename(os.path.dirname(p)),
                                            per[p]['opaque'], per[p]['rows'])
                       for p in per if per[p]['opaque']) or 'none'))
    print('    ledgers with NO DATA cell                       %d  (%s)'
          % (len([p for p in per if per[p]['data'] == 0]),
             ', '.join(os.path.basename(os.path.dirname(p)) for p in per if per[p]['data'] == 0)))
    print()
    print('  K3 are three PROPERTIES, not one count. A ledger can fail a reader on any')
    print('  of them, and "no DATA cell" is a property of what the pass chose to query,')
    print('  not of the shape of a row. Do not add them into a single number.')
    return 0


def cmd_manifest(a):
    pop = population(git=True)
    rows = []
    for i, p in enumerate(pop, 1):
        n = sum(1 for l in open(os.path.join(REPO, p)) if l.strip())
        roles = set()
        norole = 0
        with open(os.path.join(REPO, p)) as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    if 'role' in r:
                        roles.add(str(r['role'])[:28])
                    else:
                        norole += 1
        rows.append((i, p, n, len(roles), norole))
    with open(MANIFEST, 'w') as fh:
        fh.write('# manifest.tsv — precedence order. Generated by read-area-l.py manifest.\n')
        fh.write("# A later row supersedes an earlier one's VERDICT. Member counts are\n")
        fh.write('# taken from the last DATA row that carries a member field, whichever that is.\n')
        fh.write('# order\tledger\trows\tdistinct_role_values\trows_with_no_role_key\n')
        for i, p, n, nr, norole in rows:
            fh.write('%d\t%s\t%d\t%d\t%d\n' % (i, p, n, nr, norole))
    print('wrote %s (%d ledgers)' % (os.path.relpath(MANIFEST, REPO), len(rows)))
    for i, p, n, nr, norole in rows:
        print('  %d  %-58s %4d rows  %3d role values  %3d rows with no role key'
              % (i, p, n, nr, norole))
    return 0


def cmd_census(a):
    pop = population(git=True)
    rule()
    print('1. POPULATION, counted before it is read')
    rule('-')
    print('  counting rule R1 (see `population` mode): git ls-files, then the slug token')
    print('  ledgers in the population         %d' % len(pop))
    in_rows = 0
    for p in pop:
        n = sum(1 for l in open(os.path.join(REPO, p)) if l.strip())
        in_rows += n
        print('    %-58s %4d rows' % (p, n))
    print('  rows in the population            %d' % in_rows)

    recs, bad = [], []
    for p in pop:
        r, b = read_ledger(p, unreadable_ok=a.allow_unreadable)
        recs += r
        bad += b
    rule('-')
    print('  rows read                         %d   (must equal the population: %s)'
          % (len(recs), 'YES' if len(recs) == in_rows else 'NO'))
    if len(recs) != in_rows:
        raise SystemExit('ARITHMETIC CONTROL FAILED: read %d rows over a population of %d'
                         % (len(recs), in_rows))
    assert isinstance(len(recs), int) and isinstance(in_rows, int)
    print('  unreadable rows                   %d' % len(bad))
    if bad:
        for p, n, why in bad:
            print('    UNREADABLE %s line %d — %s' % (p, n, why))

    # Exhaustiveness: every ledger in the population must contribute >=1 record.
    per = collections.Counter(r['src'] for r in recs)
    rule('-')
    print('  EXHAUSTIVENESS CONTROL — every ledger contributes >= 1 record')
    empty = [p for p in pop if per[p] == 0]
    for p in pop:
        print('    %-58s %4d  %s' % (p, per[p], 'ok' if per[p] else 'EMPTY'))
    if not recs:
        raise SystemExit('EXHAUSTIVENESS CONTROL FAILED: the whole output is empty over a '
                         'non-empty population')
    if empty:
        raise SystemExit('EXHAUSTIVENESS CONTROL FAILED: %d ledger(s) contributed no record: %s'
                         % (len(empty), ', '.join(empty)))
    # The manifest must cover the population exactly.
    man = []
    if os.path.exists(MANIFEST):
        for line in open(MANIFEST):
            f = line.rstrip('\n').split('\t')
            if len(f) == 4 and f[0].isdigit():
                man.append(f[1])
    if man:
        miss = sorted(set(pop) - set(man))
        extra = sorted(set(man) - set(pop))
        print('    manifest covers the population    %s'
              % ('EXACTLY' if not miss and not extra else
                 'MISSING %s EXTRA %s' % (miss, extra)))
        if miss or extra:
            raise SystemExit('EXHAUSTIVENESS CONTROL FAILED: manifest/population mismatch')

    D = derive(recs)

    rule()
    print('2. SCHEMA PER LEDGER — what each pass wrote, counted, not remembered')
    rule('-')
    print('  %-40s %5s %7s %8s %8s %s' % ('ledger', 'rows', 'DATA', 'CTRL', 'MEMBER', 'member field'))
    for p in pop:
        rr = [r for r in recs if r['src'] == p]
        d = [r for r in rr if r['cell'] == 'DATA']
        fld = collections.Counter()
        with open(os.path.join(REPO, p)) as fh:
            for line in fh:
                if line.strip():
                    row = json.loads(line)
                    for k in ('ipro_hcp', 'ipro_hcp_urls', 'ipro_hcp_members'):
                        if k in row:
                            fld[k] += 1
        print('  %-40s %5d %7d %8d %8s %s'
              % (slug_of(p), len(rr), len(d), len(rr) - len(d),
                 fld.most_common(1)[0][0] if fld else 'NONE', dict(fld) or '-'))

    rule()
    print('3. THE CENSUS, re-derived from all %d ledgers' % len(pop))
    rule('-')
    F = read_census_file()
    win = sorted(c for c, f in F.items() if f['in_window'] == 'yes')
    print('  in-window crawls in census-84.txt  %d' % len(win))
    print()
    print('  %-16s %-14s %-14s %-6s %-6s %s' % ('crawl', 're-derived', 'census-84.txt', 'mem', 'mem', 'member source / difference'))
    print('  %-16s %-14s %-14s %-6s %-6s %s' % ('', '', '', '(mine)', '(file)',
                                                 '`mem` = "-" means NOT DERIVABLE, which is not 0'))
    diffs, memdiffs, unresolved = [], [], []
    vc = collections.Counter()
    mine_carry = []
    # The member headline is counted over every crawl the reader knows, because
    # census-84.txt line 168's own list reaches outside the window (CC-MAIN-2022-27,
    # `in_window` = `no` on that file's line 119). Both framings are published.
    mine_carry_any = [c for c, d in D.items() if d['n_members']]
    for c in win:
        d = D.get(c)
        f = F[c]
        if d is None:
            unresolved.append(c)
            print('  %-16s %-14s %-14s %-6s %-6s %s' % (c, 'NO ROWS', f['verdict'], '-', f['members'], 'absent from the population'))
            continue
        vm = d['verdict']
        vc[vm] += 1
        # `-` means NOT DERIVABLE, which is not the same claim as 0. A crawl whose
        # only member-bearing DATA rows are non-200 has no member count in the tree,
        # and this reader will not print 0 for it.
        nm = '-' if d['n_members'] is None else str(d['n_members'])
        fb = f['members']
        mark = ''
        if vm != f['verdict'] and f['verdict'] != 'older-schema':
            diffs.append((c, vm, f['verdict']))
            mark = '  <== VERDICT DIFFERS'
        elif f['verdict'] == 'older-schema':
            mark = '  <== older-schema resolved'
            diffs.append((c, vm, f['verdict']))
        if nm != '-' and fb != '-' and int(nm) != int(fb):
            memdiffs.append((c, int(nm), int(fb), d['members_src']))
            mark += '  <== MEMBERS DIFFER'
        if d['n_members']:
            mine_carry.append(c)
        print('  %-16s %-14s %-14s %-6s %-6s %s%s'
              % (c, vm, f['verdict'], nm, fb, (d['members_src'] or 'no member field')[:52], mark))
    rule('-')
    print('  re-derived verdicts over the %d in-window crawls: %s'
          % (sum(vc.values()), dict(sorted(vc.items()))))
    print('  census-84.txt published            : RECORD 65 | ABSENCE 10 | INDETERMINATE 1 | '
          'FAILURE 0 | older-schema 8')
    print('  older-schema cells resolved here   : %d'
          % len([d for d in diffs if d[2] == 'older-schema']))
    print('  with NO verdict derivable          : %d %s' % (len(unresolved), unresolved or ''))

    rule()
    print('4. CELL-BY-CELL COMPARISON — BOTH VALUES STANDING (AGENTS.md §2)')
    rule('-')
    print('  cell                          census-84.txt   re-derived   both standing?')
    cells = [
        ('published indexes', 128, len(F)),
        ('in window', 84, len(win)),
        ('RECORD', 65, vc['RECORD']),
        ('ABSENCE', 10, vc['ABSENCE']),
        ('INDETERMINATE', 1, vc['INDETERMINATE']),
        ('FAILURE', 0, vc['FAILURE']),
        ('older-schema', 8, 0),
        ('UNREAD', 0, len(unresolved)),
    ]
    print()
    print('  the `older-schema` cell: census-84.txt labels 8 cells that way; this reader')
    print('  emits that verdict 0 times, resolving all %d of them to a named row in section 5.'
          % len([d for d in diffs if d[2] == 'older-schema']))
    print()
    for name, published, mine in cells:
        agree = 'yes' if published == mine else '** NO - both values published **'
        print('  %-28s %10s %11s   %s' % (name, published, mine, agree))
    print()
    print('  the member cell is published twice on purpose. census-84.txt line 168 counts 11')
    print('  crawls, and its list includes CC-MAIN-2022-27, which its own line 119 marks')
    print('  `no` for in_window. Its 11 is therefore 10 in-window + 1 out-of-window. Both')
    print('  framings are compared here rather than one being chosen.')
    print('    crawls carrying >=1 member (any) census-84.txt %2d  re-derived %2d'
          % (11, len(mine_carry_any)))
    print('    ...of which IN window                census-84.txt %2d  re-derived %2d'
          % (10, len(mine_carry)))
    rule('-')
    print('  total in-window members, census-84.txt: %d'
          % sum(int(F[c]['members']) for c in win if F[c]['members'].isdigit()))
    mine_tot = 0
    for c in win:
        d = D.get(c)
        if d and d['n_members']:
            mine_tot += d['n_members']
    print('  total in-window members, re-derived    : %d' % mine_tot)
    if memdiffs:
        print()
        print('  MEMBER COUNTS THAT MOVE, both values standing:')
        for c, n, o, src in memdiffs:
            print('    %-16s census-84.txt=%d  re-derived=%d  from %s' % (c, o, n, src))
    # A crawl can carry members under one reader and not the other without its
    # COUNT moving (a crawl census-84.txt scores >0 that this reader scores 0).
    # That is the only way the ">1 member" cell can move without a memdiff, so
    # it is checked separately rather than inferred from the totals.
    carry_moved = []
    for c in win:
        d = D.get(c)
        if not d:
            continue
        o = int(F[c]['members']) if F[c]['members'].isdigit() else 0
        n = d['n_members'] or 0
        if (o > 0) != (n > 0):
            carry_moved.append((c, o, n, d['members_src']))
    if carry_moved:
        print()
        print('  MEMBER-CARRYING STATUS THAT MOVES, both values standing:')
        for c, o, n, src in carry_moved:
            print('    %-16s census-84.txt=%d  re-derived=%d  from %s'
                  % (c, o, n, src or 'no ledger row carries a member field'))
    if diffs:
        print()
        print('  VERDICTS THAT MOVE, both values standing:')
        for c, n, o in diffs:
            print('    %-16s census-84.txt=%-13s re-derived=%s' % (c, o, n))

    rule()
    print('5. THE EIGHT older-schema CELLS, one by one, with the row each resolves to')
    rule('-')
    eight = [c for c in win if F[c]['verdict'] == 'older-schema']
    for c in eight:
        d = D.get(c)
        if not d:
            print('  %-16s NOT RESOLVED — no ledger row' % c)
            continue
        print('  %-16s %-14s probe %s (%s)  members=%s from %s'
              % (c, d['verdict'], d['probe'], d['probe_status'],
                 'NOT DERIVABLE' if d['n_members'] is None else d['n_members'],
                 d['members_src'] or 'no DATA row answered 200 with a member field'))
        for lf in d['late_no_member_field']:
            print('  %-16s   DATA row that cannot supply a member count: %s' % ('', lf))

    rule()
    print('6. WHAT THE READER CANNOT SETTLE — the equivalence question, measured')
    rule('-')
    # K2's shapes are FOUND, not listed, so a fourth shape in a future ledger is
    # counted rather than silently missed. SHAPE_RE and EXCLUDED_FROM_K2 are
    # module-level (see DATA_TARGETS) and shared with members_of()'s branch set.
    shapes = {}
    excluded_seen = collections.Counter()
    for p in pop:
        with open(os.path.join(REPO, p)) as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                for k in row:
                    if not SHAPE_RE.match(k):
                        continue
                    if k in EXCLUDED_FROM_K2:
                        excluded_seen[k] += 1
                        continue
                    shapes.setdefault(k, []).append(row)
                    break
    # Each ledger is read ONCE, and each row is appended to exactly one shape by
    # the loop above. An earlier draft read the ledgers a second time here and
    # appended every row again, which printed exactly 2x the true member-shape
    # counts (456/178/22 for 228/89/11) — the same silent-overcount class this
    # repo's S-L2 section had to correct twice. Removed in verifier round 5.
    print('  %-20s %6s  %s' % ('member shape', 'rows', 'fields recoverable per member'))
    for k, rows_ in shapes.items():
        if not rows_:
            print('  %-20s %6d  (shape not present in the population)' % (k, 0))
            continue
        sample = None
        for row in rows_:
            try:
                m = members_of(row)
            except Unreadable:
                continue
            if m:
                sample = m          # first NON-EMPTY list, or the shape carries none
                break
        if sample is None:
            print('  %-20s %6d  every occurrence is an EMPTY list — no member to inspect'
                  % (k, len(rows_)))
            continue
        got = {'path': bool(sample[0][0]), 'host': bool(sample[0][1]),
               'ts (YYYYMMDD)': bool(sample[0][2]), 'http status': bool(sample[0][3])}
        print('  %-20s %6d  %s' % (k, len(rows_), ', '.join('%s=%s' % kv for kv in got.items())))
    print()
    print('  EVERY MEMBER COUNT HERE IS A LOWER BOUND, NOT AN EXACT TOTAL — stated here,')
    print('  next to the figures, because a limit placed upstream of a number reads as an')
    print('  exact one (AGENTS.md section 2). The mechanism measured below is the one this')
    print('  reader CAN see: a `limit=` parameter that the response actually reached.')
    print()
    # Cell A: EVERY qualifying row. Carrying a `limit=` and REACHING it are
    # different predicates, and only the second means the tail may have been cut.
    # An earlier revision printed "every other row carries no limit=" — which
    # asserts the first predicate about rows selected by the second, and is false
    # for every row that carried a limit without reaching it. Both are counted.
    ms = []
    for p in pop:
        with open(os.path.join(REPO, p)) as fh:
            for line in fh:
                if not line.strip():
                    continue
                r = json.loads(line)
                if query_of(r) not in DATA_TARGETS or status_of(r) != 200:
                    continue
                if members_of(r) is None:
                    continue
                m = re.search(r'[?&]limit=([^&]*)', r.get('path', '') or '')
                n = r.get('records', r.get('record_count'))
                if not isinstance(n, int) or isinstance(n, bool):
                    n = None
                ms.append((crawl_of(r), r['seq'], n,
                           int(m.group(1)) if m else None, p))
    floors = [x for x in ms if x[3] is not None and x[2] is not None and x[2] >= x[3]]
    carried = [x for x in ms if x[3] is not None]
    carried_not_at = [x for x in carried if x not in floors]
    nolit = [x for x in ms if x[3] is None]
    print('    member-source rows (DATA + 200 + a member field)          %d' % len(ms))
    print('      carrying a limit=                                      %3d' % len(carried))
    print('      carrying no limit=                                     %3d' % len(nolit))
    print('      AT their own limit (records >= limit) -> tail may be cut %3d' % len(floors))
    print('      carried a limit WITHOUT reaching it                    %3d' % len(carried_not_at))
    print()
    for c, s, n, lim, src in floors:
        print('      %-16s seq%-4s records=%-4s limit=%-5s %s  <== FLOOR: the tail may be cut'
              % (c, s, n, lim, src.split("/")[1]))
    print()
    print('    ONLY "AT their own limit" means a limit could have truncated the tail.')
    print('    A row that CARRIED a limit and did not reach it was not truncated by that')
    print('    mechanism; a row carrying no limit was not truncated by it either. So the')
    print('    count that bears on the figures is %d of %d, not "every other row".'
          % (len(floors), len(ms)))
    print('    Per-cell counts for the three populations are in kib-detector.py, which')
    print('    computes this with the same three predicates rather than restating them.')
    print()
    print('    And that is NOT the same as completeness: it rules out ONE mechanism. The')
    print('    body-set question needs the bodies, which AGENTS.md section 7 excludes.')
    print()
    print('  All three shapes yield a MEMBER COUNT. Two of the three yield a timestamp and')
    print('  an HTTP status. `ipro_hcp_urls` carries a URL and nothing else: the 2014-03-10')
    print("  date and 200 that census prose gives for CC-MAIN-2014-10 live in that pass's")
    print('  FINDINGS.md, not in its ledger. So "the three schemas carry the same facts" is')
    print('  demonstrated for the count and for the path/host, and NOT demonstrated for the')
    print('  date or the status. The reader normalises the count and refuses to invent the rest.')
    print()
    print('  A SECOND, larger limit, stated rather than smoothed: an empty member list on a')
    print('  200 row is read as a zero because the SAME ledger populates the same field on a')
    print('  sibling crawl with a member. That is an internal consistency argument inside one')
    print('  pass\'s ledger — it is not a demonstration that the field was computed on that row.')
    print('  Cross-check inside the tree: in 2026-10-13-area-l-7crawl-reissue, seq 21/22')
    print('  (2014-10) carry 1 member and seq 25/26 (2015-22) carry 0 with records=1.')
    return 0


# ---------------------------------------------------------------- the controls


def self_test():
    """Exercise the reader's failure paths. A reader that cannot fail is not evidence."""
    ok = True
    n_checks = 0

    def check(name, cond, detail=''):
        nonlocal ok, n_checks
        ok = ok and cond
        n_checks += 1
        print('  %-58s %s %s' % (name, 'PASS' if cond else '** FAIL **', detail))

    print('SELF-TEST — synthetic rows, one per committed schema, plus the ones it must refuse')
    rule('-')

    good = {
        'A ipro_hcp (2026-10-14/15 passes)': {
            'seq': 1, 'path': '/CC-MAIN-2020-50-index?url=carelink.minimed.eu&output=json&matchType=host',
            'http_status': 200, 'role': 'probe-host',
            'ipro_hcp': ['https://carelink.minimed.eu/ipro/hcp/login.jsf @20201202030717 status=200'],
            'records': 1},
        'B ipro_hcp_urls (2026-10-13 reissue passes)': {
            'seq': 1, 'path': '/CC-MAIN-2014-10-index?url=minimed.eu&output=json&matchType=domain',
            'http_status': 200, 'role': 'PROBE-2014-10-domain-reissue2',
            'ipro_hcp_urls': ['https://carelink.minimed.eu/ipro/hcp/login.jsf'], 'records': 1},
        'C ipro_hcp_members (2026-10-13 ipro-hcp)': {
            'seq': 34, 'path': '/CC-MAIN-2020-24-index?url=minimed.eu&output=json&matchType=domain',
            'http_status': 200, 'role': 'REISSUE-of-seq-30', 'record_count': 7,
            'ipro_hcp_count': 1,
            'ipro_hcp_members': [{'ts': '20201202030717', 'code': '200',
                                  'host': 'carelink.minimed.eu', 'path': '/ipro/hcp/login.jsf',
                                  'mimetype': '', 'is_redirect': False}]},
        'D no role key at all (pool-s7, "200 (curl)")': {
            'seq': 9, 'path': '/CC-MAIN-2014-10-index?url=minimed.eu&output=json&matchType=domain&limit=5',
            'http_status': '200 (curl)', 'crawl': 'CC-MAIN-2014-10', 'record_count': 1},
        'E control row (must not become a data cell)': {
            'seq': 2, 'path': '/CC-MAIN-2014-10-index?url=commoncrawl.org&output=json&matchType=domain',
            'http_status': 200, 'role': 'control', 'records': 37},
    }
    parsed = {}
    for name, row in good.items():
        try:
            r = read_row(row, 'fixture')
            parsed[name] = r
            check('parses: ' + name, True,
                  '-> cell=%s status=%r type=%s members=%s'
                  % (r['cell'], r['status'], type(r['status']).__name__,
                     'None' if r['members'] is None else len(r['members'])))
        except Exception as e:                                  # noqa: BLE001
            check('parses: ' + name, False, repr(e))
    rule('-')
    check('status resolves to int, not str (s7\'s "200 (curl)")',
          isinstance(parsed['D no role key at all (pool-s7, "200 (curl)")']['status'], int)
          and parsed['D no role key at all (pool-s7, "200 (curl)")']['status'] == 200)
    check('the control row is not a DATA cell',
          parsed['E control row (must not become a data cell)']['cell'] == 'CONTROL/OTHER')
    # The substantive version of the "a string comparison would miss that 200" claim,
    # over the REAL ledger. An earlier draft asserted it as
    # `('200 (curl)' == '200') is False` — two literals compared to each other,
    # False by construction, unchangeable by anything the reader does. That is a
    # vacuous control wearing a control's name. These two read the committed file:
    # if the reader stopped normalising, `resolved7` would collapse to 0 and the
    # second check FAILS.
    s7 = os.path.join(REPO, 'findings-log/2026-10-14-pool-s7-l7crawl/results.jsonl')
    raw7 = [json.loads(l) for l in open(s7) if l.strip()]
    str_eq = sum(1 for r in raw7 if r['http_status'] == '200')
    resolved7 = sum(1 for r in raw7 if status_of(r) == 200)
    check('REAL s7 ledger: a raw == "200" test finds %d of %d rows...' % (str_eq, len(raw7)),
          str_eq == 0, '-> every row is the opaque "NNN (curl)" form')
    check('...and the reader resolves %d of them to an int 200' % resolved7,
          resolved7 > 0 and all(isinstance(status_of(r), int) for r in raw7))
    check('the three fixtures agree on the member COUNT for the same fact',
          len(parsed['A ipro_hcp (2026-10-14/15 passes)']['members']) == 1
          and len(parsed['B ipro_hcp_urls (2026-10-13 reissue passes)']['members']) == 1
          and len(parsed['C ipro_hcp_members (2026-10-13 ipro-hcp)']['members']) == 1)
    check('...and on the path and host',
          parsed['A ipro_hcp (2026-10-14/15 passes)']['members'][0][:2]
          == parsed['B ipro_hcp_urls (2026-10-13 reissue passes)']['members'][0][:2]
          == parsed['C ipro_hcp_members (2026-10-13 ipro-hcp)']['members'][0][:2])
    check('...but NOT on the timestamp: ipro_hcp_urls carries none',
          parsed['A ipro_hcp (2026-10-14/15 passes)']['members'][0][2] == '20201202'
          and parsed['B ipro_hcp_urls (2026-10-13 reissue passes)']['members'][0][2] == '')
    check('a row with no member field reads None, not 0 (s7)',
          parsed['D no role key at all (pool-s7, "200 (curl)")']['members'] is None)

    rule('-')
    print('  MEMBER-SOURCE RULE — only a DATA row that answered 200 may supply a count')
    # An empty member list on a 404 or a 502 is vacuous: the query returned no
    # records, so there was nothing to find. Reading it as a zero would convert a
    # FAILURE into an absence, which census-84.txt's own verdict rule forbids.
    ok200 = dict(good['A ipro_hcp (2026-10-14/15 passes)'], http_status=200)
    fail502 = dict(good['A ipro_hcp (2026-10-14/15 passes)'], http_status=502,
                   ipro_hcp=[], records=0)
    D2 = derive([read_row(ok200, 'f'), read_row(fail502, 'f')])
    check('a 200 row supplies the count',
          D2['CC-MAIN-2020-50']['n_members'] == 1
          and D2['CC-MAIN-2020-50']['members_src'] is not None)
    D3 = derive([read_row(fail502, 'f')])
    check('a lone 502 row supplies NO count (not 0)',
          D3['CC-MAIN-2020-50']['n_members'] is None,
          '-> n_members=%r — the difference between "not derivable" and "none found"'
          % D3['CC-MAIN-2020-50']['n_members'])

    rule('-')
    print('  NEGATIVE CONTROL — rows this reader must REFUSE, not guess at')
    bad = {
        'unknown member entry shape': dict(good['A ipro_hcp (2026-10-14/15 passes)'],
                                           ipro_hcp=['total garbage with no timestamp']),
        'member field is not a list': dict(good['A ipro_hcp (2026-10-14/15 passes)'],
                                           ipro_hcp='a bare string'),
        'ipro_hcp_count disagrees with the list': dict(good['C ipro_hcp_members (2026-10-13 ipro-hcp)'],
                                                       ipro_hcp_count=99),
        'member dict without ts/path': dict(good['C ipro_hcp_members (2026-10-13 ipro-hcp)'],
                                            ipro_hcp_members=[{'code': '200'}]),
        'member url that does not parse': dict(good['A ipro_hcp (2026-10-14/15 passes)'],
                                               ipro_hcp=[' @20201202030717 status=200']),
    }
    for name, row in bad.items():
        try:
            read_row(row, 'fixture')
            check('refuses: ' + name, False, '— it parsed it, so it cannot detect this')
        except Unreadable as e:
            check('refuses: ' + name, True, '-> Unreadable: %s' % str(e)[:52])
        except Exception as e:                                  # noqa: BLE001
            check('refuses: ' + name, False, 'wrong exception %r' % e)

    rule('-')
    print('  EXHAUSTIVENESS / ARITHMETIC CONTROLS — over an empty and a real population')
    empty = []
    try:
        D = derive(empty)
        check('empty population over zero inputs does not print a verdict', D == {},
              '-> derive() returned {} — the census prints NO ROWS, not ok')
    except Exception as e:                                      # noqa: BLE001
        check('empty population raises rather than reporting', False, repr(e))
    one = [read_row(good['A ipro_hcp (2026-10-14/15 passes)'], 'f'),
           read_row(good['E control row (must not become a data cell)'], 'f')]
    D = derive(one)
    check('a crawl whose rows are ALL controls yields NO verdict, not RECORD',
          len(D) == 2 and D['CC-MAIN-2014-10']['verdict'] is None
          and D['CC-MAIN-2020-50']['verdict'] == 'RECORD',
          '-> 2014-10 verdict=%r, 2020-50 verdict=%r'
          % (D['CC-MAIN-2014-10']['verdict'], D['CC-MAIN-2020-50']['verdict']))
    check('row arithmetic is an int comparison',
          isinstance(len(one), int) and len(one) == 2)

    rule('-')
    print('  POPULATION RULE R1 — PINNED HERE, because it produced this pass\'s most')
    print('  consequential finding (derive.py read 6 ledgers where R1 finds 8) and')
    print('  AGENTS.md section 3 says a claim that should not rot gets a check. It is')
    print('  pure string analysis over committed ledgers: no vendor pin is needed.')
    all_ledgers = sorted(glob.glob(os.path.join(LOGROOT, '*', 'results.jsonl')))
    keep = [os.path.relpath(f, REPO) for f in all_ledgers if area_l_slug(slug_of(f))]
    check('R1 selects 8 area-L ledgers from the committed population',
          len(keep) == 8, '-> %d of %d committed ledgers' % (len(keep), len(all_ledgers)))
    check('R1 selects none of the 6-ledger subset derive.py actually read, unreached',
          'findings-log/2026-10-14-pool-l-crawlcontrol/results.jsonl' in keep
          and 'findings-log/2026-10-14-pool-s7-l7crawl/results.jsonl' in keep)
    # The rule is a SLUG rule, so its two edges are what could rot: a lane-lettered
    # slug must still be caught, and an unrelated letter must not be.
    check('R1 catches a lane-lettered slug (pool-l-)',
          area_l_slug('2026-10-14-pool-l-crawlcontrol'))
    check("R1 catches the l7crawl token", area_l_slug('2026-10-14-pool-s7-l7crawl'))
    check('R1 ignores the date prefix (which is not a lane token)',
          area_l_slug('2026-10-15-pool-l-ipro-census-cont'))
    check('R1 rejects an unrelated lane (area-k)', not area_l_slug('2026-10-14-area-k-clinic-controlflow'))
    check('R1 rejects a substring that is not a lane token (csr-method)',
          not area_l_slug('2026-10-13-cors-method'))
    check('R1 is order-stable (date, then slug)',
          keep == sorted(keep, key=lambda p: (os.path.basename(os.path.dirname(p)), p)))

    rule('-')
    print('  INTEGRATION NEGATIVE CONTROL — one unreadable row appended to a REAL ledger')
    # The row-level refusals above prove the parser notices. This proves the
    # CENSUS refuses to be printed at all, which is the control that matters: a
    # reader that downgrades an unreadable row to a warning would print a census
    # over 8 of its 9 rows and call it complete.
    src = os.path.join(REPO, pop_one := population(git=True)[0])
    tmp = os.path.join(HERE, '.selftest-unreadable.jsonl')
    with open(src) as fh:
        body = fh.read()
    with open(tmp, 'w') as fh:
        fh.write(body)
        fh.write(json.dumps({'seq': 9999, 'path': '/CC-MAIN-2099-99-index?url=minimed.eu',
                             'http_status': 200, 'ipro_hcp': 'not-a-list'}) + '\n')
    n_before = sum(1 for l in open(src) if l.strip())
    try:
        read_ledger(os.path.relpath(tmp, REPO))
        check('refuses to emit a census over an unreadable row', False,
              '— read_ledger returned, so it cannot detect this')
    except SystemExit as e:
        check('refuses to emit a census over an unreadable row', True,
              '-> SystemExit: %s' % str(e)[:56])
    recs2, bad2 = read_ledger(os.path.relpath(tmp, REPO), unreadable_ok=True)
    check('with --allow-unreadable it records the row instead of dropping it',
          len(bad2) == 1 and len(recs2) == n_before,
          '-> %d records kept of %d real rows, %d recorded UNREADABLE'
          % (len(recs2), n_before, len(bad2)))
    os.unlink(tmp)
    rule()
    # The count is DERIVED here, not asserted in prose. `grep -c PASS` on this
    # output would over-count by one, because the summary line below contains the
    # word PASS — which is how an earlier draft of this pass published "23 checks"
    # for 22 checks.
    print('  self-test: %s (%d checks, counted by this function, not asserted)'
          % ('PASS' if ok else 'FAIL', n_checks))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['population', 'schemas', 'manifest', 'census', 'self-test'])
    ap.add_argument('--allow-unreadable', action='store_true',
                    help='record unreadable rows as UNREADABLE instead of refusing to emit')
    a = ap.parse_args()
    if a.mode == 'self-test':
        return self_test()
    if a.mode == 'population':
        return cmd_population(a)
    if a.mode == 'schemas':
        return cmd_schemas(a)
    if a.mode == 'manifest':
        return cmd_manifest(a)
    return cmd_census(a)


if __name__ == '__main__':
    sys.exit(main())