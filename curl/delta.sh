#!/usr/bin/env bash
#
# Pull incremental changes since a checkpoint id.
# Use this in polling loops instead of repeatedly hitting the full
# /events endpoint — it's far cheaper on your data-point budget.
#
# Requires: RUNDOWN_KEY env var. Optional: jq.

set -euo pipefail

if [[ -z "${RUNDOWN_KEY:-}" ]]; then
  echo "RUNDOWN_KEY env var is required." >&2
  exit 1
fi

LAST_ID="${1:-}"
if [[ -z "$LAST_ID" ]]; then
  echo "Usage: $0 <last_delta_id> [sport_id]"
  echo "Get a starting last_id from the meta.delta_last_id field on any /events response."
  exit 1
fi

SPORT_ID="${2:-4}"   # default NBA

curl -sS \
  "https://therundown.io/api/v2/delta?key=${RUNDOWN_KEY}&last_id=${LAST_ID}&sport_id=${SPORT_ID}" \
  | (jq . 2>/dev/null || cat)
