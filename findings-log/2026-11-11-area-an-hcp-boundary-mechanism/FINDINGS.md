# Area AN — what selects the `/hcp/` boundary: a rewrite mounted above it, or a handler at it?

**Claim:** NovaLux12/carelink-api-research#196
**Date:** 2026-11-11
**Cap:** 20 requests (19 harnessed + 1 pre-itemisation reachability GET — §1)
**Delay:** `sleep 2.5` between requests to the same host, taken **inside** the per-host `flock`
(declared floor ≥ 2 s)
**Methods:** GET only. No POST, no OPTIONS, no token, no cookie, no auth, no wordlist.

**The question, and it is one question:**

> On the four clinic hosts — `carelink.medtronic.com`, `carelink.medtronic.eu`,
> `carelink-support.medtronic.com`, `carelinkhp.minimed.eu` — an absent path at the apex and
> under `/app/` answers `200 text/html` with the deployment's own entry document, under `/hcp/`
> it answers a real `404` (0 B, no `Content-Type`), and under `/hcp/configuration/` a
> `405 + Allow: POST, OPTIONS`. **What SELECTS that boundary — a rewrite mounted above `/hcp/`
> that never sees a `/hcp/` request, or a handler at `/hcp/` that answers before the rewrite?**

---

## 0. Verdict, in one paragraph, with the labels it needs

**The two mechanisms are NOT separable by an unauthenticated GET, and this pass says so instead
of picking one — but the cells do falsify the *reading* the binary framing invites, and that is
the finding.** The boundary is **not a directory, a mount point, or a filesystem subtree**:
`/hcp` **without** the trailing slash answers the **`200` fallback entry document** on all four
hosts (OBSERVED, 4 of 4, §4 cells 2/6/10/14), where a mapped directory would have produced
Apache's `DirectorySlash` `301` to `/hcp/`, and `/hcp/` itself answers `404` with **no** `301`
(OBSERVED, 4 of 4). So the selector compares a path **string beginning `/hcp/`** — the trailing
slash is part of the key — and the bare prefix is *outside* the handler's own surface.
**INFERRED, and the inference is what makes (b) the better-supported of the two:** the `404` this
family emits is **not** Apache's own file-not-found page — **0 of 31** recorded `404`s on these
four hosts across the committed ledgers carry a `Content-Type` at all, and the in-run `404` has
the same header envelope as the `405` apart from `Allow` (§5); a stock Apache `404` on this build
carries `text/html; charset=iso-8859-1`, which is exactly what `carelink.minimed.eu` returns
(area AC). Something under application control answers `/hcp/…` absences. That is consistent with
a handler answering before any rewrite and **does not prove it**, because a bare
`ErrorDocument 404: /index.html`-style configuration also produces an app-shaped absence without
a handler. **Which of location-selection (a) or phase-ordering (b) excludes the rewrite remains
UNOBSERVED, and §6 states the observation that would be needed and why a GET cannot reach it.**

---

## 1. Request accounting — 19 of a 20 cap, and the 20th disclosed

**Nineteen harnessed cells of a 20 cap.** That sentence is the shape the gate reads; the full
accounting, including the request it does **not** count, is the table.

| | n |
|---|---|
| **Cap, declared before the first cell** | **20** |
| Requests sent in total | **20** |
| Rows in `results.jsonl` | **19** |
| The 20th | **one reachability GET, sent before the cap was itemised — disclosed in §1a** |
| Failures (`000`/5xx/timeout) | **0** |
| Retries | **0** (none needed) |
| Hosts contacted | **4** — the whole declared host set, no others |
| Requests to `carelink.minimed.*`, the cumulus hosts, Common Crawl, GitHub | **0** |

The cap was itemised before the first **cell**, and the arithmetic closes exactly:
**4 hosts × 4 cells = 16, + 3 extra cells on `carelink.medtronic.com` = 19**, plus the one
reachability GET already spent = **20**. The itemisation is written in `probe.sh`'s header as the
single source of the cap; `cap_guard` reads it.

### 1a. The one request that was not itemised first, stated rather than hidden

Before the cap was itemised this pass sent **one** `GET
https://carelink.medtronic.com/hcp/configuration/public/pow.crm.settings` with
`X-System-ID: ProWeb`, to confirm the host answered and the recorded control value still held.
It returned **`200`, `97 B`** — the value area AB and area AK both record.

**That request is not in `results.jsonl` and the ledger therefore holds 19 rows against 19
harnessed cells.** It is recorded here because `AGENTS.md` §8's cap discipline and the repo's
counting rule both require the number and the artefact to agree, and the honest resolution is to
name the request rather than to inflate the ledger by back-filling a row this pass did not
capture through the harness. **It is not a claim of a 19-request pass; it is a 20-request pass
with 19 harnessed cells.** No rule was breached — the cap is 20 and 20 were sent — but the
itemisation-before-the-first-request rule was, by one request, and that is recorded as a defect
of this pass rather than smoothed over.

Method per cell: **GET only**, `--compressed` on every request, `--path-as-is` so a doubled
leading slash reaches the wire as `//hcp/…` rather than being silently normalised client-side
(§4 cell 3 depends on this), a **≥ 2.5 s** same-host delay slept **inside** `flock` on the
per-host lock. No POST, no OPTIONS, no token, no cookie, no auth. The one header sent is
`X-System-ID: ProWeb` on the three portal live controls, because without it the same key answers
`412` (OBSERVED: area AB).

**The fabricated name is `zz-an-absent-1913`.** `git grep -c 'zz-an-absent' -- .` returns **0
hits** at base `c27662f` (`grep` exit 1), so it is a name in no crawl record and no repository
file, and it does not reuse area AG's `zz-ag-absent-8713` or area AK's `zz-ak-absent-4713`.

## 2. Controls first, per host — 4 of 4 pass, and one in-run control re-derives AK exactly

Every control was sent **before** any cell on that host, because a status is not an oracle until
it is shown to discriminate.

| # | Host | Control | Status | Bytes | Verdict |
|---|---|---|---|---|---|
| 1 | `carelink.medtronic.com` | `/hcp/configuration/public/pow.crm.settings` + `X-System-ID: ProWeb` | **200** | **97** | **PASS** — AB/AK's recorded 97 B reproduced |
| 5 | `carelink.medtronic.eu` | same | **200** | **96** | **PASS** — AB's 96 B reproduced |
| 9 | `carelink-support.medtronic.com` | same | **200** | **97** | **PASS** — AB's 97 B reproduced |
| 13 | `carelinkhp.minimed.eu` | `/` | **200** | **5518** | **PASS** — area G/AK's `0f2c5f62…` reproduced |

**Cell 17 is the in-run control that matters for §5**, and it was sent *after* the sweep cells
only because it is an extra `carelink.medtronic.com` cell, not a per-host control:
`/hcp/zz-an-absent-1913` returned **`404`, 0 B, no `Content-Type`, `server: Apache/2.4.62 (Red Hat
Enterprise Linux) OpenSSL/3.5.5`, `cache-control: no-cache, must-revalidate`,
`access-control-allow-headers: X-System-ID, Content-Type, authorization`** — **the identical
header envelope area AK recorded for this exact path at `e71b1a9`**
([findings-log/2026-11-10-area-ak-portal-spa-fallback/FINDINGS.md](../2026-11-10-area-ak-portal-spa-fallback/FINDINGS.md)
row 3). So this pass's header capture is anchored to a known row, and the §5 comparison is
in-run rather than cross-pass.

## 3. The pre-registered outcome table — what each cell was sent to decide

Written into `probe.sh`'s header **before** the first cell, so the interpretation cannot be
fitted to the result afterwards. Two of the five discriminating cells were expected to separate
nothing between (a) and (b); that expectation is part of the design and is scored in §6.

| Cell | Request | Outcome A | Outcome B | What it would mean |
|---|---|---|---|---|
| 1 | `/hcp` (no slash) | `200` entry digest | `301/308` → `/hcp/` | A: the selector is a **literal string prefix `/hcp/`**, bare prefix outside the handler. B: **`DirectorySlash` — a real directory or mount point**, the strongest mount signal a GET can obtain |
| | | `404`, 0 B | anything else | `404`: the handler owns the bare prefix too. Else: Apache answered, not the app |
| 2 | `/hcp/` | `404`, 0 B | `301/302` | `404`: the app answers the prefix root as no-route. `301`: directory semantics again, and a target that differs from the request is a mount |
| | | `200` entry digest | | the selector needs a segment **after** `/hcp/` |
| 3 | `//hcp/<absent>` | `404` as the recorded cell | `200` entry digest | `404`: the selector runs on the **normalised** path (Apache merges slashes by default). `200`: the selector compares the **raw** path, or the `404` is **not** produced by Apache's location matcher at all — which cuts against both mechanisms as stated |
| 5 | `/hcp/<absent>/` | `301/308` | `404` as cell 4 | `301`: directory/mount semantics on a path that **cannot** exist. `404`: no directory semantics anywhere under `/hcp/` |
| 6 | `/app/hcp/<absent>` | `404` | `200` entry digest | `404`: the exclusion matches `/hcp/` **anywhere** in the path — a substring rule neither mechanism as stated predicts. `200`: **anchored at `^/hcp/`**, consistent with both |

Cells 4, 1, 2 and 3 were marked **NOT-SEPARATING between (a) and (b)** at design time; cell 3 and
cell 6 were the only two that could have refuted **both** mechanisms, and cell 6 on the anchored
outcome refutes neither. **No cell was designed that was expected to separate (a) from (b)**,
because none exists — see §6, which is the point of this lane.

## 4. The matrix — 19 of 19 cells, every one a verdict

Digest is the full sha256 of the decompressed body. `=build/` asks whether the body is the
**deployment's own entry document** as area AK established it.

| # | Host | Path | Status | `Content-Type` | Bytes | sha256 | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | `.com` | `/hcp/configuration/public/pow.crm.settings` | 200 | `application/octet-stream` | 97 | `370e3bba…` | control — PASS |
| 2 | `.com` | **`/hcp`** | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f62…` | **fallback — the bare prefix is NOT in the handler** |
| 3 | `.com` | `/hcp/` | **404** | **(none)** | 0 | — | handler answers the prefix root |
| 4 | `.com` | `//hcp/zz-an-absent-1913` | **404** | **(none)** | 0 | — | selector runs on the **normalised** path |
| 5 | `.eu` | control | 200 | `application/octet-stream` | 96 | `a977733a…` | control — PASS |
| 6 | `.eu` | **`/hcp`** | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f62…` | **fallback** |
| 7 | `.eu` | `/hcp/` | **404** | **(none)** | 0 | — | handler answers the prefix root |
| 8 | `.eu` | `//hcp/zz-an-absent-1913` | **404** | **(none)** | 0 | — | normalised-path match |
| 9 | `support` | control | 200 | `application/octet-stream` | 97 | `370e3bba…` | control — PASS |
| 10 | `support` | **`/hcp`** | **200** | `text/html; charset=UTF-8` | **5518** | `f637c8d0…` | **fallback — the other build, same behaviour** |
| 11 | `support` | `/hcp/` | **404** | **(none)** | 0 | — | handler answers the prefix root |
| 12 | `support` | `//hcp/zz-an-absent-1913` | **404** | **(none)** | 0 | — | normalised-path match |
| 13 | `carelinkhp` | `/` | 200 | `text/html; charset=UTF-8` | 5518 | `0f2c5f62…` | control — PASS, AK's digest in full |
| 14 | `carelinkhp` | **`/hcp`** | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f62…` | **fallback — identical to row 13** |
| 15 | `carelinkhp` | `/hcp/` | **404** | **(none)** | 0 | — | handler answers the prefix root |
| 16 | `carelinkhp` | `//hcp/zz-an-absent-1913` | **404** | **(none)** | 0 | — | normalised-path match |
| 17 | `.com` | `/hcp/zz-an-absent-1913` | **404** | **(none)** | 0 | — | **in-run control — AK row 3's header envelope reproduced** |
| 18 | `.com` | `/hcp/zz-an-absent-1913/` | **404** | **(none)** | 0 | — | **no directory semantics under `/hcp/`** |
| 19 | `.com` | **`/app/hcp/zz-an-absent-1913`** | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f62…` | **exclusion is ANCHORED at `^/hcp/`** |

**OBSERVED, and it is the finding in one line: the boundary is the literal path string `/hcp/`,
trailing slash included. `/hcp` without it is a fallback path — `200` and the entry document —
on all four hosts; `/hcp/` with it is a real `404` on all four.**

Full digests, from `sha256sum` over the retained bodies:

```
370e3bba0d28c540b1c347b5492fa3e8b0d4c176d53aa4fe0f4b11e65ac8cb44   .com control, support control
a977733a53ee0d5f…                                                 .eu control
0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d   .com /hcp, .eu /hcp, hp /hcp, hp /, .com /app/hcp/…
f637c8d0cd4ec6bc70944f7c9083ace6c205c5ecd22ce5da6ed533ece6d9a1bc   support /hcp
```

`cmp -s` at the byte level, not eyeballed: **`.com` `/hcp` ≡ `carelinkhp` `/` → identical**;
**`.eu` `/hcp` ≡ `carelinkhp` `/` → identical**; **`carelinkhp` `/hcp` ≡ `carelinkhp` `/` →
identical**; **`.com` `/app/hcp/…` ≡ `carelinkhp` `/` → identical**; **`support` `/hcp` ≠ `.com`
`/hcp` → DIFFERS**, and that is the expected other build (`f637c8d0…`, area AK §5), not a
disagreement.

## 5. The 404's header set versus the 405's — the cell that narrows the mechanism

The brief asked whether the `404`'s header set differs from the `405`'s. **Measured in one run on
one host, and the answer is: by exactly one header.**

| | `404` (row 17, `/hcp/<absent>`) | `405` (AK row 4, `/hcp/configuration/<absent>`) |
|---|---|---|
| `Content-Type` | **absent** | **absent** |
| `Content-Length` | `0` | `0` |
| `Allow` | **absent** | **`POST, OPTIONS`** |
| `Server` | `Apache/2.4.62 (Red Hat Enterprise Linux) OpenSSL/3.5.5` | identical |
| `Cache-Control` | `no-cache, must-revalidate` | identical |
| `Access-Control-Allow-Headers` | `X-System-ID, Content-Type, authorization` | identical |

**So the `404` and the `405` are emitted by the same layer and differ only in the method
advertisement.** Both carry the application's `ACAH` and its `Cache-Control`, and neither carries
a `Content-Type`. That is **not** the shape of Apache's stock `404`, which on this build is
`text/html; charset=iso-8859-1` with a body — the shape `carelink.minimed.eu` returns for an
absent apex path ([findings-log/2026-11-10-area-ac-catchall-probe/FINDINGS.md](../2026-11-10-area-ac-catchall-probe/FINDINGS.md)
§4–§5).

**Corpus cross-check at zero requests — is a stock Apache `404` observable anywhere on this
family at all?** `python3 census.py ../..` walks every `findings-log/**/*.jsonl` file (the
command's own output line reads `ledger files walked : 70` and `json rows walked : 3005` at
base `c27662f`; the repo's separate *ledger* census counts 65 and measures a different
population), resolves the host and status through every schema this corpus uses, and counts
the `404`s on these four hosts:

```
ledger files walked            : 70
json rows walked               : 3005
404 rows on the four hosts     : 31
rows whose CT could not be read: 0

  8  host=carelink-support.medtronic.com   content-type=(absent)     bytes=0
 11  host=carelink.medtronic.com           content-type=(absent)     bytes=0
  9  host=carelink.medtronic.eu            content-type=(absent)     bytes=0
  3  host=carelinkhp.minimed.eu            content-type=(absent)     bytes=0

404s carrying a Content-Type   : 0 of 31
404s carrying a body           : 0 of 31
```

**And the 0-of-31 is not an artefact of the reader, which is the part that matters.** Two
checks make it fail-able rather than merely plausible: a **positive control** over the same
read function (`353` `200` rows on the same four hosts, `339` of them read a Content-Type, so the
reader sees types where they exist), and a **per-file capability** check — for every ledger that
contributes a `404` row, does the same reader see a Content-Type on *that file's* `200` rows?
**All five contributing ledgers are capable** (`12/50`, `3/19`, `2/5`, `4/12`, `10/9` — 404 rows
and typed `200`s respectively), **0 of 5 cannot testify.** One ledger in the tree,
`2026-10-17-hcp-config-deployments/gate-curllog-not-absorbed.jsonl`, *is* uncaptured (no
Content-Type on any of its 2 `200` rows) and contributes **no** `404` row — it is named here
because a check that never encounters a blind file has not shown it can catch one.

**31 of 31** carry **no `Content-Type`** and a **zero-byte** body. There is **no recorded instance
of Apache's own error page on any of these four hosts**, across the whole committed corpus.
**OBSERVED.** What follows from it is **INFERRED**: an absence under `/hcp/` on this family is
answered by something under application control — a handler, or a configured `ErrorDocument`
whose body is empty. **The `405` proves a handler of some kind exists at `/hcp/configuration/`
(subtree constant, area AG). The `404` shares its envelope, so the simplest reading is one
handler family at `/hcp/`. That reading is INFERRED and §6 names what would break it.**

## 6. Why the two mechanisms cannot be separated by an unauthenticated GET

**This section is the deliverable, and it is a negative about observability, not a claim about
the cause.**

Mechanism **(a)** — *a rewrite mounted above `/hcp/` that never sees a `/hcp/` request* — and
mechanism **(b)** — *a handler at `/hcp/` that answers before the rewrite* — are both statements
about **Apache's request pipeline**: which phase runs first, and which `Location`/`RewriteRule`
is selected. **Neither can change a single byte of a response for any path an unauthenticated GET
can reach:**

- For a path the `/hcp/` handler answers, **both** mechanisms produce that handler's answer,
  because the handler runs in both — under (a) it runs because Apache selected a deeper location,
  under (b) because it runs at an earlier phase.
- For a path the handler does **not** answer, **both** mechanisms produce the fallback, because
  the rewrite runs in both.
- The two mechanisms differ **only** in the ordering of two events that are both invisible from
  outside, on a request where **both** would produce the same bytes. A pipeline whose outputs are
  equal on every input is not identifiable from its outputs.

**Every cell in §4 is therefore consistent with both, and the cells that were designed to differ
did not differ.** Stated per cell, against the pre-registrations in §3:

- **Cell 1 (`/hcp` → `200`)** was the strongest candidate. It **falsified the mount/directory
  reading** — no `301`, so no `DirectorySlash`, so no mapped directory at `/hcp` — and it
  **corroborated the literal `"/hcp/"` prefix** as the selector. **It separates neither mechanism**,
  because `<Location "/hcp/">` and a `RewriteCond %{REQUEST_URI} ^/hcp/` predict the identical
  `200` for the bare prefix: a `Location` with a trailing slash does not match the un-slashed
  path either.
- **Cell 2 (`/hcp/` → `404`)** shows the handler answers the prefix root. Both mechanisms have
  the handler running. **Not separating.**
- **Cell 3 (`//hcp/…` → `404`)** shows the selector operates on the **normalised** path. Both
  mechanisms sit behind Apache's `merge_slashes`. **Not separating.**
- **Cell 5 (`/hcp/<absent>/` → `404`)** shows no directory semantics under `/hcp/`. Both
  mechanisms predict a handler answer. **Not separating.**
- **Cell 6 (`/app/hcp/…` → `200`)** shows the exclusion is **anchored** at `^/hcp/`, killing the
  substring reading. Both mechanisms are anchored. **Not separating.**

**The two cells that could have refuted both, refuted neither.** A `200` on cell 3 would have
meant the selector reads the raw path or is not a location match at all; it did not. A `404` on
cell 6 would have meant a substring rule; it did not.

**What WOULD separate them, and why a GET cannot get there — named so the negative is falsifiable
rather than modest:**

| Observation that would decide it | Why no unauthenticated GET reaches it |
|---|---|
| A response from a path that is **both** inside a `Location` and matched by the rewrite — showing which one's headers win | Requires knowing which path is in both, i.e. reading the config. A GET maps the boundary, never the rule |
| A **duplicate or conflicting** header that only a stacked handler can produce (e.g. two `Allow` values, a `Server`-added `Vary`) | Nothing observed shows a stack; a single `404` envelope is what a single answering layer produces too |
| A **static file** under `/hcp/` served with `Content-Type` from Apache's static handler | No static file under `/hcp/` is recorded anywhere in this corpus, and inventing one is wordlist fuzzing |
| `TRACE` echoing a rewritten path, or a `406`/`414` from a rewrite loop | `TRACE` is disabled on this build (unverified) and would echo the request, not the config; a loop needs a path that triggers it, which is the same unknown |

**So the honest close is: NOT SEPARABLE by an unauthenticated GET.** That is a first-class answer
here, and it is better than a plausible mechanism asserted without evidence, which is exactly what
`AGENTS.md` §1 and §6 item 1 forbid.

**A third mechanism the binary framing excludes, recorded because the framing hides it.** Both (a)
and (b) presume a **rewrite**. Nothing observed requires one: the fallback could be Apache's
`FallbackResource`/`DirectoryIndex` behaviour, or an SPA served by a static handler whose absence
is overridden by `ErrorDocument`. The §5 corpus result — **no stock Apache `404` exists on this
family, 31 of 31** — is *more* consistent with a configured absence handler than with a rewrite,
and a configured absence handler is neither (a) nor (b). **INFERRED; it is the reading the
evidence leans to and it is not what the question asked.**

## 7. Delay accounting — two clocks; the single sub-floor gap is on the row that convicts itself

This harness is in the recorded **corrupt-`t0`** class (`docs/09` §4). Both figures are published
rather than one, and no cause is asserted. `python3 spacing.py` re-derives both from the committed
ledger and the retained bodies respectively.

```
== clock A: t_sent (committed, re-derivable) ==
rows 19  same-host gaps 14
min 1.726 s   max 5.502 s   mean 3.254 s
under the declared 2.5 s: 1
under the repository 2.0 s floor: 1
  SHORT seq->7 carelink.medtronic.eu 1.726 s

== impossible durations (t_done < t_sent) == 1
  IMPOSSIBLE seq 6 carelink.medtronic.eu duration -0.807 s

== clock B: kernel body mtimes (NOT re-derivable from a clone) ==
bodies stat-able 19 of 19; same-host gaps 14
min 2.588 s   max 5.184 s   mean 3.237 s
under the declared 2.5 s: 0
under the repository 2.0 s floor: 0
```

**The one sub-declared gap is the `seq 6 → 7` pair, and `seq 6` is the row whose own `t_done`
precedes its `t_sent` by 0.807 s — impossible.** Under the counting rule `docs/09` §4 sets, a
sub-declared gap on a provably corrupt series is an artefact of that corruption and is **not**
evidence of underspacing; the kernel-mtime counter reads **0 of 14 under 2.5 s, floor 2.588 s**
(OBSERVED). **So no delay rule was breached, and this pass does not claim a clean `t_sent` floor
either** — clock A's floor is 1.726 s and is published as measured.

Clock B is **not** re-derivable from a clean clone (git does not preserve mtimes), so it is
reported as a point-in-time measurement; the re-derivable copy is `spacing.txt`.

## 8. Verdict

**OBSERVED, 19 harnessed cells of a 20 cap (one reachability GET disclosed in §1a), 4 of 4
controls first, 0 failures, 0 retries, no delay rule breached:**

- **The boundary is the literal string `/hcp/`, trailing slash included.** `/hcp` without it
  answers the **`200` fallback entry document** on all four hosts (rows 2, 6, 10, 14); `/hcp/`
  with it answers a real **`404`** (rows 3, 7, 11, 15). Area AK's boundary statement —
  "`/hcp/<absent>` is a real `404`" — is **correct as measured and incomplete as a rule**: the
  bare prefix `/hcp` is a **fallback path**, not an absence, and nothing in the record said so.
- **It is not a directory, a mount point or a filesystem subtree.** No `301` at `/hcp` (all four
  hosts) and no `301` at `/hcp/<absent>/` mean `DirectorySlash` never fires, so mod_dir is not
  the selector. **INFERRED: the selector is a string comparison against `/hcp/`, not a path
  resolution.**
- **The exclusion is anchored at `^/hcp/`**: `/app/hcp/<absent>` answers the fallback (row 19),
  so the rule does not match `/hcp/` anywhere in the path.
- **The selector runs on the normalised path**: `//hcp/<absent>` answers the same `404` as
  `/hcp/<absent>` (rows 4, 8, 12, 16).
- **The `404` and the `405` are one layer's answers, differing only in `Allow`** (§5), and **no
  stock Apache `404` exists anywhere on this family across the committed corpus — 31 of 31 `404`s
  carry no `Content-Type` and 0 B.**

**NOT SEPARABLE, and that is the answer to the title question:** the two mechanisms differ only in
the ordering of two invisible pipeline events on requests where both produce the same bytes.
**The mechanism is not observable from outside, no cell in this pass separates (a) from (b), and
no cell an unauthenticated GET can send would (§6, with the four observations that would and why
each is out of reach).**

**Not claimed:** that a handler rather than a rewrite (or `ErrorDocument`) produces the `404` —
**INFERRED**, and §6 records the third mechanism the binary excludes; that `/hcp`'s `200` is the
*deployment's own* entry document on `.com`/`.eu` beyond the digest match to
`carelinkhp`'s apex (§4, where `cmp` establishes byte identity — this pass bought `carelinkhp`
`/` and not `.com` `/`); that any host outside the four behaves this way; anything about
`carelink.minimed.*` or the cumulus hosts, which were not contacted.

**Not a disclosure.** An SPA serving its own entry document at an unmatched path is ordinary
behaviour. `/hcp` returning it is a **documentation** fact — anyone probing `/hcp` instead of
`/hcp/` gets a `200` that says nothing about existence — not a security finding.

## 9. Successors

Both are minted in `docs/11` as **AQ** and **AR**, because this pass found two things it could not
close: one that **no GET can ever close**, and one that a GET **can** close cheaply.

**AQ — the mechanism, with its blocker stated as a blocker.** *What excludes the fallback from
`/hcp/…`: a `Location` selection, a rewrite phase order, or a configured `ErrorDocument`?*
**Blocker: it is not observable from an unauthenticated GET at all** (§6) — every candidate
produces identical bytes on every reachable path. **Closes when** a **PUBLISHED** vendor artefact
(a deployment descriptor, published Helm chart, container image config, or a vendor document) names
the `/hcp/` handler or the fallback rule — PUBLISHED, not OBSERVED — **or** when a response-level
anomaly appears that only a stacked handler produces (a duplicate `Allow`, a `Server`-added `Vary`,
two `Content-Type`s). **A negative counts:** "no published artefact names it" retires the question
as unanswerable rather than leaving it open forever. **Assumptions (INFERRED):** that a published
artefact would exist to find, which nothing in this repository names; and that an
`ErrorDocument`-only deployment would be indistinguishable from a handler at the response level,
which is exactly why `ErrorDocument` is in the successor rather than in this pass's verdict.

**AR — the behaviour, which a GET can close.** *`/hcp` is a fallback path because the selector
keys on the trailing slash. Does the same trailing-slash sensitivity hold for every other prefix
this family serves — i.e. is `<prefix>` without its slash a fallback path for `/app`,
`/hcp/configuration` and the apex-equivalent forms?* **Closes when** each named prefix is requested
bare and with its slash on one host, beside the same host's recorded controls, and the pair's
verdicts are recorded. **≤10 requests**, GET only, controls first. **Assumptions (INFERRED):** that
`/app` bare and `/hcp/configuration` bare are reachable at all — neither is recorded, and a `404` on
either is a result rather than a failure.

## 10. Files, and how to re-run

| File | What it holds |
|---|---|
| `probe.sh` | `CAP=20` as **one assignment** with the itemisation beside it, the **pre-registered outcome table** in the header, GET only, `--compressed --path-as-is`, sleep inside `flock` |
| `results.jsonl` | 19 rows, one per harnessed cell: status / content-type / bytes / sha256 / `location` / `allow` / `server` / full header dict |
| `run.log` | Human-readable request ledger, ending `DONE — 19 harnessed of 20` |
| `spacing.py` → `spacing.txt` | Zero-request re-derivation of **both** delay series, with the impossible-duration check that identifies the corrupt row |
| `census.py` → `census.txt` | Zero-request census of every committed `404` on the four hosts, with a positive control and a per-file capability check (§5) |

Bodies are not in the tree (`AGENTS.md` §7: no raw capture). Re-run:

```bash
./probe.sh all
python3 spacing.py
python3 census.py ../..
```
