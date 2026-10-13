# Findings — is `ACAO` on the `commoncore*` hosts method-conditional?

Correction issue [#61](https://github.com/NovaLux12/carelink-api-research/issues/61), method
half. Branch `research/x-cors-method`, 2026-10-13. Not the scope-vs-verdict decision that
issue names — see §6.

**One line: on the `commoncore*` no-route error, no. `access-control-allow-origin: *` is
emitted identically on `GET` and on empty-body `OPTIONS` — 8 of 8 cells, 2 hosts, byte-identical
bodies — so within that error the header is **not method-conditional**, and the corollary
matters more than the verdict: an `OPTIONS` response carrying `ACAO: *` here is *not* proof
that a resource exists.**

**What this is *not*, stated up front because an earlier draft of this note over-reached and
the docs had to be corrected separately (`AGENTS.md` §6 item 5).** It is **not** a claim about
path-conditionality. All 8 cells returned the same no-route envelope, so **no cell in this
design was ever matched by the gateway** — there is no contrasting cell, and a claim about
path-conditionality needs one matched and one unmatched. What the path axis actually shows is
narrower and is the point: **`ACAO` does not discriminate between the path the
2026-10-13 pass recorded and a certainly-absent path, because this gateway returns the same
no-route response for both.** See §3.2.

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
| A | `GET` | `/reports-broker/v1/ocl` | the path the 2026-10-13 pass recorded — **observed to answer identically to cell B, so it is NOT a positive control** (§3.2) |
| B | `GET` | `/reports-broker/v1/ocl-probe-absent` | **absence control** — certainly absent |
| C | `OPTIONS` (empty body) | `/reports-broker/v1/ocl-probe-absent` | **the cell the question turns on** |
| D | `OPTIONS` (empty body) | `/reports-broker/v1/ocl` | completes the path × method matrix |

⚠ **Correction, 2026-10-13, verification round of PR #65: cell A was mislabelled
`CONTROL-A-positive-recorded-path`, and it is not a positive control.** A positive control has
to discriminate from its own negative. Cell A returns the **same bytes** as the absence
control B — same status, same headers, same body digest — so on this host family it is
a repeat of the negative rather than a control over it, and the reasoning that made it look
like a control was circular (§3.2).

The label is retracted wherever it appears as prose: this table, §3, the `docs/11` addendum and the
PR body, and in `probe.sh` itself, which now records the cell as `RECORDED-PATH-not-a-control`.

**`results.jsonl` is deliberately left as sent.** Its `seq 17` and `seq 21` rows still read
`CONTROL-A-positive-recorded-path`, and that is the point: the ledger is the record of what
was sent and recorded, and a post-hoc rewrite of a ledger is exactly the move `docs/09` §4 records
as undetectable. The correction lives beside the evidence, not inside it.

What cell A does establish is recorded in §3.2 and is worth having. It is just not a control.

The candidate list is **two paths**, both already on disk; nothing was invented and nothing
was fuzzed. No `Origin` header was sent in any cell, matching the six captures this pass
follows — verified per request in `headers/NN-*.sent.h`, where `origin` appears **0 times**
across all 8.

`commoncore-trials.minimed.com` was **not probed** — see §5.2.

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

⚠ **Correction, after the verification round: this section validated the wrong series, and
the retraction stays visible.** The check published first — *"mtime span 19.651 s against
`t_sent` span 19.546 s, a difference of **+0.105 s across 8 requests**"* — is **worthless**,
and the verifier was right to reject it. `mtime_span − t_sent_span` is arithmetically
identical to `dur[n] − dur[1]`: it is computed from `t_sent` and `t_done` **alone and never
touches the mtime series**, so it is arithmetically incapable of telling a sound mtime series
from an unsound one. The old text also attributed the difference to "one request duration, not
the sum of them", which is a restatement of that identity rather than an explanation.

**The check that does discriminate is against `t_done`** — the stamp taken when curl returns,
immediately after the body is written, which is what a body-write mtime physically
corresponds to:

| | value |
|---|---|
| mtime span | 19.651294 s |
| `t_done` span | 19.651000 s |
| **difference** | **+0.000294 s over 8 requests** |
| per-row `mtime − t_done` | **−0.0035 … −0.0045 s on 7 of 8 rows**; `seq 18` is −0.4218 s |

Seven of eight rows agree to about **4 ms**, which is what the pair is *supposed* to look
like: the kernel stamps the body, curl exits, `date` runs. That is a physical correspondence,
not a coincidence of arithmetic, and it is the check `spacing.py` §3 now runs.

**And the harness series is demonstrably the faulty one here, on its own testimony.** Per
row (`spacing.txt` §4): `seq 23` records `t_sent` 15:50:51.525 and `t_done` 15:50:51.191 — a
**negative duration of −0.334 s**, which is impossible, and it is precisely the row that
manufactures the apparent **2.273 s** gap in the `t_sent` series where the kernel mtimes read
**2.753 s**. `seq 18` is the mirror image: a 0.564 s duration against 40–393 ms everywhere
else, and 0.42 s later than its own body write. Two bad readings from one clock, in opposite
directions. This is the **sixth pass** to exhibit the documented signature and the first with
**both series in one ledger plus an impossible duration to name**, so no cause is asserted —
only that the requests were spaced correctly and the `date` readings are what moved.

**Resolution, recorded because the rule I added to `docs/09` demands it.** The ledger's own
`body_mtime_epoch` is at **integer-second** resolution and cannot separate 2.737 from 2.744,
so it does **not** satisfy the rule I wrote. `spacing.py` §1 therefore prints the whole mtime
series at **microsecond** resolution, and that printed series is the copy a verifier has —
git does not preserve mtimes, so a fresh clone cannot re-derive it from the files.

---

## 3. The result

Per host, per path, per method. **8 of 8 cells carry `ACAO`, `ACAM` and `ACAH`; none carries
`Access-Control-Allow-Credentials`, `Allow` or `Vary`.** All 8 are `403`
`MissingAuthenticationTokenException`, `application/json`, **42 B**, and all 8 share one body
digest `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16` — byte-identical to
each other **and to the six captures in PR #59**. That byte-identity is **not** a control
passing; see §3.2 for what it does and does not establish.

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

Read against the two axes, **separately and with different verdicts**, because they are not
the same claim:

- **Method axis — this one has contrast, and it is a real result.** `GET` and `OPTIONS` were
  sent to the *same path*, and the header sets are indistinguishable. Two methods, one path,
  no difference: the header is **not method-conditional** on this no-route error.
- **Path axis — this one has no contrast at all, and no claim is made.** The recorded path and
  the certainly-absent path are indistinguishable down to the body digest, but that is not a
  finding about path-conditionality: **every cell returned the same no-route envelope, so
  nothing was ever matched** (§3.2).

**`access-control-allow-methods: *` appears on a response for a path that does not exist.**
`docs/09` §4 is explicit that `allow-methods` is gateway CORS configuration and **not** a
register of a route's methods, and this is a second, independent instance of that: the `*`
here is on a `MissingAuthenticationTokenException` — the `docs/09` §2 no-route error — so it
describes the **stage**, not any route. Recorded as an observation about the stage. It is not
read as a method list.

### 3.2 What the path axis actually shows, and why cell A is not a control

**The recorded path is byte-identical to a path the gateway has never heard of.** All 8
cells share one header set and one body digest, so `/reports-broker/v1/ocl` — the path the
2026-10-13 pass recorded — answers exactly as `/reports-broker/v1/ocl-probe-absent` does.
That is a real and useful observation, and it is what this pass actually has:

> **`ACAO` does not discriminate between the path a prior pass recorded and a certainly-absent
> path, because this gateway returns the same no-route response for both.**

It is **not** a claim that the header is "not path-conditional". A path-conditionality claim
needs one matched cell and one unmatched cell; this design has **zero matched cells**, so the
question is untested rather than answered. An earlier draft of this note said "neither
method-conditional nor path-conditional" and `docs/09`, the `docs/11` addendum and the PR body
carried it — `AGENTS.md` §6 item 5, derived prose contradicting its own source table. The
path claim is retracted here and removed everywhere it appears.

**Cell A is therefore not a positive control** (§2.1). Two independent reasons, and the second
is the one that matters:

1. A positive control must discriminate from its own negative. Cell A returns the same bytes
   as the absence control B.
2. The original argument was circular: §3 proved the 8 cells identical *to each other*, then
   cited that identity as the control "passing". All 8 reproduce the six PR #59 captures, so
   reproduction discriminates nothing — it is the same fact counted twice.

**What cell A is worth.** It establishes that the path recorded on 2026-10-13 is **not routed
**on this stage**, which the six captures could not show on their own (they had no contrast
cell either). The verification round confirmed it live and independently, on a **third**,
previously unseen certainly-absent path.

**Corroboration relayed by the verification round of PR #65 — second-hand, and labelled as
such.** The verifier reports four further live requests, including `GET` and empty-body
`OPTIONS` against `/reports-broker/v1/ocl-verifier-absent`, a path never sent by this pass,
reproducing `403` / 42 B / `f249b63c…` / `ACAO: *` / `ACAM: *` / `ACAH: *` on every one.
**No capture from those requests is committed in this repository, so a reader cannot
re-derive them from this tree.** They are recorded here as reported, not as my own rows, and
they are not counted in my ledger, my cap or my spacing. What they would add, if accepted: a
*third* absent path, from a session that never saw mine, showing the same envelope — which is
stronger evidence for the §3.2 observation above than my own two paths, because it cannot be
an artefact of my candidate list.

**Corroboration that is committed, and that I did not cite — `clcloud.*` behaves the
opposite way on the same error.** `regression/hurl/04-deep-surface.hurl:182` records, in the
suite's own words, that the `clcloud.minimed.eu` negative cells are *"All GET+OPTIONS 403 with
MissingAuthenticationTokenException and **no CORS**"*, and
`regression/hurl/04-deep-surface.hurl:444` **asserts** it —
`header "access-control-allow-origin" not exists` on a `401` carrying `x-ca-err: 990`. Same
error family, **opposite header behaviour, on a different stage, already pinned.** That is
independent support for the sharpest thing this pass has: **the CORS header is a property of
the stage's configuration, not of the error type** — which is exactly why the header cannot be
read as evidence about a route. The pin is untouched by this branch. It also frames the
boundary honestly: `04-deep-surface.hurl:424` lists reading (c), *"`ACAO` is emitted only on
`OPTIONS` responses regardless of route"*, as still **unresolved on `clcloud.*`**, and this
pass excludes it for `commoncore*` **only**.

---

## 4. What this settles

**OBSERVED.** On `commoncore-trials.medtronic.com` and `commoncore.medtronic.com`, the
`access-control-*` set is **not method-conditional**: it is identical on `GET` and on
empty-body `OPTIONS` (4 cells per host, 8 total). **The bound travels with the claim: every
one of those 8 cells is a `non-2xx` no-route `403`.** This is a statement about the `non-2xx`
responses only. It says nothing about a `2xx` on either method, and nothing about any other
host family — `clcloud.*` in particular emits **no** CORS at all on the same error
(`regression/hurl/04-deep-surface.hurl:444`).
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
requests against a cap of 8, and a fourth cell per host is 12.

**The budget split, re-derived without the control argument that is now withdrawn.** The
original justification was **wrong**, for two reasons. It cited a positive control that does
not exist (§3.2). And `AGENTS.md` §8 asks for "one plausible path, one
certainly-absent path" — a plausible path that answers identically to the absent one
satisfies the letter of that rule while giving it no discriminating power, which is the same
defect wearing the rule's clothes.

The defensible reason is narrower, and it is a **trade, not a rule**: the fourth cell per
host (D, `OPTIONS` on the recorded path) is the only cell that adds a contrast, and it is
what completes the method × path square. 8 requests on 2 hosts buys a complete
matrix on each; 6 on 3 hosts buys a method pair and no square anywhere. That is the trade
this pass actually made, and it is recorded as one rather than dressed up as a rule.

Closing the third host is **4 more requests**, needs no new idea, and would extend the family
claim from 2 hosts to 3.

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

⚠ **Correction, verification round: the first version of this table published
`27fd2fdcc38bc80…` for `docs/03` and it was wrong in one hex character at index 2.** The real
value is `27dd2fdc…`; `docs/00` and `docs/10` were right. This table exists so a reader can
run the check without reading this note, and on `docs/03` the check failed. All three values
below were then re-derived from `sha256sum` rather than trusting the two that matched.

| Site | Claim lives at | Change on this branch | How to check |
|---|---|---|---|
| `docs/00-summary-the-map.md` | line 166 | **none — the whole file is byte-identical to `origin/main`** | `sha256sum` = `521fdf94ed8eec78c53f16e3a781a8573b524ea8b8d9dd95fb303fdea4f14846` on both sides |
| `docs/03-discovery-and-versions.md` | line 341 | **none — byte-identical** | `27dd2fdcc38bc80cfa1a2e528d3d78d60f43f1c6187a38a07d72f847379b1f32` |
| `docs/10-open-questions.md` | line 56 | **none — byte-identical** | `cd56c252292e7bb998aa73fcaea48116d48280a16975410ca7ddd0e806307fe4` |
| `docs/11-suggested-research-areas.md` | **line 703 at `20e4afc` → line 793 on this branch** — shifted, not edited | exactly one **insertion**, a dated addendum at line 252. No deletion and no rewrite | `git diff -U0 20e4afc -- docs/11-suggested-research-areas.md` returns a single hunk, `@@ -251,0 +252,90 @@`, i.e. a pure addition. The claim's own sentence appears on neither side of that diff |

Three of the four files are untouched outright; the fourth gained an addendum **90 lines
above the Closed table** and nothing else. `docs/09` is edited too, and its edits are in §2's CORS
paragraph and §4's timestamp row — neither of which carries any of the four claims.

**All comparisons in this table are against `20e4afc`, the commit this branch was created from.**
`origin/main` has since moved (it was at `614db77` when this note was written), so a reader who
diffs against `origin/main` today will see other workers' merged work and should not read it as a
change by this branch. The merge queue re-bases and re-checks.
**What each reading would change, quoted exactly, so the ruling does not need this log
re-read.** The claim is the string *"0 non-2xx responses carrying CORS anywhere"* (and, in
`docs/03`, *"anywhere in the corpus"*).

**Reading (a) — the claim was always scoped to `clcloud.*`; the prose over-reaches.** Then
the measurement is untouched and only the quantifier moves. Three sentences change, and
nothing else on any of the four pages:

1. `docs/11-suggested-research-areas.md`, Closed-table row **X** — **line 703 at `20e4afc`,
   line 793 on this branch — replace**
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
| `results.jsonl` | **24 rows**, one per invocation; `seq 17–24` are the 8 requests. ⚠ **Only `seq 17–24` parse as JSON.** The 16 attempt-1/2 rows are deliberately malformed — that is the record of §1 — so `jq`, `json.load`, or any whole-file sweep will choke or mis-count. `spacing.py` skips them by design |
| `run.log` | 24 ordered rows, three timestamp columns each |
| `headers/NN-*.h` | response headers verbatim; the 16 attempt-1/2 captures are 0 bytes, which is the record |
| `headers/NN-*.sent.h` | **the request as sent**, verbatim — curl's own `> ` block, from which the method, the absent `Origin` and the empty body are read |
| `bodies/NN-*.b` | response bodies. **42 B on `seq 17–24` only; the other 16 files are 0 bytes** — so a glob over `bodies/*.b` returns 16 files whose sha256 is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, the digest of the empty string. That is the §1 record, not a capture |
| `spacing.py` · `spacing.txt` | the spacing measurement, both series, counting rule and validation |
| `attempt1-exit6-demo.txt` | the failure path reproduced offline, no vendor |
| `options-shape-local-check.txt` | proof that `-X OPTIONS` with no data sends an empty body, from a local socket |

## 9. Merge conflict on `docs/09`, reported and **not** resolved by this worker

Pushed `45cd5c8`. CI did not run on it, because the PR went `CONFLICTING` while this work
was in progress: `origin/main` moved from `20e4afc` (this branch's base) to `614db77` as
other workers merged. `gh pr view 65` reports `mergeable=CONFLICTING`. A dry three-way merge
(`git merge-tree --write-tree origin/main HEAD`, no worktree touched) isolates **one** real
conflict, and it is not a formatting artefact:

- `docs/11-suggested-research-areas.md` auto-merges cleanly.
- `docs/09-methodology-and-oracles.md` conflicts, at the trap-table rows
  **"A gap below the harness's own declared `sleep`"** (which `origin/main` rewrote) and
  **"The `date` series itself is the suspect"** (which this branch rewrote). Both are single
  lines several kilobytes long, and they are adjacent, so git cannot align them.

**The conflict is between two claims, not two formats, and the merge queue's own rule says a
`docs/` conflict is not auto-resolved. So it was not resolved here, and the branch is left
parked.**

Why it is a claim conflict, concretely:

1. **The occurrence accounting disagrees.** `origin/main` now reads *"22 gaps" + DASH + "B 1, X 1, Z 5, D 14, F 1, which sums"* and
   *"**F is the fifth pass whose harness emitted the sleep**"*, with area O explicitly
   **excluded** from this class (*"contributes 0 to this class"*). This branch's row says
   *"A sixth _pass_ to exhibit this signature"*. Under main's corrected numbering the two are
   reconcilable " + DASH + " B, X, Z, D, F is five, so this pass is the sixth " + DASH + " but only if
   "sixth pass to exhibit the signature" is read as main reads it for area O. That is a
   judgement about someone else's correction, and it is not this worker's to make silently.
2. **`origin/main` publishes the check this verification round retracted.**
   `docs/09` on main now states, of area F: *"its span is 75.880 s against `t_sent`'s 75.655 s,
   agreeing to 225 ms, which is **the trustworthiness test this page sets for the mtime
   series**"*. `mtime_span " + DASH + " t_sent_span` is identically `dur[n] " + DASH + " dur[1]` " + DASH + " computed from the two `date` series
   alone, never from an mtime " + DASH + " so it cannot discriminate a sound mtime series from an unsound one
   however small the number comes out (" + SEC + "2.3, where the arithmetic is shown). **The wrong check is now
   canonical in this page, and this branch's row replaces it.** Whichever side a merge keeps,
   one contributor's validation is deleted without its author seeing it.
3. **The assertion count has moved under this branch.** `origin/main` now states
   `regression/hurl/` holds **216 assertions (430 execute)**; this branch, based on
   `20e4afc`, measures **210 / 424** and says so. `research-checks.py` passes on each branch
   separately because each is self-consistent. Merging changes the number and needs a
   re-measure " + DASH + " `merge-queue.sh` step 3 does exactly that, which is the right owner for it.

**What a resolver needs to know, so the choice is not made blind.** Both sides of items 1 and 2
are recoverable from committed artefacts: area F's numbers are in
`findings-log/2026-10-13-area-f-timeline-config/FINDINGS.md`, and the arithmetic that shows
item 2 has no discriminating power is in `spacing.txt` " + SEC + "5 and `spacing.py` " + SEC + "3. Nothing needs
re-probing; it is a decision about which published check survives.

<!-- allow-unresolved-cites: findings-log/2026-10-13-area-f-timeline-config/FINDINGS.md — exists on origin/main (merged via PR #60) but not on this branch's base 20e4afc, so it does not resolve in this worktree. It is cited in section 9 as the source of another worker's mtime figures, which is the point of that section. It resolves on any branch that has merged main. -->
<!-- allow-unresolved-cites: findings-log/2026-10-13-commoncore-trials/FINDINGS.md — cited as the origin of the six GET 403 captures. That log lives on the open, unmerged PR #59 (head a7d90d3) and resolves on no branch until it merges. The captures were read directly at that ref and are quoted in section 3 by body digest, which a reader can check against the PR. -->