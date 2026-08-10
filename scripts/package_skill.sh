#!/usr/bin/env bash
# Rebuilds the distributable .skill package from
# plugins/gds-neo-api/skills/gds-neo-api/.
#
# Usage:
#   scripts/package_skill.sh [output-path]
#
# output-path defaults to dist/gds-neo-api.skill. If given, note that `zip`
# appends .zip to any name with no extension (e.g. `run` -> `run.zip`).
#
# Run this after any change under that skill directory, then commit the
# result. .github/workflows/package-check.yml fails CI if dist/gds-neo-api.skill
# drifts from what this script would produce.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src_dir="$repo_root/plugins/gds-neo-api/skills/gds-neo-api"

# Resolve a relative output path against the caller's cwd *before* the `cd`
# below changes it — otherwise a relative path lands next to src_dir instead.
if [ $# -ge 1 ]; then
  case "$1" in
    /*) out="$1" ;;
    *) out="$PWD/$1" ;;
  esac
else
  out="$repo_root/dist/gds-neo-api.skill"
fi

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
