#!/usr/bin/env python3
"""
release_status.py — answer "which services are releasable?" across N services.

Compares the staging ledger against the prod ledger and reports drift:
  - RELEASABLE : staging is ahead of prod (has unreleased, staging-verified changes)
  - IN SYNC    : staging == prod (nothing to do)
  - PROD AHEAD : prod is ahead of staging (anomaly — investigate)

Stdlib only. Runs locally and in CI. Writes a markdown table to
$GITHUB_STEP_SUMMARY when present.

Usage:
  python3 release_status.py                              # pretty table
  python3 release_status.py --format markdown            # markdown
  python3 release_status.py --format json                # machine-readable
  python3 release_status.py --today 2026-07-16           # override "now" for staleness
"""
import argparse
import datetime
import json
import os
import sys

STALE_DAYS = 7


def load(path):
    with open(path) as f:
        return json.load(f)["services"]


def classify(prod, staging):
    rows = []
    for name in sorted(set(prod) | set(staging)):
        p = prod.get(name)
        s = staging.get(name)
        if p and s and p["version"] != s["version"]:
            state = "RELEASABLE"
        elif p and s and p["version"] == s["version"]:
            state = "IN SYNC"
        elif s and not p:
            state = "RELEASABLE"        # brand new service, never in prod
        else:
            state = "PROD AHEAD"        # prod has something staging doesn't
        rows.append({"service": name, "state": state, "prod": p, "staging": s})
    return rows


def staleness(approved_at, today):
    """Age of the staging approval. Accepts an ISO date or datetime; the date
    portion is what matters for staleness."""
    if not approved_at:
        return ""
    d = datetime.date.fromisoformat(approved_at[:10])
    age = (today - d).days
    return f"⚠ stale {age}d" if age > STALE_DAYS else f"{age}d ago"


def approver(cell):
    """Who approved this staging pin. Blank when there is no record — e.g. a
    seeded entry that never passed through the gate."""
    if not cell:
        return ""
    by = cell.get("approved_by")
    return "" if not by else ("auto" if by.startswith("auto") else f"@{by}")


def render_table(rows, today):
    releasable = [r for r in rows if r["state"] == "RELEASABLE"]
    print("\n  RELEASE STATUS\n  " + "=" * 84)
    print(f"  {'':2}{'SERVICE':<16}{'STATE':<12}{'PROD':<10}{'→ STAGING':<12}{'APPROVED BY':<16}{'APPROVED'}")
    print("  " + "-" * 84)
    for r in rows:
        s, p = r["staging"], r["prod"]
        pv = p["semver"] if p else "-"
        sv = s["semver"] if s else "-"
        by = ""
        approved = ""
        if r["state"] == "RELEASABLE" and s:
            by = approver(s)
            approved = staleness(s.get("approved_at"), today)
        arrow = sv if r["state"] == "RELEASABLE" else ""
        marker = "► " if r["state"] == "RELEASABLE" else "  "
        print(f"  {marker}{r['service']:<16}{r['state']:<12}{pv:<10}{arrow:<12}{by:<16}{approved}")
    print("  " + "-" * 84)
    print(f"  {len(releasable)} releasable · {len(rows) - len(releasable)} in sync · {len(rows)} total\n")


def render_markdown(rows, today):
    releasable = [r for r in rows if r["state"] == "RELEASABLE"]
    out = ["## 🚦 Release Status", ""]
    out.append(f"**{len(releasable)} releasable** · {len(rows) - len(releasable)} in sync · {len(rows)} total")
    out.append("")
    out.append("| Service | State | Prod | → Staging | Approved by | Approved |")
    out.append("|---|---|---|---|---|---|")
    for r in rows:
        s, p = r["staging"], r["prod"]
        pv = p["semver"] if p else "-"
        if r["state"] == "RELEASABLE" and s:
            arrow = s["semver"]
            by = approver(s)
            approved = staleness(s.get("approved_at"), today)
            state = "**RELEASABLE**"
        else:
            arrow, by, approved, state = "", "", "", r["state"]
        out.append(f"| {r['service']} | {state} | {pv} | {arrow} | {by} | {approved} |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--prod", default=os.path.join(here, "environments", "prod.json"))
    ap.add_argument("--staging", default=os.path.join(here, "environments", "staging.json"))
    ap.add_argument("--format", choices=["table", "markdown", "json"], default="table")
    ap.add_argument("--today", default=None, help="ISO date to treat as today (staleness).")
    args = ap.parse_args()

    today = datetime.date.fromisoformat(args.today) if args.today else datetime.date.today()
    rows = classify(load(args.prod), load(args.staging))

    if args.format == "json":
        print(json.dumps([r for r in rows if r["state"] == "RELEASABLE"], indent=2))
    elif args.format == "markdown":
        md = render_markdown(rows, today)
        print(md)
    else:
        render_table(rows, today)

    # In CI, also publish a markdown summary to the job page.
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(render_markdown(rows, today))


if __name__ == "__main__":
    sys.exit(main())
