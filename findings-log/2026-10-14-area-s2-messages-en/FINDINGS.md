# Swarm lane S2 — what is in `/patient/configuration/messages/en` now?

Claim issue **#91** (lane S2, "headliner"). 2026-10-14. Successor to area F
successor 2.

**Total 6 of a 6 cap.** GET only — 6 GET, 0 POST, 0 OPTIONS, no
authentication, no token exchange, no cookie. **≥2.5 s between requests to the
same host** (`sleep 2.5` inside a per-host `flock`; three same-host pairs,
finish→start gaps 5.58–5.87 s). Three hosts:
`carelink.minimed.eu`, `carelink.minimed.com`,
`carelink-trials.minimed.com`. Ledger: `results.jsonl`, 6 rows, one per
request. Response bodies were consumed while in hand and removed; no raw
capture is committed (`AGENTS.md` §7).

---

## Deliverable — shape and byte size of `/patient/configuration/messages/en` across 3 deployments

**OBSERVED.** On all three deployments the route answers `200 application/json`
with a body of 22 bytes whose `sha256` is byte-identical
(`04868b50…cf227`, `results.jsonl` seq 2, 4, 6; headers in
`headers/*-msg.h`):

| | `.eu` | `.com` | `-trials` |
|---|---|---|---|
| status | `200` | `200` | `200` |
| content-type | `application/json` | `application/json` | `application/json` |
| body bytes | 22 | 22 | 22 |
| body digest | `04868b50…` | `04868b50…` | `04868b50…` |
| envelope members | `messages` | `messages` | `messages` |
| `messages` array length | **0** | **0** | **0** |

The envelope still contains exactly one member, `messages`, and the array is
empty on every deployment. There is no entry to characterise, so no translated
string, entry member list, or entry shape exists to publish.

**Canonicalisation (OBSERVED, derived in-process).** `jq -c` collapses the
22-byte body to `{"messages":[]}` (15 bytes; envelope canonical digest
`5e4ce7b3…`, `derived.json` seq 2/4/6). The 6-byte difference against the
2026-10-08 record of 16 bytes
([`CONFIG-NAMESPACE-DEEP.md`](../probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md)
line 90) is therefore **formatting on the same empty array** — not a content
change and not a new field. This re-measurement settles the earlier open
transport note: both byte counts describe the same empty envelope.

**Control (OBSERVED).** A positive control
`GET /patient/v2/configuration/public` was issued first on each host
(seq 1, 3, 5) and returned `200 application/json` on all three (26992 /
24479 / 31698 B, top-level key count 69 on every deployment, digests
`d68b6b57…` / `b0351f79…` / `bd4c69f9…`). The control proves the envelope
was live and readable unauthenticated in this same pass, and its digests
byte-match the 2026-10-13 `pool-f-config-host` record, so no drift is hidden
by a dead host.

---

## What this settles

- `/patient/configuration/messages/en` answers `200 application/json` on all
  three patient deployments, 22 bytes, digest `04868b50…`.
- Envelope member list is `["messages"]`; array length is 0 on all three.
- The 16 vs 22 byte delta is the same empty array rendered differently; the
  recorded 2026-10-08 16-byte value and the current 22-byte value agree on
  content.
- No translated string content exists to report; the array is empty.

## What this does not settle

Area F's own question — who calls `patient-timeline`, and can a third-party
client reach it — is **not** touched by this pass (pool-successor scope). F
stays open. This file supplies the shape confirmation successor 2 asked for.

## Controls actually sent (in order)

1. `GET /patient/v2/configuration/public` on `.eu` — 200 + `application/json`
   + 26992 B.
2. `GET /patient/configuration/messages/en` on `.eu` — 200 + `application/json`
   + 22 B; empty array.
3. Same control on `.com` — 200 + `application/json` + 24479 B.
4. Same candidate on `.com` — 200 + `application/json` + 22 B; empty array.
5. Same control on `-trials` — 200 + `application/json` + 31698 B.
6. Same candidate on `-trials` — 200 + `application/json` + 22 B; empty
   array.

Six requests, three hosts, GET only, no token, no other host touched. No raw
body is committed; only digests and derived shape facts survive by design.
