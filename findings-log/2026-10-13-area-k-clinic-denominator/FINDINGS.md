# Area K — clinic 225 chunk denominator, body-verified

**Date:** 2026-10-13
**Area:** K residual (clinic half of the chunk corpus); issue #78
**Host probed:** `carelinkhp.minimed.eu` (clinic portal)
**Probe mode:** read-only GET, no auth, no cookies
**Scheduling:** exclusive host lock `.loop/host-carelinkhp.minimed.eu.lock`; inter-request delay ≥2.5 s (`sleep 2.5` held inside the lock before every request); lock released after response

## Request accounting

- **GET requests used: 225 of a 225 cap.** Cap not exceeded.
- **Methods:** GET only. No POST, no OPTIONS, no token exchange, no authentication.
- **Spacing:** 2.5 s sleep inside the lock before each request.
  - Harness `t_sent` series: 224 same-host gaps, min 1.727 s, 7 under 2.0 s, 19 under 2.5 s, 17 rows with negative `t_done - t_sent` — the recurring harness-clock defect; the `t_sent` readings are not authoritative.
  - Authority is the **kernel body-write mtimes** (set by curl `-o` at write time): 224 gaps, min 2.561 s, max 2.661 s, **0 under 2.5 s and 0 under 2.0 s**; mtime span 578.978 s agrees with the `t_sent` span (579.005 s) to 27 ms.
  - See `spacing.txt` for both series.
- **Controls (already pinned by the precursor, not re-run here):** id 12 `cfb28fafc1fe9cf5` → 200 `application/javascript` (positive); `probe-absent-9f8e7d6c5b4a` → 200 `text/html` 5518 B, SHA256 `0f2c5f62…` (negative). Their identity with the documented trap is recorded in `findings-log/2026-10-13-pool-k-clinic-url-form/FINDINGS.md` req 3 and req 4.
- **Transient bodies:** response bodies were read for discrimination and hashing, then left in the run scratchpad only; committed artefacts carry digests, not values. No raw archive capture is committed.

## Derived map (re-derived, hash-pinned)

Source: the clinic portal's own `runtime.a752bb828cca4b2c.js` webpack chunk loader, read from the same origin (`carelinkhp.minimed.eu`). Extracted construction:

```
f.u = e => (2076===e?"common":e)+"."+{12:"cfb28faf…", …, 2076:"a62bb847…", …, 9864:"4d4bad27…"}[e]+".js"
```

The full 225-entry map (id → hash, with the 2076 substitution applied) is committed as `runtime-map.txt`. The emitted filename under `f.u` is `common.<hash>.js` for id 2076 and `<id>.<hash>.js` for every other id.

## What was measured

Every one of the 225 map entries was requested under the name `f.u` emits, i.e. `<emitted-name>.<hash>.js` at the portal root. Discrimination is on `Content-Type`, never on status (the portal answers `200` for every unknown path): `application/javascript` is a chunk, `text/html` 5518 B is the SPA fallback.

Result: **225 of 225 entries resolve as `application/javascript`** (HTTP 200, distinct SHA256 digests, size range 78 B–492 635 B). **Zero entries return the 5518 B SPA fallback.**

| content-type | count |
|---|---:|
| `application/javascript` | 225 |
| `text/html` (SPA fallback, 5518 B) | 0 |

`results.jsonl` (seq 1–225) carries, per request: emitted path, `t_queued`/`t_sent`/`t_done`, status, `Content-Type`, decoded body size, SHA256 and a 90-byte body head. `headers/` holds each response head.

## Findings

1. **OBSERVED — the emitted runtime names are all live.** All 225 of the map entries resolve as `application/javascript` when fetched under the name `f.u` produces (seq 1–225; 225 distinct digests, no duplicates, no empty bodies). So `f.u` is not decorative: every emitted name corresponds to a committed chunk.
2. **OBSERVED — the 2076 substitution is the join-key trap's cause.** Id 2076 maps to `common.a62bb847b4ea289e.js`, which returns 200 `application/javascript`, 20 731 B, body head `push([[2076],…` (seq 57, SHA256 `b3de036c…`). The committed-list form `/2076.a62bb847b4ea289e.js` was already shown to return the 5518 B SPA fallback (pool K pass, 2026-10-13, req 2). The name moved; the hash did not.
3. **OBSERVED — the map size is 225, and all 225 are JS chunks.** The 2026-10-08 sweep fetched "224 of a 225-entry map" with "one entry returned the SPA fallback" (`findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md:13`) and never explained it. The unexplained entry is now identified: it was id 2076 fetched under its id rather than under `common`. Re-fetching under the emitted names produces 225 `application/javascript` bodies, so the SPA entry was mis-addressed. The honest reading is that the negative conclusions (0 Medtronic hosts, 0 `deviceFamily` tokens, 0 NGP alarm codes across the corpus) survive, since a 5518 B HTML page can only contribute false *hits*, not false *misses*; only the denominator/label is corrected (223 chunks + 1 HTML page was wrong — it is 225 JS chunks).
4. **OBSERVED — no duplicate or fallback body.** 225 distinct SHA256 digests, no empty body, no 5518 B body. So there is no collapse of multiple ids onto one asset and no second latent SPA entry.

## What this does settle

- The clinic half of K now has a body-verified denominator: **225 map entries, all of them `application/javascript`**, zero SPA fallback. The "0 of N" corpus statements can carry N = 225.
- The earlier "one entry returned the SPA fallback" is resolved as the id-vs-emitted-name defect already measured in the patient corpus and now reproduced here on the clinic runtime.

## What this does not settle

- The negative vocabulary/endpoint counts (0 Medtronic hosts, etc.) are restated with denominator 225; they were never re-mined corpus-by-corpus here — the mining was done 2026-10-08 and only its *denominator* is corrected.
- Control-flow mining over the call-sites (K proper) is untouched: what the 89 call-site field names do, and the state-dependent shape of `system.logbook.entry.validation.config`, is still open.

## Successor area added

See `docs/11-suggested-research-areas.md` (K sub-note). The control-flow pass remains the open K follow-up; this residual is closed as a denominator correction.

## Evidence map

| claim | class | source |
|---|---|---|
| 225-entry clinic manifest special-cases 2076 → name `common` with hashes | OBSERVED (extracted from the live portal runtime bundle on `carelinkhp.minimed.eu`) | `findings-log/2026-10-13-area-k-clinic-denominator/runtime-map.txt`; prior `findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md` §9 item 1 |
| emitted name for 2076 is `common.a62bb847b4ea289e.js` and resolves as chunk 2076 | OBSERVED | this log, results.jsonl seq 57 (200 `application/javascript`, 20 731 B, body head `push([[2076]`) |
| id-form name for 2076 returns the SPA fallback | OBSERVED | `findings-log/2026-10-13-pool-k-clinic-url-form/FINDINGS.md` req 2 vs req 4 |
| all 225 emitted names resolve as JS, 0 SPA | OBSERVED | this log, results.jsonl seq 1–225 |
| 2026-10-08 sweep recorded 224 of 225 with one 5518 B SPA cell | OBSERVED | `findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md:13` |
| inference that the unexplained 5518 B cell is id 2076 under its id | INFERRED (bounded) | supported by pool-K pass req 2 + the map structure; the 2026-10-08 per-file ledger is not committed |
| negatives (hosts/`deviceFamily`/NGP codes) survive the denominator correction | INFERRED, bounded on the corrected denominator | trap reading in `docs/09-methodology-and-oracles.md` (an HTML 5518 B page adds hits, never misses) |
