"""Stream every line move in real time via the TheRundown WebSocket.

Pro tier and above. The server pushes one message per line change.

Requires:
    - RUNDOWN_KEY env var
    - websocket-client:  pip install websocket-client
"""

import json
import os
import sys
import urllib.parse

from websocket import WebSocketApp

KEY = os.environ["RUNDOWN_KEY"]
URL = f"wss://therundown.io/api/v2/ws/markets?{urllib.parse.urlencode({'key': KEY})}"


def on_message(_ws: WebSocketApp, raw: str) -> None:
    msg = json.loads(raw)
    # Each push carries: event_id, affiliate_id, market_id, prices (before/after)
    event_id = msg.get("event_id", "?")
    book = msg.get("affiliate_id", "?")
    market = msg.get("market_id", "?")
    prices = msg.get("prices", {})
    print(f"event {event_id}  book {book}  market {market}  -> {prices}")


def on_error(_ws: WebSocketApp, err: Exception) -> None:
    print(f"error: {err}", file=sys.stderr)


def on_close(_ws: WebSocketApp, code: int, msg: str) -> None:
    print(f"closed: {code} {msg}")


def on_open(_ws: WebSocketApp) -> None:
    print("connected, streaming line moves...")


if __name__ == "__main__":
    WebSocketApp(
        URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    ).run_forever()
