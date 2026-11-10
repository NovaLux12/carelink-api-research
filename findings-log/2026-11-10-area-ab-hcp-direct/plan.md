# plan.md — the six candidates, the three hosts, and why each cell exists (area AB)

Written **before the first sweep request**. At the time of writing, `results.jsonl`
holds **4** rows — the four corpus controls — and `derive.txt` holds the extraction
below. The sweep is issued after this file exists; nothing here is reconstructed.

## The cap and its itemisation, in one place

`probe.sh` carries `CAP=43` as a **single assignment**, and `cap_guard` reads it.

| item | cells |
|---|---:|
| 6 candidates x 3 swept hosts | 18 |
| 4 controls x 3 swept hosts | 12 |
| empty-body `OPTIONS` on the 3 POST-only routes x 3 swept hosts | 9 |
| corpus-control re-assertion of the four build digests, **one per host** | 4 |
| **total** | **43** |

## Which three hosts, and why `carelinkhp.minimed.eu` is not one of them

`6 x 3 = 18`, not 24, is deliberate and is the whole scope argument:

- **`carelinkhp.minimed.eu` is the BASELINE, not a sweep target.** The six verdicts
  area AB asks about are *already measured there*: `application`, `productContext`,
  `user` → **405** (POST-only, exists); `appContext`, `access/config`, `whitelisted`
  → **401** (exists, token-gated) — both recorded in
  `findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md` §3 (`:112`) and its
  request table (`:166`, `:175`, `:178`). §10 of that file is titled **"Do not
  re-run"** and its scope is that one host on 2026-10-08.
- **AB is the portability question, which is not "do they exist".** Re-sweeping the
  baseline would spend 6 requests proving something already recorded and would tell
  the pass nothing about the other three deployments. The three hosts swept are the
  three that lane l2 swept for the sibling `public/*` half
  (`findings-log/2026-10-17-hcp-config-deployments/plan.md` §The request plan):
  `carelink.medtronic.com` (clinic), `carelink.medtronic.eu` (clinic shadow) and
  `carelink-support.medtronic.com` (support). The support host is not optional: it
  serves a **different build**, so it is the only host where "the route table is the
  same" is a real claim rather than a build-identity tautology.
- **The baseline is still touched — once, by the corpus control.** The corpus control
  is performed **per host**, not per build (docs/11 AB's correction blockquote; lane
  l2 used four captures, `b01`–`b04`). `b01` is the baseline's build, and its digest
  is what makes "the baseline's route table is the same build as the .com/.eu clinic
  hosts" a measurement rather than an inheritance.

So: **four hosts touched, three swept.** 4 corpus controls + 39 sweep cells = 43.

## The six candidates — derived, not typed from memory

`probe.sh derive` re-extracts them offline from the two fetched builds and **aborts the
sweep** (exit 3, no request issued) if the extraction does not return exactly the six
this plan names. Extraction rule: the byte-regex
`hcp/configuration/(?!public/)([A-Za-z0-9._?=&/()-]+)` over each build body, distinct
values, sorted. The `public/` half is excluded by the negative lookahead, so this is the
**direct** subtree only.

```
DERIVE b01-baseline-clinic-asset: status=asserted bytes=3397615 sha256=2a7fa8e7af519c2b… recorded=2a7fa8e7af519c2b… reproduces=True public_literals=15 direct_literals=6
DERIVE b02-com-clinic-asset: status=asserted bytes=3397615 sha256=2a7fa8e7af519c2b… recorded=2a7fa8e7af519c2b… reproduces=True public_literals=15 direct_literals=6
DERIVE b03-eu-clinic-asset: status=asserted bytes=3397615 sha256=2a7fa8e7af519c2b… recorded=2a7fa8e7af519c2b… reproduces=True public_literals=15 direct_literals=6
DERIVE b04-support-asset: status=asserted bytes=3410666 sha256=a054555a0f22176e… recorded=a054555a0f22176e… reproduces=True public_literals=15 direct_literals=6
DERIVE b01-baseline-clinic-asset direct set: access/config appContext application productContext user whitelisted
DERIVE b02-com-clinic-asset direct set: access/config appContext application productContext user whitelisted
DERIVE b03-eu-clinic-asset direct set: access/config appContext application productContext user whitelisted
DERIVE b04-support-asset direct set: access/config appContext application productContext user whitelisted
DERIVE shared=6 clinic_only=[] support_only=[]
DERIVE VERDICT: PROCEED — 4 of 4 digests reproduce, both builds name the same 6
```

Reading of that block: **4 of 4 digests reproduce** (clinic `2a7fa8e7af519c2b…` 3 397 615 B
on the baseline and both clinic hosts, support `a054555a0f22176e…` 3 410 666 B on the
support host); **both builds name the same 6 direct literals, 15 `public/*` literals
each, 0 build-only direct literals**. That is the same population
`HCP-CONFIG-SCHEMA.md` §10 describes (6 and 15), which is the self-check that this
extraction is reading the recorded surface and not a neighbouring one.

## Per-candidate reasoning — what each host's cell is testing

Recorded baseline (from `HCP-CONFIG-SCHEMA.md` §3/:112, §5:166-178): 405 for the three
POST-only routes, 401 for the three token-gated ones. Every one of the six is a
**route literal in both builds**, so a 404 anywhere is a real finding, not an artefact
of a mis-derived name.

| # | candidate | baseline (carelinkhp) | what a swept host's cell tests |
|---|---|---|---|
| 1 | `access/config` | 401 `InvalidToken`/`AUTH`, 48 B | that the token gate — not the route's absence — is what answers there. **Body digest compared**: same 48 B envelope = portable gate; a different body = finding; a 200 = much larger finding |
| 2 | `appContext` | 401, 48 B | same, on the context route |
| 3 | `application` | 405, 0 B | that the route is registered but method-filtered, not merely unrouted. A 404 would refute portability |
| 4 | `productContext` | 405, 0 B | same |
| 5 | `user` | 405, 0 B | same |
| 6 | `whitelisted` | 401, 48 B | same as 1–2 |

**The prior this pass expects to test, stated so it can be wrong:** lane l2 found the 15
`public/*` verdicts portable 15 of 15 across exactly these three hosts while the *bodies*
differed. If the six direct verdicts behave the same way, AB closes as a **portable
negative**. That is a prediction, not a result — the cells have not been sent.

## Controls, first per host — and why these four

Per host, before any candidate: (1) `pow.crm.settings` **with** `X-System-ID: ProWeb`
→ 200 expected, proving the header is accepted and the verdict rule is live on that
host; (2) `CSU.CONTROL.CODES.SETTINGS` (UPPER) → 404 expected, proving a 404 there is a
true absence and **not** the 5518 B SPA fallback (AGENTS.md §7); (3) `cua.control.codes.settings`
(lower) → 200 expected, so (2)+(3) re-derive case-sensitivity on that host; (4)
`logbook.supported.entry.types` **with no header** → 412 expected, proving the header
gate is real and that a 412 means "header rejected", not "key absent". All four are
lane l2's controls, proven live on this host family
(`findings-log/2026-10-17-hcp-config-deployments/plan.md` rows 1–15).

These four are all under `public/`. That is a **declared limit**: the header gate has
never been measured on the **direct** subtree, and docs/11 AB lists exactly that as the
INFERRED assumption this pass was minted to falsify. It is not falsified by controls
that live under `public/` — it is falsified by the shape of the direct answers
themselves: if a direct route answers **412** on a swept host, the header gate covers
the direct subtree and that cell is a *control*, not a candidate verdict. If it answers
405/401 with the header, the gate is at least not blocking, and the recorded verdict
reproduces. Either way the sweep distinguishes the two, which is the point.

## The `OPTIONS` cells, and what they are NOT

9 cells: empty-body `OPTIONS` (no `-d`, no `-X` beyond the method itself) on
`application`, `productContext`, `user` x 3 hosts. `OPTIONS` is not a POST and is
explicitly permitted; `AGENTS.md` §11's POST restriction is untouched.

**Read them narrowly.** `docs/09` §2 records that `access-control-allow-methods` is
**not** a register of a route's methods: `carepartner/v13/display/message` advertises
`OPTIONS` on its preflight and is GET-capable. So this pass records `allow` and
`access-control-allow-methods` **per deployment as an observation** — nothing on this
page records them for this family — and does **not** infer from them that a method is
absent. The GET verdict stays the authority.

## Method and limits

GET only, plus the 9 empty-body `OPTIONS`. No POST, no token, no cookie, no
authentication beyond the `X-System-ID: ProWeb` control header, no port scan, no
wordlist, `--compressed` on every request. **2.5 s** between requests to the same host,
slept **inside** the shared per-host flock in the main clone's `.loop/`. A
`000`/5xx/timeout/unexpected 4xx is a **failure**, re-issued with its own ledger row —
never an absence. Bodies are transient; only headers and digests are committed, and the
3.4 MB bundles live in `.loop/` (gitignored).
