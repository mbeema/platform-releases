# Artifact retention at scale (100 services)

Immutable `sha-*` tags accumulate fast. Without GC the registry balloons and
costs climb. The rule: **never purge an artifact an environment still points
at**, keep every release-tagged image, and trim old untagged SHAs.

## 1. Lock release + live tags as immutable

```bash
# Prevent overwriting/deleting a semver release image.
az acr repository update \
  --name myacr --image orders:v1.4.2 \
  --write-enabled false --delete-enabled false
```

## 2. Scheduled purge of stale SHA tags (keep last 10, keep 30 days)

```bash
# Run as a scheduled ACR Task. Purges only sha-* tags; leaves vX.Y.Z alone.
PURGE_CMD="acr purge \
  --filter 'orders:^sha-.*' \
  --keep 10 \
  --ago 30d \
  --untagged"

az acr task create \
  --name purge-orders \
  --registry myacr \
  --cmd "$PURGE_CMD" \
  --schedule "0 3 * * *" \
  --context /dev/null
```

## 3. Protect what is deployed (the ledger is the allow-list)

Before any purge, resolve the digests referenced by `environments/*.json` and
exclude them. A pre-purge guard step (pseudo):

```bash
# Collect every version currently pinned in any environment ledger.
IN_USE=$(jq -r '.services[].version' platform-releases/environments/*.json | sort -u)
# Feed IN_USE into your purge filter's exclusion list so live digests survive
# even if they fall outside "last 10 / 30 days".
```

## Policy summary

| Keep | Rule |
|---|---|
| Anything pinned in any env ledger | Always — it's live somewhere |
| Every `vX.Y.Z` semver image | Always — releases are immutable history |
| Last N `sha-*` per service | Rollback headroom (N≈10) |
| `sha-*` older than 30d, untagged | Purge |
