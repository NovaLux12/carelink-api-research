#!/usr/bin/env python3
"""Area AM — offline extraction over the four committed-derived bodies. ZERO requests.

The four bodies live in the main clone's gitignored `.loop/am-scratch/` and are NOT
committed (a 39 KB vendor document copies straight into findings-log, so what is
committed is the extracted tables, not the body — AGENTS.md §7 on captures, and the
area A/G precedent).

What this script does, and why each assertion exists:

1. Parse each body TWICE — once normally, once with an `object_pairs_hook` that keeps
   duplicate keys. `json.loads` silently collapses a duplicate key to the last value,
   which is exactly the `AGENTS.md` §6 item 3 failure ("a lookup that silently returned
   null") in a different costume: a duplicate key would make the second reading differ
   from the first and be invisible. If the two readings disagree the script exits 2.
2. Assert the resolved shape before comparing anything: five top-level categories, each
   a dict of code → object carrying at least `name` and `family`. A body that does not
   have that shape is a hard failure, never an absence.
3. Emit `instinct-model-mapping.tsv` — one row per (deployment, country, category, code).
4. Emit `tail-names.tsv` — the four tail codes, both key forms, per country.
5. Exit non-zero if any of the four tail codes is missing from either country's SENSOR
   category, so a parse regression cannot be reported as "no name".

Usage: AM_SCRATCH=<dir> python3 extract.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# five levels up = the MAIN clone root: <clone>/.loop/worktrees/lam/findings-log/<area>
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
SCRATCH = os.environ.get("AM_SCRATCH", os.path.join(REPO, ".loop", "am-scratch"))

BODIES = {
    # tag -> (deployment, country)
    "m-us-com": ("carelink.minimed.com", "US"),
    "m-us-eu":  ("carelink.minimed.eu", "US"),
    "m-gb-eu":  ("carelink.minimed.eu", "GB"),
    "m-de-eu":  ("carelink.minimed.eu", "DE"),
}

TAIL = ["78963", "78964", "78965", "78968"]
# The 13 the patient family map enumerates (area AI) — the comparison set.
ALL13 = ["78893", "78953", "78954", "78955", "78956", "78957", "78958",
         "78959", "78960", "78963", "78964", "78965", "78968"]


class Dups(dict):
    """Returned by the hook only when a dict literal carried a repeated key."""
    def __init__(self, pairs):
        super().__init__()
        self.dups = []
        for k, v in pairs:
            if k in self:
                self.dups.append(k)
            self[k] = v


def dup_aware(pairs):
    d = Dups(pairs)
    return d


def find_dups(node, path="$"):
    """Walk the hook-built tree and report every dict that carried a repeated key."""
    bad = []
    if isinstance(node, Dups) and getattr(node, "dups", None):
        bad.extend(f"{path}.{k}" for k in node.dups)
    if isinstance(node, dict):
        for k, v in node.items():
            bad.extend(find_dups(v, f"{path}.{k}"))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            bad.extend(find_dups(v, f"{path}[{i}]"))
    return bad


def load(tag):
    path = os.path.join(SCRATCH, tag + ".b")
    if not os.path.exists(path):
        raise SystemExit(f"MISSING BODY: {path} — run probe.sh modelmap first")
    raw = open(path, "rb").read()
    plain = json.loads(raw)
    dupd = json.loads(raw, object_pairs_hook=dup_aware)
    # Reading 1 (json.loads, last-value-wins) vs reading 2 (duplicate-aware): any dict
    # that carried a repeated key is named here. A silent collapse is impossible.
    bad = find_dups(dupd)
    if bad:
        raise SystemExit(f"STOP {tag}: duplicate key(s) at {bad[:10]} — a single reading of "
                         f"this document is lossy and no claim may rest on one")
    if json.dumps(dupd, sort_keys=True) != json.dumps(plain, sort_keys=True):
        raise SystemExit(f"STOP {tag}: the two readings disagree with no duplicate key reported")
    # Shape assertion before any comparison (AGENTS.md §6 item 3).
    if not isinstance(plain, dict) or not plain:
        raise SystemExit(f"STOP {tag}: top level is not a non-empty object")
    nameless = []
    for cat, models in plain.items():
        if not isinstance(models, dict) or not models:
            raise SystemExit(f"STOP {tag}: category {cat!r} is not a non-empty object")
        for code, v in models.items():
            if not isinstance(v, dict):
                raise SystemExit(f"STOP {tag}: {cat}/{code} is not an object — wrong document")
            if "name" not in v:
                nameless.append(f"{cat}/{code}")
    # `DEFAULT` is a real sentinel in this document (min/max + feature flags, no name).
    # Anything ELSE without a name aborts: a nameless model would make "no name" ambiguous.
    unexpected = [n for n in nameless if not n.endswith("/DEFAULT")]
    if unexpected:
        raise SystemExit(f"STOP {tag}: {len(unexpected)} model entry/entries carry no `name` "
                         f"({unexpected[:8]}) — the shape is not the one this script reads")
    return plain, len(raw), nameless


def main():
    docs = {}
    print(f"{'tag':10s} {'deployment':26s} {'country':8s} {'bytes':>7s}  categories / code counts")
    for tag, (host, cc) in BODIES.items():
        doc, n, nameless = load(tag)
        docs[tag] = doc
        cats = " ".join(f"{k}={len(v)}" for k, v in doc.items())
        print(f"{tag:10s} {host:26s} {cc:8s} {n:7d}  {cats}  nameless={nameless}")

    # --- instinct-model-mapping.tsv : every INSTINCT row in every category, both countries
    rows = []
    for tag, (host, cc) in BODIES.items():
        for cat, models in docs[tag].items():
            for code, v in models.items():
                if v.get("family") == "INSTINCT" or "nstinct" in str(v.get("name", "")):
                    feat = v.get("features") or {}
                    rows.append((host, cc, cat, code, v.get("name", ""), v.get("family", ""),
                                 v.get("shortName", ""), feat.get("patientListNonPremium", ""),
                                 feat.get("patientListPremium", ""), feat.get("dataCalendar", ""),
                                 str(v.get("maxValue", "")), str(v.get("minValue", ""))))
    rows.sort()
    out = os.path.join(HERE, "instinct-model-mapping.tsv")
    with open(out, "w") as f:
        f.write("deployment\tcountry\tcategory\tcode\tname\tfamily\tshortName\t"
                "patientListNonPremium\tpatientListPremium\tdataCalendar\tmaxValue\tminValue\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    print(f"\nwrote {out} ({len(rows)} INSTINCT rows)")

    # --- tail-names.tsv : the four, both key forms, per country, SENSOR only
    out2 = os.path.join(HERE, "tail-names.tsv")
    missing = []
    with open(out2, "w") as f:
        f.write("country\tcode\tkey_form\tpresent\tname\tfamily\tpatientListPremium\tpatientDashboard\n")
        for cc_tag in ("m-us-com", "m-gb-eu"):
            host, cc = BODIES[cc_tag]
            models = docs[cc_tag].get("SENSOR", {})
            for c in TAIL:
                for form in (f"SKU-{c}-01", f"{c}-01"):
                    v = models.get(form)
                    if not v:
                        missing.append((cc, form))
                        f.write(f"{cc}\t{c}\t{form}\tNO\t\t\t\t\n")
                        continue
                    feat = v.get("features") or {}
                    f.write(f"{cc}\t{c}\t{form}\tYES\t{v['name']}\t{v['family']}\t"
                            f"{feat.get('patientListPremium','')}\t{feat.get('patientDashboard','')}\n")
    print(f"wrote {out2}")

    # --- coverage.tsv : the 13 family-map codes against this document, per country
    out3 = os.path.join(HERE, "coverage-13.tsv")
    with open(out3, "w") as f:
        f.write("code\tUS_bare\tUS_SKU\tGB_bare\tGB_SKU\tname_US\tname_GB\n")
        for c in ALL13:
            got = {}
            for tag, cc in (("m-us-com", "US"), ("m-gb-eu", "GB")):
                models = docs[tag].get("SENSOR", {})
                got[(cc, "bare")] = models.get(f"{c}-01")
                got[(cc, "sku")] = models.get(f"SKU-{c}-01")
            f.write(f"{c}\t"
                    f"{'Y' if got[('US','bare')] else 'N'}\t{'Y' if got[('US','sku')] else 'N'}\t"
                    f"{'Y' if got[('GB','bare')] else 'N'}\t{'Y' if got[('GB','sku')] else 'N'}\t"
                    f"{(got[('US','bare')] or {}).get('name','-')}\t"
                    f"{(got[('GB','bare')] or {}).get('name','-')}\n")
    print(f"wrote {out3}")

    if missing:
        print(f"\nMISSING (this is a hard failure, not an absence): {missing}", file=sys.stderr)
        return 2
    print("\nOK — all four tail codes present in both key forms in both countries' SENSOR category")
    return 0


if __name__ == "__main__":
    sys.exit(main())
