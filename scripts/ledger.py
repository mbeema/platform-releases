#!/usr/bin/env python3
"""
ledger.py — the one place that knows how release state is stored on disk.

State is sharded ONE FILE PER SERVICE (ledger/<service>.json), each holding all
environments:

    { "service": "orders",
      "environments": {
        "dev":     {"version": "sha-...", "semver": "v0.1.6"},
        "staging": {"version": "sha-...", "semver": "v0.1.6", "approved_by": ...},
        "prod":    {"version": "sha-...", "semver": "v0.1.6", "approved_by": ...}
      } }

Sharding per service (not per environment) is deliberate: a release touches only
its own file, so concurrent releases of different services never contend on the
same file. Every other script goes through these helpers, so the layout can
change again in one place.
"""
import json
import os

ENVS = ["dev", "staging", "prod"]


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ledger_dir(base=None):
    return base or os.path.join(_repo_root(), "ledger")


def service_path(name, base=None):
    return os.path.join(ledger_dir(base), f"{name}.json")


def list_services(base=None):
    d = ledger_dir(base)
    if not os.path.isdir(d):
        return []
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


def load_service(name, base=None):
    p = service_path(name, base)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {"service": name, "environments": {}}


def save_service(name, data, base=None):
    p = service_path(name, base)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def get_entry(name, env, base=None):
    return load_service(name, base).get("environments", {}).get(env)


def set_entry(name, env, entry, base=None):
    data = load_service(name, base)
    data.setdefault("service", name)
    data.setdefault("environments", {})[env] = entry
    save_service(name, data, base)


def env_map(env, base=None):
    """{service: entry} for every service that has a pin in this environment."""
    out = {}
    for n in list_services(base):
        e = get_entry(n, env, base)
        if e is not None:
            out[n] = e
    return out
