"""Log bounded market price changes from TheRundown's WebSocket.

Ultra tier and above. This is a finite-scope raw change logger, not a complete
board or reconnecting state client.

Requires RUNDOWN_KEY and websocket-client (pip install websocket-client).
"""

import json
import os
import sys


URL = (
    "wss://therundown.io/api/v2/ws/markets"
    "?sport_ids=4&affiliate_ids=19%2C22%2C23&market_ids=1%2C2%2C3&main_line=true"
)


def format_message(raw: str) -> str | None:
    """Return a readable line for market price messages; ignore other frames."""
    msg = json.loads(raw)
    if not isinstance(msg, dict):
        return None
    meta = msg.get("meta")
    if not isinstance(meta, dict) or meta.get("type") != "market_price":
        return None
    data = msg.get("data")
    if not isinstance(data, dict):
        return None
    return (
        f"event {data.get('event_id', '?')}  book {data.get('affiliate_id', '?')}  "
        f"market {data.get('market_id', '?')}  participant "
        f"{data.get('normalized_market_participant_id', '?')}  "
        f"line {data.get('line', '?')}  {data.get('previous_price', '?')} "
        f"-> {data.get('price', '?')}"
    )


def main() -> None:
    key = os.environ.get("RUNDOWN_KEY")
    if not key:
        print("RUNDOWN_KEY env var is required.", file=sys.stderr)
        raise SystemExit(1)

    from websocket import WebSocketApp

    def on_message(_ws, raw: str) -> None:
        try:
            line = format_message(raw)
        except (json.JSONDecodeError, AttributeError) as err:
            print(f"message error: {err}", file=sys.stderr)
            return
        if line is not None:
            print(line)

    def on_error(_ws, err: Exception) -> None:
        print(f"WebSocket error: {err}", file=sys.stderr)

    def on_close(_ws, code: int, reason: str) -> None:
        print(f"closed: {code} {reason}")

    def on_open(_ws) -> None:
        print("connected, logging market price changes...")

    WebSocketApp(
        URL,
        header={"X-TheRundown-Key": key},
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    ).run_forever()


if __name__ == "__main__":
    main()
