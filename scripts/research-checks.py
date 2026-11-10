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
  6. PROSE COUNTS — docs/11's "N open plus M closed" sentence must equal the
     heading count, the Closed-table row count and config.yml. The N+M=26
     clause was retired 2026-10-16 when the namespace widened past Z (AA,
     AB, … — see the page's own amendment); the total is unbounded again.
     Quoted history inside blockquotes is excluded.
  7. LOG CITES — cites inside findings-log/ must resolve, or carry a reasoned
     `allow-unresolved-cites` exemption. Findings-log files were previously
     read only as valid targets, never scanned as sources.
  8. LEDGER CENSUS — the committed-ledger population is derived from the tree
     (`git ls-files 'findings-log/*/results.jsonl'`), so no prose may state it
     without a commit anchor that RESOLVES and whose tree held that number.
     The bare figure is false one merge later; nothing derived it before, so
     area AA's ledger silently invalidated three hand-stated sites at once.

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

# A closed-area row in docs/11's Closed table. Hardened from the original
# `^\| [A-Z]{1,2} —` (exactly one space after the pipe): a verifier planted
# `|  ZQ — …` with two spaces above the heading and the guard passed green,
# because the predicate never matched it in the first place. The row was
# invisible to the count as well, so it would have been invisible to every
# reader of the page too. `\s+` on both sides accepts any spacing a human
# would read as a table row while still refusing prose that merely starts
# with a pipe.
CLOSED_ROW = r'^\|\s+[A-Z]{1,2}\s+—'
CLOSED_ROW_ID = r'^\|\s+([A-Z]{1,2})\s+—'


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
    # Area ids are one or two letters: A–Z, then AA, AB, … (widened 2026-10-16).
    areas = len(re.findall(r'^###\s+[A-Z]{1,2}\.\s', read('docs/11-suggested-research-areas.md'), re.M))
    areas_fail = False
    for i, line in enumerate(read('.github/ISSUE_TEMPLATE/config.yml').splitlines(), 1):
        m = re.search(r'about: (\d+) (?:open )?areas', line)
        if m and int(m.group(1)) != areas:
            fail(f'.github/ISSUE_TEMPLATE/config.yml:{i} states {m.group(1)} areas, '
                 f'measured {areas} (^### [A-Z]{1,2}. headings in docs/11)')
            areas_fail = True
    if not areas_fail:
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


def check_prose_counts():
    """docs/11 states its own open/closed count in prose — nothing else read it.

    The "N open plus M closed" sentence carries the page's own count, and it
    has drifted twice (area Z's log records the first; area M's correction the
    second) while every check stayed green, because check_numbers compares
    config.yml against the heading count and nothing compared the prose against
    either. This check parses the prose instead of the structure: every live
    (non-blockquote) "N open plus M closed" must equal the heading count, the
    Closed-table row count, and config.yml — whatever the total. The old
    N+M=26 clause ("every letter A–Z exactly once") was retired 2026-10-16 when
    the namespace widened past Z: ids are one or two letters (A–Z, then AA,
    AB, …), so the total is no longer capped at 26. Quoted history inside
    blockquotes is excluded: a correction quoting a past count is evidence, not
    a claim. Zero vendor requests — pure string analysis.
    """
    print('--- prose counts ---')
    text = read('docs/11-suggested-research-areas.md')
    areas = len(re.findall(r'^###\s+[A-Z]{1,2}\.\s', text, re.M))
    # The heading must be matched ANCHORED at line start, not by a bare string
    # split. `text.split('## Closed areas', 1)` also matches the same literal
    # inside a markdown table cell (docs/11 quotes the counting command in the
    # S-L2 duplicate-test table), so the split landed hundreds of lines early and
    # the count swept in every closed-looking row after that point — including a
    # row that had escaped the table entirely. That produced a FALSE GREEN on a
    # page whose Closed table was one row short and whose orphan row sat in
    # another area's prose. An anchored search cannot be fooled by a quoted
    # command; if the heading is missing it returns None and the check fails
    # closed rather than counting the whole file.
    m = re.search(r'^## Closed areas[ \t]*$', text, re.M)
    if m is None:
        fail('docs/11: no `## Closed areas` heading found at line start — the '
             'closed-area count cannot be derived, so the prose count is '
             'unverifiable (an unanchored split would silently count the whole '
             'file and pass)')
        return
    # A closed-area row must live INSIDE the table, not merely somewhere after
    # the heading. The failure this catches is real and was shipped: an `| AB —`
    # row was inserted into another area's prose, hundreds of lines ABOVE the
    # `## Closed areas` heading, while the Closed table itself was one row short.
    # The unanchored split counted it anyway (because the literal also appears in
    # a quoted command earlier in the page) and the page passed green with a row
    # in the wrong place. Anchoring alone would not catch it either, since the
    # orphan is simply outside the tail. So: count closed-shaped rows in the whole
    # file and require that count to equal the in-table count.
    in_table = len(re.findall(CLOSED_ROW, text[m.start():], re.M))
    whole_file = len(re.findall(CLOSED_ROW, text, re.M))
    if whole_file != in_table:
        orphan_ids = sorted(set(re.findall(CLOSED_ROW_ID, text, re.M))
                            - set(re.findall(CLOSED_ROW_ID, text[m.start():], re.M)))
        fail(f'docs/11: {whole_file - in_table} closed-area row(s) sit OUTSIDE the '
             f'Closed table ({orphan_ids}) — a closed row above the `## Closed areas` '
             f'heading is counted by no reader and reads as unstarted work; move it '
             f'into the table')
        return
    closed = in_table
    cfg = None
    for line in read('.github/ISSUE_TEMPLATE/config.yml').splitlines():
        m = re.search(r'about: (\d+) (?:open )?areas', line)
        if m:
            cfg = int(m.group(1))
    live = [(i, m) for i, line in enumerate(text.splitlines(), 1)
            if not re.match(r'\s*>', line)
            for m in re.finditer(r'(\d+) open plus (\d+) closed', line)]
    if not live:
        warn('docs/11: no live "N open plus M closed" prose — the page states '
             'no count for this check to read')
        return
    for i, m in live:
        n, c = int(m.group(1)), int(m.group(2))
        if (n, c) != (areas, closed):
            fail(f'docs/11:{i} states {n} open plus {c} closed, measured '
                 f'{areas} open + {closed} closed')
        elif cfg is not None and n != cfg:
            fail(f'docs/11:{i} states {n} open, but config.yml states {cfg}')
        else:
            ok(f'docs/11:{i} prose count {n} + {c} agrees with the page')


def check_findings_log_cites():
    """Cites inside findings-log/ must resolve — or say why they cannot.

    The gate's citation check scans docs/*.md + README.md + AGENTS.md as sources
    and reads findings-log/ only as valid targets, so a broken cite inside a raw
    pass is structurally invisible (area O's log documents the blind spot at
    length). This check scans findings-log/**/*.md as sources too: repo-root
    `findings-log/….md` cites must resolve against the tree, and bare
    `recon/|work/|recov/` cites resolve against the citing file's directory,
    then against findings-log/probe-2026-10-08/ (the legacy convention).
    A cite that dangles by policy — a capture AGENTS.md §7 forbids committing,
    prose about the check's own regex — is allowed only with a machine-readable
    exemption naming the reason, `<!-- allow-unresolved-cites: <path> — <reason>
    [; …] -->`. An exemption without a reason fails; an exemption for a path
    that resolves warns (stale). Zero vendor requests — pure string analysis.
    """
    print('--- findings-log citations ---')
    real = set(glob.glob('findings-log/**/*.md', recursive=True))
    abs_pat = re.compile(r'findings-log/[A-Za-z0-9._/-]+\.md')
    rel_pat = re.compile(r'(?<![\w./-])(?:recon|work|recov)/[A-Za-z0-9._-]+\.md')
    allow_pat = re.compile(r'<!--\s*allow-unresolved-cites:(.*?)-->', re.S)
    comment_pat = re.compile(r'<!--.*?-->', re.S)
    violations = 0
    for f in sorted(real):
        t = read(f)
        allowed = set()
        for m in allow_pat.finditer(t):
            for entry in m.group(1).split(';'):
                entry = entry.strip()
                if not entry:
                    continue
                pm = re.match(r'(\S+\.md)\s*(?:—|--)\s*(.+)', entry, re.S)
                if not pm or not pm.group(2).strip():
                    fail(f'{f}: malformed allow-unresolved-cites entry {entry!r} — '
                         f'write "<path> — <reason>"')
                    violations += 1
                    continue
                allowed.add(pm.group(1))
        body = comment_pat.sub('', t)
        cites = set(abs_pat.findall(body)) | set(rel_pat.findall(body))
        seen = set()

        def resolves(m):
            if '<' in m:
                return True
            if m.startswith('findings-log/'):
                return m in real
            d = os.path.dirname(f)
            return (os.path.normpath(os.path.join(d, m)) in real
                    or os.path.normpath(
                        os.path.join('findings-log/probe-2026-10-08', m)) in real)

        for m in sorted(cites):
            if '<' in m:
                continue
            seen.add(m)
            resolved = resolves(m)
            if resolved:
                if m in allowed:
                    warn(f'{f}: exemption for {m} is stale — the path resolves; '
                         f'remove it from allow-unresolved-cites')
                continue
            if m in allowed:
                continue
            fail(f'{f}: cites {m}, which resolves nowhere — fix the cite or add '
                 f'<!-- allow-unresolved-cites: {m} — <reason> -->')
            violations += 1
        for m in sorted(allowed - seen):
            if resolves(m):
                warn(f'{f}: exemption for {m} is stale — the path resolves; '
                     f'remove it from allow-unresolved-cites')
    if not violations:
        ok('all findings-log cites resolve or carry a reasoned exemption')


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
    open_ = set(re.findall(r'^###\s+([A-Z]{1,2})\.\s',
                           read('docs/11-suggested-research-areas.md'), re.M))
    # "Closes docs/11… area C" but not "does not close area C" (the
    # negation lookbehinds are fixed-width, so both are valid regexes).
    close_re = re.compile(
        r'(?<!not )(?<!does not )\bCloses\s+`?docs/11(?:-suggested-research-areas)?'
        r'(?:\.md)?`?\s+areas?\s+([A-Z]{1,2}(?:\s*(?:,|and|/|&)\s*[A-Z]{1,2})*)')
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


def check_ledger_census():
    """No prose may state the committed-ledger census without a commit it is true at.

    The census population is DERIVED FROM THE TREE — one item is one
    `findings-log/*/results.jsonl` — so it moves on every merge that adds a
    ledger (area AA's ledger moved it 50 → 51; PR #154 moved it again). A figure
    written by hand is therefore true at the head it was written on and false at
    the next, silently, because nothing derived it: the S-L4c block and the
    ledger-census row both restated `50` beside figures derived from it.

    This check derives the population with the census's own counting rule,
    `git ls-files 'findings-log/*/results.jsonl'`, and then, for every prose
    statement of the form "N committed ledgers", requires a commit anchor in the
    same paragraph that actually RESOLVES and whose tree really did contain N
    such files. Three failure shapes: no anchor (the bare figure — false one
    merge later by construction); an anchor that does not resolve; an anchor
    whose tree held a different number (a mis-transcribed reading, the
    S-L4c "36" class). The anchor is verified against the tree rather than
    trusted, which is what makes the figure self-deriving instead of merely
    footnoted.

    Scope: docs/ and README.md FAIL. findings-log/ only WARNS — that tree is
    append-only (AGENTS.md §3), so a stale figure in a comment there cannot be
    rewritten in place; it is superseded by a dated correction, and this check
    must not trap a lane between two rules. Blockquote BODIES are scanned, not
    skipped: the house form for stating a fresh census figure is a dated
    correction blockquote, so skipping `>` lines excluded the one place a new
    figure is most likely to be written — the distinction is enforced by the
    anchor requirement, not by refusing to look. Table ROWS are excluded, with
    or without a blockquote marker in front: a row is a reading, not a sentence,
    so `| committed ledgers | 50 | 51 |` is not a claim about 50. (That closing
    sentence was wrong on arrival rather than stale: `git log -S` shows both the
    sentence and the blockquote-scanning code landed together in a37f4df, so no
    revision ever had a docstring saying this while the code skipped `>` lines.
    It was never true here.) Zero vendor requests — `git ls-files`/`git ls-tree`
    only.
    """
    print('--- ledger census ---')
    def population_at(rev=None):
        if rev is None:
            out = subprocess.run(['git', 'ls-files', '--',
                                  'findings-log/*/results.jsonl'],
                                 capture_output=True, text=True, timeout=60)
        else:
            out = subprocess.run(['git', 'ls-tree', '-r', '--name-only', rev, '--',
                                  'findings-log/'],
                                 capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            return None
        return len([l for l in out.stdout.splitlines()
                    if re.fullmatch(r'findings-log/[^/]+/results\.jsonl', l.strip())])

    population = population_at()
    if not population:
        fail('ledger census: the counting rule `git ls-files '
             "'findings-log/*/results.jsonl'` named no files — no prose figure "
             'can be checked against it (wrong cwd, or the rule broke)')
        return

    # Figure-then-noun, allowing a connector between them (`=`, `is`, a dash,
    # a colon, a semicolon) — the shapes a person actually writes. Plus
    # noun-then-figure, which is the same claim in the other order.
    claim_pat = re.compile(
        r'(?<![\w.])([\d,]{1,5})\s*(?:[=\u2013\u2014:\-;]|\bis\b)?\s*'
        r'(?:committed|tracked)\s+ledgers?\b'
        r'|(?<![\w.])([\d,]{1,5})\s+committed\s+`?results\.jsonl`?\s+files?'
        r'|\b(?:committed|tracked)\s+ledgers?\b\s*(?:=|is|are|:)\s*([\d,]{1,5})\b')
    anchor_pat = re.compile(r'(?<![\w`/-])([0-9a-f]{7,40})(?![\w`/-])')
    para_break = re.compile(r'^\s*$|^\s*(?:#{1,6}\s|[|>]|[-*+]\s)')

    # A figure about a PART of the population is not a claim about the
    # population. "18 committed ledgers were refused" is a subset sentence: it
    # was never true or false as a census figure, so requiring it to match the
    # whole-tree count forces a truthful sentence to be rewritten and reports
    # "the population is 55" about a sentence that never claimed 55. Narrow by
    # design — an explicit partitive immediately before the figure, or a
    # past-tense verb immediately after it.
    subset_before = re.compile(r'(?:\bof\s+(?:the|these|those|which|them)\b|\bout\s+of\b)'
                               r'[^.]{0,24}$', re.I)
    subset_after = re.compile(r'^\s+(?:were|was|had|have|has|are\s+still)\b', re.I)

    def norm(line):
        """Strip markdown emphasis so `**50** committed ledgers` is a figure."""
        return re.sub(r'[*`_]', '', line)

    def in_fence(lines, i):
        """Is line i inside a fenced code block? A code sample is not a claim."""
        fence = False
        for line in lines[:i]:
            if line.lstrip().startswith('```'):
                fence = not fence
        return fence

    def paragraph(lines, i):
        """The enclosing paragraph, plus a correction blockquote directly below.

        The house form is to state the figure in the sentence and anchor it in
        the dated correction immediately under it (the S-L4c block does
        exactly this), so the anchor window has to include that block.
        """
        lo = i
        while lo > 0 and not para_break.match(lines[lo - 1]):
            lo -= 1
        hi = i
        while hi + 1 < len(lines) and not para_break.match(lines[hi + 1]):
            hi += 1
        win = lines[lo:hi + 1]
        j = hi + 1
        while j < len(lines) and (not lines[j].strip()
                                  or re.match(r'\s*>', lines[j])):
            win.append(lines[j])
            j += 1
        return [norm(l) for l in win]

    resolved_cache = {}

    def anchor_reading(sha):
        """The ledger population at `sha`, or None if the anchor is not a commit."""
        if sha not in resolved_cache:
            chk = subprocess.run(['git', 'cat-file', '-e', sha + '^{commit}'],
                                 capture_output=True, text=True, timeout=30)
            resolved_cache[sha] = population_at(sha) if chk.returncode == 0 else None
        return resolved_cache[sha]

    docs_sites = [p for p in ['README.md'] + sorted(glob.glob('docs/*.md'))
                  if os.path.exists(p)]
    log_sites = [p for p in sorted(glob.glob('findings-log/**/*.md', recursive=True))
                 if os.path.isfile(p) and os.path.getsize(p) <= 1_048_576]
    violations = stale = 0
    for path in docs_sites + log_sites:
        strict = path in docs_sites
        lines = read(path).splitlines()

        def scan_units(i):
            """The claim text for line i, joined across a hard wrap.

            A figure landing at end-of-line is the NORMAL shape in a file
            hard-wrapped at 80 columns, not a contrived one: matching a single
            line let `The census is **55**\\ncommitted ledgers` pass silently,
            which is the cheapest possible bypass. So the paragraph is joined
            before the figure is looked for.

            A blockquote is scanned as a BODY rather than skipped. Quoted
            history is evidence, but the house form for stating a NEW census
            figure is a dated correction blockquote — the S-L4c block — so
            skipping `>` lines excluded the one place a fresh figure is most
            likely to be written. The distinction is enforced by the anchor
            requirement, not by refusing to look.
            """
            lo = i
            while lo > 0 and not para_break.match(lines[lo - 1]):
                lo -= 1
            hi = i
            while hi + 1 < len(lines) and not para_break.match(lines[hi + 1]):
                hi += 1
            # Never let the joined window cross a fence: a census sentence
            # inside a code block is an example, and joining the surrounding
            # paragraph across the ``` boundaries made one look like prose.
            span = lines[lo:hi + 1]
            out_span, inf = [], False
            for l in span:
                if l.lstrip().startswith('```'):
                    inf = not inf
                    continue
                if not inf and not l.strip().startswith('|'):
                    out_span.append(l)
            joined = ' '.join(norm(l) for l in out_span)
            # A table row is a reading, not a sentence. The joined path drops
            # them above; the single-line unit needs the same guard, or
            # `> | committed ledgers | 50 | 51 |` matches noun-then-figure here.
            # A table row is a reading, not a sentence — with or without a
            # blockquote marker in front of it.
            own = '' if re.match(r'\s*>?\s*\|',
                                 re.sub(r'^\s*>\s?', '', line)) else norm(line)
            if re.match(r'\s*>\s*', line):
                # A blockquote, including LAZY CONTINUATION lines: markdown lets
                # a paragraph continue inside a quote without repeating `>`, so
                #   > The census is **94**
                #   committed ledgers.
                # is one quoted sentence. Joining only the contiguous `>` run
                # split it in half — the `>` line held no claim and the
                # continuation walked back to a `>` line and stopped. The run
                # therefore continues until a blank line or a new block marker.
                lo2 = i
                while lo2 > 0 and re.match(r'\s*>', lines[lo2 - 1]):
                    lo2 -= 1
                hi2 = i
                while hi2 + 1 < len(lines):
                    nxt = lines[hi2 + 1]
                    if not nxt.strip():
                        break
                    if re.match(r'\s*(?:#{1,6}\s|\||[-*+]\s|```)', nxt):
                        break
                    hi2 += 1
                body = [re.sub(r'^\s*>\s?', '', l) for l in lines[lo2:hi2 + 1]]
                # A table row inside the quote is a reading, not a sentence:
                # joining the quote's table let `committed ledgers | 50 | 51`
                # read as a claim about 50. Same exclusion the top-level scan
                # applies, applied after the `>` marker is stripped.
                body = [l for l in body if not l.strip().startswith('|')]
                joined = ' '.join(norm(l) for l in body)
            return [(own, i, i, lo), (joined, lo + 1, hi + 1, lo)]

        seen = set()   # per FILE: one paragraph is one claim, however many lines
        for i, line in enumerate(lines):
            if re.match(r'\s*\|', line):
                continue  # table row — quoted history, not a live prose claim
            if in_fence(lines, i):
                continue  # fenced code sample, not prose
            for text, lo_no, hi_no, para_start in scan_units(i):
                for m in claim_pat.finditer(text):
                    raw = m.group(1) or m.group(2) or m.group(3)
                    value = int(raw.replace(',', ''))
                    before = text[:m.start()]
                    after = text[m.end():]
                    if subset_before.search(before) or subset_after.match(after):
                        continue  # partitive, not a census claim
                    where = (f'{path}:{i + 1}' if para_start == i
                             else f'{path}:{lo_no}-{hi_no}')
                    # One paragraph is one claim. Join-matching finds the same
                    # figure from every line in the paragraph, so the key is the
                    # paragraph's FIRST line for both units — otherwise a
                    # wrapped paragraph reports once per line and the output is
                    # 28 warnings about one sentence.
                    key = (path, para_start, value)
                    if key in seen:
                        continue
                    seen.add(key)
                    readings = [(a, anchor_reading(a))
                                for a in anchor_pat.findall(' '.join(paragraph(lines, i)))]
                    readings = [(a, n) for a, n in readings if n is not None]
                    if not readings:
                        msg = (f'{where} states {value} committed ledgers with no '
                               f'resolving commit anchor beside it — the population is '
                               f'derived from the tree and is {population} at this head, '
                               f'so the figure is false one merge later; write '
                               f'"measured at `<sha>`" or state it as command output')
                    elif not any(n == value for _, n in readings):
                        anchors = ', '.join(f'{a}→{n}' for a, n in readings)
                        msg = (f'{where} states {value} committed ledgers, but its '
                               f'anchor(s) ({anchors}) did not hold that many; measured '
                               f'{population} at this head — re-derive, do not bump the '
                               f'figure')
                    else:
                        continue
                    if strict:
                        fail(msg)
                        violations += 1
                    else:
                        warn(msg + ' (findings-log/ is append-only — supersede with a '
                                   'dated correction, do not rewrite in place)')
                        stale += 1
    if not violations and not stale:
        ok(f'{population} committed ledgers at this head, derived; every prose '
           f'statement of the census is anchored to a commit that held it')
    elif not violations:
        ok(f'{population} committed ledgers at this head, derived; findings-log/ has '
           f'{stale} anchored-or-superseded statement(s) (warning-only, append-only tree)')


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
    check_prose_counts()
    check_findings_log_cites()
    check_log_hygiene()
    check_priorities_sync()
    check_prompt_parity()
    check_append_only()
    check_ledger_census()

    print()
    if FAILED:
        print('CHECKS FAIL — see above. The counting rule is in this file\'s header.')
        return 1
    print('CHECKS PASS — numbers, prose counts, log cites, log hygiene, priorities, prompts, the ledger census and append-only all agree.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
