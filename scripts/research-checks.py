#!/usr/bin/env python3
"""research-checks.py — the checks a diff-based gate cannot see.

Usage:
    python3 scripts/research-checks.py [--suite-log PATH]

Runs on the WHOLE tree, not a diff: the claims checked here live in README.md
and docs/, which a valid PR need not touch at all. The PR gate calls this
after the assertion suite, so --suite-log carries the suite's own output —
the ground truth for the runtime count.

THE COUNTING RULE (read this before "fixing" a number)
------------------------------------------------------
static  = jsonpath/header predicates inside [Asserts] blocks across the four
          .hurl suites
        + `check "` sites in 05-public-config.check.sh
          (the site inside the 16-family loop counts ONCE here — it is one
          site; it executes 16 times. This distinction has miscounted the
          repo's own badge twice: 93 was right once, then silently wrong; a
          195 arose from counting request lines; a 95 from miscounting the
          loop site. The rule is written down so the next person to add a
          pin changes the rule, the number, and nothing else.)
runtime = static's hurl part + 2 x `HTTP` lines (hurl counts each status
          line as two asserts: version + code)
        + 05's executed assertions: non-loop check sites + the loop site x16
          + the INLINE_05 inline PASS branches (see measure_assertions.py for
            the constant — it is not restated here, because this file used to
            say 5 in prose while the constant read 7), or the `N passed` line
            from the suite log when the gate has just run it.

What it enforces:
  1. NUMBERS — every prose count matches the measured one. Static is what
     prose must state; runtime is stated in the README and checked when the
     suite log is available. Values the assertion suite itself protects (69
     keys, 16 families, 29 countries) are deliberately NOT re-checked here —
     they are pinned by assertion, per AGENTS.md section 3. The counts-branch
     comparison is warning-only: a PR that adds pins legitimately moves the
     count before the next sweep republishes it.
  2. FINDINGS-LOG HYGIENE — every dated log dir carries its accounting
     (requests/cap/delay/method), its machine log is no longer than the
     accounting claims, and no raw archive capture is committed.
  3. PRIORITIES SYNC — no findings-log doc may declare an area closed while
     docs/11 still lists it open. This is the check whose first failure is
     the repo's own Area C desync (2026-10-11).
  4. PROMPT PARITY — every .github/prompts/*.md cites AGENTS.md, and the
     loop report contract (ITERATION / REQUESTS_USED / AREAS_OPEN / STOP /
     NOTES) agrees across loop-close-areas.prompt.md, research-loop.sh, and
     CONTRIBUTING Prompt B. Interface-based, not verbatim: prompts for
     different tasks carry different rules by design.
  5. APPEND-ONLY — findings-log/ deletions fail; modifications without a
     dated `## Correction (YYYY-MM-DD)` section fail. Additions are free.

Deliberately NOT enforced: whether a claim is true. That is the human's, or a
second pass'. (scripts/research-gate.sh header.)
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys

# The counting rule lives in one file so the gate, the badge job and anyone
# re-deriving the number cannot disagree. (An undocumented counting rule is
# itself an unverifiable claim — this repo's cardinal sin.)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure_assertions import measure  # noqa: E402

FAILED = False


def fail(msg):
    global FAILED
    FAILED = True
    print(f'  !! {msg}')


def ok(msg):
    print(f'  ok {msg}')


def warn(msg):
    print(f'  warn {msg}')


def read(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        return fh.read()


def measure_for_check(suite_log):
    """Static and runtime counts, from the one rule (measure_assertions.py)."""
    observed = None
    if suite_log and os.path.exists(suite_log):
        m = re.search(r'(\d+) passed, \d+ failed', read(suite_log))
        if m:
            observed = int(m.group(1))
    m = measure(observed_05=observed)
    detail = (f'{m["predicates"]} predicates + {m["check_sites"]} check sites '
              f'(static); {m["http_lines"]} HTTP lines; 05 executes '
              f'{m["executed_05"]}')
    return m['static'], m['runtime'], detail


def check_numbers(suite_log):
    static, runtime, detail = measure_for_check(suite_log)
    print(f'--- numbers (rule: {detail}) ---')

    # Prose sites that must state the STATIC count.
    static_sites = [
        ('README.md', r'badge/dynamic/json\?[^)"]*query=%24\.assertions\.static', 'badge (machine-written from counts.json)'),
        ('README.md', r'(\d+) pinned assertions', 'the what\'s-here row'),
        ('docs/00-summary-the-map.md', r'pins (\d+) of these facts', 'the map'),
        ('docs/09-methodology-and-oracles.md', r'holds (\d+) assertions', 'methodology'),
    ]
    static_fail = False
    for path, pattern, label in static_sites:
        if not os.path.exists(path):
            continue
        found = False
        # The badge marker is allowed to be value-free: its number comes from
        # the sweep's counts.json, and this check exists to catch *prose* going
        # stale, not to police a machine-written URL.
        value_free = 'machine-written' in label
        for i, line in enumerate(read(path).splitlines(), 1):
            for m in re.finditer(pattern, line):
                found = True
                if value_free:
                    ok(f'{path} carries the machine-written count badge')
                    continue
                if int(m.group(1)) != static:
                    fail(f'{path}:{i} ({label}) states {m.group(1)} assertions, '
                         f'measured static={static} runtime={runtime}')
                    static_fail = True
        if not found:
            fail(f'{path}: no statement matching {pattern!r} — the count moved out of prose; say it explicitly')
            static_fail = True
    if not static_fail:
        ok(f'static assertion count is {static} everywhere it is stated')

    # Prose sites that may state the RUNTIME count (checked when present).
    # The phrasing is matched loosely on purpose: it is the number that must
    # agree, not the sentence around it.
    runtime_patterns = [
        r'(\d+)\s+execute per run',
        r'(\d+) count what actually executes',
        r'executes? (\d+) per (?:full )?run',
    ]
    for path in ('README.md', 'docs/09-methodology-and-oracles.md'):
        if not os.path.exists(path):
            continue
        for i, line in enumerate(read(path).splitlines(), 1):
            for pat in runtime_patterns:
                m = re.search(pat, line)
                if m and int(m.group(1)) != runtime:
                    fail(f'{path}:{i} states {m.group(1)} executed per run, '
                         f'measured {runtime} — rule in '
                         f'scripts/measure_assertions.py')
                elif m:
                    ok(f'runtime statement at {path}:{i} matches ({runtime})')

    # Canonical page count: docs/00-11 are the numbered pages; RESEARCH-SESSION
    # is a pointer stub and is excluded.
    pages = len(glob.glob('docs/*.md')) - 1
    for i, line in enumerate(read('README.md').splitlines(), 1):
        m = re.search(r'(\d+) canonical pages', line)
        if m and int(m.group(1)) != pages:
            fail(f'README.md:{i} states {m.group(1)} canonical pages, measured {pages}')

    # Open research areas: docs/11 lettered headings vs config.yml's claim.
    areas = len(re.findall(r'^###\s+[A-Z]\.\s', read('docs/11-suggested-research-areas.md'), re.M))
    for i, line in enumerate(read('.github/ISSUE_TEMPLATE/config.yml').splitlines(), 1):
        m = re.search(r'about: (\d+) (?:open )?areas', line)
        if m and int(m.group(1)) != areas:
            fail(f'.github/ISSUE_TEMPLATE/config.yml:{i} states {m.group(1)} areas, '
                 f'measured {areas} (^### [A-Z]. headings in docs/11)')
    ok(f'{areas} open areas listed in docs/11; config.yml agrees')

    # The sweep's own data file, when the counts branch exists.
    # Warning-only, not a failure: any PR that adds a pin legitimately moves
    # the count before the next Monday sweep republishes counts.json. Failing
    # here would deadlock every assertion-adding PR until the sweep runs.
    try:
        raw = subprocess.run(['git', 'show', 'counts:counts.json'],
                             capture_output=True, text=True, timeout=10)
        if raw.returncode == 0:
            data = json.loads(raw.stdout)['assertions']
            for key, measured in (('static', static), ('runtime', runtime)):
                if data.get(key) != measured:
                    warn(f'counts:counts.json states {key}={data.get(key)}, measured {measured} '
                         f'— expected if this PR adds pins; the sweep republishes Monday')
            ok('counts:counts.json checked (warning-only)')
    except Exception:
        pass  # pre-first-sweep state: the branch does not exist yet


def check_log_hygiene():
    print('--- findings-log hygiene ---')
    date_dir = re.compile(r'^\d{4}-\d{2}-\d{2}-')
    dirs = [d for d in glob.glob('findings-log/*/')
            if date_dir.match(os.path.basename(d.rstrip('/')))]
    banned = {'.har', '.warc', '.warc.gz', '.cdx', '.cdxj',
              '.gz', '.zip', '.tar', '.tgz', '.7z'}
    for d in dirs:
        name = os.path.basename(d.rstrip('/'))
        fm = os.path.join(d, 'FINDINGS.md')
        if not os.path.exists(fm):
            fail(f'{name}: no FINDINGS.md — a raw pass needs its accounting next to the capture')
            continue
        t = read(fm)
        cap = re.search(r'\b(\d+)\s+of\s+a\s+(\d+)\s+cap', t) or \
              re.search(r'\bTotal\s+(\d+)\s+of\s+a\s+(\d+)\s+cap', t)
        if not cap:
            fail(f'{name}/FINDINGS.md: no "N of an M cap" accounting')
            continue
        used, limit = int(cap.group(1)), int(cap.group(2))
        if used > limit:
            fail(f'{name}: accounts for {used} of a {limit} cap — accounting exceeds its own cap')
        if not re.search(r'≥\s*[\d.]+\s*s|[\d.]+\s*s\s*(?:apart|between|spacing)', t):
            fail(f'{name}/FINDINGS.md: no inter-request delay stated')
        if not re.search(r'\b(GET|OPTIONS|POST)\b', t):
            fail(f'{name}/FINDINGS.md: no methods stated')
        rows = 0
        rj = os.path.join(d, 'results.jsonl')
        if os.path.exists(rj):
            rows = sum(1 for line in read(rj).splitlines() if line.strip())
        if rows > used:
            fail(f'{name}: results.jsonl has {rows} rows, FINDINGS.md accounts for {used}')
    for f in glob.glob('findings-log/**/*', recursive=True):
        if os.path.splitext(f)[1] in banned:
            fail(f'{f}: raw archive capture — AGENTS.md §7 forbids committing these')
        elif os.path.isfile(f) and os.path.getsize(f) > 1_048_576:
            fail(f'{f}: >1MiB')
    ok(f'{len(dirs)} dated log dir(s) carry their accounting; no archive captures')
    if not dirs:
        ok('no dated log dirs at this commit (pre-rule logs excepted)')


def check_priorities_sync():
    print('--- priorities sync ---')
    open_ = set(re.findall(r'^###\s+([A-Z])\.\s',
                           read('docs/11-suggested-research-areas.md'), re.M))
    # "Closes docs/11… area C" but not "does not close area C" (the
    # negation lookbehinds are fixed-width, so both are valid regexes).
    close_re = re.compile(
        r'(?<!not )(?<!does not )\bCloses\s+`?docs/11(?:-suggested-research-areas)?'
        r'(?:\.md)?`?\s+areas?\s+([A-Z](?:\s*(?:,|and|/|&)\s*[A-Z])*)')
    violations = 0
    for f in glob.glob('findings-log/**/*.md', recursive=True):
        for i, line in enumerate(read(f).splitlines(), 1):
            if '<!-- priorities-sync: ignore -->' in line:
                continue
            m = close_re.search(line)
            if not m:
                continue
            for a in re.split(r'\s*(?:,|and|/|&)\s*', m.group(1).strip()):
                if a in open_:
                    fail(f'{f}:{i} declares area {a} closed, but '
                         f'docs/11 still lists "### {a}." as open — close it into the '
                         f'Closed areas table (or add <!-- priorities-sync: ignore --> '
                         f'for a partial closure, saying why)')
                    violations += 1
    if not violations:
        ok('no findings-log closure contradicts docs/11')


def check_prompt_parity():
    """The session rules live in several places; the wiring between them must
    not silently drift. This check is interface-based, not verbatim: prompts
    for different tasks (verify, drift, regenerate, submit) carry different
    rules by design, so demanding identical invariants in each would either
    fail or bloat every prompt with rules that don't apply to it.

    What is enforced:
    1. Every .github/prompts/*.md cites AGENTS.md (the canonical rules) —
       no prompt may send an agent probing without the house rules.
    2. The loop contract agrees: loop-close-areas.prompt.md and
       research-loop.sh build_prompt() must carry the same Loop report keys
       (ITERATION / REQUESTS_USED / AREAS_OPEN / STOP / NOTES) — the shell
       parses those keys out of the report, so a renamed key silently breaks
       budget accounting. CONTRIBUTING Prompt B's report block is held to the
       same keys.
    """
    print('--- prompt parity ---')
    report_keys = ['ITERATION:', 'REQUESTS_USED:', 'AREAS_OPEN:', 'STOP:', 'NOTES:']
    loop_parties = ['.github/prompts/loop-close-areas.prompt.md',
                    'scripts/research-loop.sh']
    for src in sorted(glob.glob('.github/prompts/*.md')):
        text = read(src)
        if 'AGENTS.md' not in text:
            fail(f'{src}: does not cite AGENTS.md — every prompt must point at the house rules')
    for src in loop_parties:
        if not os.path.exists(src):
            fail(f'{src}: loop contract party missing')
            continue
        text = read(src)
        for key in report_keys:
            if key not in text:
                fail(f'{src}: Loop report contract missing {key!r} — '
                     f'the shell parses these keys (research-loop.sh)')
    # CONTRIBUTING Prompt B carries the same report block; check its keys too.
    contrib = read('CONTRIBUTING-research.md')
    idx = contrib.find('### Prompt B')
    if idx >= 0:
        nxt = contrib.find('### Prompt C', idx)
        block = contrib[idx:nxt if nxt >= 0 else len(contrib)]
        for key in report_keys:
            if key not in block:
                fail(f'CONTRIBUTING-research.md Prompt B: report block missing {key!r} — '
                     f'must match research-loop.sh')
    else:
        fail('CONTRIBUTING-research.md: ### Prompt B missing — the loop prompt has no canonical source')
    ok('prompt wiring agrees (AGENTS cites + loop report contract)')


def check_append_only():
    """findings-log/ is append-only: additions free, deletions forbidden,
    modifications require a Correction section. AGENTS.md §3 allows appending
    a `## Correction (YYYY-MM-DD)` section inside an existing doc; anything
    else rewritten in place destroys the audit trail.
    """
    print('--- findings-log append-only ---')
    try:
        base = subprocess.run(['git', 'rev-parse', '--verify', 'origin/main'],
                              capture_output=True, text=True, timeout=10)
        if base.returncode != 0:
            ok('no origin/main — append-only check skipped (fail-closed gate scans --all)')
            return
        diff = subprocess.run(['git', 'diff', '--name-status', 'origin/main...HEAD',
                               '--', 'findings-log/'],
                              capture_output=True, text=True, timeout=10)
        if diff.returncode != 0 or not diff.stdout.strip():
            ok('no findings-log changes in this diff')
            return
        violations = 0
        for line in diff.stdout.splitlines():
            parts = line.split('\t', 1)
            if len(parts) != 2:
                continue
            status, path = parts
            if status.startswith('D'):
                fail(f'{path}: deleted — findings-log/ is append-only (AGENTS.md §3)')
                violations += 1
            elif status.startswith('M'):
                text = read(path) if os.path.exists(path) else ''
                if not re.search(r'^## Correction \(\d{4}-\d{2}-\d{2}\)', text, re.M):
                    fail(f'{path}: modified without a `## Correction (YYYY-MM-DD)` '
                         f'section — append a correction, do not rewrite in place')
                    violations += 1
        if not violations:
            ok('findings-log changes are append-only (additions + dated corrections)')
    except Exception as e:
        warn(f'append-only check skipped: {e}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--suite-log', default=None,
                    help='captured output of 05-public-config.check.sh, for the runtime count')
    args = ap.parse_args()

    check_numbers(args.suite_log)
    check_log_hygiene()
    check_priorities_sync()
    check_prompt_parity()
    check_append_only()

    print()
    if FAILED:
        print('CHECKS FAIL — see above. The counting rule is in this file\'s header.')
        return 1
    print('CHECKS PASS — numbers, log hygiene, priorities, prompts, and append-only all agree.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
