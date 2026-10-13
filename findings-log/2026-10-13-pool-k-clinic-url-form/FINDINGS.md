# Pool K — clinic 224/225 denominator: static URL-form join key (id 2076)

**Date:** 2026-10-13
**Area:** K-residual (clinic half of "chunk corpus, for real this time")
**Host probed:** `carelinkhp.minimed.eu` (clinic portal)
**Probe mode:** read-only GET, no auth, no cookies
**Scheduling:** exclusive host lock `.loop/host-carelinkhp.minimed.eu.lock`; `sleep 2.5` held inside the lock before every request; lock released after response

## Request accounting

- **GET requests used: 4 of a 4 cap.** Cap not exceeded.
- **Methods:** GET only. No POST, no token exchange, no authentication.
- **Spacing:** 2.5 s sleep inside the lock before each request; measured `t_sent` gaps 2.660 s, 2.614 s, 2.617 s (all ≥ 2 s floor, all ≥ declared 2.5 s). Kernel body-write sizes are not used here; `t_sent`/`t_done` are millisecond timestamps from the harness.
- **Controls:** req 3 is a known committed clinic chunk (positive, `application/javascript`, 2224 B); req 4 is a certainly-absent name (negative twin, identical SHA256 to every other absent path, 5518 B `text/html`).
- **Transient bodies:** response bodies were read for discrimination and hashing, then deleted from the run scratchpad; only digests (not values) are committed. No raw archive capture is committed.

## Derived name under test

From the clinic bundle's webpack runtime (offline, zero vendor requests):

- manifest: `f.u = e => (2076===e?"common":e)+"."+{…,2076:"a62bb847b4ea289e",…}+".js"` [source: `findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md` §9 item 1; the manifest line itself is in the same offline artefact]
- id form that the committed 2026-10-08 `chunks.txt`-style list would use: `/2076.a62bb847b4ea289e.js`
- name form the runtime actually emits: `/common.a62bb847b4ea289e.js`

 (For the sibling patient build the same defect was measured in 2026-10-13 with hash `206e355a4a593fbd`: `common.206e355a4a593fbd.js` is live, `2076.206e355a4a593fbd.js` is 404 — see `findings-log/2026-10-13-area-k-patient-chunks/runtime-map.txt` lines 13–31.)

## Request ledger

All times UTC, millisecond resolution. `ct` = `Content-Type`, `ce` = `Content-Encoding`, `size` = decoded body bytes written by curl with `--compressed`.

| seq | path | t_queued | t_sent | t_done | status | content-type | size (B) | sha256(body) | body head (first 90 B) |
|---:|---|---|---|---|---:|---|---:|---|---|
| 1 | `/common.a62bb847b4ea289e.js` | 2026-10-13T21:55:08.790Z | 2026-10-13T21:55:11.306Z | 2026-10-13T21:55:11.425Z | 200 | `application/javascript` | 20731 | `b3de036cb88c5f4cab65d7ab2491034501844b8f83967947ba71a9b0ee24b549` | `"use strict";(self.webpackChunkpow=self.webpackChunkpow||[]).push([[2076],{1518:…` |
| 2 | `/2076.a62bb847b4ea289e.js` | 2026-10-13T21:55:11.458Z | 2026-10-13T21:55:13.966Z | 2026-10-13T21:55:14.486Z | 200 | `text/html; charset=UTF-8` | 5518 | `0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d` | `<!doctype html> …` (SPA shell) |
| 3 | `/12.cfb28fafc1fe9cf5.js` | 2026-10-13T21:55:14.741Z | 2026-10-13T21:55:16.580Z | 2026-10-13T21:55:16.660Z | 200 | `application/javascript` | 2224 | `16da534b3d91d4a78d3bf4510f9617e2a16303e5386af4d0272552db4f15283e` | `(self.webpackChunkpow=…).push([[12],{90012:…` |
| 4 | `/probe-absent-9f8e7d6c5b4a.js` | 2026-10-13T21:55:16.689Z | 2026-10-13T21:55:19.197Z | 2026-10-13T21:55:19.285Z | 200 | `text/html; charset=UTF-8` | 5518 | `0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d` | `<!doctype html> …` (SPA shell, byte-identical to req 2) |

Discriminating headers (all four responses):
- `server: Apache/2.4.62 (Red Hat Enterprise Linux) OpenSSL/3.5.5`
- `content-encoding: br` (brotli) on every response
- `cache-control: no-cache, must-revalidate`
- valid JS responses carry `content-type: application/javascript`; the SPA fallback carries `content-type: text/html; charset=UTF-8`, size 5518, and a constant `etag: W/"158e-659fa96cd58c0"` / `last-modified: Wed, 26 Aug 2026 22:17:47 GMT`
- req 2 and req 4 are byte-identical by SHA256, and their `content-type`/size match the documented SPA fallback exactly [source: `docs/09-methodology-and-oracles.md` §3, trap row].

## Findings

1. **OBSERVED — the emitted runtime name is live and is chunk 2076.** `GET /common.a62bb847b4ea289e.js` → 200 `application/javascript`, 20731 B, and its body begins `push([[2076], …` (req 1, SHA256 `b3de036c…`). The webpack chunk id that the manifest pairs with name `common` really is 2076, so the name substitution in `f.u` is not decorative.

2. **OBSERVED — the committed-list (id) form is NOT live on this host.** `GET /2076.a62bb847b4ea289e.js` → 200 `text/html`, 5518 B, SHA256 `0f2c5f62…`, byte-identical to the certainly-absent control (req 2 vs req 4). Discriminating on `Content-Type`, not status, the id form is the SPA fallback — i.e. **no such file exists under that name**.

3. **OBSERVED — the 2026-10-08 oracle holds on this host family.** The positive control `/12.cfb28fafc1fe9cf5.js` returns 200 `application/javascript` (req 3, 2224 B) and the certainly-absent name returns the SPA fallback (req 4, `text/html` 5518 B). So req 2's fallback verdict is genuine absence, not a host that returns HTML for everything.

4. **INFERRED (bounded) — the 2026-10-08 clinic corpus has one mis-addressed cell.** The 2026-10-08 sweep fetched "224 of a 225-entry map" with "one entry returned the SPA fallback" and never explained it (`findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md:13`; `docs/11-suggested-research-areas.md` K addendum). The evidence here is that the map entry for id 2076 must be requested as `common.<hash>.js`, exactly the way `f.u` emits it, or it reads as 5518 B of `index.html`. The 2026-10-08 pass requested it under its id (the same mistake the patient pass recorded) — **INFERRED because the clinic sweep's per-file ledger is not committed**, so the exact request string that produced the 5518 B cell cannot be recovered from disk. The inference is that one of the 224 recorded bodies is the SPA shell; the consequence for the published conclusions is limited: a 5518 B HTML page can only contribute false *hits*, not false *misses*, so the negatives survive and only the denominator (`224` chunks) is overstated by one in kind (223 JS chunks + 1 HTML page).

5. **OBSERVED — the join key is the hash, not the name.** Same SHA-less manifest entry `2076:"a62bb847b4ea289e"` resolves to two different URL strings depending on whether the name substitution in `f.u` is applied; the body (chunk 2076) is identical either way. This is the same "committed filename list is not a URL list" trap measured in the patient corpus [source: `docs/09-methodology-and-oracles.md` trap row; `docs/11-suggested-research-areas.md` K addendum; `findings-log/2026-10-13-area-k-patient-chunks/FINDINGS.md` §2].

## What this does not settle

- It does not re-fetch all 225 clinic entries under their `f.u` names. Only id 2076 is tested; the other 224 are assumed from the 2026-10-08 record, which has its own `f.u` substitution state unverified. Any claim about a *count* of cells therefore still rests on the 2026-10-08 sweep's uncommitted ledger.
- It does not overturn any "0 hits" negative from the clinic corpus. An HTML 5518 B body contains text that can only be mistaken for a hit, never a miss; req 2 and req 4 prove it is the shell, not a chunk.
- It does not close the whole K area. Only the `f.u` name-substitution defect for the clinic half is now measured; the control-flow mining that K proper asks for is untouched.

## Evidence map

| claim | class | source |
|---|---|---|
| clinic bundle manifest special-cases 2076 to name `common` with hash `a62bb847b4ea289e` | INFERRED (read from offline runtime artefact bundled with the probe; manifest verified structurally by the OBSERVED chunk id 2076 in req 1's body) | `findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md` §9 item 1, §2.2 (`uploader-instructions → r.e(2076)+r.e(342)`) |
| `/common.a62bb847b4ea289e.js` is live JS and is chunk id 2076 | OBSERVED | this log, req 1 (200 `application/javascript`, body head `push([[2076]`) |
| `/2076.a62bb847b4ea289e.js` is absent (SPA shell, byte-identical to control) | OBSERVED | this log, req 2 vs req 4 |
| status/content-type oracle on `carelinkhp.minimed.eu` | OBSERVED | this log, req 3 and req 4; `docs/09-methodology-and-oracles.md` §3 |
| same defect in patient corpus (common.206e… live, 2076.206e… 404) | OBSERVED | `findings-log/2026-10-13-area-k-patient-chunks/runtime-map.txt` lines 13–31; `findings-log/2026-10-13-area-k-patient-chunks/FINDINGS.md` §2 |
| 2026-10-08 clinic sweep's unexplained SPA-fallback cell | OBSERVED (the 5518 B fallback) + INFERRED (that it is the id-form request) | `findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md:13`; `docs/11-suggested-research-areas.md` K addendum |

## Gate-relevant accounting

- Cap: 4 of 4 used. No overrun.
- Request method: GET only.
- Host: `carelinkhp.minimed.eu`.
- Lock: `.loop/host-carelinkhp.minimed.eu.lock`, `sleep 2.5` inside the lock (measured `t_sent` gaps: 2.660 s, 2.614 s, 2.617 s; all ≥ 2 s and ≥ declared 2.5 s).
- No more vendor requests should be made against this name pair; both forms now carry a verdict.
