#!/usr/bin/env bash
# Fetch a dated event snapshot as raw JSON. This is latest recorded state for
# the date, not a reconstruction of odds at a specific time.
# Requires RUNDOWN_KEY. See https://therundown.io/pricing/api for plan details.
set -euo pipefail

if [[ -z "${RUNDOWN_KEY:-}" ]]; then
  echo "RUNDOWN_KEY env var is required." >&2
  exit 1
fi

DATE="${1:-}"
SPORT_ID="${2:-4}" # NBA
if [[ ! "$DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || ! date -u -d "$DATE" +%F >/dev/null 2>&1 || [[ "$(date -u -d "$DATE" +%F)" != "$DATE" ]]; then
  echo "Usage: $0 <YYYY-MM-DD> [sport_id]" >&2
  echo "Example: $0 2026-02-12 4" >&2
  exit 1
fi
if [[ ! "$SPORT_ID" =~ ^[1-9][0-9]*$ ]]; then
  echo "sport_id must be a positive integer." >&2
  exit 1
fi

curl -fSs --connect-timeout 10 --max-time 30 --config - <<EOF
url = "https://therundown.io/api/v2/sports/${SPORT_ID}/events/${DATE}?affiliate_ids=19,22,23&market_ids=1,2,3&main_line=true&hide_closed=false"
header = "X-TheRundown-Key: ${RUNDOWN_KEY}"
EOF
