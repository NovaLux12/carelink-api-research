#!/usr/bin/env python3
"""count-cites.py — how many `file:line` cites this pass publishes, counted.

THE COUNTING RULE, stated before the number (AGENTS.md §6 item 7 — the failure
this exists to prevent is 44 published as 93, and a second pass's own claim of
"23 cites" against its commit message's "29" for the same sweep).

  R-C1 SUBJECT. Only `*.md` files in THIS directory. Not docs/, not README, not
       other passes' logs.

  R-C1b CORRECTION SECTIONS ARE EXCLUDED FROM THE COUNT, NEVER FROM THE RECORD.
       The subject text is each file **up to its first
       `## Correction (YYYY-MM-DD)` heading**. Everything from that heading to the
       end is excluded.

       WHY, and this is the whole reason: a correction section QUOTES the subjects
       it corrects, because `AGENTS.md` §3 requires superseded wording to stay
       visible. Counting those quotations makes the number a FIXED POINT THAT
       RECORDING THE CORRECTION MOVES — appending a correction that quotes three
       NEW cites changes the cite count by three, so the published figure
       describes the previous commit. That is precisely the defect **C17**
       corrects (C14 is unrelated — it is the reproducibility finding about the
       three scripts): this file spent three rounds publishing the previous
       commit's number, 23 / 29 / 31 / 28 / 30 script-side.

       THE EXCLUSION IS FROM THE COUNT, NEVER FROM THE RECORD. Hiding quoted
       wording to stabilise a number would be `AGENTS.md` §1's deletion with the
       sign reversed — the wording stays on disk, stays greppable, and stays part
       of the record; it simply is not an input to this one measurement.
  R-C2 UNIT. One cite = one `path:line` or `path:line-line` token occurring
       inside backticks, where `path` carries a file extension. A path with no
       line number is NOT a cite (it is a source pointer, counted separately
       below and never added to the cite total).
  R-C3 SELF-REFERENCE. A token resolving to this directory's own `FINDINGS.md`
       is NOT counted. Those were converted to section-heading anchors precisely
       because a line cite into a file this pass keeps editing has a half-life
       shorter than the review cycle (C7). Counting them would re-import the
       fragility the anchor conversion removed.
  R-C4 SHORT FORMS. The C3 sweep table's `site` column also uses short forms
       (`docs/05:480`, `run.log:49`) with no extension. Each is counted once and
       its resolution is checked, because a regex on file extensions misses them.
  R-C5 DEDUPLICATION. Distinct (resolved-file, line-start) targets are counted
       ONCE. The same cite quoted in prose and in a table is one cite.
  R-C6 FAILURES. Every counted cite must resolve, the target line must exist, AND
       the target line must be NON-BLANK. That last clause is the one this
       script earned: a cite can resolve to a line that exists and still be
       wrong, because the text it pointed at moved. Existence is not proof that a
       citation points at what it claims (AGENTS.md §6 item 2). Any failure is
       reported and makes the script exit non-zero — a count that cannot fail is
       not evidence.

Zero network access. Reads only files tracked in this repository.

  python3 count-cites.py

Safe to run from ANY working directory — the repo root, this file's own
directory, or a clean `git archive` export of the branch. Paths are resolved
against the repository root located by walking up from THIS FILE.
"""

import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SELF = os.path.join(HERE, 'FINDINGS.md')


def repo_root():
    """Locate the repository root by walking up from THIS FILE, not from the
    working directory, so the documented invocation works from anywhere
    (AGENTS.md §10)."""
    d = HERE
    for _ in range(8):
        if os.path.isdir(os.path.join(d, 'findings-log')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    sys.exit('PATH MISS: cannot locate the repository root from ' + HERE)


ROOT = repo_root()

# R-C1b: everything from the first dated correction heading onward is quoted
# history and is excluded from the COUNT (never from the record). See the
# docstring for why a self-referential count is a fixed point that recording the
# correction moves.
CORRECTION_SPLIT = re.compile(r'^## Correction \(\d{4}-\d{2}-\d{2}\).*$', re.M)

# R-C2: a path with an extension, then :line or :line-line, inside backticks.
EXT_CITE = re.compile(r'`([A-Za-z0-9._/-]+\.(?:md|py|txt|sh|log)):(\d+)(?:-\d+)?`')
# R-C4: the sweep table's short forms.
SHORT = re.compile(r'`(docs/\d\d|run\.log|count-candidates\.py):(\d+)`')
# path-only source pointers, counted separately, never added to the cite total.
PATH_ONLY = re.compile(r'`(findings-log/[A-Za-z0-9._/-]+\.md)`')

RESOLVE_PREFIXES = ('', 'findings-log/probe-2026-10-08/', 'findings-log/')

SHORT_MAP = {
    'docs/00': 'docs/00-summary-the-map.md',
    'docs/04': 'docs/04-configuration.md',
    'docs/05': 'docs/05-devices-and-vocabulary.md',
    'docs/09': 'docs/09-methodology-and-oracles.md',
    'docs/11': 'docs/11-suggested-research-areas.md',
    'run.log': os.path.join(HERE, 'run.log'),
    'count-candidates.py': os.path.join(HERE, 'count-candidates.py'),
}


def resolve(path):
    for pre in RESOLVE_PREFIXES:
        cand = os.path.normpath(os.path.join(HERE, pre, path)) if pre \
            else os.path.normpath(os.path.join(HERE, path))
        for base in (ROOT, HERE):
            full = os.path.normpath(os.path.join(base, pre, path)) if pre \
                else os.path.normpath(os.path.join(base, path))
            if os.path.isfile(full):
                return full
    return None


def main():
    subjects = sorted(glob.glob(os.path.join(HERE, '*.md')))
    cites, failures = set(), []
    pointer_only = set()
    skipped_self = 0

    for f in subjects:
        t = open(f, encoding='utf-8', errors='replace').read()
        # R-C1b: count the findings, not the record of findings about findings
        t = CORRECTION_SPLIT.split(t, 1)[0]
        for path, line in EXT_CITE.findall(t):
            rp = resolve(path)
            if rp is None:
                failures.append((path, line, 'unresolved'))
                continue
            if os.path.realpath(rp) == os.path.realpath(SELF):
                skipped_self += 1      # R-C3
                continue
            cites.add((os.path.normpath(rp), int(line)))
        for short, line in SHORT.findall(t):
            target = SHORT_MAP.get(short)
            if target is None:
                failures.append((short, line, 'unknown short form'))
                continue
            rp = os.path.normpath(os.path.join(ROOT, target))
            if not os.path.isfile(rp):
                failures.append((short, line, 'unresolved'))
                continue
            cites.add((rp, int(line)))
        for p in PATH_ONLY.findall(t):
            pointer_only.add(p)

    print('COUNTING RULE R-C1..R-C6 — see the docstring of this script.')
    print(f'subjects          : {[os.path.basename(s) for s in subjects]}')
    print()
    print('CITES (R-C5: distinct resolved targets):')
    for path, line in sorted(cites):
        L = open(path, encoding='utf-8', errors='replace').read().splitlines()
        path = os.path.relpath(path, ROOT)
        rel = os.path.relpath(path, ROOT)
        if line > len(L):
            failures.append((rel, line, 'out of range'))
            continue
        if not L[line - 1].strip():
            failures.append((rel, line, 'target line is BLANK - cited text moved'))
            continue
        print(f'  {path}:{line:<4} {L[line - 1][-58:]}')

    print()
    print(f'CITE COUNT        = {len(cites)}')
    print(f'  excluded by R-C3 (self-referential, heading-anchored instead) = '
          f'{skipped_self}')
    print(f'  path-only source pointers, NOT cites (R-C2) = {len(pointer_only)}')
    if failures:
        print()
        for f in failures:
            print(f'  FAILURE {f}')
        sys.exit(f'{len(failures)} cite(s) failed to resolve')
    print('  failures        = 0')


if __name__ == '__main__':
    main()