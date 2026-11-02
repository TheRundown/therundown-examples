// Helpers for these sequential examples, scoped to the three Free books.
const API = 'https://therundown.io/api/v2';
const BOOKS = { 19: 'DraftKings', 22: 'BetMGM', 23: 'FanDuel' };

function createClient({
  key = process.env.RUNDOWN_KEY,
  fetchImpl = fetch,
  sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
  clock = Date.now,
} = {}) {
  if (!key)
    throw new Error(
      'Set RUNDOWN_KEY; see https://therundown.io/docs/quickstart',
    );
  let lastRequest = null;
  return async function get(path, params = {}) {
    if (lastRequest !== null)
      await sleep(Math.max(0, 1100 - (clock() - lastRequest)));
    const url = new URL(API + path);
    for (const [name, value] of Object.entries(params))
      url.searchParams.set(name, value);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetchImpl(url, {
        headers: { 'X-TheRundown-Key': key },
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status} on ${path}`);
      return await response.json();
    } finally {
      clearTimeout(timeout);
      lastRequest = clock();
    }
  };
}

function* moneylines(event) {
  for (const market of event.markets ?? []) {
    if (![1, 41].includes(market.market_id)) continue;
    for (const participant of market.participants ?? []) {
      for (const line of participant.lines ?? []) {
        for (const [book, quote] of Object.entries(line.prices ?? {})) {
          if (!Object.hasOwn(BOOKS, book) || quote.closed_at) continue;
          if (
            quote.price == null ||
            typeof quote.price === 'boolean' ||
            quote.price === ''
          )
            continue;
          const price = Number(quote.price);
          if (!Number.isFinite(price) || price === 0 || price === 0.0001)
            continue;
          yield {
            event_id: event.event_id,
            market_id: market.market_id,
            period_id: market.period_id ?? 0,
            participant_id: participant.id,
            participant_type: participant.type,
            participant: participant.name ?? '?',
            line: line.value,
            book,
            price,
          };
        }
      }
    }
  }
}
module.exports = { BOOKS, createClient, moneylines };
