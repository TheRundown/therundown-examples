# TheRundown — code examples

Official runnable examples for the [TheRundown sports data API](https://therundown.io/) in Python, Node.js, Go, and cURL.

[Get a free API key in 30 seconds](https://therundown.io/docs/quickstart) — no credit card. 20,000 data points/day on the free tier.

```
GET https://therundown.io/api/v2/sports/{sport_id}/events/{YYYY-MM-DD}
    ?key={YOUR_KEY}
    &affiliate_ids=3,19,23
    &market_ids=1,2,3
```

## What's in here

| Directory | Examples |
|---|---|
| [`python/`](./python) | `fetch_events.py`, `parse_lines.py`, `websocket_stream.py` |
| [`node/`](./node) | `fetch-events.js`, `parse-lines.js`, `websocket-stream.js` |
| [`go/`](./go) | `fetch_events.go`, `websocket_stream.go` |
| [`curl/`](./curl) | `fetch-events.sh`, `delta.sh`, `historical.sh` |

Every example reads the key from the `RUNDOWN_KEY` environment variable.

```bash
export RUNDOWN_KEY=trk_your_key_here
```

## What the API returns

```json
{
  "meta": { "delta_last_id": "abc123…" },
  "events": [
    {
      "event_id": "…",
      "sport_id": 4,
      "event_date": "2026-05-26T19:00:00Z",
      "teams": [
        { "name": "Lakers", "is_home": true },
        { "name": "Celtics", "is_home": false }
      ],
      "lines": {
        "3":  { "moneyline": { "home": -145, "away": +125 } },
        "19": { "moneyline": { "home": -148, "away": +132 } },
        "23": { "moneyline": { "home": -141, "away": +128 } }
      }
    }
  ]
}
```

Numeric keys under `lines` are affiliate (sportsbook) IDs. Look them up via `GET /api/v2/affiliates`.

## Coverage

- **30+ leagues**: NFL, NBA, MLB, NHL, NCAAF, NCAAB, EPL, MLS, Bundesliga, La Liga, UCL, Serie A, Ligue 1, ATP tennis, WTA tennis, UFC, F1, NASCAR, PGA, NRL, AFL, CFL
- **16+ sportsbooks**: DraftKings, FanDuel, BetMGM, Pinnacle, Caesars, theScore Bet, LowVig, Matchbook, Bovada, Bodog, BetOnline, Sportsbetting.ag, Intertops, YouWager, Unibet
- **Prediction markets**: Kalshi, Polymarket — same schema as sportsbook lines

## Why TheRundown

- **Public pricing.** Free / Starter $49 / Pro $149 / Ultra $399 / Enterprise.
- **Self-serve.** API key in 30 seconds. No sales call. No credit card on free.
- **One schema for everything.** Sportsbooks + prediction markets returned side-by-side.
- **Sub-second updates** over REST + WebSocket push.
- **Independent.** Not owned by an affiliate. Not owned by Sportradar.

## Links

- [Quickstart](https://therundown.io/docs/quickstart)
- [Full API reference](https://docs.therundown.io/)
- [OpenAPI 3 spec](https://docs.therundown.io/openapi.yaml)
- [Pricing](https://therundown.io/pricing/api)
- [Compare to OddsJam](https://therundown.io/compare/oddsjam) · [OpticOdds](https://therundown.io/compare/opticodds) · [DonBest](https://therundown.io/compare/donbest)

## License

MIT — see [LICENSE](./LICENSE). Use these snippets in your projects freely.
