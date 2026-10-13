# Findings — is `ACAO` on the `commoncore*` hosts method-conditional?

Correction issue [#61](https://github.com/NovaLux12/carelink-api-research/issues/61), method
half. Branch `research/x-cors-method`, 2026-10-13. Not the scope-vs-verdict decision that
issue names — see §6.

**One line: no. `access-control-allow-origin: *` is emitted identically on `GET` and on
empty-body `OPTIONS`, on a recorded path and on a certainly-absent path — 8 of 8 cells, 2
hosts, byte-identical bodies — so on this origin stack it is neither method-conditional nor
path-conditional, and the corollary matters more than the verdict: an `OPTIONS` response
carrying `ACAO: *` here is *not* proof that a resource exists.**

---

## 1. Before anything worked: two attempts that sent nothing

Recorded because the ledger rule is one row per invocation and because the failure was mine.

| Attempt | Rows | What happened | Cost |
|---|---|---|---|
| 1 | `seq 1–8` | `out` was called with six arguments against a five-parameter function, so the method word landed in the URL: curl was handed `https://commoncore-trials.medtronic.comGET` and `…comOPTIONS` | 8 resolver queries for 4 non-existent names |
| 2 | `seq 9–16` | the same defect, because the fix had been applied to the function's parameter list and **not** to the eight call sites | 8 resolver queries for 4 non-existent names |
| 3 | `seq 17–24` | fixed | **the 8 declared requests** |

All 16 failed invocations returned `curl_exit 6` ("could not resolve host"),
`http_status 000`, and wrote 0-byte header, sent-request and body captures. Name resolution
failed, so no TCP or TLS handshake was attempted: **0 vendor HTTP requests**. That is
OBSERVED from the captures — 48 capture files, all of them 0 bytes, and the recorded `curl_error_line`
— and the mechanism is reproduced offline in `attempt1-exit6-demo.txt`, where the absence of
a `Trying <ip>:443...` line is visible.

Two things that defect cost, both recorded rather than smoothed over:

- **Evidence.** The raw curl verbose stream for attempt 1 was written to a scratch directory
  and removed by the exit trap before it was read, so the error text itself was not kept. The
  recorded `curl_error_line` is attempt 2's; attempt 1's is reconstructed from `curl_exit 6`
  and the 0-byte captures.
- **Silent malformed rows.** Attempts 1 and 2 each shipped `results.jsonl` rows that are not
  valid JSON — a duplicated `seq` key, then an unquoted one — and **nothing read the file
  back**, so nothing noticed for two full runs. `docs/09` §4's "a check that looks like it
  ran is worse than no check", reached the obvious way.

Three changes make that class of defect unable to reach the network or the ledger, and they
are the reusable part of this pass:

1. `out` **refuses** any method that is not `GET`/`OPTIONS` and any path not beginning with
   `/`. Either aborts before the first request. Verified: a `POST` cell aborts with
   `ABORT: method 'POST' is not GET or OPTIONS — refusing to send` and sends nothing.
2. The capture filename carries the cell label, so an argument shift shows up in the
   filenames instead of in a malformed URL.
3. `curl_error_line` and `curl_connected_line` are recorded fields, and **every ledger row is
   assembled with `json.dumps` and parsed back before it is written.**

The harness was then validated end-to-end with `DRYRUN=1` against names under the reserved
`.invalid` TLD — **zero vendor traffic** — which is what caught defect 3 above. The request
shape was checked separately against a `python3 -m http.server` on `127.0.0.1`
(`options-shape-local-check.txt`): `-X OPTIONS` with no `-d`, no `--data` and no stdin sends
**no `Content-Length` and no upload**, i.e. a genuinely empty body.

---

## 2. Method

### 2.1 Cells — controls first, on every host probed

| Cell | Method | Path | Role |
|---|---|---|---|
| A | `GET` | `/reports-broker/v1/ocl` | **positive control** — the path the 2026-10-13 pass recorded |
| B | `GET` | `/reports-broker/v1/ocl-probe-absent` | **absence control** — certainly absent |
| C | `OPTIONS` (empty body) | `/reports-broker/v1/ocl-probe-absent` | **the cell the question turns on** |
| D | `OPTIONS` (empty body) | `/reports-broker/v1/ocl` | completes the path × method matrix |

The candidate list is **two paths**, both already on disk; nothing was invented and nothing
was fuzzed. No `Origin` header was sent in any cell, matching the six captures this pass
follows — verified per request in `headers/NN-*.sent.h`, where `origin` appears **0 times**
across all 8.

`commoncore-trials.medimed.com` was **not probed** — see §6.2.

### 2.2 Accounting

**Total 24 of a 24 cap.** Two numbers, both true, and a reader needs both:

- The cap declared before the first invocation was **8 HTTP requests to vendor hosts**. **All
  8 were used, and the cap was never reached** — the 16 aborted invocations in §1 never
  resolved a host and so never became requests.
- The ledger carries **24 rows** because every invocation gets one, whatever issued it. The
  other 16 are the two aborted attempts. They are counted here rather than reconciled away in
  prose, and they are the reason the row count exceeds the declared cap.

Delay **≥2 s**: declared **2.5 s**, slept **inside** the per-host `flock` lock in the shared
`.loop/`, so a concurrent worker on the same host cannot make the gap a fiction. Methods:
**GET** and **OPTIONS** with an empty body only. **No POST** was sent — `AGENTS.md` §11 permits
none beyond the two already pinned.

### 2.3 Spacing — measured, with its oracle named

**Measured floor: 2.737 s**, from the **kernel body-file mtimes** (`stat -c %y`, converted to
UTC), which `docs/09` §4 makes the independent series because the harness `date` series is the
suspect in five passes running. 6 same-host gaps, min 2.737 s, max 2.914 s, **0 under the
declared 2.5 s and 0 under the repo's ≥2 s floor**; the one cross-host gap (2.999 s) is
excluded from the floor and reported separately, because the rule is per host. Counting rule
and both series: `spacing.py` / `spacing.txt`.

The series were validated before being trusted, as `docs/09` §4 requires: mtime span
19.651 s against `t_sent` span 19.546 s, a difference of **+0.105 s across 8 requests** — one
request duration, not the sum of them, which is the signature of a body-write stamp rather
than the clock fault the trap describes.

⚠ **And the harness series disagrees, in the direction the trap predicts.** `t_sent` puts
`seq 23 → 24` at **2.273 s** — under the declared 2.5 s — where the kernel mtimes for the
same pair read **2.753 s**. `t_done` independently puts `seq 18 → 19` at 2.496 s. Recorded,
not rounded away, and no cause asserted: this is the **sixth pass** to exhibit the documented
signature, and the first one where **both series exist in one ledger and the better oracle
says the spacing was correct.**

---

## 3. The result

Per host, per path, per method. **8 of 8 cells carry `ACAO`, `ACAM` and `ACAH`; none carries
`Access-Control-Allow-Credentials`, `Allow` or `Vary`.** All 8 are `403`
`MissingAuthenticationTokenException`, `application/json`, **42 B**, and all 8 share one body
digest `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16` — byte-identical to
each other **and to the six captures in PR #59**, which is the positive control passing.

| Host | Path | Method | Status | `ACAO` | `ACAM` | `ACAH` | `ACAC` | `Allow` | `Vary` |
|---|---|---|---|---|---|---|---|---|---|
| `commoncore-trials.medtronic.com` | `/reports-broker/v1/ocl` | `GET` | 403 | `*` | `*` | `*` | absent | absent | absent |
| `commoncore-trials.medtronic.com` | `/reports-broker/v1/ocl-probe-absent` | `GET` | 403 | `*` | `*` | `*` | absent | absent | absent |
| `commoncore-trials.medtronic.com` | `/reports-broker/v1/ocl-probe-absent` | **OPTIONS** | 403 | `*` | `*` | `*` | absent | absent | absent |
| `commoncore-trials.medtronic.com` | `/reports-broker/v1/ocl` | **OPTIONS** | 403 | `*` | `*` | `*` | absent | absent | absent |
| `commoncore.medtronic.com` | `/reports-broker/v1/ocl` | `GET` | 403 | `*` | `*` | `*` | absent | absent | absent |
| `commoncore.medtronic.com` | `/reports-broker/v1/ocl-probe-absent` | `GET` | 403 | `*` | `*` | `*` | absent | absent | absent |
| `commoncore.medtronic.com` | `/reports-broker/v1/ocl-probe-absent` | **OPTIONS** | 403 | `*` | `*` | `*` | absent | absent | absent |
| `commoncore.medtronic.com` | `/reports-broker/v1/ocl` | **OPTIONS** | 403 | `*` | `*` | `*` | absent | absent | absent |

(`ACAO` / `ACAM` / `ACAH` = `access-control-allow-origin` / `-methods` / `-headers`;
`ACAC` = `-allow-credentials`. Captures: `headers/17-…` … `headers/24-…`; ledger:
`results.jsonl` `seq 17–24`.)

**The two axes are not merely similar, they are identical.** Strip the five per-request
headers (`date`, `x-amzn-requestid`, `x-amz-cf-id`, `x-amz-apigw-id`, `via`, `x-amz-cf-pop`)
and all 8 response-header sets hash to one value, and all 8 bodies to one value:

```bash
for n in 17-commoncore-trials-a-ocl-get 18-commoncore-trials-b-absent-get \
         19-commoncore-trials-c-absent-options 20-commoncore-trials-d-ocl-options \
         21-commoncore-a-ocl-get 22-commoncore-b-absent-get \
         23-commoncore-c-absent-options 24-commoncore-d-ocl-options; do
  sed -E '/^(date|x-amzn-requestid|x-amz-cf-id|x-amz-apigw-id|via|x-amz-cf-pop|HTTP)/d' \
    "headers/$n.h" | tr -d '\r' | sort | md5sum | cut -c1-12
  md5sum "bodies/$n.b" | cut -c1-12
done
```

Every cell returns `877da1f9291b` (headers) and `905b1fbb26e0` (body). What survives the strip
is eight lines, and three of them are the CORS headers:

```
access-control-allow-headers: *
access-control-allow-methods: *
access-control-allow-origin: *
content-encoding: deflate
content-length: 50
content-type: application/json
x-amzn-errortype: MissingAuthenticationTokenException
x-cache: Error from cloudfront
```

Read against the axes rather than as a list: `GET` and `OPTIONS` are indistinguishable on
every recorded header; the recorded path and the certainly-absent path are indistinguishable
down to the body digest.

**`access-control-allow-methods: *` appears on a response for a path that does not exist.**
`docs/09` §4 is explicit that `allow-methods` is gateway CORS configuration and **not** a
register of a route's methods, and this is a second, independent instance of that: the `*`
here is on a `MissingAuthenticationTokenException` — the `docs/09` §2 no-route error — so it
describes the **stage**, not any route. Recorded as an observation about the stage. It is not
read as a method list.

---

## 4. What this settles

**OBSERVED.** On `commoncore-trials.medtronic.com` and `commoncore.medtronic.com`, the
`access-control-*` set on this no-route error is **not method-conditional**: it is identical
on `GET` and on empty-body `OPTIONS` (4 cells per host, 8 total).

**Consequence for the mechanism question `docs/09` records as open.** The reading "emitted
only on `OPTIONS`" (`docs/09` §2, `docs/00` §CORS paragraph) is **excluded for this host
family**. It is **not** excluded for `clcloud.*` — see §6.1.

**The corollary, which is the more useful half.** `docs/09` §2 uses "`ACAO: *` **on an
`OPTIONS` request**" as *the cleanest proof that a resource exists with no `GET` method* —
that is how POST-only `v6/display/message` was found. On this origin stack that inference
does not hold: the `OPTIONS` cells here carry `ACAO: *` **and are provably no-route**, because
`x-amzn-errortype: MissingAuthenticationTokenException` is the `docs/09` §2 no-route error
and the `OPTIONS` response is byte-identical to the certainly-absent `GET` control.

- **OBSERVED:** an `OPTIONS` response on these hosts carries `ACAO: *` on a path that does not
  exist.
- **INFERRED:** therefore on this family an `OPTIONS`-time `ACAO` is not by itself evidence
  of a resource, and POST-only discovery by preflight needs the *status* (200 vs 403) beside
  the header, not the header alone. Assumption stated: that `MissingAuthenticationTokenException`
  plus `x-cache: Error from cloudfront` on this stage means no route — the assumption this
  pass did **not** have to take on trust, because the certainly-absent control was sent first
  and returned the same thing.

---

## 5. What this does not settle

### 5.1 The `clcloud.*` mechanism — untouched

Every cell here is on a `commoncore*` host. **No `clcloud.*` host was probed**, so nothing in
this pass excludes or confirms "emitted only on `OPTIONS`" for the `clcloud.*` route
families, and nothing here should be read across a host-family boundary. A stage that emits
CORS on its no-route error is a different stage from one that does not.

### 5.2 `commoncore-trials.minimed.com` — named, not dropped

1 of the six counter-examples sits there and it was **not probed**: three cells per host is 9
requests against a cap of 8, and a fourth cell per host is 12. The budget went to **two hosts
at a full path × method matrix** rather than three hosts at a matched pair, because `AGENTS.md`
§8 makes the controls mandatory and a matched pair with no positive control behind it is not a
defended comparison. Closing it is **4 more requests**, needs no new idea, and would extend
the family claim from 2 hosts to 3.

### 5.3 `Origin` reflection — deliberately untested

No `Origin` was sent. Area Z excluded "ACAO appears only when an `Origin` header is sent" on
`clcloud.*` route cells; whether that holds on `commoncore*` is **unobserved**, and
`sent_origin_header` is `0` on all 8 rows to prove the omission was intentional rather than
accidental.

### 5.4 Browser callability — a no-route error is not a route

`ACAO: *` on a `403` for a path that does not exist says nothing about what a client can
call. Nothing here changes `docs/10` §1's browser-callability row.

---

## 6. The decision this pass deliberately does not make

### 6.1 The scope-vs-verdict ruling on the word "anywhere" — the maintainer's

Issue #61 names two readings and says the choice is a maintainer's, because it rewrites the
verdict line of a **closed** area. **This branch does not change any of the four claims.**
Proof that does not depend on reading this note — the diff, and the file hashes:

| Site | Claim lives at | Change on this branch | How to check |
|---|---|---|---|
| `docs/00-summary-the-map.md` | line 166 | **none — the whole file is byte-identical to `origin/main`** | `sha256sum` = `521fdf94ed8eec78c53f16e3a781a8573b524ea8b8d9dd95fb303fdea4f14846` on both sides |
| `docs/03-discovery-and-versions.md` | line 341 | **none — byte-identical** | `27fd2fdcc38bc80cfa1a2e528d3d78d60f43f1c6187a38a07d72f847379b1f32` |
| `docs/10-open-questions.md` | line 56 | **none — byte-identical** | `cd56c252292e7bb998aa73fcaea48116d48280a16975410ca7ddd0e806307fe4` |
| `docs/11-suggested-research-areas.md` | **line 703 → 750** — shifted, not edited | exactly one **insertion**, a dated addendum at line 252. No deletion, no rewrite | `git diff -U0 origin/main -- docs/11-suggested-research-areas.md` returns a single hunk, `@@ -251,0 +252,47 @@`, i.e. a pure addition. The claim's own sentence appears on neither side of that diff, and `diff <(git show origin/main:docs/11-suggested-research-areas.md \| sed -n '703p') <(sed -n '750p' docs/11-suggested-research-areas.md)` is silent |

Three of the four files are untouched outright; the fourth gained an addendum **47 lines above
the Closed table** and nothing else. `docs/09` is edited too, and its edits are in §2's CORS
paragraph and §4's timestamp row — neither of which carries any of the four claims.

**What each reading would change, quoted exactly, so the ruling does not need this log
re-read.** The claim is the string *"0 non-2xx responses carrying CORS anywhere"* (and, in
`docs/03`, *"anywhere in the corpus"*).

**Reading (a) — the claim was always scoped to `clcloud.*`; the prose over-reaches.** Then
the measurement is untouched and only the quantifier moves. Three sentences change, and
nothing else on any of the four pages:

1. `docs/11-suggested-research-areas.md`, Closed-table row **X** — **line 703 on
   `origin/main`, line 750 once this branch merges** — replace
   *"**0 non-2xx responses carrying CORS anywhere**"* with
   *"**0 non-2xx responses carrying CORS anywhere on `clcloud.*`**"*, ideally with a dated
   pointer to this log. The row's own scope ("Re-derived live on all three hosts" — all three
   *cumulus* hosts) then matches its claim.
2. `docs/00-summary-the-map.md` **lines 164-167** (untouched by this branch) — the same
   replacement inside
   *"**9 `200`-without-CORS responses, every one a `GET` of a discovery payload, and 0
   non-2xx carrying CORS anywhere**"*.
3. `docs/03-discovery-and-versions.md` **lines 340-342** (untouched by this branch) — the same
   replacement inside
   *"**…and still zero non-2xx responses anywhere in the corpus carrying CORS**"*, or the
   word *corpus* narrowed to `clcloud.*`.

**Reading (b) — the claim is falsified as written.** Then the verdict line of a closed area
changes and the supersession must be dated and visible (`AGENTS.md` §3: a closed area leaves
the Closed table only by being superseded, never silently). The same three sentences change,
and two more become necessary:

4. `docs/10-open-questions.md` **line 56** (untouched by this branch) — the same quantifier fix
   in the §1 row, *and* the
   sentence *"The 'demands a token on `OPTIONS`' reading is **not excluded**"* needs review,
   because on these two hosts the token question is not even reached: the response is no-route
   before any authorizer runs.
5. `docs/11`'s Closed-table row X needs a supersession note pointing at the six captures on
   the open PR #59 and at this log, with the original wording kept.

**What this pass contributes to that ruling and what it does not.** It contributes that
reading (b)'s deciding cell came back the way reading (b) would need **and** so did its
control: on the one host family where a CORS-carrying non-2xx is on the record, the same
three headers are on the `GET` and on the `OPTIONS` of a path that does not exist. It does
**not** contribute a ruling, and it deliberately did not touch the four sites.

### 6.2 A stale line number in the issue itself

Issue #61 cites `docs/11-suggested-research-areas.md:758`. At `origin/main` @ `20e4afc` the
Closed-table row X is at **line 703** — the file is 726 lines. Flagged, not reconciled: the
row is not mine to edit.

---

## 7. Pins — none, and why

**No assertion was added to `regression/hurl/`, so the count delta is zero** and the static
count stays **210** (424 execute). Two reasons, both about the standing rules rather than
about this finding's value:

- Nothing in the corpus depends on it. The finding is a method fact about three headers on a
  no-route error; no bridge constant, discovery pin, family vocabulary or error taxonomy
  moves. The four claim sites it bears on are already the owner's decision.
- `AGENTS.md` §11 says a workflow may probe only patterns already in `regression/hurl/`, and
  that a new host or path enters a workflow **only after a human has added it to the suite**.
  Pinning this would put three unlisted hosts and four new paths into the weekly drift sweep's
  vendor budget, which is §11's line, not a research pass's side effect.

If the owner wants it pinned, the shape is four `check`s in a new suite file, reusing the
exact values in §3's table — and the assertion count then needs re-measuring on top of
`origin/main` at merge time, because the count is global and order-dependent.

---

## 8. Artefacts in this directory

| File | What it is |
|---|---|
| `probe.sh` | the harness **as sent**, with the attempt-1/2 correction recorded in its header |
| `results.jsonl` | **24 rows**, one per invocation; `seq 17–24` are the 8 requests |
| `run.log` | 24 ordered rows, three timestamp columns each |
| `headers/NN-*.h` | response headers verbatim; the 16 attempt-1/2 captures are 0 bytes, which is the record |
| `headers/NN-*.sent.h` | **the request as sent**, verbatim — curl's own `> ` block, from which the method, the absent `Origin` and the empty body are read |
| `bodies/NN-*.b` | response bodies, 42 B each |
| `spacing.py` · `spacing.txt` | the spacing measurement, both series, counting rule and validation |
| `attempt1-exit6-demo.txt` | the failure path reproduced offline, no vendor |
| `options-shape-local-check.txt` | proof that `-X OPTIONS` with no data sends an empty body, from a local socket |

<!-- allow-unresolved-cites: findings-log/2026-10-13-commoncore-trials/FINDINGS.md — cited as the origin of the six GET 403 captures. That log lives on the open, unmerged PR #59 (head a7d90d3) and resolves on no branch until it merges. The captures were read directly at that ref and are quoted in section 3 by body digest, which a reader can check against the PR. -->