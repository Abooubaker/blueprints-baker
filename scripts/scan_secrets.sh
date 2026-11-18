#!/usr/bin/env bash
# Fail if tracked files or a built frontend bundle contain credential-shaped text.
#
# This is a fast guard, not a replacement for GitHub secret scanning. It is
# intentionally limited to high-confidence provider prefixes and private-key
# headers so it does not flag documentation about API-key handling.
set -euo pipefail

cd "$(dirname "$0")/.."

patterns=(
  'sk-[A-Za-z0-9_-]{24,}'
  'sk-ant-api03-[A-Za-z0-9_-]{20,}'
  'ghp_[A-Za-z0-9]{30,}'
  'github_pat_[A-Za-z0-9_]{30,}'
  'gho_[A-Za-z0-9]{30,}'
  'AKIA[0-9A-Z]{16}'
  'AIza[0-9A-Za-z_-]{35}'
  'xox[baprs]-[A-Za-z0-9-]{10,}'
  '-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----'
)

status=0
for pattern in "${patterns[@]}"; do
  if matches=$(git grep -I -n -E -- "$pattern" -- . 2>/dev/null); then
    echo "Potential secret matched /$pattern/:" >&2
    echo "$matches" >&2
    status=1
  fi
done

# Database URLs only matter when they point at a non-loopback host. The dev
# compose credentials (blueprints-baker:blueprints-baker@localhost) are intentionally public.
db_pattern='postgresql(\+asyncpg)?://[^[:space:]]+:[^[:space:]@]+@'
if matches=$(git grep -I -n -E -- "$db_pattern" -- . 2>/dev/null \
  | grep -vE '@(localhost|127\.0\.0\.1|db|postgres)([:/]|$)'); then
  echo "Potential secret matched /$db_pattern/:" >&2
  echo "$matches" >&2
  status=1
fi

# A committed .env file is a policy violation even if the values look harmless.
tracked_env=$(git ls-files | grep -E '(^|/)\.env($|\.)' | grep -vE '\.env\.example$' || true)
if [[ -n "$tracked_env" ]]; then
  echo "Environment files must not be committed:" >&2
  echo "$tracked_env" >&2
  status=1
fi

# Scan the static export too, when it exists, because Pages artifacts are public.
if [[ -d apps/web/out ]]; then
  for pattern in "${patterns[@]}"; do
    if matches=$(grep -rI -n -E -- "$pattern" apps/web/out 2>/dev/null); then
      echo "Potential secret matched /$pattern/ in apps/web/out:" >&2
      echo "$matches" >&2
      status=1
    fi
  done
fi

if [[ "$status" -eq 0 ]]; then
  echo "No credential-shaped strings found in tracked files or build output."
fi
exit "$status"
