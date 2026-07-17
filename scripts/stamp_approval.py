#!/usr/bin/env python3
"""
stamp_approval.py — record WHO approved a promotion and WHEN, onto each service
entry that this run released, in the target environment.

The version bump is committed at release time, before the gate; approval happens
later, in the deploy jobs, so it is stamped here after the deploys.

  approved_by  GitHub login of the reviewer who released the environment gate.
  approved_at  When the gate released — the deploy job's start time, a real
               auditable moment rather than a wall clock.
  run_id       The release run, linking the ledger back to the full record.

Only the services in --selected are touched; storage layout lives in ledger.py.
"""
import argparse
import json
import sys

import ledger


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True, help="environment that was approved")
    ap.add_argument("--selected", required=True, help="JSON array from select_release.py")
    ap.add_argument("--approved-by", required=True)
    ap.add_argument("--approved-at", required=True, help="ISO 8601, from the deploy job start")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--comment", default="")
    ap.add_argument("--base", default=None, help="ledger dir override (tests)")
    a = ap.parse_args()

    selected = [row["service"] for row in json.loads(a.selected)]
    stamped = []
    for name in selected:
        entry = ledger.get_entry(name, a.env, a.base)
        # The entry must already exist: select wrote it at release time. A
        # missing one means the ledger changed underneath us — fail rather than
        # invent an approval record for something that was never released.
        if entry is None:
            print(f"::error::'{name}' was released but has no {a.env} entry", file=sys.stderr)
            sys.exit(1)
        entry["approved_by"] = a.approved_by
        entry["approved_at"] = a.approved_at
        entry["run_id"] = a.run_id
        if a.comment:
            entry["approval_comment"] = a.comment
        ledger.set_entry(name, a.env, entry, a.base)
        stamped.append(name)

    print(f"Stamped {', '.join(stamped)} in {a.env}: "
          f"approved_by={a.approved_by} approved_at={a.approved_at}")


if __name__ == "__main__":
    main()
