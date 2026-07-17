#!/usr/bin/env python3
"""
bump_ledger.py — set one service's pin in one environment.

Used by the dev auto-bump pipeline and usable by hand. Writes version + semver.
Provenance (who/when) is recorded by the release console's approval stamp, not
here — see scripts/stamp_approval.py. Storage layout lives in ledger.py.

Usage:
  python3 bump_ledger.py --env dev --service orders \
      --version sha-bb11cc2 --semver v1.5.0
"""
import argparse

import ledger


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--service", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--semver", default="")
    ap.add_argument("--base", default=None, help="ledger dir override (tests)")
    args = ap.parse_args()

    entry = {"version": args.version}
    if args.semver:
        entry["semver"] = args.semver
    ledger.set_entry(args.service, args.env, entry, args.base)

    print(f"Pinned {args.service} -> {args.version} ({args.semver or 'no semver'}) in {args.env}")


if __name__ == "__main__":
    main()
