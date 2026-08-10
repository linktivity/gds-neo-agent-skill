#!/usr/bin/env bash
# Rebuilds distributable .skill packages, one per skill directory under
# plugins/gds-neo-api/skills/, into dist/<skill-name>.skill.
#
# Usage:
#   scripts/package_skill.sh                     # package every skill
#   scripts/package_skill.sh <skill-name>...     # package only the named skill(s)
#   scripts/package_skill.sh --out-dir DIR [...] # write elsewhere instead of dist/
#
# Run this after any change under plugins/gds-neo-api/skills/, then commit the
# result. .github/workflows/package-check.yml fails CI if a dist/*.skill package
# drifts from what this script would produce.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skills_root="$repo_root/plugins/gds-neo-api/skills"
out_dir="$repo_root/dist"

names=()
while [ $# -gt 0 ]; do
  case "$1" in
    --out-dir)
      [ $# -ge 2 ] || { echo "--out-dir requires a value" >&2; exit 1; }
      out_dir="$2"
      shift 2
      ;;
    *)
      names+=("$1")
      shift
      ;;
  esac
done

# Resolve a relative --out-dir against the caller's cwd *before* the `cd`
# below changes it — otherwise a relative path lands next to skills_root instead.
case "$out_dir" in
  /*) ;;
  *) out_dir="$PWD/$out_dir" ;;
esac

if [ ${#names[@]} -eq 0 ]; then
  for d in "$skills_root"/*/; do
    names+=("$(basename "$d")")
  done
fi

mkdir -p "$out_dir"

for name in "${names[@]}"; do
  src_dir="$skills_root/$name"
  if [ ! -d "$src_dir" ]; then
    echo "no such skill '$name' (looked in $src_dir)" >&2
    exit 1
  fi

  out="$out_dir/$name.skill"
  rm -f "$out"

  # -D: no directory entries. -X: no extra file attributes (uid/gid etc).
  # Neither affects file content, only keeps the archive listing clean and stable.
  (
    cd "$skills_root"
    zip -r -X -D "$out" "$name" \
      -x '*.DS_Store' -x '*__pycache__*' -x '*.pyc'
  )

  echo "Wrote $out"
done
