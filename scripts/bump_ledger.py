#!/usr/bin/env python3
"""
bump_ledger.py — set one service's pin in an environment ledger.

Used by the dev auto-bump pipeline and usable by hand. Writes version + semver.
Provenance (who/when) is recorded by the release console's approval stamp, not
here — see scripts/stamp_approval.py.

Usage:
  python3 bump_ledger.py --file environments/dev.json \
      --service orders --version sha-bb11cc2 --semver v1.5.0
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--service", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--semver", default="")
    args = ap.parse_args()

    with open(args.file) as f:
        data = json.load(f)

    entry = {"version": args.version}
    if args.semver:
        entry["semver"] = args.semver

    data.setdefault("services", {})[args.service] = entry

    with open(args.file, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"Pinned {args.service} -> {args.version} ({args.semver or 'no semver'}) in {args.file}")


if __name__ == "__main__":
    main()
