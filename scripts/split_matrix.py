#!/usr/bin/env python3
"""
split_matrix.py — route the selected release set to the right deploy pipeline.

select_release.py answers "what version of which service ships". This answers
"which pipeline deploys it", by joining that set against services.json.

A reusable-workflow `uses:` cannot be chosen from a matrix expression, so the
routing cannot happen inside one deploy job — the set is split here and each
type gets its own job in release.yml.

Emits matrix_container / matrix_zip (+ has_* flags) to $GITHUB_OUTPUT.
"""
import argparse
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selected", required=True, help="JSON emitted by select_release.py")
    ap.add_argument("--registry", default="services.json")
    a = ap.parse_args()

    selected = json.loads(a.selected)
    with open(a.registry) as f:
        registry = json.load(f)["services"]

    buckets = {"container": [], "zip": []}
    for item in selected:
        name = item["service"]
        meta = registry.get(name)
        # An unregistered service must not be skipped quietly: a release that
        # reports success while shipping nothing is worse than a failed one.
        if meta is None:
            print(f"::error::'{name}' is in the ledger but not in {a.registry}. "
                  f"Add it to the registry so a deploy knows how to ship it.", file=sys.stderr)
            sys.exit(1)
        stype = meta.get("type")
        if stype not in buckets:
            print(f"::error::'{name}' has type '{stype}' in {a.registry}; "
                  f"expected 'container' or 'zip'.", file=sys.stderr)
            sys.exit(1)
        buckets[stype].append({**item, **meta})

    gh = os.environ.get("GITHUB_OUTPUT")
    for stype, rows in buckets.items():
        payload = json.dumps(rows)
        print(f"{stype}: {payload}")
        if gh:
            with open(gh, "a") as f:
                f.write(f"matrix_{stype}={payload}\n")
                f.write(f"has_{stype}={'true' if rows else 'false'}\n")


if __name__ == "__main__":
    main()
