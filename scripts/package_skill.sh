#!/usr/bin/env bash
# Rebuilds the distributable .skill package from
# plugins/gds-neo-api/skills/gds-neo-api/.
#
# Usage:
#   scripts/package_skill.sh [output-path]
#
# Run this after any change under that skill directory, then commit the
# result. .github/workflows/package-check.yml fails CI if dist/gds-neo-api.skill
# drifts from what this script would produce.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src_dir="$repo_root/plugins/gds-neo-api/skills/gds-neo-api"
out="${1:-$repo_root/dist/gds-neo-api.skill}"

rm -f "$out"
mkdir -p "$(dirname "$out")"

# -D: no directory entries. -X: no extra file attributes (uid/gid etc).
# Neither affects file content, only keeps the archive listing clean and stable.
(
  cd "$src_dir/.."
  zip -r -X -D "$out" "$(basename "$src_dir")" \
    -x '*.DS_Store' -x '*__pycache__*' -x '*.pyc'
)

echo "Wrote $out"
