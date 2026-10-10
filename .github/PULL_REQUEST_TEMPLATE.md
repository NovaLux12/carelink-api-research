## What this PR does

_One line. "Finding", "correction", "research area", or "docs"?_

## Evidence

Every claim has an evidence class and a source cite:

| Claim | Class | Source |
|---|---|---|
| | OBSERVED / PUBLISHED / INFERRED | `findings-log/...` |

## Requests used

- [ ] GET only — no POST, no token exchange, no authentication attempted
- [ ] Slept ≥2s between requests to the same host
- [ ] Stated cap respected: ____ requests of a ____ cap

## The rules

- [ ] No credential, session value, or patient identifier anywhere in the diff
- [ ] Any internal hostname redacted to `<service>.<internal>`
- [ ] Corrections and retractions in the sources are preserved, not smoothed over
- [ ] Any claim the regression suite pins has been updated in this PR, and
      `regression/hurl/run.sh` still exits 0

## Gate

```bash
cd regression/hurl && ./run.sh        # exit 0 = no drift
grep -rIE '<forbidden string>' .      # zero
```

Paste the exit codes here:

```
run.sh exit: __
scrub hits: __
```

## If this changes what a newcomer needs to know first

- [ ] `README.md` updated
- [ ] `docs/00-summary-the-map.md` updated

---

<details>
<summary>Diagrams checklist</summary>

- [ ] Mermaid only (GitHub renders it natively)
- [ ] Every branch is labelled — an unlabelled branch is an INFERRED claim in disguise
- [ ] One diagram answers one question

</details>
