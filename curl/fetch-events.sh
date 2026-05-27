#!/usr/bin/env bash
#
# Fetch today's NBA events and print the JSON.
# Requires: RUNDOWN_KEY env var. Optional: jq for pretty-printing.

set -euo pipefail

if [[ -z "${RUNDOWN_KEY:-}" ]]; then
  echo "RUNDOWN_KEY env var is required." >&2
  echo "Get one at https://therundown.io/docs/quickstart" >&2
  exit 1
fi

BASE="https://therundown.io/api/v2"
NBA_SPORT_ID=4
TODAY="$(date -u +%Y-%m-%d)"

curl -sS \
  "${BASE}/sports/${NBA_SPORT_ID}/events/${TODAY}?key=${RUNDOWN_KEY}&affiliate_ids=3,19,23&market_ids=1,2,3&main_line=true" \
  | (jq . 2>/dev/null || cat)
