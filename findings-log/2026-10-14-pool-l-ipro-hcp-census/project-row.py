#!/usr/bin/env python3
"""project-row.py — turn one CDX response into one ledger row and one run.log line.

Written to `AGENTS.md` §4 / claim #126 step 4: project each response in code for
`/ipro/hcp/` members, redact any `jsessionid_…` to a marker **plus a count**, and
keep bodies out of the tree.

A row counts as a record only when the line parses as a JSON object carrying
both `url` and `timestamp` — a `404` body ("No Captures found for: …") parses as
JSON and must never be counted as a capture.
"""
import hashlib
import json
import os
import re
import sys

(ledger, runlog, seq, role, host_tag, path, tag, hpath, bpath, code,
 t_queued, t_sent, t_done) = sys.argv[1:14]

raw = open(bpath, 'rb').read() if os.path.exists(bpath) else b''
txt = raw.decode('utf-8', 'replace')

# AGENTS.md §7: never publish a session value. Marker + count, never the value.
n_js = len(re.findall(r'jsessionid_[A-Za-z0-9_]+', txt))
txt_r = re.sub(r'jsessionid_[A-Za-z0-9_]+', '<JSESSIONID-REDACTED>', txt)

recs = []
if code == '200':
    for line in txt.splitlines():
        line = line.strip()
        if not line.startswith('{'):
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if isinstance(r, dict) and 'url' in r and 'timestamp' in r:
            recs.append(r)

ipro, hosts, codes = [], [], []
for r in recs:
    u = re.sub(r'jsessionid_[A-Za-z0-9_]+', '<JSESSIONID-REDACTED>', r.get('url', ''))
    if '/ipro/hcp/' in u:
        ipro.append('%s @%s status=%s' % (u, r.get('timestamp'), r.get('status', 'n/a')))
    m = re.search(r'//([^/]+)/', u)
    if m:
        hosts.append(m.group(1))
    if r.get('status'):
        codes.append(str(r['status']))

head = open(hpath, 'r', errors='replace').read() if os.path.exists(hpath) else ''


def hdr(name):
    m = re.search(r'^%s:\s*(.*)$' % re.escape(name), head, re.I | re.M)
    return m.group(1).strip() if m else ''


disc = '|'.join(x for x in ['content-type: %s' % hdr('content-type'),
                            ('server: %s' % hdr('server')) if hdr('server') else '',
                            ('retry-after: %s' % hdr('retry-after')) if hdr('retry-after') else ''] if x)

row = {
    'seq': int(seq), 'host': 'index.commoncrawl.org', 'host_tag': host_tag,
    'method': 'GET', 'path': path, 'role': role, 'attempt_tag': tag,
    'http_status': code, 'body_bytes': len(raw),
    'body_sha256': hashlib.sha256(raw).hexdigest(),
    'disc_headers': disc,
    'records': len(recs), 'status_codes': codes[:20],
    'ipro_hcp': ipro[:40], 'minimed_hosts': sorted(set(hosts)),
    'jsessionid_redacted': n_js,
    'body_head': re.sub(r'\s+', ' ', txt_r)[:300],
    't_queued': t_queued, 't_sent': t_sent, 't_done': t_done,
}
with open(ledger, 'a') as f:
    f.write(json.dumps(row, sort_keys=True) + '\n')
with open(runlog, 'a') as f:
    f.write('\t'.join([seq, role, host_tag, path, code, str(len(raw)), str(len(recs)),
                       str(len(ipro)), ','.join(sorted(set(hosts))),
                       t_queued, t_sent, t_done]) + '\n')