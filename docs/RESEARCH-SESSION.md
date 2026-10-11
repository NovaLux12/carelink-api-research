# Run a research session

**The instructions live in [`CONTRIBUTING-research.md`](../CONTRIBUTING-research.md).**

That file is the single source of truth for how to contribute here — the probe
rules, the evidence labels, the gate, and the submission standard. It is written
to be followed by a person or an agent, working from a link.

## Start here

- **New to the project?** Read [`00-summary-the-map.md`](00-summary-the-map.md)
  first — it is what is already known.
- **Looking for something to work on?**
  [`11-suggested-research-areas.md`](11-suggested-research-areas.md).
- **Ready to probe?** [`CONTRIBUTING-research.md`](../CONTRIBUTING-research.md) →
  *Run a research session*.
- **Already have a finding?** [`CONTRIBUTING-research.md`](../CONTRIBUTING-research.md)
  → *Submit a finding*.
- **Found a bridge bug rather than a vendor fact?** That belongs in the client, not
  here — [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge) →
  [bug form](https://github.com/NovaLux12/carelink-bridge/issues/new?template=bug.yml).

## The one-line version

```
./scripts/research-gate.sh
```

That gate — credential scan, citation validation, and the vendor assertion
suite — is what a contribution has to pass. It runs in CI too, so a red gate
blocks the merge regardless.