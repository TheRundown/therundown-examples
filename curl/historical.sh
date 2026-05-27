#!/usr/bin/env bash
#
# Fetch events for a past date. Pro tier and above for reconstruction-
# grade historical odds (every price change/close/reopen timestamped).
#
# Requires: RUNDOWN_KEY env var. Optional: jq.

set -euo pipefail

if [[ -z "${RUNDOWN_KEY:-}" ]]; then
  echo "RUNDOWN_KEY env var is required." >&2
  exit 1
fi

DATE="${1:-}"
SPORT_ID="${2:-4}"   # default NBA

if [[ -z "$DATE" ]]; then
  echo "Usage: $0 <YYYY-MM-DD> [sport_id]"
  echo "Example: $0 2026-02-12 4   # NBA, Feb 12 2026"
  exit 1
fi

curl -sS \
  "https://therundown.io/api/v2/sports/${SPORT_ID}/events/${DATE}?key=${RUNDOWN_KEY}&main_line=true" \
  | (jq . 2>/dev/null || cat)
