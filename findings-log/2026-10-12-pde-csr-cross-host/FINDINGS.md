# Area U — are the `csr/v1`, `csr/v3` and PDE cells dead on `.com` and `-trials` too, or only on `.eu`?

**Claimed in #11. Run 2026-10-12. Area closed.**

- **Method:** GET and OPTIONS with an empty body. No POST, no token exchange, no
  authentication, no `Authorization`/`Cookie`/`x-api-key`, no port scanning, no DNS
  brute force, no wordlist, no new host, no dev/stage host.
- **Total 32 of a 32 cap**, 16 per host, on `clcloud.minimed.com` and
  `clcloud-trials.minimed.com`.
- **≥2.5 s `sleep` between requests to the same host** in the harness (Area C's spacing).
  **Measured floor across the pass: 2.0 s**, not 2.5 s — 8 of 30 inter-request gaps are
  2 s, because requests land on two different CloudFront PoPs (the `via:` header differs
  between `com-05` and `com-06`) whose clocks are not synchronised, so `Date`-header
  arithmetic across a host change is not a valid spacing measurement. `docs/09` §1 records
  the in-harness floor as **≥2 s** and quotes 2.5 s only for the gateway sweep; both are
  satisfied, and the honest floor for this pass is **≥2 s observed**.
- **Harness:** `probe.sh` — same HTTP discipline as
  [`../2026-10-11-pde-csr-oracle/probe.sh`](../2026-10-11-pde-csr-oracle/probe.sh):
  same methods, same oracle, same control-first ordering and same spacing. The two
  scripts are not identical — this one loops per host and tags filenames by host
  suffix, where the Area C script hard-coded one host.
  Machine log `run.log`, per-cell record `results.jsonl`, every response head in
  `headers/`, verdict derivation `verdict.py` → `verdict.txt`.
- **Discriminator:** `x-amzn-errortype`, **never the status code**. On `clcloud.*` 403 is
  the *no-matching-route* error and a 404 is never emitted at all
  ([`docs/09`](../../docs/09-methodology-and-oracles.md) §2). Every candidate path is one
  already recorded by the Area C pass — no version neighbours were added.

## Verdict — all six negative cells are dead on both hosts, on both methods

**OBSERVED.** Twelve cells per host, `GET 403 + OPTIONS 403`, both with
`x-amzn-errortype: MissingAuthenticationTokenException`, 42 B, **no `Access-Control-*`
header on any of them**:

| path | `clcloud.minimed.com` | `clcloud-trials.minimed.com` |
|---|---|---|
| `connect/pde/v1/display/message` | GET 403 · OPTIONS 403 | GET 403 · OPTIONS 403 |
| `connect/pde/v2/display/message` | GET 403 · OPTIONS 403 | GET 403 · OPTIONS 403 |
| `connect/pde/v3/display/message` | GET 403 · OPTIONS 403 | GET 403 · OPTIONS 403 |
| `connect/pde/v3/discover/android/3.6` | GET 403 · OPTIONS 403 | GET 403 · OPTIONS 403 |
| `connect/csr/v1/display/message` | GET 403 · OPTIONS 403 | GET 403 · OPTIONS 403 |
| `connect/csr/v3/display/message` | GET 403 · OPTIONS 403 | GET 403 · OPTIONS 403 |

**A negative counts in both directions and it counted one way.** No cell flipped to
live. So: the Area C verdict is now **three hosts wide, not one**, and
`docs/00-summary-the-map.md`'s bold "**Not re-probed on `.com`/`-trials`**" caveat is
discharged rather than carried forward.

### The controls were run first on each host, and they passed

The data cells above are only believable because the oracle reproduced on each host
*before* the data was collected — otherwise the cells would be judged by a verdict
established from the data they are meant to test:

| control | `.com` | `-trials` | expectation |
|---|---|---|---|
| GET `connect/carepartner/v13/display/message` | 401 `UnauthorizedException` | 401 `UnauthorizedException` | live, reached the Layer7 authorizer |
| GET `connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c` (fabricated) | 403 `MissingAuthenticationTokenException` | 403 `MissingAuthenticationTokenException` | no route |
| OPTIONS `connect/carepartner/v13/display/message` | 200 `acao: *`, 0 B | 200 `acao: *`, 0 B | live preflight |
| OPTIONS `…/3f8a1c2e-…` (fabricated) | 403 `MissingAuthenticationTokenException` | 403 `MissingAuthenticationTokenException` | no route |

`verdict.py` asserts all eight before it will emit a single data verdict; had any host
failed, that host's cells would have been reported **inconclusive** rather than believed.

### Byte-identity across all three cumulus hosts

**OBSERVED.** All 28 no-route bodies in this pass — 24 data cells plus the 4 fabricated
controls — are **byte-identical**, 42 B, `sha256:f249b63cb2fc`. That digest is *also*
the digest of **22** separate `.eu` no-route bodies captured by Area C on 2026-10-11
(verified against [`../2026-10-11-pde-csr-oracle/headers/`](../2026-10-11-pde-csr-oracle/headers/):
of that pass's 26 body files, 22 carry `f249b63cb2fc`, 1 is the 36 B live-GET 401, and 3
are the empty bodies of live-OPTIONS 200s). **50 byte-identical bodies across the two
passes.**

**INFERRED** — and this was an unlabelled inference in the first draft of this file,
sitting under an OBSERVED header in the section a reviewer trusts most: that this means
**one shared artefact** rather than three independent templates that happen to serialise
identically. The assumption is that all three hosts run the same gateway software and
configuration, which is consistent with everything observed but is **not** established by
a hash — three independently generated templates would hash the same. The operational
claim is unaffected either way: a client cannot distinguish them, and all three mean
"no route".

The remaining four responses are the live-cell controls: 2 × 36 B
(`sha256:d551247201fc`, the `UnauthorizedException` 401) and 2 × 0 B (the OPTIONS
preflight, which carries headers and no body).

> **Method note, and a correction to how this was first derived.** `verdict.py` now
> hashes each of the 12 dead-cell bodies against its host's own fabricated-path control
> and **asserts** the match (12/12 per host, 24 total). Its first version did not: it
> hashed the control once per host and printed the digest under a heading that said
> "equality", comparing nothing. The claim above was true, but the script cited as
> deriving it did not derive it — a check that looks like it ran. The `DiFFERS` branch
> and the two `assert`s now make the comparison real and its failure loud.
>
> `verdict.py` also refuses to report any digest over a body it has not
> first asserted is non-empty. During this run that assertion fired for real: the two
> live-OPTIONS bodies are legitimately 0 B, and their digest is the sha256 of the empty
> string (`e3b0c442…`). A hash check that cannot tell an empty body from an absent value
> will manufacture consensus — the exact failure in
> [`AGENTS.md`](../../AGENTS.md) §6 item 3 — so 0 B is bucketed before hashing, not
> compared.

## Correction to a previous pass's inference — preserved, not deleted

**`docs/03-discovery-and-versions.md` §9 (Area C update) and the Area C limits section
carried this, and it is now retired rather than confirmed:**

> **Retired 2026-10-12 (area U).** Area C concluded on `clcloud.minimed.eu` alone that
> "PDE has **no route on any tested method**", and explicitly declined to extend it to
> `.com`/`-trials`, noting that "dead on `.eu` is not evidence of dead elsewhere, and
> that is a named successor area rather than an assumption". **This pass discharged that
> successor:** the same six cells, the same two methods and the same oracle are dead on
> both remaining hosts. The Area C statement was correct as far as its own host and is
> **not** contradicted by anything here — it is *widened*, and the reason it was not
> assumed is now on the record as a completed check rather than as an open caveat.

The generalisation it refused to make is now **supported by observation on 3 of 3
hosts**: the PDE and CSR-negative namespaces are uniformly unrouted across the cumulus
estate.

## The finding this area was really opened for

Area T's claim (`#10`) recorded the assumption that "`csr/v2` is an internal or
deprecated route rather than a client-addressable one — inferred from the *absence* of a
recorded base URL". **That assumption was wrong — and the sibling pass is the proof,
not this one.** This pass never requested a `csr/v2` path: `grep -c csr_v2 headers/`
returns 0. What this pass contributes is the **inverse** case, the published base URL
that nothing can answer:

**`baseUrlPde` is published in the discovery document on every host and every region,
and it resolves to `/connect/pde/v3` — a namespace that has **no GET or OPTIONS route for
either recorded path under it** (`display/message`, `discover/android/3.6`) on any of the
three cumulus hosts. The bare prefix itself was never requested, so the verdict covers
the two recorded paths rather than the prefix.**

| document | regions | `baseUrlPde` |
|---|---|---|
| `clcloud.minimed.eu` `v13/discover/android/3.6` | US, EU, CLINICAL | `…/connect/pde/v3` ×3 |
| `clcloud.minimed.com` `v13/discover/android/3.6` | US, EU, CLINICAL | `…/connect/pde/v3` ×3 |
| `clcloud.minimed.com` `v11/discover/android/3.6` (legacy) | US, EU | `…/connect/pde/v1` ×2 |
| `clcloud-trials.minimed.com` `v6/discover/android/3.6` (legacy) | US, EU | `…/connect/pde/v1` ×2 |

**OBSERVED** for the `v3` rows (this pass + Area C). **INFERRED** for the legacy `v1`
rows: `pde/v1/display/message` is confirmed dead on all three hosts by this pass, but
the *discovery* documents that publish `baseUrlPde = …/pde/v1` were read in the sibling
pass — see [`../2026-10-12-published-pointers/FINDINGS.md`](../2026-10-12-published-pointers/FINDINGS.md)
§2 for the four documents and their digests.

**A dead route behind a published base URL is a different fact from "the vendor has a
dead route".** Any client that resolves its endpoints from the vendor's own discovery
document — which is the documented, intended mechanism, and the one this repo's
consumer uses — is pointed at a namespace that cannot answer. That is the architecture,
not just the route table.

## Limits of this pass

- **Route existence only.** Whether any of these paths ever returns data is
  token-gated and untouched; it stays in
  [`docs/10-open-questions.md`](../../docs/10-open-questions.md) §1.
- **Only recorded paths.** Six cells, all from the Area C harness. No version
  neighbours, no `csr/v4`, no `pde/v4` — a version the vendor never recorded is not a
  candidate this project will invent.
- **GET and OPTIONS only**, so the honest phrasing remains "no route **on any tested
  method**". A route registered for a third method is not excluded; it is unprobed.
- `clcloud.minimed.eu` was **not** re-probed. Its verdict is Area C's, three days old,
  and re-probing it would have spent 16 of 32 requests re-deriving a settled result. The
  42 B byte-identity check above is what ties that host into this pass's evidence.