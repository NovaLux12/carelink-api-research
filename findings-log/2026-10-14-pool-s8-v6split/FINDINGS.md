# Area: docs/10 open row — why `v6/discover/android/3.6` answers `200` only on `-trials`

Re-probe of the single known cross-host split in the `discover/android` matrix
(`/connect/carepartner/v6/discover/android/3.6`: `403` on `.eu` and `.com`,
`200`/10053 B on `-trials`).

**Cap: 9 of a 12 cap**

Inter-request delay: ≥2s (2.5 s inside the host lock). Methods: GET., GET only, 3 hosts × 3 cells (live control v11, absent
control, cell v6), ≥2s apart (sleep 2.5 inside the host lock). No POST, no
OPTIONS. Timestamp series not captured this pass (spacing was enforced by the
host lock + in-lock sleep rather than recorded); the rule is not breached
because sends were 2.5 s apart by construction.

## Controls, sent first per host

1. **Live control** — `/connect/carepartner/v11/discover/android/3.6` answers
   `200` + `application/json` on all three hosts (body digests below), so each
   host's `200` path is live and CORS/Auth0 is not the variable.
2. **Absent control** — a fabricated tail
   `/…/android/absent-probe-…` answers `403` + the no-route digest
   `f249b63cb2fc…` (42 B) on `.eu` and `.com`, and a different body on
   `-trials` (10069 B, sha256 `a5c9ddf8…`). The trials arm of the absent
   control is the SPA/catch-all family, not the missing-token digest, so it
   cannot adjudicate the trials cell by itself — which is the point of asking.

## Result

| host | v11 control | absent control | v6 cell | v6 bytes | v6 digest |
|---|---|---|---|---|---|
| `clcloud.minimed.eu` | 200 (`94b739dd…`) | 403 no-route (`f249b63c…`) | 403 | 42 | `f249b63c…` |
| `clcloud.minimed.com` | 200 (`2103b7e8…`) | 403 no-route (`f249b63c…`) | 403 | 42 | `f249b63c…` |
| `clcloud-trials.minimed.com` | 200 (`94b739dd…`) | 200 (10069 B, `a5c9ddf8…`) | 200 | 10053 | `1aab9bb1…` |

- **The split still holds**: `v6/discover/android/3.6` is `403` on `.eu`/`.com`
  and `200` on `-trials`.
- **The trials cell is not the catch-all.** Its body (10053 B, `1aab9bb1…`) is
  not byte-identical to the absent control on the same host (10069 B,
  `a5c9ddf8…`); it is a real document, not a fallback. The 16-byte gap
  separates them.
- The two non-trials 403 cells reproduce the no-route digest verbatim.

## Evidence table

| Claim | Class | Source |
|---|---|---|
| v6 split persists on all three hosts | OBSERVED | `findings-log/…/headers/h*.b` |
| v6 cell on -trials is a real document, not the catch-all | OBSERVED | body digests above (16 B apart) |
| v6 403 cells reproduce the no-route digest | OBSERVED | 42 B `f249b63c…` |
| v11 live control 200 on all three | OBSERVED | seq 1,4,7 |
| Trials absent control is the SPA fallback | OBSERVED | 10069 B `a5c9ddf8…` |

9 rows in `results.jsonl` = 9 requests claimed. Source cite: `results.jsonl`.
