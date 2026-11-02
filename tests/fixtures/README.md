# V2 contract fixture

`v2-event.json` is a projection of an authenticated Product event response captured October29,2026: one November1 NFL moneyline event, DraftKings19 and FanDuel23, four open price objects. Only public event/team/market/participant/line/price fields are retained. Source IDs, deep links and other metadata were removed.

The fixture checks the V2 nesting and per-participant/book identity. It is not a current-price, coverage, latency or Free-entitlement measurement. Tests create separately controlled closed, reopened, sentinel and invalid/error variants; those are not represented as captured book removal payloads.
