# Area: `docs/10` row 58 — is `v6` the only discovery version that splits across hosts?

**51 of a 54 cap** · **GET only** (no OPTIONS, no POST, no token, no Cookie, no
`Authorization`) · ≥2.5 s between requests to the same host, sleep **inside** the
shared per-host lock · `--compressed` on every request · controls first per host.

**Answer: no. `v6` is not unique, and it is not even the only version with the
trials-only cell.** **8 of the 16 base paths split across the three hosts**
(`v2`–`v6`, `v8`, `v9`, `v10`); 8 are uniform. The seven trials-only base paths
return **one byte-identical body** (`sha256 1aab9bb1e721…`, 10 053 B) whose
content does not vary with the requested version at all, so the shape
`docs/03` §8 publishes as a `v6` property is a property of that one document on
the `-trials` deployment, not of `v6`.

---

## 0. What was asked, and what this pass does *not* claim

Issue #145 asks one question: **`ORACLE-PROBE-MATRIX.md` holds three-host
coverage for 3 of its 16 versions on `GET /connect/carepartner/<ver>/discover/android/3.6`,
so a cross-host split was undeterminable — not excluded — for the other 13, and
`docs/10` row 58 warns in as many words against reading "`v6`-specific" as "only
`v6` splits".**

Two things stay explicitly open after this pass:

- **The *why*.** What makes the `-trials` deployment answer a legacy document
  for these base paths is **not closable from outside**, and is not claimed.
  `VERSION-AXIS §4`'s filename reading (`sso_cp_us_v6.json`) stays exactly as
  recorded, with no second reading attached to it.
- **Whether a trials `200` means a route.** This pass establishes that the
  `-trials` gateway's answer on this path **does** key on the base-path segment
  (see §4) — but it does **not** establish that a matched route returns a
  per-route document rather than a template. See §5.

## 1. Method and accounting

| | |
|---|---|
| Requests | **51** of a **54** cap |
| Method | `GET` only, literal — `probe.sh` calls `curl -s --compressed` with no `-d`, `-X`, `-H` or auth flag |
| Path | `https://<host>/connect/carepartner/<ver>/discover/android/3.6` |
| Hosts | `clcloud.minimed.eu`, `clcloud.minimed.com`, `clcloud-trials.minimed.com` |
| Delay | `sleep 2.5` **inside** `flock` on the shared per-host lock (the locks are shared with every other lane in this pool run, so the delay has to be taken under the lock) |
| Controls | 2 per host, sent **first** — `v99` (recorded unrouted) and `v11` (recorded `200` on all three) |
| Cells | 16 versions × 3 hosts = 48, plus 2 controls × 3 hosts = 6 |

**Why 51 and not 54.** The `v11` control cell and the `v11` matrix cell are the
same method, same path, same host. It is sent **once** per host and counted
**once**; sending it twice would be a request that buys no new observation.
`wc -l results.jsonl` = **51**, and the ledger's `seq` runs `1..51` in send
order with no gaps and no duplicates.

**No request in this pass was issued by anything but `probe.sh`.** No `hurl
--test` was run against these cells, so the ledger is the whole request
accounting for this lane (AGENTS.md §5, the brief's ledger rule).

**Artefacts.** `probe.sh` (the harness), `results.jsonl` (one row per request:
`seq`, `host_seq`, `t_queued`, `t_sent`, `t_done`, method, url, status,
content-type, bytes, `x-amzn-errortype`, `x-cache`, `x-cum-signature` presence,
`body_sha256`, capture tag), `headers/<seq>-<host>-<ver>.{h,b}` (every response
header and body, verbatim), `run.log`, `matrix.py` (the verdict table, derived
from the ledger alone), `spacing.py` + `spacing.txt` (the two-clock spacing
check), and `cells.md` (the per-cell table, 51 rows).

**Namespace note.** The matrix's `namespace` column is `connect/carepartner` and
**already contains `connect/`**. It is used verbatim. Prefixing it again gives
`connect/connect/…`, which is the area-Y defect recorded in `docs/11` under
*"Why there is no area AA"*.

**A change to the committed harness, stated rather than smoothed over.** The
executed `probe.sh` located the shared lock directory from an absolute path;
the committed script locates it by walking up to the directory that holds
`.loop/` beside a `findings-log/`. That is the only difference, it touches the
lock file and nothing else, and no request, path, delay or recorded field is
affected. It exists because the absolute form trips the repo's own
`machine-specific paths` scrub pattern (AGENTS.md §7), which is a thing this
repository fails its own gate for.

## 2. Controls, sent first per host — and what each one proved

| seq | host | control | result | what it establishes |
|---|---|---|---|---|
| 1 | `.eu` | `v99` absent | `403` `MissingAuthenticationTokenException`, 42 B, `sha256 f249b63cb2fc…` | the **no-route class** is live on this host tonight, and it is byte-identical to the corpus digest |
| 2 | `.eu` | `v11` served | `200`, `application/json;charset=utf-8`, 20 345 B, `x-cum-signature` present, `sha256 94b739dda478…` | the **served class** is still reachable on `.eu` tonight |
| 18 | `.com` | `v99` | `403`, same 42 B, same digest | same |
| 19 | `.com` | `v11` | `200`, 18 105 B, `sha256 2103b7e850c4…` — the **`.com` legacy** v11 document | the served class is reachable on `.com`, and it is the other document, as `docs/03` §7 records |
| 35 | `-trials` | `v99` | `403`, same 42 B, same digest | **the decisive control**: `-trials` does **not** answer `200` for every tail |
| 36 | `-trials` | `v11` | `200`, 20 345 B, `sha256 94b739dda478…` — byte-identical to the `.eu` v11 doc | the served class is reachable on `-trials` |

All six controls passed, and all six ran before any matrix cell on their host.
The `v11` control is what licenses the reading of a uniform `403` on the other
15 base paths as a statement about the **version axis** rather than about a host
that stopped serving; the `v99` control on `-trials` is what stops the trials
column being read as a catch-all.

## 3. The verdict grid — 16 versions × 3 hosts, all 48 cells classified

Classes, per Oracle A (`docs/09` §2): **no-route** = `403`
`MissingAuthenticationTokenException` at the corpus 42 B digest ·
**routed-token-gated** = `401` `UnauthorizedException` · **served-signed** =
`200` with `x-cum-signature` · **served-empty** = `204`. **Status alone is never
consulted**; each verdict is status + `x-amzn-errortype` + content-type + body
digest (`AGENTS.md` §7, `AGENTS.md` §8).

| base path | `.eu` | `.com` | `-trials` | verdict |
|---|---|---|---|---|
| `v1` | no-route | no-route | no-route | uniform |
| `v2` | no-route | no-route | **served-signed** `1aab9bb1` 10 053 B | **split** |
| `v3` | no-route | no-route | **served-signed** `1aab9bb1` 10 053 B | **split** |
| `v4` | no-route | no-route | **served-signed** `1aab9bb1` 10 053 B | **split** |
| `v5` | no-route | no-route | **served-signed** `1aab9bb1` 10 053 B | **split** |
| `v6` | no-route | no-route | **served-signed** `1aab9bb1` 10 053 B | **split** |
| `v7` | no-route | no-route | no-route | uniform |
| `v8` | no-route | no-route | **served-signed** `1aab9bb1` 10 053 B | **split** |
| `v9` | no-route | no-route | **served-signed** `1aab9bb1` 10 053 B | **split** |
| `v10` | **served-empty `204`** 0 B | **served-empty `204`** 0 B | **served-signed** `94b739dd` 20 345 B | **split** |
| `v11` | served-signed `94b739dd` 20 345 B | served-signed `2103b7e8` 18 105 B | served-signed `94b739dd` 20 345 B | uniform **status**, three different documents (`docs/03` §7) |
| `v12` | routed-token-gated `401` | `401` | `401` | uniform |
| `v13` | served-signed `f8488626` 20 256 B | **same bytes** | **same bytes** | uniform, byte-identical |
| `v14` | no-route | no-route | no-route | uniform |
| `v15` | no-route | no-route | no-route | uniform |
| `v16` | no-route | no-route | no-route | uniform |

**Counting rule, stated so the number can be re-derived and not read as a
generalisation:** a *split* is a base path whose three cells fall into two or
more different classes **under the table above**, counting `served-empty` as its
own class and not merging it into `served-signed`. All 48 cells are classified —
**0 ambiguous**. Under that rule: **8 split** (`v2`, `v3`, `v4`, `v5`, `v6`,
`v8`, `v9`, `v10`), **8 uniform** (`v1`, `v7`, `v11`, `v12`, `v13`, `v14`,
`v15`, `v16`).

**32 of the 51 responses are the same 42-byte body at one digest** — `f249b63cb2fc…`,
the corpus no-route digest, byte-identical across all three hosts.

## 4. The finding: the trials cell is one document, not seven cells

The `-trials` column is not a column of seven similar cells. It is **one body
served under seven different base-path segments**:

| `-trials` base path | status | bytes | body `sha256` | `x-cum-signature` (sha256 of the header value) |
|---|---|---|---|---|
| `v2` `v3` `v4` `v5` `v6` `v8` `v9` | `200` | 10 053 | **`1aab9bb1e721…`** | **`f96b2a5168e6`** — one value, 7 of 7 |

`cmp` on the seven captured bodies returns identical for all seven. The body
carries `"config":"android,3.6"` — it **echoes the app-version segment and
nothing else**: no field, and no byte of it, varies with the requested base
path. The document is the legacy one `VERSION-AXIS §4` describes: `CP` is a
2-entry list (`SSOConfiguration` only, no `Auth0SSOConfiguration`, no
`baseUrlCms`), both regions name
`https://carelink-trials.minimed.com/configs/v1/sso_cp_us_v6.json`, all three
`baseUrl*` values point at `*-trials` hosts, `certificates[]` = 3 entries,
`supportedCountries` = 76.

**Two consequences, and both are corrections rather than additions:**

1. **`docs/03` §8's `v6` framing does not survive.** That section is headed *"`v6`
   — trials-only for discovery"* and its subject is a path that is `200` only on
   `-trials`. Every word of that is still true of `v6`; what is false is the
   implicature that `v6` is what makes it trials-only. Six other base paths —
   `v2`, `v3`, `v4`, `v5`, `v8`, `v9` — answer the identical document on the
   identical host and are no-route on both patient hosts. The trials-only cell
   is a property of **that one document on that one deployment**.
2. **`docs/10` row 58's warning is vindicated, and the thing it warned against
   is the smaller error.** Row 58 said: *"Do not read `v6`-specific as only `v6`
   splits."* The matrix would have supported exactly that misreading on its own
   evidence, because it has three-host coverage for `v6`, `v11` and `v12` only.
   The answer is not "`v6` and seven others split"; it is **"`v6` is one of
   seven base paths that all resolve to the same byte-identical body, so the
   split is in the document, not in the version."**

**And the `-trials` column is not a catch-all, which is why the above is a
finding and not an artefact.** On the same host, in the same run, under the same
path shape: `v1`, `v7`, `v14`, `v15`, `v16` **and the `v99` control** all answer
`403 MissingAuthenticationTokenException` at the 42 B no-route digest, while
`v2`–`v6`, `v8`, `v9`, `v10`, `v11`, `v13` answer `200`. The trials gateway is
therefore **keying on the base-path segment** — a route table, not a blanket
catch-all on this path (OBSERVED). *What a matched route returns — a per-route
document or a template — is not established here*, and §5 says so.

**The other new split, `v10`.** `.eu` and `.com` answer `204` with an **empty
body** (`sha256 e3b0c44298fc…`, the digest of zero bytes) and **no**
`x-cum-signature`; `-trials` answers `200` with the **20 345 B `v11` document**.
This is a status split the matrix could not see, because `v10` was probed on
`.eu` only. `docs/09` Oracle A tabulates `200` and `204` in **one** row
(*"no errortype (200/204) → public"*), so the two answers are the same class to
that oracle; this pass separates them as `served-empty` vs `served-signed`,
which is a refinement of the oracle and not a contradiction of it (see §5).

**The `-trials` `v10` document, specifically.** The 20 345 B document served at
`-trials` `/v10/discover/android/3.6` is byte-identical to the one at
`-trials` `/v11/discover/android/3.6` (`94b739dda478…`), and both carry the same
`x-cum-signature`. So the trials deployment answers `v11`'s document for `v10`
as well — **not** the empty `204` both patient hosts give at `v10`.

## 5. Limits — what these 51 requests cannot settle

- **A trials `200` does not prove a route per se.** This pass proves the trials
  gateway discriminates on the base-path segment (§4) and that the response does
  not vary with the requested version (§4). It does **not** prove that each of
  the seven matched base paths has its own route registration rather than one
  rule covering seven. Separating those needs the `OPTIONS` axis
  (`GET 403 + OPTIONS 200` → POST-only, per `docs/09` §2), which this pass was
  forbidden from running. **Recorded as ambiguous rather than resolved.**
- **`x-cum-signature` — a second correction, and this one is decidable.** The
  ledger records only the signature's *presence*, so the value comparison below
  is derived from the committed `headers/*.h` files, offline, at zero requests.

  | held constant | varied | signature values |
  |---|---|---|
  | body `1aab9bb1` + host `-trials` | base path, `v2`…`v6`, `v8`, `v9` | **1** (`f96b2a51…`) |
  | body `94b739dd` + host `-trials` | base path, `v10` vs `v11` | **1** (`17afd412…`) |
  | body `f8488626` | host, `.eu` / `.com` / `-trials` | **3** (`640e0f93…`, `5c14c13d…`, `1303f30d…`) |
  | body `94b739dd` | host, `.eu` / `-trials` | **2** (`a275f08e…`, `17afd412…`) |

  `VERSION-AXIS §1` calls this "a distinct base64 value per document (6 distinct
  values across 6 docs), i.e. a per-document integrity signature". **Refuted as
  stated:** one byte-identical body at three hosts carries three signatures, and
  one byte-identical body under two different base paths on one host carries
  one. What is consistent with all 17 signed cells here is a function of
  **(document, host)** — that last step is INFERRED, on the assumption that no
  third variable varies with it; the within-host pair is what rules out
  "per-request", and the cross-host triple is what rules out "per-document".
  `docs/03` §1 already recorded the host-specificity; this pass supplies the
  within-host control that reading was missing.
- **The `204` split is new to the oracle, not a contradiction of it.**
  `docs/09` Oracle A tabulates `403`, `401` and `200/204` in one row reading
  "public"; this pass found `204` **and** `200` on the **same base path across
  hosts** (`v10`), which is a distinction that grouping does not make. Recorded
  as a refinement, from one pass on one base path — the grouping is not wrong,
  it is coarser than one axis needs.
- **One pass, one day.** Every verdict is `2026-10-17`. Nothing here is pinned,
  so none of it is drift-guarded — see §7.
- **Nothing was pinned in `regression/hurl/`, deliberately.** The natural pins
  (the `1aab9bb1e721…` digest, the `v10` `204`, the `v6` cell) would add **51
  vendor requests to every weekly drift sweep** — against the ~80-request budget
  `AGENTS.md` §11 states — on a surface this lane does not own. A budget change
  to the sweep is the same class of decision as widening the gate's own patterns
  (`docs/09` §4), which this repo has repeatedly declined to let a research pass
  make. **No diff here changes a claim the suite already pins**, so no suite
  update was required by `AGENTS.md` §5. The pin question is carried as part of
  the successor in §7 rather than settled here.

## 6. Spacing — measured two ways, because `docs/09` §4 says the `date` series is the suspect

Full output in `spacing.txt`, printed at microsecond resolution because git does
not preserve mtimes.

| host | gaps | `t_sent` min | `t_sent` under 2.5 s | mtime min | mtime under 2.5 s |
|---|---|---|---|---|---|
| `.eu` | 16 | 2.634 s | **0** | 2.643 s | **0** |
| `.com` | 16 | 2.849 s | **0** | 2.843 s | **0** |
| `-trials` | 16 | 2.857 s | **0** | 2.857 s | **0** |

**Measured floor: 2.634 s** (`t_sent`, `.eu`) — above both the declared 2.5 s and
the repo's `>=2 s` floor, on **both** clocks, with **0** sub-declared gaps
anywhere. **0 of 51 rows carry a negative duration** (`t_done < t_sent`), so
this pass's `date` series does not convict itself the way areas B, F, K and the
CORS pass did, and its gaps are evidence rather than artefacts.

The two clocks disagree by up to 5.7 s on **4 gaps per slow host, always in
adjacent pairs that cancel** — and the cause is visible in the ledger rather
than assumed. The eight slowest requests by duration are every `200`/`204`
document cell (5.07–6.02 s: `-trials` `v10` 6.024, `-trials` `v13` 5.959,
`-trials` `v11` 5.769, `.com` `v11` 5.685, …, `.eu` `v10` 5.073), while every
`403`/`401` cell is **0.058–0.420 s** (35 of 35). A slow request pushes its own
body mtime later,
which lengthens the mtime gap **before** it and shortens the one **after** it,
while the `t_sent` gap absorbs the whole delay in the later pair. Both clocks
remain above the floor on every gap. **No cause beyond that is asserted**, and
`docs/09` §4's open question ("why does a sub-declared gap appear at all?")
gains nothing from this pass, which has none.

## 7. Evidence table

| Claim | Class | Source |
|---|---|---|
| 8 of the 16 base paths split across the three hosts | OBSERVED | `results.jsonl` + `cells.md`; derived by `matrix.py` |
| `v6` is **not** the only version with the trials-only cell — `v2`–`v5`, `v8`, `v9` share it | OBSERVED | seq 38–41, 44–45, cells `*trials*v{2,3,4,5,8,9}.b`, all `sha256 1aab9bb1e721…` |
| Those seven trials responses are **byte-identical** (`cmp`, 7 of 7) | OBSERVED | `headers/*-clcloud-trials.minimed.com-v{2,3,4,5,6,8,9}.b` |
| The body echoes `android/3.6` and nothing about the base path | OBSERVED | first field of each of the seven bodies: `"config":"android,3.6"` |
| The `-trials` gateway **discriminates** on the base-path segment (not a catch-all) | OBSERVED | `v1`, `v7`, `v14`–`v16` and the `v99` control all `403` at `f249b63cb2fc…` on the same host, seq 35, 37, 43, 49, 50, 51 |
| `-trials` serves the `v11` document at `v10` too (`94b739dda478…`, same signature) | OBSERVED | seq 46 vs seq 36 |
| `v10` is a status split: `204`+empty body on `.eu`/`.com`, `200` on `-trials` | OBSERVED | seq 12, 29, 46 |
| `v13` byte-identical across all three hosts (`f8488626…`, 20 256 B) — **a re-derivation, not a new fact**: `docs/03` §1 already publishes it and area Y refuted an earlier "`.eu` only" premise off area X's 2026-10-12 capture | OBSERVED | seq 14, 31, 48 |
| `.com` `v11` is the other document (`2103b7e850c4…`, 18 105 B) — `docs/03` §7 reproduced | OBSERVED | seq 19 |
| `x-cum-signature` is **not** per-document; `(document, host)` is consistent, per-request is refuted | OBSERVED for the two refutations, INFERRED for the `(document, host)` reading | `headers/*.h`, derived offline; 17 signed cells |
| `-trials` `200` on this path does not by itself prove a per-route registration | stated as a limit | §5; needs the `OPTIONS` axis, not run |
| Why `-trials` serves a legacy document at all | **not claimed** | §0 |
| All six controls passed before any matrix cell on their host | OBSERVED | `run.log` seq order, `results.jsonl` `seq`/`host_seq` |

## 8. Reproducing

```
probe.sh            # 51 requests, GET only, cap 54, sleep 2.5 inside the host lock
matrix.py           # the verdict grid, from results.jsonl alone (zero requests)
spacing.py          # the two-clock spacing check -> spacing.txt (zero requests)
results.jsonl       # 51 rows, one per request
cells.md            # the 51-row per-cell table
headers/            # every response header and body, verbatim
run.log             # send order with t_queued/t_sent/t_done
```

`LOCKDIR=` overrides where the shared per-host locks are found; the script
locates them itself otherwise. Every claim above is a direct read of
`results.jsonl`, `headers/` or `run.log`.

## Correction (2026-10-17) — verifier round 1: the signed-cell population is **14**, not 17

**One figure in this log is withdrawn, and it is the population figure inside the
sentence whose whole credibility is "I checked every signed cell".** The
conclusion is unchanged; the count is corrected.

**Affected sites, verbatim:**

| site | as written | corrected to |
|---|---|---|
| `FINDINGS.md` **line 220** (§5) | *"What is consistent with all **17** signed cells here is a function of **(document, host)**"* | **14** |
| `FINDINGS.md` **line 287** (§7 evidence table) | *"derived offline; **17** signed cells"* | **14** |
| `docs/03` §1 (the same sentence, canonical) | *"consistent with all **17** signed cells in that pass"* | **14** — corrected in place, with the `17` and its provenance left visible beside it (`docs/` supersedes but does not erase, `AGENTS.md` §3) |

**`17` is withdrawn and replaced by `14`.**

**Counting rule — what qualifies as a signed cell, so the number is re-derivable
rather than typed.** A *signed cell* is a response whose captured headers carry
an `x-cum-signature` value. Of this pass's 51 cells:

| group | count | carries a signature? |
|---|---|---|
| no-route `403` envelope, 42 B, `f249b63cb2fc…` | 32 | no |
| `v12` `401` envelope, 36 B, `d551247201fc…` | 3 | no |
| `v10` `204`, empty body, on `.eu` and `.com` | 2 | no |
| **signed cells** | **14** | **yes** |

32 + 3 + 2 + **14** = **51**. ✔

**The 14 signed cells, verbatim, by `seq`:** **2, 14, 19, 31, 36, 38, 39, 40,
41, 42, 44, 45, 46, 48** —

| seq | host | base path | status | bytes | body `sha256` | signature value |
|---|---|---|---|---|---|---|
| 2 | `.eu` | `v11` | `200` | 20 345 | `94b739dda478…` | `a275f08e…` |
| 14 | `.eu` | `v13` | `200` | 20 256 | `f84886265667…` | `640e0f93…` |
| 19 | `.com` | `v11` | `200` | 18 105 | `2103b7e850c4…` | `e185ef39…` |
| 31 | `.com` | `v13` | `200` | 20 256 | `f84886265667…` | `5c14c13d…` |
| 36 | `-trials` | `v11` | `200` | 20 345 | `94b739dda478…` | `17afd412…` |
| 38 | `-trials` | `v2` | `200` | 10 053 | `1aab9bb1e721…` | `f96b2a51…` |
| 39 | `-trials` | `v3` | `200` | 10 053 | `1aab9bb1e721…` | `f96b2a51…` |
| 40 | `-trials` | `v4` | `200` | 10 053 | `1aab9bb1e721…` | `f96b2a51…` |
| 41 | `-trials` | `v5` | `200` | 10 053 | `1aab9bb1e721…` | `f96b2a51…` |
| 42 | `-trials` | `v6` | `200` | 10 053 | `1aab9bb1e721…` | `f96b2a51…` |
| 44 | `-trials` | `v8` | `200` | 10 053 | `1aab9bb1e721…` | `f96b2a51…` |
| 45 | `-trials` | `v9` | `200` | 10 053 | `1aab9bb1e721…` | `f96b2a51…` |
| 46 | `-trials` | `v10` | `200` | 20 345 | `94b739dda478…` | `17afd412…` |
| 48 | `-trials` | `v13` | `200` | 20 256 | `f84886265667…` | `1303f30d…` |

**How the `17` happened — reconstructed from the ledger, not guessed.**
Grouping `results.jsonl` by body digest gives **seven** groups:

| body `sha256` | bytes | cells | status | signed? |
|---|---|---|---|---|
| `f249b63cb2fc…` | 42 | 32 | `403` no-route | no |
| `1aab9bb1e721…` | 10 053 | 7 | `200` | **yes** |
| `94b739dda478…` | 20 345 | 3 | `200` | **yes** |
| `d551247201fc…` | 36 | 3 | `401` | **no** |
| `f8488626…` | 20 256 | 3 | `200` | **yes** |
| `e3b0c44298fc…` | 0 | 2 | `204` | no |
| `2103b7e850c4…` | 18 105 | 1 | `200` | **yes** |

**17 = 51 − 32 − 2** — every cell that was neither a no-route `403` nor an empty
`204`. The error was therefore exactly one thing: **the three `401` cells were
counted as signed, and they carry no `x-cum-signature` at all** (36 B,
`{"message":"Authentication failure"}`, `x-cache: Error from cloudfront`).
Dropping them gives 7 + 3 + 3 + 1 = **14**, which is the four **signed** groups
above and agrees with the rule in the previous section.

*(A first attempt at this paragraph reconstructed `17` as the five small groups
and produced 15 and 18 — neither is 17, and both were wrong. The table above is
the version that survives checking against `results.jsonl`; recording the failed
arithmetic because it is the `AGENTS.md` §6 item 7 shape.)*

**The conclusion was checked and stands.** `(document, host)` holds for all
**14**: every one of the seven `(document, host)` groups above carries exactly
**one** signature value. Both refutations are unaffected and do not depend on the
population figure at all —

- *per-document* is refuted by body `f8488626…` at three hosts carrying three
  values (seq 14, 31, 48);
- *per-request* is refuted by body `94b739dda478…` on `-trials` at two base paths
  carrying one (seq 36, 46).

**Evidence the verifier added, which strengthens the second refutation.** All
**14** signed cells carry `x-cache: Miss from cloudfront` — every one is a fresh
origin response, none an edge replay. That is what makes the `seq 36` / `seq 46`
identity an **origin** result about the document rather than a cache hit that
happened to match, which is the only way that control could have been a false
refutation. The verifier spent **0 vendor requests** establishing it, from the
committed `headers/*.h` alone; re-derived here independently and identical.

**Second defect from the same round, recorded here because it was found by the
same re-derivation.** `docs/03` §8a's grid **omitted `v6` entirely** — the
section's own subject — listing the row label as `v2–v5, v8, v9`, six base paths
where there are seven, so the page showed 15 of 16 and a reader could not see or
re-check the three `v6` cells. **This log's §3 table always carried `v6`**
(`seq` 8 no-route on `.eu`, 25 no-route on `.com`, 42 served-signed `1aab9bb1e721…`
on `-trials`), so the defect was in the synthesis, not in the evidence. The
canonical page is fixed: **all 16 base paths now have their own row**, and §3's
counting rule is carried onto the page so "8 of 16" is re-derivable from `docs/`
and not only from here (`AGENTS.md` §10).