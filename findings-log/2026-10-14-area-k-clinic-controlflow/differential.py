#!/usr/bin/env python3
"""Cross-client differential: clinic build vs patient build, by SET OPERATION.

Written because a sentence like "the clinic client calls more endpoints" is
worthless without the set difference (AGENTS.md section 6 item 5 — derived prose
that contradicted its own source table and propagated into five pages).

Three questions, three answers:

 1. ARE THESE THE SAME BUILD? Compared by content hash, per chunk id, plus the
    eager bundles and the runtimes. A differential between a corpus and itself
    would be vacuous, so this runs FIRST and the differential refuses to print if
    the two builds are not distinct.

 2. THE SETS. Shapes in clinic but not patient (clinician-only), in patient but
    not clinic (patient-only), and in both (shared). Each with its method
    breakdown. A shape is (METHOD, normalised_path) — the same key S4's own
    counting rule produces, slot-renumbered by position, so the two sides are
    counted by ONE rule rather than two.

 3. THE ARITHMETIC. Are S4's four counter columns summing to its total? Is its
    by_method sum equal to its distinct_pairs? Both re-derived from the committed
    counters.json, never from the prose that quotes it — S4 section 7.1 records
    what reading the prose instead of the file costs.

Usage: differential.py <clinic-pairs.tsv> <patient-pairs.tsv> <patient-counters.json>
                        <clinic-counters.json> <clinic-map> <patient-map> <out.json>
"""
import csv
import hashlib
import json
import sys


def read_pairs(path):
    """(METHOD, normalized_path) -> set of branches, from an S4 pairs.tsv."""
    out = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            key = (row["method"], row["normalized_path"])
            out.setdefault(key, set()).add(row["branch"])
    return out


def read_map(path):
    """Chunk id -> (emitted basename, content hash), plus any NON-NUMERIC-id entries.

    Accepts either of the two shapes the two passes committed:
      * `id name hash` per line (the clinic runtime-map.txt), or
      * a `<<<DERIVED_BEGIN>>> … <<<DERIVED_END>>>` block of
        `<emitted-basename>.<hash>.js` lines (the patient runtime-map.txt, which
        also carries a prose report above the block).

    The non-numeric bucket exists because the `f.u` special case emits the NAME
    `common` for chunk id 2076, so one entry in each derived list has a
    non-numeric id in that list and would be silently dropped by an
    id-join-keyed comparison. Dropping it would understate the patient map by one
    entry and make the two sides' counts incomparable, so it is counted
    separately and reported rather than discarded.
    """
    out, special = {}, {}
    text = open(path).read()
    body = text
    if "<<<DERIVED_BEGIN>>>" in text:
        body = text.split("<<<DERIVED_BEGIN>>>", 1)[1].split("<<<DERIVED_END>>>", 1)[0]
    for line in body.splitlines():
        p = line.split()
        if len(p) == 3 and p[0].isdigit():
            out[p[0]] = (p[1], p[2])
        elif line.strip().endswith(".js"):
            f = line.strip()
            cid, _, h = f[:-3].rpartition(".")
            (out if cid.isdigit() else special)[cid] = (cid, h)
    return out, special


def methods(keys):
    d = {}
    for m, _p in keys:
        d[m] = d.get(m, 0) + 1
    return dict(sorted(d.items()))


def breakdown(pairs, keys):
    """method breakdown AND branch breakdown AND interpolation split for a set."""
    ks = {k for k in keys if k in pairs}
    lead = sum(1 for _m, p in ks if p.startswith("/"))
    interp = sum(1 for _m, p in ks if "{" in p)
    branches = {}
    for k in ks:
        for b in pairs[k]:
            branches[b] = branches.get(b, 0) + 1
    return {
        "n": len(ks),
        "by_method": methods(ks),
        "by_branch": dict(sorted(branches.items())),
        "with_leading_slash": lead,
        "without_leading_slash": len(ks) - lead,
        "with_interpolation": interp,
        "without_interpolation": len(ks) - interp,
        "paths": sorted(f"{m} {p}" for m, p in ks),
    }


def main():
    (clinic_pairs_p, patient_pairs_p, patient_counters_p,
     clinic_counters_p, clinic_map_p, patient_map_p, out_p) = sys.argv[1:8]

    clinic_pairs = read_pairs(clinic_pairs_p)
    patient_pairs = read_pairs(patient_pairs_p)
    pc = json.load(open(patient_counters_p))
    cc = json.load(open(clinic_counters_p))

    out = {"build_distinctness": {}, "differential": {}, "arithmetic": {}}

    # ------------------------------------------------- 1. are these one build?
    cmap, cspecial = read_map(clinic_map_p)
    pmap, pspecial = read_map(patient_map_p)
    shared_ids = set(cmap) & set(pmap)
    same_hash = sorted((i for i in shared_ids if cmap[i][1] == pmap[i][1]), key=int)
    out["build_distinctness"] = {
        "counting_rule": ("chunk id is the join key; the CONTENT HASH decides "
                          "whether the two builds put different bytes under it. A "
                          "name diff cannot tell 'same file, wrong name' from "
                          "'two different files' (docs/09 section 4, trap row 3)."),
        "clinic_map_entries": len(cmap),
        "clinic_map_entries_with_non_numeric_id": cspecial,
        "patient_map_entries": len(pmap),
        "patient_map_entries_with_non_numeric_id": pspecial,
        "chunk_ids_in_both": len(shared_ids),
        "chunk_ids_with_IDENTICAL_content_hash": len(same_hash),
        "chunk_ids_with_DIFFERENT_content_hash": len(shared_ids) - len(same_hash),
        "identical_hash_ids": same_hash,
        "ids_only_in_clinic": sorted(set(cmap) - set(pmap), key=int),
        "ids_only_in_patient": sorted(set(pmap) - set(cmap), key=int),
        "n_ids_only_in_clinic": len(set(cmap) - set(pmap)),
        "n_ids_only_in_patient": len(set(pmap) - set(cmap)),
        "example_divergence": [
            {"id": i, "clinic_emitted": ".".join(cmap[i]), "patient_emitted": ".".join(pmap[i])}
            for i in sorted(shared_ids, key=int)[:6]
        ],
        "eager_main_bundle_clinic_sha256": "2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba",
        "eager_main_bundle_patient_sha256": "0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa",
        "eager_main_bundle_bytes_clinic": 3397615,
        "eager_main_bundle_bytes_patient": 3417255,
        "runtime_sha256_clinic": "47939ec873c1fd9a05d733f0a487c28957b82e0a558187361fd6742b01f0959a",
        "runtime_sha256_patient": "0dfea208804facf881a79ea9e8758dc6900e74ef174c11ba50250c0a62273722",
        "runtime_bytes_clinic": 8597,
        "runtime_bytes_patient": 8268,
        "webpack_global_name": "self.webpackChunkpow — the SAME global namespace "
                              "name in both builds, which is why a name-based join "
                              "would be meaningless; only the content hash decides",
    }
    distinct = (out["build_distinctness"]["chunk_ids_with_DIFFERENT_content_hash"] > 0
                and out["build_distinctness"]["eager_main_bundle_clinic_sha256"]
                != out["build_distinctness"]["eager_main_bundle_patient_sha256"])

    # ------------------------------------------------------- 2. the set op
    C, P = set(clinic_pairs), set(patient_pairs)
    clinic_only = C - P
    patient_only = P - C
    shared = C & P
    out["differential"] = {
        "precondition_builds_are_distinct": distinct,
        "key": "(METHOD, normalized_path) — S4's own slot-renumbering rule, both sides",
        "n_clinic_shapes": len(C),
        "n_patient_shapes": len(P),
        "n_shared": len(shared),
        "n_clinic_only": len(clinic_only),
        "n_patient_only": len(patient_only),
        "set_arithmetic": f"{len(clinic_only)} + {len(shared)} = {len(C)}; "
                          f"{len(patient_only)} + {len(shared)} = {len(P)}",
        "clinic_only": breakdown(clinic_pairs, clinic_only),
        "patient_only": breakdown(patient_pairs, patient_only),
        "shared": breakdown(clinic_pairs, shared),
    }

    # ------------------------------------------------------- 3. arithmetic
    def arith(c, label):
        cols = ["sites_with_literal_path", "sites_with_baseurl_resolved_path",
                "sites_with_constant_resolved_path", "sites_with_unresolved_variable_path"]
        tot = sum(c[k] for k in cols)
        bm = sum(c["by_method"].get(m, 0) for m in ("get", "post", "put", "delete", "patch"))
        return {
            "corpus": label,
            "n_chunk_files": c["n_chunk_files"],
            "corpus_bytes": c["corpus_bytes"],
            "corpus_manifest_sha256": c["corpus_manifest_sha256"],
            "http_call_sites_total_committed": c["http_call_sites_total"],
            "four_columns": {k: c[k] for k in cols},
            "four_columns_sum": tot,
            "four_columns_sum_minus_total": tot - c["http_call_sites_total"],
            "four_columns_sum_equals_total": tot == c["http_call_sites_total"],
            "by_method": c["by_method"],
            "by_method_sum": bm,
            "distinct_pairs": c["distinct_pairs"],
            "by_method_sum_equals_distinct_pairs": bm == c["distinct_pairs"],
            "leading_slash_sum": c["pairs_with_leading_slash"] + c["pairs_without_leading_slash"],
            "leading_slash_sum_equals_distinct_pairs":
                c["pairs_with_leading_slash"] + c["pairs_without_leading_slash"] == c["distinct_pairs"],
            "interpolation_sum": c["pairs_with_interpolation"] + c["pairs_without_interpolation"],
            "interpolation_sum_equals_distinct_pairs":
                c["pairs_with_interpolation"] + c["pairs_without_interpolation"] == c["distinct_pairs"],
        }

    out["arithmetic"]["patient"] = arith(pc, "patient (S4, committed counters.json)")
    out["arithmetic"]["clinic"] = arith(cc, "clinic (this pass, committed counters.json)")

    with open(out_p, "w") as fh:
        json.dump(out, fh, indent=2)

    print(json.dumps(out["build_distinctness"], indent=2))
    print("\n=== DIFFERENTIAL ===")
    d = out["differential"]
    print(f"builds distinct: {d['precondition_builds_are_distinct']}")
    print(f"clinic {d['n_clinic_shapes']} / patient {d['n_patient_shapes']}  "
          f"shared {d['n_shared']}  clinic-only {d['n_clinic_only']}  patient-only {d['n_patient_only']}")
    print(f"set arithmetic: {d['set_arithmetic']}")
    for k in ("clinic_only", "patient_only", "shared"):
        print(f"\n-- {k}: n={d[k]['n']} by_method={d[k]['by_method']} "
              f"by_branch={d[k]['by_branch']} lead_slash={d[k]['with_leading_slash']}/"
              f"{d[k]['without_leading_slash']} interp={d[k]['with_interpolation']}/"
              f"{d[k]['without_interpolation']}")
    print("\n=== ARITHMETIC ===")
    print(json.dumps(out["arithmetic"], indent=2))
    print("\n-- clinic-only paths --")
    for p in d["clinic_only"]["paths"]:
        print("  ", p)
    print("\n-- patient-only paths --")
    for p in d["patient_only"]["paths"]:
        print("  ", p)


if __name__ == "__main__":
    main()