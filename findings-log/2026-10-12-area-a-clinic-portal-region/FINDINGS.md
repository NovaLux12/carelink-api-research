# Area A — is `carelinkhp` the clinician portal for every region?

**Pass date:** 2026-10-12 · **Claim issue:** [#21](https://github.com/NovaLux12/carelink-api-research/issues/21)
**Branch:** `research/a-carelinkhp-region` · **Ledger:** `results.jsonl` (20 rows, one per HTTP request) · **DNS:** `dns.jsonl` (8 rows, recorded separately)

## Verdict

**Negative on the region's existence, and positive on what actually splits the family.**
There is no `.com` variant of `carelinkhp`. Every `carelinkhp*.minimed.{eu,com}` name
outside the baseline is **NXDOMAIN**. The clinician-portal bundle is deployed on
**six hosts across two TLDs**, and the split is **product role (clinic vs support),
not region** — every `.eu`/`.com` pair measured serves the *same* build.

Two builds exist:

| Build | Entry document (5518 B) sha256 | Main asset | Asset size |
|---|---|---|---|
| **A — clinic / `pow`** | `0f2c5f6257a6fc6a…` | `main.fb5f8cb7eb60c4d5.js` | 3,397,615 B |
| **B — support / `cua`** | `f637c8d0cd4ec6bc…` | `main.759cddab23085086.js` | 3,410,666 B |

| Host | Build | Ledger row |
|---|---|---|
| `carelinkhp.minimed.eu` | A | seq 4 |
| `carelink.medtronic.com` | A | seq 8 |
| `carelink.medtronic.eu` | **A** | seq 19 |
| `carelink-support.medtronic.eu` | B | seq 15 |
| `carelink-support.medtronic.com` | B | seq 20 |

`carelinkhp-prod.minimed.eu` — the only `carelinkhp*` name in the corpus that had
**never been probed** — is **NXDOMAIN**, so `recon/JS-API-SURFACE.md` Q2 ("does the same
bundle [serve] from `carelinkhp-prod.minimed.eu`") has no host to answer on.

## Request accounting

**20 of a 20 cap.** GET only throughout — no POST, no `-X`, no `-d`, no token, no
authentication, no port scan, no DNS brute force. 8 DNS lookups are recorded in
`dns.jsonl` and are **not** counted against the cap: they are resolver traffic, not
requests to a vendor host, and no HTTP request was issued to any host that failed to
resolve.

**Declared delay: 2.5 s, sleep inside the per-host `flock`.** Measured from
`run.log`: **minimum consecutive same-host gap 2 s over 14 gaps; all 14 are ≥ the
BRIEF's 2 s hard floor, 10 of 14 are ≥ 2.5 s.** The four short readings are a
**logging-resolution artefact, not a short interval** — `run.log` timestamps have
one-second resolution against a 2.5 s declared delay, so a compliant 2.5 s sleep plus
a fast request lands anywhere in 2.4–2.9 s and truncates to 2 or 3. I did not capture
sub-second resolution, so I am not claiming 2.5 s was measured — I am claiming the log
**cannot resolve finer than 1 s** and never recorded a gap below the 2 s floor.

## Controls, in the order they were sent

Controls were sent **first on every host**, before any candidate.

1. **Certainly-absent path** — `GET /a-control-this-path-cannot-exist-2026-10-12`.
   *The same fabricated string was used on all five responding hosts, deliberately:*
   the fallback body is the question, so the fallback bodies have to be
   byte-comparable to each other and to each host's own root. A per-host nonce would
   have produced three incomparable rows.
   **What it proved:** the SPA catch-all is live on all five hosts, and — the result
   that changed the pass — **the catch-all is byte-identical to the host's own entry
   document** (seq 1≡3, 5≡7, 9≡11, 13≡14, 16≡17). So a document-path probe cannot
   distinguish "real portal" from "fallback" on this host family. See §Methodology.
2. **Known-live published config key** — `GET /hcp/configuration/public/pow.crm.settings`
   with `X-System-ID: ProWeb`. Chosen because it is a **published vendor key already
   pinned** in the regression suite (`regression/hurl/05-public-config.check.sh:98`),
   so "live here" is a recorded fact and not an assumption.
   **What it proved:** all three `.com`/`.eu` portal hosts return `200` for it — a
   parked page cannot answer that. It also produced the per-host CRM base (§5).

Every host passed both controls. **No stop condition fired**: the absent-path control
returned the expected fallback on every host, no host turned out to be in a
parked-wildcard space (`carelink.medtronic.*` is a Medtronic apex, not `*.carelink.*`),
and nothing resembling a credential, session value, internal hostname or patient
identifier appeared in any response.

## Findings

### 1. `carelink.medtronic.eu` **does** serve the bundle — `docs/01` and `docs/10` say it does not

`docs/01-hosts-and-estate.md:69` records `carelink.medtronic.eu` as "**does not**
serve that bundle — it returns the 5518-byte SPA fallback, md5-identical to the
`carelinkhp` trap page", and `docs/10-open-questions.md` §2 closes the question "Is
`carelink.medtronic.eu` a second portal deployment?" with "**No — false positive.**"

**Both are refuted (OBSERVED, seq 16–19).** Its entry document is byte-identical to
`carelinkhp.minimed.eu`'s — md5 `6aedf6c4004fbb29a298bc62128480be`, sha256
`0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d`, **the same value
the repo has recorded since 2026-10-08** — and when asked for the chunk **its own
document names**, it served `main.fb5f8cb7eb60c4d5.js` at **3,397,615 B,
sha256 `2a7fa8e7af519c2b`**, byte-identical to both other build-A hosts.

**The md5 half of the original claim was right and is re-anchored here** — I
independently reproduced `6aedf6c4004fbb29a298bc62128480be` from a live capture. It is
the **conclusion** drawn from it that was wrong.

The error is exactly §2 of this file: *the document **is** the catch-all*, so "returns
the 5518-byte fallback" was never evidence of absence. The host was classified as a
false positive because only the document was ever measured, and the document is
precisely the artefact that cannot answer the question. The `cmp`-identical evidence
that cleared `carelink.medtronic.com` existed on disk; the same test was never run on
`.eu`.

### 2. `carelink-support.medtronic.com` serves a **different build**, not "the same document"

`docs/07-admin-portal-and-reporting.md:24`, `docs/01-hosts-and-estate.md:68` and
`findings-log/probe-2026-10-08/SECURITY-FINDINGS.md` §S3 all record that
`carelink-support.medtronic.com` "serves the same document" as `carelinkhp.minimed.eu`.

**Refuted (OBSERVED, seq 9–12, 20).** Its entry document is a *different 5518-byte
document* — md5 `3e27b4df100cbc43ad6379d2517557fc`, sha256
`f637c8d0cd4ec6bc70944f7c9083ace6c205c5ecd22ce5da6ed533ece6d9a1bc` — and the only
difference from build A's document is the content-hashed chunk names:

```
build A: runtime.a752bb828cca4b2c.js   polyfills.e98da8d5da636e6e.js   main.fb5f8cb7eb60c4d5.js
build B: runtime.0c0212e340fbafc0.js   polyfills.e98da8d5da636e6e.js   main.759cddab23085086.js
```

Asking it for `main.fb5f8cb7eb60c4d5.js` returns the 5518 B catch-all (seq 12).
Asking it for `main.759cddab23085086.js` returns the real asset: **3,410,666 B,
sha256 `a054555a0f22176e`**, `content-type: application/javascript` (seq 20).

So `.com` support serves **build B**, and the host-name/labelling was right while the
"same document" claim was wrong.

### 3. `docs/08`'s digest is attached to the wrong artefact

`docs/08-security-findings.md` records that a host serves build B as
"`main.759cddab23085086.js`, sha256 `f637c8d0…`", and widens the S3 finding to "five
hosts".

**`f637c8d0…` is the sha256 of the 5518-byte entry document, not of the asset** (OBSERVED,
seq 11/14 vs seq 15/20). The asset `main.759cddab23085086.js` hashes to
`a054555a0f22176e…`. The build B *host* attribution in `docs/08` — `carelink-support.medtronic.eu`
— is **confirmed**: that host serves the identical document and the identical asset
(seq 13–15). But the digest recorded beside the asset name belongs to a different
file.

This is `AGENTS.md` §6.3 in the shape it warns about: a digest was carried forward
without asserting **which artefact was hashed**. The build-B host list in `docs/08` is
unchanged by this correction; only the digest's subject moves.

### 4. The region axis does nothing; the product axis is the split

Every `.eu`/`.com` pair measured serves the same build:

| Pair | `.eu` build | `.com` build |
|---|---|---|
| `carelink.medtronic.{eu,com}` | A (seq 19) | A (seq 8) |
| `carelink-support.medtronic.{eu,com}` | B (seq 15) | B (seq 20) |

So the answer to the area's title question — *is `carelinkhp` the clinician portal for
every region?* — is that **region is not a variable on this host family**. The one
thing that does vary is which product you are looking at (clinic `pow` vs support
`cua`), and both products are mirrored across both TLDs.

**INFERRED**, on the assumption that the bundle's published config names its own CRM
target correctly: the `base.uri` in `pow.crm.settings` tracks the **deployment**, not
the product (`.com` hosts, support included, all publish `carelink.medtronic.com/crm`).
This is one key on three hosts and no `cua.crm.settings` was probed, so it is offered as
a reading, not a finding.

### 5. `pow.crm.settings` differs by host — 96 B vs 97 B

| Host | Body |
|---|---|
| `carelinkhp.minimed.eu` (seq 2) | `{"base.uri":"https://carelink.medtronic.eu/crm","product":"pow","version":"4.5"}` — 96 B |
| `carelink.medtronic.com` (seq 6) | `{"base.uri":"https://carelink.medtronic.com/crm",…}` — 97 B |
| `carelink-support.medtronic.com` (seq 10) | `{"base.uri":"https://carelink.medtronic.com/crm",…}` — 97 B |

The single byte is `.eu` → `.com`. This is a **PUBLISHED** key served without a login,
and it is the only cell in this pass where the three hosts are *not* byte-identical —
which is itself the evidence that build A and build B are two deployments of one
product family rather than one deployment.

## Methodology correction — the 5518-byte discriminator does not work, for two separate reasons

`docs/09-methodology-and-oracles.md` §4 and `AGENTS.md` §7 both say to discriminate
the SPA fallback on `Content-Type`, "never on status", and `docs/09` adds "or the
exact 5518-byte size". **That advice is wrong in two ways this pass measured, and the
error is what produced Finding 1.**

1. **There is no document-path discriminator at all.** The catch-all *is* the entry
   document — seq 1≡3, 5≡7, 9≡11, 13≡14, 16≡17, all seven pairs byte-identical. The
   fallback and the real portal root are the same 5518 bytes. Any probe that measures
   only a document path cannot distinguish them, and `Content-Type` cannot help because
   both are `text/html`.
2. **Size is not a discriminator either.** 5518 B maps to **at least two distinct
   digests** — `0f2c5f6257a6fc6a…` (builds A hosts) and `f637c8d0cd4ec6bc…`
   (build B hosts). A host serving build B satisfies "5518 bytes" and is not the
   `carelinkhp` page.

**The discriminator that does work is an asset path**, and it works on three axes at
once: the catch-all answers an asset path with `content-type: text/html` and 5518 B,
while a real asset answers with `content-type: application/javascript` and its own
size. Measured both ways on `carelink.medtronic.eu`: build A's chunk → 3,397,615 B
`application/javascript`; build B's chunk → 5518 B `text/html`.

So the rule becomes: **ask for a content-hashed chunk that the host's own document
names**, and discriminate on `Content-Type` + size + digest together. Naming a chunk in
HTML is not serving it — which is why seq 20 exists, to verify the build B `.com` host
*serves* the chunk its document names rather than inferring it from the string
(`AGENTS.md` §6.2).

## What was searched and found empty

- **`carelinkhp-prod.minimed.eu`** — NXDOMAIN. The only `carelinkhp*` name in the corpus
  never probed; it appears only in archive queries that returned 0 rows
  (`recon/ARCHIVE-URLS.md:39,369`) and as open Q2 in `recon/JS-API-SURFACE.md:1162`.
- **`carelinkhp.minimed.com`**, **`carelinkhp-prod.minimed.com`** — NXDOMAIN,
  re-confirming `PROBE-FINDINGS.md:29`. `carelinkhp-trials.minimed.com` — NXDOMAIN,
  improving on `CONFIG-NAMESPACE-DEEP.md:254`'s `000 / TCP connect failed`: the resolver
  returns **NXDOMAIN**, so there was never an address to connect to.
- **`carelinkhp-test.minimed.eu`** — a `test` deployment (`docs/01:103`). **Recorded
  and not probed**, per `docs/09` §1's bar on dev/stage/test contact. Resolver lookup
  only.

No `.minimed.{eu,com}` host was probed that is not named in this repository before this
pass. No wordlist, no enumeration, no DNS brute force.

## Reproducing

```bash
bash findings-log/2026-10-12-area-a-clinic-portal-region/probe.sh    # batch 1, 12 requests
bash findings-log/2026-10-12-area-a-clinic-portal-region/probe2.sh   # batch 2, 6 requests
bash findings-log/2026-10-12-area-a-clinic-portal-region/probe3.sh   # batch 3, 1 request
bash findings-log/2026-10-12-area-a-clinic-portal-region/probe4.sh   # batch 4, 1 request
```

The four scripts exist because the pass changed shape mid-run: batch 2 was written after
batch 1 showed a `.com` host holding a digest `docs/08` attributed to a `.eu` host, and
batches 3 and 4 each test one inference the previous batch made. Bodies ≤ 100 KB are
committed under `headers/`; the two 3.4 MB bundle assets are deliberately **not**
committed, so their digests are reproducible only by re-fetching. `probe3.sh` exits
non-zero on an unset `RUNLOG` after its ledger row is written — the request and the row
are recorded; only the log append failed, and the row was appended by hand.

## Evidence table

| Claim | Class | Source |
|---|---|---|
| Build A served by `carelinkhp.minimed.eu` | OBSERVED | `results.jsonl` seq 4 |
| Build A served by `carelink.medtronic.com` | OBSERVED | `results.jsonl` seq 8 |
| **Build A served by `carelink.medtronic.eu`** — refutes `docs/01:69`, `docs/10` §2 | OBSERVED | `results.jsonl` seq 19 |
| Build B served by `carelink-support.medtronic.eu` | OBSERVED | `results.jsonl` seq 15 |
| Build B served by `carelink-support.medtronic.com` — refutes `docs/07:24`, `docs/01:68`, SECURITY-FINDINGS §S3 | OBSERVED | `results.jsonl` seq 20 |
| Catch-all ≡ host's own entry document, 7 of 7 host-pairs | OBSERVED | `results.jsonl` seq 1≡3, 5≡7, 9≡11, 13≡14, 16≡17 |
| 5518 B maps to ≥ 2 distinct digests | OBSERVED | `results.jsonl` seq 3 vs seq 11 |
| `docs/08`'s `f637c8d0…` is the document, not the asset (`a054555a…` is the asset) | OBSERVED | `results.jsonl` seq 14 vs seq 15 |
| Build A asset digest `2a7fa8e7af519c2b` reproduces the value recorded 2026-10-08 | OBSERVED | `results.jsonl` seq 4; `AUTH-TENANT-FINDINGS.md:248` |
| `carelinkhp` entry doc md5 `6aedf6c4004fbb29a298bc62128480be` reproduces the recorded value | OBSERVED | `headers/carelinkhp-minimed-eu-root.b`; `CONFIG-NAMESPACE-DEEP.md:264` |
| 5 × `carelinkhp*.minimed.{eu,com}` names NXDOMAIN | OBSERVED (DNS) | `dns.jsonl` |
| `pow.crm.settings` `base.uri` tracks TLD, not product | OBSERVED | `results.jsonl` seq 2, 6, 10 |
| `pow.crm.settings` is unauthenticated on all three | OBSERVED | `results.jsonl` seq 2, 6, 10 |
| Region is not a variable on this host family | INFERRED from the two pairs above | assumption: nothing is injected per-region at the edge; a `Content-Length`/`Vary` split would falsify it, and none was seen |
| The CRM base tracks deployment rather than product | INFERRED | one key, three hosts, no `cua.crm.settings` probed |

**Not established, and deliberately not claimed:** whether build B's `hcp/*` surface
differs from build A's (not probed — the area is bundle identity, not route parity);
whether any host outside this list serves either build (no enumeration was performed);
and whether `docs/08`'s S3 finding's "five hosts" count is right in total — this pass
measured five hosts but the finding's host list was not re-derived.