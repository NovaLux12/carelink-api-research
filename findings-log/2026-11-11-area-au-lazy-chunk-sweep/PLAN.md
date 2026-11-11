# Area AU — plan, written before the first request

**Area:** `docs/11` §AU — "Were the 211 patient lazy chunks ever swept for the `INSTINCT` range
tail — and does the `model-mapping` route exist in any chunk the eager bundle does not reach?"
**Host:** `carelink.minimed.eu` only. **Method:** GET only. **Cap:** 225 requests.
**Delay:** `sleep 2.5` inside the shared per-host `flock` (`≥ 2.5 s` same-host spacing).

## What is already known (from the area's own text, OBSERVED)

- `SKU-78963/78964/78965/78968-01` carry `name: "Instinct Sensor"` in
  `/patient/configuration/system/model-mapping/{US,GB,DE}` (area AM).
- `7896\d` is 0 hits in the 3 417 255 B eager bundle (area AM).
- The 211 lazy chunks were swept for the *discovery* token set only (area K); its
  `grep-out.txt` carries 38 tokens, none a SKU or model number.

## What this pass buys, in request order

| # | request | why |
|---|---|---|
| 1 | `common.206e355a4a593fbd.js` | **CONTROL, known-exists with a pinned digest.** Chunk 2076 emits as `common`; area K measured 200 / 21 157 B / `de1f782d…`. Content-hashed name, so the assertion is safe. Abort on mismatch. |
| 2 | `runtime.79e2f9040b1dad8f.js` | **CONTROL, corpus re-derivation.** `f.u` in the runtime is the only thing that defines the chunk list and the `2076→common` rename. Digest asserted (`0dfea208…`, 8 268 B) or abort. |
| 3 | `main.6595daf83bd6c4d1.js` → `main.6595daf83bd6d4b1.js` | **CONTROL, matcher-positive.** The eager bundle carries 3 `Instinct` occurrences and 0 `7896\d` (area AM). Proves the census can see `Instinct`, so a zero over 211 bodies is a zero and not a broken matcher. |
| 4–214 | the 211 chunks, **on their emitted names** | the sweep |

**3 controls + 211 cells = 214 of a 225 cap.** Eleven spare, held back deliberately: a
retry on a transport failure is the only thing that may spend them, and no path is
re-sent after it has a ledger row.

## The sweep list is re-derived, not inherited

`docs/11` §AU records the defect: the committed `chunks-swept.txt` carries the **id** form
`2076.206e355a4a593fbd.js`, which 404s, while the runtime emits that chunk under the
**name** `common`. So the list this pass sweeps is rebuilt from `f.u` in the body fetched at
seq 2, and diffed against the committed list offline. The sweep uses the derived list. If
the derived count is not 211 the run aborts — the population is the question.

## Tokens, and why each one

| token | derived from |
|---|---|
| `7896` / `7896[0-9]` | the area's question; the range tail area AI established |
| `SKU-` | the key form in `model-mapping` (area AM) |
| `productName`, `marketingName` | named in `docs/11` §AU as the "second, richer naming path" |
| `Instinct` / `INSTINCT` | the family string in `model-mapping` and the event-type table |
| `model-mapping`, `modelMapping`, `ModelMapping`, `deviceModelMapping` | the route literal area AM read out of the eager bundle at byte 3 374 392 |
| `configuration/system` | the subtree the `model-mapping` route lives under |

Three counts per token per body (`docs/09` §5): case-sensitive, case-insensitive control,
quoted literal. Every non-zero case-insensitive-only hit gets its enclosing identifier
captured, because `pDe`-inside-`propDecorators` is the documented false-hit class here.

## What "closed" means, and that a negative counts

211 bodies fetched on their emitted names, each `application/javascript` with a distinct
digest, 0 fallbacks; every occurrence of the token set recorded with byte offset and
enclosing context. **A negative closes the area** — "no `7896` occurrence appears in the 211
lazy chunks fetched from `carelink.minimed.eu`" is a complete answer to the corpus half of
the naming question.

## Request-accounting discipline

Every request gets exactly one `results.jsonl` row, appended immediately after the request
completes (never buffered to the end). `hits.tsv` gets exactly one row per chunk, written as
that body lands, so a kill mid-sweep loses at most the in-flight cell. Bodies are never
committed; their digests and sizes are.
