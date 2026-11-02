"""Small helpers for the sequential, three-book examples in this directory."""
import math
import os
import time

import requests

API = "https://therundown.io/api/v2"
BOOKS = {"19": "DraftKings", "22": "BetMGM", "23": "FanDuel"}


class Client:
    def __init__(self, key=None):
        self.key = key or os.environ.get("RUNDOWN_KEY")
        if not self.key:
            raise ValueError("Set RUNDOWN_KEY; see https://therundown.io/docs/quickstart")
        self.last_request = None

    def get(self, path, params=None):
        # These examples issue calls sequentially. Free permits 1 req/sec.
        if self.last_request is not None:
            time.sleep(max(0, 1.1 - (time.monotonic() - self.last_request)))
        try:
            response = requests.get(
                API + path, params=params,
                headers={"X-TheRundown-Key": self.key}, timeout=15,
            )
            response.raise_for_status()
            return response.json()
        finally:
            self.last_request = time.monotonic()


def moneylines(event):
    """Yield open prices with their exact returned market/participant identity."""
    for market in event.get("markets") or []:
        if market.get("market_id") not in (1, 41):
            continue
        for participant in market.get("participants") or []:
            for line in participant.get("lines") or []:
                for book, quote in (line.get("prices") or {}).items():
                    if book not in BOOKS or quote.get("closed_at"):
                        continue
                    raw = quote.get("price")
                    if raw is None or isinstance(raw, bool):
                        continue
                    try:
                        price = float(raw)
                    except (TypeError, ValueError):
                        continue
                    if not math.isfinite(price) or price in (0, 0.0001):
                        continue
                    yield {"event_id": event.get("event_id"),
                           "market_id": market["market_id"],
                           "period_id": market.get("period_id", 0),
                           "participant_id": participant.get("id"),
                           "participant_type": participant.get("type"),
                           "participant": participant.get("name", "?"),
                           "line": line.get("value"), "book": book, "price": price}
