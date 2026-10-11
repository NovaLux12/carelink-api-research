## What this PR does

_One line. "Finding", "correction", "research area", or "docs"?_

## Evidence

Every claim has an evidence class and a source cite:

| Claim | Class | Source |
|---|---|---|
| | OBSERVED / PUBLISHED / INFERRED | `findings-log/...` |

## Requests used

- [ ] GET only, except OPTIONS with an empty body to find POST-only routes, and the two pinned POSTs in `04-deep-surface.hurl` (public client_ids, asserted as 403 failures) — no other POST, no token exchange, no authentication attempted
- [ ] Slept ≥2s between requests to the same host
- [ ] Stated cap respected: ____ requests of a ____ cap

## The rules

- [ ] No credential, session value, or patient identifier anywhere in the diff
- [ ] Any internal hostname redacted to `<service>.<internal>`
- [ ] Corrections and retractions in the sources are preserved, not smoothed over
- [ ] Any claim the regression suite pins has been updated in this PR, and
      `./scripts/research-gate.sh` still exits 0 (PR gate = 05-public-config
      suite + static checks; the full five-suite probe runs in the weekly
      drift sweep)

## Gate

```bash
./scripts/research-gate.sh        # must exit 0 — CI runs the same script
```

Paste the exit code here:

```
research-gate.sh exit: __
```

## If this changes what a newcomer needs to know first

- [ ] `README.md` updated
- [ ] `docs/00-summary-the-map.md` updated

## Downstream consumer impact

<!--
[NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge) pins
values from this repo and runs this repo's regression suite before a release.
-->

- [ ] No pinned consumer value affected
- [ ] A pinned value moved (discovery pin, `BLE_API_VERSIONS`, family vocabulary, error taxonomy) — issue labelled `downstream-bridge` and linked here: ____

---

<details>
<summary>Diagrams checklist</summary>

- [ ] Mermaid only (GitHub renders it natively)
- [ ] Every branch is labelled — an unlabelled branch is an INFERRED claim in disguise
- [ ] One diagram answers one question

</details>
