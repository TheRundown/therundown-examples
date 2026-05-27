"""Build a side-by-side moneyline comparison table across sportsbooks.

Demonstrates the unified schema — every sportsbook returns lines in the
same shape, so a single dict-walk renders a comparison view.

Requires:
    - RUNDOWN_KEY env var
    - requests:  pip install requests
"""

import datetime as dt
import os

import requests

BASE = "https://therundown.io/api/v2"
KEY = os.environ["RUNDOWN_KEY"]
NBA = 4


def affiliate_lookup() -> dict[str, str]:
    """Map affiliate IDs → human names. Cache this in your app."""
    r = requests.get(f"{BASE}/affiliates", params={"key": KEY}, timeout=10)
    r.raise_for_status()
    return {str(a["affiliate_id"]): a["name"] for a in r.json()["affiliates"]}


def main() -> None:
    books = affiliate_lookup()
    today = dt.date.today().isoformat()
    r = requests.get(
        f"{BASE}/sports/{NBA}/events/{today}",
        params={"key": KEY, "market_ids": "1", "main_line": "true"},
        timeout=10,
    )
    r.raise_for_status()
    events = r.json().get("events", [])

    for ev in events:
        teams = ev["teams"]
        home = next(t["name"] for t in teams if t.get("is_home"))
        away = next(t["name"] for t in teams if not t.get("is_home"))
        print(f"\n=== {away} @ {home} ===")
        print(f"{'Book':<20} {'Home':>8} {'Away':>8}")
        print("-" * 38)
        for aff_id, markets in ev.get("lines", {}).items():
            ml = markets.get("moneyline") or {}
            print(
                f"{books.get(aff_id, aff_id):<20} "
                f"{ml.get('home', '-'):>8} {ml.get('away', '-'):>8}"
            )


if __name__ == "__main__":
    main()
