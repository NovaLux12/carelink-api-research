# AUTHORITATIVE method + status facts (verified 2026-10-09, repeated x3)

## ⚠️ Correction to earlier notes — a harness artifact almost shipped
The earlier observation "monitor/data GET → 403, POST → 405; connect/data
GET → 403, POST → 403" was WRONG. It was caused by `curl -d` forcing POST, so
cases labelled "GET with body" were actually POSTs. Never send `-d` with `-X GET`.

Use the `Allow` header from OPTIONS as the authority, not repeated status codes.

## Verified, reproducible

| Endpoint | `Allow` (from OPTIONS) | Method the bridge uses | Unauth GET | Unauth POST |
|---|---|---|---|---|
| `carelink.*/patient/monitor/data` | `HEAD, GET, OPTIONS` | **GET** ✓ | 401 `InvalidToken` | 405 |
| `carelink.*/patient/connect/data?…last24hours` | *(no Allow header returned)* | **GET** ✓ | 401 `InvalidToken` | 403 `Missing Authentication Token` |
| `clcloud.*/connect/carepartner/{v6,v11,v13}/display/message` | OPTIONS → 200 | **POST** (gateway 403s GET) | 403 (HTML, gateway) | 401 `Authentication failure` |
| `carelink.*/patient/dataUpload/recentUploads` | `POST, OPTIONS` | n/a (bridge does not call) | 405 | 405 with empty body |
| `carelink.*/patient/users/me` | — | GET | 401 `InvalidToken` | — |

## Conclusion for issue #74
The bridge's existing methods are CORRECT. Issue #74 is purely about the HOST
(clcloud vs carelink) for the legacy `connect/data` fallback — not about the
method. Any doc or comment claiming a method bug would be false.

## Conclusion for issue #77
`certificates[]` is always exactly 8 entries, IDENTICAL between the v13 (patient)
and v11 (trials) documents (same sha256). It is therefore NOT a tenant
discriminator. A change-detector on it is only a "did Medtronic rotate their
pinned roots" tripwire — the implementation must not imply more than that.

Pinned hosts, in order: carelink.minimed.com, carelink.minimed.eu,
clcloud.minimed.com, clcloud.minimed.eu, carelink-trials.minimed.com,
clcloud-trials.minimed.com, www.medtronic.com, carelink-content.medtronic.com.

Note `www.medtronic.com` and `carelink-content.medtronic.com` are pinned by
Medtronic's OWN client — first-party evidence that the `medtronic.com` domain is
not a third party, which supports the domain-gotcha note in the docs.
