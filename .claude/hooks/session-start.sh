#!/bin/bash
# CIPHER — SessionStart hook for Claude Code on the web.
# Installs the project (with dev tools) so tests and linters are ready.
set -euo pipefail

# Only run in the remote (web) environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# Editable install with dev dependencies (pytest, ruff). Idempotent.
python -m pip install --upgrade pip >/dev/null
python -m pip install -e ".[dev]"
