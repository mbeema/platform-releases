#!/usr/bin/env python3
"""
select_release.py — pick services to promote from one environment to the next.

Given a source ledger (--from), a target ledger (--to), and a selection ("all"
or a comma-separated list), pins the chosen services in the target to the
source's version and emits the selected set as JSON for a deploy matrix.

Usage:
  python3 select_release.py --from environments/staging.json --to environments/prod.json --select all
  python3 select_release.py --from environments/dev.json --to environments/staging.json --select "orders,payments"
"""
import argparse
import json
import os
import sys


def load(p):
    with open(p) as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--to", dest="dst", required=True)
    ap.add_argument("--select", required=True, help="'all' or comma-separated service names")
    a = ap.parse_args()

    src, dst = load(a.src), load(a.dst)
    ss, ds = src["services"], dst.setdefault("services", {})

    # Releasable = source ahead of target (or missing in target).
    releasable = {n for n, v in ss.items() if n not in ds or ds[n]["version"] != v["version"]}

    sel = a.select.strip().lower()
    if sel in ("all", "all-releasable", ""):
        chosen = sorted(releasable)
    else:
        names = [x.strip() for x in a.select.split(",") if x.strip()]
        for n in names:
            if n not in ss:
                print(f"::warning::'{n}' not in {src['environment']} — skipped", file=sys.stderr)
            elif n not in releasable:
                print(f"::notice::'{n}' already matches {dst['environment']} — nothing to release", file=sys.stderr)
        chosen = [n for n in names if n in releasable]

    selected = []
    for n in chosen:
        entry = {"version": ss[n]["version"]}
        if "semver" in ss[n]:
            entry["semver"] = ss[n]["semver"]
        ds[n] = entry  # promoting drops source-only metadata (commits/prs/verified)
        selected.append({"service": n, "version": ss[n]["version"], "semver": ss[n].get("semver", "")})

    with open(a.dst, "w") as f:
        json.dump(dst, f, indent=2)
        f.write("\n")

    out = json.dumps(selected)
    print(out)
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"selected={out}\n")
            f.write(f"has={'true' if selected else 'false'}\n")


if __name__ == "__main__":
    main()
