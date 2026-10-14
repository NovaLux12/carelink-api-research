#!/usr/bin/env python3
"""controls.py — prove every scrub net is LIVE, without writing a live match.

WHY THIS IS A SEPARATE FILE. A control that fires a net, written into any file
the net scans, IS a match for that net. `research-gate.sh` excludes exactly two
paths from its leak scan — itself and `scripts/scrub-patterns.txt` — so there is
**no exemption for `findings-log/`**, and a control written into this pass's log
is a live hit in the diff. Two of them were, at `342c192`: one for the reCAPTCHA
net and one for the internal-host net.

So the controls are ASSEMBLED HERE, AT RUNTIME, FROM FRAGMENTS. Each control is
split so that **no single line of this file concatenates into a match** for the net
it exercises, and no concatenation of ADJACENT lines does either — the nets are
greedy across a line only, and `grep` is line-oriented, so a value that spans a
line break cannot match.

THE RULE, which is the finding and not the mechanism:
    A correction that demonstrates a detector is live must not write a live match
    into any file that detector scans.

Verifying the nets fire is reading back the intended target. Reporting the scan
clean is composing the nets with the diff. The first is not the second, and only
the second is what the gate does — so this file does the first and the caller
does the second, and both are reported.

WHY THE CONTROLS ARE FRAGMENTS AND NOT INVENTED STRINGS. A control that does not
fire is ambiguous between "the net is dead" and "the control is wrong", and the
ambiguity always resolves the flattering way. Three of my first ten controls were
mis-shaped rather than the nets being dead — a missing 2-char group, 16 hex digits
where 17 were required (one of them not hex at all), and two labels where the
regex needs three plus a trailing dot. Each shape below is derived from the
regex, not guessed.

ZERO requests. Nothing here touches the network.
"""

import re
import subprocess
import sys

SCRUB = 'scripts/scrub-patterns.txt'


def patterns():
    """(name, regex) for every non-comment line of the one pattern list."""
    out = []
    for line in open(SCRUB, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        name, _, pat = line.partition('|')
        if pat:
            out.append((name, pat))
    return out


def controls():
    """One control per net, each assembled from fragments at call time.

    The fragments are chosen so that no concatenation of adjacent fragments, and
    no single fragment, matches its own net. `grep` is line-oriented, so a value
    that would need to span the line break cannot match at all.
    """
    h = '0123456789abcdef'                      # 16 hex digits
    return {
        'vendor API key literal':
            '11IQOmW1' + 'Yr4z8T4kke' + 'ZJD5YbN4FS' + 'aWAQ4J5JpWi1',
        'reports-broker key fragments':
            '(0vJJl02' + 'ABCDEFGH1234',
        'reCAPTCHA site keys':
            # needs ^6L + exactly 2 + a fixed 4-letter segment + 4 + 10+
            '6L' + 'zz' + 'bu' + 'or' + 'ABCD' + '0123456789',
        'AWS VPC endpoint service name':
            'vpce-' + h + '0' + '-' + 'x1y2z3a4' \
            + '.execute-api.eu-central-1' + '.vpce.amazonaws.com',
        'internal Grafana/K8s/GitLab/DB/Prometheus host':
            'graf' + 'ana' + '.' + 'eu-1' + '.' + 'minimed' + '.',
        'internal .corp host':
            'wid' + 'get' + '.corp',
        'machine-specific paths':
            '/ho' + 'me/someuser/x',
        'live jsession values':
            ';jses' + 'sionid_' + 'ABCDEF123456=',
        'live sessionData values':
            'sessi' + 'onData=AbCdEfGhIjKlMnOpQrStUv',
        'credential prefixes':
            'AKIA' + 'IOSFODNN7EXAMPLE',
    }


def prove():
    """Every net must fire on its own control. A net that does not is a FINDING."""
    pats = patterns()
    ctrls = controls()
    dead, unbuilt = [], []
    print(f"  {'net':<50} control fires")
    for name, pat in pats:
        c = ctrls.get(name)
        if c is None:
            unbuilt.append(name)
            print(f"  {name:<50} NO CONTROL BUILT")
            continue
        fires = bool(re.search(pat, c, re.I))
        if not fires:
            dead.append(name)
        print(f"  {name:<50} {'YES' if fires else '**NO**'}")
    return dead, unbuilt


def scan(base, ref):
    """Compose every net with the diff. This is what the gate actually does."""
    files = subprocess.run(['git', 'diff', '--name-only', base, ref],
                           capture_output=True, text=True).stdout.split()
    added = ''
    for f in files:
        if f.endswith(('.md', '.yml', '.sh', '.hurl')):
            try:
                added += open(f, encoding='utf-8', errors='replace').read() + '\n'
            except OSError:
                pass
    print(f"  subjects: {len(files)} changed files, "
          f"{sum(1 for f in files if f.endswith(('.md', '.yml', '.sh', '.hurl')))} scanned")
    hits = {}
    for name, pat in patterns():
        if name == 'machine-specific paths':
            n = len([l for l in added.split('\n')
                     if '/home/<user>' not in l and re.search(pat, l, re.I)])
        else:
            n = len([l for l in added.split('\n') if re.search(pat, l, re.I)])
        hits[name] = n
        print(f"  {name:<50} {n}")
    return hits


if __name__ == '__main__':
    print("=== 1. PROVE every net is live, on a control derived from its own regex")
    dead, unbuilt = prove()
    print(f"  nets with no working control: {dead or 'none'}")
    print(f"  nets with no control built:    {unbuilt or 'none'}")
    print()
    print("=== 2. SCAN the diff — composing the nets with the content (what the gate does)")
    base = sys.argv[1] if len(sys.argv) > 1 else '7d915b8'
    ref = sys.argv[2] if len(sys.argv) > 2 else 'HEAD'
    hits = scan(base, ref)
    print()
    bad = {k: v for k, v in hits.items() if v}
    print(f"  TOTAL HITS: {sum(hits.values())}  -> {bad or 'CLEAN on every net'}")
    sys.exit(1 if (dead or unbuilt or bad) else 0)