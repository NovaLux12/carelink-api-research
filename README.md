# CareLink API research

Read-only, unauthenticated documentation of Medtronic's CareLink network
surface — the auth tenants, the API namespaces, the configuration the vendor
publishes without a login, and the undocumented services those configs name.

This is research, not a client. It exists so that the next person building a
CareLink integration — or auditing one — does not start from zero.

**Start here:** [`docs/00-summary-the-map.md`](docs/00-summary-the-map.md).

## What is in here

```
docs/               canonical, synthesised, dated. Read these first.
findings-log/       append-only research logs, dated and verbatim. The audit trail.
regression/hurl/    a pinned assertion suite that re-checks the vendor surface.
                    Exit 0 = nothing drifted. Run it before quoting any claim.
```

`docs/` supersedes `findings-log/` where they disagree. The logs are kept because
conclusions were retracted and re-derived, and that history is evidence.

## Rules — do not break these

These are not stylistic. Each one exists because breaking it leaked something.

1. **Never commit a credential.** API keys, tokens, site keys, session values.
   Record *that* a credential is published and *where*, never the value. Two
   vendor keys and one reCAPTCHA site key are known to be published; all are
   redacted in `findings-log/` with the finding intact.
2. **Never publish internal hostnames.** Names recovered from certificate logs
   (`grafana.*`, `k8s.*`, `gitlab.*`, `db.*`, monitoring hosts) are redacted to
   `<service>.<internal>.minimed.<tld>`. The finding — that a vendor's CT logs
   leak internal infrastructure names — survives the redaction; the names do not.
3. **Never publish raw archive captures.** Common Crawl/Wayback records contain
   live `jsessionid_*` values in URL paths, and pre-Auth0 authorize URLs whose
   `sessionData` is a plaintext-base64 JWS. Only the extracted facts are here.
4. **`*.carelink.eu`, `*.carelink.com`, `*.clcloud.eu` are wildcard DNS on a
   parking operator.** A random unregistered string resolves, and every name 302s
   to a parked page. ~50 names in the collection are false positives. Never
   report one as a vendor asset — that is how a false positive reaches a
   disclosure.
5. **This host family returns HTTP 200 with 5518 bytes of HTML for every path
   that does not exist.** Discriminate on `Content-Type`, never on status code.
   This trap caused three near-misses in one session.
6. **`carelink.minimed.eu` serves `Content-Encoding: gzip` unconditionally,**
   ignoring `Accept-Encoding` entirely (verified against `identity`, `gzip`,
   `deflate`). Use `curl --compressed`. Without it every parse fails.

## Method

Everything here was gathered read-only and unauthenticated, one request every
1–2 seconds, against endpoints the vendor publishes. No credentials were used, no
authentication was attempted, no state was created, and no token was ever
presented. Hosts that appeared internal were recorded and left alone.

Where a conclusion came from **published vendor configuration** rather than a
**live API response**, the docs say so. The distinction matters: Medtronic's own
config files disagree with each other about how device families are spelled, and
one document's trailing-whitespace padding makes it unusable as a machine
contract.

## Status

Unverified-until-proven is the default. Anything confirmed against a live
authenticated response is labelled; anything else is labelled INFERRED. Repo
issues #81 (wire shape), #84 (authenticated config), #85 (timestamp semantics)
and #76 (report bodies) remain open precisely because they need a token.

## Provenance

Derived from `NovaLux12/carelink-bridge` research notes (2026-07-21 and
2026-10-08/09 passes), scrubbed and synthesised for publication. Original
append-only logs are in `findings-log/` unedited apart from the redactions
listed above.
