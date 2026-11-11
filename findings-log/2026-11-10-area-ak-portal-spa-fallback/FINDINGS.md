# Area AK — the 5518 B fallback is prefix-scoped on all four clinic hosts, and §7 says otherwise

**The question, and it is one question:**

> `AGENTS.md` §7 documents the 5518 B `text/html` catch-all **for `carelinkhp.minimed.eu`
> only**. Area AG's certainly-absent control found `200 + 5518 B` at the **root** of
> `carelink.medtronic.com` and `carelink.medtronic.eu`, where §7 does not document it.
> **Which prefixes on which portal hosts serve that fallback, and is the body
> byte-identical to the documented `carelinkhp` one?**

**Answer: the fallback is real on all four hosts, it is scoped by PREFIX and not by host,
and §7's warning is wrong in three separate ways.** It is wrong about **which hosts** (four,
not one); wrong about the **scope** (`outside /hcp/` only — `/hcp/…` answers a real `404` on
every one of the four, *including `carelinkhp`*); and wrong to leave **size** as the
discriminator, because 5518 B is the size of **two different builds**. The scope clause is
the trap: **§7 as written invites exactly the trust in `carelinkhp` that the measurement
refutes**, since that host has a real `404` under `/hcp/` like the rest.

---

## 1. Request accounting — 20 of a 20 cap

| | n |
|---|---|
| **Cap, declared before the first request** | **20** |
| Requests sent | **20** |
| Failures (`000`/5xx/timeout) | **0** |
| Retries | **0** (none needed) |
| Hosts contacted | **4** — the whole declared host set, no others |
| Requests to Common Crawl / GitHub / any other host | **0** |
| Rows in `results.jsonl` | **20** |

The cap was itemised **before** the first request and the arithmetic closes exactly:
**4 hosts × (1 live control + 4 prefix cells) = 20.** No row of headroom was taken and none
remains — the matrix is complete, so no top-up was wanted.

Method: **GET only**, `--compressed` on every request, a declared **≥ 2.5 s** same-host
delay slept **inside** `flock` on the per-host lock. No POST, no OPTIONS, no token, no
cookie, no auth. The one header sent is `X-System-ID: ProWeb` on the three portal
known-live controls, because without it the same key answers `412`
(OBSERVED: area AB, `findings-log/2026-11-10-area-ab-hcp-direct/FINDINGS.md`). No
wordlist: four cells and one control per host, named in `probe.sh` before the run.

**The fabricated name is `zz-ak-absent-4713`.** `git grep -c 'zz-ak-absent' -- .` returns
**0 hits** at base `e71b1a9`, so it is a name in no crawl record and no repository file.

## 2. Delay accounting — two clocks, and they disagree only where the harness clock convicts itself

This harness is in the recorded **corrupt-`t0` class** (`docs/09` §4). Both figures are
published rather than one, and no cause is asserted. `python3 spacing.py` re-derives both
from committed and local data respectively — **zero requests**.

```
== clock A: t_sent (committed, re-derivable) ==
rows 20  negative durations (t_done < t_sent): 2
  IMPOSSIBLE seq 1 carelink.medtronic.com duration -0.557 s
  IMPOSSIBLE seq 9 carelink.medtronic.eu duration -0.689 s
same-host gaps 16  min 1.847 s  max 3.351 s  mean 2.658 s
under declared 2.5 s: 2
under repository 2.0 s floor: 2
  shortest carelink.medtronic.eu seq 9->10 1.847 s
  shortest carelink.medtronic.com seq 1->2 1.977 s

== clock B: kernel body mtimes (NOT re-derivable from a clone) ==
bodies stat-able 20 of 20  same-host gaps 16
min 2.595 s  max 2.844 s  mean 2.693 s   FLOOR ON THIS CLOCK: 2.595 s
under declared 2.5 s: 0
under repository 2.0 s floor: 0
```

**The two series conflict on exactly the two rows the harness clock itself convicts, and
nowhere else.** The two nominal sub-2.5 s gaps are `seq 1→2` and `seq 9→10`; `seq 1` and
`seq 9` are the two rows whose own `t_done` precedes their `t_sent` — **impossible**, so at
least one stamp on each is corrupt (OBSERVED). Under the counting rule `docs/09` §4 already
sets, a sub-declared gap on a provably corrupt series is an artefact of that corruption and
is **not** evidence of underspacing; the kernel mtime counter reads **0 of 16 under 2.5 s,
minimum 2.595 s** (OBSERVED). **So no delay rule was breached, and this pass does not claim
a clean `t_sent` floor either** — clock A's floor is 1.847 s and is published as measured.

Clock B is **not** re-derivable from a clean clone (git does not preserve mtimes), so it is
reported as a point-in-time measurement and the re-derivable copy is `spacing.txt`.

## 3. Controls first, per host — 4 of 4 pass

Sent **before** any cell on that host, because a status is not an oracle until it is shown
to discriminate.

| Host | Control | Status | Bytes | Verdict |
|---|---|---|---|---|
| `carelink.medtronic.com` | `/hcp/configuration/public/pow.crm.settings` + `X-System-ID: ProWeb` | **200** | 97 | **PASS** — reproduces area AB's recorded 200 and 97 B exactly |
| `carelink.medtronic.eu` | same | **200** | 96 | **PASS** — reproduces AB's 96 B (the `.eu` key value is one byte shorter) |
| `carelink-support.medtronic.com` | same | **200** | 97 | **PASS** — reproduces AB's 97 B |
| `carelinkhp.minimed.eu` | `/` | **200** | 5518 | **PASS** — reproduces area G's recorded entry digest `0f2c5f62…` in full |

No failure occurred, so nothing in this log reads as an absence. The three portal digests
(`370e3bba0d28c540…` twice, `a977733a53ee0d5f…`) are **byte-identical to area AB's rows**,
so the hosts are serving the documents they were serving when AB measured them.

## 4. The matrix — 20 of 20 cells, every one a verdict

Digests are the **full** sha256 of the decompressed body. `=hp/` asks the decisive question:
is this indistinguishable from the documented baseline's own entry document?

| # | Host | Path | Status | `Content-Type` | Bytes | sha256 | `=hp/`? |
|---|---|---|---|---|---|---|---|
| 1 | `.com` | `/hcp/…/public/pow.crm.settings` | 200 | `application/octet-stream` | 97 | `370e3bba0d28c540…` | control |
| 2 | `.com` | `/zz-ak-absent-4713` | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f6257a6fc6a…` | **YES** |
| 3 | `.com` | `/hcp/zz-ak-absent-4713` | **404** | **(none)** | 0 | — | no |
| 4 | `.com` | `/hcp/configuration/zz-ak-absent-4713` | **405** | **(none)** | 0 | — | no |
| 5 | `.com` | `/app/zz-ak-absent-4713` | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f6257a6fc6a…` | **YES** |
| 6 | `.eu` | `/hcp/…/public/pow.crm.settings` | 200 | `application/octet-stream` | 96 | `a977733a53ee0d5f…` | control |
| 7 | `.eu` | `/zz-ak-absent-4713` | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f6257a6fc6a…` | **YES** |
| 8 | `.eu` | `/hcp/zz-ak-absent-4713` | **404** | **(none)** | 0 | — | no |
| 9 | `.eu` | `/hcp/configuration/zz-ak-absent-4713` | **405** | **(none)** | 0 | — | no |
| 10 | `.eu` | `/app/zz-ak-absent-4713` | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f6257a6fc6a…` | **YES** |
| 11 | `support` | `/hcp/…/public/pow.crm.settings` | 200 | `application/octet-stream` | 97 | `370e3bba0d28c540…` | control |
| 12 | `support` | `/zz-ak-absent-4713` | **200** | `text/html; charset=UTF-8` | **5518** | `f637c8d0cd4ec6bc…` | **no — other build** |
| 13 | `support` | `/hcp/zz-ak-absent-4713` | **404** | **(none)** | 0 | — | no |
| 14 | `support` | `/hcp/configuration/zz-ak-absent-4713` | **405** | **(none)** | 0 | — | no |
| 15 | `support` | `/app/zz-ak-absent-4713` | **200** | `text/html; charset=UTF-8` | **5518** | `f637c8d0cd4ec6bc…` | **no — other build** |
| 16 | `carelinkhp` | `/` | 200 | `text/html; charset=UTF-8` | 5518 | `0f2c5f6257a6fc6a…` | baseline |
| 17 | `carelinkhp` | `/zz-ak-absent-4713` | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f6257a6fc6a…` | **YES — identical to row 16** |
| 18 | `carelinkhp` | `/hcp/zz-ak-absent-4713` | **404** | **(none)** | 0 | — | no |
| 19 | `carelinkhp` | `/hcp/configuration/zz-ak-absent-4713` | **405** | **(none)** | 0 | — | no |
| 20 | `carelinkhp` | `/app/zz-ak-absent-4713` | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f6257a6fc6a…` | **YES** |

Full digests, from `sha256sum` over the retained bodies:

```
0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d   .com root, .eu root, hp root, hp /, .com /app/, .eu /app/, hp /app/
f637c8d0cd4ec6bc70944f7c9083ace6c205c5ecd22ce5da6ed533ece6d9a1bc   support root, support /app/
```

**OBSERVED, and this is the finding in one line: the same 404 at `/hcp/…` and the same
405 at `/hcp/configuration/…` on all four hosts, and the same 200 fallback at root and at
`/app/` on all four hosts. The hostname is not the variable; the prefix is.**

## 5. Byte identity — measured with `cmp`, and the answer is not "one page"

The brief's question was whether the portal bodies are byte-identical to the documented
`carelinkhp` one. **Measured, `cmp` at the byte level, not eyeballed:**

| Pair | `cmp` |
|---|---|
| `.com` `/` ≡ `carelinkhp` `/` | **identical** |
| `.eu` `/` ≡ `carelinkhp` `/` | **identical** |
| `carelinkhp` `/app/` ≡ `carelinkhp` `/` | **identical** |
| `.com` `/app/` ≡ `.com` `/` | **identical** |
| `.eu` `/app/` ≡ `.eu` `/` | **identical** |
| `support` `/app/` ≡ `support` `/` | **identical** |
| `support` `/` ≡ `carelinkhp` `/` | **DIFFERS** |

**OBSERVED: three hosts serve one body; the fourth serves a different one of the same
size.** `.com`, `.eu` and `carelinkhp` are byte-for-byte the same 5518 bytes
(`0f2c5f62…`). `carelink-support.medtronic.com` serves **5518 bytes with a different
digest** (`f637c8d0…`). Both digests reproduce this repository's already-recorded ones for
their builds — `0f2c5f62…` is the clinic entry document and `f637c8d0…` the support one,
each recorded on 2026-10-13
([`findings-log/2026-10-13-area-g-device-tables/FINDINGS.md`](../../2026-10-13-area-g-device-tables/FINDINGS.md) rows 1–2 and 4–5).

**The difference is 31 bytes in 2 lines, and it is the build's own asset names:**

```
31 differing byte positions, first at offset 5327 of 5518, last at 5471
 − <script src="runtime.a752bb828cca4b2c.js" … <script src="main.fb5f8cb7eb60c4d5.js"
 + <script src="runtime.0c0212e340fbafc0.js" … <script src="main.759cddab23085086.js"
```

(OBSERVED; `difflib` over the two retained bodies, 0 requests.) Those are exactly the two
content-hashed bundles area AB asserted per host — `main.fb5f8cb7eb60c4d5.js` for the three
clinic hosts, `main.759cddab23085086.js` for support
([`findings-log/2026-11-10-area-ab-hcp-direct/FINDINGS.md`](../2026-11-10-area-ab-hcp-direct/FINDINGS.md), corpus control).

**So the fallback is not a generic error page at all — it is each deployment's own entry
document, served at any unmatched path.** That reading is **INFERRED** on `.com`/`.eu`,
because the cap did not allow fetching their real `/`; it is **OBSERVED** on `carelinkhp`,
where `/` and the fabricated path returned the identical digest in this run (rows 16, 17),
and it is consistent with three further observations: the `ETag` carries the size
(`W/"158e-659fa96cd58c0"`, `0x158e` = 5518) and differs per build
(`W/"158e-659fa99b90700"` on support); `Last-Modified` is 2026-08-26 for both; and
`<title>Dashboard</title>` with `<base>`-relative asset paths is the shape of an app index,
not of an error page.

**Consequence for the discriminator, and it is a correction in its own right: 5518 B is not
a fingerprint.** Two different builds produce it. The size distinguishes a fallback from a
`404`/`405` here; it does **not** distinguish one deployment from another — only the digest
does.

## 6. The scope, stated exactly

**The catch-all covers root and `/app/`, and stops at `/hcp/`.** Per host, the four cells
form three distinct handler shapes, and the pattern is identical on all four hosts:

| Prefix family | Verdict on `.com` | `.eu` | `support` | `carelinkhp` |
|---|---|---|---|---|
| `/` (apex) | **200** 5518 B `text/html` | **200** | **200** | **200** |
| `/app/…` | **200** 5518 B `text/html` | **200** | **200** | **200** |
| `/hcp/…` | **404**, 0 B, **no `Content-Type`** | 404 | 404 | **404** |
| `/hcp/configuration/…` | **405**, 0 B, `Allow: POST, OPTIONS`, no `Content-Type` | 405 | 405 | **405** |

**The `carelinkhp` column is the one that matters, because §7 says that host catches
every path.** It does not. `carelinkhp.minimed.eu/hcp/zz-ak-absent-4713` answered a real
**`404`** with a zero-byte body and **no `Content-Type` header at all** (row 18), and
`/hcp/configuration/…` answered **`405`** (row 19) — the same two verdicts as the three
portal hosts. Whatever serves the fallback is mounted **above** `/hcp/` and is not reached
from inside it.

**Two further points, both OBSERVED and both worth carrying:**

- **The `404` and `405` here carry no `Content-Type` header whatsoever** — not
  `text/html`, not `iso-8859-1`. So §7's "discriminate on `Content-Type`" is correct but
  incomplete: the honest rule is *a `200` is only a document if its `Content-Type` says
  so*, and on this family a genuine absence has **no** content type to discriminate on,
  only a zero length. This differs measurably from `carelink.minimed.eu`, whose apex `404`
  is a 196 B `text/html; charset=iso-8859-1` Apache page
  ([`findings-log/2026-11-10-area-ac-catchall-probe/FINDINGS.md`](../2026-11-10-area-ac-catchall-probe/FINDINGS.md) §4–§5).
- **`/app/` on these hosts is the same handler as root**, not area AC's `/app/` catch-all.
  AC measured `carelink.minimed.eu/app/…` returning a **1833 B** shell; these four hosts
  return the **5518 B** entry document there (rows 5, 10, 15, 20). So `/app/` is a
  catch-all prefix on **both** families with **different bodies**, which is the same
  prefix-mechanism, two deployments — and it means AC's finding does not extend to this
  host family unchanged (**INFERRED**: the mechanism is inferred to be the same rewrite;
  only the bodies were measured, and only on four hosts).

## 7. Verdict

**OBSERVED, 20 of a 20 cap, 4 of 4 controls first, 0 failures, 0 retries, no rule breach:
the 5518 B `text/html` fallback is served at `/` and under `/app/` on all four clinic hosts,
and `/hcp/…` and `/hcp/configuration/…` answer real `404`/`405` on all four.**

- **§7's host scope is too narrow.** Four hosts run it, not one. `carelink.medtronic.com`,
  `carelink.medtronic.eu` and `carelink-support.medtronic.com` were all undocumented.
- **§7's path scope is too wide.** "Every path that does not exist" is **false on
  `carelinkhp` itself** — the one host it names. `/hcp/…` is a true `404` there.
- **§7's discriminator is too weak.** 5518 B is two builds' size, so size separates
  fallback from absence but not deployment from deployment. The digest does that.
- **A negative is recorded as a negative:** this pass did **not** find any path prefix
  outside `{/ , /app/}` that serves the fallback. `/hcp/` and `/hcp/configuration/` were
  each tested on all four hosts and each answered a real absence, 8 of 8 cells.

**Not claimed:** that the fallback is deliberate rather than an SPA rewrite default (no
mechanism asserted); that no other prefix catches (only the two tested do not, per the
cap); that `.com`/`.eu`'s `/` is their entry document as a live fact (INFERRED, as labelled
in §5); anything about `carelink.minimed.eu`, which is outside this pass's host set.

**Not a disclosure.** An SPA serving its own entry document at unmatched paths is ordinary
behaviour. This is a **measurement limitation**, and the finding is that the record told a
reader the limitation was narrower than it is.

## 8. Proposed correction to `AGENTS.md` §7 — PROPOSED, NOT APPLIED

**This pass did not edit `AGENTS.md`, `CONTRIBUTING-research.md` or `docs/09`. All three
carry the same falsehood and all three are maintainer surfaces. The wording below is put
forward for the maintainer; the orchestrator decides.**

**Current text** (`AGENTS.md:228-231`, verbatim):

```
> [!CAUTION]
> `carelinkhp.minimed.eu` returns **HTTP 200 + `text/html` (5518 bytes)** for every
> path that does not exist. Discriminate on `Content-Type`, never on status.
```

**Proposed replacement:**

```
> [!CAUTION]
> **The 5518 B SPA fallback is prefix-scoped, and it is on FOUR hosts, not one.**
> `carelinkhp.minimed.eu`, `carelink.medtronic.{com,eu}` and
> `carelink-support.medtronic.com` each return **HTTP 200 + `text/html`, 5518 bytes**, for
> any path that does not exist **at the apex or under `/app/`** — the body is that
> deployment's own entry document, not an error page. **It stops at `/hcp/`:**
> `/hcp/<absent>` answers a real **`404`** (0 B, **no `Content-Type` header at all**) and
> `/hcp/configuration/<absent>` answers **`405` + `Allow: POST, OPTIONS`** — on all four
> hosts, including `carelinkhp`. So the status code *is* an oracle under `/hcp/` and is
> **worthless** at the apex and under `/app/`. **5518 B is not a fingerprint** — the clinic
> build (`.com`, `.eu`, `carelinkhp`) serves `sha256 0f2c5f62…` and the support build
> serves a *different* 5518 B body, `f637c8d0…`; discriminate on the **digest**, and on
> `Content-Type` before length.

[source: findings-log/2026-11-10-area-ak-portal-spa-fallback/FINDINGS.md]
```

**The three sites the same sentence appears at, and what each needs** (verified by
`grep -rn 5518`): `AGENTS.md:230` (the block above); `CONTRIBUTING-research.md:59` — same
claim in prose, needs the same scope clause; `CONTRIBUTING-research.md:270` — the prompt
scaffolding, same; and `docs/09-methodology-and-oracles.md:196` — the trap-table row
**already corrects the gzip mechanism** and carries a `5518-byte SPA fallback` entry naming
`carelinkhp.minimed.eu` for "**every** unknown path", which needs the same correction.
**None of the four was edited here.**

## 9. What this pass does not say

- It does not re-derive area AG's `405`/`Allow` finding, re-run area AC's census, or
  contact `carelink.minimed.eu` — that host is outside the claim's host set. Zero requests
  left this four-host group.
- It does not assert a cause for the fallback, for the 2 corrupt `t_sent` stamps, or for
  `.com`/`.eu`/`carelinkhp` sharing one build.
- It does not add a `regression/` pin. A pin on the fallback would cost 4 requests on
  **every** PR gate **and** per weekly sweep, to assert something that changes only when a
  deployment is rebuilt — and the build change is already caught by AB's corpus control,
  which pins the asset digests at 4 requests *that already exist*.
- It does not claim `carelink-support.medtronic.eu` (the fourth host area G swept) behaves
  as these do; it is a different hostname and was **not** in this cap.
- It does not edit `AGENTS.md`, `CONTRIBUTING-research.md` or `docs/09`. §8 proposes.

## 10. Files, and how to re-run

| File | What it holds |
|---|---|
| `probe.sh` | `CAP=20` as **one assignment** with the itemisation beside it; GET only, `--compressed`, sleep inside `flock` |
| `results.jsonl` | 20 rows, one per request, status / content-type / bytes / sha256 / `etag` / `last-modified` |
| `run.log` | Human-readable request ledger, ending `DONE — 20 of 20` |
| `spacing.py` → `spacing.txt` | Zero-request re-derivation of **both** delay series, with the impossible-duration check that identifies the corrupt rows |

**Bodies are not in the tree** (`AGENTS.md` §7: no raw capture). Re-run:

```bash
./probe.sh all
```
