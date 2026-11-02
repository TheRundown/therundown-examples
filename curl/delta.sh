#!/usr/bin/env bash
# One bounded market-delta read from a saved matching events bootstrap.
# Requires known zero-delay entitlement, explicit server delay0, python3 and curl.
# Free/delayed/unknown access must repeat narrow snapshots instead.
# See https://docs.therundown.io/guides/efficient-polling
set -euo pipefail

if [[ -z "${RUNDOWN_KEY:-}" ]]; then
  echo 'RUNDOWN_KEY env var is required.' >&2
  exit 1
fi
if [[ "${KNOWN_ZERO_DELAY_ENTITLEMENT:-}" != 1 ]]; then
  echo 'Stop: delta requires a known zero-delay entitlement. Use narrow snapshots on delayed or unknown access.' >&2
  exit 1
fi
SNAPSHOT="${1:-}"
HEADERS="${2:-}"
SPORT_ID="${3:-4}"
if [[ ! -f "$SNAPSHOT" || ! -f "$HEADERS" || ! "$SPORT_ID" =~ ^[1-9][0-9]*$ ]]; then
  echo "Usage: $0 <snapshot.json> <snapshot-headers.txt> [sport_id]" >&2
  echo 'Save a fresh matching bootstrap: market_ids=1,41&affiliate_ids=19,22,23&main_line=true.' >&2
  exit 1
fi
CURSOR=$(python3 - "$SNAPSHOT" "$HEADERS" <<'PY'
import json, re, sys
from pathlib import Path
try:
    body = json.loads(Path(sys.argv[1]).read_text())
    headers = Path(sys.argv[2]).read_text().splitlines()
except (OSError, ValueError):
    raise SystemExit('Unable to read the saved bootstrap.')
delays = [line.split(':', 1)[1].strip() for line in headers
          if ':' in line and line.split(':', 1)[0].lower() == 'x-data-delay-seconds']
if not delays or any(delay != '0' for delay in delays):
    raise SystemExit('Stop: the bootstrap must explicitly report X-Data-Delay-Seconds: 0.')
if not isinstance(body, dict) or not isinstance(body.get('meta'), dict):
    raise SystemExit('Stop: no bootstrap metadata object.')
cursor = body['meta'].get('delta_last_id')
if isinstance(cursor, bool) or not (
    isinstance(cursor, int) or isinstance(cursor, str) and re.fullmatch('[0-9]+', cursor)
):
    raise SystemExit('Stop: no valid positive integer bootstrap cursor; never substitute 0.')
try:
    value = int(cursor)
except ValueError:
    raise SystemExit('Stop: invalid bootstrap cursor.')
if value <= 0:
    raise SystemExit('Stop: bootstrap cursor must be positive.')
print(value)
PY
)
curl -fSs --connect-timeout 10 --max-time 30 --config - <<EOF
url = "https://therundown.io/api/v2/markets/delta?last_id=${CURSOR}&sport_id=${SPORT_ID}&market_ids=1,41&affiliate_ids=19,22,23&limit=100"
header = "X-TheRundown-Key: ${RUNDOWN_KEY}"
EOF
