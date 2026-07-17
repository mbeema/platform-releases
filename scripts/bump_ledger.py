#!/usr/bin/env python3
"""
bump_ledger.py — set one service's pin in an environment ledger.

Used by the auto-bump pipeline (staging) and usable by hand. Writes the version
+ semver, and for staging stamps commits/PRs/verified so the release-status
report stays informative.

Usage:
  python3 bump_ledger.py --file environments/staging.json \
      --service orders --version sha-bb11cc2 --semver v1.5.0 \
      [--commits 7 --prs 3 --verified 2026-07-16]
"""
import argparse
import datetime
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--service", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--semver", default="")
    ap.add_argument("--commits", type=int, default=None)
    ap.add_argument("--prs", type=int, default=None)
    ap.add_argument("--verified", default=None, help="ISO date; defaults to today for staging.")
    args = ap.parse_args()

    with open(args.file) as f:
        data = json.load(f)

    env = data.get("environment", "")
    entry = {"version": args.version}
    if args.semver:
        entry["semver"] = args.semver

    # Staging entries carry freshness/volume metadata for the report.
    if env == "staging":
        if args.commits is not None:
            entry["commits"] = args.commits
        if args.prs is not None:
            entry["prs"] = args.prs
        entry["verified"] = args.verified or datetime.date.today().isoformat()

    data.setdefault("services", {})[args.service] = entry

    with open(args.file, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"Pinned {args.service} -> {args.version} ({args.semver or 'no semver'}) in {args.file}")


if __name__ == "__main__":
    main()
