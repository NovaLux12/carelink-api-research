#!/usr/bin/env python3
"""project-row.py — turn one CDX response into one ledger row and one run.log line.

Modelled on `findings-log/2026-10-14-pool-l-ipro-hcp-census/project-row.py`, with
three fields this pass needs and area L did not:

  * `host_seq` — written explicitly (one host is in scope, so it equals `seq`;
    a reviewer recomputing the same-host spacing series must not have to infer it),
  * `crawl` — derived from the request path, **with the regex asserted to have
    matched** rather than defaulting to null (AGENTS.md section 6 item 3: a lookup
    that silently returns the wrong value is how this project has been wrong),
  * `attempt` / `is_failure` — so every retry is visibly a retry and every failure
    is visibly a failure, never an absence.

A row counts as a record only when the line parses as a JSON object carrying both
`url` and `timestamp` — a `404` body ("No Captures found for: …") parses as JSON
and must never be counted as a capture.
"""
import hashlib
import json
import os
import re
import sys

(ledger, runlog, seq, host_seq, role, host_tag, path, tag, hpath, bpath, code,
 t_queued, t_sent, t_done) = sys.argv[1:15]

raw = open(bpath, 'rb').read() if os.path.exists(bpath) else b''
txt = raw.decode('utf-8', 'replace')

# AGENTS.md section 7: never publish a session value. Marker + count, never the value.
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

# The crawl this row is about. ASSERTED, not defaulted: a null here would silently
# drop the row out of every per-crawl table this pass publishes.
#
# The id shape is the published one, NOT `CC-MAIN-<yyyy>-<ww>`: three of the 44
# out-of-window indexes are `CC-MAIN-2012`, `CC-MAIN-2008-2009` and
# `CC-MAIN-2009-2010`, and a `-<ww>`-only pattern fails on all three — which is
# area L's shipped `budget.py:crawl_of` pattern, and it drops them out of every
# per-crawl table rather than raising (AGENTS.md section 6 item 3).
m = re.match(r'^/(CC-MAIN-[0-9]{4}(?:-[0-9]+)?)-index\?', path)
crawl = m.group(1) if m else None
if crawl is None and role != 'inventory':
    raise SystemExit('project-row.py: role=%s path=%r does not match the crawl-id '
                     'pattern; refusing to write an uncategorised row' % (role, path))

# The query the row asked: `url=<q>&matchType=<mt>` — used by the reader to decide
# a row's cell from WHAT IT QUERIED, never from the free-text role (area L's S-L4).
mu = re.search(r'[?&]url=([^&]*)', path)
mm = re.search(r'[?&]matchType=([^&]*)', path)
query = mu.group(1) if mu else ''
match_type = mm.group(1) if mm else ''
# Whether this row named a host scope (matchType=host/prefix) or the whole domain.
scope = 'host' if match_type in ('host', 'prefix') else 'domain'

ipro, hosts, codes, paths_ipro = [], [], [], []
for r in recs:
    u = re.sub(r'jsessionid_[A-Za-z0-9_]+', '<JSESSIONID-REDACTED>', r.get('url', ''))
    if '/ipro/hcp/' in u:
        ipro.append('%s @%s status=%s' % (u, r.get('timestamp'), r.get('status', 'n/a')))
        paths_ipro.append(u)
    mh = re.search(r'//([^/]+)/', u)
    if mh:
        hosts.append(mh.group(1))
    if r.get('status'):
        codes.append(str(r['status']))

head = open(hpath, 'r', errors='replace').read() if os.path.exists(hpath) else ''


def hdr(name):
    mh = re.search(r'^%s:\s*(.*)$' % re.escape(name), head, re.I | re.M)
    return mh.group(1).strip() if mh else ''


disc = '|'.join(x for x in ['content-type: %s' % hdr('content-type'),
                            ('server: %s' % hdr('server')) if hdr('server') else '',
                            ('retry-after: %s' % hdr('retry-after')) if hdr('retry-after') else '',
                            ('x-amzn-errortype: %s' % hdr('x-amzn-errortype')) if hdr('x-amzn-errortype') else ''] if x)

# The counting rule, in code: 502/504/503/400 is a FAILURE, never an absence.
is_failure = code not in ('200', '301', '302', '404')

mre = re.search(r'-r(\d+)$', tag)
attempt = int(mre.group(1)) if mre else 0

row = {
    'seq': int(seq), 'host_seq': int(host_seq), 'host': 'index.commoncrawl.org',
    'host_tag': host_tag, 'method': 'GET', 'path': path, 'role': role,
    'crawl': crawl, 'query': query, 'match_type': match_type, 'scope': scope,
    'attempt_tag': tag, 'attempt': attempt,
    'http_status': code, 'is_failure': is_failure,
    'body_bytes': len(raw), 'body_sha256': hashlib.sha256(raw).hexdigest(),
    'disc_headers': disc,
    'records': len(recs), 'status_codes': codes[:20],
    'ipro_hcp': ipro[:60], 'ipro_count': len(ipro), 'ipro_paths': paths_ipro[:60],
    'all_paths': sorted({re.sub(r'^https?://[^/]+', '', u).split('?')[0]
                         for u in (r.get('url', '') for r in recs)})[:60],
    'minimed_hosts': sorted(set(hosts)),
    # Truncation detector (lane S6): a response whose byte count is an exact
    # multiple of 1024 was cut short, so every count here is a FLOOR.
    'truncation_boundary': bool(raw) and len(raw) % 1024 == 0,
    'jsessionid_redacted': n_js,
    'body_head': re.sub(r'\s+', ' ', txt_r)[:300],
    't_queued': t_queued, 't_sent': t_sent, 't_done': t_done,
}
with open(ledger, 'a') as f:
    f.write(json.dumps(row, sort_keys=True) + '\n')
with open(runlog, 'a') as f:
    f.write('\t'.join([seq, host_seq, role, host_tag, path, code, str(len(raw)),
                       str(len(recs)), str(len(ipro)), ','.join(sorted(set(hosts))),
                       t_queued, t_sent, t_done]) + '\n')