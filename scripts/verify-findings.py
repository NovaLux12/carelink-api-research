#!/usr/bin/env python3
"""verify-findings.py — the auto-verification hook on a green drift sweep.

Usage:
    python3 scripts/verify-findings.py --suite-green

What it does, and what it deliberately does not do
---------------------------------------------------
For every open issue labelled `needs-verification`, it finds which regression
assertions the issue references (by quoted `check "…"` label, by suite
filename, or by an explicit `<!-- pins: … -->` trailer) and, when the sweep
was green, moves the issue to `verified` + `pinned` with a comment saying
which sweep confirmed it.

It proves the *pinned value still holds* — nothing more. It cannot and does
not judge whether the finding's interpretation was right; that is the human
reviewer's (CONTRIBUTING-research.md, "What the gate checks"). If no pins are
found, it says nothing at all: silence beats noise, because a bot that
comments on everything is a bot humans learn to mute.

Never removes `verified`. A later drift opens a correction issue; silently
demoting a label would be the "never pick one silently" failure in AGENTS.md
section 2.

Requires `gh` and GH_TOKEN; without either it exits 0 with a note, so a local
run is harmless.
"""

import json
import os
import re
import subprocess
import sys

CONFIG = '05-public-config.check.sh'
SUITES = ['01-discovery-pin', '02-sso-oidc', '03-patient-api',
          '04-deep-surface', '05-public-config']


def sh(args, capture=True):
    return subprocess.run(args, capture_output=capture, text=True)


def inventory():
    """Stable assertion IDs: 05's check labels (the labels ARE names), and one
    suite-level ID per hurl suite. An issue that quotes a label maps exactly;
    a typo'd label maps to nothing rather than to the wrong assertion."""
    ids = set()
    try:
        with open(f'regression/hurl/{CONFIG}', encoding='utf-8') as fh:
            for line in fh:
                m = re.match(r'\s*check\s+"(.*?)"', line)
                if m:
                    ids.add(f'{CONFIG}::{m.group(1)}')
    except OSError:
        pass
    for s in SUITES:
        ids.add(f'{s}.hurl::suite')
    return ids


def extract_pins(body):
    """Assertion IDs an issue references. Precise shapes only."""
    pins = set()
    for m in re.finditer(r'`([^`]*check "[^`]+")`|`([^`]*\.hurl)`|`([^`]*check\.sh)`', body):
        text = next(g for g in m.groups() if g)
        for label in re.findall(r'check "([^"]+)"', text):
            pins.add(f'{CONFIG}::{label}')
        for suite in re.findall(r'([0-9]{2}-[a-z0-9-]+)\.hurl', text):
            pins.add(f'{suite}.hurl::suite')
    for trailer in re.findall(r'<!--\s*pins:\s*(.*?)\s*-->', body):
        for ident in trailer.split(';'):
            pins.add(ident.strip())
    return pins


def main():
    if '--suite-green' not in sys.argv:
        print('verify-findings: nothing to do (pass --suite-green after a green sweep)')
        return 0
    if not sh(['which', 'gh']).returncode == 0:
        print('verify-findings: gh not available; skipping')
        return 0
    if not os.environ.get('GH_TOKEN') and not os.environ.get('GITHUB_TOKEN'):
        print('verify-findings: no token; skipping')
        return 0

    ids = inventory()
    res = sh(['gh', 'issue', 'list', '--label', 'needs-verification',
              '--state', 'open', '--limit', '100', '--json',
              'number,title,body,url'])
    if res.returncode != 0:
        print('verify-findings: gh issue list failed; skipping')
        return 0
    issues = json.loads(res.stdout or '[]')
    moved = mentioned = 0
    for issue in issues:
        pins = extract_pins(issue.get('body') or '') & ids
        if not pins:
            continue
        mentioned += 1
        n = issue['number']
        body = (
            f"The weekly drift sweep is green: every pinned assertion this issue "
            f"references ({len(pins)} of them) still holds — see the sweep run for "
            f"the evidence. Moving `needs-verification` → `verified` (LABELS.md: "
            f"`verified` = independently reproduced by a second pass). This confirms "
            f"the pinned values, not the interpretation — that stays with the "
            f"reviewer.\n\nPins: " + ', '.join(f'`{p}`' for p in sorted(pins)))
        sh(['gh', 'issue', 'comment', str(n), '--body', body])
        sh(['gh', 'issue', 'edit', str(n), '--remove-label', 'needs-verification',
            '--add-label', 'verified,pinned'])
        moved += 1
    print(f'verify-findings: {mentioned} issue(s) referenced pins, {moved} moved to verified')
    return 0


if __name__ == '__main__':
    sys.exit(main())