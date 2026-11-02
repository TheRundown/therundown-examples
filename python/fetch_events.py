"""Print today's open NBA moneylines. Requires RUNDOWN_KEY and requests.

Run: python fetch_events.py. Use a returned UTC schedule date if today is empty.
Prices and source coverage depend on your plan; Free is delayed pre-match only.
"""
from datetime import datetime, timezone

from v2 import BOOKS, Client, moneylines


def main():
    today = datetime.now(timezone.utc).date().isoformat()
    body = Client().get(f"/sports/4/events/{today}", {
        "affiliate_ids": ",".join(BOOKS), "market_ids": "1",
        "main_line": "true", "hide_closed": "true",
    })
    events = body.get("events") or []
    if not events:
        print(f"No NBA events returned for UTC date {today}; check the schedule.")
    for event in events:
        print(f"\n{event['event_id']} ({event['event_date']})")
        for row in moneylines(event):
            print(f"  {row['participant']} | {BOOKS[row['book']]} | "
                  f"market {row['market_id']} period {row['period_id']} | {row['price']:+g}")


if __name__ == "__main__":
    main()
