#!/usr/bin/env python3
"""measure-assertions.py — the ONE counting rule for this repo's assertion counts.

Usage:
  python3 scripts/measure-assertions.py            # prints "<static> <runtime>"
  python3 scripts/measure-assertions.py --json     # the counts.json the badge reads

THE COUNTING RULE
-----------------
This repo's badge, the gate's numbers check and the drift sweep's badge job
all read the number from here, because a number maintained in three places is
a number that will disagree with two of them. It already has: 93 was right
once and then silently wrong after two rounds of suite growth, a 195 appeared
from counting request lines, and a 95 from miscounting the loop's check site.
The rule is written down so the next person to add a pin changes the rule, the
number, and nothing else.

  static  = jsonpath/header predicates inside [Asserts] blocks across the four
            .hurl suites
          + `check "` sites in 05-public-config.check.sh
            (the site inside the 16-family loop counts ONCE — it is one site;
            it executes 16 times. That distinction is the trap.)

  runtime = hurl part + 2 x `HTTP` lines
              (hurl counts each status line as two asserts: version + code)
          + 05's executed assertions: non-loop check sites + the loop site x16
            + the 5 inline PASS branches
            (the live suite prints this as "<n> passed"; pass --observed-05
             with that number to use the measured value instead of the rule's)

LOOP-SITE DETECTION IS STRUCTURAL, NOT INDENTATIONAL (corrected 2026-10-12)
--------------------------------------------------------------------------
Until 2026-10-12 this rule counted a check site as a "loop site" if the line
started with whitespace:

    if line[0] in ' \t': loop_sites += 1

That used indentation as a proxy for "inside the 16-family loop". Indentation
is not that: it says the line is NESTED, not that it is nested *in a loop*.
Any `check` inside an `if`/`case` is nested too, and was therefore multiplied
by 16 when it runs exactly once.

Observed consequence: four checks added inside an `if`/`else` in 05 were counted
as 64 executed assertions instead of 4, so the derived runtime came out 64 too
high — `executed_05` 61 -> 125, runtime 359 -> 423, against the 363 the suite
actually printed. Both numbers were defensible on paper; 423 was the counting
rule's arithmetic and 363 was what 05 actually executed. The rule was wrong and
the live count was right.

The rule now tracks bash BLOCK STRUCTURE: it maintains a stack of open blocks,
and a check site is a loop site iff some enclosing block is a `for`/`while`/
`until` — not `if`, `case`, or a function body. Block openers, closers
(`done`/`esac`/`fi`) and `else`/`elif` re-opening are all indent-matched, so a
check inside an `if` nested in a loop is still a loop site, and a check inside
an `if` that is not in a loop is not.

**The counting rule changed and the reason is recorded here on purpose.** A rule
that silently reverts to indentation re-introduces exactly this miscount, and
`docs/09` section 4 already records the sibling defect class — a count the
gate's regex cannot see, passing while wrong.

`_loop_sites()` carries a self-test (`--self-test`) over synthetic shell shapes:
nested loops, loops inside conditionals, conditionals inside loops, `elif`/
`else` chains, `case`, `while`, two sibling loops, and a function body. Run it
after touching this function; a rule that cannot fail is worse than no rule
(docs/09 section 5).

KNOWN LIMIT — two constants remain hand-maintained (2026-10-12)
--------------------------------------------------------------
The STRUCTURAL fix above settles one question only: whether a `check "` site
sits inside a `for`/`while`/`until`. Two numbers about EXECUTION are still
hand-maintained constants, and a pass that adds either kind of construct must
re-derive both rather than trust them:

  1. `LOOP_FAMILY_SITES = 16` — the trip count of the family loop.
  2. `INLINE_05 = 7  # 5 from the pre-area-A suite + area A's 2 build-marker branches
               # (its `for spec in ...` loop asserts inline, so it adds 0 check
               #  sites and 0 loop sites — see the KNOWN LIMIT note above).` — how many assertions 05 runs OUTSIDE any `check "` site,
     counting the inline `PASS=$((PASS + 1))` branches at the top of the file
     and the shadow / sibling / family-map comparisons. At base that is 4
     literal sites executing 5 times (the sibling and family-map branches are
     single sites inside 2-iteration loops).

The error direction differs and matters to whoever hits it:
  - a stale `LOOP_FAMILY_SITES` OVER-counts (site counted 16x when it runs once);
  - a stale `INLINE_05` UNDER-counts (new inline branches execute but are not
    counted at all), and **under-counting is the dangerous direction** because
    a too-small number still looks like a plausible count and nothing fails.

**Area A's branch (`research/a-carelinkhp-region`) exercises (2), not (1).**
Verified against A's actual source, not inferred: its `for spec in ...` loop over
2 portal hosts contains **no `check "` site at all** — it asserts inline via
`PASS=$((PASS + 1))`, so **A adds zero check sites** (41 -> 41) and the loop
site this rule identifies on A's tree is still the 16-family loop, whose
multiplier of 16 is correct. **Treating A's loop correctly needs no rule change
at all**; only `INLINE_05` needs to go 5 -> 7 to account for A's two extra
inline executions (measured: `static 167`, `runtime 361`, matching A's own
figures — with `INLINE_05` left at 5 the same tree yields `runtime 359`).

(Earlier revision of this block, 2026-10-12, said A's loop was a second loop
site whose multiplier of 16 was "14 too high". That was wrong in both the
constant and the direction; it was corrected after being checked against A's
code. The verifier is not the reason — the claim was simply unverified.)

This is deliberately NOT auto-derived. Deriving trip counts and inline-execution
counts from shell source is a much harder problem than locating a site inside a
loop, and getting it half-right would be worse than a documented constant.
**Until it is derived, any pass that adds a loop or an inline PASS branch to
05 must update these two constants and re-run `--self-test`.** `--observed-05`
bypasses the whole derivation by using the live suite's own `N passed`, which
is why the gate prefers it whenever a suite log is present.
"""

import argparse
import datetime
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HURL_DIR = os.path.join(ROOT, 'regression/hurl')
CONFIG_SUITE = os.path.join(HURL_DIR, '05-public-config.check.sh')

# The one inline assertion family in 05 that is not a `check "` call: the shadow
# grep, the two sibling 412 checks, and the two family-map hash comparisons
# (05-public-config.check.sh — see its own PASS/FAIL branches).
INLINE_05 = 7  # 5 from the pre-area-A suite + area A's 2 build-marker branches.
               # Its `for spec in ...` loop asserts inline, so it adds 0 check
               # sites and 0 loop sites — see the KNOWN LIMIT note above.
LOOP_FAMILY_SITES = 16


def _read(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        return fh.read()


_BLOCK_OPEN = re.compile(r'^(\s*)(for|while|until|case|if)\b')
_LOOP_OPEN = re.compile(r'^\s*(for|while|until)\b')
_BLOCK_REOPEN = re.compile(r'^(\s*)(else|elif)\b')
_BLOCK_CLOSE = re.compile(r'^\s*(done|esac|fi)\b')
_CHECK_SITE = re.compile(r'^\s*check\s+"')

# `loop_sites` counts DISTINCT check SITES that sit inside a loop, so two check
# sites in one loop are 2 (each executes per iteration) — not 1 and not 2
# executions. `measure()` then multiplies by LOOP_FAMILY_SITES once, which is
# correct only because 05 has exactly one loop over the 16 families and no
# other multi-iteration loop; `self_test` asserts that shape.


def _loop_sites(lines):
    """Count check sites that are lexically inside a `for`/`while`/`until`.

    Structural, not indentational — see the header. Returns the count of such
    sites. Block nesting is tracked with an explicit stack, indent-matched on
    both open and close, so an `if` inside a loop still counts and an `if`
    outside one does not.
    """
    stack = []          # list of (indent, kind) with kind in {'loop','if','case'}
    n = 0
    for line in lines:
        rm = _BLOCK_REOPEN.match(line)
        if rm:
            # `else`/`elif` re-opens the nearest `if` at the same indent.
            ind = len(rm.group(1))
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == ind and stack[i][1] == 'if':
                    stack[i:] = [(ind, 'if')]
                    break
            continue
        cm = _BLOCK_CLOSE.match(line)
        if cm:
            ind = len(line) - len(line.lstrip())
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == ind:
                    del stack[i:]
                    break
            continue
        m = _BLOCK_OPEN.match(line)
        if m:
            ind = len(m.group(1))
            kind = 'loop' if _LOOP_OPEN.match(line) else m.group(2)
            while stack and stack[-1][0] >= ind:
                stack.pop()
            stack.append((ind, kind))
            continue
        if _CHECK_SITE.match(line) and any(k == 'loop' for _, k in stack):
            n += 1
    return n


# Synthetic shell shapes with the expected loop-site count. The indentation
# rule gets several of these wrong, which is the whole reason the rule changed;
# they are kept so a later edit cannot quietly revert to it. Expectations count
# DISTINCT sites inside a loop.
_SELF_TEST_CASES = [
    ('for loop, one site', 'for f in a b; do\n  check "x" "y" z\ndone', 1),
    ('if/else is not a loop', 'if [ -s f ]; then\n  check "x" "y" z\nfi', 0),
    ('if/else/else', 'if a; then\n check "x"\nelse\n check "y"\nfi', 0),
    ('elif chain', 'if a; then\n check "1"\nelif b; then\n check "2"\nfi', 0),
    ('if/elif/else', 'if a; then\n check "1"\nelif b; then\n check "2"\n'
                     'else\n check "3"\nfi', 0),
    ('case is not a loop', 'case $x in\n a)\n  check "c"\n ;;\nesac', 0),
    ('while loop', 'while read l; do\n  check "w"\ndone', 1),
    ('loop inside if', 'if a; then\n for f in x; do\n  check "p"\n done\nfi', 1),
    ('if inside loop', 'for f in a b; do\n if [ -n "$f" ]; then\n  check "q"\n'
                      ' fi\ndone', 1),
    ('if/else inside loop', 'for f in a; do\n if x; then\n  check "r"\n else\n'
                            '  check "s"\n fi\ndone', 2),
    ('two sibling loops', 'for a in x; do\n check "1"\ndone\nfor b in y; do\n'
                          ' check "2"\ndone', 2),
    ('loop then if outside', 'if a; then\n check "z"\nfi\nfor g in a; do\n'
                             ' check "y"\ndone', 1),
    ('loop then if/else inside', 'for f in a; do\n check "L"\n if x; then\n'
                                 '  check "I"\n else\n  check "E"\n fi\ndone', 3),
    ('function body is not a loop', 'f() {\n check "z"\n}', 0),
    ('loop inside function', 'f() {\n for g in a; do\n  check "n"\n done\n}', 1),
    ('no blocks at all', 'check "top" "f" expected\n', 0),
]


def self_test(verbose=True):
    """Exercise _loop_sites against synthetic shapes. Returns a failure list.

    Also asserts the property the indentation rule violated: a check nested in
    an `if`/`case` OUTSIDE any loop must not be counted, while one nested in an
    `if` INSIDE a loop must be. That single contrast is the whole bug.
    """
    failures = []
    for name, src, want in _SELF_TEST_CASES:
        got = _loop_sites(src.splitlines())
        if got != want:
            failures.append(f'{name}: want {want}, got {got}')
        elif verbose:
            print(f'  ok   {name} ({got})')

    # The discriminating pair, stated as the invariant it is.
    outside = 'if [ -s f ]; then\n  check "x" "f" e\nfi'
    inside = 'for f in a; do\n if [ -n "$f" ]; then\n  check "x" "f" e\n fi\ndone'
    if _loop_sites(outside.splitlines()) != 0:
        failures.append('indented-but-not-looped check was counted as a loop site')
    elif verbose:
        print('  ok   INVARIANT: indented-not-looped is 0')
    if _loop_sites(inside.splitlines()) != 1:
        failures.append('indented-inside-loop check was NOT counted as a loop site')
    elif verbose:
        print('  ok   INVARIANT: indented-inside-loop is 1')
    return failures


def measure(root=ROOT, observed_05=None):
    """Return a dict of measured counts. `observed_05` is the "<n> passed"
    line from a live 05 run; when given it replaces the derived rule for 05."""
    predicates = http_lines = 0
    per_suite = {}
    for f in sorted(glob.glob(os.path.join(root, 'regression/hurl/*.hurl'))):
        in_asserts = False
        p = h = 0
        for line in _read(f).splitlines():
            s = line.strip()
            if re.match(r'^\[[A-Za-z]+\]$', s):
                in_asserts = (s == '[Asserts]')
                continue
            if in_asserts and (s.startswith('jsonpath ') or s.startswith('header ')):
                p += 1
            if s.startswith('HTTP '):
                h += 1
        per_suite[os.path.basename(f).replace('.hurl', '')] = p
        predicates += p
        http_lines += h

    suite_lines = _read(os.path.join(root, 'regression/hurl/05-public-config.check.sh')).splitlines()
    sites = sum(1 for line in suite_lines if _CHECK_SITE.match(line))
    loop_sites = _loop_sites(suite_lines)
    per_suite['05-public-config'] = sites

    derived_05 = (sites - loop_sites) + LOOP_FAMILY_SITES * loop_sites + INLINE_05
    executed_05 = observed_05 if observed_05 is not None else derived_05
    static = predicates + sites
    runtime = (predicates + 2 * http_lines) + executed_05
    return {
        'static': static,
        'runtime': runtime,
        'predicates': predicates,
        'http_lines': http_lines,
        'check_sites': sites,
        'loop_sites': loop_sites,
        'executed_05': executed_05,
        'executed_05_derived': derived_05,
        'suites': per_suite,
    }


def counts_json(m, run_url='', commit=''):
    return {
        'generated_utc': datetime.datetime.now(datetime.timezone.utc)
                                .strftime('%Y-%m-%dT%H:%M:%SZ'),
        'run_url': run_url,
        'commit': commit,
        'assertions': {'static': m['static'], 'runtime': m['runtime']},
        'detail': {
            'predicates': m['predicates'],
            'http_lines': m['http_lines'],
            'check_sites': m['check_sites'],
            'loop_sites': m['loop_sites'],
            'executed_05': m['executed_05'],
            'suites': m['suites'],
        },
        'rule': ('static = predicates inside [Asserts] + check sites '
                 '(family-loop site counted once); runtime = predicates + 2xHTTP '
                 '+ 05 executed. See scripts/measure-assertions.py.'),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true',
                    help='print the counts.json the badge reads')
    ap.add_argument('--observed-05', type=int, default=None,
                    help="the '<n> passed' count from a live 05 run, if you have it")
    ap.add_argument('--self-test', action='store_true',
                    help='exercise _loop_sites against synthetic shell shapes '
                         'and exit non-zero on any failure')
    args = ap.parse_args()
    if args.self_test:
        fails = self_test(verbose=True)
        if fails:
            print('\nSELF-TEST FAILED:')
            for f in fails:
                print(f'  !! {f}')
            return 1
        print(f'\nself-test passed ({len(_SELF_TEST_CASES)} shapes)')
        return 0
    m = measure(observed_05=args.observed_05)
    if args.json:
        print(json.dumps(counts_json(
            m,
            run_url=os.environ.get('RUN_URL', ''),
            commit=os.environ.get('GITHUB_SHA', '')[:12]), indent=2))
    else:
        print(m['static'], m['runtime'])


if __name__ == '__main__':
    # sys.exit, not a bare call: `main()` returning 1 is useless if the return
    # value is discarded, and a self-test that reports failures while exiting 0
    # is a check that cannot fail — the exact defect class docs/09 §5 names.
    # Caught by running it, after noticing the shell reported 0 on a rule that
    # the same run had just printed eight failures for.
    sys.exit(main())