"""Compare returned open moneylines from three sportsbooks, one row per quote.

Run: python parse_lines.py. Requires RUNDOWN_KEY and requests.
The helper spaces the catalog and event calls for Free's burst limit.
"""
from datetime import datetime, timezone

from v2 import BOOKS, Client, moneylines


def main():
    client = Client()
    catalog = client.get("/affiliates")
    books = {str(book["affiliate_id"]): book.get("affiliate_name") or book.get("name") or str(book["affiliate_id"])
             for book in catalog.get("affiliates") or []}
    today = datetime.now(timezone.utc).date().isoformat()
    body = client.get(f"/sports/4/events/{today}", {
        "affiliate_ids": ",".join(BOOKS), "market_ids": "1",
        "main_line": "true", "hide_closed": "true",
    })
    for event in body.get("events") or []:
        print(f"\n=== {event['event_id']} ({event['event_date']}) ===")
        print(f"{'Book':<20} {'Selection':<30} {'Market/period':<14} {'Price':>8}")
        for row in moneylines(event):
            print(f"{books.get(row['book'], row['book']):<20} "
                  f"{row['participant']:<30} "
                  f"{str(row['market_id']) + '/' + str(row['period_id']):<14} "
                  f"{row['price']:>+8g}")


if __name__ == "__main__":
    main()
