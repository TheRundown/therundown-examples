# TheRundown — code examples

Examples for the [TheRundown sports odds and data API](https://therundown.io/api) in Python, Node.js, Go, and cURL.

[Get started](https://therundown.io/docs/quickstart). The free plan includes 20,000 points/day and 200,000/month, with no credit card required.

```
GET https://therundown.io/api/v2/sports/{sport_id}/events/{YYYY-MM-DD}
    ?affiliate_ids=19,22,23
    &market_ids=1,2,3
    &main_line=true
    &hide_closed=true
X-TheRundown-Key: {YOUR_KEY}
```

Use a UTC calendar date for `{YYYY-MM-DD}`. This bounded request selects three books and three markets and asks for main lines with closed prices hidden. Authenticate with the `X-TheRundown-Key` header; the examples read the value from `RUNDOWN_KEY`.

## What's in here

| Directory             | Examples                                                   |
| --------------------- | ---------------------------------------------------------- |
| [`python/`](./python) | `fetch_events.py`, `parse_lines.py`, `websocket_stream.py` |
| [`node/`](./node)     | `fetch-events.js`, `parse-lines.js`, `websocket-stream.js` |
| [`go/`](./go)         | `fetch_events.go`, `websocket_stream.go`                   |
| [`curl/`](./curl)     | `fetch-events.sh`, `delta.sh`, `historical.sh`             |

Every example reads the key from the `RUNDOWN_KEY` environment variable.

```bash
export RUNDOWN_KEY='<your API key>'
```

## Run an example

Python requires Python 3.10+ and the packages in `python/requirements.txt`; run a script from that directory. Node requires Node18+; install `node/` dependencies to run its WebSocket logger. The Go files are separate programs: use `go run fetch_events.go` or `go run websocket_stream.go` from `go/`. Do not run both mains as one package. Shell examples require Bash and curl; the dated script also uses GNU `date`.

The runnable REST examples focus on moneylines and request only the three Free books. The introductory request above also shows spread and total filters. The price printers skip nonempty `closed_at` and the `0.0001` off-board sentinel, accept an empty closure timestamp as open, and do not infer availability from `updated_at`. Ultra allows one concurrent connection per account, so run one logger at a time on that tier. WebSocket examples are bounded change loggers; they do not build or recover a complete board. See the [streaming guide](https://docs.therundown.io/guides/websocket-streaming) for a full client design and usage costs.

## Market-delta example

`curl/delta.sh` makes one request to `/api/v2/markets/delta`. It requires a saved matching snapshot body, its response headers, and an explicitly known zero-delay entitlement. Delayed or unknown access repeats narrow snapshots instead. Do not pass the events snapshot's integer cursor to `/api/v2/delta`, which uses a different cursor type.

For known zero-delay access, bootstrap the same NBA moneyline/book scope:

```bash
SNAPSHOT_HEADERS=snapshot-headers.txt bash curl/fetch-events.sh > snapshot.json
# Set this only after confirming your plan has zero data delay.
KNOWN_ZERO_DELAY_ENTITLEMENT=1 bash curl/delta.sh snapshot.json snapshot-headers.txt 4
```

The script also requires the server's explicit `X-Data-Delay-Seconds: 0` header and a positive integer `meta.delta_last_id`; unknown, delayed or invalid inputs stop before requesting deltas. These two shell requests focus on full-game moneyline IDs `1,41` and books `19,22,23`; live rows keep ID `41`. The delta read is limited to 100 rows. It does not use an undocumented main-line filter, and this moneyline scope does not request spread/total ladders. Delta is scoped by sport, not date; callers must retain their own event membership and exact quote identity. This script prints the response and does not merge it into a board. See [efficient polling](https://docs.therundown.io/guides/efficient-polling).

## What the API returns

V2 event responses nest prices under `events → markets → participants → lines → prices`, with affiliate IDs as keys in `prices`. This abbreviated example illustrates the shape; values are placeholders, not live odds.

```json
{
  "meta": { "delta_last_id": "123456789" },
  "events": [
    {
      "event_id": "…",
      "sport_id": 4,
      "event_date": "…",
      "teams": [{ "name": "Away" }, { "name": "Home" }],
      "markets": [
        {
          "market_id": 1,
          "period_id": 0,
          "participants": [
            {
              "name": "Home",
              "lines": [
                {
                  "prices": { "19": { "price": -110 }, "22": { "price": -105 } }
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

Numeric keys in each line's `prices` map are affiliate (book) IDs. Look them up via `GET /api/v2/affiliates`. The dated shell example retains closed prices, which carry their actual `closed_at` signal. Dated event snapshots contain the latest recorded prices for that date; they do not reconstruct prices as they stood at a particular time.

## Coverage

Discover IDs with `GET /api/v2/sports`, `GET /api/v2/affiliates`, and `GET /api/v2/markets`. See the [quickstart](https://therundown.io/docs/quickstart) for scoped requests. Availability varies by source, sport, market, and plan.

## Why TheRundown

- **Plans for different needs.** Free includes five-minute-delayed prematch full-game main lines from DraftKings, FanDuel, and BetMGM, at 1 request/second. Starter is $49/month with 60-second-delayed REST; Pro is $149/month with 30-second-delayed REST; Ultra is $399/month with real-time REST and WebSocket access. See [current pricing](https://therundown.io/pricing/api) for details.
- **One schema for everything.** Books and markets use the same structured response format.

## Links

- [Quickstart](https://therundown.io/docs/quickstart)
- [Full API reference](https://docs.therundown.io/)
- [OpenAPI 3 spec](https://docs.therundown.io/openapi.yaml)
- [Pricing](https://therundown.io/pricing/api)
- [Compare to OddsJam](https://therundown.io/compare/oddsjam) · [OpticOdds](https://therundown.io/compare/opticodds) · [DonBest](https://therundown.io/compare/donbest)

## Offline checks

No real API key or network request is needed for the contract tests:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py'
node --test tests/node.test.js
(cd go && go test fetch_events.go fetch_events_test.go)
(cd go && go test websocket_stream.go websocket_stream_test.go)
```

The checked-in event fixture is a projection of an Oct29 Product response; tests add explicitly controlled closure/reopen/error cases. WS tests use recorded protocol shapes and fake transports, and do not establish live delivery or account entitlements.

## License

MIT — see [LICENSE](./LICENSE). Use these snippets in your projects freely.
