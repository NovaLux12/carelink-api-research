# Area AZ — is the per-route `OPTIONS` resolution STABLE, and does a fabricated name at DEPTH 2 answer the same way?

Closes `docs/11-suggested-research-areas.md` area **AZ** (items 1 and 2 of its brief; item 3 is
a bounded non-claim, §5). Claim: issue #221. Branch `research/laz`.

**Result: every cell reproduced. 18 of 18 reproduction cells answer their AY value to the digit
— status, byte count, full body digest, `ACAO` and `ACAM` — across the three cumulus hosts, at
a gap of 10.23 h since the AY pass.** Nine fabricated siblings `403` at the no-route digest with
no `ACAO`; nine real leaves `200`, 0 B, `ACAO: *`. **Both depth-2 cells also answer `403` at the
no-route digest, 42 B, no `ACAO`.** No cell flipped, so nothing is retracted and no dated
superseding note is owed to the AY row.

⚠ **One clause of AZ's own closure condition is NOT met and this row says so:** AZ's "Closes
when" asked for the re-run **at least 24 h after** the AY pass
[source: docs/11-suggested-research-areas.md §AZ]. This run measured **10.23 h**, because the
lane was directed to re-run it now. The stability half is therefore measured over **10.2 h, not
24 h** — that interval is a property of this pass, not a claim about a day. The ≥24 h re-run is
minted as successor **BE** rather than counted as done here.

## 0. The question, and what a flip would have cost

Every cell in areas C, N, Z, AP and AY is a **single observation per base per host**
[source: findings-log/2026-11-11-area-aq-options-per-route/FINDINGS.md §6.1]. AY read its nine
fabricated-vs-real pairs as making the `200` a **route** signal in `csr/v2`, bare `v2` and
`carepartner/v6` on all three cumulus hosts — that reading is INFERRED from nine cells to three
subtree properties, and a single flipped cell would have scoped it to the pass date and forced a
dated superseding note on the AY row
[source: findings-log/2026-11-11-area-aq-options-per-route/FINDINGS.md §4].

Three route verdicts ride on those cells:

| verdict | written as | cell that carries it | source |
|---|---|---|---|
| `connect/csr/v2/display/message` | live, POST-only | `OPTIONS` 200 + `ACAO: *` | [source: findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md:69] |
| `connect/v2/display/message` (bare) | live, POST-only | `OPTIONS` 200 + `ACAO: *` | [source: findings-log/2026-10-12-csr-cross-host/FINDINGS.md:58] |
| `connect/carepartner/v6/display/message` | live, POST-only | `OPTIONS` 200 + `ACAO: *` | [source: findings-log/2026-10-12-area-z-origin-reflection/FINDINGS.md:116] |

## 1. Method

- **Three hosts, and no others**: `clcloud.minimed.com`, `clcloud.minimed.eu`,
  `clcloud-trials.minimed.com`. The clinic hosts and `carelinkhp` belong to sibling lanes.
- **23 of a 24 cap** harnessed — plus **one pre-flight `GET` spent before the plan was
  itemised** (§1a), so the **wire total is 24 of a 24 cap**. Zero failures, zero retries,
  `curl_exit: 0` on all 23 ledger rows.
- **Empty-body `OPTIONS` + `GET` only** (`--request OPTIONS`, never `-X OPTIONS` with a body).
  No `POST`, no `Authorization`, no `Cookie`, no `x-api-key`, no `X-System-ID`, no token
  exchange, no wordlist, no DNS, no port scan, no dev/stage host.
- **`sleep 2.5` inside the per-host `flock`** — a ≥ 2.5 s delay between requests to the same
  host, held inside the lock — on `$REPO/.loop/host-<host>.lock`, structure copied from
  [source: findings-log/2026-11-11-area-aq-options-per-route/probe.sh].
- **The control is a GATE on every host.** Per host, first: `GET /connect/carepartner/v2/zz-aq2-absent-7241`
  must be `403` / 42 B / `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16`.
  `gate()` compares status **and** byte count **and** full digest **and** host; a mismatch exits
  9 and no question cell is issued for that host. All three gates printed `GATE OK` (§2).
- **The fabricated literal is AY's own**: `zz-aq2-absent-7241`. Re-using it is what makes this a
  **reproduction** rather than a new measurement — a different literal would leave "the name
  changed" as an alternative explanation for any cell that moved. It is certainly absent on each
  host by measurement, not assertion: cell 1's `GET` returns the published no-route body.
- **The depth-2 literal is new**: `zz-az2-absent-9917`, used only in `…/zz-az2-absent-9917/deeper`
  — one segment **below** the leaf depth. It had **zero hits in the committed tree before this
  pass wrote anything** (`git grep -c 'zz-az2-absent-9917' origin/main -- .` → no match, exit 1);
  at this head it appears only in this lane's own artefacts.
- **Reading rule, unchanged from `docs/09` §2**: `403` at the no-route digest ⇒ no route matched
  that path for that method; `200` + `ACAO: *` ⇒ a route answered. A fabricated sibling answering
  `200` would be the flip.

### 1a. Disclosed defect — one request outside the itemised plan

Before `probe.sh` was written, a single empty-body-indifferent reachability `GET` was sent to
`https://clcloud.minimed.com/connect/carepartner/v2/zz-aq2-absent-7241` to confirm the oracle
still answered `403` at all (`2026-11-11T22:26:37.497Z`, `403`). That request is **not in
`results.jsonl`**, was not harnessed, and bought no cell. It is counted in the wire total (24 of
24), not the harnessed figure (23 of 24). The same breach of the itemise-first rule is on the
record for area AN [source: findings-log/2026-11-11-area-an-hcp-boundary-mechanism/FINDINGS.md §1a];
this pass repeats it rather than back-filling a row.

## 2. Controls (OBSERVED)

| seq | host | method | path | status | `x-amzn-errortype` | bytes | sha256 |
|---|---|---|---|---|---|---|---|
| 1 | `.com` | GET | `carepartner/v2/zz-aq2-absent-7241` | **403** | `MissingAuthenticationTokenException` | 42 | **`f249b63cb2fc…`** |
| 9 | `.eu` | GET | `carepartner/v2/zz-aq2-absent-7241` | **403** | `MissingAuthenticationTokenException` | 42 | **`f249b63cb2fc…`** |
| 17 | `-trials` | GET | `carepartner/v2/zz-aq2-absent-7241` | **403** | `MissingAuthenticationTokenException` | 42 | **`f249b63cb2fc…`** |

**OBSERVED** — `results.jsonl` seq 1, 9, 17; `run.log` `GATE OK` lines. Each reproduces the same
host's AY control (seq 2, 10, 18) on status, bytes and full digest
[source: findings-log/2026-11-11-area-aq-options-per-route/FINDINGS.md §2]. The direction of the
oracle is unchanged: **`403` is a NEGATIVE — no matching route — and never a positive.**

## 3. Stability — the nine pairs, re-run (OBSERVED)

| base | host | fabricated `OPTIONS` | status | B | digest | `ACAO` | real leaf `OPTIONS` | status | B | `ACAO` / `ACAM` | vs AY |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `csr/v2` | `.com` | seq 2 | **403** | 42 | `f249b63c…` | — | seq 3 | **200** | 0 | `*` / `OPTIONS,POST` | **same** |
| `csr/v2` | `.eu` | seq 10 | **403** | 42 | `f249b63c…` | — | seq 11 | **200** | 0 | `*` / `OPTIONS,POST` | **same** |
| `csr/v2` | `-trials` | seq 18 | **403** | 42 | `f249b63c…` | — | seq 19 | **200** | 0 | `*` / `OPTIONS,POST` | **same** |
| bare `v2` | `.com` | seq 4 | **403** | 42 | `f249b63c…` | — | seq 5 | **200** | 0 | `*` / `POST,OPTIONS` | **same** |
| bare `v2` | `.eu` | seq 12 | **403** | 42 | `f249b63c…` | — | seq 13 | **200** | 0 | `*` / `POST,OPTIONS` | **same** |
| bare `v2` | `-trials` | seq 20 | **403** | 42 | `f249b63c…` | — | seq 21 | **200** | 0 | `*` / `POST,OPTIONS` | **same** |
| `v6` | `.com` | seq 6 | **403** | 42 | `f249b63c…` | — | seq 7 | **200** | 0 | `*` / `OPTIONS` | **same** |
| `v6` | `.eu` | seq 14 | **403** | 42 | `f249b63c…` | — | seq 15 | **200** | 0 | `*` / `OPTIONS` | **same** |
| `v6` | `-trials` | seq 22 | **403** | 42 | `f249b63c…` | — | seq 23 | **200** | 0 | `*` / `OPTIONS` | **same** |

**Which answer is the same?** Not just the status: `verify.py` compares each of the 18
reproduction cells against the AY ledger row for the same `(host, method, path)` on
**`http_status`, `body_bytes`, `body_sha256`, `acao`, `acam` and `errortype`** — 18 of 18 match on
all six fields, and it fails if any field moves. The `ACAM` orderings also reproduce exactly
(`OPTIONS,POST` / `POST,OPTIONS` / `OPTIONS`), which is corroboration from the same source family,
not independent confirmation (`AGENTS.md` §2.1).

**Zero flips in 18 of 18 fields-sets.** This is the observation that would have falsified the AY
reading — a fabricated sibling answering `200`, or a leaf answering `403` — and it did not occur
(OBSERVED).

## 4. Depth — one fabricated name one segment deeper (OBSERVED)

| host | subtree | path | status | B | digest | `ACAO` |
|---|---|---|---|---|---|---|
| `.com` | `csr/v2` | `/connect/csr/v2/zz-az2-absent-9917/deeper` (seq 8) | **403** | 42 | `f249b63c…` | — |
| `.eu` | `carepartner/v6` | `/connect/carepartner/v6/zz-az2-absent-9917/deeper` (seq 16) | **403** | 42 | `f249b63c…` | — |

Both answer the **same** 42-byte no-route body as their host's control and their leaf-depth
fabricated sibling, with no `ACAO`, no `ACAM`, no `Allow`. **So the leaf-depth control in AY was
not an artefact of depth 2 vs depth 3 of the subtree**: an absent path one segment deeper is
answered by the same unmatched-route path, and does not pick up a catch-all preflight keyed one
segment up (OBSERVED for these two cells; INFERRED that "the same body" means "the same
unmatched-route path" — byte identity cannot exclude two distinct handlers emitting the same
bytes, which is the bound area AX states for the same inference shape
[source: findings-log/2026-11-11-area-ax-trailing-slash/FINDINGS.md §0]).

**What depth 2 does not cover:** the third host (`-trials`) has no depth-2 cell in this pass
(§6.1), and no cell was taken at depth 4 or deeper. Depth 2 here means one segment below each
subtree's `display/message` leaf, i.e. `csr/v2/<name>/deeper`.

## 5. Bounded non-claim — the MECHANISM is not reachable from here, and is not asserted

Item 3 of the AZ brief asked which mechanism produces the preflight — an edge-generated `OPTIONS`
reply that never reaches the route, or a per-route registration table. **This pass does not
distinguish them, and neither does anything else in the record.**

The reason is structural, not budgetary: both mechanisms predict **every cell this pass can
send**. A request shape that an edge answers without consulting a registration table, and a
request shape a table answers by matching a route, both produce `403` at the no-route digest for
an unmatched path and `200` + `ACAO: *` for a matched one. Separating them needs either a `POST`
(token-gated, `docs/10` §1, out of scope and out of this repository's method rules) or a response
field that differs between the two — and **no such field has been observed on this family** in
any committed ledger (OBSERVED: the header sets of the nine fabricated `403`s and the nine leaf
`200`s in §3 differ only in `content-length`, `x-amzn-requestid`, `x-amz-apigw-id`, `x-amz-cf-id`,
`access-control-allow-*` and `x-cache` — no field distinguishes *which layer* produced the reply).

**The header shape that motivates the question is unchanged and unexplained:** `ACAO`/`ACAM` are
present on a `200` whose `GET` is `401` (`carepartner/v13/display/message`, live) and on a `200`
whose `GET` is `403` (`v2/display/message`, unrouted) — the same header shape marking two
opposite `GET` states. That is why `ACAM` is not read as a method register anywhere in this repo.
What this pass adds is that the shape is **stable over 10.23 h**, not what generates it. **No
cause is asserted.**

## 6. Limits — what this does NOT prove

1. **10.23 h, not 24 h, and not a deployment cadence.** AZ's own condition asked for ≥24 h
   [source: docs/11-suggested-research-areas.md §AZ]; this run measured 10.23 h. Nothing here
   measures how often this gateway's configuration changes, so neither 10.2 h nor 24 h is a
   measured stability window — both are conventions (INFERRED). Successor **BE**.
2. **One depth-2 cell per host, two hosts.** `.com` under `csr/v2` and `.eu` under
   `carepartner/v6`; `-trials` and the bare `v2` subtree have no depth-2 cell. The reading in §4
   is therefore two cells, not a nine-cell matrix, and it is **not** claimed for bare `v2` or for
   `-trials`.
3. **Three hosts, three bases.** Nothing here says anything about `commoncore*`, the clinic hosts,
   `carelinkhp`, or any base outside `csr/v2`, bare `v2` and `carepartner/v6`.
4. **"POST-only" stays INFERRED.** No `POST` was sent; `ACAM` is not a method register
   [source: findings-log/2026-10-12-csr-cross-host/FINDINGS.md §Verdict 2]. The body behind each
   route is token-gated and unobserved.
5. **Not pinned.** These cells are not in `regression/hurl/`, so this control is evidence as of its
   run date, not a standing assertion. A successor could pin three of the nine.
6. **Not a disclosure.** Every cell is an unauthenticated `GET` or empty-body `OPTIONS`; every byte
   quoted is an error envelope or a CORS preflight served to any anonymous caller.

## 7. Requests, spacing, and the two clocks

**23 of a 24 cap** harnessed, **24 of 24 on the wire** (§1a), zero unspent *within* the plan,
zero failures, zero retries, `curl_exit: 0` on all 23 rows, `GET` + empty-body `OPTIONS` only,
`sleep 2.5` held inside the per-host `flock`.

- **Clock A — `t_sent`**: **20 gaps**, equal to `sum(rows_per_host − 1)` = (8−1) + (8−1) + (7−1)
  = 7 + 7 + 6 = **20**, checked against the per-host row counts rather than carried. Floor
  **2.591 s**, **0 under 2.5 s**, **0 impossible negative durations**. Per host: `.com` 7 gaps
  min 2.662 s, `.eu` 7 gaps min 2.591 s, `-trials` 6 gaps min 2.668 s.
- **Clock B — kernel body mtime** (`stat -c %.9Y` on the response body, captured per request):
  **23 bodies, 23 distinct mtimes**, span 60.249 s; 20 gaps, floor **2.591 s**, **0 under 2.5 s**.
  It is proven to be a second clock rather than one batch stamp: every one of the 23 mtimes falls
  inside its own `[t_sent, t_done]` window (23 of 23, tolerance 50 ms), and the two spans agree to
  1.7 ms (A 60.251 s, B 60.249 s).
- ⚠ **Clock B is not re-derivable from a clean clone** — git does not preserve mtimes and the
  bodies live in a gitignored scratch dir. Clock A is the one a stranger can reproduce from
  `results.jsonl` alone, and it agrees with clock B on the floor to the millisecond here. Unlike
  several earlier passes, **this harness is not in the corrupt-`t0` class**: no negative duration
  appears in §7, so no gap is quarantined and no cause is disclaimed.

## 8. Reproducing this at zero requests

```
python3 findings-log/2026-11-11-area-az-options-stability/verify.py
```

Re-derives the row count and the 7/8/8 split, the 20-gap total against `sum(rows_per_host − 1)`,
all three controls, all 18 reproduction cells against the **AY ledger** on six fields, the two
depth-2 cells, both clocks including the per-row `[t_sent, t_done]` window test, and the gap in
hours since the AY pass. Exits 0 only when every one holds. It issues no requests.

## 9. The registry — AZ retires, BD and BE are minted

`python3 scripts/research-checks.py` at this head prints the open/closed figures; this log quotes
them rather than computing them (`AGENTS.md` §6 item 7). Letters were read free at commit time via
`grep -oE '^### [A-Z]{1,2}\.' docs/11*.md` against the closed rows: `AZ` retires by this close and
**`BD`** / **`BE`** were the next free ids.

- **BD** — pin three of the nine cells into `regression/hurl/` so the per-route reading stops
  being evidence-that-ages (§6.5).
- **BE** — the ≥24 h re-run AZ's own condition asked for and this pass could not buy (§6.1).
