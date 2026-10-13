# The vendor's own patient app cannot match the Flex family either

Source: `https://carelink.minimed.eu/` serves the **patient portal's** main bundle
at the domain root — not under `/app/` — at 3.4 MB. It is a different bundle from
the *clinician* portal's `main.fb5f8cb7eb60c4d5.js`, which is what all prior JS
work was based on.

**This is the first artefact in the whole research pass that comes from the
patient app rather than the clinic app.** Everything in `JS-API-SURFACE.md` and
`CHUNK-CORPUS-FINDINGS.md` is clinic-side. Do not cite those for patient-path
questions — this note and the config findings are the patient-side sources.

## The finding

Module `45559` of the patient bundle is:

```js
{ BLE: "BLE", BLE_X: "BLE_X", SIMPLERA: "SIMPLERA",
  SIMPLERA_X: "SIMPLERA_X", GUARDIAN: "GUARDIAN" }
```

consumed as:

```js
deviceFamily.startsWith(…)
```

Five tokens. `CC880` is **not among them**, nor is anything containing `FLEX`.

## What that means for issue #81

This is the strongest evidence yet that the device-family matcher is
**model-based, not family-based** — and it weakens the confidence of the
`CC880` conclusion.

Two readings, and I cannot currently separate them:

- **(a) CC880 is the Flex family, and Medtronic's own patient app is out of
  date.** The app would then also fail to detect a Flex. Possible — vendor
  flagship apps routinely lag a shipping device — but odd for a device that is
  already shipping and reported live upstream.
- **(b) There is a further family value we have not found**, one that *does*
  start with one of those five tokens, and the Flex reports that. The published
  config's `CC880 → "MiniMed™ Flex"` mapping would then be a *display* name for a
  device whose wire family is something else.

**Reading (b) is the one that keeps #81 open.** The published configuration tells
us Medtronic's internal label for the Flex; it does not tell us what the patient
API emits, and the patient bundle's five-token `startsWith` matcher is direct
evidence that whatever the Flex sends must be matched *somehow* by code that
looks nothing like a `CC880` comparison.

**Consequence for third-party clients:** matching `CC880` exactly *and* keeping a
model-prefix fallback is not belt-and-braces, it is necessary. A family-only
matcher — even one containing all sixteen published families — is a guess about
which of the two readings is right. The model-prefix path is the one that works
under either reading, because the six Flex model numbers are consistent across
every source we hold.

## NGP alarm codes: absent from the patient bundle too

The patient bundle was also grepped for the NGP vocabulary. Zero real hits — the
three apparent matches are Samsung user-agent strings. This adds to the
accumulating negative for #84: not in the config, not in the clinic bundle, not
in the clinic's 224 lazy chunks, and not in the patient bundle.

## What would settle it

One authenticated `GET /patient/monitor/data` response, logged key-names-only,
would resolve #81 outright. The instruction for that is in
`findings-log/probe-2026-10-08/work/DRAFT-upstream-issue3-reply.md` (deliberately
unresolvable — excluded from this repo by design, as it is a third-party
correspondence draft, so no committed path will ever satisfy this cite).

## Methodology note

This bundle was found by the source-map pass as a side effect, not by the
targeted search. The lesson is that a **negative result on one artefact is worth
extra probing on the same host** — the `.js.map` hunt was the wrong question for
the root of the patient host, and it stumbled onto the right artefact.

## Correction (2026-10-13)

**The "What would settle it" section cites a path that resolves nowhere, and that
is deliberate.** `findings-log/probe-2026-10-08/work/DRAFT-upstream-issue3-reply.md`
is a third-party correspondence draft, excluded from this repo by design — so the
cite is unresolvable on purpose, and the sentence above now says so explicitly
instead of leaving the reader to infer it from "(excluded …)".

<!-- allow-unresolved-cites: findings-log/probe-2026-10-08/work/DRAFT-upstream-issue3-reply.md — third-party correspondence draft, excluded from this repo by design -->

The comment above is the machine-readable half of the same statement: the gate's
findings-log citation check (`scripts/research-checks.py`) flags any cite that resolves
nowhere, and this path is deliberately unresolvable, so the reason travels with the
exemption rather than living only in prose.
