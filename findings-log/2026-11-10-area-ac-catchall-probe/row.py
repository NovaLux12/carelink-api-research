#!/usr/bin/env python3
"""row.py — one response -> one ledger row + one run.log line.

Commits a bounded projection only: status, content-type, bytes, sha256 and a short
redacted body_head (AGENTS.md section 7: a raw capture is never published).
"""
import hashlib
import json
import os
import re
import sys

seq, role, path, tag, hpath, bpath, code, tq, ts, td = sys.argv[1:11]
raw = open(bpath, 'rb').read() if os.path.exists(bpath) else b''
txt = raw.decode('utf-8', 'replace')
n_js = len(re.findall(r'jsessionid_[A-Za-z0-9_]+', txt))
txt_r = re.sub(r'jsessionid_[A-Za-z0-9_]+', '<JSESSIONID-REDACTED>', txt)
head = open(hpath, 'r', errors='replace').read() if os.path.exists(hpath) else ''


def hdr(name):
    m = re.search(r'^%s:\s*(.*)$' % re.escape(name), head, re.I | re.M)
    return m.group(1).strip() if m else ''


mre = re.search(r'-r(\d+)$', tag)
attempt = int(mre.group(1)) if mre else 0
row = {
    'seq': int(seq), 'host_seq': int(seq), 'host': 'carelink.minimed.eu',
    'method': 'GET', 'path': path, 'role': role, 'attempt_tag': tag, 'attempt': attempt,
    'http_status': code,
    # A 000/5xx/timeout is a FAILURE, never an absence.
    'is_failure': code not in ('200', '301', '302', '403', '404', '410'),
    'content_type': hdr('content-type'), 'content_length_hdr': hdr('content-length'),
    'body_bytes': len(raw), 'body_sha256': hashlib.sha256(raw).hexdigest(),
    'server': hdr('server'), 'raw_gzip': raw[:2] == b'\x1f\x8b',
    'truncation_boundary': bool(raw) and len(raw) % 1024 == 0,
    'jsessionid_redacted': n_js,
    'body_head': re.sub(r'\s+', ' ', txt_r)[:200],
    't_sent': ts, 't_done': td, 't_queued': tq,
}
with open('results.jsonl', 'a') as f:
    f.write(json.dumps(row, sort_keys=True) + '\n')
with open('run.log', 'a') as f:
    f.write('\t'.join([seq, role, path, code, row['content_type'] or '-',
                       str(len(raw)), row['body_sha256'][:16], ts, td]) + '\n')
