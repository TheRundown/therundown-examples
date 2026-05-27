/**
 * Build a side-by-side moneyline comparison across sportsbooks.
 *
 * Demonstrates that every sportsbook returns lines in the same shape,
 * so one Object.entries() walk renders a comparison view.
 *
 * Requires: RUNDOWN_KEY env var. Node 18+.
 */

const BASE = 'https://therundown.io/api/v2';
const KEY = process.env.RUNDOWN_KEY;
const NBA = 4;

async function fetchJson(path, params) {
  const url = new URL(`${BASE}${path}`);
  url.searchParams.set('key', KEY);
  for (const [k, v] of Object.entries(params ?? {})) {
    url.searchParams.set(k, v);
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} on ${path}`);
  return res.json();
}

async function main() {
  const books = Object.fromEntries(
    (await fetchJson('/affiliates')).affiliates.map((a) => [
      String(a.affiliate_id),
      a.name,
    ]),
  );
  const today = new Date().toISOString().slice(0, 10);
  const { events = [] } = await fetchJson(`/sports/${NBA}/events/${today}`, {
    market_ids: '1',
    main_line: 'true',
  });

  for (const ev of events) {
    const home = ev.teams.find((t) => t.is_home)?.name ?? '?';
    const away = ev.teams.find((t) => !t.is_home)?.name ?? '?';
    console.log(`\n=== ${away} @ ${home} ===`);
    console.log('Book                  Home     Away');
    console.log('--------------------------------------');
    for (const [affId, markets] of Object.entries(ev.lines ?? {})) {
      const ml = markets.moneyline ?? {};
      const name = (books[affId] ?? affId).padEnd(20);
      const home = String(ml.home ?? '-').padStart(8);
      const away = String(ml.away ?? '-').padStart(8);
      console.log(`${name} ${home} ${away}`);
    }
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
