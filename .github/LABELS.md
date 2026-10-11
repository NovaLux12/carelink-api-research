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
| `downstream-bridge` | `0e8a16` | A finding that moves a value the bridge pins — the consumer must be notified |
| `automation` | `ededed` | Opened by a scheduled workflow, not a human |
| `drift` | `fbca04` | A pinned vendor assertion failed on re-probe |
| `stale-claim` | `bfd4f2` | A claimed research area has had no activity |
| `downstream-bridge` | `1d76db` | Changes a value [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge) pins (discovery pin, `BLE_API_VERSIONS`, family vocabulary, error taxonomy). The consumer must be notified and linked before the issue closes. |
