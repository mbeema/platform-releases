#!/usr/bin/env python3
"""
select_release.py — decide what lands in a target environment.

Two modes:
  PROMOTE  (--from-env SRC): pin the chosen services from the source env (the
                             env below). Multi-service and 'all' supported.
  PIN      (--version V):     pin ONE service to a specific immutable build. Used
                             to release/redeploy an exact version (e.g. rollback).

Operates on environment NAMES; storage layout lives in ledger.py. Emits the
selected set as JSON for a deploy matrix.
"""
import argparse
import json
import os
import sys

import ledger


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to-env", required=True, help="target environment name")
    ap.add_argument("--from-env", default=None, help="source environment (promote mode)")
    ap.add_argument("--select", required=True, help="'all' or comma-separated service names")
    ap.add_argument("--version", default=None, help="immutable version to pin (pin mode)")
    ap.add_argument("--semver", default=None)
    ap.add_argument("--base", default=None, help="ledger dir override (tests)")
    a = ap.parse_args()

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
        ledger.set_entry(n, a.to_env, entry, a.base)
        selected.append({"service": n, "version": a.version, "semver": a.semver or ""})
    else:
        # ---- PROMOTE from the env below ----
        if not a.from_env:
            print("::error::promotion mode needs --from-env", file=sys.stderr)
            sys.exit(1)
        src = ledger.env_map(a.from_env, a.base)
        dst = ledger.env_map(a.to_env, a.base)
        releasable = {x for x, v in src.items() if x not in dst or dst[x]["version"] != v["version"]}
        sel = a.select.strip().lower()
        if sel in ("all", "all-releasable", ""):
            chosen = sorted(releasable)
        else:
            for n in names:
                if n not in src:
                    print(f"::warning::'{n}' not in {a.from_env} — skipped", file=sys.stderr)
                elif n not in releasable:
                    print(f"::notice::'{n}' already matches {a.to_env} — nothing to release", file=sys.stderr)
            chosen = [n for n in names if n in releasable]
        for n in chosen:
            # Only version+semver are promoted; approval is re-earned at the gate,
            # so the fresh entry deliberately drops any prior approval fields.
            entry = {"version": src[n]["version"]}
            if "semver" in src[n]:
                entry["semver"] = src[n]["semver"]
            ledger.set_entry(n, a.to_env, entry, a.base)
            selected.append({"service": n, "version": src[n]["version"], "semver": src[n].get("semver", "")})

    out = json.dumps(selected)
    print(out)
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"selected={out}\n")
            f.write(f"has={'true' if selected else 'false'}\n")


if __name__ == "__main__":
    main()
