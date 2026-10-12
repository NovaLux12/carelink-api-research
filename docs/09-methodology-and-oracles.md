# Methodology and oracles

How this research was actually done, so it can be repeated or extended without
re-deriving the hard parts — or repeating the mistakes. Everything here comes
from the append-only logs; the method facts were re-verified three times
[source: findings-log/probe-2026-10-08/work/METHOD-FACTS.md]. Extends
[`00-summary-the-map.md`](00-summary-the-map.md).

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = in a vendor
document served without a login · **INFERRED** = reasoned, not seen.

Citations are `[source: findings-log/<file> §n]`; inside tables the bare
filename is the same file: `VERSION-AXIS` =
`findings-log/probe-2026-10-08/recon/VERSION-AXIS.md`, `AWS-GATEWAYS` =
`findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md`, `HCP-SCHEMA` =
`findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md`, `METHOD-FACTS` =
`findings-log/probe-2026-10-08/work/METHOD-FACTS.md`, `CLAIM-AUDIT` =
`findings-log/probe-2026-10-08/audit/CLAIM-AUDIT-2026-10-09.md`, `CONFIG-DEEP` =
`findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md`, `CONFIG-NS` =
`findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE.md`, `RECON-SUBDOMAINS` =
`findings-log/probe-2026-10-08/recon/RECON-SUBDOMAINS.md`, `CROSS-REGION` =
`findings-log/probe-2026-10-08/CROSS-REGION-CONFIG-FINDINGS.md`, `COMMONCRAWL` =
`findings-log/probe-2026-10-08/recon/cc/COMMONCRAWL-URLS.md`, `CHUNK-CORPUS` =
`findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md`, `JSMAP-HUNT` =
`findings-log/probe-2026-10-08/recon/JSMAP-HUNT.md`, `PROBE-FINDINGS` =
`findings-log/probe-2026-10-08/PROBE-FINDINGS.md`, `DRIFT-AND-NEW` =
`findings-log/probe-2026-10-08/recon/DRIFT-AND-NEW-2026-10-10.md`.

## 1. The constraints every pass ran under

| Constraint | How it was honoured |
|---|---|
| Read-only | GET and empty-body probes only; no `-X` overrides, no POST that writes. The one credential-adjacent act in the whole project was sending the published bundle key to the reports host to test validity — it returned 403 [source: findings-log/probe-2026-10-08/SECURITY-FINDINGS.md §Scope, S3] |
| Unauthenticated | no `Authorization`, no `Cookie`, no token, no api-key of the vendor's. A dummy `X-Api-Key: DUMMY-NOT-A-KEY-000000000000` was the only auth-ish header ever sent [AWS-GATEWAYS §8] |
| Low rate | ≥1.2 s spacing on probe rounds; ≥2 s per host enforced in-harness (`last_hit[]`); 2.5 s measured floor on the gateway sweep; ≥3 s on archive calls [VERSION-AXIS §Method; AWS-GATEWAYS §1; recon/ARCHIVE-URLS.md §0] |
| Hard request caps | per pass, and never exceeded: 30 (22 used), 60 (42 used), 80 (80), 70 (70), 90 (90), 26 archive, 41 Wayback, ~600 total across the day's passes [CONFIG-NS §Method; HCP-SCHEMA §1; CONFIG-DEEP §cap; VERSION-AXIS §Method; AWS-GATEWAYS §1; COMMONCRAWL §0; SECURITY-FINDINGS §Scope] |
| No dev/stage contact | dev/stage/test/load hosts are **enumerated passively and listed, never probed** [PROBE-FINDINGS §1; RECON-SUBDOMAINS §7.2] |
| No scanning | no port scans, no DNS bruteforce, no vhost fuzzing, no path enumeration beyond bounded, justified candidate lists [RECON-SUBDOMAINS §0; CONFIG-NS §Method] |
| Hosts that looked internal | recorded and left alone — every internal-looking name refuses the public network [RECON-SUBDOMAINS §4.5] |

## 2. Oracle A — the AWS API-Gateway family (inverted)

On `clcloud.*` and the five `*.execute-api.*.amazonaws.com` gateways the
surface is AWS API Gateway behind CloudFront, so every response carries
`x-amzn-errortype` — and Amazon uses **different error types for "no route"
versus "reached a backend authorizer"** [source: VERSION-AXIS §1].

| Signal | Meaning | Verdict |
|---|---|---|
| `x-amzn-errortype: MissingAuthenticationTokenException` (403, 42 B) | **no matching route** | dead — path does not exist |
| `UnauthorizedException` + `x-ca-err: 990` (401) | request reached Medtronic's Layer7 authorizer | live — route exists, token-gated |
| no errortype (200/204) | public | live, unauthenticated |

**The inversion, stated plainly:** on these gateways **403 is the unmatched-route
error**, a 404 is never emitted (it is simply not in the gateway's response
vocabulary — zero 404s in 90 requests), so "403 = exists, auth-gated" is false
and "404 = absent" is unreachable. A certainly-absent control UUID returns
byte-identical output to the published root. **403 can never positively confirm a
route; it only ever confirms a negative** [source: AWS-GATEWAYS §0, §2].

The full oracle needs **both** methods, or it under-reports liveness:

```
GET 403 + OPTIONS 403 → dead
GET 403 + OPTIONS 200 → live, POST-only      (CORS headers present)
GET 401              → live with GET
GET 200/204          → public
```

`access-control-allow-origin: *` on an OPTIONS request is the cleanest proof that
a resource exists with no GET method — that is how POST-only
`v6/display/message` was found [source: VERSION-AXIS §1]. **But
`access-control-allow-methods` is not a register of the route's methods:**
`carepartner/v13/display/message` advertises `OPTIONS` on its preflight and is
GET-capable (`GET` → 401 `UnauthorizedException` + `x-ca-err: 990`) on all three
hosts (OBSERVED,
[findings-log/2026-10-12-csr-cross-host/FINDINGS.md]). Settle method
registration from the GET probe; treat the CORS method list as corroboration
only. The one positive direction on the bare gateways: on `dialog-lite`, `500
InternalServerErrorException` proves a path **is** matched (the Lambda raised),
which is how the stage-wide catch-all was identified; on `patient-timeline` 403
positively confirms *no* GET/OPTIONS route [source: AWS-GATEWAYS §2, §11].
`x-cache: Miss/Error from cloudfront` tracks the same split but is a weaker,
derived signal — keep `x-amzn-errortype` as the authority. **Latency is not an
oracle**: host dominates, not version [source: VERSION-AXIS §1].

## 3. Oracle B — the portal family (reliable)

On `carelinkhp.*` / `/hcp/*` the status set **is** reliable, because the SPA
fallback is distinguishable by content-type and the namespace is case-sensitive
[source: HCP-SCHEMA §3, §4]:

| Response | Meaning |
|---|---|
| `200` + `application/json` | key exists, published unauthenticated |
| `401` + `InvalidToken` | **key exists but is token-gated** |
| `404`, 0 bytes | **key does not exist** |
| `412`, 0 bytes | header check failed (missing/invalid `X-System-ID`) |
| `405` | exists, POST-only |
| `200` + `text/html` + 5518 B | SPA fallback — says nothing about existence |

Validated with a positive control: `…/public/personal/media/config/eu` → 401
(exists, gated) versus `…/public/personal/media/config` → 404 and a fabricated
key → 404. And with a case control: `CSU.CONTROL.CODES.SETTINGS` → 404 while
`cua.control.codes.settings` → 200, so a lower-case 404 is a true absence. Two
controls convert 28 "not found" verdicts into a defensible negative
[source: HCP-SCHEMA §4, §7].

**What neither oracle can prove:** content behind a gate; and on the `configs/v1`
S3 bucket, `AccessDenied` is returned for absent keys too — a 403 there is
indistinguishable from "exists but unreadable", so the honest phrasing is "no
evidence of existence", never "confirmed absent" [source: CONFIG-NS TARGET 3;
AUTH-TENANT-FINDINGS §6].

## 4. The trap list

| Trap | Detail | Fix |
|---|---|---|
| Parked wildcard namespaces | `*.carelink.{eu,com}` and `*.clcloud.eu` are wildcard DNS on parking operators — a random, certainly-unregistered string resolves and 302s to a parked page; a Let's Encrypt wildcard reissued on a ~90-day cadence injects the names into every CT scraper. 49 collected names are false positives | never attribute a name from this space to Medtronic; the proof is a name that cannot exist [RECON-SUBDOMAINS §3; PROBE-FINDINGS deep §8] |
| 5518-byte SPA fallback | `carelinkhp.minimed.eu` returns 200 `text/html`, exactly 5518 B, for **every** unknown path — including fabricated chunk names. Nearly stored 225 copies of `index.html` in the chunk sweep | discriminate on `Content-Type`, never on status; `carelink.medtronic.eu` serves the same page gzipped, so compare sizes after decompression [CHUNK-CORPUS; CONFIG-DEEP TARGET 5] |
| Unconditional gzip | `carelink.minimed.eu` serves gzip ignoring `Accept-Encoding` (RFC 9110 §8.4); hurl's jsonpath returns `none` because hurl only decodes what it asked for — which is why the config regression is a shell script, not a `.hurl` file | `curl --compressed`, or decompress locally; do not re-request [HURL-05 header; README rule 6] |
| `index.commoncrawl.org` unreachable | both attempts failed (`curl (56)` / `(52)`) while `data.commoncrawl.org` over the identical TLS path worked — a host-level failure, not rate limiting | used the bulk path (binary-search `cluster.idx`, ranged `cdx-NNNNN.gz` fetches); coverage capped to two crawls instead of ~100, and that cap is stated rather than papered over [COMMONCRAWL §0–§1] |
| `curl -d` forcing POST | an earlier "GET vs POST" matrix was wrong because `-d` forces POST — cases labelled "GET with body" were actually POSTs | re-probe with a clean GET and discriminate on `x-amzn-errortype`, **not** the status. There is no `Allow` header to fall back on: across all 42 captured `clcloud.*` responses on disk (26 from 2026-10-11, 16 from 2026-10-12) **not one carried `Allow`**, so the GET probe is the only method authority this host family offers [METHOD-FACTS §Correction] |
| CORS `allow-methods` read as a method register | `access-control-allow-methods` is gateway CORS configuration, not the route's registered methods. `carepartner/v13/display/message` advertises `OPTIONS` and is GET-capable (`GET` → 401 `UnauthorizedException` + `x-ca-err: 990`) on all three hosts | settle method registration from the **GET probe**; treat `allow-methods` as corroboration. The header is also not canonicalised: two routes that are *both* GET-403 and OPTIONS-200 advertise different lists, in different orders, with different allow-headers (OBSERVED: `csr/v2` → `OPTIONS,POST`, bare `v2` → `POST,OPTIONS` + three extra allow-headers) [findings-log/2026-10-12-csr-cross-host/FINDINGS.md] |
| jq `//` swallowing `false` | a country sweep conflated "key absent" with "value false" | re-derive with `has()` [PROBE-FINDINGS deep §8] |
| Mis-offset CDX fetches | an earlier pass's computed byte ranges landed on alphabetical neighbours; the `raw-*.cdx` artefacts look like results and are not | corrected fetches kept; wrong artefacts labelled misleading on disk [COMMONCRAWL §1] |
| Self-measurement artefact | `deep-matrix.jsonl`'s `x-api-key: "len=10"` is the length of the scrubber's own `[REDACTED]` placeholder — the pass measured itself | length column ignored; further scrubbing added [CONFIG-DEEP §Measurement artifact] |

## 5. Verification discipline — the four ways this project has been wrong

Each of these actually happened. Each produced a mechanism, not an apology.

**1. A claim without evidence.** The `pde/v3` status was recorded as 401 in the
notes when the live probe returned 403; a review round then "corrected" the
architecture doc from 403 to 401, and a later round marked it VERIFIED — four
rounds, all trusting the previous hop. Re-probed twice: **403**. The distinction
matters: on `clcloud.*` that body is a gateway-level rejection (the host does
not route the path at all), not an app-level token gate. **Fix:** re-probe the
numbers, don't re-read the notes; the correction-of-a-correction is recorded as
such [source: CLAIM-AUDIT §FOUND WRONG]. Same class: the METHOD-FACTS `curl -d`
artifact, and the S3-bucket 403 that was never evidence of non-existence even
though the conclusion it supported held [source: METHOD-FACTS; CONFIG-NS].

**2. A grep that hit without proving.** "Neither `main.js` nor `runtime.js`
contains a `sourceMappingURL` comment" was false — `hp-main.js` contains the
token at byte offset 1791807, as a `worker-loader` string literal, not a
directive. The conclusion (no source maps) survived; the stated reason did not.
Same class twice more: the apparent `ngp`/`guardian` matches in the clinic bundle
were zxcvbn dictionary noise (case-sensitive grep: 0 hits), and the patient
bundle's three "NGP" hits were Samsung user-agent strings. And once more in the
2026-10-10 drift sweep: a prose note quoted the family-map hash as `215e6671de09`
when it actually hashes to `8ce419a22fd3` on every artefact on disk and live —
the pinned regression assertion had been right all along and the hand-written
note was wrong, which is how it surfaced [source: DRIFT-AND-NEW §Documented
defect]. **Fix:** prove what a hit *is* — literal vs directive, byte offset,
case-sensitive control — and replace sampling with an exhaustive offline grep
plus 62 live probes and written reopen conditions; "values quoted in prose notes
are not evidence. The pinned assertion is" [source: CHUNK-CORPUS §source maps;
HCP-SCHEMA §4; recov/PATIENT-APP-VOCABULARY.md; JSMAP-HUNT §7; DRIFT-AND-NEW].

**3. A hash comparison over a lookup that silently returned null.** The
cross-region config comparison reported four "SAME" rows where only three were
same: the walker looked up dotted-nested paths with a single
`dict.get("a.b.c")`, got `None`, and hashed `None` — two genuinely different
values produced identical digests and looked like agreement. **Fix:** walk the
path segment-by-segment and assert the resolved type; `HURL-05` treats an
all-zero digest (`e3b0c442…`, the sha256 of the empty string) as a failure
rather than a comparison. "A hash check over a lookup that can silently return
`null` will manufacture consensus" [source: CROSS-REGION §Verification note;
HURL-05].

**4. A dead test-file typecheck.** In the bridge repo, neither `npx tsc
--noEmit` nor CI could see a type error in any test file — the base tsconfig
excludes `test/` — which is how a TS2322 in a test went unnoticed. **Fix:**
`tsconfig.test.json`, which has to restate both `include` and `exclude` (the
base excludes `test/`) and set `rootDir: "."` (the base sets `rootDir: "src"`);
verified by injecting a type error and watching CI's new step fail. Recorded
downstream in the consumer repo:
[source: [NovaLux12/carelink-bridge CHANGELOG #87](https://github.com/NovaLux12/carelink-bridge/blob/main/CHANGELOG.md)].

The generalisation behind all four: a check that *looks* like it ran is worse
than no check, because it converts a gap into a green tick.

## 6. The append-only log / canonical-docs split

`docs/` is canonical, synthesised, dated. `findings-log/` is append-only,
verbatim, dated — the audit trail. **`docs/` supersedes `findings-log/` where
they disagree**, and the logs are kept anyway, because conclusions were retracted
and re-derived and that history is itself evidence (a retraction you cannot see
is a claim you cannot audit) [source: README].

Practical consequences, all visible in this repo:

- Corrections are **appended, never edited away**: the `pde/v3` 403→401→403
  chain, the S3 scope widening, the source-map claim's wrong reason, and the
  four-tenant upgrade all live in the logs with their reasoning intact
  [source: CLAIM-AUDIT; SECURITY-FINDINGS addendum; CHUNK-CORPUS;
  AUTH-TENANT-FINDINGS §8].
- Claims are pinned by a regression suite so they fail loudly rather than rot:
  `regression/hurl/` holds 110 assertions (262 execute per run, counting the
  16-family loop expansion and hurl's status-line checks); exit 0 = the public
  surface has not drifted *past the pinned values* since 2026-10-08
  [source: docs/00-summary-the-map.md;
  findings-log/probe-2026-10-08/work/VALIDATION-RUNBOOK.md Tier 5]. The config
  checks deliberately pin the vendor's *current wrong* `lhpro` bound so a vendor
  fix breaks the test and updates the note [source: HURL-05].
- Where a pass's own evidence could not be written to disk, the log says so
  instead of implying it exists: the 2026-10-10 drift sweep is explicitly a
  **reconstruction from the agent's report**, "re-verify before treating any row
  as OBSERVED" — a provenance caveat, not a finding [source: DRIFT-AND-NEW
  §Provenance].
- Redaction rules (six of them in the README) exist because breaking them
  leaked something: never commit a credential, never publish internal hostnames,
  never publish raw archive captures, never report a parked-namespace name,
  discriminate on content-type not status, use `curl --compressed`
  [source: README §Rules].

## 7. Reproducing

The pass harnesses and machine logs are named in each source file and are the
authoritative artefacts: `vaxis-probe.sh` / `vaxis.jsonl` (oracle + 70-cell
sweep), `aws-gw-probe.py` / `gw-probe-results.jsonl` (cap + delay + scrub),
`hcp2probe.sh` / `hcp2-matrix.jsonl`, `deep-probe.sh` / `deep-matrix.jsonl`,
`cdx/q.sh` + `request-log.tsv` (archive passes), `locate.py` / `qr.sh` /
`ccparse.py` (Common Crawl bulk path), and `hurl/run.sh` + `05-public-config.check.sh`
(drift detection) [source: VERSION-AXIS §8; AWS-GATEWAYS §9; HCP-SCHEMA §1;
CONFIG-DEEP §cap; COMMONCRAWL §10; HURL-05]. Re-derive the oracle controls
before trusting any future 404 or 403 from these hosts [source: HCP-SCHEMA
§10].
