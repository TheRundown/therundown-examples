"""Fetch today's NBA events and print the moneyline for each game.

Requires:
    - RUNDOWN_KEY env var (get one at https://therundown.io/docs/quickstart)
    - requests:  pip install requests
"""

import datetime as dt
import os

import requests

BASE = "https://therundown.io/api/v2"
KEY = os.environ["RUNDOWN_KEY"]

# Sport IDs come from /api/v2/sports. NBA happens to be 4.
NBA_SPORT_ID = 4

# Affiliate IDs come from /api/v2/affiliates. These are DraftKings, FanDuel,
# Pinnacle — three of the 16+ sportsbooks TheRundown covers.
AFFILIATES = "3,19,23"


def main() -> None:
    today = dt.date.today().isoformat()
    r = requests.get(
        f"{BASE}/sports/{NBA_SPORT_ID}/events/{today}",
        params={
            "key": KEY,
            "affiliate_ids": AFFILIATES,
            "market_ids": "1,2,3",  # moneyline, spread, total
            "main_line": "true",
        },
        timeout=10,
    )
    r.raise_for_status()
    events = r.json().get("events", [])

    if not events:
        print(f"No NBA events on {today}.")
        return

    for ev in events:
        teams = ev.get("teams", [])
        home = next((t["name"] for t in teams if t.get("is_home")), "?")
        away = next((t["name"] for t in teams if not t.get("is_home")), "?")
        print(f"\n{away} @ {home}  ({ev['event_date']})")

        lines = ev.get("lines", {})
        for affiliate_id, markets in lines.items():
            ml = markets.get("moneyline", {})
            if ml:
                print(
                    f"  book {affiliate_id}: "
                    f"home={ml.get('home', '?')}  away={ml.get('away', '?')}"
                )


if __name__ == "__main__":
    main()
