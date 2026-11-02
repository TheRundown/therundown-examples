/** Print today's open NBA moneylines. Requires RUNDOWN_KEY; Node18+.
 * If today is empty, choose a returned UTC schedule date. Free is delayed prematch.
 */
const { BOOKS, createClient, moneylines } = require('./v2');

async function main() {
  const today = new Date().toISOString().slice(0, 10);
  const body = await createClient()(`/sports/4/events/${today}`, {
    affiliate_ids: Object.keys(BOOKS).join(','),
    market_ids: '1',
    main_line: 'true',
    hide_closed: 'true',
  });
  if (!body.events?.length)
    console.log(
      `No NBA events returned for UTC date ${today}; check the schedule.`,
    );
  for (const event of body.events ?? []) {
    console.log(`\n${event.event_id} (${event.event_date})`);
    for (const row of moneylines(event)) {
      console.log(
        `  ${row.participant} | ${BOOKS[row.book]} | market ${row.market_id} period ${row.period_id} | ${row.price > 0 ? '+' : ''}${row.price}`,
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
