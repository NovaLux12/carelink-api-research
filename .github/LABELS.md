# Label scheme

Apply with `gh label create <name> --description "..." --color <hex>` on first run,
or let the issue forms apply the defaults above.

| Label | Colour | Meaning |
|---|---|---|
| `finding` | `0e8a16` | A confirmed, sourced finding |
| `correction` | `d93f0b` | Something here is wrong |
| `research-area` | `1d76db` | An area from docs/11 is claimed and being worked |
| `security` | `b60205` | Exposure, credential, or data-path issue |
| `needs-verification` | `fbca04` | Filed, not yet independently checked |
| `verified` | `0e8a16` | Independently reproduced by a second session |
| `pinned` | `5319e7` | Covered by a regression-suite assertion |
| `docs` | `c5def5` | Documentation only |
| `blocked-on-token` | `bfd4f2` | Cannot proceed without an authenticated response |
| `automation` | `ededed` | Opened by a scheduled workflow, not a human |
| `drift` | `fbca04` | A pinned vendor assertion failed on re-probe |
| `stale-claim` | `bfd4f2` | A claimed research area has had no activity |
| `downstream-bridge` | `1d76db` | Changes a value [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge) pins. The consumer must be notified and linked before the issue closes — see below. |

### `downstream-bridge` in full

Applies when a finding changes a **pinned** value on the consumer side: the
discovery app-version pin, `BLE_API_VERSIONS`, the device family vocabulary, or an
error-class taxonomy. Not every finding needs it — only one a consumer has
hard-coded.

The issue is not finished without the notification: link the consumer issue, name the
constant that moved, and say that the bridge runs this repo's suite before a release.
The drift sweep is the job most likely to need this label.
