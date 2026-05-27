/**
 * Fetch today's NBA events and print the moneyline for each game.
 *
 * Requires:
 *   - RUNDOWN_KEY env var
 *   - Node 18+ (uses the built-in `fetch`)
 */

const BASE = 'https://therundown.io/api/v2';
const KEY = process.env.RUNDOWN_KEY;
if (!KEY) {
  console.error('RUNDOWN_KEY env var is required. Get one at https://therundown.io/docs/quickstart');
  process.exit(1);
}

// Sport IDs come from /api/v2/sports. NBA is 4.
const NBA = 4;
// Affiliate IDs come from /api/v2/affiliates.
const AFFILIATES = '3,19,23';

async function main() {
  const today = new Date().toISOString().slice(0, 10);
  const url = new URL(`${BASE}/sports/${NBA}/events/${today}`);
  url.searchParams.set('key', KEY);
  url.searchParams.set('affiliate_ids', AFFILIATES);
  url.searchParams.set('market_ids', '1,2,3');
  url.searchParams.set('main_line', 'true');

  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  }
  const { events = [] } = await res.json();

  if (events.length === 0) {
    console.log(`No NBA events on ${today}.`);
    return;
  }

  for (const ev of events) {
    const home = ev.teams.find((t) => t.is_home)?.name ?? '?';
    const away = ev.teams.find((t) => !t.is_home)?.name ?? '?';
    console.log(`\n${away} @ ${home}  (${ev.event_date})`);

    for (const [affiliateId, markets] of Object.entries(ev.lines ?? {})) {
      const ml = markets.moneyline;
      if (ml) {
        console.log(`  book ${affiliateId}: home=${ml.home ?? '?'}  away=${ml.away ?? '?'}`);
      }
    }
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
