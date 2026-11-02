/**
 * Log bounded market price changes from TheRundown's WebSocket.
 * Ultra tier and above. This is a finite-scope raw change logger, not a
 * complete board or reconnecting state client.
 *
 * Requires RUNDOWN_KEY and `npm install ws` to run.
 */

const URL =
  'wss://therundown.io/api/v2/ws/markets' +
  '?sport_ids=4&affiliate_ids=19%2C22%2C23&market_ids=1%2C2%2C3&main_line=true';

function formatMessage(raw) {
  const msg =
    typeof raw === 'string' ? JSON.parse(raw) : JSON.parse(raw.toString());
  if (
    !msg ||
    typeof msg !== 'object' ||
    !msg.meta ||
    msg.meta.type !== 'market_price' ||
    !msg.data ||
    typeof msg.data !== 'object'
  )
    return null;
  const data = msg.data;
  return (
    `event ${data.event_id ?? '?'}  book ${data.affiliate_id ?? '?'}  ` +
    `market ${data.market_id ?? '?'}  participant ` +
    `${data.normalized_market_participant_id ?? '?'}  line ${data.line ?? '?'}  ` +
    `${data.previous_price ?? '?'} -> ${data.price ?? '?'}`
  );
}

function main() {
  const key = process.env.RUNDOWN_KEY;
  if (!key) {
    console.error('RUNDOWN_KEY env var is required.');
    process.exitCode = 1;
    return;
  }

  let WebSocket;
  try {
    WebSocket = require('ws');
  } catch (err) {
    console.error(
      'WebSocket dependency missing; install it with npm install ws.',
    );
    process.exitCode = 1;
    return;
  }

  const ws = new WebSocket(URL, { headers: { 'X-TheRundown-Key': key } });
  ws.on('open', () =>
    console.log('connected, logging market price changes...'),
  );
  ws.on('message', (raw) => {
    try {
      const line = formatMessage(raw);
      if (line !== null) console.log(line);
    } catch (err) {
      console.error('message error:', err.message);
    }
  });
  ws.on('error', (err) => console.error('WebSocket error:', err.message));
  ws.on('close', (code, reason) =>
    console.log(`closed: ${code} ${reason.toString()}`),
  );
}

module.exports = { formatMessage };

if (require.main === module) main();
