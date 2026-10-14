# Findings - swarm lane S3: commoncore Origin-axis CORS (area F addendum halves (a) and (c))

Issue #92, 2026-10-13, branch research/s3-headliner. Both closure halves
named in the addendum item ("(a) third host verdict on the square" and
"(c) one host verdict on the Origin axis") are closed below; half (b) stays
in the blocked table, unchanged.

## One line

All 12 cells return the same no-route 403 MissingAuthenticationTokenException
carrying access-control-allow-origin: *, access-control-allow-methods: *,
access-control-allow-headers: *, no Vary, no Allow, no
access-control-allow-credentials, body
{"message":"Missing Authentication Token"}
(sha256 f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16).
Varying the host (the previously unprobed third host) and varying Origin changed
nothing in any cell, so on this no-route envelope both axes are
non-discriminating and neither is an oracle.

## 1. Counting

12 of a 12 cap. 12 real HTTP requests to vendor hosts: 4 on
commoncore-trials.minimed.com plus 4 + 4 on commoncore.medtronic.com. Cap never
exceeded. Cap declared before the first invocation: GET and empty-body OPTIONS
only, >=2.5s between same-host requests, no POST. wc -l results.jsonl = 12.

Methods: GET and OPTIONS with an empty body only. No POST was sent. Origin is a
request header only.

Spacing. t_sent (UTC millisecond ISO-8601):

- commoncore-trials.minimed.com: 3 same-host gaps, min 2.933s, max 3.528s.
- commoncore.medtronic.com: 7 same-host gaps, min 2.731s, max 3.001s.

Independent kernel body-mtime series (re-statted at nanosecond resolution):
min 2.734s across the same pairs, 0 of 10 gaps under 2.5s. No sub-declared
gap on either oracle. Measured spacing floor: 2.731s (t_sent), 2.734s (mtime).
No t_done series convicts itself (every duration positive, 0.2-0.9s per row
in run.log).

## 2. Cells

### Host T, commoncore-trials.minimed.com - breadth (half (a))

1. GET /reports-broker/v1/ocl, no Origin -> 403, digest f249..., ACAO/ACAM/ACAH *
2. GET /reports-broker/v1/ocl-probe-absent, no Origin -> byte-identical
3. OPTIONS /reports-broker/v1/ocl-probe-absent, no Origin -> byte-identical
4. OPTIONS /reports-broker/v1/ocl, no Origin -> byte-identical

### Host O, commoncore.medtronic.com - bare (half (c) baseline)

5. GET /reports-broker/v1/ocl, no Origin -> 403, digest f249..., ACAO/ACAM/ACAH *
6. GET /reports-broker/v1/ocl-probe-absent, no Origin -> byte-identical
7. OPTIONS /reports-broker/v1/ocl-probe-absent, no Origin -> byte-identical
8. OPTIONS /reports-broker/v1/ocl, no Origin -> byte-identical

### Host O, commoncore.medtronic.com - Origin: https://example.invalid

9. GET /reports-broker/v1/ocl, Origin sent -> byte-identical to #5
10. GET /reports-broker/v1/ocl-probe-absent, Origin sent -> byte-identical to #6
11. OPTIONS /reports-broker/v1/ocl-probe-absent, Origin sent -> byte-identical to #7
12. OPTIONS /reports-broker/v1/ocl, Origin sent -> byte-identical to #8

https://example.invalid is an RFC 2606 reserved origin: it can only be echoed
or dropped, never dialled.

## 3. What each half closes

(a) Breadth - closed, negative on discrimination. commoncore-trials.minimed.com
answers both paths and both methods with the exact same no-route envelope as
the two hosts already probed (2026-10-13 cors-method pass). A third host that
carried 1 of the 6 counter-examples to the family claim joins the same
square, byte-identical. The no-route envelope is stage-level on the
commoncore* family, not host-specific. No positive control exists on this
stage on any of the three hosts: the recorded path answers identically to the
certainly-absent one, one more data point on the same envelope (PR #65
correction).

(c) Origin axis - closed, negative on discrimination. Across the 8 paired cells
on commoncore.medtronic.com (#5-#12), sending Origin:
https://example.invalid changed the HTTP status (403 on all 12), the full
access-control-* set, Vary, Allow, the body and its digest. The only
differences between a paired bare/Origin cell were per-request AWS
identifiers the gateway stamps on every response, plus the requested/absent
Origin itself. The gateway does not echo Origin here, and Vary is absent on all
12 cells, so no Origin-conditional handling of the no-route envelope is
observed and the * is not an echo.

## 4. Cross-check

The * is a literal in both access-control-allow-origin and
access-control-allow-methods on every cell. On commoncore* an OPTIONS
response carrying ACAO: * is not proof that a resource exists (docs/09 s2
must read the status beside the header). That needs a routed cell, which this
pass - like the one before - did not send: all 12 cells answered with
MissingAuthenticationTokenException. Statement about the no-route envelope
only, not generalisable to a routed response.

## 5. What remains open

Half (b): a matched commoncore* cell, i.e. one on a path this stage routes, is
untouched and stays in the blocked table row "Report bodies from commoncore".
Token-blocked, not budget-blocked. Every path ever recorded on commoncore*
sits behind a clinician-scoped token; one probe of the namespace root settles
it. Candidate list: the two paths already on disk from the 2026-10-13 passes,
nothing invented, nothing fuzzed.

## 6. Evidence

- results.jsonl, 12 rows, schema in the pass harness.
- headers/, 24 files (one raw + one sent per request).
- bodies/, 12 captures, all identical.
- run.log: seq host method path t_queued t_sent t_done.
- probe.sh: harness as sent.
- append-only: this pass appends, edits nothing else.
