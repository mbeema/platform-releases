#!/usr/bin/env python3
"""
dashboard.py — the single pane: what version of each service is in each env.

Reads dev/staging/prod ledgers and renders a services x environments matrix.
Emits:
  --fragment PATH   body-only HTML (for a Claude Artifact / embed)
  --standalone PATH self-contained HTML page (for GitHub Pages)
  stdout            a markdown table (also appended to $GITHUB_STEP_SUMMARY)
"""
import argparse
import datetime
import json
import os

ENVS = ["dev", "staging", "prod"]


def load(env, base):
    with open(os.path.join(base, f"{env}.json")) as f:
        return json.load(f)["services"]


def build_rows(base):
    ledgers = {e: load(e, base) for e in ENVS}
    names = sorted(set().union(*[set(l) for l in ledgers.values()]))
    rows = []
    for n in names:
        cells = {e: ledgers[e].get(n) for e in ENVS}
        newest = cells["dev"]["version"] if cells["dev"] else None
        versions = [c["version"] for c in cells.values() if c]
        rolled_out = len(set(versions)) == 1 and len(versions) == len(ENVS)
        rows.append({"name": n, "cells": cells, "newest": newest, "rolled_out": rolled_out})
    return rows


# ---------------------------------------------------------------- HTML
STYLE = """
<style>
  :root{
    --ground:#f5f8fb; --surface:#ffffff; --ink:#0f1b2d; --muted:#5c6b82;
    --border:#e4eaf3; --head:#f0f4f9; --accent:#0e9bb0;
    --good:#15803d; --good-bg:#dcfce7; --warn:#b45309; --warn-bg:#fdf0d5;
    --shadow:0 1px 2px rgba(15,27,45,.05),0 10px 30px rgba(15,27,45,.06);
  }
  @media (prefers-color-scheme:dark){
    :root{
      --ground:#090e18; --surface:#101a2c; --ink:#e7eef8; --muted:#93a4bd;
      --border:#213149; --head:#16233a; --accent:#2bd0e0;
      --good:#4ade80; --good-bg:#0f2a1c; --warn:#fbbf24; --warn-bg:#33230a;
      --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
    }
  }
  :root[data-theme="light"]{
    --ground:#f5f8fb; --surface:#ffffff; --ink:#0f1b2d; --muted:#5c6b82;
    --border:#e4eaf3; --head:#f0f4f9; --accent:#0e9bb0;
    --good:#15803d; --good-bg:#dcfce7; --warn:#b45309; --warn-bg:#fdf0d5;
  }
  :root[data-theme="dark"]{
    --ground:#090e18; --surface:#101a2c; --ink:#e7eef8; --muted:#93a4bd;
    --border:#213149; --head:#16233a; --accent:#2bd0e0;
    --good:#4ade80; --good-bg:#0f2a1c; --warn:#fbbf24; --warn-bg:#33230a;
  }
  *{box-sizing:border-box}
  .rct{
    font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
    color:var(--ink); background:var(--ground); padding:clamp(20px,4vw,44px);
    line-height:1.5; -webkit-font-smoothing:antialiased;
  }
  .rct .head{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-end;justify-content:space-between;margin-bottom:26px}
  .rct h1{font-size:clamp(20px,3vw,27px);margin:0;letter-spacing:-.02em;font-weight:680;text-wrap:balance}
  .rct .sub{margin:4px 0 0;color:var(--muted);font-size:14px}
  .rct .chips{display:flex;gap:10px;flex-wrap:wrap}
  .rct .chip{background:var(--surface);border:1px solid var(--border);border-radius:12px;
    padding:10px 14px;display:flex;flex-direction:column;min-width:88px;box-shadow:var(--shadow)}
  .rct .chip .n{font-size:22px;font-weight:700;font-variant-numeric:tabular-nums;line-height:1}
  .rct .chip .l{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-top:5px}
  .rct .chip.good .n{color:var(--good)} .rct .chip.warn .n{color:var(--warn)}
  .rct .tablewrap{overflow-x:auto;border:1px solid var(--border);border-radius:14px;
    background:var(--surface);box-shadow:var(--shadow)}
  .rct table{border-collapse:collapse;width:100%;min-width:640px}
  .rct th,.rct td{text-align:left;padding:13px 16px;border-bottom:1px solid var(--border)}
  .rct thead th{background:var(--head);font-size:11px;text-transform:uppercase;letter-spacing:.08em;
    color:var(--muted);font-weight:600;position:sticky;top:0}
  .rct tbody tr:last-child td{border-bottom:none}
  .rct .svc{font-weight:620;font-size:14.5px}
  .rct .cell{white-space:nowrap}
  .rct .ver{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-variant-numeric:tabular-nums;
    font-size:13.5px;font-weight:600}
  .rct .sha{display:block;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;color:var(--muted);margin-top:2px}
  .rct .cell.behind{position:relative}
  .rct .cell.behind .ver{color:var(--warn)}
  .rct .cell.behind::before{content:"";position:absolute;left:0;top:9px;bottom:9px;width:3px;
    background:var(--warn);border-radius:0 2px 2px 0}
  .rct .cell.empty{color:var(--muted)}
  .rct .pill{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;
    padding:4px 11px;border-radius:999px;white-space:nowrap}
  .rct .pill::before{content:"";width:7px;height:7px;border-radius:50%}
  .rct .pill.good{background:var(--good-bg);color:var(--good)} .rct .pill.good::before{background:var(--good)}
  .rct .pill.warn{background:var(--warn-bg);color:var(--warn)} .rct .pill.warn::before{background:var(--warn)}
  .rct .foot{margin-top:16px;font-size:12px;color:var(--muted)}
  .rct .foot b{color:var(--ink);font-weight:600}
</style>
"""


def cell_html(cell, newest):
    if not cell:
        return '<td class="cell empty">—</td>'
    behind = " behind" if newest and cell["version"] != newest else ""
    return (f'<td class="cell{behind}"><span class="ver">{cell.get("semver","?")}</span>'
            f'<span class="sha">{cell["version"]}</span></td>')


def render_inner(rows, generated):
    total = len(rows)
    promoting = sum(1 for r in rows if not r["rolled_out"])
    done = total - promoting
    body = [STYLE, '<div class="rct">']
    body.append('<div class="head"><div>'
                '<h1>Release Control Tower</h1>'
                '<p class="sub">What&#39;s deployed where, across every environment</p></div>'
                '<div class="chips">'
                f'<div class="chip"><span class="n">{total}</span><span class="l">services</span></div>'
                f'<div class="chip warn"><span class="n">{promoting}</span><span class="l">promoting</span></div>'
                f'<div class="chip good"><span class="n">{done}</span><span class="l">rolled out</span></div>'
                '</div></div>')
    body.append('<div class="tablewrap"><table><thead><tr>'
                '<th>Service</th><th>Dev</th><th>Staging</th><th>Prod</th><th>Status</th>'
                '</tr></thead><tbody>')
    for r in rows:
        status = ('<span class="pill good">Rolled out</span>' if r["rolled_out"]
                  else '<span class="pill warn">Promoting</span>')
        cells = "".join(cell_html(r["cells"][e], r["newest"]) for e in ENVS)
        body.append(f'<tr><td class="svc">{r["name"]}</td>{cells}<td>{status}</td></tr>')
    body.append('</tbody></table></div>')
    body.append(f'<p class="foot">Generated <b>{generated}</b> · source of truth: '
                'platform-releases ledgers · amber = behind the latest build</p>')
    body.append('</div>')
    return "\n".join(body)


def render_markdown(rows):
    out = ["## Release Control Tower", "", "| Service | Dev | Staging | Prod | Status |",
           "|---|---|---|---|---|"]
    for r in rows:
        c = {e: (r["cells"][e]["semver"] if r["cells"][e] else "—") for e in ENVS}
        status = "✅ Rolled out" if r["rolled_out"] else "🟡 Promoting"
        out.append(f'| {r["name"]} | {c["dev"]} | {c["staging"]} | {c["prod"]} | {status} |')
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--base", default=os.path.join(here, "environments"))
    ap.add_argument("--fragment", default=None)
    ap.add_argument("--standalone", default=None)
    ap.add_argument("--generated", default=None)
    a = ap.parse_args()

    generated = a.generated or datetime.date.today().isoformat()
    rows = build_rows(a.base)
    inner = render_inner(rows, generated)

    if a.fragment:
        with open(a.fragment, "w") as f:
            f.write(inner + "\n")
    if a.standalone:
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Release Control Tower</title>'
                '<style>html,body{margin:0}body{background:#f5f8fb}'
                '@media(prefers-color-scheme:dark){body{background:#090e18}}</style>'
                f'</head><body>{inner}</body></html>')
        with open(a.standalone, "w") as f:
            f.write(page)

    md = render_markdown(rows)
    print(md)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(md)


if __name__ == "__main__":
    main()
