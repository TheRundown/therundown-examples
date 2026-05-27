/**
 * Stream every line move in real time via the TheRundown WebSocket.
 * Pro tier and above.
 *
 * Requires:
 *   - RUNDOWN_KEY env var
 *   - npm install ws
 */

const WebSocket = require('ws');

const KEY = process.env.RUNDOWN_KEY;
if (!KEY) {
  console.error('RUNDOWN_KEY env var is required.');
  process.exit(1);
}

const url = `wss://therundown.io/api/v2/ws/markets?key=${encodeURIComponent(KEY)}`;
const ws = new WebSocket(url);

ws.on('open', () => {
  console.log('connected, streaming line moves...');
});

ws.on('message', (raw) => {
  const msg = JSON.parse(raw.toString());
  const { event_id, affiliate_id, market_id, prices } = msg;
  console.log(
    `event ${event_id ?? '?'}  book ${affiliate_id ?? '?'}  ` +
      `market ${market_id ?? '?'}  -> ${JSON.stringify(prices ?? {})}`,
  );
});

ws.on('error', (err) => console.error('error:', err));
ws.on('close', (code, reason) => console.log(`closed: ${code} ${reason}`));
