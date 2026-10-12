# Area I — Auth0 tenant behavioural differences (2026-10-12)

Claim issue **#23**. Unauthenticated, **GET only**, no token exchange, no
authentication, no POST. Nothing here needed a credential; nothing produced
one.

**19 of a 20 cap** — 17 via `curl` (probe pass) + 2 via `hurl 8.0.1`
(live validation of the two new pins). Declared delay **2.5 s between requests
to the same host**, enforced as a `sleep` *inside* the per-host `flock` in
`probe.sh` — outside the lock, four concurrent pool workers would fire
simultaneously on one host, which is worse than not serialising at all.
`--compressed` on every request.

**Measured spacing floor: 2.000 s**, from the 12 same-host gaps in
`results.jsonl`. Read that number carefully: `ts_utc` is recorded at
**1-second resolution**, so this ledger **cannot resolve a 2.5 s sleep** — 2.000
and 3.000 are the only values it can produce, and the gaps quantise onto them.
The floor is therefore a **lower bound**, not a measurement of the declared
delay; the delay itself rests on `probe.sh`, which is committed. Areas B, X and
Z hit the same wall (short or unverifiable same-host gaps) and recorded it
rather than smoothing it over; this is the fourth pass to do so, and the fix —
millisecond timestamps — is noted for the next one.

---

## 1. The tenant set: five, and how "three" and "four" were both right

The area opened with a contradiction to reconcile: `AUTH-TENANT-FINDINGS.md` §1
compared **three** tenants, `docs/11` area I and `docs/02` §1 spoke of
**four**. Neither number was an error. They count two different axes over the
same five-host estate.

| Axis | Count | Set |
|---|---|---|
| Field-by-field policy comparison, `AUTH-TENANT` §1 | **3** | `minimed.eu`, `medtronic.eu`, `-trials.minimed.com` |
| Field-by-field policy comparison, `RECON-SUBDOMAINS` §4.1 added the 4th | **4** | the above **+ `medtronic.com`** |
| JWKS kids with known key material, `AUTH-TENANT` §8 / `PROBE-FINDINGS` §8 | **4** | `minimed.{eu,com}`, `medtronic.{eu,com}` — **excludes trials**, and is the only set that includes `minimed.com` |
| Union | **5** | all of the above |

The decisive gap: **`carelink-login.minimed.com` (patient US) was in nobody's
policy comparison.** §1 never compared it; `RECON-SUBDOMAINS` §4.1 compared
`medtronic.com` against "the three known tenants" and so never touched it either.
And `-trials.minimed.com` — the tenant §1's "needs no separate auth handling"
conclusion leans on hardest — was in the policy set but **never in the key set**,
which is why `docs/02` §9 still carried its kids as *"Unknown — not in any
source"*.

**This pass compared all five.** `corpus-audit.py` §F enumerates every
`carelink-login*` host named anywhere in the tracked corpus: **five, and this
pass covered five.** Nothing was left out by choice. (The eight
`carelink-login-{dev,stage1-next,test1,clinical-*}` hosts the Wayback sweep
found are dev/stage/test by name and are enumerated-not-probed by policy —
`RECON-SUBDOMAINS` §7.2. They are out of scope and were not contacted.)

## 2. The negative, in its strongest available form

`AUTH-TENANT` §1 compared fields. This pass compared the **whole document**:
parse, substitute the tenant's own hostname for `<TENANT>`, sort keys,
re-serialise, hash.

```
carelink-login-trials.minimed.com  normalised 2640B  sha256:0c0db635f5e9b08b
carelink-login.minimed.eu          normalised 2640B  sha256:0c0db635f5e9b08b
carelink-login.minimed.com         normalised 2640B  sha256:0c0db635f5e9b08b
carelink-login.medtronic.eu        normalised 2640B  sha256:0c0db635f5e9b08b
carelink-login.medtronic.com       normalised 2640B  sha256:0c0db635f5e9b08b
distinct normalised digests: 1 of 5
```

**OBSERVED.** The five discovery documents are **byte-identical** once the
tenant hostname is substituted out. Not "the same fields" — the same bytes.

### The presence/absence comparison, which is the stronger one

The area asked specifically for fields *present in one document and absent in
another*, which is a different claim from "values differ" and survives a
document that merely renames fields.

- Field-name union across the five documents: **30**.
- Fields absent from at least one document: **0**.
- Fields whose value differs after hostname normalisation: **0**.
- Fields whose value differs raw: **12 of 30** — and **every one of the 12 is a
  URL string containing that tenant's own hostname**
  (`issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`,
  `userinfo_endpoint`, `end_session_endpoint`, `registration_endpoint`,
  `revocation_endpoint`, `mfa_challenge_endpoint`,
  `device_authorization_endpoint`, `backchannel_authentication_endpoint`,
  `global_token_revocation_endpoint`).

### A correction to §1 that falls out of this

`AUTH-TENANT` §1 — and `docs/02` §1, which repeats it — says the tenants are
"identical except `issuer`, the endpoint hostnames derived from it, **and
`registration_endpoint`**". **`registration_endpoint` is not a separate
difference.** It differs only by hostname, exactly like the other eleven. The
list of differences is *twelve host-derived URLs*, not *eleven plus a special
case*. Small, but it is a claim a client could act on, so it is corrected here
rather than left.

Policy parity is therefore **confirmed at five tenants**, where §1 established
it at three. The consequence §1 drew — the trials tenant needs no separate auth
handling — **survives, and is now backed by the tenant §1's comparison did not
include on either axis.**

## 3. The positive: one behavioural difference the policy surface cannot show

Two documents being identical says nothing about how the hosts *behave*. They
differ here.

**OBSERVED — `x-ratelimit-limit` on the discovery and JWKS responses:**

| Tenant | `x-ratelimit-limit` | rows |
|---|---|---|
| `carelink-login.minimed.eu` | **500** | seq 5, 6 |
| `carelink-login.medtronic.eu` | **500** | seq 11, 12 |
| `carelink-login-trials.minimed.com` | **100** | seq 2, 3 |
| `carelink-login.minimed.com` | **100** | seq 8, 9 |
| `carelink-login.medtronic.com` | **100** | seq 15, 16 |

The split is **`.eu` = 500, everything else = 100** — 10 observations, 2 per
tenant, and the value never varies within a tenant while taking exactly two
distinct values across five. It is invisible in the discovery documents, which
are byte-identical. This is the first behavioural difference between these
tenants on record.

- **INFERRED**, and labelled because it is: that 500/100 is *tenant
  configuration* rather than a negotiated tier depends on Auth0 treating
  `x-ratelimit-limit` as a static per-rule setting. What is **observed** is only
  that the header is constant within each tenant and differs between them.
  `x-ratelimit-remaining` does *not* track cleanly across my two requests per
  tenant (e.g. `.eu` reads 461 then 482, rising), which is consistent with a
  shared bucket other traffic is also consuming — so `remaining` is a live
  counter and says nothing about configuration. **Nothing a client must handle
  depends on this reading**: both values are far above any realistic unauthenticated
  client rate, and the difference does not change what any endpoint accepts.

**OBSERVED — `/oidc/register`, the `registration_endpoint` every tenant
advertises, is absent on every tenant.** 5 of 5 rows return
`404 application/json; charset=utf-8`, 60 B,
`{"statusCode":404,"error":"Not Found","message":"Not Found"}`,
**one digest `f006bbd60894…` across all five hosts** (seq 4, 7, 10, 13, 17).
One artefact, five tenants. A published capability that does not exist,
identically, everywhere.

**OBSERVED — the rest of the behavioural surface is uniform.** On all five
tenants the discovery document and the JWKS both return `200` with
`access-control-allow-origin: *`, `access-control-allow-credentials: false`,
`cache-control: public, max-age=15, stale-while-revalidate=15,
stale-if-error=86400`, `content-encoding: gzip`, `server: cloudflare`, and
HSTS `max-age=31536000; includeSubDomains`. The `ACAO: *` + `credentials:
false` combination `SECURITY-FINDINGS` §"Checked and clean" recorded for the
login hosts is confirmed on all five including the two never previously
compared for it.

## 4. Two 404 signatures — and one of them is a proper oracle

The controls (§6) were not decoration; they produced the pass's most reusable
artefact. On `carelink-login.*`, a `404` is **not one thing**:

| | certainly-absent `/.well-known/*` | absent advertised `/oidc/register` |
|---|---|---|
| `content-type` | `text/plain; charset=utf-8` | `application/json; charset=utf-8` |
| body | 10 B | 60 B, `{"statusCode":404,…}` |
| digest | `0802559db137…` | `f006bbd60894…` |
| **`x-auth0-not-found`** | **`1`** | **absent** |
| `cache-control` | `public, max-age=60` | `no-cache` |

**OBSERVED:** `x-auth0-not-found: 1` appears on the well-known miss and on
nothing else in 19 responses. It is a better oracle than status code on this
host family — it says *the tenant's front door does not know this path*
specifically, which a status code alone cannot.

**INFERRED**, with its assumption: that the two signatures correspond to two
different routing states — an unrouted path versus a path that reached Auth0's
API layer and was answered by a handler with nothing to return. The two
signatures are observed; the *meaning* assigned to them is not, and nothing
here needs it to be. Recorded so the next pass does not have to re-derive it.

**Controls first, on two hosts, both passed.** The absent-path control was sent
as seq 1, *before* any candidate on that host, precisely so that a front door
answering everything would be discovered before its documents were read as
evidence. It did not: seq 1 and seq 14 are both `404 text/plain`, identical
digest, on two differently-configured tenants.

## 5. The trials tenant's key set — `Unknown` discharged

`docs/02` §9 carried *"JWKS kids for `carelink-login-trials.minimed.com` —
Unknown — not in any source. The four-way comparison never covered the clinical
tenant, so 'disjoint' is established for the four compared issuers only."*

**OBSERVED** (seq 3), `carelink-login-trials.minimed.com` publishes **two** RSA
RS256 signing keys: `kCezLNMQV0tlc3hZinEly` and `pNzjt7ruOaWE4rlDCBPoP`.

The disjointness claim therefore extends from four tenants to **five**:

```
tenants: 5   distinct kids: 10 of 10 entries
kids shared by >1 tenant: 0  (none)
every tenant holds exactly 2 keys: True
every key RSA/RS256/use=sig: True
```

Ten `kid`s, none shared. "Completely disjoint" is no longer a four-tenant
statement, and `docs/02` §9's caveat is discharged.

## 6. Two transcription defects in the published corpus, both settled against it

The corpus disagrees with itself about two `kid` strings. Eyeballing
base64url identifiers is exactly how this repo has been wrong before (AGENTS.md
§6 #2), so `corpus-audit.py` does the comparison in code against a named
`file:line`, and prints disagreements instead of resolving them by eye.

**(a) `carelink-login.minimed.com`, second kid — a DROPPED CHARACTER, previously
unrecorded.**

| | value |
|---|---|
| **Live** (seq 9) | `qjHNmcQOpW_gQvHz6zaD8` — 21 chars |
| `AUTH-TENANT-FINDINGS.md:280` | `qjHNmcQOpW_gvHz6zaD8` — **20 chars** |
| `docs/02:34` | `qjHNmcQOpW_gvHz6zaD8` — **20 chars** |

The corpus string is the live string **minus one `Q`**. This one had never been
flagged anywhere, and `docs/02` §8's machinery could not have caught it: §8 was
built to hold a *transposition* in abeyance, and this is a *deletion*, which
leaves no second reading to compare — you have to go to live.

**(b) `carelink-login.medtronic.com`, second kid — `docs/02` §8's unresolved
disagreement, now resolved *against* the file `docs/02` recommended.**

| | value |
|---|---|
| **Live** (seq 16) | `80YhF8vW25gJ1_rR_lOOJ` |
| `RECON-SUBDOMAINS.md:244` | `80YhF8vW25gJ1_rR_lOOJ` — **matches** |
| `AUTH-TENANT-FINDINGS.md:282` | `80YhF8vW25gJ1_rR_lLOJ` — `O`/`L` transposed |

`docs/02` §8 said: *"treat it [the AUTH-TENANT form] as the better-attested one
and confirm against the live `/.well-known/jwks.json` before relying on either."*
Confirmed against live, and it is the **other** spelling. `docs/02` §8's
recommendation is therefore wrong in the direction it warned about.

**Corroborating, and explicitly not the proof:** all ten observed `kid`s are 21
characters, and `qjHNmc…` at 20 is the only string in the set that is not.
That is consistent with both being transcription slips, but the live fetch is
what settles each; the length check would not have been sufficient on its own.

`docs/02` §8 is left in place with its correction attached, per AGENTS.md §3.

## 7. Controls, and what each one proved

| # | seq | Request | Result | What it proved |
|---|---|---|---|---|
| C1 | 1 | `carelink-login-trials.minimed.com/.well-known/openid-configurationx` | `404` `text/plain` 10 B, `x-auth0-not-found: 1` | A missing well-known document on this host family is a **404**, not a 200 fallback page. **The oracle holds** — without it, "field X is absent" and "this document is a fallback" would be indistinguishable. Sent first, before any candidate on this host, per §6's stop condition. |
| C2 | 2 | `carelink-login-trials.minimed.com/.well-known/openid-configuration` | `200` `application/json` 2825 B | The known-live counterpart on the same host, immediately after: C1's 404 is a property of the *path*, not of the host. |
| C3 | 14 | `carelink-login.medtronic.com/.well-known/openid-configurationx` | `404` `text/plain` 10 B, **same digest as C1** | The absent-signature is not host-specific, and — the reason for spending the request — one host's 404 says nothing about the *next* host's front door. Sent before that host's candidates. |

Both absent-path controls returned 404, so **no stop condition fired**.

## 8. Every negative result, stated

- `registration_endpoint` advertised on all five tenants, **absent on all five**
  (§3). Not one of them serves it.
- `kids shared by >1 tenant: 0`. The five key sets stay disjoint (§5).
- `fields absent from at least one document: 0` (§2).
- `x-auth0-not-found` appears on 2 of 19 responses and on **no** live document.
- No `x-ratelimit-*` header on any `404`, and no `access-control-allow-origin`
  on any `404` — only the `200`s carry CORS here (§3).
- The trials tenant has **no** field the other four lack. There is no
  trials-specific OAuth surface to implement.

## 9. Blocked, not tested

Recorded as blocked rather than attempted, per the area's hard scope limit.

- **Does any tenant accept a token minted by another?** Needs a token.
  `docs/10` §1 carries the row; §6 of the issue's plan notes this pass supplies
  the per-tenant issuer inventory it needs — now at five.
- **Is the `device_code` grant rejected for the trials client too?** All five
  documents advertise `urn:ietf:params:oauth:grant-type:device_code`; `docs/02`
  §1 has it definitively rejected for the two *patient* clients. Re-proving that
  needs a **POST** to `/oauth/token`, which is **area J's subject** and is out of
  scope here. Doing it would have duplicated another area and broken the
  read-only rule. Left open.
- **`/mfa/challenge`** is advertised on all five and has no probe result in any
  source (`docs/02` §9 still carries it as Unknown). It would have cost 5 more
  requests; the cap is committed. Named in the successor instead.

## 10. What is now pinned

Two test cases added to `regression/hurl/02-sso-oidc.hurl`, both **validated
live** (seq 18, 19; `hurl` exit 0 for both) through a *different client* from
the pass that produced them, so a pin that does not hold fails here rather than
in the weekly drift sweep:

- `carelink-login-trials.minimed.com/.well-known/openid-configuration` — issuer,
  the four host-derived endpoints, `authorization_code` + `refresh_token`,
  `S256` **and** `plain`, `token_endpoint_auth_methods_supported` contains
  `none`, plus `ACAO: *` and `ACAC: false`.
- `carelink-login-trials.minimed.com/.well-known/jwks.json` — exactly 2 keys,
  RSA/RS256, both `kid`s.

The kid values are pinned deliberately: key rotation here is **expected drift,
not a defect**, and a red suite should send a human to re-record them from live
rather than be worked around. The hurl files carry that instruction inline.

Assertion counts re-measured with the one counting rule
(`scripts/measure_assertions.py`): **167 → 184 static, 359 → 380 execute per
run**. Both counts updated at every site — `README.md` ×2, `docs/09` — and
re-grepped by hand, because `docs/09` §4 records a count once wrapped across a
line break that the gate's pattern could not see while reporting green.

## 11. Discipline notes

- **GET only.** No POST, no `-X` override, no `-d`, no token exchange, no
  authentication, no port scan, no DNS brute force, no path enumeration beyond
  the closed candidate list below. Candidate justification: every path is one
  of `/.well-known/openid-configuration`, `/.well-known/jwks.json` or a path
  named *inside* a document this pass read (`registration_endpoint` →
  `/oidc/register`); the only fabricated paths are the two controls
  `…-configurationx`, which exist to be absent.
- **Per-host locking.** `flock <pool>/.loop/host-<host>.lock` around each single
  request with the sleep inside. Never held two at once, never held one while
  running the gate, never touched `.loop/merge.lock`. The lock directory is
  **discovered by walking up for `.loop/BRIEF.md`**, not hard-coded: the first
  version of both scripts carried a literal `/home/<user>` path and the gate
  failed the diff on it ("machine-specific paths"). That edit is the **only**
  change made to either harness after the run, it is confined to how the lock
  directory is located, and it changes neither what was requested nor the
  spacing between requests.
- **Nothing secret was found or published.** The surface carries client IDs and
  JWKS material. Client IDs are already public in `docs/02` and are not
  reproduced here. The JWKS `kid`s are published by the vendor at an
  unauthenticated URI. The RSA moduli and `x5c` chains are **not** committed —
  `bodies/` is gitignored and `jwks-keys.json` carries `kid`/`kty`/`alg`/`use`
  only, with the reason recorded in the file. One Auth0 custom-domain hostname
  appears in those chains; it stays out of this repo's history.
- **A failed tool call cost two ledger rows and no requests.** `hurl --test`
  is a boolean flag in 8.0.1, not a name selector; two invocations exited 1 on
  a local selector error having opened no socket. Those two rows were written,
  caught as false, and **removed** rather than left standing — a ledger row that
  claims a fetch which never happened is the same defect class as a claim with
  no source. The real run used one file per case.
- **`verdict.txt` re-derives from committed artefacts alone.** Verified by
  moving `bodies/` aside and re-running `diff.py`: byte-identical output. The
  five discovery documents and both controls are committed verbatim under
  `openid/`; `diff.py` re-checks every document against its ledger row's byte
  count and sha256 *before* comparing anything, because AGENTS.md §6 #3 is a
  comparison over a lookup that silently returned nothing.