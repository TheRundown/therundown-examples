const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createClient, moneylines } = require('../node/v2');
const { formatMessage } = require('../node/websocket-stream');
const fixture = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'fixtures/v2-event.json')),
);

test('captured V2 shape yields all four open quotes with side identity', () => {
  const rows = [...moneylines(fixture.events[0])];
  assert.equal(rows.length, 4);
  assert.deepEqual(
    new Set(rows.map((r) => r.price)),
    new Set([-170, -168, 142]),
  );
  assert.equal(
    new Set(rows.map((r) => r.participant_id + '/' + r.book)).size,
    4,
  );
});

test('closed, reopened, sentinel and quiet-price controls', () => {
  const event = structuredClone(fixture.events[0]);
  const prices = event.markets[0].participants[0].lines[0].prices;
  prices[19].closed_at = '2026-11-01T19:00:00Z';
  assert.equal([...moneylines(event)].length, 3);
  prices[19].closed_at = '';
  prices[19].updated_at = '2000-01-01T00:00:00Z';
  assert.equal([...moneylines(event)].length, 4);
  prices[19].price = 0.0001;
  assert.equal([...moneylines(event)].length, 3);
  prices[19].price = 'NaN';
  assert.equal([...moneylines(event)].length, 3);
});

test('HTTP helper authenticates in header and paces sequential calls', async () => {
  const calls = [];
  let clock = 0;
  const get = createClient({
    key: 'example-test-key',
    clock: () => clock,
    sleep: async (ms) => {
      clock += ms;
    },
    fetchImpl: async (url, options) => {
      calls.push({ url, options, clock });
      return { ok: true, json: async () => fixture };
    },
  });
  await get('/affiliates');
  await get('/sports/4/events/2026-11-02', { market_ids: '1' });
  assert.equal(calls.length, 2);
  assert.ok(calls[1].clock - calls[0].clock >= 1000);
  for (const call of calls) {
    assert.equal(call.options.headers['X-TheRundown-Key'], 'example-test-key');
    assert.equal(call.url.searchParams.has('key'), false);
  }
});

test('pacing waits after the previous response, including its latency', async () => {
  let clock = 0;
  const starts = [];
  const get = createClient({
    key: 'example-test-key',
    clock: () => clock,
    sleep: async (ms) => {
      clock += ms;
    },
    fetchImpl: async () => {
      starts.push(clock);
      clock += 500;
      return { ok: true, json: async () => fixture };
    },
  });
  await get('/affiliates');
  await get('/sports/4/events/2026-11-02');
  assert.ok(starts[1] - (starts[0] + 500) >= 1000);
});

test('HTTP error is surfaced before body parsing', async () => {
  let parsed = false;
  const get = createClient({
    key: 'example-test-key',
    fetchImpl: async () => ({
      ok: false,
      status: 401,
      json: async () => {
        parsed = true;
      },
    }),
  });
  await assert.rejects(get('/affiliates'), /HTTP 401/);
  assert.equal(parsed, false);
});

for (const name of ['fetch-events', 'parse-lines']) {
  test(`${name} entrypoint prints captured prices without network`, async () => {
    const originalFetch = global.fetch,
      originalLog = console.log,
      originalKey = process.env.RUNDOWN_KEY;
    const output = [];
    try {
      process.env.RUNDOWN_KEY = 'example-test-key';
      global.fetch = async (url) => ({
        ok: true,
        json: async () =>
          url.pathname.endsWith('/affiliates')
            ? {
                affiliates: [
                  { affiliate_id: 19, affiliate_name: 'DraftKings' },
                ],
              }
            : fixture,
      });
      console.log = (...args) => output.push(args.join(' '));
      await require(`../node/${name}`).main();
      assert.ok(
        output.some(
          (line) => line.includes('Buffalo Bills') && line.includes('-170'),
        ),
      );
      assert.ok(
        output.some(
          (line) => line.includes('Baltimore Ravens') && line.includes('142'),
        ),
      );
    } finally {
      global.fetch = originalFetch;
      console.log = originalLog;
      if (originalKey === undefined) delete process.env.RUNDOWN_KEY;
      else process.env.RUNDOWN_KEY = originalKey;
    }
  });
}

test('WS formatter reads the nested envelope and ignores heartbeat', () => {
  assert.equal(
    formatMessage(JSON.stringify({ meta: { type: 'heartbeat' } })),
    null,
  );
  const line = formatMessage(
    JSON.stringify({
      meta: { type: 'market_price' },
      data: {
        event_id: 'fixture',
        affiliate_id: 19,
        market_id: 41,
        normalized_market_participant_id: 61,
        price: '-170',
      },
    }),
  );
  assert.match(line, /fixture.*book 19.*market 41.*participant 61.*-170/);
});

test('WS entrypoint constructs bounded header-auth upgrade without connecting', () => {
  let captured;
  function FakeWebSocket(url, options) {
    captured = { url, options };
    this.on = () => this;
  }
  const module = { exports: {} };
  const requireFake = (name) => {
    assert.equal(name, 'ws');
    return FakeWebSocket;
  };
  requireFake.main = module;
  vm.runInNewContext(
    fs.readFileSync(
      path.join(__dirname, '../node/websocket-stream.js'),
      'utf8',
    ),
    {
      require: requireFake,
      module,
      process: { env: { RUNDOWN_KEY: 'example-test-key' } },
      console,
    },
  );
  const url = new URL(captured.url);
  assert.equal(url.searchParams.has('key'), false);
  assert.equal(url.searchParams.get('sport_ids'), '4');
  assert.equal(url.searchParams.get('affiliate_ids'), '19,22,23');
  assert.equal(
    captured.options.headers['X-TheRundown-Key'],
    'example-test-key',
  );
});
