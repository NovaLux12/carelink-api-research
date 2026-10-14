#!/usr/bin/env python3
r"""controls.py — prove every scrub net is live, and scan the COMMITTED tree.

WHY THIS IS A SEPARATE FILE, AND WHY IT IS NOT WHAT KEEPS THE GATE GREEN.
A control that fires a net, written into a file the net scans, IS a match for that
net. Two of them were, at `342c192`, and one of those was a live match for the
internal-host net.

The fragment-splitting below is good hygiene and is kept. It is **not** what makes
the gate green: `research-gate.sh` chooses its subjects with
`grep -E '\.(md|yml|yaml|sh|hurl)$'`, so **`.py` is excluded in `diff` mode and in
`--all` mode alike** and this file is never read by the gate at all. What makes the
gate green is simply that **no live match is written anywhere the gate reads** — in
this pass, 12 of 32 changed files. The other 21 added files, `results.jsonl`,
`run.log`, `grep-out.txt` and all 17 `headers/*.h`, are outside the gate's subject
filter entirely, and a future change to that filter would be a change in what is
checked, not in what is true.

THE RULE, which is the finding and not the mechanism:
    A correction that demonstrates a detector is live must not write a live match
    into any file that detector scans.

WHY THE CONTROLS ARE FRAGMENTS AND NOT INVENTED STRINGS. A control that does not
fire is ambiguous between "the net is dead" and "the control is wrong", and the
ambiguity always resolves the flattering way. Three of my first ten controls were
mis-shaped rather than the nets being dead — a missing 2-char group, 16 hex digits
where 17 were required (one of them not hex at all), and two labels where the regex
needs three plus a trailing dot. Each shape below is derived from the regex.

READS THE COMMITTED TREE, NOT THE WORKING TREE. The first version of this file took
a `ref` for the subject list and then read the files with `open()`. That is a false
clean with an exit code attached: run against `342c192`, whose committed
`FINDINGS.md` carries a live net-#5 match, it reported `TOTAL HITS: 0` and exited 0.
**An exit code that disagrees with the gate is worse than prose.** So every byte
scanned here comes from `git cat-file` at the requested ref, and a scan of an
arbitrary ref is a scan of that ref.

WHOLE-FILE, NOT ADDED-LINES. `research-gate.sh` builds its subject text from the
ADDED lines of a diff. This scanner reads whole files, which is strictly stronger:
`^`-anchored nets fire here on lines the gate would never see. The two can therefore
disagree in the safe direction only, and a disagreement the other way — this
scanner clean, the gate red — is the one to investigate.

ZERO requests. Nothing here touches the network.
"""

import re
import subprocess
import sys

SCRUB = 'scripts/scrub-patterns.txt'
GATE_EXTS = ('.md', '.yml', '.yaml', '.sh', '.hurl')   # research-gate.sh's own filter


def git(*args, binary=False):
    p = subprocess.run(['git', *args], capture_output=True)
    return p.stdout if binary else p.stdout.decode('utf-8', 'replace')


def patterns():
    """(name, regex) for every non-comment line of the one pattern list, AT ref."""
    out = []
    for line in git('show', f'{sys.argv[2] if len(sys.argv) > 2 else "HEAD"}:{SCRUB}').split('\n'):
        line = line.rstrip('\n')
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        name, _, pat = line.partition('|')
        if pat:
            out.append((name, pat))
    return out


def controls():
    """One control per net, assembled from fragments AT CALL TIME.

    Split so that no single line of this file, and no concatenation of adjacent
    fragments, matches the net it exercises. `grep` is line-oriented, so a value
    that would need to span the line break cannot match at all.
    """
    h = '0123456789abcdef'                      # 16 hex digits
    return {
        'vendor API key literal':
            '11IQOmW1' + 'Yr4z8T4kke' + 'ZJD5YbN4FS' + 'aWAQ4J5JpWi1',
        'reports-broker key fragments':
            '(0vJJl02' + 'ABCDEFGH1234',
        'reCAPTCHA site keys':
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
    pats, ctrls = patterns(), controls()
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
    """Compose every net with the COMMITTED tree at `ref`. This is what ships."""
    files = [f for f in git('diff', '--name-only', base, ref).split() if f]
    # research-gate.sh's own subject filter, applied to the same file list
    gate_subjects = [f for f in files if f.endswith(GATE_EXTS)]
    print(f"  changed files: {len(files)}   read by the gate's filter: "
          f"{len(gate_subjects)}   NOT read by it: {len(files) - len(gate_subjects)}")
    print(f"  content source: `git cat-file` AT {ref} (never the working tree)")
    hits, scanned = {}, []
    for f in gate_subjects:
        blob = git('cat-file', '-p', f'{ref}:{f}', binary=True).decode('utf-8', 'replace')
        scanned.append(f)
        for name, pat in patterns():
            n = len([l for l in blob.split('\n')
                     if not ('/home/<user>' in l and name == 'machine-specific paths')
                     and re.search(pat, l, re.I)])
            hits.setdefault(name, 0)
            hits[name] += n
    for name, _ in patterns():
        print(f"  {name:<50} {hits.get(name, 0)}")
    return hits, scanned


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else '7d915b8'
    ref = sys.argv[2] if len(sys.argv) > 2 else 'HEAD'
    print(f"=== base {base}   ref {ref}")
    print()
    print("=== 1. PROVE every net is live, on a control derived from its own regex")
    dead, unbuilt = prove()
    print(f"  nets with no working control: {dead or 'none'}")
    print(f"  nets with no control built:    {unbuilt or 'none'}")
    print()
    print("=== 2. SCAN the committed tree — composing the nets with the content")
    hits, _ = scan(base, ref)
    print()
    bad = {k: v for k, v in hits.items() if v}
    print(f"  TOTAL HITS: {sum(hits.values())}  -> {bad or 'CLEAN on every net'}")
    sys.exit(1 if (dead or unbuilt or bad) else 0)

