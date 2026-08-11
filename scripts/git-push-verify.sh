#!/usr/bin/env bash
set -euo pipefail
repo="${1:-.}"
cd "$repo"
git rev-parse --is-inside-work-tree >/dev/null
[ -z "$(git status --short)" ]
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}')
[ "$(git rev-parse HEAD)" = "$(git rev-parse "$upstream")" ]
echo "Git push verification PASS: HEAD matches $upstream and tree is clean"
