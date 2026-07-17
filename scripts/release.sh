#!/usr/bin/env bash
# Interactive "select and release" from your terminal.
# Shows what's releasable, asks which to ship, pins prod.json, and pushes.
# The push (as you) triggers promote.yml, which deploys the selected services.
set -euo pipefail
cd "$(dirname "$0")/.."

git pull -q origin main
echo
python3 scripts/release_status.py
echo
read -rp "Release which services? (comma-separated names, or 'all'): " SEL

python3 scripts/select_release.py --select "$SEL" >/dev/null

if git diff --quiet environments/prod.json; then
  echo "Nothing to release for '$SEL'."
  exit 0
fi

echo "--- prod.json changes ---"
git --no-pager diff environments/prod.json
read -rp "Push and release the above? [y/N] " OK
[[ "$OK" == "y" || "$OK" == "Y" ]] || { git checkout environments/prod.json; echo "Aborted."; exit 0; }

git add environments/prod.json
git commit -m "release: $SEL"
git push origin main
echo "✅ Pushed. promote.yml is deploying: $SEL"
