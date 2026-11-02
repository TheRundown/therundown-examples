"""Offline contract tests for the actual example helpers and entrypoints."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
import v2
import fetch_events
import parse_lines
import websocket_stream

FIXTURE = json.loads((ROOT / 'tests/fixtures/v2-event.json').read_text())


class ExamplesTest(unittest.TestCase):
    def test_captured_nested_prices_and_exact_identity(self):
        rows = list(v2.moneylines(FIXTURE['events'][0]))
        self.assertEqual(len(rows), 4)
        self.assertEqual({r['price'] for r in rows}, {-170.0, -168.0, 142.0})
        self.assertEqual({r['participant'] for r in rows}, {'Buffalo Bills', 'Baltimore Ravens'})
        self.assertEqual(len({(r['participant_id'], r['book']) for r in rows}), 4)

    def test_closure_reopen_sentinel_and_quiet_quote_controls(self):
        event = copy.deepcopy(FIXTURE['events'][0])
        prices = event['markets'][0]['participants'][0]['lines'][0]['prices']
        prices['19']['closed_at'] = '2026-11-01T19:00:00Z'
        self.assertEqual(len(list(v2.moneylines(event))), 3)
        prices['19']['closed_at'] = ''
        prices['19']['updated_at'] = '2000-01-01T00:00:00Z'
        self.assertEqual(len(list(v2.moneylines(event))), 4)
        prices['19']['price'] = 0.0001
        self.assertEqual(len(list(v2.moneylines(event))), 3)
        prices['19']['price'] = 'NaN'
        self.assertEqual(len(list(v2.moneylines(event))), 3)

    def test_http_header_and_sequential_free_pacing(self):
        response = Mock()
        response.json.return_value = FIXTURE
        clock = [0.0]
        def sleep(seconds):
            clock[0] += seconds
        with patch.object(v2.requests, 'get', return_value=response) as get, \
             patch.object(v2.time, 'monotonic', side_effect=lambda: clock[0]), \
             patch.object(v2.time, 'sleep', side_effect=sleep):
            client = v2.Client('example-test-key')
            client.get('/affiliates')
            client.get('/sports/4/events/2026-11-02', {'market_ids': '1'})
        self.assertGreaterEqual(clock[0], 1)
        self.assertEqual(get.call_count, 2)
        for call in get.call_args_list:
            self.assertEqual(call.kwargs['headers'], {'X-TheRundown-Key': 'example-test-key'})
            self.assertNotIn('key=', call.args[0])
        self.assertEqual(response.raise_for_status.call_count, 2)

    def test_pacing_waits_after_the_previous_response(self):
        response = Mock()
        response.json.return_value = FIXTURE
        clock, starts = [0.0], []
        def get(*args, **kwargs):
            starts.append(clock[0])
            clock[0] += 0.5
            return response
        with patch.object(v2.requests, 'get', side_effect=get), \
             patch.object(v2.time, 'monotonic', side_effect=lambda: clock[0]), \
             patch.object(v2.time, 'sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)):
            client = v2.Client('example-test-key')
            client.get('/affiliates')
            client.get('/sports/4/events/2026-11-02')
        self.assertGreaterEqual(starts[1] - (starts[0] + 0.5), 1)

    def test_http_error_is_not_parsed(self):
        response = Mock()
        response.raise_for_status.side_effect = RuntimeError('HTTP401')
        with patch.object(v2.requests, 'get', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'HTTP401'):
                v2.Client('example-test-key').get('/sports/4/events/2026-11-02')
        response.json.assert_not_called()

    def test_fetch_entrypoint_prints_actual_fixture_prices(self):
        with patch.object(fetch_events, 'Client') as client, contextlib.redirect_stdout(io.StringIO()) as output:
            client.return_value.get.return_value = FIXTURE
            fetch_events.main()
        self.assertIn('Buffalo Bills', output.getvalue())
        self.assertIn('-170', output.getvalue())
        self.assertIn('+142', output.getvalue())

    def test_comparison_entrypoint_keeps_sides(self):
        with patch.object(parse_lines, 'Client') as client, contextlib.redirect_stdout(io.StringIO()) as output:
            client.return_value.get.side_effect = [{'affiliates': [{'affiliate_id': 19, 'affiliate_name': 'DraftKings'}]}, FIXTURE]
            parse_lines.main()
        self.assertIn('DraftKings', output.getvalue())
        self.assertIn('Baltimore Ravens', output.getvalue())
        self.assertIn('Buffalo Bills', output.getvalue())

    def test_websocket_upgrade_uses_header_without_connecting(self):
        transport = Mock()
        with patch.dict('sys.modules', {'websocket': transport}), \
             patch.dict('os.environ', {'RUNDOWN_KEY': 'example-test-key'}):
            websocket_stream.main()
        call = transport.WebSocketApp.call_args
        self.assertEqual(call.kwargs['header'], {'X-TheRundown-Key': 'example-test-key'})
        self.assertNotIn('key=', call.args[0])
        self.assertIn('sport_ids=4', call.args[0])
        transport.WebSocketApp.return_value.run_forever.assert_called_once()

    def test_websocket_envelope_and_heartbeat(self):
        data = {'event_id': 'fixture', 'affiliate_id': 19, 'market_id': 41,
                'normalized_market_participant_id': 61, 'line': None, 'price': '-170'}
        # Importing the formatter never opens a socket or requires a real key.
        self.assertIsNone(websocket_stream.format_message(json.dumps({'meta': {'type': 'heartbeat'}})))
        result = websocket_stream.format_message(json.dumps({'meta': {'type': 'market_price'}, 'data': data}))
        self.assertIn('fixture', result)
        self.assertIn('-170', result)


if __name__ == '__main__':
    unittest.main()
