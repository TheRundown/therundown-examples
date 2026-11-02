/** Compare returned open moneylines, one row per quote. RUNDOWN_KEY; Node18+.
 * The helper spaces catalog and event calls for Free's burst limit.
 */
const { BOOKS, createClient, moneylines } = require('./v2');

async function main() {
  const get = createClient();
  const books = Object.fromEntries(
    ((await get('/affiliates')).affiliates ?? []).map((book) => [
      String(book.affiliate_id),
      book.affiliate_name ?? book.name ?? String(book.affiliate_id),
    ]),
  );
  const today = new Date().toISOString().slice(0, 10);
  const body = await get(`/sports/4/events/${today}`, {
    affiliate_ids: Object.keys(BOOKS).join(','),
    market_ids: '1',
    main_line: 'true',
    hide_closed: 'true',
  });
  for (const event of body.events ?? []) {
    console.log(`\n=== ${event.event_id} (${event.event_date}) ===`);
    console.log(
      'Book                 Selection                      Market/period     Price',
    );
    for (const row of moneylines(event)) {
      console.log(
        `${(books[row.book] ?? row.book).padEnd(20)} ${row.participant.padEnd(30)} ${(row.market_id + '/' + row.period_id).padEnd(14)} ${String(row.price).padStart(8)}`,
      );
    }
  }
}
if (require.main === module)
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
module.exports = { main };
