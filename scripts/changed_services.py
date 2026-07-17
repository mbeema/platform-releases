#!/usr/bin/env python3
"""
changed_services.py — diff two prod ledgers and emit the services whose pinned
version changed. Used by the promote pipeline to deploy EXACTLY the bumped
services (not all N).

Usage:
  python3 changed_services.py OLD_prod.json NEW_prod.json
Prints a JSON array suitable for a GitHub Actions matrix:
  [ { "service": "orders", "version": "sha-bb11cc2", "semver": "v1.5.0" }, ... ]
"""
import json
import sys


def load(path):
    try:
        with open(path) as f:
            return json.load(f)["services"]
    except FileNotFoundError:
        return {}


def main():
    old = load(sys.argv[1])
    new = load(sys.argv[2])
    changed = []
    for name in sorted(new):
        if name not in old or old[name]["version"] != new[name]["version"]:
            changed.append({
                "service": name,
                "version": new[name]["version"],
                "semver": new[name].get("semver", ""),
            })
    print(json.dumps(changed))


if __name__ == "__main__":
    main()
