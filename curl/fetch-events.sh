#!/usr/bin/env bash
# Fetch today's NBA main moneylines as raw JSON. Requires RUNDOWN_KEY.
set -euo pipefail

if [[ -z "${RUNDOWN_KEY:-}" ]]; then
  echo "RUNDOWN_KEY env var is required. See https://therundown.io/docs/quickstart" >&2
  exit 1
fi

TODAY="$(date -u +%Y-%m-%d)"
curl -fSs --dump-header "${SNAPSHOT_HEADERS:-/dev/null}" --connect-timeout 10 --max-time 30 --config - <<EOF
url = "https://therundown.io/api/v2/sports/4/events/${TODAY}?affiliate_ids=19,22,23&market_ids=1,41&main_line=true&hide_closed=true"
header = "X-TheRundown-Key: ${RUNDOWN_KEY}"
EOF
