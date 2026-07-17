#!/usr/bin/env python3
"""
select_release.py — decide what lands in a target environment's ledger.

Two modes:
  PROMOTE  (--from SRC):  pin the chosen services from the source env (the env
                          below). Multi-service and 'all' supported.
  PIN      (--version V): pin ONE service to a specific immutable build. Used to
                          release/redeploy an exact version (e.g. a rollback).

Emits the selected set as JSON for a deploy matrix.
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
    ap.add_argument("--to", required=True)
    ap.add_argument("--select", required=True, help="'all' or comma-separated service names")
    ap.add_argument("--from", dest="src", default=None, help="source ledger (promote mode)")
    ap.add_argument("--version", default=None, help="immutable version to pin (pin mode)")
    ap.add_argument("--semver", default=None)
    a = ap.parse_args()

    dst = load(a.to)
    ds = dst.setdefault("services", {})
    names = [x.strip() for x in a.select.split(",") if x.strip()]
    selected = []

    if a.version:
        # ---- PIN a specific build (single service) ----
        if len(names) != 1:
            print("::error::a specific version requires exactly one service", file=sys.stderr)
            sys.exit(1)
        n = names[0]
        entry = {"version": a.version}
        if a.semver:
            entry["semver"] = a.semver
        ds[n] = entry
        selected.append({"service": n, "version": a.version, "semver": a.semver or ""})
    else:
        # ---- PROMOTE from the env below ----
        if not a.src:
            print("::error::promotion mode needs --from", file=sys.stderr)
            sys.exit(1)
        src = load(a.src)
        ss = src["services"]
        releasable = {x for x, v in ss.items() if x not in ds or ds[x]["version"] != v["version"]}
        sel = a.select.strip().lower()
        if sel in ("all", "all-releasable", ""):
            chosen = sorted(releasable)
        else:
            for n in names:
                if n not in ss:
                    print(f"::warning::'{n}' not in {src['environment']} — skipped", file=sys.stderr)
                elif n not in releasable:
                    print(f"::notice::'{n}' already matches {dst['environment']} — nothing to release", file=sys.stderr)
            chosen = [n for n in names if n in releasable]
        for n in chosen:
            entry = {"version": ss[n]["version"]}
            if "semver" in ss[n]:
                entry["semver"] = ss[n]["semver"]
            ds[n] = entry
            selected.append({"service": n, "version": ss[n]["version"], "semver": ss[n].get("semver", "")})

    with open(a.to, "w") as f:
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
