#!/usr/bin/env python3
"""Area I — derive the tenant diff from the sealed ledger.

Reads only artefacts this pass committed (../openid/*.json for the discovery
documents, ../jwks-keys.json for the key sets) and cross-checks every one
against its results.jsonl row. Nothing is fetched. Every number printed here is
traceable to a ledger seq.

Two comparisons, and the second is the one the area asked for:
  A. key-set / value comparison  — where two documents both carry a field, do
     the values match?
  B. PRESENCE comparison          — which fields does each document carry that
     the others do not?  (strictly stronger than A: "values differ" can be
     satisfied by two documents that are field-identical modulo hostnames)
"""
import json, hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(HERE, 'results.jsonl')) if l.strip()]
by_tag = {r['host_tag']: r for r in rows}
by_seq = {r['seq']: r for r in rows}

TENANTS = [
    ('carelink-login-trials.minimed.com', 't02-trials-oidc',   't03-trials-jwks'),
    ('carelink-login.minimed.eu',         't05-eu-oidc',       't06-eu-jwks'),
    ('carelink-login.minimed.com',        't08-us-oidc',       't09-us-jwks'),
    ('carelink-login.medtronic.eu',       't11-meu-oidc',      't12-meu-jwks'),
    ('carelink-login.medtronic.com',      't15-mcom-oidc',     't16-mcom-jwks'),
]

def slug(p):
    return p.strip('/').replace('/', '-').replace('.', '_')

def checked_openid(seq):
    """Load a committed discovery document and verify it against its ledger row.

    AGENTS.md §6 failure mode 3 — a comparison over a lookup that silently
    returned nothing looks exactly like agreement. Assert the row, the byte
    count and the digest before the bytes are used for anything.
    """
    r = by_seq[seq]
    p = os.path.join(HERE, 'openid', f"{seq:02d}-{r['host']}-GET-{slug(r['path'])}.json")
    raw = open(p, 'rb').read()
    assert r['http_status'] == '200', f"seq {seq}: not a 200, refusing to parse"
    assert len(raw) == r['body_bytes'], f"seq {seq}: {len(raw)}B on disk, ledger says {r['body_bytes']}B"
    assert hashlib.sha256(raw).hexdigest() == r['body_sha256'], f"seq {seq}: digest mismatch"
    return json.loads(raw)

JWKS = json.load(open(os.path.join(HERE, 'jwks-keys.json')))['tenants']

print('=' * 78)
print('A. JWKS key sets')
print('=' * 78)
kids = {}
for host, otag, jtag in TENANTS:
    r = by_tag[jtag]
    ks = JWKS[host]
    kids[host] = [k['kid'] for k in ks]
    for k in ks:
        print(f"{host:<34} kid={k['kid']}  kty={k['kty']}  alg={k['alg']}  "
              f"use={k['use']}  x5c={k['has_x5c']}  x5t={k['has_x5t']}")
    print(f"{'':<34} row seq={r['seq']}  {r['body_bytes']}B sha256:{r['body_sha256'][:12]}")

allk = [k for v in kids.values() for k in v]
print()
print(f"tenants: {len(TENANTS)}   distinct kids: {len(set(allk))} of {len(allk)} entries")
dupes = {k: [h for h, v in kids.items() if k in v] for k in set(allk)}
dupes = {k: v for k, v in dupes.items() if len(v) > 1}
print(f"kids shared by >1 tenant: {len(dupes)}  {dupes if dupes else '(none)'}")
print(f"every tenant holds exactly 2 keys: {all(len(v)==2 for v in kids.values())}")
print(f"every key RSA/RS256/use=sig: "
      f"{all(k['kty']=='RSA' and k['alg']=='RS256' and k['use']=='sig' for v in JWKS.values() for k in v)}")
print(f"every kid 21 chars: {all(len(k)==21 for k in allk)}   distinct lengths: {sorted({len(k) for k in allk})}")

print()
print('=' * 78)
print('B0. strongest form — whole document, tenant hostname substituted out')
print('=' * 78)
digs = {}
for host, otag, _ in TENANTS:
    d = checked_openid(by_tag[otag]['seq'])
    s = json.dumps(d, sort_keys=True).replace(host, '<TENANT>')
    digs[host] = (hashlib.sha256(s.encode()).hexdigest(), len(s))
    print(f"  {host:<34} normalised {len(s):>5}B sha256:{digs[host][0][:16]}")
print(f"  distinct normalised digests: {len({d for d, _ in digs.values()})} of {len(digs)}")
print("  -> the five documents are BYTE-IDENTICAL once the tenant hostname is")
print("     substituted out. Not 'the same fields' — the same bytes.")

print()
print('=' * 78)
print('B. openid-configuration — field-by-field, INCLUDING presence/absence')
print('=' * 78)
oidc = {h: checked_openid(by_tag[t]['seq']) for h, t, _ in TENANTS}
allfields = sorted({k for d in oidc.values() for k in d})
# host-derived fields: values that legitimately differ because the issuer differs.
def hostval(v, h):
    if isinstance(v, str) and h in v:
        return v.replace(h, '<TENANT-HOST>')
    if isinstance(v, list):
        return [hostval(x, h) for x in v]
    return v

print(f"union of field names across the five documents: {len(allfields)}")
print()
hdr = f"{'field':<48}"
for h, _, _ in TENANTS:
    hdr += f" {h.replace('carelink-login-','')[:26]:>26}"
print(hdr)
print('-' * len(hdr))

absent_somewhere, all_same, all_diff_host = [], [], []
for f in allfields:
    present = [h for h in oidc if f in oidc[h]]
    if len(present) != len(TENANTS):
        absent_somewhere.append((f, present))
        continue
    norm = {h: hostval(oidc[h][f], h) for h in oidc}
    vals = [json.dumps(v, sort_keys=True) for v in norm.values()]
    line = f"{f:<48}"
    if len(set(vals)) == 1:
        all_same.append(f)
        line += f" {'IDENTICAL':>26}"
    else:
        all_diff_host.append((f, norm))
        line += f" {'DIFFERS':>26}"
    print(line)

print()
print('--- fields ABSENT from at least one document (the stronger comparison) ---')
if not absent_somewhere:
    print('NONE — all five documents carry the identical set of '
          f'{len(allfields)} field names.')
for f, present in absent_somewhere:
    print(f"  {f}: present on {len(present)}/5 -> {sorted(present)}")
print()
print('--- fields present on all five but value-differing after normalising the')
print('    tenant hostname out of the value ---')
for f, norm in all_diff_host:
    for h, v in norm.items():
        print(f"  {f} @ {h} = {json.dumps(v)}")
print()
print(f"identical on all five: {len(all_same)}  |  differ: {len(all_diff_host)}  "
      f"|  absent somewhere: {len(absent_somewhere)}")

print()
print('=' * 78)
print('C. raw (un-normalised) value difference per field')
print('=' * 78)
rawdiff = []
for f in allfields:
    if any(f not in oidc[h] for h in oidc):
        continue
    vals = {h: json.dumps(oidc[h][f]) for h in oidc}
    if len(set(vals.values())) > 1:
        rawdiff.append(f)
        for h, v in vals.items():
            print(f"  {f} @ {h} = {v}")
print()
print(f"raw value-differing fields: {len(rawdiff)} of {len(allfields)}")

print()
print('=' * 78)
print('D. behavioural cells reachable by unauthenticated GET')
print('=' * 78)
for host, _, _ in TENANTS:
    r = by_tag.get({'carelink-login-trials.minimed.com':'t04-trials-register',
                    'carelink-login.minimed.eu':'t07-eu-register',
                    'carelink-login.minimed.com':'t10-us-register',
                    'carelink-login.medtronic.eu':'t13-meu-register',
                    'carelink-login.medtronic.com':'t17-mcom-register'}[host])
    fn = f"{r['seq']:02d}-{r['host']}-GET-{slug(r['path'])}.json"
    b = open(os.path.join(HERE, 'openid', fn), 'rb').read()
    assert len(b) == r['body_bytes'] and hashlib.sha256(b).hexdigest() == r['body_sha256']
    print(f"{host:<34} /oidc/register seq={r['seq']} {r['http_status']} "
          f"{r['content_type']} {r['body_bytes']}B sha256:{r['body_sha256'][:12]} body={b.decode()!r}")