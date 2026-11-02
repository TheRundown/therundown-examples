"""Exercise shell transport arguments and delta eligibility with a fake curl."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CurlExamplesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        fake = self.folder / 'curl'
        fake.write_text('#!/usr/bin/env python3\nimport os,sys,json\nfrom pathlib import Path\nPath(os.environ["CAPTURE"]).write_text(json.dumps({"argv":sys.argv[1:],"config":sys.stdin.read()}))\nprint("{}")\n')
        fake.chmod(0o755)
        self.env = dict(os.environ, RUNDOWN_KEY='example-test-key',
                        PATH=str(self.folder) + os.pathsep + os.environ['PATH'],
                        CAPTURE=str(self.folder / 'capture.json'))
        self.env.pop('KNOWN_ZERO_DELAY_ENTITLEMENT', None)
        self.body = self.folder / 'snapshot.json'
        self.headers = self.folder / 'headers.txt'
        self.body.write_text(json.dumps({'meta': {'delta_last_id': '123456789123456789'}}))
        self.headers.write_text('HTTP/2 200\nX-Data-Delay-Seconds: 0\n')

    def run_example(self, script, *args):
        return subprocess.run(['bash', str(ROOT / 'curl' / script), *map(str, args)],
                              env=self.env, text=True, capture_output=True, timeout=5)

    def capture(self):
        return json.loads((self.folder / 'capture.json').read_text())

    def test_fetch_uses_header_stdin_and_bounded_filters(self):
        result = self.run_example('fetch-events.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = self.capture()
        self.assertNotIn('example-test-key', ' '.join(captured['argv']))
        self.assertIn('header = "X-TheRundown-Key: example-test-key"', captured['config'])
        self.assertNotIn('key=', captured['config'])
        self.assertIn('affiliate_ids=19,22,23&market_ids=1,41', captured['config'])
        self.assertIn('-fSs', captured['argv'])

    def test_invalid_historical_inputs_never_invoke_curl(self):
        for day, sport in [('2026-02-30', '4'), ('2026-11-01', '4/../x')]:
            result = self.run_example('historical.sh', day, sport)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.folder / 'capture.json').exists())

    def test_historical_header_and_scoped_date(self):
        result = self.run_example('historical.sh', '2026-11-01', '4')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('/sports/4/events/2026-11-01?', self.capture()['config'])
        self.assertIn('hide_closed=false', self.capture()['config'])
        self.assertNotIn('key=', self.capture()['config'])

    def test_unknown_or_delayed_access_never_calls_delta(self):
        result = self.run_example('delta.sh', self.body, self.headers)
        self.assertNotEqual(result.returncode, 0)
        self.env['KNOWN_ZERO_DELAY_ENTITLEMENT'] = '1'
        for value in ['300', 'unknown', '', '300\nX-Data-Delay-Seconds: 0']:
            self.headers.write_text('X-Data-Delay-Seconds: ' + value + '\n')
            result = self.run_example('delta.sh', self.body, self.headers)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.folder / 'capture.json').exists())

    def test_invalid_cursors_never_call_delta(self):
        self.env['KNOWN_ZERO_DELAY_ENTITLEMENT'] = '1'
        for cursor in [None, 0, -1, True, '0', 'abc', 1.5]:
            self.body.write_text(json.dumps({'meta': {'delta_last_id': cursor}}))
            result = self.run_example('delta.sh', self.body, self.headers)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.folder / 'capture.json').exists())

    def test_known_zero_delay_and_exact_large_cursor_use_market_endpoint(self):
        self.env['KNOWN_ZERO_DELAY_ENTITLEMENT'] = '1'
        result = self.run_example('delta.sh', self.body, self.headers, '4')
        self.assertEqual(result.returncode, 0, result.stderr)
        config = self.capture()['config']
        self.assertIn('/markets/delta?last_id=123456789123456789&sport_id=4', config)
        self.assertIn('market_ids=1,41', config)
        self.assertNotIn('key=', config)
        self.assertIn('limit=100', config)
        self.assertNotIn('main_line=', config)


if __name__ == '__main__':
    unittest.main()
