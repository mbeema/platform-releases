# platform-releases — the release control plane

The single source of truth for **what version of each service is live in each
environment**, and the mechanism to release "when ready" across 100 services.

```
platform-releases/
├─ environments/
│  ├─ prod.json               what is LIVE in prod (the pins)
│  └─ staging.json            what has passed staging (release candidates)
├─ scripts/
│  ├─ release_status.py       diff staging vs prod → "which are releasable?"
│  └─ changed_services.py     diff prod pins across a commit → who to deploy
├─ .github/workflows/
│  ├─ release-status.yml      scheduled/on-demand "what's ready to ship" report
│  └─ promote.yml             on prod.json change → deploy EXACTLY the bumped ones
└─ policies/
   └─ acr-retention.md        keep-live / keep-releases / purge-stale GC policy
```

## The loop

```
build once → push image :sha  →  green in staging → CI bumps staging.json pin
                                          │
   release-status.yml  reads staging vs prod  →  "N services releasable"
                                          │
   RELEASE = PR that bumps prod.json pin  →  merge
                                          │
   promote.yml  detects changed pins  →  deploys ONLY those (slot swap)
                                          │
   git history of prod.json  =  the audit log.  revert = rollback.
```

## Why this scales to 100 services

- **"Which to release" is a diff, not a decision.** `release_status.py` surfaces
  only the handful of services where staging is ahead of prod. The rest are
  provably in sync — you never think about them.
- **Release is a reviewed PR.** Bumping a pin in `prod.json` is auditable,
  batchable (one service or twenty in one PR), and revertable.
- **Deploy touches only what changed.** `promote.yml` diffs the commit and runs
  a matrix over exactly the bumped services — not all 100.
- **Independent cadence.** Each service's pin moves on its own; there is no
  global version and no big-bang train.

## Try the POC locally

```bash
# Which services are releasable right now?
python3 scripts/release_status.py --today 2026-07-16

# Simulate the promote detector: who changed between two ledgers?
python3 scripts/changed_services.py environments/prod.json environments/staging.json
```

## Releasing, step by step

1. Run (or read the scheduled) **release-status** report → see candidates.
2. Open a PR editing `environments/prod.json`, changing the `version` (and
   `semver`) of the service(s) you want to ship to match `staging.json`.
3. Reviewer approves the PR (this is your release approval).
4. Merge → **promote.yml** deploys exactly those services to prod (slot swap).
5. Something wrong? **Revert the PR** → promote redeploys the previous digest.

> POC note: `promote.yml`'s deploy step is a dummy `echo`. In production it calls
> `reusable-deploy.yml` / `reusable-deploy-zip.yml` with the pinned digest.
