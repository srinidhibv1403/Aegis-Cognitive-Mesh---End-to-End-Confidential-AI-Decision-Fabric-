#!/usr/bin/env bash
set -euo pipefail
QUESTION="${1:-}"
MODE="${ASSIST_MODE:-local}"  # local | cloud (default: local)

if [[ -z "$QUESTION" ]]; then
  echo "Usage: ASSIST_MODE=local ./scripts/assist.sh \"<question>\"" >&2
  exit 1
fi

if [[ "$MODE" == "local" ]]; then
  ./scripts/local_assistant.py "$QUESTION"
else
  echo "{\"error\":\"cloud mode is disabled by default; set up private endpoint + approved config to enable later.\"}"
fi
