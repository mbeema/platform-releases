#!/usr/bin/env python3
"""
stamp_approval.py — record WHO approved a promotion and WHEN, onto each service
entry that this run released.

The version bump is committed at release time (in select), before the gate.
Approval happens later, in the deploy jobs, so it cannot be known then — this
runs after the deploys and adds the governance facts as a second commit.

  approved_by  GitHub login of the reviewer who released the environment gate.
  approved_at  When the gate released — sourced from the deploy job's start
               time, not a wall clock, so it is the real moment and auditable.
  run_id       The release run, so the ledger links back to the full record
               (logs, the resolved pin, the approval comment).

Only the services in --selected are touched; other entries are left as-is.
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--selected", required=True, help="JSON array from select_release.py")
    ap.add_argument("--approved-by", required=True)
    ap.add_argument("--approved-at", required=True, help="ISO 8601, from the deploy job start")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--comment", default="")
    a = ap.parse_args()

    selected = [row["service"] for row in json.loads(a.selected)]
    with open(a.file) as f:
        data = json.load(f)
    services = data.get("services", {})

    stamped = []
    for name in selected:
        entry = services.get(name)
        # The entry must already exist: select wrote it at release time. A
        # missing one means the ledger changed underneath us — fail rather than
        # invent an approval record for something that was never released.
        if entry is None:
            print(f"::error::'{name}' was released but is absent from {a.file}", file=sys.stderr)
            sys.exit(1)
        entry["approved_by"] = a.approved_by
        entry["approved_at"] = a.approved_at
        entry["run_id"] = a.run_id
        if a.comment:
            entry["approval_comment"] = a.comment
        stamped.append(name)

    with open(a.file, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"Stamped {', '.join(stamped)} in {a.file}: "
          f"approved_by={a.approved_by} approved_at={a.approved_at}")


if __name__ == "__main__":
    main()
