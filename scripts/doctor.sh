#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v python3 >/dev/null || { echo "error: python3 is unavailable" >&2; exit 1; }
python3 "$repo_dir/scripts/validate_records.py" --help >/dev/null
python3 "$repo_dir/scripts/build_agent_db.py" --help >/dev/null
test -f "$repo_dir/SKILL.md"
test -f "$repo_dir/references/data-contract.md"
test -f "$repo_dir/references/feishu-publish.md"
printf '%s\n' "ok: local runtime and references are available; no data was read"
