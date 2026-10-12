# Area I — Auth0 tenant behavioural differences (2026-10-12)

Claim issue **#23**. Unauthenticated, **GET only**, no token exchange, no
authentication, no POST. Nothing here needed a credential; nothing produced
one.

**32 of a 34 cap, in two budgets, and no POST among any of the 32.** The
original budget was **19 of a 20 cap** — 17 via `curl` (probe pass) + 2 via
`hurl 8.0.1` (live validation of the two new pins). The **supplementary budget
of 14** was authorised by the repository owner after a verifier refuted this
pass's `registration_endpoint` claim, specifically to complete it, and **13 of
those 14 were used** (10 planned OPTIONS probes + 3 diagnostics; 1 left unused).
The two are kept separate because they were authorised separately and spent for
different reasons; they are added into one total only because the ledger is one
file, and its 32 rows have to be accounted for as one number.

Declared delay **2.5 s between requests to the same host**, enforced as a
`sleep` *inside* the per-host `flock` in both `probe.sh` and
`probe-options.sh` — outside the lock, four concurrent pool workers would fire
simultaneously on one host, which is worse than not serialising at all.
`--compressed` on every request.

The supplementary phase is **OPTIONS with an empty body**, which
`PULL_REQUEST_TEMPLATE.md:15` permits for exactly the purpose of finding
POST-only routes. The method sent is OPTIONS on all 13 rows;
`Access-Control-Request-Method: POST` is a preflight *declaration* of what a
browser would send, not a POST, and no request body was sent.

**Measured spacing floor: 2.000 s**, from the same-host gaps in
`results.jsonl` — 12 in the original GET phase and 5 more in the supplementary
OPTIONS phase, none below 2 s. Read that number carefully: `ts_utc` is recorded at
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
`carelink-login*` host named anywhere in the **tracked Markdown** (its scan is
`.md`-only; see §14 — the wording here said "tracked corpus" before that was
tightened, and the conclusion is unaffected because the tenant set comes from the
captured documents, not from the prose scan): **five, and this
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

**OBSERVED — `/oidc/register` returns `404` to GET on all five tenants.** 5 of 5
rows return `404 application/json; charset=utf-8`, 60 B,
`{"statusCode":404,"error":"Not Found","message":"Not Found"}`, **one digest
`f006bbd60894…` across all five hosts** (seq 4, 7, 10, 13, 17). That GET
observation stands.

**RETRACTED 2026-10-12 — the inference layered on it was wrong, and so was the
method that produced it.** This pass reported the endpoint as *"absent on every
tenant… A published capability that does not exist, identically, everywhere."*
**That claim is false.** The endpoint is live. A verifier refuted it with an
OPTIONS preflight, and the supplementary run below confirms the refutation on
this pass's own evidence.

The error was the **method**, not the reading. A GET-only probe cannot see a
POST-only route, and this repo said so before the pass began:
`PULL_REQUEST_TEMPLATE.md:15` ("GET only, **except OPTIONS with an empty body to
find POST-only routes**"), `docs/09:64-71` (`GET 403 + OPTIONS 200 → live,
POST-only`; "the cleanest proof that a resource exists with no GET method"),
`docs/00` and `docs/06:310,443`. `PROBE-FINDINGS.md:247` is titled *"Endpoints
that are POST-only (a GET-only probe reads them as dead)"* and opens "I
initially recorded `/oauth/revoke` as 404" — the identical error, already made
and already written down. Its `/oidc/register` row (`:258`) carries a `—` in the
POST column: the earlier pass **declined to assert absence**, and this pass read
that silence as a finding. A `—` is not a 404.

The retraction is kept visible rather than deleted, per AGENTS.md §3. What
survives from the original claim is the GET capture; what does not is "absent".

### The corrected claim, established on all five tenants

**OBSERVED — supplementary budget of 14, 13 used.** OPTIONS with an empty body,
`Origin: https://probe.invalid` (a non-routable placeholder, so the preflight
cannot look like a real referrer), `Access-Control-Request-Method: POST`,
`Access-Control-Request-Headers: content-type`. **A certainly-absent control per
tenant**, `/oidc/registerx`, sent *first* on every host (seq 20, 22, 24, 26, 28) —
one host's 404 says nothing about the next host's front door.

| Tenant | `/oidc/register` OPTIONS | `allow-methods` | `x-auth0-not-found` | control `/oidc/registerx` |
|---|---|---|---|---|
| `carelink-login-trials.minimed.com` | **204**, 0 B | **`POST`** | absent | 404, 10 B, `x-auth0-not-found: 1` |
| `carelink-login.minimed.eu` | **204**, 0 B | **`POST`** | absent | 404, 10 B, `x-auth0-not-found: 1` |
| `carelink-login.minimed.com` | **204**, 0 B | **`POST`** | absent | 404, 10 B, `x-auth0-not-found: 1` |
| `carelink-login.medtronic.eu` | 404, 107 B | absent | absent | 404, 10 B, `x-auth0-not-found: 1` |
| `carelink-login.medtronic.com` | 404, 107 B | absent | absent | 404, 10 B, `x-auth0-not-found: 1` |

**The three patient tenants are live and POST-only**, on the repo's own oracle
(`docs/09:65`): 204 + `access-control-allow-origin` +
`access-control-allow-methods: POST` on the advertised path, against 404 +
`x-auth0-not-found: 1` + `text/plain` on the one-character-different control,
same host, same method, same headers. An advertisement that is honoured rather
than dangling.

**The two shadow tenants answer differently, and the difference is real.** Both
return `404 application/json`, 107 B, **one digest `af370969b232…`**, body
`{"statusCode":404,"error":"Not Found","message":"CORS error: Missing
Access-Control-Request-Method header"}` — and **no `access-control-*` header at
all**, while their own controls return `x-auth0-not-found: 1`.

That body is surprising, because the header it names **was sent**. Verified
rather than assumed, at the cost of three of the four spare requests: a verbose
capture (seq 30) shows `> Access-Control-Request-Method: POST` on the wire and
the server still answering that it is missing; changing the declared method to
`GET` (seq 31) returns the **identical 107 B digest**; widening the requested
headers (seq 32) likewise. Per AGENTS.md §6 #2 the response saying one thing and
the wire saying another is exactly the case that has to be settled by the wire —
here the header is demonstrably present, so the message is server behaviour, not
a client bug.

**INFERRED**, and labelled because it is: that the shadow tenants route
`/oidc/register` to a CORS handler that rejects the preflight before method
negotiation, which is why they return no `access-control-*` headers and a
method-invariant body. The observed facts are the two digests, the absent ACAO,
and the invariance; the handler's internal reason is not observed and nothing
here needs it. **What is established either way is that `/oidc/register` is not
an unrouted path on the shadow tenants either** — their front door marks the
control with `x-auth0-not-found: 1` and does not mark this one, so the request
reached a handler. Whether the shadow tenants would answer a conforming POST is
**not established** and needs a POST, which is area J's subject and remains out
of scope.

So the corrected claim is narrower and more useful than the retraction: three
of five tenants serve the advertised capability and are proven POST-only; on the
other two the route exists and answers, but with a CORS-layer 404 that a client
cannot distinguish from absence by status alone. A client implementing dynamic
client registration against CareLink must implement the trial/EU/US tenant and
treat the shadow tenants as unusable for it.

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

| | certainly-absent `/.well-known/*` | advertised `/oidc/register`, GET 404 |
|---|---|---|
| `content-type` | `text/plain; charset=utf-8` | `application/json; charset=utf-8` |
| body | 10 B | 60 B, `{"statusCode":404,…}` |
| digest | `0802559db137…` | `f006bbd60894…` |
| **`x-auth0-not-found`** | **`1`** | **absent** |
| `cache-control` | `public, max-age=60` | `no-cache` |

**OBSERVED:** `x-auth0-not-found: 1` appears on the well-known miss and on the
absent-path controls, and on nothing else — 7 of the 32 responses this pass
recorded (seq 1, 14 in the GET phase; the five `/oidc/registerx` controls in the
supplementary phase), each of them a path the front door does not know. It is a
better oracle than status code on this host family — it says *the tenant's front
door does not know this path* specifically, which a status code alone cannot.
Note what it is **not** on: the GET 404 from `/oidc/register` on any tenant, and
the 107 B CORS 404 from the two shadow tenants. Both reached a handler; neither
is an unrouted path.

**INFERRED**, with its assumption: that the two signatures correspond to two
different routing states — an unrouted path versus a path that reached Auth0's
API layer and was answered by a handler with nothing to return. The two
signatures are observed; the *meaning* assigned to them is not, and nothing
here needs it to be. Recorded so the next pass does not have to re-derive it.

**This paragraph was right, and it was in the same file as the claim it
contradicts.** The inference recorded here — that the `/oidc/register` 404 was
"a path that reached Auth0's API layer" — is precisely what makes it NOT an
absence. §3 nevertheless reported the endpoint as absent. The pass held a correct
reading and a false summary of it in one document, and shipped the summary.
Correcting it is a matter of taking the INFERRED paragraph at face value, not of
gathering new evidence: the evidence needed to reject "absent" was already in
this file, and this is the same defect class as AGENTS.md §6 #5, derived prose
contradicting its own source table. The OPTIONS run settled it empirically, but
the tell was here.

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

### The supplementary phase added five more controls, one per tenant

The GET-phase controls above were one per host on **two** hosts. The
supplementary OPTIONS phase repeats the discipline on **every** tenant, because
the question it answers — is this path routed? — is per-host:

| # | seq | Request | Result | What it proved |
|---|---|---|---|---|
| C4-C8 | 20, 22, 24, 26, 28 | `/oidc/registerx` (OPTIONS) on each of the five tenants | `404` `text/plain` 10 B, `x-auth0-not-found: 1`, **one digest `0802559db137…` across all five** | The front door marks an unrouted path identically on every tenant, and `/oidc/register` does **not** carry that mark on any of them. This is what makes the 204/404 pair an oracle rather than an observation: same host, same method, same preflight headers, one character of path apart. Sent *first* on each host, before that host's candidate. |

These five controls are also what exposed the original error: had the pass run
the OPTIONS control on `medtronic.eu`, it would have seen `x-auth0-not-found: 1`
on `/oidc/registerx` and its absence on `/oidc/register` in the same run, and the
"absent" claim would not have survived its own evidence.

## 8. Every negative result, stated

- `registration_endpoint` advertised on all five tenants, **`404` to GET on all
  five** (§3). **RETRACTED and superseded: this is no longer a statement about
  absence.** It is live and POST-only on `trials.minimed.com`, `minimed.eu` and
  `minimed.com` (204 + `allow-methods: POST`, per-tenant controls at 404 +
  `x-auth0-not-found: 1`), and on `medtronic.{eu,com}` it reaches a CORS handler
  that answers 404 with no `access-control-*` headers. The GET capture is still
  true; "not one of them serves it" was not, and never could have been, from a
  GET-only probe.
- `kids shared by >1 tenant: 0`. The five key sets stay disjoint (§5).
- `fields absent from at least one document: 0` (§2).
- `x-auth0-not-found` appears on 7 of 32 responses and on **no** live document
  (§4).
- No `x-ratelimit-*` header on any `404`, and no `access-control-allow-origin`
  on any GET `404` — only the `200`s carry CORS there. **Superseded for the
  OPTIONS phase:** `/oidc/register` on the three patient tenants returns
  `access-control-allow-origin` *on a 204*, which is the whole point of it
  (§3).
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
  requests; the cap is committed. Named in the successor instead — **with the
  method corrected**, see §11: it is POST-only by specification (`mfa_challenge`
  takes an MFA token and returns a challenge), so a GET-only successor would
  repeat this pass's error on a second endpoint.

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
- **A failed tool call cost four ledger rows and no requests.** `hurl --test`
  is a boolean flag in 8.0.1, not a name selector. `run.log:22-25` records
  **four** invocations exiting 1 — two script runs × two test cases, at
  18:03:34/18:03:36 and 18:03:52/18:03:54 — every one on a local selector
  error, `Cannot access '<name>': No such file or directory`, having opened no
  socket. That error string is reproducible offline against a non-existent
  filename on hurl 8.0.1, so "opened no socket" is a property of the failure
  mode, not an assumption. Each failing run wrote **two** rows; all **four**
  were caught as false and **removed** rather than left standing — a ledger row
  that claims a fetch which never happened is the same defect class as a claim
  with no source. Removing them was the right call, and `run.log` keeps the
  failed attempts visible instead of tidying them away: a reader can see four
  attempts, zero surviving rows, and reconcile that against the 19-of-20
  accounting at the top of this file, whose 19 rows are the 17 `curl` rows plus
  the 2 that stand from the succeeding run.
  The row count is re-derivable from the log rather than taken on trust — every
  `run.log` line carries the `seq` and `host_seq` that `validate-pins.sh:33,46,48`
  computed from the file as it stood, and both restart at 18/5 for each run,
  which is what 17 rows at the start of a run implies. The real run used one
  file per case.

  Corrected 2026-10-12. An earlier revision of this bullet said "two
  invocations" and "two ledger rows". `run.log:22-25` shows four `hurl_exit=1`
  lines, not two; the row count follows from the seq arithmetic above. The
  defect was an **under**count in the honest direction — it made the discard
  look smaller than it was, and it did not inflate the 19-of-20 cap, which is
  unchanged either way because these invocations opened no socket. Recorded
  rather than silently overwritten, per AGENTS.md §3.
- **`verdict.txt` re-derives from committed artefacts alone.** Verified by
  moving `bodies/` aside and re-running `diff.py`: byte-identical output. The
  five discovery documents and both controls are committed verbatim under
  `openid/`; `diff.py` re-checks every document against its ledger row's byte
  count and sha256 *before* comparing anything, because AGENTS.md §6 #3 is a
  comparison over a lookup that silently returned nothing.

  Re-checked 2026-10-12 in the **stricter** form: `git archive <this commit>`
  extracted into a clean tree containing only tracked files — `bodies/`
  therefore entirely absent, as it is for anyone who clones the repo — and
  `diff.py` re-run there reproduced `verdict.txt` **byte-identically**. That is
  a stronger claim than the local "move `bodies/` aside" test above, because it
  proves nothing in the analysis depends on an artefact a reviewer will not
  have. All 17 raw bodies left on the probing machine were separately checked
  against their `results.jsonl` sha256 and byte counts and all 17 match, so the
  uncommitted bodies are provably the ledger's own captures rather than
  something substituted afterwards.


## 12. The successor, re-tested against its own quality bar

`docs/11`'s area J addendum was written by this pass, so it inherits this pass's
mistakes unless it is checked. It is checked here, on the four tests the repo
applies to a proposed area.

**Derived — PASS.** The advertisement-versus-reality question is real and is not
answered by anything else open: the three siblings are recorded on the EU tenant
only, and `/mfa/challenge` has no probe result in any source. Derivation does
**not** rest on the retracted claim any more — it now rests on the fact that the
retraction *itself* established a route-reachability question this pass could not
answer with GET.

**Bounded — PASS, and the bound is now per-tenant rather than per-pass.** 3 paths
× 5 tenants + a control per host, all path names taken from a discovery document
this repo already holds. No wordlist, no enumeration.

**Non-duplicate — PASS.** Distinct from area J's blocked half (that one needs a
token; this needs none) and from `/oidc/register`, which this pass has now closed
on all five tenants.

**Labelled — the criterion that caught the original error, so it is stated
explicitly.** The addendum's *premise* was labelled OBSERVED and was true; its
*inference* was unlabelled and was false. That is the same asymmetry the verifier
flagged on `x-ratelimit-limit`, where this pass labelled correctly. A successor
inherits its author's labelling habits, which is why the addendum now carries the
inference as INFERRED and names the observed facts it rests on.

**What changed in it, and why it was not dropped.** The addendum previously read
*GET only*, justified by this pass's "absent on all five". All three endpoints are
**POST-only by specification** — `bc-authorize` takes an `auth_req_id`, `mfa_challenge`
takes an MFA token, `global-token-revocation` takes a connection name — so the
original method would have returned "absent" on every tenant and been false every
time. It would have repeated this pass's error three more times. It is therefore
**rewritten, not dropped**: the question it poses is unchanged and still open,
only the verb is corrected. Dropping it would have deleted a real question because
the pass that wrote it up got the method wrong.

## 13. Discharging one leg of issue #23 inside this PR, and why

The claim issue's proposed successor had more than one leg. This pass closed one
of them **in the PR** rather than leaving it for a follow-up: `docs/02` §9's
"JWKS kids for `carelink-login-trials.minimed.com` — Unknown — not in any
source" (§5). The reasoning, stated because a partial discharge is the kind of
thing that goes unexamined:

- It was **already paid for**. The trials JWKS fetch (seq 3) was inside the
  original 20-cap and was requested on its own merits. Closing the leg cost
  **zero** additional requests; leaving it open would have meant re-fetching a
  document this pass had already read.
- It was **bounded and self-contained** — 2 kids, 0 shared, verifiable from
  `jwks-keys.json` and reproducible from a clean clone.
- It was **not a substitute for the rest of the issue.** Area J's token-minting
  question, the `device_code` rejection, and the sibling-endpoint sweep all remain
  open and are named in §9 and §12.

So the discharge is one leg of a multi-leg successor, completed because it was
free and bounded, and **not** a claim that #23 is done. It sits consistently with
`docs/10:46`, which is this repo's prior art for a source disagreeing with itself
(COMMONCRAWL §4e's 12-vs-7): both readings are given, the superseded one stays
visible, and nothing is quietly dropped. The difference is the one that matters —
§4e is a *counting* disagreement settled by leaving both numbers standing, while
this is a *method* error settled by new evidence, so it is corrected **and** the
original retained rather than merely balanced.

## 14. One overstatement in this pass's own tooling

`corpus-audit.py` §F is described as enumerating every `carelink-login*` host
"anywhere in the tracked corpus". Its scan is `if not f.endswith('.md'): continue`
(`:79`), so it reads **Markdown only**.

Separately: `corpus-audit.py` reads `bodies/*.b`, which is gitignored, so it **does
not run from a clean clone** — unlike `diff.py`, which does. That is pre-existing,
not introduced by this fix, and it is recorded rather than papered over. The
kid-disagreement it exists to police is independently re-derivable from committed
material: `jwks-keys.json` holds all ten live kids, and the corpus strings are
`AUTH-TENANT-FINDINGS.md:280,282`, `docs/02:34` and `RECON-SUBDOMAINS.md:244`, all
tracked. What is **not** re-derivable from a clean clone is a check that a live
`kid` string is still live — which needs the network, as it should. Harmless today — no host name lives
outside `.md` in a way that changed the answer — but the conclusion is only as
strong as the scan behind it, so the wording is corrected to say what the code
does. The finding it supports (five tenants, and the union that exposed the two
gaps) is unaffected: the tenant set came from the discovery documents and JWKS
captures, which are `.md` and `.json` in the *results*, not from the `.md` scan.

## 15. A defect this fix introduced and caught: duplicated ledger keys

The supplementary rows were first written with `seq` 1-13, colliding with the
original GET phase. `seq` is `diff.py`'s primary key (`by_seq = {r['seq']: r
for r in rows}`), so the later rows silently shadowed the earlier ones and the
clean-clone re-derivation stopped working — `checked_openid()` looked up `seq 2`,
got an OPTIONS row for `/oidc/registerx`, and died on a filename that did not
exist.

It failed **loudly** rather than silently, which is the only reason it was caught
before the push: the assert-and-verify discipline in `checked_openid()` (added
after AGENTS.md §6 #3) turned a wrong answer into a traceback. A bare dict lookup
without the byte-count and digest assertions would have compared a control's
metadata against a discovery document and produced a plausible wrong number —
the exact failure mode §6 #3 names, one level up. Rows are now numbered 20-32,
`seq` is unique and contiguous over 1-32, and every seq cited in this file points
at the row it claims.

## 16. Correction history for this pass

Two corrections, both recorded rather than overwritten, both kept visible at the
point a reader meets them:

| Date | What | Where it stays visible |
|---|---|---|
| 2026-10-12 | `registration_endpoint` "absent on all five" — **false**; live and POST-only | this file §3 (retraction above the corrected claim), §7 C4-C8; `docs/02`, `docs/10`, `docs/11`, `PR.md` |
| 2026-10-12 | four `hurl_exit=1` invocations / four removed rows, not "two" | this file §11, with the prior wording quoted |

The second correction came from a verifier and the first from a verifier too. In
both cases the *evidence was already on disk* — the run.log lines, and this
file's own §4 inference that described the 404 as "a path that reached Auth0's
API layer". Neither needed a new request to detect; both needed someone to read
the artefact instead of the summary. That is the failure mode worth carrying
forward: a pass that ships a summary is a pass that has to be checked twice.
